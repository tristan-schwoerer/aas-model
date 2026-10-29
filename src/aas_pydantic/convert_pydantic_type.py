"""A pydantic submodel class as the AAS submodel template it describes: the inverse of ``idta_generate.py``.

The template is what the class would have been generated from (scripts/README.md, "Generated model behavior"):

- every element carries its ``SMT/Cardinality``: a required field is ``One``, an optional one ``ZeroToOne``,
  a map (``Dict[str, X]``) one element, named by its class or a placeholder (``Skill__00__``), that is
  ``ZeroToMany``/``OneToMany``/``TwoToMany`` by its minimum (``Recursive`` where it contains itself) with
  its ``AllowedIdShort``; a member of ``IDTA_ONE_OF`` is mandatory, as templates write alternatives;
- a list is a SubmodelElementList with one example item, its list attributes kept;
- a leaf keeps its semanticId, supplementalSemanticIds, description, displayName (``TEMPLATE_DISPLAY_NAME``,
  which labels the template element and not its instances), valueType, contentType,
  its default value as the example and ``FORM_CHOICES``/``ALLOWED_RANGE`` as ``FormChoices`` and
  ``SMT/AllowedRange``;
- a class's base classes are part of it: a template is complete, not a delta to the one it extends.

Templates are for readers of the AAS: they carry no Python class names.
"""

from __future__ import annotations

import re
import typing
from typing import Any, Optional

from basyx.aas import model
from basyx.aas.model import datatypes
from basyx.aas.model.datatypes import XSD_TYPE_CLASSES, from_xsd
from pydantic import BaseModel

from aas_pydantic import aas_model, convert_util
from aas_pydantic.convert_pydantic_model import _make_basyx_reference, _make_external_reference, _make_qualifiers

# Fields of an element that are its metadata or value, not child elements.
_NOT_CHILDREN = frozenset({
    *convert_util.META_FIELDS, "value", "value_type", "value_id", "content_type", "min", "max", "first", "second",
    "entity_type", "global_asset_id", "type_value_list_element", "value_type_list_element",
    "semantic_id_list_element", "order_relevant", "input_variable", "output_variable", "in_output_variable",
})
_GENERIC_ID_SHORT = aas_model.SubmodelElementCollection.model_fields["id_short"].default
_MAP_CARDINALITY = {0: "ZeroToMany", 1: "OneToMany", 2: "TwoToMany"}
# Where a template has to name a global asset but an example would mislead (AASd-014).
_INTENTIONALLY_EMPTY = "https://admin-shell.io/SMT/General/IntentionallyEmpty"


def convert_model_to_submodel_template(model_type: type[aas_model.Submodel], identifier: str) -> model.Submodel:
    """The submodel template ``model_type`` describes, under the id ``identifier``."""
    prototype = model_type.model_construct()
    version, revision = getattr(model_type, "VERSION", ""), getattr(model_type, "REVISION", "")
    return model.Submodel(
        id_=identifier,
        id_short=prototype.id_short or model_type.__name__,
        kind=model.ModellingKind.TEMPLATE,
        semantic_id=convert_util.get_semantic_id(prototype),
        supplemental_semantic_id=_supplemental(prototype),
        description=convert_util.get_basyx_description_from_model(prototype),
        display_name=_display_name(model_type, prototype),
        administration=model.AdministrativeInformation(version=version, revision=revision)
        if version and revision else None,
        submodel_element=_children(model_type, (model_type,)),
    )


# ── Children ─────────────────────────────────────────────────────────────────

def _children(cls: type, stack: tuple) -> list:
    one_of = set(getattr(cls, "IDTA_ONE_OF", ()))
    children = []
    for name, field in cls.model_fields.items():
        if name in _NOT_CHILDREN or name.startswith("_"):
            continue
        annotation = aas_model._resolve_annotation(aas_model._field_annotation(cls, name))
        element = _child(cls, name, field, annotation, stack, name in one_of)
        if element is not None:
            children.append(element)
    return children


def _child(cls: type, name: str, field, annotation: Any, stack: tuple, one_of: bool):
    id_short = aas_model._aas_field_name(cls, name)
    extra = field.json_schema_extra if isinstance(field.json_schema_extra, dict) else {}
    if typing.get_origin(annotation) is dict:
        item_cls = _element_class(aas_model._container_item_type(annotation))
        if item_cls is None:
            return None
        minimum = 1 if one_of else extra.get("idta_min_cardinality", 0)
        recursive = _recurses(item_cls, stack)
        cardinality = extra.get("idta_cardinality") or _MAP_CARDINALITY.get(minimum, "OneToMany")
        default = item_cls.model_fields["id_short"].default
        named = isinstance(default, str) and default and default != _generic_id_short(item_cls)
        element = _element(item_cls, default if named else f"{id_short}__00__", stack, recursive)
        qualifiers = [_cardinality(cardinality)]
        if extra.get("idta_allowed_id_short"):
            # IDTA writes an optional part in brackets (``Time[\d{2,3}]``).
            pattern = re.sub(r"\((.+)\)\?$", r"[\1]", extra["idta_allowed_id_short"])
            qualifiers.append(_qualifier("AllowedIdShort", pattern))
        return _qualified(element, qualifiers)
    element_cls = _element_class(annotation)
    if element_cls is None:
        return None
    required = field.is_required() or one_of
    recursive = _recurses(element_cls, stack)
    element = _element(element_cls, id_short, stack, recursive, default=field.default)
    return _qualified(element, [_cardinality("One" if required else "ZeroToOne")])


def _recurses(cls: type, stack: tuple) -> bool:
    """Whether ``cls`` is the kind of element one it is nested in is: they share a class of their own (a data
    schema's ``items`` in an action's input schema: both are data schemas). The template then names it without
    repeating its children, as IDTA templates write a recursive definition. The base layer's generic classes make
    no kinship."""
    own = _own_classes(cls)
    return any(own & _own_classes(outer) for outer in stack)


def _own_classes(cls: type) -> set:
    return {base for base in cls.__mro__
            if isinstance(base, type) and issubclass(base, aas_model.SubmodelElement)
            and base.__module__ != aas_model.__name__}


def _element_class(annotation: Any) -> Optional[type]:
    """The element class a field holds: the first member of a union (a template names one element)."""
    annotation = aas_model._resolve_annotation(annotation)
    if typing.get_origin(annotation) in (typing.Union, aas_model._UnionType):
        members = [a for a in typing.get_args(annotation) if isinstance(a, type) and a is not type(None)]
        annotation = members[0] if members else None
    if isinstance(annotation, type) and issubclass(annotation, aas_model.SubmodelElement):
        return annotation
    return None


def _generic_id_short(cls: type) -> str:
    """The id_short default of the base element class ``cls`` derives from (``Property``, …)."""
    for base in cls.__mro__:
        if base.__module__ == aas_model.__name__ and "id_short" in base.model_fields:
            return base.model_fields["id_short"].default
    return _GENERIC_ID_SHORT


# ── Elements ─────────────────────────────────────────────────────────────────

def _element(cls: type, id_short: Optional[str], stack: tuple, recursive: bool = False, default: Any = None):
    """The template element of ``cls`` (its children unless it recurses into itself)."""
    prototype = default if isinstance(default, cls) else cls.model_construct()
    common = dict(
        id_short=id_short,
        semantic_id=convert_util.get_semantic_id(prototype),
        supplemental_semantic_id=_supplemental(prototype),
        description=convert_util.get_basyx_description_from_model(prototype),
        display_name=_display_name(cls, prototype),
        qualifier=_make_qualifiers(getattr(prototype, "qualifiers", None) or []) + _restrictions(cls),
    )
    children = [] if recursive else None
    if issubclass(cls, aas_model.SubmodelElementList):
        return _list(cls, prototype, common, stack, recursive)
    if issubclass(cls, aas_model.Entity):
        self_managed = prototype.entity_type == "SelfManagedEntity"
        return model.Entity(
            entity_type=model.EntityType.SELF_MANAGED_ENTITY if self_managed else model.EntityType.CO_MANAGED_ENTITY,
            global_asset_id=(prototype.global_asset_id or _INTENTIONALLY_EMPTY) if self_managed else None,
            statement=children if recursive else _children(cls, stack + (cls,)), **common)
    if issubclass(cls, aas_model.SubmodelElementCollection):
        return model.SubmodelElementCollection(
            value=children if recursive else _children(cls, stack + (cls,)), **common)
    if issubclass(cls, aas_model.Property):
        value_type = XSD_TYPE_CLASSES.get(prototype.value_type, datatypes.String)
        return model.Property(value_type=value_type, value=_value(prototype.value, value_type), **common)
    if issubclass(cls, aas_model.MultiLanguageProperty):
        return model.MultiLanguageProperty(value=model.MultiLanguageTextType(prototype.value)
                                           if prototype.value else None, **common)
    if issubclass(cls, aas_model.Range):
        value_type = XSD_TYPE_CLASSES.get(prototype.value_type, datatypes.String)
        return model.Range(value_type=value_type, min=_value(prototype.min, value_type),
                           max=_value(prototype.max, value_type), **common)
    if issubclass(cls, aas_model.File):
        return model.File(content_type=prototype.content_type or None, value=prototype.value or None, **common)
    if issubclass(cls, aas_model.Blob):
        return model.Blob(content_type=prototype.content_type or None, value=prototype.value or None, **common)
    if issubclass(cls, aas_model.ReferenceElement):
        return model.ReferenceElement(value=_make_basyx_reference(prototype.value) if prototype.value else None,
                                      **common)
    if issubclass(cls, aas_model.RelationshipElement):
        empty = model.ExternalReference((model.Key(model.KeyTypes.GLOBAL_REFERENCE, _INTENTIONALLY_EMPTY),))
        return model.RelationshipElement(
            first=_make_basyx_reference(prototype.first) if prototype.first else empty,
            second=_make_basyx_reference(prototype.second) if prototype.second else empty, **common)
    if issubclass(cls, aas_model.Capability):
        return model.Capability(**common)
    if issubclass(cls, aas_model.Operation):
        return model.Operation(**common)
    raise TypeError(f"{cls.__name__} is no element a template can hold")


def _list(cls: type, prototype, common: dict, stack: tuple, recursive: bool) -> model.SubmodelElementList:
    item_cls = getattr(cls, "item_type", None)
    item_cls = item_cls if isinstance(item_cls, type) and issubclass(item_cls, aas_model.SubmodelElement) else None
    declared = prototype.type_value_list_element
    type_value = (getattr(model, declared) if isinstance(declared, str) else declared) if declared else (
        _basyx_class(item_cls) or model.SubmodelElementCollection)
    value_type = prototype.value_type_list_element
    # An example item where the item is described: a container, or a leaf with a semanticId of its own.
    items = []
    described = item_cls is not None and (
        issubclass(item_cls, (aas_model.SubmodelElementCollection, aas_model.Entity))
        or item_cls.model_fields["semantic_id"].default)
    if described and not recursive and not _recurses(item_cls, stack):
        item = _element(item_cls, None, stack + (cls,))
        items = [_qualified(item, [_cardinality(getattr(cls, "ITEM_CARDINALITY", "") or "One")])]
    if value_type is None and item_cls is not None and "value_type" in item_cls.model_fields:
        value_type = item_cls.model_fields["value_type"].default  # AASd-109: a list of values declares their type
    return model.SubmodelElementList(
        type_value_list_element=type_value,
        value_type_list_element=XSD_TYPE_CLASSES.get(value_type, value_type) if isinstance(value_type, str)
        else value_type,
        semantic_id_list_element=_make_external_reference(prototype.semantic_id_list_element)
        if prototype.semantic_id_list_element else None,
        order_relevant=prototype.order_relevant, value=items, **common)


def _basyx_class(cls: Optional[type]) -> Optional[type]:
    from aas_pydantic.convert_pydantic_model import _aas_cls_to_basyx
    return _aas_cls_to_basyx(cls) if cls is not None else None


# ── Metadata ─────────────────────────────────────────────────────────────────

def _display_name(cls: type, prototype: BaseModel) -> Optional[model.MultiLanguageNameType]:
    names = getattr(prototype, "display_name", None) or getattr(cls, "TEMPLATE_DISPLAY_NAME", None)
    return model.MultiLanguageNameType(dict(names)) if names else None


def _supplemental(prototype: BaseModel) -> list:
    return [_make_external_reference(s) for s in (getattr(prototype, "supplemental_semantic_ids", None) or [])]


def _value(lexical: Any, value_type):
    """A default value, typed as its value type (none when empty)."""
    if lexical in (None, ""):
        return None
    if isinstance(lexical, bool):
        lexical = "true" if lexical else "false"
    try:
        return from_xsd(str(lexical), value_type)
    except (ValueError, TypeError) as error:
        raise ValueError(f"the default {lexical!r} is not a {value_type.__name__}") from error


def _qualifier(type_: str, value: str) -> model.Qualifier:
    return model.Qualifier(type_, datatypes.String, value=value, kind=model.QualifierKind.TEMPLATE_QUALIFIER)


def _cardinality(value: str) -> model.Qualifier:
    return _qualifier("SMT/Cardinality", value)


def _restrictions(cls: type) -> list:
    """A Property's value restrictions as the template qualifiers they come from."""
    qualifiers = []
    if getattr(cls, "FORM_CHOICES", ()):
        qualifiers.append(_qualifier("FormChoices", ";".join(cls.FORM_CHOICES)))
    if getattr(cls, "ALLOWED_RANGE", ()):
        qualifiers.append(_qualifier("SMT/AllowedRange", f"[{cls.ALLOWED_RANGE[0]}, {cls.ALLOWED_RANGE[1]}]"))
    return qualifiers


def _qualified(element, qualifiers: list):
    """``element`` with ``qualifiers`` first (its cardinality leads, as templates write it)."""
    existing = list(element.qualifier)
    element.qualifier.clear()
    for qualifier in (*qualifiers, *existing):
        element.qualifier.add(qualifier)
    return element
