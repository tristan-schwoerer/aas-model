from __future__ import annotations

from collections import OrderedDict


from basyx.aas import model
from basyx.aas.model import datatypes
from basyx.aas.model.datatypes import XSD_TYPE_CLASSES, from_xsd

from typing import Optional, Union
from aas_pydantic import convert_util, aas_model

from aas_pydantic.convert_util import (
    convert_primitive_type_to_xsdtype,
    get_aas_meta,
    get_attribute_infos,
    get_id_short,
    get_semantic_id,
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
    # By id: two submodels may share an idShort, and one submodel may be held by two fields.
    aas_submodels = {}
    aas_submodel_data_specifications = []
    for attribute_info in aas_attribute_infos:
        if attribute_info.name in _META:
            continue
        submodel = convert_model_to_submodel(model_submodel=attribute_info.value)
        attribute_data_specification = (
            convert_util.get_data_specification_for_attribute(attribute_info, submodel)
        )
        if attribute_data_specification:
            aas_submodel_data_specifications.append(attribute_data_specification)
        if submodel and submodel.id not in aas_submodels:
            aas_submodels[submodel.id] = submodel

    # ── AssetInformation: the asset is identified by the shell's id ────────
    asset_type = getattr(model_aas, "asset_type", "") or None
    asset_information = model.AssetInformation(
        global_asset_id=model.Identifier(model_aas.id),
        asset_kind=model.AssetKind.INSTANCE,
        asset_type=model.Identifier(asset_type) if asset_type else None,
    )
    specific_ids = getattr(model_aas, "specific_asset_ids", {}) or {}
    if specific_ids:
        asset_information.specific_asset_id = [
            model.SpecificAssetId(name=name, value=str(value)) for name, value in sorted(specific_ids.items())
        ]

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
    submodel_elements = _children(model_submodel)
    return model.Submodel(
        id_short=get_id_short(model_submodel),
        id_=model.Identifier(model_submodel.id),
        description=convert_util.get_basyx_description_from_model(model_submodel),
        display_name=convert_util.get_basyx_display_name_from_model(model_submodel),
        embedded_data_specifications=convert_util.get_data_specification_for_model(model_submodel),
        semantic_id=get_semantic_id(model_submodel),
        qualifier=_make_qualifiers(model_submodel.qualifiers),
        supplemental_semantic_id=[_make_external_reference(s) for s in model_submodel.supplemental_semantic_ids],
        submodel_element=submodel_elements,
        administration=administration,
    )


def _children(container, skip: tuple[str, ...] = ()) -> list:
    """The BaSyx elements of a container's fields, a map's entries inline. Each element carries its own class
    marker; the container says nothing about them."""
    elements = []
    for attribute_info in get_attribute_infos(container):
        if attribute_info.name in skip:
            continue
        if isinstance(attribute_info.value, dict):
            elements.extend(_inline_dict_children(attribute_info.value, field_info=attribute_info.field_info))
            continue
        element = create_submodel_element(
            _aas_attribute_name(attribute_info), _named_by_field(attribute_info),
            field_info=attribute_info.field_info,
        )
        if element is not None:
            elements.append(element)
    return elements


def _make_basyx_reference(ref: aas_model.Reference) -> model.Reference:
    """Convert an aas_pydantic Reference (ModelReference/ExternalReference)
    to the corresponding basyx Reference."""
    is_model_reference = isinstance(ref, aas_model.ModelReference) or ref.type_ == "ModelReference"

    def _to_basyx_key_type(type_str: str) -> model.KeyTypes:
        if not type_str:
            if is_model_reference:
                raise ValueError(f"a key of the ModelReference {ref.key} has no type")
            return model.KeyTypes.GLOBAL_REFERENCE
        try:
            return model.KeyTypes[convert_util.key_type_to_basyx_name(type_str)]
        except KeyError as error:
            raise ValueError(f"unknown key type {type_str!r} in {ref.key}") from error

    basyx_keys = tuple(model.Key(type_=_to_basyx_key_type(k.type_), value=k.value) for k in ref.key)
    if is_model_reference:
        target_type = getattr(model, ref.key[-1].type_, model.Referable) if ref.key else model.Referable
        return model.ModelReference(
            key=basyx_keys, type_=target_type,
            referred_semantic_id=(
                _make_external_reference(ref.referred_semantic_id)
                if ref.referred_semantic_id else None
            ),
        )
    return model.ExternalReference(
        key=basyx_keys,
        referred_semantic_id=(
            _make_external_reference(ref.referred_semantic_id)
            if ref.referred_semantic_id else None
        ),
    )


def _aas_attribute_name(attribute_info) -> str:
    extra = attribute_info.field_info.json_schema_extra
    return extra.get("aas_id_short", attribute_info.name) if isinstance(extra, dict) else attribute_info.name


def _named_by_field(attribute_info):
    """A named field's element under the field's name: the name is its id_short, also for an element assigned
    after its container was validated (before its markers, which carry the id_short, are made)."""
    value, name = attribute_info.value, _aas_attribute_name(attribute_info)
    if isinstance(value, aas_model.Referable) and value.id_short != name:
        return value.model_copy(update={"id_short": name})
    return value


def create_submodel_element(
    attribute_name: str,
    attribute_value: Union[aas_model.SubmodelElement, tuple, list, set],
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
        # Named-field style: an Entity's fields (and maps) are its statements.
        statements = _children(attribute_value, skip=("entity_type", "global_asset_id"))
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
            embedded_data_specifications=convert_util.get_data_specification_for_model(attribute_value),
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
        sml.embedded_data_specifications = convert_util.get_data_specification_for_model(attribute_value)
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
        operation = create_operation(attribute_name, attribute_value, sid, q, s, d, dn)
        operation.embedded_data_specifications = convert_util.get_data_specification_for_model(attribute_value)
        return operation

    if isinstance(attribute_value, aas_model.File):
        return create_file(attribute_value, sid, *_model_metadata(attribute_value))
    if isinstance(attribute_value, aas_model.Blob):
        return create_blob(attribute_value, sid, *_model_metadata(attribute_value))

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
            except (ValueError, TypeError) as error:
                raise ValueError(f"{attribute_name}: {value!r} is not a {vt_str}") from error
        return model.Property(
            id_short=attribute_name, value=value,
            value_type=vt,
            value_id=_make_external_reference(attribute_value.value_id) if attribute_value.value_id else None,
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
            value_id=_make_external_reference(attribute_value.value_id) if attribute_value.value_id else None,
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

        def bound(lexical):
            if lexical in ("", None):
                return None
            if not isinstance(lexical, str):
                lexical = str(lexical).lower() if isinstance(lexical, bool) else str(lexical)
            try:
                return from_xsd(lexical, vt)
            except (ValueError, TypeError) as error:
                raise ValueError(f"{attribute_name}: the bound {lexical!r} is not a {vt_str}") from error
        min_val, max_val = bound(attribute_value.min), bound(attribute_value.max)
        return model.Range(
            id_short=attribute_name,
            value_type=vt,
            min=min_val,
            max=max_val,
            semantic_id=sid or get_semantic_id(attribute_value),
            qualifier=q, supplemental_semantic_id=s, description=d, display_name=dn)

    # A plain value is wrapped into its element class when the model is validated, so none arrives here.
    raise TypeError(f"{attribute_name}: {type(attribute_value).__name__} is not a submodel element")


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
        if isinstance(val, aas_model.Referable) and val.id_short != id_short:
            # Also for an element put into the map after validation, before its
            # markers (which carry its id_short) are made.
            val = val.model_copy(update={"id_short": id_short})
        sme = create_submodel_element(id_short, val, field_info=field_info)
        if sme is not None:
            sme.id_short = id_short
            children.append(sme)
    return children


def create_submodel_element_collection(
    model_sec: aas_model.SubmodelElementCollection,
) -> model.SubmodelElementCollection:
    value = _children(model_sec)
    return model.SubmodelElementCollection(
        id_short=get_id_short(model_sec),
        value=value,
        description=convert_util.get_basyx_description_from_model(model_sec),
        display_name=convert_util.get_basyx_display_name_from_model(model_sec),
        embedded_data_specifications=convert_util.get_data_specification_for_model(model_sec),
        semantic_id=get_semantic_id(model_sec),
    )


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
        # An item named only by its class default has no name to restore: it is
        # neither checked for uniqueness nor parked (AASd-120 drops it below).
        id_short_field = type(el).model_fields.get("id_short") if isinstance(el, aas_model.Referable) else None
        named = id_short_field is None or el.id_short != id_short_field.default
        if isinstance(submodel_element, model.SubmodelElementCollection) and named:
            if submodel_element.id_short in submodel_element_ids:
                raise ValueError(
                    f"Submodel element collection with id {submodel_element.id_short} already exists in list"
                )
            # Its name stays in its class marker (``own_id_short``), so names must be unique in the list. It is
            # shown by its name: its display name, unless it has one of its own.
            submodel_element_ids.update({submodel_element.id_short: None})
            if not submodel_element.display_name:
                submodel_element.display_name = model.MultiLanguageNameType({"en": submodel_element.id_short})
        # AASd-120: items of a SubmodelElementList must not carry an id_short.
        submodel_element.id_short = None
        submodel_elements.append(submodel_element)

    semantic_id_list_element = (
        _make_external_reference(sml.semantic_id_list_element)
        if sml is not None and sml.semantic_id_list_element
        else None
    )
    # AASd-107/114: the items' semanticIds agree with each other and with semanticIdListElement. An item keeps
    # its own (an item class's concept) when they do; the items' supplementalSemanticIds are kept as they are.
    item_semantic_ids = {item.semantic_id for item in submodel_elements}
    if len(item_semantic_ids) > 1 or (
        semantic_id_list_element is not None and item_semantic_ids - {None, semantic_id_list_element}
    ):
        raise ValueError(
            f"{attribute_name}: the items' semanticIds "
            f"{sorted(str(i.key[0].value) for i in item_semantic_ids if i is not None)} differ "
            f"from each other or from its semanticIdListElement (AASd-107/114)"
        )

    if submodel_elements:
        type_value_list_element = type(submodel_elements[0])
        # AASd-109: all items share the list's value type.
        value_type_list_element = getattr(submodel_elements[0], "value_type", None)
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
    elif isinstance(value, tuple):
        ordered = True
    elif isinstance(value, list):
        ordered = True
    else:
        raise ValueError(
            f"Value must be a list, tuple or set, provided type {type(value)}"
        )

    if sml is not None and sml.type_value_list_element:
        type_value_list_element = sml.type_value_list_element
        if isinstance(type_value_list_element, str):
            type_value_list_element = getattr(
                model, type_value_list_element, model.Property
            )
    if sml is not None and sml.value_type_list_element:
        value_type_list_element = XSD_TYPE_CLASSES.get(
            sml.value_type_list_element, value_type_list_element
        )
    return model.SubmodelElementList(
        id_short=attribute_name,
        type_value_list_element=type_value_list_element,
        value_type_list_element=value_type_list_element,
        semantic_id_list_element=semantic_id_list_element,
        value=submodel_elements,
        order_relevant=sml.order_relevant if sml is not None else ordered,
    )


def create_file(attribute_value: aas_model.File, sid=None, q=(), s=(), d=None, dn=None) -> Optional[model.File]:
    """A BaSyx File; none without a content type, or without a value unless the class keeps Files without one
    (``KEEP_WITHOUT_VALUE``)."""
    if not attribute_value.content_type:
        return None
    if not attribute_value.value and not type(attribute_value).KEEP_WITHOUT_VALUE:
        return None
    return model.File(
        id_short=attribute_value.id_short,
        content_type=attribute_value.content_type,
        value=attribute_value.value or None,
        semantic_id=sid or get_semantic_id(attribute_value),
        qualifier=q, supplemental_semantic_id=s, description=d, display_name=dn,
    )


def create_blob(attribute_value: aas_model.Blob, sid=None, q=(), s=(), d=None, dn=None) -> Optional[model.Blob]:
    """A BaSyx Blob; none without a content type (BaSyx requires one)."""
    if not attribute_value.content_type:
        return None
    return model.Blob(
        id_short=attribute_value.id_short,
        content_type=attribute_value.content_type,
        value=attribute_value.value,
        semantic_id=sid or get_semantic_id(attribute_value),
        qualifier=q, supplemental_semantic_id=s, description=d, display_name=dn,
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
            value_type = XSD_TYPE_CLASSES.get(qd.value_type, datatypes.String)
            kwargs = {
                "type_": qd.type_,
                "value_type": value_type,
                # The value's lexical form, typed as its value_type declares (basyx casts strictly).
                "value": (from_xsd(qd.value, value_type) if qd.value else None) if isinstance(qd.value, str) else qd.value,
                "value_id": (
                    _make_external_reference(qd.value_id) if qd.value_id else None
                ),
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
                "value_id": (
                    _make_external_reference(qd["value_id"])
                    if qd.get("value_id") else None
                ),
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
    def variables(values, prefix):
        elements = (create_submodel_element(v.id_short or f"{prefix}_{i}", v) for i, v in enumerate(values))
        return [element for element in elements if element is not None]
    input_vars = variables(op.input_variable, "input")
    output_vars = variables(op.output_variable, "output")
    inoutput_vars = variables(op.in_output_variable, "inoutput")
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
