import copy
import datetime
import json
import re
from types import NoneType
from typing import Any, Dict, List, Union
import uuid
from basyx.aas import model

import typing

from basyx.aas.model import datatypes
from pydantic import BaseModel, ConfigDict
from pydantic.fields import FieldInfo

from aas_pydantic import aas_model


# ── AAS metadata reader (for Field.json_schema_extra["aas"]) ─────────────

AAS_META_KEY = "aas"


def get_aas_meta(field_info: FieldInfo) -> Dict[str, Any]:
    """Extract AAS metadata from a Pydantic FieldInfo."""
    extra = field_info.json_schema_extra or {}
    if isinstance(extra, dict):
        return extra.get(AAS_META_KEY, {})
    return {}


class AttributeFieldInfo(BaseModel):
    name: str
    field_info: FieldInfo

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AttributeInfo(AttributeFieldInfo):
    value: Any


# ── Model fields that carry AAS metadata, never submodel elements ─────────
# These come from Identifiable/Referable/HasSemantics and must be excluded
# whenever a model is walked to build/convert submodel elements.
META_FIELDS = frozenset(
    {
        "id",
        "id_short",
        "description",
        "display_name",
        "semantic_id",
        "supplemental_semantic_ids",
        "qualifiers",
    }
)


def get_attribute_field_infos(
    obj: Union[
        type[aas_model.AAS],
        type[aas_model.Submodel],
        type[aas_model.SubmodelElementCollection],
    ]
) -> List[AttributeFieldInfo]:
    """
    Returns a dictionary of all attributes of an object that are not None, do not start with an underscore and are not standard attributes of the aas object.

    Args:
        obj (Union[aas_model.AAS, aas_model.Submodel, aas_model.SubmodelElementCollection]): Object to get the attributes from
    Returns:
        List[AttributeFieldInfo]: List of attributes of the object
    """
    attribute_infos = []
    # ``obj`` is a CLASS here (type[...]) — class attribute access, not the
    # deprecated instance access.
    for attribute_name, field_info in obj.model_fields.items():
        if attribute_name in META_FIELDS:
            continue
        if attribute_name.startswith("_"):
            continue
        attribute_infos.append(
            AttributeFieldInfo(name=attribute_name, field_info=field_info)
        )
    return attribute_infos


def get_attribute_infos(
    obj: Union[aas_model.AAS, aas_model.Submodel, aas_model.SubmodelElementCollection]
) -> List[AttributeInfo]:
    """
    Returns a dictionary of all attributes of an object that are not None, do not start with an underscore and are not standard attributes of the aas object.

    Args:
        obj (Union[aas_model.AAS, aas_model.Submodel, aas_model.SubmodelElementCollection]): Object to get the attributes from

    Returns:
        List[AttributeInfo]: List of attributes of the object
    """
    attribute_infos = []
    for attribute_name, field_info in type(obj).model_fields.items():
        if attribute_name in META_FIELDS:
            continue
        if attribute_name.startswith("_"):
            continue
        attribute_value = getattr(obj, attribute_name)
        attribute_infos.append(
            AttributeInfo(
                name=attribute_name, field_info=field_info, value=attribute_value
            )
        )
    return attribute_infos


def get_str_description(langstring_set: model.LangStringSet) -> str:
    """
    Converts a LangStringSet to a string.
    Args:
        langstring_set (model.LangStringSet): LangStringSet to convert
    Returns:
        str: String representation of the LangStringSet
    """
    if not langstring_set:
        return ""
    if "en" in langstring_set:
        return str(langstring_set.get("en"))
    elif "ger" in langstring_set:
        return str(langstring_set.get("ger"))
    elif "de" in langstring_set:
        return str(langstring_set.get("de"))
    else:
        return str(langstring_set.get(list(langstring_set.keys())[0]))


def get_basyx_description_from_model(
    model_object: (
        aas_model.AAS | aas_model.Submodel | aas_model.SubmodelElementCollection
    ),
) -> model.LangStringSet:
    """
    Creates a LangStringSet from an aas model.
    Args:
        model_object (aas_model.AAS | aas_model.Submodel | aas_model.SubmodelElementCollection): The model to get the description from.
    Returns:
        model.LangStringSet: LangStringSet description representation of the model object
    Raises:
        ValueError: If the description of the model object is not a dict or a string
    """
    if not model_object.description:
        return None
    try:
        dict_description = json.loads(model_object.description)
        if not isinstance(dict_description, dict):
            raise ValueError
    except ValueError:
        dict_description = {"en": model_object.description}
    return model.MultiLanguageTextType(dict_description)


def get_basyx_display_name_from_model(
    model_object: typing.Any,
) -> typing.Optional[model.MultiLanguageNameType]:
    """
    Create a basyx MultiLanguageNameType from a model's ``display_name``
    (a lang→text map, mirroring basyx ``Referable.display_name``).
    """
    display_name = getattr(model_object, "display_name", None)
    if not display_name:
        return None
    return model.MultiLanguageNameType(dict(display_name))


def get_str_display_name(
    display_name: typing.Union[model.MultiLanguageNameType, dict, None],
) -> typing.Optional[typing.Dict[str, str]]:
    """
    Convert a basyx display_name (lang→text) to a plain dict, or None when empty.
    """
    if not display_name:
        return None
    return {str(k): str(v) for k, v in dict(display_name).items()}


def get_class_name_from_basyx_model(
    item: typing.Union[
        model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection
    ]
) -> str:
    """
    Returns the class name of an basyx model from the data specifications.

    Args:
        item (model.HasDataSpecification): Basyx model to get the class name from

    Raises:
        ValueError: If no data specifications are found in the item or if no class name is found

    Returns:
        str: Class name of the basyx model
    """
    if not item.embedded_data_specifications:
        return item.id_short
    for data_spec in item.embedded_data_specifications:
        content = data_spec.data_specification_content
        if not isinstance(content, model.DataSpecificationIEC61360):
            continue
        if not content.preferred_name.get("en") == "class":
            continue
        condition_smc = any(
            key.value == item.id_short for key in data_spec.data_specification.key
        )
        condition_aas_sm = hasattr(item, "id") and any(
            key.value == item.id for key in data_spec.data_specification.key
        )
        if not condition_smc and not condition_aas_sm:
            continue

        return content.value
    raise ValueError(
        f"No class name found in item with id {item.id_short} and type {type(item)}"
    )


def get_class_name_from_basyx_template(
    item: typing.Union[model.Submodel, model.SubmodelElementCollection]
) -> str:
    """
    Returns the class name of an basyx model from the data specifications.

    Args:
        item (model.HasDataSpecification): Basyx model to get the class name from

    Raises:
        ValueError: If no data specifications are found in the item or if no class name is found

    Returns:
        str: Class name of the basyx model
    """
    # Field names equal the published id_shorts (camelCase) — the class name
    # is the id_short itself, no case conversion.
    if not item.embedded_data_specifications:
        return item.id_short
    return get_class_name_from_basyx_model(item)


def get_attribute_name_from_basyx_model(
    item: typing.Union[
        model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection
    ],
    referenced_item_id: str,
) -> List[str]:
    """
    Returns the attribute name of the referenced element of the item.

    Args:
        item (typing.Union[model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection]): The container of the refernced item
        referenced_item_id (str): The id of the referenced item

    Raises:
        ValueError: If not data specifications are found in the item or if no attribute name is found

    Returns:
        str: The attribute name of the referenced item
    """
    # Field names equal the published id_shorts (camelCase) — the attribute
    # name is the referenced id_short itself, no case conversion.
    if not item.embedded_data_specifications:
        return referenced_item_id
    attribute_names = []
    for data_spec in item.embedded_data_specifications:
        content = data_spec.data_specification_content
        if not isinstance(content, model.DataSpecificationIEC61360):
            continue
        if not any(
            key.value == referenced_item_id for key in data_spec.data_specification.key
        ):
            continue
        if not content.preferred_name.get("en") == "attribute":
            continue
        attribute_names.append(content.value)
    if attribute_names:
        return attribute_names
    raise ValueError(
        f"Attribute reference to {referenced_item_id} could not be found in {item.id_short} of type {type(item)}"
    )


def get_attribute_names_from_basyx_template(
    item: typing.Union[
        model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection
    ],
    referenced_item_id_short: str,
) -> List[str]:
    """
    Returns the attribute name of the referenced element of the item.

    Args:
        item (typing.Union[model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection]): The container of the refernced item
        referenced_item_id (str): The id of the referenced item

    Raises:
        ValueError: If not data specifications are found in the item or if no attribute name is found

    Returns:
        str: The attribute name of the referenced item
    """
    # Field names equal the published id_shorts (camelCase) — the attribute
    # name is the referenced id_short itself, no case conversion.
    if not item.embedded_data_specifications:
        return [referenced_item_id_short]
    return get_attribute_name_from_basyx_model(item, referenced_item_id_short)


def get_data_specification_for_model_template(
    model_type: typing.Union[
        type[aas_model.AAS],
        type[aas_model.Submodel],
        type[aas_model.SubmodelElementCollection],
    ],
) -> typing.List[model.EmbeddedDataSpecification]:
    return [
        model.EmbeddedDataSpecification(
            data_specification=model.ExternalReference(
                key=(
                    model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE,
                        value=(get_template_id(model_type)),
                    ),
                ),
            ),
            data_specification_content=model.DataSpecificationIEC61360(
                preferred_name=model.LangStringSet({"en": "class"}),
                value=get_template_id(model_type),
            ),
        )
    ]


def get_data_specification_for_model(
    item: typing.Union[
        aas_model.AAS, aas_model.Submodel, aas_model.SubmodelElementCollection
    ],
) -> typing.List[model.EmbeddedDataSpecification]:
    return [
        model.EmbeddedDataSpecification(
            data_specification=model.ExternalReference(
                key=(
                    model.Key(
                        type_=model.KeyTypes.GLOBAL_REFERENCE,
                        value=(
                            item.id
                            if isinstance(
                                item, typing.Union[aas_model.AAS, aas_model.Submodel]
                            )
                            else item.id_short
                        ),
                    ),
                ),
            ),
            data_specification_content=model.DataSpecificationIEC61360(
                preferred_name=model.LangStringSet({"en": "class"}),
                value=item.__class__.__name__.split(".")[-1],
            ),
        )
    ]


def get_model_keys_for_data_specification(
    item: typing.Union[
        NoneType, aas_model.AAS, aas_model.Submodel, aas_model.SubmodelElementCollection
    ] = None,
) -> typing.Tuple[model.Key]:
    if item is None:
        return (
            model.Key(
                type_=model.KeyTypes.GLOBAL_REFERENCE,
                value=uuid.uuid4().hex,
            ),
        )
    return (
        model.Key(
            type_=model.KeyTypes.GLOBAL_REFERENCE,
            value=(
                item.id
                if isinstance(item, typing.Union[aas_model.AAS, aas_model.Submodel])
                else item.id_short
            ),
        ),
    )


def get_data_specification_for_attribute(
    attribute_field_info: AttributeFieldInfo, basyx_attribute: Any
) -> model.EmbeddedDataSpecification:
    model_keys = get_model_keys_for_data_specification(basyx_attribute)
    return model.EmbeddedDataSpecification(
        data_specification=model.ExternalReference(
            key=model_keys,
        ),
        data_specification_content=model.DataSpecificationIEC61360(
            preferred_name=model.LangStringSet({"en": "attribute"}),
            value=attribute_field_info.name,
        ),
    )


def get_optional_data_specification_for_attribute(
    attribute_field_info: AttributeFieldInfo,
) -> typing.Optional[model.EmbeddedDataSpecification]:
    if not (
        typing.get_origin(attribute_field_info.field_info.annotation) is Union
        and type(None) in typing.get_args(attribute_field_info.field_info.annotation)
    ):
        return
    model_keys = get_model_keys_for_data_specification()

    return model.EmbeddedDataSpecification(
        data_specification=model.ExternalReference(
            key=model_keys,
        ),
        data_specification_content=model.DataSpecificationIEC61360(
            preferred_name=model.LangStringSet({"en": "optional"}),
            value=attribute_field_info.name,
        ),
    )


def get_immutable_data_specification_for_attribute_name(
    attribute_name: str,
) -> model.EmbeddedDataSpecification:
    model_keys = get_model_keys_for_data_specification()
    return model.EmbeddedDataSpecification(
        data_specification=model.ExternalReference(
            key=model_keys,
        ),
        data_specification_content=model.DataSpecificationIEC61360(
            preferred_name=model.LangStringSet({"en": "immutable"}),
            value=attribute_name,
        ),
    )


def get_immutable_data_specification_for_attribute(
    attribute_field_info: AttributeFieldInfo,
) -> typing.Optional[model.EmbeddedDataSpecification]:
    if not typing.get_origin(attribute_field_info.field_info.annotation) == tuple:
        return
    return get_immutable_data_specification_for_attribute_name(
        attribute_field_info.name
    )


def get_default_data_specification_for_attribute(
    attribute_field_info: AttributeFieldInfo,
    basyx_attribute: typing.Union[
        NoneType, aas_model.AAS, aas_model.Submodel, aas_model.SubmodelElementCollection
    ],
) -> typing.Optional[model.EmbeddedDataSpecification]:
    default_val = attribute_field_info.field_info.default
    # Avoid IEC61360 crash on empty/falsy defaults
    if default_val is None or default_val == "" or default_val == 0:
        return None
    # Convert model instances to a meaningful string (not Python repr)
    if isinstance(default_val, aas_model.Referable):
        default_str = default_val.id_short
    elif isinstance(default_val, (list, tuple, set)):
        default_str = ", ".join(
            getattr(v, 'id_short', str(v)) for v in default_val
        )
    else:
        default_str = str(default_val)
    # Some defaults have empty id_short or produce empty strings — skip those
    if not default_str or not default_str.strip():
        return None
    model_keys = get_model_keys_for_data_specification(basyx_attribute)
    return model.EmbeddedDataSpecification(
        data_specification=model.ExternalReference(
            key=model_keys,
        ),
        data_specification_content=model.DataSpecificationIEC61360(
            preferred_name=model.LangStringSet({"en": "default"}),
            value=default_str,
        ),
    )


def get_union_data_specification_for_attribute(
    attribute_field_info: AttributeFieldInfo,
) -> typing.Optional[model.EmbeddedDataSpecification]:
    if not (
        typing.get_origin(attribute_field_info.field_info.annotation) == Union
        and len(
            [
                arg
                for arg in typing.get_args(attribute_field_info.field_info.annotation)
                if arg != NoneType
            ]
        )
        > 1
    ):
        return
    model_keys = get_model_keys_for_data_specification()

    return model.EmbeddedDataSpecification(
        data_specification=model.ExternalReference(
            key=model_keys,
        ),
        data_specification_content=model.DataSpecificationIEC61360(
            preferred_name=model.LangStringSet({"en": "union"}),
            value=attribute_field_info.name,
        ),
    )


def get_default_value_from_basyx_model(
    item: Union[
        model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection
    ],
    attribute_id: str,
) -> typing.Any:
    """
    Returns the default value of an attribute

    Args:
        item (Union[model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection]): The item to check
        attribute_name (str): The name of the attribute

    Returns:
        bool: If the attribute is optional
    """
    if not item.embedded_data_specifications:
        return
    for data_spec in item.embedded_data_specifications:
        content = data_spec.data_specification_content
        if not isinstance(content, model.DataSpecificationIEC61360):
            continue
        if not (content.preferred_name.get("en") == "default"):
            continue
        if not any(
            key.value == attribute_id for key in data_spec.data_specification.key
        ):
            continue
        return content.value
    return


def is_attribute_from_basyx_model_immutable(
    item: typing.Union[
        model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection
    ],
    attribute_name: str,
) -> bool:
    """
    Returns if the referenced item of the item is immutable.

    Args:
        item (typing.Union[model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection]): The container of the refernced item
        referenced_item_id (str): The id of the referenced item

    Raises:
        ValueError: If not data specifications are found in the item or if no attribute name is found

    Returns:
        bool: If the referenced item is immutable
    """
    if not item.embedded_data_specifications:
        return False
    for data_spec in item.embedded_data_specifications:
        content = data_spec.data_specification_content
        if not isinstance(content, model.DataSpecificationIEC61360):
            continue
        if not content.preferred_name.get("en") == "immutable":
            continue
        return content.value == attribute_name
    return False


def is_optional_attribute_type(
    item: Union[
        model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection
    ],
    attribute_name: str,
) -> bool:
    """
    Returns if an attribute of an aas is optional.

    Args:
        item (Union[model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection]): The item to check
        attribute_name (str): The name of the attribute

    Returns:
        bool: If the attribute is optional
    """
    if not item.embedded_data_specifications:
        return True
    for data_spec in item.embedded_data_specifications:
        content = data_spec.data_specification_content
        if not isinstance(content, model.DataSpecificationIEC61360):
            continue
        if not (
            content.preferred_name.get("en") == "optional"
            and content.value == attribute_name
        ):
            continue
        return True
    return False


def is_union_attribute_type(
    item: Union[
        model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection
    ],
    attribute_name: str,
) -> bool:
    """
    Returns if an attribute of an aas is optional.

    Args:
        item (Union[model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection]): Aas to get the attribute from
        attribute_name (str): The name of the attribute

    Returns:
        bool: If the attribute is optional
    """
    if not item.embedded_data_specifications:
        return False
    for data_spec in item.embedded_data_specifications:
        content = data_spec.data_specification_content
        if not isinstance(content, model.DataSpecificationIEC61360):
            continue
        if not (
            content.preferred_name.get("en") == "union"
            and content.value == attribute_name
        ):
            continue
        return True
    return False


def get_template_id(
    element: Union[
        type[aas_model.AAS],
        type[aas_model.Submodel],
        type[aas_model.SubmodelElementCollection],
    ]
) -> str:
    return element.__name__.split(".")[-1]


def get_id_short(
    element: Union[
        aas_model.AAS, aas_model.Submodel, aas_model.SubmodelElementCollection
    ]
) -> str:
    if element.id_short:
        return element.id_short
    else:
        return element.id


def get_semantic_id(
    model_object: aas_model.Submodel | aas_model.SubmodelElementCollection,
) -> str | None:
    if model_object.semantic_id:
        semantic_id = model.ExternalReference(
            key=(model.Key(model.KeyTypes.GLOBAL_REFERENCE, model_object.semantic_id),)
        )
    else:
        semantic_id = None
    return semantic_id


def get_value_type_of_attribute(
    attribute: Union[str, int, float, bool]
) -> model.datatypes:
    if isinstance(attribute, bool):
        return model.datatypes.Boolean
    elif isinstance(attribute, int):
        return model.datatypes.Integer
    elif isinstance(attribute, float):
        return model.datatypes.Double
    else:
        return model.datatypes.String


def get_semantic_id_value_of_model(
    basyx_model: typing.Union[model.Submodel, model.SubmodelElement]
) -> str:
    """
    Returns the semantic id of a submodel or submodel element.

    Args:
        basyx_model (model.Submodel | model.SubmodelElement): Basyx model to get the semantic id from.

    Returns:
        str: Semantic id of the model.
    """
    if not isinstance(basyx_model, model.HasSemantics):
        raise NotImplementedError("Type not implemented:", type(basyx_model))
    if not basyx_model.semantic_id:
        return ""
    return basyx_model.semantic_id.key[0].value


def convert_basyx_value_type_to_xsd(value_type: Any) -> str:
    """Map a basyx datatype class back to its xs:type string (e.g. datatypes.String -> 'xs:string')."""
    for name, cls in datatypes.XSD_TYPE_CLASSES.items():
        if value_type is cls:
            return name
    return "xs:string"


def key_type_to_basyx_name(type_str: str) -> str:
    """Convert an AAS KeyType string (PascalCase, as in AAS JSON / kg-bridge)
    to the basyx KeyTypes enum member name (SCREAMING_SNAKE_CASE).

    e.g. 'AssetAdministrationShell' -> 'ASSET_ADMINISTRATION_SHELL'
    """
    if not type_str:
        return type_str
    return re.sub(r"(?<!^)(?=[A-Z])", "_", type_str).upper()


def key_type_from_basyx_name(name: str) -> str:
    """Convert a basyx KeyTypes enum member name to the AAS KeyType string
    (PascalCase, as in AAS JSON / kg-bridge).

    e.g. 'ASSET_ADMINISTRATION_SHELL' -> 'AssetAdministrationShell'
    """
    if not name:
        return name
    return "".join(p.capitalize() for p in name.split("_") if p)


def convert_xsdtype_to_primitive_type(
    xsd_data_type: model.DataTypeDefXsd,
) -> aas_model.PrimitiveSubmodelElement:
    if xsd_data_type == datatypes.Duration:
        return str
    elif xsd_data_type == datatypes.DateTime:
        return datetime.datetime
    elif xsd_data_type == datatypes.Date:
        return datetime.datetime
    elif xsd_data_type == datatypes.Time:
        return datetime.time
    # TODO: implement GyearMonth, GYer, GMonthDay, GDay, GMonth
    elif xsd_data_type == datatypes.Boolean:
        return bool
    elif xsd_data_type == datatypes.Base64Binary:
        return bytes
    elif xsd_data_type == datatypes.HexBinary:
        return bytes
    elif xsd_data_type == datatypes.Float:
        return float
    elif xsd_data_type == datatypes.Double:
        return float
    elif xsd_data_type == datatypes.Decimal:
        return float
    elif xsd_data_type == datatypes.Integer:
        return int
    elif xsd_data_type == datatypes.Long:
        return int
    elif xsd_data_type == datatypes.Int:
        return int
    elif xsd_data_type == datatypes.Short:
        return int
    elif xsd_data_type == datatypes.Byte:
        return int
    elif xsd_data_type == datatypes.NonPositiveInteger:
        return int
    elif xsd_data_type == datatypes.NegativeInteger:
        return int
    elif xsd_data_type == datatypes.NonNegativeInteger:
        return int
    elif xsd_data_type == datatypes.PositiveInteger:
        return int
    elif xsd_data_type == datatypes.UnsignedLong:
        return int
    elif xsd_data_type == datatypes.UnsignedInt:
        return int
    elif xsd_data_type == datatypes.UnsignedShort:
        return int
    elif xsd_data_type == datatypes.UnsignedByte:
        return int
    elif xsd_data_type == datatypes.AnyURI:
        return str
    elif xsd_data_type == datatypes.String:
        return str
    elif xsd_data_type == datatypes.NormalizedString:
        return str


def convert_primitive_type_to_xsdtype(
    primitive_type: aas_model.PrimitiveSubmodelElement,
) -> model.DataTypeDefXsd:
    if primitive_type == str:
        return datatypes.String
    elif primitive_type == datetime.datetime:
        return datatypes.DateTime
    elif primitive_type == datetime.time:
        return datatypes.Time
    elif primitive_type == bool:
        return datatypes.Boolean
    elif primitive_type == bytes:
        return datatypes.Base64Binary
    elif primitive_type == float:
        return datatypes.Double
    elif primitive_type == int:
        return datatypes.Integer
    else:
        raise NotImplementedError("Type not implemented:", primitive_type)


def patch_id_short_with_temp_attribute(
    submodel_element_collection: model.SubmodelElementCollection,
) -> None:
    """AASd-120 patch: store an SMC item's id_short as a temporary Property
    inside its own ``value``.

    ``SubmodelElementList`` items must not carry an id_short in basyx
    (AASd-120), so the id_short is parked in a synthetic ``temp_id_short_…``
    Property that ``unpatch_id_short_from_temp_attribute`` / 
    ``unpatched_id_short_smc_copy`` restore on the way back."""
    temp_id_short_property = model.Property(
        id_short="temp_id_short_attribute_" + uuid.uuid4().hex,
        value_type=convert_primitive_type_to_xsdtype(str),
        value=submodel_element_collection.id_short,
    )
    submodel_element_collection.value.add(temp_id_short_property)


def unpatch_id_short_from_temp_attribute(smec: model.SubmodelElementCollection):
    """
    Unpatches the id_short attribute of a SubmodelElementCollection from the temporary attribute.

    Args:
        sm_element (model.SubmodelElementCollection): SubmodelElementCollection to unpatch.
    """
    if not smec.id_short.startswith("generated_submodel_list_hack_"):
        return smec
    no_temp_values = []
    id_short = None
    for sm_element in smec.value:
        if isinstance(sm_element, model.Property) and sm_element.id_short.startswith(
            "temp_id_short_attribute"
        ):
            id_short = sm_element.value
            continue
        no_temp_values.append(sm_element)

    if not id_short:
        # return smec
        new_id_short = smec.parent.id_short
        smec.parent = None
        smec.id_short = new_id_short
        return smec

    for value in no_temp_values:
        smec.value.remove(value)
    new_smec = model.SubmodelElementCollection(
        id_short=id_short,
        value=no_temp_values,
        embedded_data_specifications=smec.embedded_data_specifications,
    )
    return new_smec


def unpatched_id_short_smc_copy(smec: model.SubmodelElementCollection):
    """Return a copy of *smec* with the real id_short restored from the temp
    attribute, WITHOUT mutating the original (AASd-120 list items).

    The container-style back-conversion uses this so the source basyx store
    is left intact — the mutating variant above is only safe in the
    named-field path, which repatches the original afterward.
    """
    if not smec.id_short.startswith("generated_submodel_list_hack_"):
        return smec
    work = copy.deepcopy(smec)
    return unpatch_id_short_from_temp_attribute(work)


def repatch_id_short_to_temp_attribute(
    smec: model.SubmodelElementCollection, temp_smec: model.SubmodelElementCollection
):
    """
    Repatches the id_short attribute of a SubmodelElementCollection to the temporary attribute.

    Args:
        sm_element (model.SubmodelElementCollection): SubmodelElementCollection to repatch.
    """
    values_to_repatch = []
    for sm_element in temp_smec.value:
        values_to_repatch.append(sm_element)
    temp_smec.value.clear()
    for sm_element in values_to_repatch:
        smec.value.add(sm_element)
    return smec


def strip_temp_id_short_attributes(store) -> None:
    """Remove the AASd-120 ``temp_id_short_attribute_*`` patch Properties from
    every SubmodelElementCollection in *store* (mutates in place).

    The temp attribute is only a round-trip vehicle for restoring an SML
    item's id_short on the way back; it must never appear in a serialized or
    published AAS.  Call before ``object_store_to_json`` / AASX export, e.g.::

        strip_temp_id_short_attributes(obj_store)
        json_str = json_serialization.object_store_to_json(obj_store)

    Only SMC items of a SubmodelElementList ever receive the patch, so walking
    Submodel / SMC / SML containers is sufficient (Entity/Operation children
    never get one).
    """
    def _strip_element(el) -> None:
        if isinstance(el, model.Submodel):
            for child in el.submodel_element:
                _strip_element(child)
        elif isinstance(el, model.SubmodelElementCollection):
            if el.value:
                for child in list(el.value):
                    if (
                        isinstance(child, model.Property)
                        and child.id_short
                        and child.id_short.startswith("temp_id_short_attribute_")
                    ):
                        el.value.remove(child)
                    else:
                        _strip_element(child)
        elif isinstance(el, model.SubmodelElementList):
            for child in el.value:
                _strip_element(child)

    for obj in store:
        if isinstance(obj, model.AssetAdministrationShell):
            for sm in obj.submodel:
                _strip_element(sm)
        elif isinstance(obj, model.Submodel):
            _strip_element(obj)
