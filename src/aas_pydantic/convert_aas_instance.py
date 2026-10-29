from __future__ import annotations

import typing
from pydantic import BaseModel, TypeAdapter

from aas_pydantic import aas_model, convert_util
from basyx.aas import model
from basyx.aas.model import datatypes


from aas_pydantic.convert_util import (
    get_semantic_id_value_of_model,
)


def convert_store_to_model(
    obj_store: model.DictIdentifiableStore, model_type: type[aas_model.AAS], aas_id: typing.Optional[str] = None,
) -> aas_model.AAS:
    """The AAS in ``obj_store`` (the one with ``aas_id``, or its only one) as ``model_type``, or the subclass of it
    its class marker names (a ``CappingStation`` read as a ``Resource``), with its submodels.

    The shell's markers name the field holding each submodel; a submodel is that field's class, or the subclass
    of it its own class marker names (an ``OperationalMqttInterfaces`` in a ``DmpAssetInterfacesDescription``
    field). The asset's type, specific asset ids and the template the AAS derives from are read back too."""
    shells = [o for o in obj_store if isinstance(o, model.AssetAdministrationShell)
              and (aas_id is None or o.id == aas_id)]
    if len(shells) != 1:
        raise ValueError(f"expected one AAS{f' with id {aas_id}' if aas_id else ''}, found {len(shells)}")
    shell = shells[0]
    model_type = _marked_subclass(model_type, shell)
    by_id = {o.id: o for o in obj_store}
    data = get_initial_dict_for_model_instantiation(shell)
    info = shell.asset_information
    if info.asset_type:
        data["asset_type"] = str(info.asset_type)
    if info.specific_asset_id:
        data["specific_asset_ids"] = {sid.name: sid.value for sid in info.specific_asset_id}
    if shell.derived_from is not None:
        data["derived_from"] = shell.derived_from.key[0].value
    for reference in shell.submodel:
        submodel = by_id.get(reference.key[0].value)
        if submodel is None:
            continue
        [field] = convert_util.get_attribute_name_from_basyx_model(shell, submodel.id)
        data[field] = convert_submodel_to_model_instance(submodel, _submodel_class(model_type, field, submodel))
    return _validated(model_type, data)


def _submodel_class(model_type: type, field: str, submodel: model.Submodel) -> type:
    """The class of the submodel a field holds: the field's, or the subclass of it the submodel's class marker
    names."""
    annotation = aas_model._resolve_annotation(aas_model._field_annotation(model_type, field))
    members = typing.get_args(annotation) if typing.get_origin(annotation) in (typing.Union, aas_model._UnionType) \
        else (annotation,)
    declared = [m for m in members if isinstance(m, type) and issubclass(m, aas_model.Submodel)]
    if len(declared) != 1:
        raise ValueError(f"{model_type.__name__}.{field} holds no single submodel class")
    return _marked_subclass(declared[0], submodel)


def _marked_subclass(cls: type, identifiable: model.Identifiable) -> type:
    """``cls``, or the subclass of it the identifiable's class marker names."""
    try:
        name = convert_util.get_class_name_from_basyx_model(identifiable)
    except ValueError:
        return cls
    marked = [sub for sub in _subclasses(cls) if sub.__name__ == name]
    return marked[0] if len(marked) == 1 else cls


def _subclasses(cls: type) -> list:
    found = [cls]
    for sub in cls.__subclasses__():
        found.extend(_subclasses(sub))
    return found


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
        return _container_element_to_pydantic(sm_element, attribute_type)
    elif isinstance(sm_element, model.File):
        return convert_file_to_pydantic_model(sm_element)
    elif isinstance(sm_element, model.Blob):
        return convert_blob_to_pydantic_model(sm_element)
    else:
        raise NotImplementedError("Type not implemented:", type(sm_element))


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
        "id_short": convert_util.own_id_short(basyx_model),
        "description": convert_util.get_str_description(basyx_model.description),
        "display_name": convert_util.own_display_name(basyx_model),
    }
    if model_instantiation_dict["id_short"] is None:
        del model_instantiation_dict["id_short"]  # an unnamed list item: its class names it
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


def _marked_class(basyx_el: model.SubmodelElement, expected_cls=None):
    """The pydantic class an element's class marker names, or ``None``. The marker holds only the class's name,
    which several templates may use: it decides only when exactly one class of that name fits the element (its
    kind, the class it is declared as, its semanticId)."""
    if not basyx_el.embedded_data_specifications:
        return None
    try:
        name = convert_util.get_class_name_from_basyx_model(basyx_el)
    except ValueError:
        return None
    candidates = [cls for cls in aas_model._ELEMENT_CLASSES_BY_NAME.get(name, ())
                  if _same_kind(cls, basyx_el) and (expected_cls is None or issubclass(cls, expected_cls))]
    if len(candidates) > 1:
        sid = convert_util.get_semantic_id_value_of_model(basyx_el)
        candidates = [cls for cls in candidates if cls.model_fields["semantic_id"].default == sid]
    return candidates[0] if len(candidates) == 1 else None


def _same_kind(cls: type, basyx_el: model.SubmodelElement) -> bool:
    """Whether a pydantic element class is the kind of the BaSyx element (an SMC class for an SMC, …)."""
    kinds = ((aas_model.SubmodelElementList, model.SubmodelElementList), (aas_model.Entity, model.Entity),
             (aas_model.SubmodelElementCollection, model.SubmodelElementCollection),
             (aas_model.Operation, model.Operation), (aas_model.Property, model.Property),
             (aas_model.MultiLanguageProperty, model.MultiLanguageProperty), (aas_model.Range, model.Range),
             (aas_model.ReferenceElement, model.ReferenceElement),
             (aas_model.RelationshipElement, model.RelationshipElement),
             (aas_model.File, model.File), (aas_model.Blob, model.Blob), (aas_model.Capability, model.Capability))
    return any(issubclass(cls, pydantic_kind) and isinstance(basyx_el, basyx_kind) for pydantic_kind, basyx_kind in kinds)


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
    marked = _marked_class(basyx_el, expected_cls)
    if marked is not None:
        return marked
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

    For a UNION-typed container the first element class is returned; callers
    that dispatch per element narrow the union by the element's kind
    (``_candidate_for``), so a Property and an SMC can share one map.
    """
    classes = _multi_element_classes(values_cls, field)
    return classes[0] if classes else None


_METADATA = frozenset({*convert_util.META_FIELDS, "asset_type", "derived_from", "specific_asset_ids"})


def _holds_elements(annotation) -> bool:
    """Whether a field holds elements or submodels: one, a union of them, or a map or list of them."""
    annotation = aas_model._resolve_annotation(annotation)
    origin = typing.get_origin(annotation)
    if origin in (dict, list):
        annotation = aas_model._container_item_type(annotation)
        origin = typing.get_origin(annotation)
    members = typing.get_args(annotation) if origin in (typing.Union, aas_model._UnionType) else (annotation,)
    return any(isinstance(m, type) and issubclass(m, (aas_model.SubmodelElement, aas_model.Submodel))
               for m in members)


def _complete(model_type: type, data: dict) -> dict:
    """``data`` with every element field the AAS does not hold set empty (an empty map or list, or none), so a
    class default does not come back in its place (an empty ``parameter`` map is not the class's Location)."""
    data = dict(data)
    for name, field in model_type.model_fields.items():
        if name in data or name in _METADATA or field.is_required():
            continue
        annotation = aas_model._field_annotation(model_type, name)
        if not _holds_elements(annotation):
            continue
        origin = typing.get_origin(aas_model._resolve_annotation(annotation))
        data[name] = {} if origin is dict else [] if origin is list else None
    return data


def _validated(model_type: type, data: dict):
    return TypeAdapter(model_type).validate_python(_complete(model_type, data))


def _candidate_for(candidates: list, basyx_el: model.SubmodelElement):
    """The one class of a union-typed map that is the element's kind (``VariableProp`` for a Property where the
    map holds ``VariableProp | VariableItem``), else ``None``."""
    fitting = [cls for cls in candidates if isinstance(cls, type) and _same_kind(cls, basyx_el)]
    return fitting[0] if len(fitting) == 1 else None


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


def _named_element_types(ann):
    members = typing.get_args(ann) if typing.get_origin(ann) is typing.Union else (ann,)
    return tuple(
        member for member in members
        if isinstance(member, type) and issubclass(member, aas_model.SubmodelElement)
    )


def _matching_named_type(candidates, basyx_el):
    """Choose the occurrence-specific definition of a shared semantic concept."""
    if len(candidates) == 1:
        return candidates[0]
    sid = convert_util.get_semantic_id_value_of_model(basyx_el)
    supplemental = _element_supplemental_sids(basyx_el)
    for candidate in candidates:
        if sid and _element_cls_sid(candidate) != sid:
            continue
        if supplemental != _element_cls_supplemental(candidate):
            continue
        if isinstance(basyx_el, model.File | model.Blob):
            declared = candidate.model_fields.get("content_type")
            if declared and declared.default != basyx_el.content_type:
                continue
        if isinstance(basyx_el, model.Property):
            declared = candidate.model_fields.get("value_type")
            if declared and convert_util.convert_basyx_value_type_to_xsd(basyx_el.value_type) != declared.default:
                continue
        return candidate
    return candidates[0]


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
        if _named_element_types(ann):
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
        candidates = _named_element_types(ann)
        if candidates:
            aas_name = aas_model._aas_field_name(cls, fname)
            element_fields[aas_name] = (fname, candidates)
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
            fname, candidates = named
            out[fname] = _container_element_to_pydantic(
                c, expected_cls=_matching_named_type(candidates, c)
            )
            continue
        sid = convert_util.get_semantic_id_value_of_model(c)
        fields = dict_fields.get(sid) or []
        if not fields and fallback_field is not None:
            fields = [fallback_field]
        if len(fields) == 1:
            # As in _container_children_data: a union-typed map must not pin
            # its first class; the semanticId registry resolves each child.
            elem_cls = _candidate_for(_multi_element_classes(cls, fields[0]), c)
            out.setdefault(fields[0], {})[c.id_short] = _container_element_to_pydantic(
                c, expected_cls=elem_cls
            )
        else:
            out[c.id_short] = _container_element_to_pydantic(c)
    return out


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
            elem_cls = _candidate_for(_multi_element_classes(values_cls, field), c)
            converted = _container_element_to_pydantic(c, expected_cls=elem_cls)
            key = _dict_id_short_to_key(c.id_short, _multi_key_type(values_cls, field))
            out.setdefault(field, {})[key] = converted
        else:
            named = next((
                name for name in values_cls.model_fields
                if aas_model._aas_field_name(values_cls, name) == c.id_short
            ), c.id_short)
            out[named] = _container_element_to_pydantic(c)
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
            items.append(_container_element_to_pydantic(c, item_cls))
        data = {
            **_element_meta(basyx_el),
            "value": items,
            "type_value_list_element": (
                basyx_el.type_value_list_element.__name__
                if basyx_el.type_value_list_element
                else None
            ),
            "value_type_list_element": (
                convert_util.convert_basyx_value_type_to_xsd(
                    basyx_el.value_type_list_element
                )
                if basyx_el.value_type_list_element
                else None
            ),
            "semantic_id_list_element": (
                basyx_el.semantic_id_list_element.key[0].value
                if basyx_el.semantic_id_list_element
                and basyx_el.semantic_id_list_element.key
                else ""
            ),
            "order_relevant": basyx_el.order_relevant,
        }
    else:
        # Leaf class resolved by semanticId (e.g. a typed Property subclass).
        data = get_submodel_element_value(basyx_el, None).model_dump()
    try:
        return cls(**_complete(cls, data))
    except Exception as e:  # noqa: BLE001 — a container no pydantic class represents is a modeling mistake,
        # not something to degrade into a lossy generic container: fail loudly.
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
        return _validated(model_type, dict_model_instantiation)

    if _is_container_style_model(model_type, "submodel_element"):
        # Container-style Submodel — children populate its ``Dict[str, X]``
        # field(s), grouped back into multi-cardinality maps by concept
        # semanticId (named-field style: ``StateGroup.value``,
        # ``Parameters.parameter``, or the base ``submodel_element`` fallback).
        dict_model_instantiation.update(
            _container_children_data(sm.submodel_element, model_type)
        )
        return _validated(model_type, dict_model_instantiation)

    raise ValueError(f"{model_type.__name__} declares no element fields to read {sm.id_short!r} into")


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
    if model_type is None:
        # No class declares this collection's children (AAS JSON carries none).
        model_type = aas_model.DynamicSubmodelElementCollection

    if _is_container_style_model(model_type, "value"):
        # Container-style SMC — children populate ``value`` keyed by id_short.
        dict_model_instantiation["value"] = {
            el.id_short: _container_element_to_pydantic(el)
            for el in sm_element.value
        }
        return _validated(model_type, dict_model_instantiation)

    return _container_element_to_pydantic(sm_element, model_type)


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
            item = convert_submodel_collection_to_pydantic_model(sme, model_type=item_type)
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
                "supplemental_semantic_ids": _element_supplemental_sids(sm_element),
                "qualifiers": _convert_basyx_qualifiers(getattr(sm_element, "qualifier", None) or ()),
                "value": dumped,
                "type_value_list_element": (
                    sm_element.type_value_list_element.__name__
                    if sm_element.type_value_list_element
                    else None
                ),
                "value_type_list_element": (
                    convert_util.convert_basyx_value_type_to_xsd(
                        sm_element.value_type_list_element
                    )
                    if sm_element.value_type_list_element
                    else None
                ),
                "semantic_id_list_element": (
                    sm_element.semantic_id_list_element.key[0].value
                    if sm_element.semantic_id_list_element
                    and sm_element.semantic_id_list_element.key
                    else ""
                ),
                "order_relevant": sm_element.order_relevant,
            }
        )

    if not sm_element.order_relevant:
        return set(sme_pydantic_models)
    if model_type is tuple:
        return tuple(sme_pydantic_models)
    return sme_pydantic_models


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
    args = typing.get_args(model_type)
    return args[0] if args else model_type


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
    referred_semantic_id = ""
    if basyx_ref.referred_semantic_id and basyx_ref.referred_semantic_id.key:
        referred_semantic_id = basyx_ref.referred_semantic_id.key[0].value
    return cls(key=keys, referred_semantic_id=referred_semantic_id)


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
                value="" if q.value is None else datatypes.xsd_repr(q.value),
                value_type=convert_util.convert_basyx_value_type_to_xsd(q.value_type),
                value_id=(
                    q.value_id.key[0].value
                    if q.value_id is not None and q.value_id.key
                    else ""
                ),
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
    meta = {
        "id_short": convert_util.own_id_short(basyx_el),
        "description": convert_util.get_str_description(basyx_el.description),
        "display_name": convert_util.own_display_name(basyx_el),
        "semantic_id": convert_util.get_semantic_id_value_of_model(basyx_el),
        "supplemental_semantic_ids": _element_supplemental_sids(basyx_el),
        "qualifiers": _convert_basyx_qualifiers(
            getattr(basyx_el, "qualifier", None) or ()
        ),
    }
    if meta["id_short"] is None:
        del meta["id_short"]  # an unnamed list item: its class names it
    return meta


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
        # The XSD lexical form ("false", not Python's "False").
        value="" if sm_element.value is None else datatypes.xsd_repr(sm_element.value),
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
        # A variable is an element: a list variable stays a SubmodelElementList
        # (with its metadata and qualifiers), not a bare Python list.
        return [get_submodel_element_value(var, aas_model.SubmodelElementList
                                           if isinstance(var, model.SubmodelElementList) else None)
                for var in variables or ()]

    return aas_model.Operation(
        **_element_meta(sm_element),
        input_variable=_convert_vars(sm_element.input_variable),
        output_variable=_convert_vars(sm_element.output_variable),
        in_output_variable=_convert_vars(sm_element.in_output_variable),
    )


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
        value=sm_element.value or "",
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
