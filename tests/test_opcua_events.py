"""WoT event affordances in the AID extension: the protocol-neutral
EventAffordance terms and the OPC UA event vocabulary (DMP terms; OPC 10101
v1.00 defines none), serialized to AAS JSON as the DMP projects them."""

from __future__ import annotations

import json

from aas_pydantic.convert_pydantic_model import convert_model_to_submodel
from basyx.aas.adapter.json import AASToJsonEncoder

from aas_model.constants import (
    AID_EVENT_DEFINITION, AID_EVENT_CANCELLATION, AID_EVENT_DATA, AID_EVENT_DATA_RESPONSE,
    AID_EVENT_SUBSCRIPTION, AID_OPCUA_EVENT_FIELD, AID_OPCUA_EVENT_TYPE,
    BASE_URL,
)
from aas_model.submodel_templates import DmpEvent
from aas_model.submodel_templates.aid import DmpAssetInterfacesDescription
from aas_model.testing import opcua_interface

TRANSITION_FIELDS = {
    "Message": {"type": "string"},
    "Severity": {"type": "integer"},
    "ToState": ({"type": "string"}, "0:ToState"),
    "ToStateId": ({"type": "string"}, "0:ToState/0:Id"),
}


def _aid() -> DmpAssetInterfacesDescription:
    interface = opcua_interface("opc.tcp://device:4840", properties={"State": "/?id=ns=1;s=State"},
                                events={"Transition": ("i=2253", TRANSITION_FIELDS, "i=2378")})
    return DmpAssetInterfacesDescription(id_short="AssetInterfacesDescription", id=f"{BASE_URL}/aid/test",
                                         InterfaceTemplateForOPCUA={"interface_opcua": interface})


def _serialized() -> dict:
    return json.loads(json.dumps(convert_model_to_submodel(_aid()), cls=AASToJsonEncoder))


def _child(element: dict, id_short: str) -> dict:
    children = element.get("submodelElements", element.get("value", []))
    return next(child for child in children if child.get("idShort") == id_short)


def _semantic(element: dict) -> str:
    return element["semanticId"]["keys"][0]["value"]


def _event(serialized: dict) -> dict:
    interaction = _child(_child(serialized, "interface_opcua"), "InteractionMetadata")
    return _child(_child(interaction, "events"), "Transition")


def test_event_affordance_carries_every_wot_event_term():
    fields = DmpEvent.model_fields
    assert {"title", "subscription", "data", "dataResponse", "cancellation", "forms"} <= set(fields)
    assert fields["subscription"].annotation.__args__[0].model_fields["semantic_id"].default == AID_EVENT_SUBSCRIPTION
    assert fields["data"].annotation.__args__[0].model_fields["semantic_id"].default == AID_EVENT_DATA
    assert fields["dataResponse"].annotation.__args__[0].model_fields["semantic_id"].default == AID_EVENT_DATA_RESPONSE
    assert fields["cancellation"].annotation.__args__[0].model_fields["semantic_id"].default == AID_EVENT_CANCELLATION


def test_opcua_event_names_notifier_event_type_and_selected_fields():
    event = _event(_serialized())
    assert _semantic(event) == AID_EVENT_DEFINITION
    forms = _child(event, "forms")
    assert _child(forms, "href")["value"] == "/?id=i=2253"
    assert "op" not in {child["idShort"] for child in forms["value"]}  # default: subscribeevent
    assert _child(forms, "contentType")["value"] == "application/octet-stream"

    event_type = _child(event, "uav_eventType")
    assert (_semantic(event_type), event_type["value"]) == (AID_OPCUA_EVENT_TYPE, "i=2378")

    data = _child(event, "data")
    assert _semantic(data) == AID_EVENT_DATA
    assert _child(data, "type")["value"] == "object"
    fields = {field["idShort"]: field for field in _child(data, "properties")["value"]}
    assert list(fields) == ["Message", "Severity", "ToState", "ToStateId"]
    assert "uav_eventField" not in {child["idShort"] for child in fields["Message"]["value"]}
    path = _child(fields["ToStateId"], "uav_eventField")
    assert (_semantic(path), path["value"]) == (AID_OPCUA_EVENT_FIELD, "0:ToState/0:Id")
    assert "subscription" not in {child["idShort"] for child in event["value"]}


def test_opcua_event_terms_use_the_project_namespace():
    event = _event(_serialized())

    def walk(element: dict):
        if element.get("idShort", "").startswith("uav_event"):
            assert _semantic(element).startswith(f"{BASE_URL}/aid/"), element["idShort"]
        for child in element.get("value", []) if isinstance(element.get("value"), list) else []:
            walk(child)
    walk(event)
