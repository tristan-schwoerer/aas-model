"""Build AID data schemas from JSON Schemas (draft 2020-12), and back.

An AID data schema is a TD DataSchema (TD 1.1 §5.3.2.1): AID's own elements
plus the terms it marks EXTERNAL, which ``aas_model.submodel_templates.aid``
adds (docs/aid-extension.md §3.6). The mapping:

====================================  =====================================
JSON Schema                           AID element (semanticId)
====================================  =====================================
``type``                              ``type`` (rdf-syntax-ns#type)
``title`` / ``description``           ``title`` / the AAS description
``const`` / ``default`` / ``enum``    ``const`` / ``default`` / ``enum`` SML
``unit``                              ``unit``
``minimum``/``maximum``               ``min_max`` Range (inclusive)
``exclusiveMinimum``/``…Maximum``     ``exclusiveMinimum``/``…Maximum``
``multipleOf``                        ``multipleOf``
``minLength``/``maxLength``           ``lengthRange`` Range
``pattern`` / ``format``              ``pattern`` / ``format``
``contentEncoding``/``…MediaType``    ``contentEncoding``/``contentMediaType``
``readOnly`` / ``writeOnly``          ``readOnly`` / ``writeOnly``
``minItems``/``maxItems``             ``itemsRange`` Range
``items`` (one schema)                ``items`` (a full data schema)
``properties``                        ``properties`` → ``property_name`` map
``required``                          ``required`` SML of member names
``oneOf``                             ``oneOf`` SML of data schemas
====================================  =====================================

A schema is converted completely or not at all: a keyword without an AID
representation raises ``ValueError`` naming its path, unless the caller drops
it explicitly with ``ignore``. Annotations (``$schema``, ``$id``, ``$comment``,
``examples``) are not schema content and are skipped. Before conversion
:func:`load_schema` dereferences the schema: ``$ref`` (external and
``#/…``-internal, at any depth) is inlined and ``allOf`` is merged; ``oneOf``
stays. Two rewrites keep the meaning:

- a type union ``["T", "null"]`` (any disjoint types) becomes ``oneOf`` with
  one branch per type;
- ``prefixItems`` whose positions differ only in their annotations becomes
  ``items`` (the per-position titles are lost; validation is unchanged).

``anyOf``, ``not``, ``if``/``then``/``else``, ``additionalProperties``,
``patternProperties``, ``items`` as an array of schemas and heterogeneous
``prefixItems`` have no TD/AID representation.

Named-field style: datapoint children are DIRECT named fields on the
container (``dp.type``, ``dp.forms``, … — no ``value`` wrapper).
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import typing
from pathlib import Path
from typing import Any, Collection, Dict, Optional, Type
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen

from pydantic import BaseModel

from aas_pydantic import Property, Range

from aas_pydantic.submodel_templates.asset_interfaces_description import (
    enum as _Enum,
)
from aas_model.submodel_templates.aid import DmpOneOfBranch, DmpProperty, Required
from aas_model.constants import SCHEMA_BASE
from aas_model.submodel_templates.aid.forms import PROTOCOL_PREFIXES

# type keyword → the WoT value stored in ``type``
_TYPE_MAP = {
    "string": "string",
    "number": "number",
    "integer": "integer",
    "boolean": "boolean",
    "object": "object",
    "array": "array",
    "null": "null",
}

# Keywords that are annotations, not schema content.
_ANNOTATIONS = frozenset({"$schema", "$id", "$comment", "examples", "$defs", "definitions"})
# Keywords with an AID representation (title/description included).
_SUPPORTED = frozenset({
    "type", "title", "description", "const", "default", "unit", "enum",
    "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf",
    "minLength", "maxLength", "pattern", "format", "contentEncoding", "contentMediaType",
    "readOnly", "writeOnly", "items", "prefixItems", "minItems", "maxItems",
    "properties", "required", "oneOf",
})
# Keywords that describe a value without constraining it (kept on a union's outer schema).
_DESCRIPTIVE = frozenset({"title", "description", "unit", "default", "readOnly", "writeOnly"})


def _to_str(value: Any) -> str:
    """String form of a JSON value for a Property value (lowercase booleans,
    JSON-encoded containers)."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int, float)):
        return str(value)
    return json.dumps(value, separators=(",", ":"))


def _infer_type(schema: Dict[str, Any]) -> Optional[str]:
    """The schema's single data type: its ``type``, else ``object`` when it
    has ``properties``, ``array`` when it has ``items``/``prefixItems``, else
    none (a schema without a type accepts any value, e.g. a ``oneOf``)."""
    t = schema.get("type")
    if isinstance(t, str):
        return _TYPE_MAP.get(t)
    if schema.get("properties"):
        return "object"
    if schema.get("items") or schema.get("prefixItems"):
        return "array"
    return None


def _set_range(range_el: Any, lo: Any, hi: Any) -> None:
    """Set a Range element's min/max from JSON Schema bounds (may be None)."""
    if lo is not None:
        range_el.min = lo
    if hi is not None:
        range_el.max = hi


def _validate_integer_bounds(schema: Dict[str, Any]) -> None:
    """Reject bounds that the IDTA integer Range cannot mirror losslessly."""
    if _infer_type(schema) != "integer":
        return
    for name in ("minimum", "maximum"):
        bound = schema.get(name)
        fractional_float = (
            isinstance(bound, float)
            and (not math.isfinite(bound) or not bound.is_integer())
        )
        if bound is not None and (
            not isinstance(bound, (int, float))
            or isinstance(bound, bool)
            or fractional_float
        ):
            raise ValueError(
                f"JSON Schema integer {name}={bound!r} is fractional or invalid; "
                "the AID integer min/max Range cannot represent it without "
                "changing the schema semantics"
            )


def _const_value_type(datatype: str) -> str:
    return {
        "string": "xs:string",
        "boolean": "xs:boolean",
        "integer": "xs:int",
        "number": "xs:double",
    }.get(datatype, "xs:string")


def _member_id_short(key: str) -> str:
    """Return the key unchanged when valid, otherwise a deterministic AAS alias."""
    if len(key) <= 128 and re.fullmatch(
        r"[A-Za-z](?:[A-Za-z0-9_-]*[A-Za-z0-9_])?", key
    ):
        return key
    return "member_" + hashlib.sha256(key.encode("utf-8")).hexdigest()


def _set_range_if_bounds(container: Any, name: str, lo: Any, hi: Any) -> None:
    """Create the ``name`` Range child only when the schema declares at least
    one bound — an optional (ZeroToOne) child must not appear empty."""
    if lo is not None or hi is not None:
        _set_range(_child(container, name, Range), lo, hi)


def _required_default(cls: Type[Any], **fields: Any) -> Any:
    """Construct *cls* from *fields*, filling the mandatory (no-default) model
    fields not given with empty instances of their declared type.

    The generator emits required (One) children without a default so pydantic
    enforces that they are provided — a bare ``property_name`` therefore still
    needs its mandatory ``forms`` container (and the form's ``href``/
    ``security``).  This is the converter's "mandatory structure is present"
    construction for datapoints; optional children stay ``None`` until the
    schema says otherwise."""
    kwargs = {}
    for fname, field in cls.model_fields.items():
        if fname in fields or not field.is_required():
            continue
        target = _field_model_type_from_annotation(field.annotation)
        if target is not None:
            kwargs[fname] = _required_default(target)
    return cls(**kwargs, **fields)


def _field_model_type_from_annotation(ann: Any) -> Optional[Type[Any]]:
    """The concrete model class an annotation refers to (Optional unwrapped;
    TypeAliases / forward refs already resolved by pydantic), else ``None``."""
    origin = typing.get_origin(ann)
    if origin is typing.Union:
        args = [a for a in typing.get_args(ann) if a is not type(None)]
        ann = args[0] if args else ann
    if isinstance(ann, type) and issubclass(ann, BaseModel):
        return ann
    return None


def _field_model_type(container: Any, name: str) -> Optional[Type[Any]]:
    """The concrete model class a container's *name* field is typed with
    (Optional unwrapped; pydantic resolves TypeAliases / forward refs), else
    ``None``.  This is what lets the converter construct a *named* leaf class
    (``Optional[Key]`` → ``Key()``) whose class-level defaults carry the
    template's semanticId / value_type."""
    field = type(container).model_fields.get(name)
    if field is None:
        return None
    return _field_model_type_from_annotation(field.annotation)


def _child(container: Any, name: str, cls: Type[Any]) -> Any:
    """The container's child *name*, creating it when absent.

    Optional (ZeroToOne) template children are ``None`` until set, so the
    converter constructs them on demand.  The field's declared type wins over
    *cls* when it is a concrete model — that named class carries the template
    defaults (semanticId, value_type, …).  *cls* is the fallback for fields
    typed with a generic base or an alias that did not resolve."""
    v = getattr(container, name)
    if v is None:
        target = _field_model_type(container, name)
        v = (target or cls)()
        v.id_short = name
        setattr(container, name, v)
    return v


def _safe_id_short(value: str, index: int) -> str:
    """An id_short for an enum SML item: the value itself when it is a valid
    AAS idShort (AASd-002), else ``value_<index>``."""
    if value and value[0].isalpha() and all(
        c.isalnum() or c in "._" for c in value
    ):
        return value
    return f"value_{index}"


def _fill_enum(enum_sml: Any, values: list) -> None:
    """Populate the ``enum`` SML (json-schema#enum) with its item class's Properties."""
    item_cls = getattr(type(enum_sml), "item_type", None) or Property
    seen = set()
    items = []
    for i, v in enumerate(values):
        short = _safe_id_short(_to_str(v), i)
        while short in seen:
            short = f"{short}_{i}"
        seen.add(short)
        items.append(item_cls(id_short=short, value=_to_str(v)))
    enum_sml.value = items



# --------------------------------------------------------------------------- #
# Dereferencing: $ref (external and internal, at any depth) inlined, allOf merged
# --------------------------------------------------------------------------- #

def _merge(left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    """``allOf`` of two dereferenced schemas: members and required names are
    unions, nested schemas merge, any other keyword of ``right`` wins."""
    result = dict(left)
    for key, value in right.items():
        if key not in result:
            result[key] = value
        elif key == "required":
            result[key] = list(dict.fromkeys([*result[key], *value]))
        elif key == "properties":
            merged = dict(result[key])
            for name, member in value.items():
                merged[name] = _merge(merged[name], member) if name in merged else member
            result[key] = merged
        elif isinstance(value, dict) and isinstance(result[key], dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


def _pointer(document: Any, fragment: str) -> Any:
    target = document
    for token in [t for t in fragment.lstrip("/").split("/") if t]:
        token = token.replace("~1", "/").replace("~0", "~")
        target = target[int(token)] if isinstance(target, list) else target[token]
    return target


def dereference(schema: Dict[str, Any], base: str, loader, *, _depth: int = 0) -> Dict[str, Any]:
    """Inline every ``$ref`` (external by URL or path relative to ``base``,
    internal by ``#/…`` pointer into its document) and merge ``allOf``, at
    every depth. ``oneOf`` branches are dereferenced and kept; ``loader``
    loads a document by URL or path."""
    def walk(node: Any, doc: Any, url: str, depth: int) -> Any:
        if depth > 64:
            raise ValueError(f"$ref nesting deeper than 64 levels at {url} (recursive schema?)")
        if isinstance(node, list):
            return [walk(item, doc, url, depth) for item in node]
        if not isinstance(node, dict):
            return node
        result: Dict[str, Any] = {}
        if "$ref" in node:
            ref = node["$ref"]
            target_url, _, fragment = ref.partition("#")
            if target_url:
                target_url = urljoin(url, target_url) if urlparse(url).scheme or url.startswith("/") \
                    else _join_path(url, target_url)
                target_doc = loader(target_url)
            else:
                target_url, target_doc = url, doc
            result = walk(_pointer(target_doc, fragment), target_doc, target_url, depth + 1)
        for sub in node.get("allOf", []):
            result = _merge(result, walk(sub, doc, url, depth + 1))
        for key, value in node.items():
            if key in ("$ref", "allOf") or key in _ANNOTATIONS:
                continue
            if key == "properties" and isinstance(value, dict):
                value = {name: walk(member, doc, url, depth + 1) for name, member in value.items()}
            elif isinstance(value, (dict, list)) and key not in ("enum", "const", "default", "required", "examples"):
                value = walk(value, doc, url, depth + 1)
            result = _merge(result, {key: value})
        return result
    return walk(schema, schema, base, _depth)


def _join_path(base: str, relative: str) -> str:
    return os.path.normpath(os.path.join(os.path.dirname(base), relative))


# --------------------------------------------------------------------------- #
# JSON Schema → AID
# --------------------------------------------------------------------------- #

def _unrepresentable(path: str, keyword: str) -> ValueError:
    return ValueError(f"{path}: the JSON Schema keyword {keyword!r} has no TD/AID representation; "
                      f"convert the schema or drop it explicitly with ignore={{{keyword!r}}}")


def _rewrite_type_union(schema: Dict[str, Any], path: str) -> Dict[str, Any]:
    """``{"type": [A, B, …], …}`` → ``{"oneOf": [{"type": A, …}, {"type": B, …}]}``.
    Exact for disjoint types (each branch keeps the constraints; those that
    don't apply to its type are inert, as in JSON Schema)."""
    types = schema["type"]
    if not types or not all(isinstance(t, str) and t in _TYPE_MAP for t in types):
        raise ValueError(f"{path}/type: unsupported type union {types!r}")
    if {"integer", "number"} <= set(types):
        raise ValueError(f"{path}/type: the union {types!r} overlaps (every integer is a number); oneOf cannot express it")
    if "oneOf" in schema:
        raise ValueError(f"{path}: a type union together with oneOf has no TD/AID representation")
    outer = {k: v for k, v in schema.items() if k in _DESCRIPTIVE}
    constraints = {k: v for k, v in schema.items() if k != "type" and k not in _DESCRIPTIVE}

    def applies(keyword: str, datatype: str) -> bool:
        owner = next((t for t, words in _TYPE_KEYWORDS.items() if keyword in words), None)
        return owner is None or owner == datatype or (owner == "number" and datatype == "integer")

    return {**outer, "oneOf": [{**{k: v for k, v in constraints.items() if applies(k, t)}, "type": t}
                               for t in types]}


# Keywords that constrain values of one type only; others (enum, const, …) apply to all.
_TYPE_KEYWORDS = {
    "string": {"minLength", "maxLength", "pattern", "format", "contentEncoding", "contentMediaType"},
    "number": {"minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf"},
    "array": {"items", "prefixItems", "minItems", "maxItems"},
    "object": {"properties", "required"},
}


def _homogeneous_items(schema: Dict[str, Any], path: str) -> Dict[str, Any]:
    """``prefixItems`` whose positions differ only in annotations → their
    shared ``items`` schema; anything else is a tuple TD cannot describe."""
    if "items" in schema:
        raise ValueError(f"{path}: prefixItems together with items has no TD/AID representation")
    positions = schema["prefixItems"]
    shapes = [{k: v for k, v in p.items() if k not in ("title", "description")} for p in positions
              if isinstance(p, dict)]
    if len(shapes) != len(positions) or not shapes or any(shape != shapes[0] for shape in shapes):
        raise ValueError(f"{path}/prefixItems: positions with different schemas (a tuple) have no TD/AID representation")
    return shapes[0]


def _schema_field(container: Any, name: str, path: str) -> Any:
    """The container's data-schema child ``name`` (created when absent); the
    container must be an AID extension class, which carries every term."""
    if name not in type(container).model_fields:
        raise ValueError(f"{path}: {type(container).__name__} has no {name!r}; build data schemas "
                         f"with the AID extension classes (aas_model.submodel_templates.aid)")
    return _child(container, name, Property)


def populate_datapoint(
    dp: Any,
    schema: Dict[str, Any],
    *,
    key: Optional[str] = None,
    schema_url: Optional[str] = None,
    ignore: Collection[str] = (),
    path: str = "$",
) -> None:
    """Fill an existing data schema (a ``DmpProperty``, an action's input or
    output, an event payload, a nested member) from a dereferenced JSON
    Schema dict.

    Only the fields the schema describes are touched — fields the caller
    already set (``forms``, ``key``, …) are left alone. A keyword naming a
    binding term of the datapoint's class (e.g. ``uav_eventField`` on an OPC UA
    event field) sets that term. Any other keyword without an AID
    representation raises ``ValueError`` unless it is in ``ignore`` (applied at
    every depth).

    ``schema_url`` (the JSON Schema URL the datapoint was built from) is
    recorded as a supplemental semantic id on the datapoint — the schema URL
    rides on the DataSchema it represents instead of a separate URL Property.
    """
    ignore = frozenset(ignore)
    schema = {k: v for k, v in schema.items() if k not in ignore and k not in _ANNOTATIONS}
    terms = {keyword: schema.pop(keyword) for keyword in list(schema)
             if keyword not in _SUPPORTED and keyword.startswith(PROTOCOL_PREFIXES)
             and keyword in type(dp).model_fields}
    for keyword in schema:
        if keyword not in _SUPPORTED:
            raise _unrepresentable(path, keyword)
    for keyword, value in terms.items():
        _child(dp, keyword, Property).value = _to_str(value)
    if isinstance(schema.get("type"), list):
        schema = _rewrite_type_union(schema, path)
    if "prefixItems" in schema:
        shared = _homogeneous_items(schema, path)
        schema = {**{k: v for k, v in schema.items() if k != "prefixItems"}, "items": shared}
    if isinstance(schema.get("items"), list):
        raise ValueError(f"{path}/items: an array of schemas (a tuple) has no TD/AID representation")
    if "type" in schema and _infer_type(schema) is None:
        raise ValueError(f"{path}/type: unknown type {schema['type']!r}")

    if key:
        dp.id_short = key
        _child(dp, "key", Property).value = key

    if schema_url and schema_url not in (dp.supplemental_semantic_ids or []):
        dp.supplemental_semantic_ids = (dp.supplemental_semantic_ids or []) + [schema_url]

    datatype = _infer_type(schema)
    _validate_integer_bounds(schema)
    if datatype:
        _child(dp, "type", Property).value = datatype

    if schema.get("title"):
        _child(dp, "title", Property).value = _to_str(schema["title"])
    if schema.get("description"):
        dp.description = _to_str(schema["description"])
    if "const" in schema:
        const = _child(dp, "const", Property)
        const.value = _to_str(schema["const"])
        const.value_type = _const_value_type(datatype)
    if "default" in schema:
        _child(dp, "default", Property).value = _to_str(schema["default"])
    if schema.get("unit"):
        _child(dp, "unit", Property).value = _to_str(schema["unit"])
    if schema.get("enum"):
        _fill_enum(_child(dp, "enum", _Enum), schema["enum"])

    # numeric / string / array bounds — Ranges appear only when bounded
    _set_range_if_bounds(dp, "min_max", schema.get("minimum"), schema.get("maximum"))
    _set_range_if_bounds(dp, "lengthRange", schema.get("minLength"), schema.get("maxLength"))
    _set_range_if_bounds(dp, "itemsRange", schema.get("minItems"), schema.get("maxItems"))
    number_type = "xs:integer" if datatype == "integer" else "xs:double"
    for keyword in ("exclusiveMinimum", "exclusiveMaximum", "multipleOf"):
        if keyword in schema:
            element = _schema_field(dp, keyword, path)
            element.value, element.value_type = _to_str(schema[keyword]), number_type
    for keyword in ("pattern", "format", "contentEncoding", "contentMediaType", "readOnly", "writeOnly"):
        if keyword in schema:
            _schema_field(dp, keyword, path).value = _to_str(schema[keyword])

    if isinstance(schema.get("items"), dict):
        _schema_field(dp, "items", path)
        populate_datapoint(dp.items, schema["items"], ignore=ignore, path=f"{path}/items")
    if "oneOf" in schema:
        if not isinstance(schema["oneOf"], list) or not schema["oneOf"]:
            raise ValueError(f"{path}/oneOf: expected a non-empty array of schemas")
        branches = _schema_field(dp, "oneOf", path)
        branch_cls = getattr(type(branches), "item_type", DmpOneOfBranch)
        branches.value = []
        for index, branch_schema in enumerate(schema["oneOf"]):
            branch = _required_default(branch_cls)
            populate_datapoint(branch, branch_schema, ignore=ignore, path=f"{path}/oneOf/{index}")
            branch.id_short = f"branch_{index}"
            branches.value.append(branch)
    if "properties" in schema:
        members = schema["properties"]
        container = _schema_field(dp, "properties", path)
        member_cls = _map_item_type(container, "property_name")
        props_map = container.property_name
        reserved = {name for name in members if _member_id_short(name) == name}
        aliases = set()
        for name, sub in members.items():
            alias = _member_id_short(name)
            if alias != name:
                alias = f"{alias}_{len(aliases)}"
                while alias in reserved or alias in aliases:
                    alias += "_"
            aliases.add(alias)
            child = _required_default(member_cls)
            populate_datapoint(child, sub, key=name, ignore=ignore, path=f"{path}/properties/{name}")
            child.id_short = alias
            props_map[alias] = child
    if "required" in schema:
        names = schema["required"]
        unknown = [n for n in names if n not in schema.get("properties", {})]
        if unknown:
            raise ValueError(f"{path}/required: {unknown} are not members of this object")
        _schema_field(dp, "required", path)
        # An empty list requires nothing, as an absent one does.
        dp.required = Required(value=[Property(value=name) for name in names]) if names else None


def _map_item_type(container: Any, name: str) -> Type[Any]:
    """The value class of a container's ``Dict[str, X]`` field."""
    ann = type(container).model_fields[name].annotation
    args = typing.get_args(ann)
    return args[1] if len(args) == 2 and isinstance(args[1], type) else type(container)


def datapoint_from_schema(
    schema: Dict[str, Any],
    *,
    key: Optional[str] = None,
    cls: Type[Any] = DmpProperty,
    schema_url: Optional[str] = None,
    ignore: Collection[str] = (),
    **fields: Any,
) -> Any:
    """A ``cls`` built from a dereferenced JSON Schema dict: its data schema terms from ``schema``, its other fields
    (``title``, ``forms``, ``observable``, …) from ``fields`` as the class's own constructor takes them.

    ``cls`` defaults to a property affordance (``DmpProperty``); pass e.g.
    ``DmpActionInput``/``DmpActionOutput`` or an event payload class. Nested
    members, ``items`` and ``oneOf`` branches take the classes their parent
    declares. Mandatory children not given (e.g. a property's ``forms``) are
    constructed, so the datapoint is always a valid instance. ``key`` names it
    (its idShort and AID ``key``); ``ignore`` names keywords to drop instead of
    failing on them.

    ``schema_url`` (the JSON Schema URL) is recorded as a supplemental
    semantic id on the built datapoint.
    """
    dp = _required_default(cls, **fields)
    populate_datapoint(dp, schema, key=key, schema_url=schema_url, ignore=ignore)
    return dp


# --------------------------------------------------------------------------- #
# AID → JSON Schema
# --------------------------------------------------------------------------- #

def _value_from_property(value: str, datatype: Optional[str]) -> Any:
    """Recover the JSON value encoded in an AAS Property (whose value is text)."""
    if datatype == "string":
        return value
    if datatype == "null":
        return None
    if datatype == "boolean":
        normalized = value.casefold()
        if normalized in ("true", "false"):
            return normalized == "true"
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return value


def _number(value: str, integer: bool) -> Any:
    number = float(value)
    return int(number) if integer or number.is_integer() and "." not in value and "e" not in value.lower() else number


def _range_from_element(schema: Dict[str, Any], element: Any,
                        lower: str, upper: str, *, integer: bool = False) -> None:
    if element is None:
        return
    for name, bound in ((lower, element.min), (upper, element.max)):
        if bound is not None:
            schema[name] = int(bound) if integer else float(bound)


def schema_from_datapoint(dp: Any) -> Dict[str, Any]:
    """Reconstruct the JSON Schema of an AID data schema (any level: a
    property, an action's input/output, an event payload, a member, an
    array's ``items``, a ``oneOf`` branch). Transport/form metadata and schema
    URLs are not JSON Schema keywords and are excluded."""
    schema: Dict[str, Any] = {}
    datatype_element = getattr(dp, "type", None)
    datatype = datatype_element.value if datatype_element is not None else None
    if datatype:
        schema["type"] = datatype

    title = getattr(dp, "title", None)
    if title is not None:
        schema["title"] = title.value
    description = getattr(dp, "description", None)
    # Template classes provide prose descriptions which aren't payload schemas.
    if description and description != type(dp).model_fields["description"].default:
        schema["description"] = description
    for name in ("const", "default"):
        element = getattr(dp, name, None)
        if element is not None:
            schema[name] = _value_from_property(element.value, datatype or "string")
    unit = getattr(dp, "unit", None)
    if unit is not None:
        schema["unit"] = unit.value
    enum = getattr(dp, "enum", None)
    if enum is not None:
        schema["enum"] = [_value_from_property(element.value, datatype or "string")
                          for element in enum.value]

    _range_from_element(schema, getattr(dp, "min_max", None),
                        "minimum", "maximum", integer=datatype == "integer")
    _range_from_element(schema, getattr(dp, "lengthRange", None),
                        "minLength", "maxLength", integer=True)
    _range_from_element(schema, getattr(dp, "itemsRange", None),
                        "minItems", "maxItems", integer=True)
    for name in ("exclusiveMinimum", "exclusiveMaximum", "multipleOf"):
        element = getattr(dp, name, None)
        if element is not None:
            schema[name] = _number(element.value, datatype == "integer")
    for name in ("pattern", "format", "contentEncoding", "contentMediaType"):
        element = getattr(dp, name, None)
        if element is not None:
            schema[name] = element.value
    for name in ("readOnly", "writeOnly"):
        element = getattr(dp, name, None)
        if element is not None:
            schema[name] = str(element.value).lower() == "true"

    items = getattr(dp, "items", None)
    if items is not None:
        schema["items"] = schema_from_datapoint(items)
    one_of = getattr(dp, "oneOf", None)
    if one_of is not None:
        schema["oneOf"] = [schema_from_datapoint(branch) for branch in one_of.value]
    properties = getattr(dp, "properties", None)
    if properties is not None:
        schema["properties"] = {
            (child.key.value if child.key is not None else name): schema_from_datapoint(child)
            for name, child in properties.property_name.items()
        }
    required = getattr(dp, "required", None)
    if required is not None:
        schema["required"] = [name.value for name in required.value]
    return schema


def without(schema: Any, *keywords: str) -> Any:
    """``schema`` with ``keywords`` removed at every depth: the explicit,
    visible way to drop constraints TD/AID cannot represent (the builder
    refuses them otherwise). Member names in ``properties`` are kept."""
    if isinstance(schema, list):
        return [without(item, *keywords) for item in schema]
    if not isinstance(schema, dict):
        return schema
    return {key: ({name: without(member, *keywords) for name, member in value.items()}
                  if key == "properties" and isinstance(value, dict) else without(value, *keywords))
            for key, value in schema.items() if key not in keywords}


def _schema_dir() -> Path:
    """The vendored schemas: ``MQTT_SCHEMAS_DIR``, or the ``MQTTSchemas`` of an aas-model checkout."""
    return Path(os.environ.get("MQTT_SCHEMAS_DIR") or Path(__file__).resolve().parents[2] / "MQTTSchemas")


def _read_schema(ref: str) -> Dict[str, Any]:
    """One schema document by URL or path. A published schema (``SCHEMA_BASE``) is read from the vendored copy
    and fetched only when that has no such file; a relative path is relative to the vendored schemas."""
    if urlparse(ref).scheme in ("http", "https"):
        if ref.startswith(f"{SCHEMA_BASE}/"):
            local = _schema_dir() / ref.removeprefix(f"{SCHEMA_BASE}/")
            if local.is_file():
                return json.loads(local.read_text(encoding="utf-8"))
        with urlopen(ref, timeout=5) as response:
            return json.load(response)
    path = Path(ref) if Path(ref).is_absolute() else _schema_dir() / ref
    return json.loads(path.read_text(encoding="utf-8"))


def load_schema(schema_url: str) -> Dict[str, Any]:
    """Load and dereference a JSON Schema (URL or path) into one dict: every
    ``$ref`` inlined (published schemas are read from the vendored ``MQTTSchemas``),
    ``allOf`` merged, ``oneOf`` kept. Pass the result to
    :func:`datapoint_from_schema` / :func:`populate_datapoint`."""
    documents: Dict[str, Any] = {}

    def read(ref: str) -> Dict[str, Any]:
        if ref not in documents:
            documents[ref] = _read_schema(ref)
        return documents[ref]

    return dereference(read(schema_url), schema_url, read)
