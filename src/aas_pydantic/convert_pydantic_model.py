from __future__ import annotations

from collections import OrderedDict
from enum import Enum


from basyx.aas import model
from basyx.aas.model import datatypes
from basyx.aas.model.datatypes import XSD_TYPE_CLASSES, from_xsd

from typing import Optional, Union
import typing
from aas_pydantic import convert_util, aas_model

from aas_pydantic.convert_util import (
    AAS_META_KEY,
    convert_primitive_type_to_xsdtype,
    get_aas_meta,
    get_attribute_infos,
    get_id_short,
    get_semantic_id,
    patch_id_short_with_temp_attribute,
)

import logging

logger = logging.getLogger(__name__)


def convert_model_to_aas(
    model_aas: aas_model.AAS,
) -> model.DictIdentifiableStore[model.Identifiable]:
    """
    Convert a model aas to an Basyx AssetAdministrationShell and return it as a DictIdentifiableStore with all Submodels

    Args:
        model_aas (aas_model.AAS): model aas to convert

    Returns:
        model.DictIdentifiableStore[model.Identifiable]: DictIdentifiableStore with all Submodels
    """
    _META = {"asset_type", "derived_from", "specific_asset_ids"}
    aas_attribute_infos = get_attribute_infos(model_aas)
    aas_submodels = {}
    aas_submodel_data_specifications = []
    for attribute_info in aas_attribute_infos:
        if attribute_info.name in _META:
            continue
        submodel = convert_model_to_submodel(model_submodel=attribute_info.value)
        attribute_data_specification = (
            convert_util.get_data_specification_for_attribute(attribute_info, submodel)
        )
        aas_submodel_data_specifications.append(attribute_data_specification)
        if submodel and not submodel.id_short in aas_submodels:
            aas_submodels.update({submodel.id_short: submodel})

    # ── AssetInformation with metadata from the Pydantic model ────────
    asset_type = getattr(model_aas, "asset_type", "") or "Instance"
    asset_information = model.AssetInformation(
        global_asset_id=model.Identifier(model_aas.id),
        asset_kind=model.AssetKind.INSTANCE,
        asset_type=model.Identifier(asset_type) if asset_type else None,
    )

    # Specific asset IDs
    specific_ids = getattr(model_aas, "specific_asset_ids", {}) or {}
    if specific_ids:
        sid_set = set()
        for name, value in specific_ids.items():
            sid_set.add(model.SpecificAssetId(
                name=name, value=str(value),
                external_subject_id=model.ExternalReference(key=(
                    model.Key(model.KeyTypes.GLOBAL_REFERENCE,
                              f"https://admin-shell.io/aas/3/0/SpecificAssetId/{name}"),))))
        asset_information.specific_asset_id = sid_set

    # Derived-from template
    derived_from = getattr(model_aas, "derived_from", "") or ""

    # ── Build AAS shell ────────────────────────────────────────────────────
    aas_kwargs = {
        "asset_information": asset_information,
        "id_short": get_id_short(model_aas),
        "id_": model.Identifier(model_aas.id),
        "description": convert_util.get_basyx_description_from_model(model_aas),
        "display_name": convert_util.get_basyx_display_name_from_model(model_aas),
        "submodel": {
            model.ModelReference.from_referable(submodel)
            for submodel in aas_submodels.values()
        },
        "embedded_data_specifications": convert_util.get_data_specification_for_model(
            model_aas
        ) + aas_submodel_data_specifications,
    }
    if derived_from:
        aas_kwargs["derived_from"] = model.ModelReference(
            (model.Key(model.KeyTypes.ASSET_ADMINISTRATION_SHELL, derived_from),),
            model.AssetAdministrationShell)

    basyx_aas = model.AssetAdministrationShell(**aas_kwargs)
    obj_store: model.DictIdentifiableStore[model.Identifiable] = model.DictIdentifiableStore()
    obj_store.add(basyx_aas)
    for sm in aas_submodels.values():
        obj_store.add(sm)
    return obj_store


def convert_model_to_submodel(
    model_submodel: aas_model.Submodel,
    administration: Optional[model.AdministrativeInformation] = None,
) -> Optional[model.Submodel]:
    if not model_submodel:
        return
    submodel_attributes = get_attribute_infos(model_submodel)
    submodel_elements = []
    submodel_element_data_specifications = []

    for attribute_info in submodel_attributes:
        # Skip metadata fields (not actual submodel elements)
        if attribute_info.name in ("qualifiers", "supplemental_semantic_ids"):
            continue

        attr_value = attribute_info.value
        # Dict[str, SMC] map → inline entries as direct submodel elements
        if isinstance(attr_value, dict):
            submodel_elements.extend(
                _inline_dict_children(attr_value, field_info=attribute_info.field_info)
            )
            continue

        # Pass field_info so create_submodel_element can read AAS metadata
        submodel_element = create_submodel_element(
            attribute_info.name, attr_value,
            field_info=attribute_info.field_info,
        )
        attribute_data_specification = (
            convert_util.get_data_specification_for_attribute(
                attribute_info, submodel_element
            )
        )
        submodel_element_data_specifications.append(attribute_data_specification)
        immutable_attribute_data_specification = (
            convert_util.get_immutable_data_specification_for_attribute(attribute_info)
        )
        if immutable_attribute_data_specification:
            submodel_element_data_specifications.append(
                immutable_attribute_data_specification
            )
        if not attribute_info.field_info.is_required():
            default_data_specification = (
                convert_util.get_default_data_specification_for_attribute(
                    attribute_info, submodel_element
                )
            )
            if default_data_specification:
                submodel_element_data_specifications.append(default_data_specification)
        if submodel_element:
            submodel_elements.append(submodel_element)

    basyx_submodel = model.Submodel(
        id_short=get_id_short(model_submodel),
        id_=model.Identifier(model_submodel.id),
        description=convert_util.get_basyx_description_from_model(model_submodel),
        display_name=convert_util.get_basyx_display_name_from_model(model_submodel),
        embedded_data_specifications=convert_util.get_data_specification_for_model(
            model_submodel
        )
        + submodel_element_data_specifications,
        semantic_id=get_semantic_id(model_submodel),
        submodel_element=submodel_elements,
        administration=administration,
    )
    return basyx_submodel


def _make_basyx_reference(ref: aas_model.Reference) -> model.Reference:
    """Convert an aas_pydantic Reference (ModelReference/ExternalReference)
    to the corresponding basyx Reference."""
    def _to_basyx_key_type(type_str: str) -> model.KeyTypes:
        """Convert an aas_pydantic key type string to a basyx KeyTypes member."""
        try:
            return model.KeyTypes[convert_util.key_type_to_basyx_name(type_str)]
        except KeyError:
            logger.warning(
                "Unknown KeyType '%s' – falling back to ASSET_ADMINISTRATION_SHELL",
                type_str,
            )
            return model.KeyTypes.ASSET_ADMINISTRATION_SHELL

    basyx_keys = tuple(
        model.Key(
            type_=_to_basyx_key_type(k.type_) if k.type_ else model.KeyTypes.ASSET_ADMINISTRATION_SHELL,
            value=k.value,
        )
        for k in ref.key
    )
    if isinstance(ref, aas_model.ModelReference) or ref.type_ == "ModelReference":
        return model.ModelReference(key=basyx_keys, type_="")
    return model.ExternalReference(key=basyx_keys)


def create_submodel_element(
    attribute_name: str,
    attribute_value: Union[
        aas_model.SubmodelElementCollection, str, float, int, bool, tuple, list, set
    ],
    field_info=None,
) -> Optional[model.SubmodelElement]:
    """Create a basyx SubmodelElement — type-based dispatch."""
    if not attribute_value and not (isinstance(attribute_value, bool) or attribute_value == 0):
        return None

    # Metadata: for model types read from the instance; for primitives from field_info
    aas_meta = get_aas_meta(field_info) if field_info else {}
    sid = (_make_external_reference(aas_meta["semantic_id"])
           if aas_meta.get("semantic_id") else None)
    quals_meta = aas_meta.get("qualifiers", [])
    suppl_meta = aas_meta.get("supplemental_semantic_ids", [])
    desc_text = aas_meta.get("description")

    def _model_metadata(inst):
        """Read qualifiers/supplemental from a model instance (HasSemantics fields)."""
        q = _make_qualifiers(getattr(inst, 'qualifiers', None) or quals_meta)
        s = ([_make_external_reference(x) for x in (getattr(inst, 'supplemental_semantic_ids', None) or suppl_meta)]
             if (getattr(inst, 'supplemental_semantic_ids', None) or suppl_meta) else [])
        d = (model.MultiLanguageTextType({"en": desc_text}) if desc_text
             else (convert_util.get_basyx_description_from_model(inst) if inst.description else None))
        dn = (convert_util.get_basyx_display_name_from_model(inst)
              if getattr(inst, 'display_name', None) else None)
        return q, s, d, dn

    quals = _make_qualifiers(quals_meta) if quals_meta else []
    suppl = [_make_external_reference(s) for s in suppl_meta] if suppl_meta else []
    desc = model.MultiLanguageTextType({"en": desc_text}) if desc_text else None
    dn_meta = model.MultiLanguageNameType(dict(display_name_meta)) if (display_name_meta := aas_meta.get("display_name")) else None

    if isinstance(attribute_value, aas_model.Entity):
        q, s, d, dn = _model_metadata(attribute_value)
        entity_type = (
            model.EntityType.SELF_MANAGED_ENTITY
            if attribute_value.entity_type == "SelfManagedEntity"
            else model.EntityType.CO_MANAGED_ENTITY
        )
        statements = []
        # Named-field style: children are DIRECT named fields (and/or Dict
        # maps) on the Entity — no ``statements`` container required.
        smc_attributes = get_attribute_infos(attribute_value)
        for attribute_info in smc_attributes:
            if attribute_info.name in ("entity_type", "global_asset_id"):
                continue
            attr_value = attribute_info.value
            if isinstance(attr_value, dict):
                statements.extend(
                    _inline_dict_children(
                        attr_value, field_info=attribute_info.field_info
                    )
                )
                continue
            sme = create_submodel_element(
                attribute_info.name, attr_value,
                field_info=attribute_info.field_info,
            )
            if sme:
                statements.append(sme)
        global_asset_id = attribute_value.global_asset_id or None
        if (
            entity_type is model.EntityType.SELF_MANAGED_ENTITY
            and not global_asset_id
        ):
            raise ValueError(
                f"Self-managed Entity {attribute_name!r} requires global_asset_id "
                "(AASd-014)"
            )
        return model.Entity(
            id_short=attribute_name,
            entity_type=entity_type,
            statement=statements,
            global_asset_id=global_asset_id,
            semantic_id=sid or get_semantic_id(attribute_value),
            qualifier=q, supplemental_semantic_id=s, description=d, display_name=dn,
        )

    if isinstance(attribute_value, aas_model.SubmodelElementList):
        sml = create_submodel_element_list(
            attribute_name, attribute_value.value, field_info, sml=attribute_value
        )
        q, s, d, dn = _model_metadata(attribute_value)
        sml_sid = get_semantic_id(attribute_value)
        if sml_sid: sml.semantic_id = sml_sid
        elif sid: sml.semantic_id = sid
        if q: sml.qualifier = q
        if s: sml.supplemental_semantic_id = s
        if d: sml.description = d
        if dn: sml.display_name = dn
        return sml

    if isinstance(attribute_value, aas_model.SubmodelElementCollection):
        smc = create_submodel_element_collection(attribute_value)
        q, s, d, dn = _model_metadata(attribute_value)
        if q: smc.qualifier = q
        if s: smc.supplemental_semantic_id = s
        if d: smc.description = d
        if dn: smc.display_name = dn
        return smc

    if isinstance(attribute_value, (list, tuple, set)):
        sml = create_submodel_element_list(attribute_name, attribute_value, field_info)
        if sid: sml.semantic_id = sid
        if quals: sml.qualifier = quals
        if suppl: sml.supplemental_semantic_id = suppl
        if desc: sml.description = desc
        if dn_meta: sml.display_name = dn_meta
        return sml

    if isinstance(attribute_value, aas_model.Capability):
        q, s, d, dn = _model_metadata(attribute_value)
        return model.Capability(id_short=attribute_name, semantic_id=sid or get_semantic_id(attribute_value), qualifier=q, supplemental_semantic_id=s, description=d, display_name=dn)

    if isinstance(attribute_value, aas_model.Operation):
        q, s, d, dn = _model_metadata(attribute_value)
        return create_operation(attribute_name, attribute_value, sid, q, s, d, dn)

    if isinstance(attribute_value, aas_model.File):
        return create_file(attribute_value)
    if isinstance(attribute_value, aas_model.Blob):
        return create_blob(attribute_value)

    # ── Typed leaf models (metadata from instance, not field_info) ──
    if isinstance(attribute_value, aas_model.ReferenceElement):
        q, s, d, dn = _model_metadata(attribute_value)
        if not attribute_value.value:
            return None
        return model.ReferenceElement(
            id_short=attribute_name, value=_make_basyx_reference(attribute_value.value),
            semantic_id=sid or get_semantic_id(attribute_value),
            qualifier=q, supplemental_semantic_id=s, description=d, display_name=dn)

    if isinstance(attribute_value, aas_model.Property):
        q, s, d, dn = _model_metadata(attribute_value)
        vt_str = attribute_value.value_type
        vt = XSD_TYPE_CLASSES.get(vt_str, datatypes.String)
        value = attribute_value.value
        # Empty string = not set → None (basyx rejects '' for non-string types).
        if value == "":
            value = None
        elif vt is not datatypes.String:
            try:
                value = from_xsd(value, vt)
            except (ValueError, TypeError):
                logger.warning(
                    "Could not parse Property value %r as %s – keeping as string",
                    value, vt_str,
                )
                value = attribute_value.value
        return model.Property(
            id_short=attribute_name, value=value,
            value_type=vt,
            semantic_id=sid or get_semantic_id(attribute_value),
            qualifier=q, supplemental_semantic_id=s, description=d, display_name=dn)

    if isinstance(attribute_value, aas_model.MultiLanguageProperty):
        q, s, d, dn = _model_metadata(attribute_value)
        return model.MultiLanguageProperty(
            id_short=attribute_name,
            value=(
                attribute_value.value
                if attribute_value.value
                else None
            ),
            semantic_id=sid or get_semantic_id(attribute_value),
            qualifier=q, supplemental_semantic_id=s, description=d, display_name=dn)

    if isinstance(attribute_value, aas_model.RelationshipElement):
        q, s, d, dn = _model_metadata(attribute_value)
        first = (
            _make_basyx_reference(attribute_value.first)
            if attribute_value.first else None
        )
        second = (
            _make_basyx_reference(attribute_value.second)
            if attribute_value.second else None
        )
        if first is None or second is None:
            # basyx requires both endpoints (References) on a relationship.
            return None
        return model.RelationshipElement(
            id_short=attribute_name,
            first=first,
            second=second,
            semantic_id=sid or get_semantic_id(attribute_value),
            qualifier=q, supplemental_semantic_id=s, description=d, display_name=dn)

    if isinstance(attribute_value, aas_model.Range):
        q, s, d, dn = _model_metadata(attribute_value)
        vt_str = attribute_value.value_type
        vt = XSD_TYPE_CLASSES.get(vt_str, datatypes.String)
        vt_python = convert_util.convert_xsdtype_to_primitive_type(vt)
        min_val = attribute_value.min if attribute_value.min != "" else None
        max_val = attribute_value.max if attribute_value.max != "" else None
        # Cast string min/max to the Python type matching value_type
        if min_val is not None and not isinstance(min_val, vt_python):
            try:
                min_val = vt_python(min_val)
            except (ValueError, TypeError):
                pass
        if max_val is not None and not isinstance(max_val, vt_python):
            try:
                max_val = vt_python(max_val)
            except (ValueError, TypeError):
                pass
        return model.Range(
            id_short=attribute_name,
            value_type=vt,
            min=min_val,
            max=max_val,
            semantic_id=sid or get_semantic_id(attribute_value),
            qualifier=q, supplemental_semantic_id=s, description=d, display_name=dn)

    prop = create_property(attribute_name, attribute_value)
    if sid: prop.semantic_id = sid
    if quals: prop.qualifier = quals
    if suppl: prop.supplemental_semantic_id = suppl
    if desc: prop.description = desc
    if dn_meta: prop.display_name = dn_meta
    return prop


def create_property(
    attribute_name: str,
    attribute_value: Union[str, int, float, bool],
) -> model.Property:
    if isinstance(attribute_value, Enum):
        attribute_value = attribute_value.value
        attribute_type = str
    else:
        attribute_type = type(attribute_value)

    property = model.Property(
        id_short=attribute_name,
        value_type=convert_primitive_type_to_xsdtype(attribute_type),
        value=attribute_value,
    )
    return property


def _dict_item_type(ann):
    """Element class of a ``Dict[str, E]`` annotation, or ``None``.

    A container may accept a UNION of element classes — e.g. the Variables /
    Parameters submodels take ``Union[VariableProp, VariableItem]`` so a
    submodel can mix plain Properties with grouped SMCs in one map. The first
    element class is returned; children are then built from the concrete
    instances, so the other union members convert correctly too.
    """
    args = typing.get_args(ann)
    if len(args) == 2 and args[0] is str:
        inner = args[1]
        if typing.get_origin(inner) is typing.Union:
            candidates = typing.get_args(inner)
        else:
            candidates = (inner,)
        for candidate in candidates:
            if isinstance(candidate, type) and issubclass(candidate, aas_model.SubmodelElement):
                return candidate
    return None


def _dict_key_to_id_short(key):
    """AAS id_short must be a non-empty string starting with a letter
    (AASd-002).  ``int`` dict keys (``Dict[int, X]``) are mapped to a
    zero-padded ``param_<n>`` id_short so they survive conversion; string
    keys pass through unchanged."""
    if isinstance(key, int):
        return f"param_{key:02d}"
    return key


def _inline_dict_children(
    attr_value,
    field_info=None,
) -> list:
    """Convert a container's children to named BaSyx elements.

    Accepts a ``Dict[str, AnySubmodelElement]`` (dynamic name-keyed map) whose
    keys become the id_shorts of the children.

    Works for any AAS element type: Property, Range, Operation,
    SubmodelElementCollection, SubmodelElementList, MultiLanguageProperty, etc.

    The key always wins as the authoritative id_short (overrides any id_short
    already set on the model instance).
    """
    if isinstance(attr_value, dict):
        items = list(attr_value.items())
    else:
        items = []
    children = []
    for key, val in items:
        if val is None:
            continue
        id_short = _dict_key_to_id_short(key)
        sme = create_submodel_element(id_short, val, field_info=field_info)
        if sme is not None:
            sme.id_short = id_short
            children.append(sme)
    return children


def create_submodel_element_collection(
    model_sec: aas_model.SubmodelElementCollection,
) -> model.SubmodelElementCollection:
    value = []
    smc_attributes = get_attribute_infos(model_sec)
    submodel_element_data_specifications = []

    for attribute_info in smc_attributes:
        # Skip metadata fields (not actual submodel elements)
        if attribute_info.name in ("qualifiers", "supplemental_semantic_ids"):
            continue

        attr_value = attribute_info.value

        # Dict[str, SMC] map → inline entries as direct children
        if isinstance(attr_value, dict):
            value.extend(
                _inline_dict_children(attr_value, field_info=attribute_info.field_info)
            )
            continue

        sme = create_submodel_element(
            attribute_info.name, attr_value,
            field_info=attribute_info.field_info,
        )
        attribute_data_specification = (
            convert_util.get_data_specification_for_attribute(attribute_info, sme)
        )
        submodel_element_data_specifications.append(attribute_data_specification)
        immutable_attribute_data_specification = (
            convert_util.get_immutable_data_specification_for_attribute(attribute_info)
        )
        if immutable_attribute_data_specification:
            submodel_element_data_specifications.append(
                immutable_attribute_data_specification
            )
        if (
            not attribute_info.field_info.is_required()
            and attribute_info.field_info.default
        ):
            default_data_specification = (
                convert_util.get_default_data_specification_for_attribute(
                    attribute_info, sme
                )
            )
            if default_data_specification:
                submodel_element_data_specifications.append(default_data_specification)
        if sme:
            value.append(sme)

    id_short = get_id_short(model_sec)

    smc = model.SubmodelElementCollection(
        id_short=id_short,
        value=value,
        description=convert_util.get_basyx_description_from_model(model_sec),
        display_name=convert_util.get_basyx_display_name_from_model(model_sec),
        embedded_data_specifications=convert_util.get_data_specification_for_model(
            model_sec
        )
        + submodel_element_data_specifications,
        semantic_id=get_semantic_id(model_sec),
    )
    return smc


# pydantic element class (or subclass) → basyx model class, for declaring an
# SML's ``type_value_list_element`` from its ``item_type`` when the list is
# empty (template example items are no longer pre-populated).
_AAS_TO_BASYX_ELEMENT = (
    (aas_model.Property, model.Property),
    (aas_model.MultiLanguageProperty, model.MultiLanguageProperty),
    (aas_model.Range, model.Range),
    (aas_model.ReferenceElement, model.ReferenceElement),
    (aas_model.RelationshipElement, model.RelationshipElement),
    (aas_model.File, model.File),
    (aas_model.Blob, model.Blob),
    (aas_model.Capability, model.Capability),
    (aas_model.Operation, model.Operation),
    (aas_model.Entity, model.Entity),
    (aas_model.SubmodelElementCollection, model.SubmodelElementCollection),
    (aas_model.SubmodelElementList, model.SubmodelElementList),
)


def _aas_cls_to_basyx(cls) -> Optional[type]:
    """The basyx model class for a pydantic element class (or subclass), or
    ``None`` when *cls* is not a concrete element type."""
    if not isinstance(cls, type):
        return None
    for aas_cls, basyx_cls in _AAS_TO_BASYX_ELEMENT:
        if issubclass(cls, aas_cls):
            return basyx_cls
    return None


def create_submodel_element_list(
    attribute_name: str, value: list | tuple | set,
    field_info=None,  # Optional[FieldInfo] — for list-level AAS metadata
    sml: Optional[aas_model.SubmodelElementList] = None,
) -> model.SubmodelElementList:
    submodel_elements = []
    submodel_element_ids = OrderedDict()
    for el in value:
        submodel_element = create_submodel_element(attribute_name, el, field_info=field_info)
        if submodel_element is None:
            # Empty element (e.g. a ReferenceElement with no value) — skip.
            continue
        if isinstance(submodel_element, model.SubmodelElementCollection):
            if submodel_element.id_short in submodel_element_ids:
                raise ValueError(
                    f"Submodel element collection with id {submodel_element.id_short} already exists in list"
                )
            submodel_element_ids.update({submodel_element.id_short: None})
            patch_id_short_with_temp_attribute(submodel_element)
        # AASd-120: items of a SubmodelElementList must not carry an id_short.
        submodel_element.id_short = None
        # Clear individual semantic_ids (AASd-114: all SML items share the list's semantic_id)
        if hasattr(submodel_element, 'semantic_id') and submodel_element.semantic_id:
            if hasattr(submodel_element, 'supplemental_semantic_id'):
                submodel_element.supplemental_semantic_id = []
            submodel_element.semantic_id = None
        submodel_elements.append(submodel_element)

    if submodel_elements and isinstance(submodel_elements[0], model.Property):
        # value_type_list_element must be the basyx datatype of the items
        # (AASd-109: all items share the list's value type).
        value_type_list_element = submodel_elements[0].value_type
        type_value_list_element = type(submodel_elements[0])
    elif submodel_elements and isinstance(
        submodel_elements[0], model.Reference | model.SubmodelElementCollection
    ):
        value_type_list_element = None
        type_value_list_element = type(submodel_elements[0])
    else:
        # Empty list — declare the item type from the SML class's ``item_type``
        # (template example items are no longer pre-populated, so there are no
        # items to infer it from).  Falls back to Property/xs:string.
        item_cls = getattr(type(sml), "item_type", None) if sml is not None else None
        mapped = _aas_cls_to_basyx(item_cls)
        if mapped and mapped is not model.Property:
            value_type_list_element = None
            type_value_list_element = mapped
        else:
            value_type_list_element = convert_primitive_type_to_xsdtype(str)
            type_value_list_element = model.Property
    if isinstance(value, set):
        ordered = False
        iterable_type = "set"
    elif isinstance(value, tuple):
        ordered = True
        iterable_type = "tuple"
    elif isinstance(value, list):
        ordered = True
        iterable_type = "list"
    else:
        raise ValueError(
            f"Value must be a list, tuple or set, provided type {type(value)}"
        )

    sml = model.SubmodelElementList(
        id_short=attribute_name,
        type_value_list_element=type_value_list_element,
        value_type_list_element=value_type_list_element,
        value=submodel_elements,
        order_relevant=ordered,
    )
    return sml


def create_file(attribute_value: aas_model.File) -> Optional[model.File]:
    """Generate a basyx File. Returns None if value or content_type is empty."""
    if not attribute_value.value or not attribute_value.content_type:
        return None
    return model.File(
        id_short=attribute_value.id_short,
        description=(
            {"en": attribute_value.description}
            if attribute_value.description
            else None
        ),
        display_name=convert_util.get_basyx_display_name_from_model(attribute_value),
        semantic_id=get_semantic_id(attribute_value),
        content_type=attribute_value.content_type,
        value=attribute_value.value,
    )


def create_blob(attribute_value: aas_model.Blob) -> Optional[model.Blob]:
    """
    Function generates a basyx blob objects from a pydantic Blob.

    Args:
        attribute_value (aas_model.Blob): pydantic Blob instance.

    Returns:
        model.Blob: Basyx blob.  None when content_type is empty (basyx
        requires a non-empty content type — mirrors create_file).
    """
    if not attribute_value.content_type:
        return None
    return model.Blob(
        id_short=attribute_value.id_short,
        description=(
            {"en": attribute_value.description}
            if attribute_value.description
            else None
        ),
        display_name=convert_util.get_basyx_display_name_from_model(attribute_value),
        # Mirror create_file: the pydantic ``semantic_id`` is a plain string —
        # basyx needs an ExternalReference (a raw string serializes to an
        # invalid ``"semanticId": "..."`` and is rejected by the AAS server).
        semantic_id=get_semantic_id(attribute_value),
        content_type=attribute_value.content_type,
        value=attribute_value.value,
    )


# ── Helpers ─────────────────────────────────────────────────────────────

def _make_external_reference(uri: str) -> model.ExternalReference:
    return model.ExternalReference(
        key=(model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE, value=uri),)
    )


_QUALIFIER_KIND_TO_BASYX = {
    "ConceptQualifier": model.QualifierKind.CONCEPT_QUALIFIER,
    "TemplateQualifier": model.QualifierKind.TEMPLATE_QUALIFIER,
}


def _make_qualifiers(qds: list) -> list:
    result = []
    for qd in qds:
        # Handle both Qualifier model instances and raw dicts (from json_schema_extra)
        if hasattr(qd, 'type_'):
            # Qualifier model instance
            kwargs = {
                "type_": qd.type_,
                "value_type": XSD_TYPE_CLASSES.get(qd.value_type, datatypes.String),
                "value": qd.value,
                "kind": _QUALIFIER_KIND_TO_BASYX.get(qd.kind, model.QualifierKind.TEMPLATE_QUALIFIER),
            }
            if qd.semantic_id:
                kwargs["semantic_id"] = _make_external_reference(qd.semantic_id)
        else:
            # Raw dict from json_schema_extra
            kwargs = {
                "type_": qd["type"],
                "value_type": datatypes.String,
                "value": qd["value"],
                "kind": model.QualifierKind.TEMPLATE_QUALIFIER,
            }
            if "semantic_id" in qd and qd["semantic_id"]:
                kwargs["semantic_id"] = _make_external_reference(qd["semantic_id"])
        result.append(model.Qualifier(**kwargs))
    return result


def create_operation(
    attribute_name: str,
    op: aas_model.Operation,
    sid=None, quals=None, suppl=None, desc=None, dn=None,
) -> model.Operation:
    """Create a basyx Operation from an aas_pydantic Operation model."""
    input_vars = [
        create_submodel_element(v.id_short or f"input_{i}", v)
        for i, v in enumerate(op.input_variable)
    ]
    output_vars = [
        create_submodel_element(v.id_short or f"output_{i}", v)
        for i, v in enumerate(op.output_variable)
    ]
    inoutput_vars = [
        create_submodel_element(v.id_short or f"inoutput_{i}", v)
        for i, v in enumerate(op.in_output_variable)
    ]
    return model.Operation(
        id_short=attribute_name,
        input_variable=input_vars,
        output_variable=output_vars,
        in_output_variable=inoutput_vars,
        semantic_id=sid or get_semantic_id(op),
        qualifier=quals or [],
        supplemental_semantic_id=suppl or [],
        description=desc,
        display_name=dn,
    )
