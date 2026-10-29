"""Event affordances (WoT EventAffordance) authored with their classes: MQTT events and OPC UA events, the
notification's data schema built with ``datapoint_from_schema``, added to an interface and serialized."""

from __future__ import annotations

import json

from aas_pydantic.convert_pydantic_model import convert_model_to_submodel
from aas_pydantic.submodel_templates.asset_interfaces_description import ContentType
from basyx.aas.adapter.json import AASToJsonEncoder

from aas_model.constants import (
    AID_EVENT_DATA, AID_EVENT_DEFINITION, AID_OPCUA_EVENT_FIELD, AID_OPCUA_EVENT_TYPE,
)
from aas_model.json_schema_aid import datapoint_from_schema
from aas_model.resource_template.operational import MqttInterfaces
from aas_model.submodel_templates.aid import (
    DmpAssetInterfacesDescription, DmpEvent, DmpEventData, DmpEvents, DmpForm, MqttForm, OpcuaEvent, OpcuaEventData,
    OpcuaEvents,
)
from aas_model.testing import opcua_interface


def _serialized(aid) -> dict:
    return json.loads(json.dumps(convert_model_to_submodel(aid), cls=AASToJsonEncoder))


def _child(element: dict, id_short: str) -> dict:
    children = element.get("submodelElements", element.get("value", []))
    return next(child for child in children if child.get("idShort") == id_short)


def _semantic(element: dict) -> str:
    return element["semanticId"]["keys"][0]["value"]


def _events(serialized: dict, interface: str) -> dict:
    return _child(_child(_child(serialized, interface), "InteractionMetadata"), "events")


def test_mqtt_event_authors_only_what_differs_from_the_wot_defaults():
    aid = MqttInterfaces(id_short="AssetInterfacesDescription")
    aid.id = "urn:test:aid"
    aid.InterfaceTemplateForMQTT["interface_mqtt"].InteractionMetadata.events = DmpEvents(property_name={
        "Finished": DmpEvent(
            title="Finished",
            data=datapoint_from_schema({"type": "object", "properties": {"Code": {"type": "integer"}}},
                                       cls=DmpEventData),
            forms=MqttForm(href="EVT/Finished", mqv_qos="1"),
        ),
    })

    finished = _child(_events(_serialized(aid), "interface_mqtt"), "Finished")
    assert _semantic(finished) == AID_EVENT_DEFINITION
    assert _child(finished, "title")["value"] == "Finished"
    data = _child(finished, "data")
    assert _semantic(data) == AID_EVENT_DATA
    assert _child(_child(_child(data, "properties"), "Code"), "type")["value"] == "integer"
    forms = _child(finished, "forms")
    assert _child(forms, "href")["value"] == "EVT/Finished"
    assert _child(forms, "mqv_qos")["value"] == "1"
    # op (subscribeevent), mqv_controlPacket (subscribe) and mqv_retain
    # (false) are the WoT MQTT binding defaults.
    assert not {"op", "mqv_controlPacket", "mqv_retain"} & {child["idShort"] for child in forms["value"]}


def test_interfaces_get_an_events_container_only_with_events():
    aid = MqttInterfaces(id_short="AssetInterfacesDescription")
    aid.id = "urn:test:aid"
    interaction = _child(_child(_serialized(aid), "interface_mqtt"), "InteractionMetadata")
    assert "events" not in {child["idShort"] for child in interaction["value"]}


def test_opcua_event_selects_fields_and_filters_by_event_type():
    interface = opcua_interface("opc.tcp://device:4840", properties={"State": "/?id=ns=1;s=State"})
    # A field that is not the namespace-0 BrowseName of the same name names its browse path.
    interface.InteractionMetadata.events = OpcuaEvents(property_name={
        "Transition": OpcuaEvent(
            title="Transition", uav_eventType="i=2378",
            data=datapoint_from_schema({"type": "object", "properties": {
                "Message": {"type": "string"},
                "ToStateId": {"type": "string", "uav_eventField": "0:ToState/0:Id"},
            }}, cls=OpcuaEventData),
            forms=DmpForm(href="/?id=i=2253", contentType=ContentType(value="application/octet-stream")),
        ),
    })
    aid = DmpAssetInterfacesDescription(id_short="AssetInterfacesDescription", id="urn:test:aid",
                                        InterfaceTemplateForOPCUA={"interface_opcua": interface})
    serialized = _serialized(aid)

    transition = _child(_events(serialized, "interface_opcua"), "Transition")
    forms = _child(transition, "forms")
    assert _child(forms, "href")["value"] == "/?id=i=2253"
    assert _child(forms, "contentType")["value"] == "application/octet-stream"
    event_type = _child(transition, "uav_eventType")
    assert (_semantic(event_type), event_type["value"]) == (AID_OPCUA_EVENT_TYPE, "i=2378")
    fields = _child(_child(transition, "data"), "properties")
    path = _child(_child(fields, "ToStateId"), "uav_eventField")
    assert (_semantic(path), path["value"]) == (AID_OPCUA_EVENT_FIELD, "0:ToState/0:Id")
    assert "uav_eventField" not in {child["idShort"] for child in _child(fields, "Message")["value"]}
