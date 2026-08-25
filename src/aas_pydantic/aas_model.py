from __future__ import annotations

import copy
import itertools
from types import UnionType as _UnionType
from typing import Annotated, Any, Dict, List, Optional, TypeVar, Union, Literal
import typing

from basyx.aas.model import (
    AssetAdministrationShell,
    DictIdentifiableStore,
    Submodel
)
from pydantic import (
    AfterValidator,
    BaseModel,
    Field,
    ValidationError,
    field_serializer,
    model_serializer,
    model_validator,
)


BasyxModels = AssetAdministrationShell | Submodel | DictIdentifiableStore


def string_does_start_with_a_character(v: str):
    assert v, "value must not be an empty string"
    assert v[0].isalpha(), "value must start with a character"
    return v


AasIdString = Annotated[str, AfterValidator(string_does_start_with_a_character)]
Reference = TypeVar(
    "Reference",
    bound=Annotated[str, AfterValidator(string_does_start_with_a_character)],
)


class Referable(BaseModel):
    # Strict basyx alignment: unknown fields (e.g. the old alias names) are
    # rejected instead of silently ignored.
    model_config = {"extra": "forbid"}

    id_short: AasIdString
    description: str = ""
    # basyx Referable.display_name — lang→text map (e.g. for SML items that
    # carry no id_short, so they can still be identified visually).
    display_name: Optional[Dict[str, str]] = None


class Identifiable(Referable):
    id: AasIdString

    @model_validator(mode="before")
    @classmethod
    def check_id_and_id_short(cls, data: Any) -> Any:
        if isinstance(data, BaseModel):
            data = data.model_dump()
        elif not isinstance(data, dict):
            data = {
                "id": getattr(data, "id", ""),
                "id_short": getattr(data, "id_short", ""),
            }
        assert "id" in data or "id_short" in data, "Either id or id_short must be set"
        if "id_short" not in data:
            data["id_short"] = data["id"]
        if "id" not in data:
            data["id"] = data["id_short"]
        return data


class Qualifier(BaseModel):
    """AAS Qualifier — named constraint with optional semantic reference.

    Field names follow basyx strictly: ``type_``, ``value``, ``value_type``,
    ``value_id``, ``kind``, ``semantic_id``.  Unknown fields (e.g. the old
    ``type`` alias) are rejected.
    """
    model_config = {"extra": "forbid"}

    type_: str = ""
    value: str = ""
    value_type: str = "xs:string"
    value_id: str = ""
    semantic_id: str = ""
    kind: str = "TemplateQualifier"

class Cardinality(Qualifier):
    type_: str = "SMT/Cardinality"
    value: Literal["ZeroToOne", "ZeroToMany", "One", "OneToMany"] = "ZeroToMany"
    semantic_id: str = "https://admin-shell.io/SubmodelTemplates/Cardinality/1/0"


class HasSemantics(BaseModel):
    semantic_id: str = ""
    supplemental_semantic_ids: List[str] = []
    qualifiers: List[Qualifier] = []


class AAS(Identifiable):
    # AAS-level metadata (not submodels — excluded from check_submodels)
    asset_type: str = ""
    derived_from: str = ""
    specific_asset_ids: dict[str, str] = {}

    @model_validator(mode="before")
    @classmethod
    def set_optional_fields_to_None(cls, data):
        if isinstance(data, BaseModel):
            data = data.model_dump()
        for field_name, field_info in cls.model_fields.items():
            if field_name in data:
                continue
            if typing.get_origin(field_info.annotation) == Union and type(
                None
            ) in typing.get_args(field_info.annotation):
                data[field_name] = None
        return data

    @model_validator(mode="after")
    def check_submodels(self) -> Any:
        _meta = {"id", "id_short", "description", "display_name", "asset_type", "derived_from", "specific_asset_ids"}
        for field_name, field_info in type(self).model_fields.items():
            if field_name in _meta:
                continue
            elif (
                typing.get_origin(field_info.annotation) == Union
                and type(None) in typing.get_args(field_info.annotation)
                and getattr(self, field_name) is None
            ):
                continue
            try:
                Submodel.model_validate(getattr(self, field_name))
            except ValidationError:
                assert False, f"Field '{field_name}' must be of type Submodel"
        return self


def is_valid_submodel_element(submodel_element: Any) -> bool:
    """Rich-only element check.

    Accepts only ``SubmodelElement`` instances, lists/containers of them, or
    dicts that either (a) are ``Dict[str, SubmodelElement]`` containers, or
    (b) serialize to one of the concrete element classes.  Bare primitives are
    rejected.  Validation runs against the concrete element classes (not the
    abstract ``SubmodelElement`` base) because every element type declares
    extra fields that the base model forbids.
    """
    if submodel_element is None:
        return True
    if isinstance(submodel_element, SubmodelElement):
        return True
    elif isinstance(submodel_element, (list, tuple, set)):
        return all(is_valid_submodel_element(e) for e in submodel_element)
    elif isinstance(submodel_element, dict):
        if "id_short" not in submodel_element:
            # Dict[str, SubmodelElement] container
            return all(
                is_valid_submodel_element(v) for v in submodel_element.values()
            )
        # Serialized element — validate against the concrete element classes.
        for cls in _CONCRETE_ELEMENT_TYPES:
            try:
                cls.model_validate(submodel_element)
                return True
            except Exception:
                continue
        # Fallback: an SMC-shaped dict whose concrete subclass is not known
        # here — every non-meta value must itself be a valid element.
        return all(
            is_valid_submodel_element(v)
            for k, v in submodel_element.items()
            if k not in _ELEMENT_META_KEYS
        )
    return False


def _stamp_container_id_shorts(model: Any) -> None:
    """Enforce ``key == id_short`` for every dict-container child.

    The dict key is the single source of truth for a child's id_short, so
    source never repeats ``id_short=<key>`` on the instances.  This stamps
    each child's id_short from its key on every constructed model
    (defaults included).  Children are copied, never mutated.

    Named-field style: dynamic maps are ``Dict[str, X]`` fields anywhere on a
    container (``Variables.variable``, ``MqttActions.property_name``,
    ``Endpoints.endpoint``, …)."""
    try:
        hints = typing.get_type_hints(type(model), include_extras=True)
    except Exception:
        hints = {k: v.annotation for k, v in type(model).model_fields.items()}
    for fname, ann in hints.items():
        if fname in ("id_short", "description", "display_name", "semantic_id",
                     "qualifiers", "supplemental_semantic_ids", "category"):
            continue
        container = getattr(model, fname, None)
        if not isinstance(container, dict):
            continue
        if typing.get_origin(ann) is not dict:
            # e.g. a plain dict value (not a model field) — still stamp it.
            pass
        for k, v in list(container.items()):
            if isinstance(v, SubmodelElement) and v.id_short != k:
                container[k] = v.model_copy(update={"id_short": k})


# Every concrete element class registers itself here (via
# ``SubmodelElement.__init_subclass__``) so dumps can carry a ``modelType``
# discriminator and revalidation resolves the concrete type directly instead
# of relying on fragile key inference.
_ELEMENT_CLASS_REGISTRY: dict = {}

# semanticId value → list of concrete element classes carrying it.  Populated
# alongside the class registry.  Resolution only uses a semanticId when it is
# UNIQUE — shared semanticIds (e.g. handwritten MQTT deltas vs their generated
# bases, or an SML vs its items) are ambiguous and fall back to generic types.
_SEMANTIC_ID_REGISTRY: dict = {}


def _resolve_semantic_id_cls(sid: str):
    """Concrete class uniquely identified by *sid*, or ``None`` when the
    semanticId is shared by several classes (ambiguous → generic fallback)."""
    classes = _SEMANTIC_ID_REGISTRY.get(sid)
    if classes and len(classes) == 1:
        return classes[0]
    return None


def _dump_container(container: Any, concept_sid: str = "") -> Any:
    """Serialize a container losslessly — each child is dumped with its own
    concrete model and tagged with ``modelType`` (its class name).

    Handles ``Dict[str, SubmodelElement]`` containers and lists (SML/Operation).
    pydantic's ``Dict[str, SubmodelElement]`` serializer uses the abstract
    ``SubmodelElement`` schema and drops subclass fields, hence the explicit
    per-child dump here."""
    if isinstance(container, dict):
        return {
            k: _tag_dump(v, concept_sid) if isinstance(v, BaseModel) else v
            for k, v in container.items()
        }
    if isinstance(container, (list, tuple)):
        return [_tag_dump(v) if isinstance(v, BaseModel) else v for v in container]
    return container


def _field_concept_sid(container: BaseModel, field_name: str) -> str:
    """semanticId of the element class of a ``Dict[str, E]`` field (the concept
    semanticId of the multi-cardinality map), or ``""``."""
    try:
        ann = typing.get_type_hints(type(container), include_extras=True).get(field_name)
    except Exception:
        ann = None
    args = typing.get_args(ann) if ann is not None else ()
    if len(args) == 2 and args[0] is str:
        inner = args[1]
        if isinstance(inner, type) and issubclass(inner, SubmodelElement):
            return _element_cls_semantic_id(inner)
    return ""


def _element_cls_semantic_id(cls) -> str:
    """semanticId carried by an element class (``semantic_id`` is a pydantic
    field, so read its default — the class attribute is a raising descriptor
    in pydantic v2.11+)."""
    try:
        f = cls.model_fields.get("semantic_id")
        if f is not None and isinstance(f.default, str):
            return f.default
    except Exception:
        pass
    return ""


def _tag_dump(model: BaseModel, concept_sid: str = "") -> dict:
    """Dump *model* with a ``modelType`` discriminator so revalidation can
    resolve its concrete class.  A *concept_sid* (the containing Dict-map
    field's concept semanticId) is stamped on the dump when the element has
    none — so bare user entries (e.g. ``Property`` in ``Dict[str, Mode]``)
    round-trip back into the right map field."""
    d = {**model.model_dump(), "modelType": type(model).__name__}
    if concept_sid and not d.get("semantic_id"):
        d["semantic_id"] = concept_sid
    return d


def _serialize_element_containers(model: BaseModel, handler) -> Any:
    """Lossless ``model_dump`` for named-field containers.

    pydantic's default serializer uses the *declared* schema for the values of
    ``Dict[str, E]`` / ``List[E]`` fields, so subclass instances inside them
    (e.g. ``Position`` in ``Dict[str, ParameterItem]``) lose their extra
    fields (x/y/yaw).  Re-dump every element-container field from the live
    model via ``_dump_container`` (concrete per-child dump + ``modelType``
    tag), so a dump child's concrete subclass survives a round-trip through
    ``model_dump()``.
    """
    data = handler(model)
    if not isinstance(data, dict):
        return data
    # NOTE: the SML ``value`` and Operation ``input_variable``/... fields have
    # their own per-field serializers; this generic pass additionally covers
    # every named ``Dict[str, E]`` / ``List[E]`` element-container field.
    for fname in type(model).model_fields:
        if fname in _ELEMENT_META_KEYS or fname in (
            "type_value_list_element", "value_type_list_element",
            "semantic_id_list_element", "order_relevant",
        ):
            continue
        ann = _field_annotation(type(model), fname)
        origin = typing.get_origin(ann)
        if origin is dict:
            args = typing.get_args(ann)
            if len(args) == 2 and args[0] is str:
                inner = _resolve_annotation(args[1])
                if isinstance(inner, type) and issubclass(inner, SubmodelElement):
                    data[fname] = _dump_container(getattr(model, fname))
        elif origin in (list, tuple, set):
            args = typing.get_args(ann)
            if args:
                inner = _resolve_annotation(args[0])
                if isinstance(inner, type) and issubclass(inner, SubmodelElement):
                    data[fname] = _dump_container(getattr(model, fname))
    return data


class SubmodelElement(HasSemantics, Referable):
    """Abstract base for all AAS SubmodelElements.

    Every SubmodelElement carries an id_short (from Referable) and
    optional semantic_id / qualifiers (from HasSemantics).  Concrete
    types — Property, Range, SMC, SML, Entity, etc. — inherit from here.
    """

    @model_serializer(mode="wrap")
    def _ser_element_containers(self, handler):
        return _serialize_element_containers(self, handler)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        _ELEMENT_CLASS_REGISTRY[cls.__name__] = cls
        # semanticId is read robustly: a value defined in this class's own
        # body wins (``__dict__`` — still a plain attribute at this point);
        # otherwise the inherited field default from ``model_fields`` is used.
        # (``getattr`` alone fails here: pydantic v2.11+ replaces plain class
        # attributes with raising descriptors once the parent is finalized, so
        # inherited semanticIds would silently never register.)
        _sid = cls.__dict__.get("semantic_id")
        if not isinstance(_sid, str):
            _sid = ""
        if not _sid:
            _field = cls.model_fields.get("semantic_id")
            if _field is not None and isinstance(_field.default, str):
                _sid = _field.default
        if _sid:
            _SEMANTIC_ID_REGISTRY.setdefault(_sid, []).append(cls)


class SubmodelElementCollection(SubmodelElement):
    """An SMC holding named child elements.

    Mirrors basyx ``SubmodelElementCollection``.  Named-field style:
    subclasses hold their children as DIRECT named element fields (field
    name == id_short) and/or ``Dict[str, X]`` dynamic maps.  The base itself
    is metadata-only — a bare SMC is an empty container, so every container
    with children is a subclass that declares them.
    """
    id_short: AasIdString = "SubmodelElementCollection"

    @model_validator(mode="before")
    @classmethod
    def coerce_containers(cls, data):
        return _coerce_container_data(cls, data)

    @model_validator(mode="after")
    def check_submodel_elements(self) -> Any:
        _stamp_container_id_shorts(self)
        for field_name in type(self).model_fields:
            if field_name in ["id_short", "description", "display_name",
                              "semantic_id", "qualifiers",
                              "supplemental_semantic_ids"]:
                continue
            el = getattr(self, field_name)
            assert is_valid_submodel_element(el), \
                f"Field {field_name} is not a valid SubmodelElement"
            # field name == id_short (single canonical name per element) —
            # a named-field child built from a config dict without an explicit
            # id_short would otherwise keep the class default.
            if isinstance(el, SubmodelElement) and el.id_short != field_name:
                setattr(self, field_name, el.model_copy(update={"id_short": field_name}))
        return self


class SubmodelElementList(SubmodelElement):
    """Pydantic model for an AAS SubmodelElementList.

    Wraps an ordered list of submodel elements with list-level AAS metadata
    (semantic_id, description, qualifiers).  The ``value`` field holds the
    actual list items.  ``type_value_list_element``/``value_type_list_element``/
    ``semantic_id_list_element``/``order_relevant`` mirror the basyx
    SubmodelElementList attributes.
    """
    value: List[Any] = []
    id_short: AasIdString = "SubmodelElementList"
    type_value_list_element: Optional[str] = None
    value_type_list_element: Optional[str] = None
    semantic_id_list_element: str = ""
    order_relevant: bool = True

    @field_serializer("value")
    def _ser_value_lossless(self, v, _info):
        return _dump_container(v)

    @model_validator(mode="before")
    @classmethod
    def coerce_containers(cls, data):
        return _coerce_container_data(cls, data)

    @model_validator(mode="after")
    def check_submodel_elements(self) -> Any:
        for field_name in type(self).model_fields:
            if field_name in ["id_short", "description", "display_name",
                              "semantic_id", "qualifiers",
                              "supplemental_semantic_ids",
                              "type_value_list_element",
                              "value_type_list_element",
                              "semantic_id_list_element",
                              "order_relevant"]:
                continue
            assert is_valid_submodel_element(getattr(self, field_name)), \
                f"Field {field_name} is not a valid SubmodelElement"
        return self


class Entity(SubmodelElement):
    """Pydantic model for an AAS Entity.

    Mirrors basyx ``Entity``: an ``entity_type`` (SelfManagedEntity or
    CoManagedEntity), an optional ``global_asset_id`` (required for
    self-managed entities per AASd-014), and child elements as DIRECT named
    fields (named-field style) and/or ``Dict[str, X]`` dynamic maps.  The
    base itself is metadata-only — a bare Entity is an empty container, so
    every Entity with children is a subclass that declares them.
    """
    entity_type: str = "CoManagedEntity"
    id_short: AasIdString = "Entity"
    global_asset_id: str = ""

    @model_validator(mode="before")
    @classmethod
    def coerce_containers(cls, data):
        return _coerce_container_data(cls, data)

    @model_validator(mode="after")
    def check_submodel_elements(self) -> Any:
        _stamp_container_id_shorts(self)
        for field_name in type(self).model_fields:
            if field_name in ["id_short", "description", "display_name",
                              "semantic_id", "qualifiers",
                              "supplemental_semantic_ids", "entity_type",
                              "global_asset_id"]:
                continue
            el = getattr(self, field_name)
            assert is_valid_submodel_element(el), \
                f"Field {field_name} is not a valid SubmodelElement"
            # field name == id_short (single canonical name per element).
            if isinstance(el, SubmodelElement) and el.id_short != field_name:
                setattr(self, field_name, el.model_copy(update={"id_short": field_name}))
        return self


class Operation(SubmodelElement):
    id_short: AasIdString = "Operation"
    input_variable: List[SubmodelElement] = []
    output_variable: List[SubmodelElement] = []
    in_output_variable: List[SubmodelElement] = []

    @field_serializer("input_variable", "output_variable", "in_output_variable")
    def _ser_variables_lossless(self, v, _info):
        return _dump_container(v)


class Capability(SubmodelElement):
    id_short: AasIdString = "Capability"


class Property(SubmodelElement):
    id_short: AasIdString = "Property"
    value: str = ""
    value_type: str = "xs:string"
    value_id: str = ""


class MultiLanguageProperty(SubmodelElement):
    """A MultiLanguageProperty; ``value`` is a lang→text map (basyx LangStringSet)."""
    id_short: AasIdString = "MultiLanguageProperty"
    value: Optional[Dict[str, str]] = None
    value_id: str = ""


class Range(SubmodelElement):
    """A Range element matching basyx (``min``/``max``).

    ``min``/``max`` are Optional — basyx allows open-ended ranges (a bound
    may be unset, e.g. a JSON Schema with only ``minimum``)."""
    id_short: AasIdString = "Range"
    min: Optional[str | int | float] = None
    max: Optional[str | int | float] = None
    value_type: str = "xs:string"


def _aas_json_reference_normalize(data: Any) -> Any:
    """Normalize AAS JSON reference field names (``type``/``keys``) onto the
    strict pydantic names (``type_``/``key``).  Used by ``Key`` and
    ``Reference`` so raw AAS JSON (e.g. RelationshipElement endpoints, AAS
    JSON dumps) coerces cleanly without adding backwards-compat aliases."""
    if isinstance(data, BaseModel):
        return data.model_dump()
    if isinstance(data, dict):
        data = dict(data)
        if "type" in data and "type_" not in data:
            data["type_"] = data.pop("type")
        if "keys" in data and "key" not in data:
            data["key"] = tuple(data.pop("keys"))
    return data


class Key(BaseModel):
    """A key of a Reference, referencing an element in its name space."""
    model_config = {"extra": "forbid"}

    # The AAS KeyType strings basyx accepts (PascalCase, as in AAS JSON and
    # kg-bridge).  ``""`` means "unset" — the converter falls back to
    # ASSET_ADMINISTRATION_SHELL.  basyx's internal ``_``-prefixed members and
    # the spec-only Identifiable/Referable (not in basyx's enum) are omitted.
    type_: Literal[
        "",
        "AnnotatedRelationshipElement",
        "AssetAdministrationShell",
        "BasicEventElement",
        "Blob",
        "Capability",
        "ConceptDescription",
        "DataElement",
        "Entity",
        "EventElement",
        "File",
        "FragmentReference",
        "GlobalReference",
        "MultiLanguageProperty",
        "Operation",
        "Property",
        "Range",
        "ReferenceElement",
        "RelationshipElement",
        "Submodel",
        "SubmodelElement",
        "SubmodelElementCollection",
        "SubmodelElementList",
    ] = ""
    value: str = ""

    @model_validator(mode="before")
    @classmethod
    def normalize_aas_json(cls, data: Any) -> Any:
        return _aas_json_reference_normalize(data)


class Reference(BaseModel):
    """Abstract superclass of ExternalReference and ModelReference.

    Reference to either a model element of the same or another AAS or to an
    external entity.  A reference is an ordered list of keys, each key
    referencing an element.  The complete list of keys may for example be
    concatenated to a path that then gives unique access to an element or
    entity.

    **Constraint AASd-121:** For References the value of Key/type of the
    first key of Reference/keys shall be one of GloballyIdentifiables.
    """
    model_config = {"extra": "forbid"}

    type_: Literal["ModelReference", "ExternalReference"] = "ModelReference"
    key: tuple[Key, ...] = ()
    referred_semantic_id: str = ""

    @model_validator(mode="before")
    @classmethod
    def normalize_aas_json(cls, data: Any) -> Any:
        return _aas_json_reference_normalize(data)

    @model_validator(mode="after")
    def dispatch_concrete(self) -> Any:
        """Dispatch to the concrete subclass matching ``type_`` so AAS-JSON
        input (validated against the base) yields a real
        ModelReference/ExternalReference and ``isinstance`` checks hold."""
        if self.type_ == "ModelReference" and not isinstance(self, ModelReference):
            return ModelReference(**self.model_dump())
        if self.type_ == "ExternalReference" and not isinstance(self, ExternalReference):
            return ExternalReference(**self.model_dump())
        return self


# KeyTypes that may start a ModelReference (AASd-123 — the first key must
# reference an Identifiable).
_AAS_IDENTIFIABLE_KEY_TYPES = frozenset({
    "AssetAdministrationShell", "ConceptDescription", "Submodel",
})

# KeyTypes that may follow the first key of a ModelReference — the
# "fragmented" element types (AAS fragment keys).  GlobalReference /
# FragmentReference are external markers, not model-element references.
_AAS_FRAGMENT_KEY_TYPES = frozenset({
    "AnnotatedRelationshipElement", "BasicEventElement", "Blob", "Capability",
    "DataElement", "Entity", "EventElement", "File", "MultiLanguageProperty",
    "Operation", "Property", "Range", "ReferenceElement",
    "RelationshipElement", "SubmodelElement", "SubmodelElementCollection",
    "SubmodelElementList",
})


class ModelReference(Reference):
    """A Reference to a model element of the same or another AAS."""
    type_: Literal["ModelReference"] = "ModelReference"

    @model_validator(mode="after")
    def _check_model_reference_keys(self) -> Any:
        """Enforce ModelReference key structure (AASd-123): the first key must
        reference an Identifiable, the rest must be fragment element types.
        Empty (unset) placeholder keys are skipped."""
        keys = [k for k in self.key if k.type_]
        if not keys:
            return self
        assert keys[0].type_ in _AAS_IDENTIFIABLE_KEY_TYPES, (
            "The first key of a ModelReference must be an Identifiable "
            f"(AssetAdministrationShell/ConceptDescription/Submodel), got {keys[0].type_!r}"
        )
        for k in keys[1:]:
            assert k.type_ in _AAS_FRAGMENT_KEY_TYPES, (
                "Keys after the first of a ModelReference must be fragment "
                f"element types, got {k.type_!r}"
            )
        return self


class ExternalReference(Reference):
    """A Reference to an external entity (outside the AAS)."""
    type_: Literal["ExternalReference"] = "ExternalReference"

    @model_validator(mode="after")
    def _check_external_reference_keys(self) -> Any:
        """An ExternalReference must have exactly one GlobalReference key.
        Empty (unset) placeholder keys are skipped."""
        keys = [k for k in self.key if k.type_]
        if not keys:
            return self
        assert len(keys) == 1 and keys[0].type_ == "GlobalReference", (
            "An ExternalReference must have exactly one GlobalReference key, "
            f"got {[k.type_ for k in keys]!r}"
        )
        return self


class ReferenceElement(SubmodelElement):
    id_short: AasIdString = "ReferenceElement"
    value: Optional[Reference] = None


class RelationshipElement(SubmodelElement):
    """A RelationshipElement whose endpoints (``first``/``second``) are
    References — mirroring basyx, where both must point at Referable
    elements (subject and object of the relationship)."""
    id_short: AasIdString = "RelationshipElement"
    first: Optional[Reference] = None
    second: Optional[Reference] = None


class File(SubmodelElement):
    """A File element matching basyx (``content_type``/``value``)."""
    id_short: AasIdString = "File"
    content_type: str = ""
    value: str = ""


class Blob(SubmodelElement):
    """A Blob element; ``content_type``/``value`` (aliases ``media_type``/``content``) match basyx."""
    model_config = {"populate_by_name": True}

    id_short: AasIdString = "Blob"
    content_type: str = ""
    value: Optional[bytes] = None


# All concrete SubmodelElement types.  Used by ``is_valid_submodel_element``
# to validate serialized (dict) elements under ``extra="forbid"``.
_CONCRETE_ELEMENT_TYPES: tuple = (
    Property, MultiLanguageProperty, Range, ReferenceElement, RelationshipElement,
    SubmodelElementCollection, SubmodelElementList, File, Blob, Entity,
    Operation, Capability,
)

# Meta keys that are not themselves submodel elements.
_ELEMENT_META_KEYS: frozenset = frozenset({
    "id_short", "description", "display_name", "semantic_id",
    "supplemental_semantic_ids", "qualifiers", "entity_type",
    "global_asset_id",
})


# ═══════════════════════════════════════════════════════════════════════════════
# Raw-dict → SubmodelElement coercion (AAS JSON / config / pydantic dumps)
# ═══════════════════════════════════════════════════════════════════════════════
# The base container fields (``value`` / ``submodel_element``) are typed
# ``Dict[str, SubmodelElement]``.  Raw element dicts (e.g. from a config or an
# AAS JSON dump) are coerced here into concrete element instances before
# pydantic validates the container, so the ``Dict[str, X]`` type check is real.

_ELEMENT_TYPE_BY_MODELTYPE = {
    "Property": Property,
    "MultiLanguageProperty": MultiLanguageProperty,
    "Range": Range,
    "ReferenceElement": ReferenceElement,
    "RelationshipElement": RelationshipElement,
    "File": File,
    "Blob": Blob,
    "Capability": Capability,
    "Operation": Operation,
    "Entity": Entity,
    "SubmodelElementCollection": SubmodelElementCollection,
    "SubmodelElementList": SubmodelElementList,
}


class _PlaceholderId:
    """Deterministic id_short generator for SMC items that carry none."""
    _counter = itertools.count()

    @classmethod
    def next(cls) -> str:
        return f"elem{next(cls._counter)}"


def _resolve_annotation(annotation: Any) -> Any:
    """Strip Annotated/Optional wrappers; strings (forward refs) → None."""
    if isinstance(annotation, str):
        return None
    while typing.get_origin(annotation) is typing.Annotated:
        annotation = typing.get_args(annotation)[0]
    return annotation


def _container_item_type(annotation: Any) -> Any:
    """Dict[str, X] / List[X] → X (or None when unknown)."""
    annotation = _resolve_annotation(annotation)
    origin = typing.get_origin(annotation)
    if origin in (dict, list, set, tuple):
        args = typing.get_args(annotation)
        if args:
            return args[1] if origin is dict and len(args) == 2 else args[0]
    return None


def _infer_model_type(d: dict) -> str:
    """Best-effort inference for dicts without ``modelType`` (pydantic dumps)."""
    v = d.get("value")
    if isinstance(v, list):
        return "SubmodelElementList"
    if isinstance(v, dict):
        if v and all(isinstance(x, dict) for x in v.values()):
            return "SubmodelElementCollection"
        return "MultiLanguageProperty"
    if "statements" in d:
        return "Entity"
    if "min" in d or "max" in d:
        return "Range"
    if "first" in d and "second" in d:
        return "RelationshipElement"
    if "content_type" in d:
        return "File" if isinstance(v, str) else "Blob"
    if "key" in d or "keys" in d:
        return "ReferenceElement"
    if "input_variable" in d or "output_variable" in d:
        return "Operation"
    return "Property"


class _UnknownFieldError(ValueError):
    """Raised by ``_build_element`` when a dict names a field the target
    class does not define — a config/model mistake that must fail LOUDLY
    rather than be swallowed by the coercion fallbacks (which only exist to
    tolerate wrong element *types*, not wrong *field names*)."""


_UNKNOWN_FIELD_MARK = "Unknown field(s)"


def _is_unknown_field_error(e: Exception) -> bool:
    """True when *e* is a config-mistake error: a bare ``_UnknownFieldError``
    or a pydantic ``ValidationError`` that wraps one (a before-validator
    raising it inside ``cls(**d)`` gets converted into a ValidationError, so
    the coercion fallbacks must recognize the wrapped form too and NOT
    swallow it — falling through to a nonsense type inference would only
    produce a misleading error)."""
    if isinstance(e, _UnknownFieldError):
        return True
    return _UNKNOWN_FIELD_MARK in str(e)


def _build_element(cls: type, d: dict) -> Any:
    """Build an element instance from a normalized dict, recursing into
    container children."""
    d = dict(d)
    # Reject unknown keys LOUDLY — a dict that names something the class does
    # not define is a config/model mistake, not something to silently drop
    # (silent drops hid real schema bugs before).  Field names equal the
    # published id_shorts (camelCase) on the regenerated templates; the
    # handwritten base classes (File/Blob/Operation/…) keep their own field
    # names (e.g. ``content_type``) — there is NO snake/camel fallback: a key
    # must name a model field exactly.  Only the dump / AAS-JSON
    # discriminators that are deliberately not model fields are tolerated:
    # ``modelType`` (our own ``_tag_dump`` tag, resolved into the concrete
    # class before we get here) and ``category`` (basyx AAS JSON may carry
    # it, the model does not model it).
    fields = set(cls.model_fields)
    unknown = set(d) - fields
    tolerated = {"modelType", "category"}
    if unknown - tolerated:
        raise _UnknownFieldError(
            f"Unknown field(s) {sorted(unknown - tolerated)} for "
            f"{cls.__name__} — allowed: {sorted(fields)}"
        )
    d = {k: v for k, v in d.items() if k in fields}
    if issubclass(cls, MultiLanguageProperty):
        d = dict(d)
        v = d.get("value")
        if isinstance(v, list):  # AAS JSON: [{language, text}] → lang map
            d["value"] = {
                lang.get("language"): lang.get("text")
                for lang in v if isinstance(lang, dict)
            }
    elif issubclass(cls, SubmodelElementList):
        d = dict(d)
        kids = d.get("value") or []
        if isinstance(kids, list):
            # AASd-114: list items share the list's semanticId, so semanticId
            # resolution would pick the wrong class — target the declared item
            # class explicitly instead (already-typed instances pass through).
            item_tp = getattr(cls, "item_type", None)
            d["value"] = [
                coerce_submodel_element(c, target_type=item_tp) for c in kids
            ]
    elif issubclass(cls, (SubmodelElementCollection, Submodel, Entity)):
        d = dict(d)
        # AAS JSON lists children (``value``/``statements``/
        # ``submodel_element`` as a LIST) — convert to id_short-keyed dicts.
        # Named-field style: the key is only ever injected when it is already
        # present in the dict (a list of children); containers now declare
        # their children as named fields / named Dict maps, so there is no
        # base container field to populate unconditionally.
        for container in ("submodel_element", "statements", "value"):
            kids = d.get(container)
            if isinstance(kids, list):
                d[container] = {
                    (c.get("id_short") or c.get("idShort") or _PlaceholderId.next()): c
                    for c in kids
                    if isinstance(c, dict)
                }
    return cls(**d)


def _concrete_element_targets(target_type: Any) -> list:
    """Concrete (non-abstract) element classes named by a container's
    annotation — used for subclass-specialized ``Dict[str, X]`` containers."""
    if target_type is None:
        return []
    resolved = _resolve_annotation(target_type)
    origin = typing.get_origin(resolved)
    if origin in (typing.Union, _UnionType):
        members = typing.get_args(resolved)
    else:
        members = (resolved,)
    return [
        m for m in members
        if isinstance(m, type) and issubclass(m, SubmodelElement)
        and m is not SubmodelElement
    ]


def coerce_submodel_element(
    value: Any,
    id_short: Optional[str] = None,
    target_type: Optional[type] = None,
) -> Any:
    """Coerce a raw dict (AAS JSON / config / pydantic dump) into a concrete
    SubmodelElement instance.  Already-typed elements pass through unchanged.

    When ``target_type`` names a concrete element type (subclass-specialized
    container, e.g. ``Dict[str, Parameter]``), that type is enforced — a wrong
    element is left raw so pydantic reports the type error.  Otherwise the type
    is inferred from ``modelType`` / keys.
    """
    if isinstance(value, SubmodelElement):
        if (
            target_type is not None
            and isinstance(target_type, type)
            and issubclass(target_type, SubmodelElement)
            and not isinstance(value, target_type)
        ):
            # Upcast a base-class instance to the target subclass (e.g. a bare
            # ``Property`` into ``Dict[str, Mode]``) so the concept semanticId
            # carried by the subclass is applied.  The dump's empty
            # ``semantic_id`` is dropped so the subclass default wins.
            try:
                d = value.model_dump()
                if not d.get("semantic_id"):
                    d.pop("semantic_id", None)
                return _build_element(target_type, d)
            except Exception:
                pass
        return value
    if not isinstance(value, dict):
        return value

    # Keys stay verbatim — ``_build_element`` accepts only exact model field
    # names (the template's original casing), no snake/camel fallback.
    d = dict(value.items())
    if id_short and not d.get("id_short"):
        d["id_short"] = id_short

    concrete = _concrete_element_targets(target_type)
    if concrete:
        # The field's declared type is authoritative for typed fields, but a
        # ``modelType`` discriminator naming a *subclass* of it wins (a
        # subclass-specialized override, e.g. ExtendedSkills vs Skills).  A
        # modelType naming an unrelated same-named class (AID's ``Type`` vs
        # CCI's ``Type`` — the registry is keyed by bare class name) is
        # ignored so the declared type is used.
        mt = d.get("modelType")
        mt_cls = _ELEMENT_CLASS_REGISTRY.get(mt) if mt else None
        if mt_cls is not None and any(
            mt_cls is c or issubclass(mt_cls, c) for c in concrete
        ):
            concrete = [mt_cls]
        if len(concrete) == 1:
            # A single declared type is authoritative — surface build errors
            # LOUDLY (a config mistake must not be hidden behind a raw-dict
            # extra_forbidden cascade).
            return _build_element(concrete[0], d)
        last_unknown = None
        for cls in concrete:
            try:
                return _build_element(cls, d)
            except Exception as e:
                if _is_unknown_field_error(e):
                    last_unknown = e
                # else: wrong element type — try the next candidate
        if last_unknown is not None:
            raise last_unknown
        return value

    # generic container (Dict[str, SubmodelElement]) — a dump's ``modelType``
    # discriminator is authoritative; otherwise a UNIQUE semanticId (config
    # dicts) resolves the concrete class; otherwise infer from keys.
    mt = d.get("modelType")
    if mt:
        cls = _ELEMENT_CLASS_REGISTRY.get(mt) or _ELEMENT_TYPE_BY_MODELTYPE.get(mt)
        if cls is not None:
            try:
                return _build_element(cls, d)
            except Exception as e:
                if _is_unknown_field_error(e):
                    raise
    sid = d.get("semantic_id")
    if isinstance(sid, str) and sid:
        cls = _resolve_semantic_id_cls(sid)
        if cls is not None:
            try:
                return _build_element(cls, d)
            except Exception as e:
                if _is_unknown_field_error(e):
                    raise
    mt = _infer_model_type(d)
    cls = _ELEMENT_CLASS_REGISTRY.get(mt) or _ELEMENT_TYPE_BY_MODELTYPE.get(mt)
    if cls is None:
        return value
    try:
        return _build_element(cls, d)
    except Exception as e:
        if _is_unknown_field_error(e):
            raise
        return value


def _coerce_container_data(cls: Any, data: Any) -> Any:
    """model_validator(mode='before') helper: coerce raw dicts inside ANY
    dynamic container field.

    Named-field style: containers hold their children as DIRECT named fields
    and/or ``Dict[str, X]`` dynamic maps on any field (e.g. ``Variables.
    variable``, ``MqttActions.property_name``, ``Endpoints.endpoint``).  Each
    ``Dict[str, X]`` map is coerced here: every raw dict becomes a concrete
    element instance (targeted at ``X``, or resolved via the dump's
    ``modelType`` discriminator when present), so a dump child's concrete
    subclass (e.g. ``Position`` in ``Dict[str, ParameterItem]``) survives.

    Values-model fields (legacy ``value: MyValues``) are left to pydantic —
    the values model's own ``coerce_values`` before-validator coerces each
    child.  SML ``value`` lists are coerced here too."""
    if isinstance(data, BaseModel):
        data = data.model_dump()
    if not isinstance(data, dict):
        return data
    for key, field in cls.model_fields.items():
        if key not in data:
            continue
        if key in ("id_short", "description", "display_name", "semantic_id",
                   "qualifiers", "supplemental_semantic_ids", "category",
                   "entity_type", "global_asset_id", "type_value_list_element",
                   "value_type_list_element", "semantic_id_list_element",
                   "order_relevant"):
            continue
        field_tp = _resolve_annotation(field.annotation)
        origin = typing.get_origin(field_tp)
        item_tp = _container_item_type(field_tp)
        val = data[key]
        if origin is dict or (item_tp is not None and isinstance(val, dict)):
            default_children = field.default if field.default is not None else None
            if isinstance(default_children, dict):
                merged = dict(val)
                for dk, dv in default_children.items():
                    if dk not in merged:
                        merged[dk] = copy.deepcopy(dv)
                val = merged
            data[key] = {
                k: coerce_submodel_element(
                    v, id_short=k,
                    target_type=(
                        None  # dump children carry modelType → registry resolves
                        if isinstance(v, dict) and "modelType" in v
                        else (
                            type(default_children[k])
                            if isinstance(default_children, dict) and k in default_children
                            else item_tp
                        )
                    ),
                )
                for k, v in val.items()
            }
        elif origin in (list, tuple, set) and isinstance(val, list):
            item_tp = getattr(cls, "item_type", None) or item_tp
            data[key] = [
                coerce_submodel_element(v, target_type=item_tp) for v in val
            ]
        elif isinstance(val, dict):
            # Named element field (e.g. ``Position.y``) given as a raw config
            # dict — coerce via the field's declared type and stamp the field
            # name as id_short (the single canonical name).  Already-typed
            # values pass through unchanged.
            elem_tp = _resolve_annotation(field_tp)
            if typing.get_origin(elem_tp) is typing.Union:
                args = [a for a in typing.get_args(elem_tp) if a is not type(None)]
                if len(args) == 1:
                    elem_tp = args[0]
            if isinstance(elem_tp, type) and issubclass(elem_tp, SubmodelElement):
                # Preserve the field default's metadata (semanticId,
                # supplemental sids, description, value_type, …) when the
                # config overrides a named element field with a raw dict —
                # a field typed with a generic leaf (e.g. ``forms.href:
                # Property`` whose concept sid lives only on the field
                # default) would otherwise lose it, and semanticId-based
                # consumers (back-conversion, semantic extraction) rely on it.
                # The field default is the deep-merge base; config values win;
                # id_short stays the canonical field name (stamped below).
                merged_val = val
                if isinstance(val, dict):
                    default = field.default
                    if default is not None and isinstance(default, SubmodelElement):
                        base = default.model_dump()
                        base.pop("id_short", None)
                        merged_val = {**base, **val}
                data[key] = coerce_submodel_element(
                    merged_val, id_short=key, target_type=elem_tp
                )
    return data


def _field_annotation(cls: Any, name: str) -> Any:
    """Resolved annotation for a model field (handles forward refs)."""
    try:
        hints = typing.get_type_hints(cls, include_extras=True)
        if name in hints:
            return hints[name]
    except Exception:
        pass
    return cls.model_fields[name].annotation


PrimitiveSubmodelElement = int | float | str | bool | bytes


class Submodel(HasSemantics, Identifiable):
    """A Submodel whose children are DIRECT named element fields (named-field
    style) and/or ``Dict[str, X]`` dynamic maps.  The base itself is
    metadata-only — a bare Submodel is an empty submodel, so every Submodel
    with children is a subclass that declares them."""

    @model_serializer(mode="wrap")
    def _ser_element_containers(self, handler):
        return _serialize_element_containers(self, handler)

    @model_validator(mode="before")
    @classmethod
    def coerce_containers(cls, data):
        return _coerce_container_data(cls, data)

    @model_validator(mode="after")
    def check_submodel_elements(self) -> Any:
        _stamp_container_id_shorts(self)
        for field_name in type(self).model_fields:
            if field_name in ["id", "id_short", "description", "display_name",
                              "semantic_id", "qualifiers",
                              "supplemental_semantic_ids"]:
                continue
            el = getattr(self, field_name)
            assert is_valid_submodel_element(el), \
                f"Field {field_name} is not a valid SubmodelElement"
            # field name == id_short (single canonical name per element).
            if isinstance(el, SubmodelElement) and el.id_short != field_name:
                setattr(self, field_name, el.model_copy(update={"id_short": field_name}))
        return self
