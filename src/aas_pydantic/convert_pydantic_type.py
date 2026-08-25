from __future__ import annotations

from collections import OrderedDict
import json
from types import NoneType
import typing
from urllib import parse
from enum import Enum
import uuid


from basyx.aas import model

from typing import Any, Optional, Set, Union
from pydantic import BaseModel, ConfigDict

# from aas_middleware.model.core import Reference
from aas_pydantic import convert_util, aas_model

from aas_pydantic.convert_util import (
    AttributeFieldInfo,
    convert_primitive_type_to_xsdtype,
    get_attribute_field_infos,
    get_template_id,
    patch_id_short_with_temp_attribute,
)

import basyx.aas.adapter.json.json_serialization
import logging

logger = logging.getLogger(__name__)


def convert_model_to_aas_template(
    model_type: type[aas_model.AssetAdministrationShell],
) -> model.DictIdentifiableStore[model.Identifiable]:
    """
    Convert a model aas to an Basyx AssetAdministrationShell and return it as a DictIdentifiableStore with all Submodels

    Args:
        model_type (type[aas_model.AssetAdministrationShell]): Type of the model

    Returns:
        model.DictIdentifiableStore[model.Identifiable]: DictIdentifiableStore with all Submodels
    """
    aas_attribute_infos = get_attribute_field_infos(model_type)
    aas_submodels = {}
    aas_submodel_data_specifications = []
    for attribute_info in aas_attribute_infos:
        if attribute_info.name in ("asset_type", "derived_from", "specific_asset_ids"):
            continue
        if typing.get_origin(attribute_info.field_info.annotation) == Union:
            types_to_check = [
                type_annotation
                for type_annotation in typing.get_args(
                    attribute_info.field_info.annotation
                )
                if type_annotation != NoneType
            ]
            optional_attribute_data_specification = (
                convert_util.get_optional_data_specification_for_attribute(
                    attribute_info
                )
            )
            if optional_attribute_data_specification:
                aas_submodel_data_specifications.append(
                    optional_attribute_data_specification
                )
            union_attribute_data_specification = (
                convert_util.get_union_data_specification_for_attribute(attribute_info)
            )
            if union_attribute_data_specification:
                aas_submodel_data_specifications.append(
                    union_attribute_data_specification
                )

        else:
            types_to_check = [attribute_info.field_info.annotation]

        for type_annotation in types_to_check:
            submodel = convert_model_to_submodel_template(model_type=type_annotation)
            attribute_data_specifications = (
                convert_util.get_data_specification_for_attribute(
                    attribute_info, submodel
                )
            )
            aas_submodel_data_specifications.append(attribute_data_specifications)
            if not attribute_info.field_info.is_required():
                default_data_specification = (
                    convert_util.get_default_data_specification_for_attribute(
                        attribute_info, submodel
                    )
                )
                aas_submodel_data_specifications.append(default_data_specification)

            if submodel and not submodel.id_short in aas_submodels:
                aas_submodels.update({submodel.id_short: submodel})

    asset_information = model.AssetInformation(
        asset_kind=model.AssetKind.TYPE,
        asset_type=model.Identifier("Type"),
        global_asset_id=model.Identifier(get_template_id(model_type)),
    )

    basyx_aas = model.AssetAdministrationShell(
        asset_information=asset_information,
        id_short=get_template_id(model_type),
        id_=model.Identifier(get_template_id(model_type)),
        description={
            "en": f"Type aas with id {get_template_id(model_type)} that contains submodel templates"
        },
        submodel={
            model.ModelReference.from_referable(submodel)
            for submodel in aas_submodels.values()
        },
        embedded_data_specifications=convert_util.get_data_specification_for_model_template(
            model_type
        )
        + aas_submodel_data_specifications,
    )
    obj_store: model.DictIdentifiableStore[model.Identifiable] = model.DictIdentifiableStore()
    obj_store.add(basyx_aas)
    for sm in aas_submodels.values():
        obj_store.add(sm)
    return obj_store


def _is_container_field(annotation: Any) -> bool:
    """True for ``Dict[str, X]`` container fields whose children cannot be
    represented as named fields in a template."""
    if typing.get_origin(annotation) == dict:
        return True
    return False


def convert_model_instance_to_submodel_template(
    model_instance: aas_model.Submodel,
) -> Optional[model.Submodel]:
    return convert_model_to_submodel_template(type(model_instance))


def convert_model_to_submodel_template(
    model_type: type[aas_model.Submodel],
) -> Optional[model.Submodel]:
    if not model_type:
        return
    submodel_attributes = get_attribute_field_infos(model_type)
    submodel_elements = []
    submodel_element_data_specifications = []

    for attribute_info in submodel_attributes:
        if _is_container_field(attribute_info.field_info.annotation):
            continue
        if typing.get_origin(attribute_info.field_info.annotation) == Union:
            types_to_check = [
                type_annotation
                for type_annotation in typing.get_args(
                    attribute_info.field_info.annotation
                )
                if type_annotation != NoneType
            ]
            optional_attribute_data_specification = (
                convert_util.get_optional_data_specification_for_attribute(
                    attribute_info
                )
            )
            if optional_attribute_data_specification:
                submodel_element_data_specifications.append(
                    optional_attribute_data_specification
                )
            union_attribute_data_specification = (
                convert_util.get_union_data_specification_for_attribute(attribute_info)
            )
            if union_attribute_data_specification:
                submodel_element_data_specifications.append(
                    union_attribute_data_specification
                )

        else:
            types_to_check = [attribute_info.field_info.annotation]

        for counter, type_annotation in enumerate(types_to_check):
            if len(types_to_check) > 1:
                attribute_name = f"{attribute_info.name}_{counter}"
            else:
                attribute_name = attribute_info.name
            submodel_element = create_submodel_element_template(
                attribute_name=attribute_name, attribute_type=type_annotation
            )
            attribute_data_specifications = (
                convert_util.get_data_specification_for_attribute(
                    attribute_info, submodel_element
                )
            )
            submodel_element_data_specifications.append(attribute_data_specifications)
            immutable_attribute_data_specification = (
                convert_util.get_immutable_data_specification_for_attribute(
                    attribute_info
                )
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
                submodel_element_data_specifications.append(default_data_specification)
            if submodel_element and not any(
                stored_submodel_element.id_short == submodel_element.id_short
                for stored_submodel_element in submodel_elements
            ):
                submodel_elements.append(submodel_element)

    basyx_submodel = model.Submodel(
        id_short=get_template_id(model_type),
        id_=model.Identifier(get_template_id(model_type)),
        # description=convert_util.get_basyx_description_from_model(model_type)=convert_util.get_basyx_description_from_model(model_type),
        description={
            "en": f"Submodel with id {get_template_id(model_type)} that contains submodel elements"
        },
        embedded_data_specifications=convert_util.get_data_specification_for_model_template(
            model_type
        )
        + submodel_element_data_specifications,
        semantic_id="",
        submodel_element=submodel_elements,
    )
    return basyx_submodel


def create_submodel_element_template(
    attribute_name: str,
    attribute_type: Union[
        type[aas_model.SubmodelElementCollection],
        type[str],
        type[float],
        type[int],
        type[bool],
        type[tuple],
        type[list],
        type[set],
    ],
) -> Optional[model.SubmodelElement]:
    """
    Create a basyx SubmodelElement from a model SubmodelElementCollection or a primitive type

    Args:
        attribute_name (str): Name of the attribute that is used for ID and id_short
        attribute_type (Union[type[aas_model.SubmodelElementCollection], type[str], type[float], type[int], type[bool], type[tuple], type[list], type[set]): Type of the attribute


    Returns:
        model.SubmodelElement: basyx SubmodelElement
    """
    if not attribute_type:
        return
    if typing.get_origin(attribute_type) == dict:
        # Dict[str, X] container fields (e.g. the base ``value`` /
        # ``submodel_element`` containers) hold heterogeneous children that a
        # named-field template cannot represent as a single element — skip.
        return
    if (
        typing.get_origin(attribute_type) == list
        or typing.get_origin(attribute_type) == tuple
        or typing.get_origin(attribute_type) == set
    ):
        sml = create_submodel_element_list(attribute_name, attribute_type)
        return sml
    elif attribute_type == aas_model.Reference:
        key = model.Key(
            type_=model.KeyTypes.ASSET_ADMINISTRATION_SHELL,
            value=get_template_id(attribute_type),
        )
        reference = model.ModelReference(key=(key,), type_="")
        reference_element = model.ReferenceElement(
            id_short=attribute_name,
            value=reference,
        )
        return reference_element
    elif typing.get_origin(attribute_type) is typing.Literal:
        property = create_property(attribute_name, str)
        return property
    elif issubclass(attribute_type, Enum):
        property = create_property(attribute_name, str)
        return property
    elif issubclass(attribute_type, aas_model.SubmodelElementCollection):
        smc = create_submodel_element_collection(attribute_type)
        return smc
    elif issubclass(attribute_type, aas_model.SubmodelElementList):
        return create_submodel_element_list_template(attribute_name, attribute_type)
    elif issubclass(attribute_type, aas_model.Entity):
        # Entities are represented as SMC templates in the basyx direction.
        return create_submodel_element_collection(attribute_type)
    elif issubclass(attribute_type, aas_model.Operation):
        return model.Operation(id_short=attribute_name)
    elif issubclass(attribute_type, aas_model.Capability):
        return model.Capability(id_short=attribute_name)
    elif issubclass(attribute_type, aas_model.Property):
        return model.Property(id_short=attribute_name, value_type=model.datatypes.String)
    elif issubclass(attribute_type, aas_model.MultiLanguageProperty):
        return model.MultiLanguageProperty(id_short=attribute_name)
    elif issubclass(attribute_type, aas_model.Range):
        return model.Range(id_short=attribute_name, value_type=model.datatypes.String)
    elif issubclass(attribute_type, aas_model.ReferenceElement):
        return model.ReferenceElement(id_short=attribute_name)
    elif issubclass(attribute_type, aas_model.RelationshipElement):
        empty_ref = model.ExternalReference(
            key=(
                model.Key(
                    type_=model.KeyTypes.GLOBAL_REFERENCE,
                    value="https://example.com/reference",
                ),
            )
        )
        return model.RelationshipElement(
            id_short=attribute_name, first=empty_ref, second=empty_ref
        )
    elif issubclass(attribute_type, aas_model.File):
        return create_file(attribute_type)
    elif issubclass(attribute_type, aas_model.Blob):
        return create_blob(attribute_type)
    else:
        property = create_property(attribute_name, attribute_type)

        return property


def create_submodel_element_list_template(
    attribute_name: str,
    sml_type: type[aas_model.SubmodelElementList],
) -> model.SubmodelElementList:
    """Create a basyx SubmodelElementList template from a SubmodelElementList subclass.

    The item element type is inferred from the ``value`` field annotation.
    """
    ann = sml_type.model_fields["value"].annotation
    args = typing.get_args(ann)
    item_type = args[0] if args else None

    submodel_elements = []
    if (
        item_type
        and item_type is not NoneType
        and item_type is not typing.Any
        and item_type is not aas_model.SubmodelElement
    ):
        el = create_submodel_element_template(attribute_name, item_type)
        if el is not None:
            submodel_elements.append(el)

    return model.SubmodelElementList(
        id_short=attribute_name,
        type_value_list_element=(
            type(submodel_elements[0]) if submodel_elements else None
        ),
        value_type_list_element=(
            submodel_elements[0].value_type
            if submodel_elements and isinstance(submodel_elements[0], model.Property)
            else None
        ),
        value=submodel_elements,
        order_relevant=True,
    )


def create_property(
    attribute_name: str,
    attribute_type: Union[type[str], type[float], type[int], type[bool]],
) -> model.Property:
    if issubclass(attribute_type, Enum):
        attribute_type = str

    property = model.Property(
        id_short=attribute_name,
        value_type=convert_primitive_type_to_xsdtype(attribute_type),
        value=None,
    )
    return property


def create_submodel_element_collection(
    model_sec: type[aas_model.SubmodelElementCollection],
) -> model.SubmodelElementCollection:
    value = []
    smc_attributes = get_attribute_field_infos(model_sec)
    submodel_element_data_specifications = []

    for attribute_info in smc_attributes:
        if _is_container_field(attribute_info.field_info.annotation):
            continue
        if typing.get_origin(attribute_info.field_info.annotation) == Union:
            types_to_check = [
                type_annotation
                for type_annotation in typing.get_args(
                    attribute_info.field_info.annotation
                )
                if type_annotation != NoneType
            ]
            optional_attribute_data_specification = (
                convert_util.get_optional_data_specification_for_attribute(
                    attribute_info
                )
            )
            if optional_attribute_data_specification:
                submodel_element_data_specifications.append(
                    optional_attribute_data_specification
                )
            union_attribute_data_specification = (
                convert_util.get_union_data_specification_for_attribute(attribute_info)
            )
            if union_attribute_data_specification:
                submodel_element_data_specifications.append(
                    union_attribute_data_specification
                )
        elif attribute_info.field_info.annotation == NoneType:
            continue
        else:
            types_to_check = [attribute_info.field_info.annotation]

        for counter, type_annotation in enumerate(types_to_check):
            if len(types_to_check) > 1:
                attribute_name = f"{attribute_info.name}_{counter}"
            else:
                attribute_name = attribute_info.name
            submodel_element = create_submodel_element_template(
                attribute_name=attribute_name, attribute_type=type_annotation
            )
            attribute_data_specifications = (
                convert_util.get_data_specification_for_attribute(
                    attribute_info, submodel_element
                )
            )
            submodel_element_data_specifications.append(attribute_data_specifications)
            immutable_attribute_data_specification = (
                convert_util.get_immutable_data_specification_for_attribute(
                    attribute_info
                )
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
                submodel_element_data_specifications.append(default_data_specification)
            if submodel_element and not any(
                stored_submodel_element.id_short == submodel_element.id_short
                for stored_submodel_element in value
            ):
                value.append(submodel_element)

    id_short = get_template_id(model_sec)

    smc = model.SubmodelElementCollection(
        id_short=id_short,
        value=value,
        # description=convert_util.get_basyx_description_from_model(model_sec),
        description={
            "en": f"Submodel element collection with id {id_short} that contains submodel elements"
        },
        embedded_data_specifications=convert_util.get_data_specification_for_model_template(
            model_sec
        )
        + submodel_element_data_specifications,
        semantic_id="",
    )
    return smc


def create_submodel_element_list(
    name: str, attribute_type: Union[type[tuple], type[list], type[set]]
) -> model.SubmodelElementList:
    submodel_elements = []
    submodel_element_ids = OrderedDict()
    for el in typing.get_args(attribute_type):
        # TODO: potentially check here because of Unions and Optional types inside lists and sets...
        submodel_element = create_submodel_element_template(name, el)
        if isinstance(submodel_element, model.SubmodelElementCollection):
            if submodel_element.id_short in submodel_element_ids:
                raise ValueError(
                    f"Submodel element collection with id {submodel_element.id_short} already exists in list"
                )
            submodel_element_ids.update({submodel_element.id_short: None})
            patch_id_short_with_temp_attribute(submodel_element)
        submodel_element.id_short = None
        submodel_elements.append(submodel_element)

    if submodel_elements and isinstance(submodel_elements[0], model.Property):
        if len(typing.get_args(attribute_type)) > 1 and not all(
            arg is typing.get_args(attribute_type)[0]
            for arg in typing.get_args(attribute_type)
        ):
            raise ValueError(
                f"Submodel element list with different types is not supported. Please use a SubmodelElementCollection instead."
            )
        value_type_list_element = submodel_elements[0].value_type
        type_value_list_element = type(submodel_elements[0])
    elif submodel_elements and isinstance(
        submodel_elements[0],
        model.Reference
        | model.SubmodelElementCollection
        | model.ReferenceElement
        | model.SubmodelElementList,
    ):
        value_type_list_element = None
        type_value_list_element = type(submodel_elements[0])
    else:
        value_type_list_element = convert_primitive_type_to_xsdtype(str)
        type_value_list_element = model.Property

    if typing.get_origin(attribute_type) == set:
        ordered = False
        iterable_type = "set"
    elif typing.get_origin(attribute_type) == tuple:
        ordered = True
        iterable_type = "tuple"
    elif typing.get_origin(attribute_type) == list:
        ordered = True
        iterable_type = "list"
    else:
        raise ValueError(
            f"Type {attribute_type} is not supported for SubmodelElementList, provided subclass of list, tuple or set"
        )

    sml = model.SubmodelElementList(
        id_short=f"{iterable_type}_of_{get_template_id(typing.get_args(attribute_type)[0])}",
        type_value_list_element=type_value_list_element,
        value_type_list_element=value_type_list_element,
        value=submodel_elements,
        order_relevant=ordered,
    )
    return sml


def create_file(attribute_type: type[aas_model.File]) -> model.File:
    """
    Function generates a basyx file objects from a pydantic File.

    Args:
        attribute_value (aas_model.File): pydantic File instance.

    Returns:
        model.File: Basyx file.
    """
    return model.File(id_short=get_template_id(attribute_type), content_type="unknown")


def create_blob(attribute_type: type[aas_model.Blob]) -> model.Blob:
    """
    Function generates a basyx file objects from a pydantic File.

    Args:
        attribute_value (aas_model.File): pydantic File instance.

    Returns:
        model.File: Basyx file.
    """
    return model.Blob(id_short=get_template_id(attribute_type), content_type="unknown")
