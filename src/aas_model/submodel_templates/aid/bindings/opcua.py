"""OPC UA binding: Method actions (OPC 10101) and events (no OPC 10101
vocabulary; the ``uav_event*`` terms are this project's)."""

from __future__ import annotations

from typing import Dict, Optional

from pydantic import model_validator

from aas_pydantic import Property
from aas_pydantic.aas_model import AasIdString
from aas_pydantic.submodel_templates.asset_interfaces_description import (
    EndpointMetadata_OPCUA, InterfaceTemplateForOPCUA as _BaseOpcuaInterface, Title, forms_OPCUA,
    securityDefinitions_OPCUA,
)

from aas_model.constants import AID_OPCUA_COMPONENT_OF, AID_OPCUA_EVENT_FIELD, AID_OPCUA_EVENT_TYPE
from aas_model.submodel_templates.aid.affordances import (
    DmpAction, DmpActions, DmpEvent, DmpEventData, DmpEvents, DmpInteractionMetadata,
)
from aas_model.submodel_templates.aid.data_schema import DmpDataSchema, DmpSchemaProperties
from aas_model.submodel_templates.aid.forms import DmpActionForm, DmpForm
from aas_model.submodel_templates.aid.interface import DmpEndpointMetadata


# ── Method actions ───────────────────────────────────────────────────────────

class UavComponentOf(Property):
    """``uav:componentOf`` (OPC 10101 §7.1.3): the NodeId of the Object that
    owns the Method. Mandatory on OPC UA actions; the Call service addresses
    a Method as (objectId, methodId)."""
    id_short: AasIdString = "uav_componentOf"
    semantic_id: str = AID_OPCUA_COMPONENT_OF
    description: str = "NodeId of the UA Object the method is defined in (the objectId of the UA Call service)."


class OpcuaForm(DmpForm, forms_OPCUA):
    """The form of an OPC UA variable or event: ``href`` is ``/?id=<NodeId>``."""


class OpcuaActionForm(DmpActionForm, forms_OPCUA):
    """The form of an OPC UA Method."""


class DmpOpcuaEndpointMetadata(DmpEndpointMetadata, EndpointMetadata_OPCUA):
    """OPC UA endpoint metadata: its security definitions include the OPC UA channel and authentication
    schemes."""
    securityDefinitions: securityDefinitions_OPCUA = securityDefinitions_OPCUA()


class OpcuaAction(DmpAction):
    """An OPC UA Method: the form ``href`` is ``/?id=<Method NodeId>``, input
    and output are its arguments."""
    uav_componentOf: Optional[UavComponentOf] = None
    forms: OpcuaActionForm = OpcuaActionForm()

    @model_validator(mode="after")
    def validate_component_of(self):
        value = self.uav_componentOf.value if self.uav_componentOf is not None else None
        if not isinstance(value, str) or not value.strip():
            raise ValueError("OPC UA actions require a non-empty uav_componentOf NodeId")
        return self


class OpcuaActions(DmpActions):
    """Dynamic map of OPC UA actions (name → OpcuaAction)."""
    property_name: Dict[str, OpcuaAction] = {}


# ── Events ───────────────────────────────────────────────────────────────────

class UavEventType(Property):
    """The OPC UA EventType a subscription is filtered to (where clause:
    ``OfType``), e.g. ``i=2378`` (ProgramTransitionEventType) or
    ``nsu=urn:vendor;s=JobDoneEventType``. Events of subtypes pass too;
    without the term every event of the notifier is delivered."""
    id_short: AasIdString = "uav_eventType"
    semantic_id: str = AID_OPCUA_EVENT_TYPE
    description: str = "NodeId of the OPC UA EventType the subscription is filtered to (OfType); subtypes are included."


class UavEventField(Property):
    """Browse path of an event field relative to the event (select clause),
    as ``/``-separated qualified names, e.g. ``0:ToState/0:Id``; a name
    without ``<namespaceIndex>:`` is in namespace 0. Without the term the
    data-schema property's own name is the field's BrowseName in namespace
    0 — so ``Message``, ``Severity``, ``Time``, ``SourceName``, ``EventType``
    need no term."""
    id_short: AasIdString = "uav_eventField"
    semantic_id: str = AID_OPCUA_EVENT_FIELD
    description: str = "Browse path of the event field relative to the event, e.g. 0:ToState/0:Id (select clause)."


class OpcuaEventField(DmpDataSchema):
    """One property of an OPC UA event's ``data`` schema: one selected
    event field, optionally with its browse path."""
    uav_eventField: Optional[UavEventField] = None


class OpcuaEventFields(DmpSchemaProperties):
    """The properties of an OPC UA event's ``data`` schema (name → field)."""
    property_name: Dict[str, OpcuaEventField] = {}


class OpcuaEventData(DmpEventData):
    """``data`` of an OPC UA event: an object schema, one property per
    selected event field. A notification is delivered as that object."""
    properties: Optional[OpcuaEventFields] = None


class OpcuaEvent(DmpEvent):
    """An OPC UA event (OPC 10000-3 §5.4, 10000-4 §7.22.3): the form ``href``
    NodeId (or ``uav_browsePath``) names the event notifier (e.g. the
    ``Server`` object ``i=2253``); ``data`` selects the event fields and the
    optional ``uav_eventType`` filters by EventType. Consumed with an event
    monitored item."""
    uav_eventType: Optional[UavEventType] = None
    data: Optional[OpcuaEventData] = None


class OpcuaEvents(DmpEvents):
    """Dynamic map of OPC UA events (name → OpcuaEvent)."""
    property_name: Dict[str, OpcuaEvent] = {}


class OpcuaInteractionMetadata(DmpInteractionMetadata):
    actions: Optional[OpcuaActions] = None
    events: Optional[OpcuaEvents] = None


class DmpOpcuaInterface(_BaseOpcuaInterface):
    title: Title = Title()
    EndpointMetadata: DmpOpcuaEndpointMetadata = DmpOpcuaEndpointMetadata()
    InteractionMetadata: OpcuaInteractionMetadata = OpcuaInteractionMetadata()
