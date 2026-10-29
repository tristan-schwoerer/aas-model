"""TD DataSchema terms AID marks EXTERNAL (docs/aid-extension.md §3.6) and the
form's ``additionalResponses`` (§3.4): built from JSON Schema, exported to AAS
JSON and parsed back without loss; unrepresentable schemas fail loudly."""

from __future__ import annotations

import pytest

from aas_json import parse_submodel_dict
from aas_model.constants import AID_WOT_ONE_OF, AID_WOT_REQUIRED
from aas_model.json_schema_aid import datapoint_from_schema, load_schema, schema_from_datapoint, without
from aas_model.submodel_templates.aid import (
    AdditionalResponse, AdditionalResponseSchema, AdditionalResponseSuccess, AdditionalResponses,
    DmpActionOutput, DmpAssetInterfacesDescription,
)
from aas_model.testing import build_aid, mqtt_interface
from aas_pydantic.submodel_templates.asset_interfaces_description import ContentType

from test_serde import _roundtrip

# Every term of the extension, nested: members, items holding objects, oneOf branches.
SCHEMA = {
    "type": "object",
    "properties": {
        "State": {"type": "string", "enum": ["SUCCESS", "FAILURE"]},
        "Note": {"oneOf": [{"type": "string", "maxLength": 80}, {"type": "null"}]},
        "Speed": {"type": "number", "exclusiveMinimum": 0, "exclusiveMaximum": 2.5, "multipleOf": 0.5},
        "Code": {"type": "string", "pattern": "^[A-Z]{3}$", "format": "uuid", "readOnly": True},
        "Image": {"type": "string", "contentEncoding": "base64", "contentMediaType": "image/png"},
        "Stations": {"type": "array", "minItems": 1, "items": {
            "type": "object",
            "properties": {"Name": {"type": "string"}, "Position": {"type": "array", "items": {"type": "number"}}},
            "required": ["Name"]}},
    },
    "required": ["State", "Stations"],
}


def _exported_output(output) -> tuple[dict, DmpActionOutput]:
    interface = mqtt_interface("mqtt://broker:1883/base/", actions={"Start": ("CMD/Start", "DATA/Start")})
    interface.InteractionMetadata.actions.property_name["Start"].output = output
    serialized = _roundtrip(build_aid(mqtt=interface))
    back = parse_submodel_dict(serialized, DmpAssetInterfacesDescription)
    return serialized, back.InterfaceTemplateForMQTT["interface_mqtt"].InteractionMetadata.actions.property_name["Start"]


def _find(element, id_short):
    if isinstance(element, dict):
        if element.get("idShort") == id_short:
            return element
        element = element.get("submodelElements", element.get("value"))
    if isinstance(element, list):
        for child in element:
            found = _find(child, id_short)
            if found is not None:
                return found
    return None


def test_every_data_schema_term_survives_export_and_parse():
    serialized, action = _exported_output(datapoint_from_schema(SCHEMA, cls=DmpActionOutput))
    assert schema_from_datapoint(action.output) == SCHEMA
    # the AAS shapes: required and oneOf are lists with their W3C IRIs
    required = _find(serialized, "required")
    assert required["modelType"] == "SubmodelElementList"
    assert required["semanticId"]["keys"][0]["value"] == AID_WOT_REQUIRED
    one_of = _find(serialized, "oneOf")
    assert one_of["modelType"] == "SubmodelElementList" and one_of["typeValueListElement"] == "SubmodelElementCollection"
    assert one_of["semanticId"]["keys"][0]["value"] == AID_WOT_ONE_OF
    assert all("idShort" not in branch for branch in one_of["value"]), "AASd-120: list members have no idShort"


def test_no_required_qualifier_is_written():
    serialized, _ = _exported_output(datapoint_from_schema(SCHEMA, cls=DmpActionOutput))

    def qualifiers(element):
        if isinstance(element, dict):
            yield from (q["type"] for q in element.get("qualifiers", []))
            for value in element.values():
                yield from qualifiers(value)
        elif isinstance(element, list):
            for value in element:
                yield from qualifiers(value)
    assert "RequiredProperties" not in set(qualifiers(serialized))


def test_additional_responses_with_inline_schemas_survive_export_and_parse():
    interface = mqtt_interface("mqtt://broker:1883/base/", actions={"Start": ("CMD/Start", "DATA/Start")})
    form = interface.InteractionMetadata.actions.property_name["Start"].forms
    error = datapoint_from_schema({"type": "object", "properties": {"Error": {"type": "string"}}, "required": ["Error"]},
                                  cls=AdditionalResponseSchema)
    form.additionalResponses = AdditionalResponses(value=[AdditionalResponse(
        id_short="failure", success=AdditionalResponseSuccess(value="false"),
        contentType=ContentType(value="application/json"), schema=error)])
    back = parse_submodel_dict(_roundtrip(build_aid(mqtt=interface)), DmpAssetInterfacesDescription)
    [response] = back.InterfaceTemplateForMQTT["interface_mqtt"].InteractionMetadata.actions \
        .property_name["Start"].forms.additionalResponses.value
    assert response.success.value == "false"
    assert response.contentType.value == "application/json"
    assert schema_from_datapoint(response.schema) == {
        "type": "object", "properties": {"Error": {"type": "string"}}, "required": ["Error"]}


@pytest.mark.parametrize("schema, expected", [
    ({"type": ["string", "null"], "maxLength": 8, "title": "Note"},
     {"title": "Note", "oneOf": [{"type": "string", "maxLength": 8}, {"type": "null"}]}),
    ({"type": "array", "prefixItems": [{"type": "number", "title": "X"}, {"type": "number", "title": "Y"}]},
     {"type": "array", "items": {"type": "number"}}),
])
def test_rewrites_that_keep_the_meaning(schema, expected):
    assert schema_from_datapoint(datapoint_from_schema(schema)) == expected


@pytest.mark.parametrize("schema, message", [
    ({"anyOf": [{"type": "string"}]}, "'anyOf' has no TD/AID representation"),
    ({"type": "object", "additionalProperties": {"type": "string"}}, "'additionalProperties' has no TD/AID"),
    ({"type": "array", "items": [{"type": "number"}]}, "an array of schemas (a tuple)"),
    ({"type": "array", "prefixItems": [{"type": "number"}, {"type": "string"}]}, "positions with different schemas"),
    ({"type": ["integer", "number"]}, "overlaps"),
    ({"type": "object", "properties": {"a": {}}, "required": ["b"]}, "['b'] are not members"),
    ({"type": "object", "properties": {"Deep": {"type": "string", "not": {"const": "x"}}}}, "$/properties/Deep"),
])
def test_unrepresentable_schemas_fail_loudly_with_their_path(schema, message):
    with pytest.raises(ValueError, match=message.replace("$", r"\$").replace("[", r"\[").replace("]", r"\]")
                       .replace("(", r"\(").replace(")", r"\)")):
        datapoint_from_schema(schema)


def test_dropping_a_keyword_is_explicit():
    schema = {"type": "object", "properties": {"Map": {"type": "object", "additionalProperties": {"type": "string"}}}}
    dp = datapoint_from_schema(without(schema, "additionalProperties"))
    assert schema_from_datapoint(dp) == {"type": "object", "properties": {"Map": {"type": "object"}}}


def test_load_schema_inlines_internal_and_nested_references():
    # planarStations: #/$defs references inside items; the nullable Coordinate becomes oneOf
    schema = load_schema("planarStations.schema.json")
    approach = schema["properties"]["Stations"]["items"]["properties"]["Approach Position"]
    assert "$ref" not in str(schema)
    assert approach["items"] == {"type": ["number", "null"]}
    built = schema_from_datapoint(datapoint_from_schema(schema))
    assert built["properties"]["Stations"]["items"]["properties"]["Approach Position"]["items"] == {
        "oneOf": [{"type": "number"}, {"type": "null"}]}


def test_string_list_members_show_their_value_as_display_name():
    serialized, _ = _exported_output(datapoint_from_schema(SCHEMA, cls=DmpActionOutput))
    members = _find(serialized, "required")["value"]
    assert [m["displayName"] for m in members] == [[{"language": "en", "text": "State"}],
                                                   [{"language": "en", "text": "Stations"}]]
    assert all("idShort" not in m for m in members), "AASd-120: list members have no idShort"
