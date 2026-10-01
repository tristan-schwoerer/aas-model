"""Build AID object-schema datapoints from JSON Schemas (draft 2020-12).

The IDTA AssetInterfacesDescription data schemas are a WoT-2.0-ized subset of
JSON Schema:

============  ==========================================================
JSON Schema   AID element (semanticId)
============  ==========================================================
``type``      ``value.type`` (rdf-syntax-ns#type)
``title``     ``value.title`` (td#title)
``const``     ``value.const`` (json-schema#const)
``enum``      ``value.enum`` SML (json-schema#enum)
``default``   ``value.default`` (json-schema#default)
``minimum``/``maximum``        ``value.min_max`` Range (minMaxRange)
``minLength``/``maxLength``    ``value.lengthRange`` Range (lengthRange)
``minItems``/``maxItems``      ``value.itemsRange`` Range (itemsRange)
``items``     ``value.items`` SMC (json-schema#items)
``properties``                 ``value.properties`` → ``property_name`` map
============  ==========================================================

This module turns a plain (already-dereferenced) JSON Schema dict into the
generated ``property_name`` / ``property_name_json_schema`` classes, so
resource messages (``MQTTSchemas/*.json``) don't have to be hand-built.

``$ref`` / ``allOf`` / ``anyOf`` / ``oneOf`` resolution is delegated to
:class:`schema_parser.SchemaParser` via :func:`load_schema`; pass the result
to :func:`datapoint_from_schema` (new instance) or :func:`populate_datapoint`
(fill an existing instance, e.g. an ``MqttProperty`` whose forms / schema
URLs are already set).

Named-field style: datapoint children are DIRECT named fields on the
container (``dp.type``, ``dp.forms``, … — no ``value`` wrapper).

Limitations (mirroring the IDTA template): the ``items`` schema is leaf-only
(no nested objects/arrays inside an array), there is no ``required`` marker,
and ``anyOf``/``oneOf`` unions are approximated by the dereferencer (first
branch).
"""

from __future__ import annotations

import json
import typing
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel

from aas_pydantic import Property, Range

from aas_pydantic.submodel_templates.asset_interfaces_description import (
    enum as _Enum,
    forms as _Forms,
    items as _Items,
    property_name as _PropertyName,
    property_name_json_schema as _NestedPropertyName,
    properties_json_schema as _PropertiesSchema,
)

# type keyword → the WoT value stored in ``value.type``
_TYPE_MAP = {
    "string": "string",
    "number": "number",
    "integer": "integer",
    "boolean": "boolean",
    "object": "object",
    "array": "array",
    "null": "null",
}


def _to_str(value: Any) -> str:
    """String form of a JSON value for a Property value (lowercase booleans,
    JSON-encoded containers)."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int, float)):
        return str(value)
    return json.dumps(value, separators=(",", ":"))


def _infer_type(schema: Dict[str, Any]) -> str:
    """The element's data type: explicit ``type``, else inferred from the
    schema's structure (object if it has ``properties``, array if it has
    ``items``/``prefixItems``, else ``string``)."""
    t = schema.get("type")
    if isinstance(t, str) and t in _TYPE_MAP:
        return _TYPE_MAP[t]
    if isinstance(t, list):
        # JSON Schema union type (e.g. ["string", "null"]) — first known wins
        for item in t:
            if isinstance(item, str) and item in _TYPE_MAP:
                return _TYPE_MAP[item]
    if schema.get("properties"):
        return "object"
    if schema.get("items") or schema.get("prefixItems"):
        return "array"
    return "string"


def _set_range(range_el: Any, lo: Any, hi: Any) -> None:
    """Set a Range element's min/max from JSON Schema bounds (may be None)."""
    if lo is not None:
        range_el.min = lo
    if hi is not None:
        range_el.max = hi


def _set_range_if_bounds(container: Any, name: str, lo: Any, hi: Any) -> None:
    """Create the ``name`` Range child only when the schema declares at least
    one bound — an optional (ZeroToOne) child must not appear empty."""
    if lo is not None or hi is not None:
        _set_range(_child(container, name, Range), lo, hi)


def _required_default(cls: Type[Any]) -> Any:
    """Construct *cls* filling mandatory (no-default) model fields with empty
    instances of their declared type.

    The generator emits required (One) children without a default so pydantic
    enforces that they are provided — a bare ``property_name`` therefore still
    needs its mandatory ``forms`` container (and the form's ``href``/
    ``security``).  This is the converter's "mandatory structure is present"
    construction for datapoints; optional children stay ``None`` until the
    schema says otherwise."""
    kwargs = {}
    for fname, field in cls.model_fields.items():
        if not field.is_required():
            continue
        target = _field_model_type_from_annotation(field.annotation)
        if target is not None:
            kwargs[fname] = _required_default(target)
    return cls(**kwargs)


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
    """Populate the ``enum`` SML (json-schema#enum) with Property items."""
    seen = set()
    items = []
    for i, v in enumerate(values):
        short = _safe_id_short(_to_str(v), i)
        while short in seen:
            short = f"{short}_{i}"
        seen.add(short)
        items.append(Property(id_short=short, value=_to_str(v)))
    enum_sml.value = items


def _fill_items(items: Any, schema: Dict[str, Any]) -> None:
    """Populate the ``items`` SMC (json-schema#items) for a leaf item schema.

    The AID ``items`` schema is leaf-only — nested objects/arrays inside an
    array are not representable and are skipped.  Direct named fields on the
    ``items`` SMC (``type``, ``title``, ``enum``, ``min_max``, …).
    """
    _child(items, "type", Property).value = _infer_type(schema)
    if schema.get("title"):
        _child(items, "title", Property).value = _to_str(schema["title"])
    if "const" in schema:
        _child(items, "const", Property).value = _to_str(schema["const"])
    if "default" in schema:
        _child(items, "default", Property).value = _to_str(schema["default"])
    if schema.get("unit"):
        _child(items, "unit", Property).value = _to_str(schema["unit"])
    if schema.get("enum"):
        _fill_enum(_child(items, "enum", _Enum), schema["enum"])
    _set_range_if_bounds(items, "min_max",
                         schema.get("minimum"), schema.get("maximum"))
    _set_range_if_bounds(items, "lengthRange",
                         schema.get("minLength"), schema.get("maxLength"))


def _fill_prefix_items(items: Any, prefix_items: list) -> None:
    """Populate ``items`` from a homogeneous ``prefixItems`` tuple (e.g. the
    position ``[x, y, theta]`` pattern).  AID arrays are homogeneous, so only
    the shared type/constraints are captured."""
    subs = [s for s in prefix_items if isinstance(s, dict)]
    if not subs:
        return
    types = {_infer_type(s) for s in subs}
    if len(types) == 1:
        _fill_items(items, {**subs[0], "type": next(iter(types))})


def _fill_form(
    forms: Any,
    *,
    href: Optional[str] = None,
    op: Optional[str] = None,
    content_type: Optional[str] = None,
    subprotocol: Optional[str] = None,
) -> None:
    """Write the WoT form's transport binding into an existing form container.

    ``href`` is the topic/URI the message comes from.  Fields are only set when
    the form's class declares them (the generic ``forms`` template lacks
    ``op`` — that lives on the MQTT ``MqttForm`` extension), so this composes
    with both the generated form and a caller-supplied ``MqttForm``."""
    for fname, value in (
        ("href", href),
        ("op", op),
        ("contentType", content_type),
        ("subprotocol", subprotocol),
    ):
        if value is None or fname not in type(forms).model_fields:
            continue
        _child(forms, fname, Property).value = value


def populate_datapoint(
    dp: Any,
    schema: Dict[str, Any],
    *,
    key: Optional[str] = None,
    schema_url: Optional[str] = None,
    forms: Any = None,
    href: Optional[str] = None,
    op: Optional[str] = None,
    content_type: Optional[str] = None,
    subprotocol: Optional[str] = None,
) -> None:
    """Fill an existing datapoint instance (``property_name`` or a subclass
    like ``MqttProperty``, or a nested ``property_name_json_schema``) from a
    dereferenced JSON Schema dict.

    Only the fields the schema describes are touched — fields the caller
    already set (``forms``, ``key``, …) are left alone, so this composes with
    the MQTT/resource builders.

    ``schema_url`` (the JSON Schema URL the datapoint was built from) is
    recorded as a supplemental semantic id on the datapoint — the schema URL
    rides on the DataSchema it represents instead of a separate URL Property.
    """
    if key:
        dp.id_short = key
        _child(dp, "key", Property).value = key

    if schema_url and schema_url not in (dp.supplemental_semantic_ids or []):
        dp.supplemental_semantic_ids = (dp.supplemental_semantic_ids or []) + [schema_url]

    datatype = _infer_type(schema)
    _child(dp, "type", Property).value = datatype

    if schema.get("title"):
        _child(dp, "title", Property).value = _to_str(schema["title"])
    if schema.get("description"):
        dp.description = _to_str(schema["description"])
    if "const" in schema:
        _child(dp, "const", Property).value = _to_str(schema["const"])
    if "default" in schema:
        _child(dp, "default", Property).value = _to_str(schema["default"])
    if schema.get("unit"):
        _child(dp, "unit", Property).value = _to_str(schema["unit"])
    if schema.get("enum"):
        _fill_enum(_child(dp, "enum", _Enum), schema["enum"])

    # ``property_name.forms`` is mandatory (missing qualifier → One).  The
    # schema itself carries no form info — the caller supplies the transport
    # binding: either a ready ``forms`` instance (e.g. ``MqttForm``) or the
    # WoT form fields (``href`` = the topic the message comes from, ``op``,
    # ``content_type``, ``subprotocol``).  A caller-supplied form replaces the
    # empty required-structure one; an already-set forms (MQTT builders) is
    # left alone unless the caller passes explicit form fields.
    if "forms" in type(dp).model_fields:
        if forms is not None:
            f = forms
            setattr(dp, "forms", f)
        else:
            f = getattr(dp, "forms", None)
            if f is None:
                f = _child(dp, "forms", _Forms)
                setattr(dp, "forms", f)
        _fill_form(f, href=href, op=op,
                   content_type=content_type, subprotocol=subprotocol)

    # numeric / string / array bounds — Ranges appear only when bounded
    _set_range_if_bounds(dp, "min_max",
                         schema.get("minimum"), schema.get("maximum"))
    _set_range_if_bounds(dp, "lengthRange",
                         schema.get("minLength"), schema.get("maxLength"))

    if datatype == "array":
        _set_range_if_bounds(dp, "itemsRange",
                             schema.get("minItems"), schema.get("maxItems"))
        item = schema.get("items")
        if isinstance(item, dict):
            _fill_items(_child(dp, "items", _Items), item)
        elif schema.get("prefixItems"):
            _fill_prefix_items(_child(dp, "items", _Items), schema["prefixItems"])
    elif datatype == "object":
        # recursive object-schema nesting (WoT 2.0 ``properties`` keyword)
        props_map = _child(dp, "properties", _PropertiesSchema).property_name
        for name, sub in (schema.get("properties") or {}).items():
            props_map[name] = datapoint_from_schema(
                sub, key=name, cls=_NestedPropertyName
            )


def datapoint_from_schema(
    schema: Dict[str, Any],
    *,
    key: Optional[str] = None,
    cls: Type[Any] = _PropertyName,
    schema_url: Optional[str] = None,
    forms: Any = None,
    href: Optional[str] = None,
    op: Optional[str] = None,
    content_type: Optional[str] = None,
    subprotocol: Optional[str] = None,
) -> Any:
    """Build a new datapoint instance from a dereferenced JSON Schema dict.

    ``cls`` defaults to the top-level ``property_name`` (PropertyDefinition);
    pass ``property_name_json_schema`` for nested object members (the
    converter does this automatically for ``properties`` children).  Mandatory
    children (e.g. ``property_name.forms``) are constructed so the datapoint is
    always a valid instance.

    The ``forms`` container is mandatory and carries the transport binding
    (the topic the message comes from).  Pass the WoT form fields directly —
    ``href`` (topic/URI), ``op`` (e.g. ``observeProperty``), ``content_type``,
    ``subprotocol`` — or a ready ``forms`` instance (e.g. ``MqttForm`` from
    ``aas_model.submodel_templates.aid``) to include MQTT qualifiers.

    ``schema_url`` (the JSON Schema URL) is recorded as a supplemental
    semantic id on the built datapoint.
    """
    dp = _required_default(cls)
    populate_datapoint(
        dp, schema, key=key, schema_url=schema_url,
        forms=forms, href=href, op=op,
        content_type=content_type, subprotocol=subprotocol,
    )
    return dp


def load_schema(schema_url: str) -> Dict[str, Any]:
    """Load + dereference a JSON Schema (URL or path) into a flat dict.

    ``$ref`` is resolved against the ``MQTTSchemas`` directory (github.io
    URLs map to the local vendored copy), and ``allOf``/``anyOf``/``oneOf``
    are merged — see :class:`schema_parser.SchemaParser`.
    """
    from aas_model.schema_parser import SchemaParser  # lazy: schema_parser imports requests

    return SchemaParser().parse_schema(schema_url)
