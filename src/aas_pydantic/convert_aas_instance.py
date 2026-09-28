from __future__ import annotations

import typing
from pydantic import BaseModel, TypeAdapter

from aas_pydantic import aas_model, convert_util
from basyx.aas import model


from aas_pydantic.convert_util import (
    is_attribute_from_basyx_model_immutable,
    get_semantic_id_value_of_model,
    repatch_id_short_to_temp_attribute,
    unpatch_id_short_from_temp_attribute,
)


def get_types_name_dict(
    types: typing.List[typing.Type[aas_model.AssetAdministrationShell | aas_model.Submodel]],
) -> typing.Dict[str, type]:
    """
    Returns a dictionary with the type names as keys and the types as values.

    Args:
        types (typing.List[type]): List of types to create the dictionary from.

    Returns:
        typing.Dict[str, type]: Dictionary with the type names as keys and the types as values.
    """
    types_name_dict = {t.__name__.split(".")[-1]: t for t in types}
    for top_level_type in types:
        if not issubclass(top_level_type, aas_model.AAS):
            continue
        for attribute_name, attribute_type in top_level_type.model_fields.items():
            annotation = attribute_type.annotation
            if typing.get_origin(annotation) is typing.Annotated:
                annotation = typing.get_args(annotation)[0]
            if typing.get_origin(annotation) is typing.Union:
                for contained_type in typing.get_args(annotation):
                    if typing.get_origin(contained_type) is typing.Annotated:
                        contained_type = typing.get_args(contained_type)[0]
                    if not (isinstance(contained_type, type) and issubclass(contained_type, aas_model.Submodel)):
                        continue
                    types_name_dict[contained_type.__name__.split(".")[-1]] = (
                        contained_type
                    )
                continue
            if not (isinstance(annotation, type) and issubclass(annotation, aas_model.Submodel)):
                continue
            types_name_dict[annotation.__name__.split(".")[-1]] = annotation
    return types_name_dict


def convert_object_store_to_pydantic_models(
    obj_store: model.DictIdentifiableStore, types: typing.List[type]
) -> typing.List[aas_model.AssetAdministrationShell]:
    """
    Converts an object store with AAS and submodels to pydantic models, representing the original data structure.

    Args:
        obj_store (model.DictIdentifiableStore): Object store with AAS and submodels
        types (typing.List[type]): List of types to create the pydantic models from. Can be only top level types.

    Returns:
        typing.List[aas_model.AssetAdministrationShell]: List of pydantic models
    """
    type_name_dict = get_types_name_dict(types)

    pydantic_submodels: typing.List[aas_model.Submodel] = []
    for identifiable in obj_store:
        if not isinstance(identifiable, model.Submodel):
            continue
        class_name = convert_util.get_class_name_from_basyx_model(identifiable)
        if not class_name in type_name_dict:
            pass
        pydantic_submodel = convert_submodel_to_model_instance(
            identifiable, type_name_dict[class_name]
        )
        pydantic_submodels.append(pydantic_submodel)

    pydantic_aas_list: typing.List[aas_model.AssetAdministrationShell] = []
    for identifiable in obj_store:
        if not isinstance(identifiable, model.AssetAdministrationShell):
            continue
        class_name = convert_util.get_class_name_from_basyx_model(identifiable)
        if not class_name in type_name_dict:
            pass
        pydantic_aas = convert_aas_to_pydantic_model_instance(
            identifiable, pydantic_submodels, type_name_dict[class_name]
        )
        pydantic_aas_list.append(pydantic_aas)

    return pydantic_aas_list


def convert_aas_to_pydantic_model_instance(
    aas: model.AssetAdministrationShell,
    pydantic_submodels: typing.List[aas_model.Submodel],
    model_type: type = aas_model.AssetAdministrationShell,
) -> aas_model.AssetAdministrationShell:
    """
    Converts an AAS to a Pydantic model.

    Args:
        aas (model.AssetAdministrationShell): AAS to convert

    Returns:
        aas_model.AssetAdministrationShell: Pydantic model of the asset administration shell
    """
    dict_model_instantiation = get_initial_dict_for_model_instantiation(aas)
    aas_submodel_ids = [sm.get_identifier() for sm in aas.submodel]

    for sm in pydantic_submodels:
        if not sm.id in aas_submodel_ids:
            continue
        attribute_names_of_submodel = (
            convert_util.get_attribute_names_from_basyx_template(aas, sm.id)
        )
        if len(attribute_names_of_submodel) > 1:
            raise ValueError(
                "Multiple attribute names found for submodel:",
                attribute_names_of_submodel,
            )
        attribute_name_of_submodel = attribute_names_of_submodel[0]
        dict_model_instantiation.update({attribute_name_of_submodel: sm.model_dump()})
    return TypeAdapter(model_type).validate_python(dict_model_instantiation)


def get_submodel_element_value(
    sm_element: model.SubmodelElement, attribute_type: type = None
) -> aas_model.SubmodelElement:
    """
    Returns the value of a SubmodelElement.

    Args:
        sm_element (model.SubmodelElement): SubmodelElement to get the value from.

    Returns:
        aas_model.SubmodelElement: Value of the SubmodelElement.
    """
    if isinstance(sm_element, model.SubmodelElementCollection):
        return convert_submodel_collection_to_pydantic_model(
            sm_element, model_type=attribute_type
        )
    elif isinstance(sm_element, model.SubmodelElementList):
        return convert_submodel_list_to_pydantic_model(
            sm_element, model_type=attribute_type
        )
    elif isinstance(sm_element, model.ReferenceElement):
        return convert_reference_element_to_pydantic_model(sm_element)
    elif isinstance(sm_element, model.Property):
        return convert_property_to_pydantic_model(sm_element)
    elif isinstance(sm_element, model.MultiLanguageProperty):
        return convert_multi_language_property_to_pydantic_model(sm_element)
    elif isinstance(sm_element, model.Range):
        return convert_range_to_pydantic_model(sm_element)
    elif isinstance(sm_element, model.RelationshipElement):
        return convert_relationship_element_to_pydantic_model(sm_element)
    elif isinstance(sm_element, model.Capability):
        return convert_capability_to_pydantic_model(sm_element)
    elif isinstance(sm_element, model.Operation):
        return convert_operation_to_pydantic_model(sm_element)
    elif isinstance(sm_element, model.Entity):
        return convert_entity_to_pydantic_model(sm_element, attribute_type)
    elif isinstance(sm_element, model.File):
        return convert_file_to_pydantic_model(sm_element)
    elif isinstance(sm_element, model.Blob):
        return convert_blob_to_pydantic_model(sm_element)
    else:
        raise NotImplementedError("Type not implemented:", type(sm_element))


def get_model_instantiation_dict_from_submodel_element(
    attribute_name: str, attribute_value: typing.Any
) -> typing.Dict[str, typing.Any]:
    """
    Converts a SubmodelElement to a dict.

    Args:
        attribute_name (str): Name of the attribute to create in the dictionary.
        sm_element (model.SubmodelElement): SubmodelElement to convert.

    Returns:
        dict: Dictionary that can be used to instantiate a Pydantic model.
    """
    if isinstance(attribute_value, BaseModel):
        attribute_value = attribute_value.model_dump()
    elif isinstance(attribute_value, (list, set, tuple)) and any(
        isinstance(element, BaseModel) for element in attribute_value
    ):
        attribute_value = [element.model_dump() for element in attribute_value]
    return {attribute_name: attribute_value}


def get_initial_dict_for_model_instantiation(
    basyx_model: (
        model.Submodel
        | model.AssetAdministrationShell
        | model.SubmodelElementCollection
    ),
) -> typing.Dict[str, typing.Any]:
    """
    Returns a dictionary that can be used to instantiate a Pydantic model based on a provided basyx submodel.

    Args:
        basyx_model (model.Submodel | model.AssetAdministrationShell | model.SubmodelElementCollection): Basyx model to create the dictionary from.

    Returns:
        typing.Dict[str, typing.Any]: Dictionary that can be used to instantiate a Pydantic model.
    """
    model_instantiation_dict = {
        "id_short": basyx_model.id_short,
        "description": convert_util.get_str_description(basyx_model.description),
        "display_name": convert_util.get_str_display_name(
            getattr(basyx_model, "display_name", None)
        ),
    }
    if isinstance(basyx_model, model.Identifiable):
        model_instantiation_dict["id"] = str(basyx_model.id)
    if isinstance(basyx_model, model.HasSemantics):
        model_instantiation_dict["semantic_id"] = get_semantic_id_value_of_model(
            basyx_model
        )
    return model_instantiation_dict


def _is_container_style_model(model_type, container_key: str) -> bool:
    """True when a model holds its children in ``Dict[str, X]`` container
    fields (the *container_key* and/or other name-keyed maps) rather than
    named element fields."""
    if not (isinstance(model_type, type) and issubclass(model_type, BaseModel)):
        return False
    try:
        hints = typing.get_type_hints(model_type, include_extras=True)
    except Exception:
        hints = {k: v.annotation for k, v in model_type.model_fields.items()}
    for f, ann in hints.items():
        if f in convert_util.META_FIELDS or f == container_key:
            continue
        if typing.get_origin(ann) is typing.ClassVar:
            continue  # VERSION/REVISION ClassVars are not children
        if typing.get_origin(ann) is not dict:
            return False
    return True


def _resolve_element_cls(
    basyx_el: model.SubmodelElement,
    expected_cls=None,
):
    """Concrete pydantic class for a basyx element.

    ``expected_cls`` (an SML class's ``item_type``) wins — SML items lose their
    semanticId to AASd-114 in basyx, so the list's declared item class is the
    only reliable discriminator.  Otherwise the element's semanticId resolves
    via the registry populated by the generated/handwritten classes
    (type-preserving round-trip); falls back to the base pydantic type for the
    basyx type.  ``None`` for plain leaves (Property, ReferenceElement, …)
    whose semanticId has no registered class.
    """
    if expected_cls is not None:
        return expected_cls
    sid = convert_util.get_semantic_id_value_of_model(basyx_el)
    if sid:
        cls = aas_model._resolve_semantic_id_cls(sid)
        if cls is not None:
            return cls
    if isinstance(basyx_el, model.Entity):
        return aas_model.Entity
    if isinstance(basyx_el, model.SubmodelElementCollection):
        return aas_model.SubmodelElementCollection
    if isinstance(basyx_el, model.SubmodelElementList):
        return aas_model.SubmodelElementList
    return None


def _resolve_values_cls(cls, container_key: str):
    """The values-model class named by *cls*'s *container_key* field (e.g.
    ``EntryNodeValues`` for ``EntryNode.statements``), or ``None``."""
    try:
        hints = typing.get_type_hints(cls, include_extras=True)
        ann = hints.get(container_key)
    except Exception:
        ann = cls.model_fields[container_key].annotation
    return ann if isinstance(ann, type) else None


def _element_cls_sid(cls) -> str:
    """semanticId carried by an element class.  ``semantic_id`` is a pydantic
    *field* (not a ClassVar), so the class attribute is replaced by a raising
    descriptor in pydantic v2.11+ — read the field default instead."""
    try:
        f = cls.model_fields.get("semantic_id")
        if f is not None and isinstance(f.default, str):
            return f.default
    except Exception:
        pass
    return ""


def _element_cls_supplemental(cls) -> list:
    """Supplemental semanticIds carried by an element class (field default)."""
    try:
        f = cls.model_fields.get("supplemental_semantic_ids")
        if f is not None and isinstance(f.default, list):
            return list(f.default)
    except Exception:
        pass
    return []


def _element_supplemental_sids(basyx_el) -> list:
    """Supplemental semanticIds of a basyx element (IRI strings)."""
    out = []
    for ref in (getattr(basyx_el, "supplemental_semantic_id", None) or []):
        if ref is not None and ref.key:
            out.append(ref.key[0].value)
    return out


def _dict_element_classes(ann):
    """Element classes of a ``Dict[str, E]`` annotation.

    A container may accept a UNION of element classes — e.g. the Variables /
    Parameters submodels take ``Union[VariableProp, VariableItem]`` so a
    submodel can mix plain Properties with grouped SMCs in one map. Returns
    every SubmodelElement class named by the annotation (empty when the value
    type is not an element class).
    """
    args = typing.get_args(ann)
    if len(args) != 2 or args[0] not in (str, int):
        return []
    inner = args[1]
    if typing.get_origin(inner) is typing.Union:
        candidates = typing.get_args(inner)
    else:
        candidates = (inner,)
    return [c for c in candidates
            if isinstance(c, type) and issubclass(c, aas_model.SubmodelElement)]


def _multi_fields_by_sid(values_cls):
    """Map element-class semanticId → list of ``Dict[str, E]`` field names of
    the values model.  Every ``Dict[str, E]`` field is a multi-cardinality map;
    the element class carries its concept semanticId, so back-conversion groups
    by that semanticId (the sid now lives on the class instead of a
    ``_multi_cardinality`` ClassVar).  A container accepting a UNION of element
    classes contributes one entry per class semanticId."""
    if values_cls is None:
        return {}
    try:
        hints = typing.get_type_hints(values_cls, include_extras=True)
    except Exception:
        hints = {k: v.annotation for k, v in values_cls.model_fields.items()}
    result = {}
    for fname, ann in hints.items():
        for inner in _dict_element_classes(ann):
            sid = _element_cls_sid(inner)
            if sid:
                result.setdefault(sid, []).append(fname)
    return result


def _multi_element_cls(values_cls, field: str):
    """Element class of a ``Dict[str, E]`` field, or ``None``.

    For a UNION-typed container the first element class is returned; the
    back-conversion path then re-dispatches per element (see
    ``_best_fit_subclass``), so a Property and an SMC can share one map.
    """
    classes = _multi_element_classes(values_cls, field)
    return classes[0] if classes else None


def _multi_element_classes(values_cls, field: str) -> list:
    """ALL element classes a ``Dict[str, E]`` field accepts, or ``[]``.

    A container may be annotated with a union of element classes (e.g.
    ``Union[VariableProp, VariableItem]``) so flat Properties and grouped SMCs
    can share one map. Callers that must pin a single class use
    ``_multi_element_cls``; callers that can dispatch per element use this.
    """
    try:
        hints = typing.get_type_hints(values_cls, include_extras=True)
        return _dict_element_classes(hints.get(field))
    except Exception:
        return []


def _unwrap_optional(ann):
    """Strip ``Optional[...]`` / ``Union[..., None]`` wrappers from an
    annotation, returning the single contained type (or *ann* unchanged)."""
    if typing.get_origin(ann) is typing.Union:
        args = [a for a in typing.get_args(ann) if a is not type(None)]
        if len(args) == 1:
            return args[0]
    return ann


def _has_direct_element_fields(cls) -> bool:
    """True when *cls* carries leaf children as DIRECT named element fields
    (e.g. handwritten ``VariableItem`` with ``variable``/``interface_reference``)
    rather than inside a ``value`` values model / pure Dict container."""
    try:
        hints = typing.get_type_hints(cls, include_extras=True)
    except Exception:
        hints = {k: v.annotation for k, v in cls.model_fields.items()}
    for fname, ann in hints.items():
        if fname in aas_model._ELEMENT_META_KEYS:
            continue
        ann = _unwrap_optional(ann)
        if isinstance(ann, type) and issubclass(ann, aas_model.SubmodelElement):
            return True
    return False


def _dict_field_names(values_cls) -> list:
    """Field names of a ``Dict[str, E]`` container on *values_cls*."""
    if values_cls is None:
        return []
    try:
        hints = typing.get_type_hints(values_cls, include_extras=True)
    except Exception:
        hints = {k: v.annotation for k, v in values_cls.model_fields.items()}
    return [f for f, ann in hints.items()
            if f not in aas_model._ELEMENT_META_KEYS and _dict_element_classes(ann)]


def _container_named_field_data(cls, basyx_children):
    """Children of an SMC whose leaf children are DIRECT named fields (no
    values model): route by ``id_short`` to element-typed fields, by
    semanticId to ``Dict[str, E]`` fields (nested children), remainder flat by
    id_short."""
    try:
        hints = typing.get_type_hints(cls, include_extras=True)
    except Exception:
        hints = {k: v.annotation for k, v in cls.model_fields.items()}
    element_fields = {}
    for fname, ann in hints.items():
        if fname in aas_model._ELEMENT_META_KEYS:
            continue
        ann = _unwrap_optional(ann)
        if isinstance(ann, type) and issubclass(ann, aas_model.SubmodelElement):
            element_fields[fname] = ann
    dict_fields = _multi_fields_by_sid(cls)
    out = {}
    # A class with a single Dict[str, E] container routes any unmatched child
    # there, so a child published without a semanticId still lands in the
    # container instead of being flattened onto the class (and rejected).
    fallback_field = next(iter(
        {f for f in _dict_field_names(cls)}), None) if len(_dict_field_names(cls)) == 1 else None
    for c in basyx_children:
        named = element_fields.get(c.id_short)
        if named is not None:
            out[c.id_short] = _container_element_to_pydantic(c, expected_cls=named)
            continue
        sid = convert_util.get_semantic_id_value_of_model(c)
        fields = dict_fields.get(sid) or []
        if not fields and fallback_field is not None:
            fields = [fallback_field]
        if len(fields) == 1:
            elem_cls = _multi_element_cls(cls, fields[0])
            out.setdefault(fields[0], {})[c.id_short] = _container_element_to_pydantic(
                c, expected_cls=elem_cls
            )
        else:
            out[c.id_short] = _container_element_to_pydantic(c)
    return out


def _best_fit_subclass(cls, basyx_el):
    """A registered subclass of *cls* whose DIRECT named element fields match
    the basyx element's children (structural best-fit).

    Recovers concrete container subclasses (e.g. ``Position`` living in a
    ``Dict[str, ParameterItem]``) when the element's semanticId is a
    config-supplied value not registered to any class — the semanticId can
    therefore not resolve the concrete type, but the child id_shorts can.
    The class matching the most child fields wins; ``None`` when nothing
    fits."""
    if not isinstance(basyx_el, (model.Entity, model.SubmodelElementCollection)):
        return None
    children = {
        c.id_short
        for c in (
            basyx_el.value
            if isinstance(basyx_el, model.SubmodelElementCollection)
            else basyx_el.statement
        )
    }
    if not children:
        return None
    # Direct element field names of the (base) class — the subclass must ADD
    # element fields beyond these (e.g. Position adds x/y/yaw over
    # ParameterItem); inherited/overridden base fields are not distinguishing.
    base_names = _direct_element_field_names(cls)
    best = None
    best_count = -1
    for classes in aas_model._SEMANTIC_ID_REGISTRY.values():
        for cand in classes if isinstance(classes, list) else [classes]:
            if cand is cls or not issubclass(cand, cls):
                continue
            names = _direct_element_field_names(cand)
            added = names - base_names
            if not added or not added <= children or len(added) <= best_count:
                continue
            best = cand
            best_count = len(added)
    return best


def _direct_element_field_names(cls):
    """Direct (named) SubmodelElement-typed field names of *cls* (meta keys
    excluded, Optional unwrapped)."""
    try:
        hints = typing.get_type_hints(cls, include_extras=True)
    except Exception:
        hints = {k: v.annotation for k, v in cls.model_fields.items()}
    names = set()
    for fname, ann in hints.items():
        if fname in aas_model._ELEMENT_META_KEYS:
            continue
        ann = _unwrap_optional(ann)
        if isinstance(ann, type) and issubclass(ann, aas_model.SubmodelElement):
            names.add(fname)
    return names


def _container_data_for(basyx_el, cls):
    """Pydantic data dict for a container element *cls* (SMC/Entity) in the
    named-field style: children map to the DIRECT named fields, nested
    children route into the ``Dict[str, E]`` fields; pure Dict containers
    (no direct fields) route children into their OWN named ``Dict[str, E]``
    map(s) by concept semanticId (or, for a genuinely generic base container
    with no map of its own, the base ``value``/``statements`` fallback)."""
    if isinstance(basyx_el, model.Entity):
        data = {
            **_element_meta(basyx_el),
            "entity_type": (
                "SelfManagedEntity"
                if basyx_el.entity_type is model.EntityType.SELF_MANAGED_ENTITY
                else "CoManagedEntity"
            ),
            "global_asset_id": basyx_el.global_asset_id or "",
        }
        if _has_direct_element_fields(cls):
            data.update(_container_named_field_data(cls, basyx_el.statement))
        else:
            data.update(_container_children_data(basyx_el.statement, cls))
        return data
    if isinstance(basyx_el, model.SubmodelElementCollection):
        if _has_direct_element_fields(cls):
            return {
                **_element_meta(basyx_el),
                **_container_named_field_data(cls, basyx_el.value),
            }
        return {
            **_element_meta(basyx_el),
            **_container_children_data(basyx_el.value, cls),
        }
    return None


def _multi_key_type(values_cls, field: str):
    """Key type (int/str) of a ``Dict[K, E]`` multi field, else ``str``."""
    try:
        hints = typing.get_type_hints(values_cls, include_extras=True)
    except Exception:
        return str
    args = typing.get_args(hints.get(field))
    return args[0] if len(args) == 2 and args[0] in (str, int) else str


def _dict_id_short_to_key(id_short, key_type):
    """Inverse of ``_dict_key_to_id_short``: ``param_01`` → 1 for
    int-keyed fields; strings pass through."""
    if key_type is int:
        try:
            return int(str(id_short).removeprefix("param_"))
        except ValueError:
            return id_short
    return id_short


def _sole_dict_field(values_cls):
    """The single ``Dict[str, E]`` field of *values_cls* (a pure Dict
    container), or ``None`` when there is none / several.  Named-field
    style: every container declares its own map(s) — there are no base
    ``value``/``submodel_element``/``statements`` fallbacks anymore."""
    if values_cls is None:
        return None
    try:
        hints = typing.get_type_hints(values_cls, include_extras=True)
    except Exception:
        hints = {k: v.annotation for k, v in values_cls.model_fields.items()}
    fields = []
    for fname, ann in hints.items():
        if fname in convert_util.META_FIELDS:
            continue
        if typing.get_origin(ann) is dict:
            fields.append(fname)
    return fields[0] if len(fields) == 1 else None


def _container_children_data(basyx_children, values_cls):
    """Group converted basyx children back into the container's values model:
    children are routed to the ``Dict[str, E]`` field whose element class
    carries the child's semanticId (group-then-convert: the field's element
    class is used as the conversion target, so shared semanticIds like CCI/CCT
    ``Skill`` still resolve to the right type).  Unmatched children keep
    ``id_short`` as the field name — or, when the container is a pure
    ``Dict[str, E]`` map (a single Dict field), land in that map."""
    by_sid = _multi_fields_by_sid(values_cls)
    sole_field = _sole_dict_field(values_cls)
    out = {}
    for c in basyx_children:
        sid = convert_util.get_semantic_id_value_of_model(c)
        fields = by_sid.get(sid) or []
        if len(fields) == 1:
            field = fields[0]
        elif len(fields) > 1:
            # semanticId genuinely shared by several fields (e.g. AID's six
            # InterfaceTemplateFor* all use ``.../Interface``) — disambiguate by
            # supplemental semanticIds first (each protocol carries a unique
            # supplemental IRI), then by the child's resolved class, else the
            # first field wins.
            field = None
            child_supp = _element_supplemental_sids(c)
            if child_supp:
                for f in fields:
                    ec = _multi_element_cls(values_cls, f)
                    if ec is not None and _element_cls_supplemental(ec) and set(
                        child_supp
                    ) <= set(_element_cls_supplemental(ec)):
                        field = f
                        break
            if field is None:
                resolved = _container_element_to_pydantic(c).__class__.__name__
                for f in fields:
                    ec = _multi_element_cls(values_cls, f)
                    if ec is not None and ec.__name__ == resolved:
                        field = f
                        break
            if field is None:
                field = fields[0]
        else:
            field = sole_field  # pure Dict container — the map holds children
        if field is not None:
            # A union-typed container (flat Property + grouped SMC in one map)
            # must not pin the first candidate: let the semanticId registry
            # resolve each child to its own class.
            candidates = _multi_element_classes(values_cls, field)
            elem_cls = candidates[0] if len(candidates) == 1 else None
            converted = _container_element_to_pydantic(c, expected_cls=elem_cls)
            key = _dict_id_short_to_key(c.id_short, _multi_key_type(values_cls, field))
            out.setdefault(field, {})[key] = converted
        else:
            out[c.id_short] = _container_element_to_pydantic(c)
    return out


def _container_element_to_pydantic(
    basyx_el: model.SubmodelElement,
    expected_cls=None,
) -> aas_model.SubmodelElement:
    """Convert a basyx element into a pydantic element, resolving the concrete
    class from its semanticId (or an SML's declared item class) — type-covering
    round-trip.  Falls back to a generic container instance on failure.
    """
    cls = _resolve_element_cls(basyx_el, expected_cls)
    if cls is None:
        return get_submodel_element_value(basyx_el, None)
    if isinstance(basyx_el, (model.Entity, model.SubmodelElementCollection)):
        data = _container_data_for(basyx_el, cls)
    elif isinstance(basyx_el, model.SubmodelElementList):
        items = []
        item_cls = getattr(cls, "item_type", None)
        for c in basyx_el.value:
            if isinstance(c, model.SubmodelElementCollection):
                # restore the real id_short, drop the AASd-120 temp attribute
                # (non-mutating — the source store stays intact)
                c = convert_util.unpatched_id_short_smc_copy(c)
            items.append(_container_element_to_pydantic(c, item_cls))
        data = {
            **_element_meta(basyx_el),
            "value": items,
            "type_value_list_element": (
                basyx_el.type_value_list_element.__name__
                if basyx_el.type_value_list_element
                else None
            ),
            "order_relevant": basyx_el.order_relevant,
        }
    else:
        # Leaf class resolved by semanticId (e.g. a typed Property subclass).
        data = get_submodel_element_value(basyx_el, None).model_dump()
    try:
        return cls(**data)
    except Exception as e:  # noqa: BLE001 — before failing, try a registered
        # subclass whose DIRECT named fields match the children (e.g. Position
        # for a ``Dict[str, ParameterItem]`` whose semanticId the config
        # overrode).  If that does not fit either, FAIL LOUDLY — a container
        # that no registered pydantic class can represent is a modeling
        # mistake, not something to degrade into a lossy generic container.
        better = _best_fit_subclass(cls, basyx_el)
        if better is not None:
            try:
                return better(**(_container_data_for(basyx_el, better) or data))
            except Exception:
                pass
        sid = convert_util.get_semantic_id_value_of_model(basyx_el)
        raise ValueError(
            f"Cannot back-convert container '{getattr(basyx_el, 'id_short', '?')}' "
            f"(modelType={type(basyx_el).__name__}, semanticId={sid or '(none)'}): "
            f"no registered pydantic class represents it and the typed build of "
            f"{cls.__name__} failed ({type(e).__name__}: {e}). "
            f"Back-conversion only supports content modeled by the pydantic classes."
        ) from e


def convert_submodel_to_model_instance(
    sm: model.Submodel, model_type: type[aas_model.Submodel] = None
) -> aas_model.Submodel:
    """
    Converts a Submodel to a Pydantic model.

    Args:
        sm (model.Submodel): Submodel to convert.
        model_type (type[aas_model.Submodel]): Pydantic model type to convert the submodel to.

    Returns:
        aas_model.Submodel: Pydantic model of the submodel.
    """
    if model_type is None:
        raise ValueError(
            "convert_submodel_to_model_instance requires model_type — pass the "
            "pydantic Submodel class.  (Legacy template inference from a basyx "
            "Submodel was removed: back-conversion only supports content "
            "modeled by the pydantic classes, which are constructed from the "
            "JSON config templates.)"
        )
    dict_model_instantiation = get_initial_dict_for_model_instantiation(sm)

    if _has_direct_element_fields(model_type):
        # Named-field Submodel — children map to direct named fields and
        # ``Dict[str, E]`` maps by concept semanticId (named-field style).
        dict_model_instantiation.update(
            _container_named_field_data(model_type, sm.submodel_element)
        )
        return TypeAdapter(model_type).validate_python(dict_model_instantiation)

    if _is_container_style_model(model_type, "submodel_element"):
        # Container-style Submodel — children populate its ``Dict[str, X]``
        # field(s), grouped back into multi-cardinality maps by concept
        # semanticId (named-field style: ``Variables.variable``,
        # ``Parameters.parameter``, or the base ``submodel_element`` fallback).
        dict_model_instantiation.update(
            _container_children_data(sm.submodel_element, model_type)
        )
        return TypeAdapter(model_type).validate_python(dict_model_instantiation)

    for sm_element in sm.submodel_element:
        attribute_names = convert_util.get_attribute_names_from_basyx_template(
            sm, sm_element.id_short
        )
        if len(attribute_names) > 1:
            raise ValueError(
                "Multiple attribute names found for submodel element:", attribute_names
            )
        attribute_name = attribute_names[0]
        attribute_type = get_type_of_attribute(model_type, attribute_name)
        attribute_value = get_submodel_element_value(sm_element, attribute_type)
        sme_model_instantiation_dict = (
            get_model_instantiation_dict_from_submodel_element(
                attribute_name, attribute_value
            )
        )
        dict_model_instantiation.update(sme_model_instantiation_dict)
    return TypeAdapter(model_type).validate_python(dict_model_instantiation)


def get_type_of_attribute(
    model_type: typing.Union[type[BaseModel], typing.Union[type[BaseModel]]],
    attribute_name: str,
) -> typing.Union[type[BaseModel]]:
    """
    Returns the type of an attribute of a Pydantic model.

    Tries ``attribute_name`` first, then ``{attribute_name}_ref`` as a fallback.
    The ``_ref`` suffix is used by idta_generate.py to work around a Pydantic
    v2.13.4 bug where circular ``Dict[str, X]`` schema generation crashes when
    a back-reference field name collides with the class holding the Dict
    (e.g. ``properties: Optional['properties']`` → renamed to ``properties_ref``).

    Args:
        model_type (typing.Union[type[BaseModel], typing.Union]): Pydantic model type to get the attribute type from.
        attribute_name (str): Name of the attribute to get the type from.

    Returns:
        typing.Union[type[BaseModel], typing.Union]: Type of the attribute.
    """
    def _find_field(mt, name):
        if hasattr(mt, "model_fields") and name in mt.model_fields:
            return mt.model_fields[name].annotation
        # _ref fallback: Pydantic circular Dict bug workaround (idta_generate.py)
        ref_name = f"{name}_ref"
        if hasattr(mt, "model_fields") and ref_name in mt.model_fields:
            return mt.model_fields[ref_name].annotation
        return None

    if typing.get_origin(model_type) is typing.Union:
        for contained_type in typing.get_args(model_type):
            result = _find_field(contained_type, attribute_name)
            if result is not None:
                return result
    result = _find_field(model_type, attribute_name)
    if result is not None:
        return result
    raise ValueError(
        f"Attribute {attribute_name} not found in model fields with attributes {list(model_type.model_fields.keys())}."
    )


def convert_submodel_collection_to_pydantic_model(
    sm_element: model.SubmodelElementCollection,
    model_type: type[aas_model.SubmodelElementCollection],
) -> aas_model.SubmodelElementCollection:
    """
    Converts a SubmodelElementCollection to a Pydantic model.

    Args:
        sm_element (model.SubmodelElementCollection): SubmodelElementCollection to convert.

    Returns:
        aas_model.SubmodelElementCollection: Pydantic model of the submodel element collection.
    """
    dict_model_instantiation = get_initial_dict_for_model_instantiation(sm_element)

    if _is_container_style_model(model_type, "value"):
        # Container-style SMC — children populate ``value`` keyed by id_short.
        dict_model_instantiation["value"] = {
            el.id_short: _container_element_to_pydantic(el)
            for el in sm_element.value
        }
        return TypeAdapter(model_type).validate_python(dict_model_instantiation)

    for sub_sm_element in sm_element.value:
        attribute_names = convert_util.get_attribute_names_from_basyx_template(
            sm_element, sub_sm_element.id_short
        )
        if len(attribute_names) > 1:
            raise ValueError(
                "Multiple attribute names found for submodel element:", attribute_names
            )
        attribute_name = attribute_names[0]
        attribute_type = get_type_of_attribute(model_type, attribute_name)
        attribute_value = get_submodel_element_value(sub_sm_element, attribute_type)
        dict_sme_instantiation = get_model_instantiation_dict_from_submodel_element(
            attribute_name, attribute_value
        )
        dict_model_instantiation.update(dict_sme_instantiation)
    return TypeAdapter(model_type).validate_python(dict_model_instantiation)


def convert_submodel_list_to_pydantic_model(
    sm_element: model.SubmodelElementList, model_type: type[typing.Any]
) -> typing.Union[
    typing.List[aas_model.SubmodelElement],
    typing.Set[aas_model.SubmodelElement],
    typing.Tuple[aas_model.SubmodelElement],
]:
    """
    Converts a SubmodelElementList to a Pydantic model.

    Args:
        sm_element (model.SubmodelElementList): SubmodelElementList to convert.

    Returns:
        typing.List[aas_model.SubmodelElement]: List of Pydantic models of the submodel elements.
    """
    sme_pydantic_models = []
    item_type = _sml_item_type(model_type)
    for sme in sm_element.value:
        if isinstance(sme, model.SubmodelElementCollection):
            new_sme = unpatch_id_short_from_temp_attribute(sme)
            item = convert_submodel_collection_to_pydantic_model(
                new_sme, model_type=item_type
            )
            repatch_id_short_to_temp_attribute(sme, new_sme)
            sme_pydantic_models.append(item)
        else:
            sme_pydantic_models.append(
                get_submodel_element_value(sme, attribute_type=item_type)
            )

    # Field typed as a SubmodelElementList subclass (template pattern) → build
    # an SML instance carrying the converted items + list metadata.
    if (
        model_type is not None
        and isinstance(model_type, type)
        and issubclass(model_type, aas_model.SubmodelElementList)
    ):
        dumped = [
            e.model_dump() if isinstance(e, BaseModel) else e
            for e in sme_pydantic_models
        ]
        return TypeAdapter(model_type).validate_python(
            {
                "id_short": sm_element.id_short,
                "description": convert_util.get_str_description(sm_element.description),
                "display_name": convert_util.get_str_display_name(
                    getattr(sm_element, "display_name", None)
                ),
                "semantic_id": convert_util.get_semantic_id_value_of_model(sm_element),
                "value": dumped,
                "type_value_list_element": (
                    sm_element.type_value_list_element.__name__
                    if sm_element.type_value_list_element
                    else None
                ),
                "order_relevant": sm_element.order_relevant,
            }
        )

    if not sm_element.order_relevant:
        return set(sme_pydantic_models)
    if model_type is tuple:
        return tuple(sme_pydantic_models)
    return sme_pydantic_models


def _list_item_type(model_type: type[typing.Any]) -> type:
    """Return the item type of a subscripted list/set/tuple annotation,
    falling back to the model type itself when not subscripted."""
    args = typing.get_args(model_type)
    return args[0] if args else model_type


def _sml_item_type(model_type: type[typing.Any]) -> type:
    """Item type for an SML field.

    - For a ``List[X]``-typed field: the element ``X``.
    - For a ``SubmodelElementList`` subclass: the annotation of its ``value``
      field (e.g. ``List[Property]`` → ``Property``).
    """
    if model_type is not None and isinstance(model_type, type) and issubclass(
        model_type, aas_model.SubmodelElementList
    ):
        ann = model_type.model_fields["value"].annotation
        args = typing.get_args(ann)
        return args[0] if args else aas_model.SubmodelElement
    return _list_item_type(model_type)


def _convert_basyx_reference_to_pydantic(
    basyx_ref: model.Reference,
) -> aas_model.Reference:
    """Convert a basyx Reference (ModelReference or ExternalReference)
    to the corresponding aas_pydantic Reference."""
    keys = tuple(
        aas_model.Key(
            type_=convert_util.key_type_from_basyx_name(k.type.name),
            value=k.value,
        )
        for k in basyx_ref.key
    )
    cls = (
        aas_model.ModelReference
        if isinstance(basyx_ref, model.ModelReference)
        else aas_model.ExternalReference
    )
    return cls(key=keys)


_QUALIFIER_KIND_MAP = {
    "CONCEPT_QUALIFIER": "ConceptQualifier",
    "TEMPLATE_QUALIFIER": "TemplateQualifier",
}


def _convert_basyx_qualifiers(basyx_qualifiers: typing.Iterable[model.Qualifier]) -> list:
    """Convert basyx Qualifiers to aas_pydantic Qualifiers."""
    result = []
    for q in basyx_qualifiers or ():
        result.append(
            aas_model.Qualifier(
                type_=q.type,
                value="" if q.value is None else str(q.value),
                value_type=convert_util.convert_basyx_value_type_to_xsd(q.value_type),
                semantic_id=(
                    convert_util.get_semantic_id_value_of_model(q)
                    if q.semantic_id
                    else ""
                ),
                kind=_QUALIFIER_KIND_MAP.get(q.kind.name, str(q.kind.name)),
            )
        )
    return result


def _element_meta(basyx_el: model.SubmodelElement) -> typing.Dict[str, typing.Any]:
    """Common metadata (id_short, description, display_name, semantic_id,
    qualifiers) shared by all basyx submodel elements."""
    return {
        "id_short": basyx_el.id_short,
        "description": convert_util.get_str_description(basyx_el.description),
        "display_name": convert_util.get_str_display_name(
            getattr(basyx_el, "display_name", None)
        ),
        "semantic_id": convert_util.get_semantic_id_value_of_model(basyx_el),
        "qualifiers": _convert_basyx_qualifiers(
            getattr(basyx_el, "qualifier", None) or ()
        ),
    }


def convert_reference_element_to_pydantic_model(
    sm_element: model.ReferenceElement,
) -> aas_model.ReferenceElement:
    """
    Converts a basyx ReferenceElement to an aas_pydantic ReferenceElement.

    Args:
        sm_element (model.ReferenceElement): Basyx ReferenceElement to convert.

    Returns:
        aas_model.ReferenceElement: Pydantic model of the ReferenceElement.
    """
    return aas_model.ReferenceElement(
        **_element_meta(sm_element),
        value=_convert_basyx_reference_to_pydantic(sm_element.value)
        if sm_element.value
        else None,
    )


def convert_property_to_pydantic_model(
    sm_element: model.Property,
) -> aas_model.Property:
    """
    Converts a basyx Property to an aas_pydantic Property.

    Args:
        sm_element (model.Property): Basyx Property to convert.

    Returns:
        aas_model.Property: Pydantic model of the Property.
    """
    return aas_model.Property(
        **_element_meta(sm_element),
        value="" if sm_element.value is None else str(sm_element.value),
        value_type=convert_util.convert_basyx_value_type_to_xsd(sm_element.value_type),
    )


def convert_multi_language_property_to_pydantic_model(
    sm_element: model.MultiLanguageProperty,
) -> aas_model.MultiLanguageProperty:
    """
    Converts a basyx MultiLanguageProperty to an aas_pydantic MultiLanguageProperty.

    ``value`` carries the full lang→text map (basyx LangStringSet).
    """
    return aas_model.MultiLanguageProperty(
        **_element_meta(sm_element),
        value=dict(sm_element.value) if sm_element.value else None,
    )


def convert_range_to_pydantic_model(sm_element: model.Range) -> aas_model.Range:
    """
    Converts a basyx Range to an aas_pydantic Range.
    """
    return aas_model.Range(
        **_element_meta(sm_element),
        min=sm_element.min,
        max=sm_element.max,
        value_type=convert_util.convert_basyx_value_type_to_xsd(sm_element.value_type),
    )


def convert_relationship_element_to_pydantic_model(
    sm_element: model.RelationshipElement,
) -> aas_model.RelationshipElement:
    """
    Converts a basyx RelationshipElement to an aas_pydantic RelationshipElement.
    """
    return aas_model.RelationshipElement(
        **_element_meta(sm_element),
        first=_convert_basyx_reference_to_pydantic(sm_element.first),
        second=_convert_basyx_reference_to_pydantic(sm_element.second),
    )


def convert_capability_to_pydantic_model(
    sm_element: model.Capability,
) -> aas_model.Capability:
    """
    Converts a basyx Capability to an aas_pydantic Capability.
    """
    return aas_model.Capability(**_element_meta(sm_element))


def convert_operation_to_pydantic_model(
    sm_element: model.Operation,
) -> aas_model.Operation:
    """
    Converts a basyx Operation to an aas_pydantic Operation.

    basyx-python-sdk stores the operation variables as bare SubmodelElements
    directly in the ``input_variable`` / ``output_variable`` /
    ``in_output_variable`` NamespaceSets — there is NO ``OperationVariable``
    wrapper in-memory (the wrapper only appears in the AAS JSON wire format,
    which basyx's own (de)serializer handles).  The pydantic model mirrors
    that: ``Operation.input_variable`` etc. are ``List[SubmodelElement]``.
    """
    def _convert_vars(variables) -> list:
        result = []
        for var in variables or ():
            result.append(get_submodel_element_value(var))
        return result

    return aas_model.Operation(
        **_element_meta(sm_element),
        input_variable=_convert_vars(sm_element.input_variable),
        output_variable=_convert_vars(sm_element.output_variable),
        in_output_variable=_convert_vars(sm_element.in_output_variable),
    )


def convert_entity_to_pydantic_model(
    sm_element: model.Entity,
    model_type: type = None,
) -> aas_model.Entity:
    """
    Converts a basyx Entity to an aas_pydantic Entity.

    Entity statements are mapped onto the named fields of the pydantic
    Entity subclass (like a SubmodelElementCollection).
    """
    if model_type is None:
        model_type = aas_model.Entity
    dict_model_instantiation = get_initial_dict_for_model_instantiation(sm_element)
    dict_model_instantiation["entity_type"] = (
        str(sm_element.entity_type.value) if sm_element.entity_type else ""
    )
    dict_model_instantiation["qualifiers"] = _convert_basyx_qualifiers(
        getattr(sm_element, "qualifier", None) or ()
    )
    for sub_sm_element in sm_element.statement:
        attribute_names = convert_util.get_attribute_names_from_basyx_template(
            sm_element, sub_sm_element.id_short
        )
        if len(attribute_names) > 1:
            raise ValueError(
                "Multiple attribute names found for submodel element:", attribute_names
            )
        attribute_name = attribute_names[0]
        attribute_type = get_type_of_attribute(model_type, attribute_name)
        attribute_value = get_submodel_element_value(sub_sm_element, attribute_type)
        dict_sme_instantiation = get_model_instantiation_dict_from_submodel_element(
            attribute_name, attribute_value
        )
        dict_model_instantiation.update(dict_sme_instantiation)
    return TypeAdapter(model_type).validate_python(dict_model_instantiation)


def convert_file_to_pydantic_model(sm_element: model.File) -> aas_model.File:
    """
    Convert a File to a pydantic model

    Args:
        sm_element (model.File): Basyx File to convert.

    Returns:
        aas_model.File: Pydantic model of the file
    """
    return aas_model.File(
        **_element_meta(sm_element),
        content_type=sm_element.content_type,
        value=sm_element.value,
    )


def convert_blob_to_pydantic_model(sm_element: model.Blob) -> aas_model.Blob:
    """
    Convert a Blob to a pydantic model

    Args:
        sm_element (model.Blob): Basyx Blob to convert.

    Returns:
        aas_model.Blob: Pydantic model of the Blob
    """
    return aas_model.Blob(
        **_element_meta(sm_element),
        content_type=sm_element.content_type,
        value=sm_element.value,
    )
