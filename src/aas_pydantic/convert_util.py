import datetime
import json
import re
from typing import Any, Dict, List, Union
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
            key.value == own_id_short(item) for key in data_spec.data_specification.key
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


def get_model_keys_for_data_specification(item: Any) -> typing.Tuple[model.Key]:
    """The key a marker names its element by: an Identifiable's id, a Referable's idShort (pydantic or BaSyx),
    or a plain name (an attribute's, for markers about an attribute rather than an element)."""
    if isinstance(item, str):
        value = item
    elif isinstance(item, (aas_model.AAS, aas_model.Submodel, model.Identifiable)):
        value = item.id
    else:
        value = item.id_short
    return (model.Key(type_=model.KeyTypes.GLOBAL_REFERENCE, value=value),)


def get_data_specification_for_attribute(
    attribute_field_info: AttributeFieldInfo, basyx_attribute: Any
) -> typing.Optional[model.EmbeddedDataSpecification]:
    """The marker naming the attribute that holds ``basyx_attribute``; none for an absent element."""
    if basyx_attribute is None:
        return None
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


# The idShort BaSyx gives a SubmodelElementList item, which has none of its own (AASd-120).
LIST_ITEM_ID_SHORT = "generated_submodel_list_hack_"


def own_id_short(element) -> typing.Optional[str]:
    """An element's idShort. A list item has none in the AAS (AASd-120); its name is the key of its own class
    marker, where it has one (a collection of a named class), else it has no name."""
    id_short = element.id_short
    if id_short and not id_short.startswith(LIST_ITEM_ID_SHORT):
        return id_short
    keys = {spec.data_specification.key[0].value for spec in element.embedded_data_specifications
            if isinstance(spec.data_specification_content, model.DataSpecificationIEC61360)
            and spec.data_specification_content.preferred_name.get("en") == "class"}
    return keys.pop() if len(keys) == 1 else None


def own_display_name(element) -> typing.Optional[dict]:
    """An element's display name, without the one a list item is given by its name (``create_submodel_element_list``):
    that is the item's idShort, not a name of its own."""
    display_name = get_str_display_name(getattr(element, "display_name", None))
    in_list = isinstance(getattr(element, "parent", None), model.SubmodelElementList)
    if display_name is not None and in_list and display_name == {"en": own_id_short(element)}:
        return None
    return display_name


def strip_temp_id_short_attributes(store) -> None:
    """Remove the ``temp_id_short_attribute_*`` Properties from every SubmodelElementCollection in *store*
    (mutates in place).

    Older versions parked a list item's idShort in such a Property; a list item's name is its class marker's key
    now (``own_id_short``), so a store built today has none. Publishers keep calling this for AAS built before.

    Only SMC items of a SubmodelElementList receive the patch, but such a list can
    sit anywhere: in a Submodel, an SMC, an Entity's statements or an Operation's
    variables.
    """
    def _strip_element(el) -> None:
        if isinstance(el, model.Submodel):
            for child in el.submodel_element:
                _strip_element(child)
        elif isinstance(el, model.Entity):
            for child in el.statement:
                _strip_element(child)
        elif isinstance(el, model.Operation):
            for variable in (*el.input_variable, *el.output_variable, *el.in_output_variable):
                _strip_element(variable)
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
