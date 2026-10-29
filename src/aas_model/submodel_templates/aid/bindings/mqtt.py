"""MQTT binding: AID's MQTT form terms (``mqv_controlPacket``, ``mqv_qos``,
``mqv_retain``, the generated ``forms_MQTT``) and request/reply actions (MQTT 5
Response Topic + Correlation Data)."""

from __future__ import annotations

from typing import Dict, Optional

from aas_pydantic import Property
from aas_pydantic.aas_model import AasIdString
from aas_pydantic.submodel_templates.asset_interfaces_description import (
    EndpointMetadata_t, InterfaceTemplateForMQTT as _BaseMqttInterface, Title, forms_MQTT,
)

from aas_model.constants import AID_MQTT_RESPONSE_TOPIC
from aas_model.submodel_templates.aid.affordances import DmpAction, DmpActions, DmpInteractionMetadata
from aas_model.submodel_templates.aid.forms import DmpActionForm, DmpForm
from aas_model.submodel_templates.aid.interface import DmpEndpointMetadata


class MqvResponseTopic(Property):
    """MQTT 5 request/reply (no W3C term): the topic the device publishes the
    action's result to. The request carries it as its Response Topic together
    with Correlation Data, which the reply echoes. Present = request/reply;
    absent, the action only invokes (it is published one way)."""
    id_short: AasIdString = "mqv_responseTopic"
    semantic_id: str = AID_MQTT_RESPONSE_TOPIC
    description: str = "Topic the action's result is published to (MQTT 5 Response Topic); the reply echoes the request's Correlation Data."


class MqttForm(DmpForm, forms_MQTT):
    """The form of an MQTT property or event: ``href`` is the topic."""


class MqttActionForm(DmpActionForm, forms_MQTT):
    """The form of an MQTT action: ``href`` is the request topic,
    ``mqv_controlPacket`` defaults to ``publish`` (WoT MQTT binding)."""
    mqv_responseTopic: Optional[MqvResponseTopic] = None


class MqttAction(DmpAction):
    forms: MqttActionForm = MqttActionForm()


class MqttActions(DmpActions):
    """Dynamic map of MQTT actions (name → MqttAction)."""
    property_name: Dict[str, MqttAction] = {}


class MqttInteractionMetadata(DmpInteractionMetadata):
    actions: Optional[MqttActions] = None


class MqttInterface(_BaseMqttInterface):
    title: Title = Title()
    EndpointMetadata: EndpointMetadata_t = DmpEndpointMetadata()
    InteractionMetadata: MqttInteractionMetadata = MqttInteractionMetadata()
