"""Operation mappings: the command (IDTA Sources/Transformation/Sinks) and the
response (the AIMC ``Response*`` additions), and MQTT event affordances in
the AID extension, serialized to AAS JSON as the DMP projects them."""

from __future__ import annotations

import json

from aas_pydantic.convert_pydantic_model import convert_model_to_aas
from basyx.aas.adapter.json import json_serialization

from aas_model.constants import AID_EVENT_DATA, AID_EVENT_DEFINITION, AIMC_RESPONSE_TRANSFORMATION, BASE_URL
from aas_model.resource_template import ResourceTypeAAS
from aas_model.submodel_templates import (
    Aimc, AimcMappingConfiguration, AimcMappingConfigurations, DmpResponseSink, DmpResponseSource,
)
from aas_model.submodel_templates.aid import DmpAssetInterfacesDescription
from aas_model.testing import aimc_ref, mqtt_interface
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import SinksItem, SourcesItem


def _submodels(**submodels) -> dict:
    asset = ResourceTypeAAS(id_short="TwoPhase", id=f"{BASE_URL}/aas/TwoPhase",
                            asset_type="TwoPhase", **submodels)
    doc = json.loads(json_serialization.object_store_to_json(convert_model_to_aas(asset)))
    return {submodel["idShort"]: submodel for submodel in doc["submodels"]}


def _child(element: dict, id_short: str) -> dict:
    children = element.get("submodelElements", element.get("value", []))
    return next(child for child in children if child.get("idShort") == id_short)


def _semantic(element: dict) -> str:
    return element["semanticId"]["keys"][0]["value"]


def test_mqtt_event_affordance_serializes_as_a_wot_event_with_its_data_schema():
    interface = mqtt_interface("mqtt://broker:1883/base", properties={"State": "/state"}, events={
        "Finished": ("/events/finished", {"type": "object", "properties": {"code": {"type": "integer"}}})})
    aid = DmpAssetInterfacesDescription(id_short="AssetInterfacesDescription",
                                        InterfaceTemplateForMQTT={"interface_mqtt": interface})

    serialized = _submodels(asset_interfaces_description=aid)["AssetInterfacesDescription"]
    interaction = _child(_child(serialized, "interface_mqtt"), "InteractionMetadata")
    events = _child(interaction, "events")
    finished = _child(events, "Finished")
    assert _semantic(events) == "https://www.w3.org/2019/wot/td#EventAffordance"
    assert _semantic(finished) == AID_EVENT_DEFINITION
    assert _semantic(_child(finished, "data")) == AID_EVENT_DATA
    assert _child(_child(finished, "data"), "type")["value"] == "object"
    assert "op" not in {child["idShort"] for child in _child(finished, "forms")["value"]}
    assert [child["idShort"] for child in events["value"]] == ["Finished"]


def test_interfaces_without_events_serialize_no_events_container():
    aid = DmpAssetInterfacesDescription(id_short="AssetInterfacesDescription", InterfaceTemplateForMQTT={
        "interface_mqtt": mqtt_interface("mqtt://broker:1883/base", properties={"State": "/state"})})
    serialized = _submodels(asset_interfaces_description=aid)["AssetInterfacesDescription"]
    interaction = _child(_child(serialized, "interface_mqtt"), "InteractionMetadata")
    assert "events" not in {child["idShort"] for child in interaction["value"]}


RESPONSE_LUA = """
function aimc_main(sources)
  return { Start = { Result = sources.Result }, LastResult = sources.Result }
end
"""
AID = "{aas_id}/submodels/AssetInterfacesDescription"
# DMP additions to the IDTA MappingConfiguration: none may claim an IDTA semantic id.
EXTENSION_FIELDS = {"ResponseSources", "ResponseTransformation", "ResponseSinks", "Evaluation"}


def _mqtt(*path: str):
    return aimc_ref(AID, "interface_mqtt", "InteractionMetadata", *path)


def _start_mapping():
    """MQTT 5 request/reply: the command, the reply's Result member, and a
    best-effort copy of it into the AAS."""
    return AimcMappingConfiguration(
        id_short="Start",
        Sources=[
            SourcesItem(
                SourceId="Start",
                Source=aimc_ref("{aas_id}/submodels/ControlComponentInstance", "Skills", "Start", "operation"),
            )
        ],
        Sinks=[SinksItem(SinkId="Start", Sink=_mqtt("actions", "Start"))],
        Transformation="function aimc_main(sources) return { Start = sources.Start } end",
        ResponseSources=[DmpResponseSource(SourceId="Result", Source=_mqtt("actions", "Start", "output", "Result"))],
        ResponseTransformation=RESPONSE_LUA,
        ResponseSinks=[
            DmpResponseSink(SinkId="LastResult", Sink=aimc_ref("{aas_id}/submodels/Variables", "LastResult"))
        ],
        DefaultPollingInterval="0.0",
    )


def _serialized_aimc() -> dict:
    aimc = Aimc(id_short="AIMC", MappingConfigurations=AimcMappingConfigurations(value=[_start_mapping()]))
    return _submodels(asset_interfaces_mapping_configuration=aimc)["AIMC"]


def _serialized_mapping() -> dict:
    return _child(_serialized_aimc(), "MappingConfigurations")["value"][0]


def test_operation_mapping_serializes_command_and_response():
    entry = _serialized_mapping()
    assert [_child(item, "SinkId")["value"] for item in _child(entry, "Sinks")["value"]] == ["Start"]
    assert _semantic(_child(entry, "ResponseTransformation")) == AIMC_RESPONSE_TRANSFORMATION
    result = _child(entry, "ResponseSources")["value"][0]
    assert _child(result, "Source")["value"]["keys"][-1]["value"] == "Result"
    assert {child["idShort"] for child in entry["value"]}.isdisjoint(
        {"StatusSources", "StatusTransformation", "StatusTimeout"})
    assert [_child(item, "SourceId")["value"] for item in _child(entry, "ResponseSources")["value"]] == ["Result"]
    assert [_child(item, "SinkId")["value"] for item in _child(entry, "ResponseSinks")["value"]] == ["LastResult"]


def test_every_dmp_addition_uses_the_project_namespace():
    entry = _serialized_mapping()

    def walk(element: dict, inside_extension: bool):
        extension = inside_extension or element.get("idShort") in EXTENSION_FIELDS
        if extension and "semanticId" in element:
            assert _semantic(element).startswith(f"{BASE_URL}/aimc/"), \
                f"{element.get('idShort')} has the non-project semantic id {_semantic(element)}"
        for child in element.get("value", []) if isinstance(element.get("value"), list) else []:
            walk(child, extension)

    seen = {child["idShort"] for child in entry["value"]}
    assert EXTENSION_FIELDS - {"Evaluation"} <= seen
    walk(entry, False)
