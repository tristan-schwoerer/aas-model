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


def key_type_to_basyx_name(type_str: str) -> str:
    """Convert an AAS KeyType string (PascalCase, as in AAS JSON / kg-bridge)
    to the basyx KeyTypes enum member name (SCREAMING_SNAKE_CASE).

    e.g. 'AssetAdministrationShell' -> 'ASSET_ADMINISTRATION_SHELL'
    """
    if not type_str:
        return type_str
    return re.sub(r"(?<!^)(?=[A-Z])", "_", type_str).upper()


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
