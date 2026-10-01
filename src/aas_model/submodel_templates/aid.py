"""
DMP-extended AssetInterfacesDescription — extensions over the generated IDTA AID.

Named-field style: containers hold their child elements as DIRECT named
fields (field name == id_short) — no ``value``/``submodel_element`` wrapper.

Layering (DMP v3): the generated IDTA template
(``aas_pydantic.submodel_templates.asset_interfaces_description``) stays
PRISTINE — every DMP extension lives HERE, in ONE hierarchy:

- **Generic (protocol-neutral) WoT extension** — the generated ``actions``
  container cannot author action affordances and the generated ``forms``
  cannot declare the invocation/response pattern. For EVERY protocol
  interface (HTTP, Modbus, OPC UA, BACnet, IO-Link over Profinet REST):

      class DmpForm(forms):
          op: Property = Property(...)             # td#hasOperationType
          response: Optional[DmpResponseForm]      # td/hypermedia#response
      class DmpAction(SubmodelElementCollection):  # td#ActionAffordance
          title / safe / idempotent / synchronous / input / output / forms
      class DmpActions(actions):
          property_name: Dict[str, DmpAction]
      class Dmp<Protocol>Interface(InterfaceTemplateFor<Protocol>):
          InteractionMetadata: DmpGenericInteractionMetadata

  WoT TD 1.1 conformance (reviewed against §5.3.1.4 / §5.3.4.2, 2026-09-18):
  ``DmpAction`` carries every ActionAffordance term — ``input``/``output``
  (DataSchemas), ``safe``/``idempotent`` (with-default booleans; absent
  = false), ``synchronous`` (optional; moved up from the old MQTT-only
  flag), ``title``; ``forms`` rides the generated single-form IDTA
  abstraction. ``DmpResponseForm`` follows the WoT ``ExpectedResponse``
  shape EXACTLY (``contentType`` only — no href; the reply rides the same
  protocol). Deliberate WoT omissions (no DMP consumer, and the IDTA
  template does not model them either): ``uriVariables``,
  ``additionalResponses``, ``contentCoding``, ``scopes``, per-affordance
  ``description`` children. Form ``op`` values are the lowercase WoT
  operation types (``invokeaction``, …). MQTT keeps only TRANSPORT
  vocabulary: the reply topic lives on the typed ``MqttResponseForm``
  (IDTA MQTT binding vocabulary) because a pub/sub reply needs a
  destination — a synchronous protocol answers on the form itself.

  The reply pattern is protocol-inherent where the protocol answers
  synchronously (HTTP response = the reply; OPC UA / Modbus / BACnet writes
  ack) — a declared ``forms.response`` is only meaningful for pub/sub-style
  transports.

- **MQTT extension** — a thin TRANSPORT-VOCABULARY subclass of the generic
  layer; nothing structural is MQTT-specific:

      class MqttForm(DmpForm):
          mqv_retain / mqv_qos / mqv_control_packet   # WoT MQTT binding terms
          response: MqttResponseForm                  # REQUIRED correlated reply
      class MqttAction(DmpAction):   # ActionAffordance terms inherited
      class MqttActions(DmpActions) / MqttProperties(properties) /
      MqttInteractionMetadata(DmpGenericInteractionMetadata)

- **OPC UA extension** — the same methodology (IDTA: the affordance stays
  protocol-agnostic, the protocol-specific terms live on the protocol-
  specific form):

      class OpcuaForm(DmpForm):
          uav_componentOf        # OPC-10101 §7.1.3, mandatory on actions
          uav_browsePath         # §6.5.3; href carries the §6.2 NodeId
      class OpcuaAction(DmpAction) / OpcuaProperty(property) /
      OpcuaActions(DmpActions) / OpcuaProperties(properties) /
      OpcuaInteractionMetadata(DmpGenericInteractionMetadata)

  UA Methods are INVOKABLE by the DMP: camel-milo's UA ``Call`` service
  (node = the owning Object from ``uav_componentOf``, method = the §6.2
  NodeId in ``href``) answers inline with its OutputArguments.

The former REST operation-delegation interface (``interface_rest``) is
RETIRED (ADR-022): the AID models only the device's own communication — the
caller-facing REST surface is derived by the DMP.

The top-level :class:`DmpAssetInterfacesDescription` overrides the generated
``InterfaceTemplateFor*`` dict fields with the DMP-extended interface
classes, so a hand-authored or generated AID parses with full action
affordances on every protocol.
"""

from __future__ import annotations

from typing import Dict, Optional

from aas_pydantic import (
    SubmodelElementCollection, Property,
)

from aas_pydantic.submodel_templates.asset_interfaces_description import (
    forms as _BaseForm,
    property_name as _BaseProperty,
    property_name_json_schema as _BaseDataSchema,
    actions as _BaseActions,
    properties as _BaseProperties,
    InteractionMetadata as _BaseInteractionMetadata,
    InterfaceTemplateForMQTT as _BaseMqttInterface,
    InterfaceTemplateForHTTP as _BaseHttpInterface,
    InterfaceTemplateForMODBUS as _BaseModbusInterface,
    InterfaceTemplateForOPCUA as _BaseOpcuaInterface,
    InterfaceTemplateForBacnet as _BaseBacnetInterface,
    InterfaceTemplateForIOLINK_OVER_PROFINET_REST as _BaseIolinkInterface,
    UavBrowsePath,
    EndpointMetadata as _BaseEndpointMetadata,
    securityDefinitions as _BaseSecurityDefinitions,
    opcua_channel_sc as OpcuaChannelSc,
    opcua_authentication_sc as OpcuaAuthenticationSc,
    ModvMostSignificantByte, ModvMostSignificantWord, ModvPollingTime,
    ModvTimeout, ModvType, ModvFunction, ModvEntity, ModvZeroBasedAddressing,
    BacvUseService, BacvIsISO8601, BacvHasBinaryRepresentation,
    BacvHasFieldName, BacvHasContextTag,
    IolvMethod, IolvAccessRigths, IolvType, IolvByteOffset, IolvByteLength,
    IolvBitOffset, IolvBitLength,
    AssetInterfacesDescription as _BaseAID,
    # Required (One) children of the generated classes — provided here so the
    # variants construct: forms need href/security; the interface needs
    # title + endpoint metadata.
    Title, Base, ContentType, EndpointMetadata, Href,
    security_t, securityDefinitions,
    EndpointMetadata_t,
)

from aas_model.constants import (
    AID_MQTT_RESPONSE_FORM, AID_MQTT_RETAIN, AID_MQTT_CONTROL_PACKET,
    AID_MQTT_QOS, AID_MQTT_REQUEST_REPLY, AID_MQTT_RESPONSE_TOPIC,
    AID_SYNCHRONOUS, AID_WOT_SAFE, AID_WOT_IDEMPOTENT,
    AID_ACTION_INPUT, AID_ACTION_OUTPUT,
    AID_WOT_OPERATION_TYPE, AID_WOT_RESPONSE_FORM,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Generic (protocol-neutral) WoT extension — action affordances + form
# invocation/response pattern for EVERY protocol interface.
# ═══════════════════════════════════════════════════════════════════════════════

class DmpResponseForm(SubmodelElementCollection):
    """Correlated-reply form of an action — the WoT ``ExpectedResponse``
    shape EXACTLY (TD 1.1 §5.3.4.3): the reply rides the SAME protocol and
    form, so only the expected content type is declared. A pub/sub transport
    that needs a reply DESTINATION subclasses this (see
    ``MqttResponseForm``); synchronous protocols (HTTP request/response;
    OPC UA / Modbus / BACnet writes) carry no response form at all."""
    semantic_id: str = AID_WOT_RESPONSE_FORM

    contentType: Property = Property(
        semantic_id="https://www.w3.org/2019/wot/hypermedia#forContentType")


class DmpForm(_BaseForm):
    """Generated WoT form + the DMP invocation/response pattern: ``op``
    declares the WoT operation type (lowercase per TD 1.1 Table 27 —
    ``invokeaction`` for actions) and the optional ``response`` form carries
    the expected reply content type (WoT ExpectedResponse)."""
    href: Href = Href()
    security: security_t = security_t()
    op: Property = Property(
        semantic_id=AID_WOT_OPERATION_TYPE)
    response: Optional[DmpResponseForm] = None


class DmpActionInput(_BaseDataSchema):
    """WoT ``input`` DataSchema of an action (td#hasInput) — the invocation's
    JSON Schema structure, built via
    :func:`aas_model.json_schema_aid.datapoint_from_schema`."""
    semantic_id: str = AID_ACTION_INPUT
    description: str = "Data schema describing the input of the action."


class DmpActionOutput(_BaseDataSchema):
    """WoT ``output`` DataSchema of an action (td#hasOutput) — the response's
    JSON Schema structure."""
    semantic_id: str = AID_ACTION_OUTPUT
    description: str = "Data schema describing the output of the action."


class DmpAction(SubmodelElementCollection):
    """WoT ActionAffordance, protocol-neutral (TD 1.1 §5.3.1.4): an
    invokable function of the asset. ``forms.htv_methodName`` carries the
    invocation method and ``forms.op`` the WoT operation type (lowercase,
    ``invokeaction``); ``input``/``output`` are DataSchemas;
    ``safe``/``idempotent`` are the with-default WoT booleans (absent =
    false); ``synchronous`` documents whether the action completes within
    the form interaction (WoT: optional boolean)."""
    semantic_id: str = "https://www.w3.org/2019/wot/td#ActionAffordance"
    description: str = "WoT ActionAffordance: an invokable function of the asset. The form declares the invocation endpoint, method and operation type; input/output describe the request/response payload schemas; the optional response form carries the expected reply content type (WoT ExpectedResponse)."
    title: Optional[Title] = None
    safe: Optional[Property] = None
    idempotent: Optional[Property] = None
    synchronous: Optional[Property] = None
    input: Optional[DmpActionInput] = None
    output: Optional[DmpActionOutput] = None
    forms: DmpForm = DmpForm()


class DmpActions(_BaseActions):
    """Dynamic map of generic actions (name → DmpAction)."""
    property_name: Dict[str, DmpAction] = {}


class DmpGenericInteractionMetadata(_BaseInteractionMetadata):
    """Interaction metadata with the DMP action extension for generic
    (non-MQTT) protocol interfaces."""
    actions: DmpActions = DmpActions()
    properties: _BaseProperties = _BaseProperties()


class DmpHttpInterface(_BaseHttpInterface):
    """HTTP interface with the DMP action extension."""
    InteractionMetadata: DmpGenericInteractionMetadata = DmpGenericInteractionMetadata()


class UavComponentOf(Property):
    """``uav:componentOf`` (OPC-10101 §7.1.3) — the NodeId of the UA Object
    that owns a UA Method. MANDATORY on OPC UA action forms: the UA ``Call``
    service addresses the method as (objectId, methodId)."""
    semantic_id: str = "http://opcfoundation.org/UA/WoT-Binding/componentOf"
    description: str = "NodeId of the UA Object the method is defined in (the invocation objectId of the UA Call service)."


class OpcuaForm(DmpForm):
    """OPC UA form vocabulary shared by BOTH affordance kinds (OPC-10101):
    the optional ``uav_browsePath`` (§6.5.3 — a root-relative browse-name
    path to the addressed node) and the §6.2 ``href`` NodeId convention
    (``/?id=<nodeId>``, percent-encoded). The UA ``Call`` service's owning
    Object lives on the ACTION form (``OpcuaActionForm.uav_componentOf``) —
    a variable has no owning-object call semantics."""
    uav_browsePath: Optional[UavBrowsePath] = None


class OpcuaActionForm(OpcuaForm):
    """OPC UA form of an ACTION affordance: ``uav_componentOf`` (§7.1.3) is
    MANDATORY — the UA ``Call`` service addresses the method as
    (objectId = owning Object, methodId = the href NodeId)."""
    uav_componentOf: UavComponentOf = UavComponentOf()


class OpcuaAction(DmpAction):
    """Generic action affordance + the OPC UA action form."""
    forms: OpcuaActionForm = OpcuaActionForm()


class OpcuaProperty(_BaseProperty):
    """Standard WoT PropertyDefinition + the shared OPC UA form (the
    variable is addressed by browsePath or the href NodeId)."""
    forms: OpcuaForm = OpcuaForm()


class OpcuaActions(DmpActions):
    """Dynamic map of OPC UA actions (name → OpcuaAction)."""
    property_name: Dict[str, OpcuaAction] = {}


class OpcuaProperties(_BaseProperties):
    """Dynamic map of OPC UA properties (name → OpcuaProperty)."""
    property_name: Dict[str, OpcuaProperty] = {}


class OpcuaInteractionMetadata(DmpGenericInteractionMetadata):
    """Interaction metadata with OPC-UA-specialised actions/properties."""
    actions: OpcuaActions = OpcuaActions()
    properties: OpcuaProperties = OpcuaProperties()


class OpcuaSecurityDefinitions(_BaseSecurityDefinitions):
    """OPC UA security schemes (OPC-10101 §6.3.3): the UA channel and
    authentication schemes alongside the generic WoT schemes."""
    # field name == idShort; the annotation uses the clash-alias name (the
    # field-name default would shadow the imported class otherwise — the same
    # ``*_t`` alias pattern the generated template uses)
    opcua_channel_sc: Optional[OpcuaChannelSc] = None
    opcua_authentication_sc: Optional[OpcuaAuthenticationSc] = None


class OpcuaEndpointMetadata(_BaseEndpointMetadata):
    """OPC UA endpoint metadata: the §6.2 ``opc.tcp://`` base + the OPC UA
    security schemes."""
    securityDefinitions: OpcuaSecurityDefinitions = OpcuaSecurityDefinitions()


class ModbusEndpointMetadata(_BaseEndpointMetadata):
    """Modbus connection-level terms (WoT Modbus binding): byte/word order,
    polling rate, response timeout, register type."""
    modv_mostSignificantByte: Optional[ModvMostSignificantByte] = None
    modv_mostSignificantWord: Optional[ModvMostSignificantWord] = None
    modv_pollingTime: Optional[ModvPollingTime] = None
    modv_timeout: Optional[ModvTimeout] = None
    modv_type: Optional[ModvType] = None


class ModbusForm(DmpForm):
    """Modbus request terms (WoT Modbus binding): function code or registry
    entity + zero-based addressing on the addressed datapoint."""
    modv_function: Optional[ModvFunction] = None
    modv_entity: Optional[ModvEntity] = None
    modv_zeroBasedAddressing: Optional[ModvZeroBasedAddressing] = None


class ModbusAction(DmpAction):
    forms: ModbusForm = ModbusForm()


class ModbusProperty(_BaseProperty):
    forms: ModbusForm = ModbusForm()


class ModbusActions(DmpActions):
    property_name: Dict[str, ModbusAction] = {}


class ModbusProperties(_BaseProperties):
    property_name: Dict[str, ModbusProperty] = {}


class ModbusInteractionMetadata(DmpGenericInteractionMetadata):
    actions: ModbusActions = ModbusActions()
    properties: ModbusProperties = ModbusProperties()


class BacnetForm(DmpForm):
    """BACnet payload-encoding terms (WoT BACnet binding) on the addressed
    datapoint's form."""
    bacv_useService: Optional[BacvUseService] = None
    bacv_isISO8601: Optional[BacvIsISO8601] = None
    bacv_hasBinaryRepresentation: Optional[BacvHasBinaryRepresentation] = None
    bacv_hasFieldName: Optional[BacvHasFieldName] = None
    bacv_hasContextTag: Optional[BacvHasContextTag] = None


class BacnetAction(DmpAction):
    forms: BacnetForm = BacnetForm()


class BacnetProperty(_BaseProperty):
    forms: BacnetForm = BacnetForm()


class BacnetActions(DmpActions):
    property_name: Dict[str, BacnetAction] = {}


class BacnetProperties(_BaseProperties):
    property_name: Dict[str, BacnetProperty] = {}


class BacnetInteractionMetadata(DmpGenericInteractionMetadata):
    actions: BacnetActions = BacnetActions()
    properties: BacnetProperties = BacnetProperties()


class IolinkForm(DmpForm):
    """IO-Link request/response terms (WoT IO-Link binding) on the addressed
    datapoint's form."""
    iolv_method: Optional[IolvMethod] = None
    iolv_accessRights: Optional[IolvAccessRigths] = None
    iolv_type: Optional[IolvType] = None
    iolv_byteOffset: Optional[IolvByteOffset] = None
    iolv_byteLength: Optional[IolvByteLength] = None
    iolv_bitOffset: Optional[IolvBitOffset] = None
    iolv_bitLength: Optional[IolvBitLength] = None


class IolinkAction(DmpAction):
    forms: IolinkForm = IolinkForm()


class IolinkProperty(_BaseProperty):
    forms: IolinkForm = IolinkForm()


class IolinkActions(DmpActions):
    property_name: Dict[str, IolinkAction] = {}


class IolinkProperties(_BaseProperties):
    property_name: Dict[str, IolinkProperty] = {}


class IolinkInteractionMetadata(DmpGenericInteractionMetadata):
    actions: IolinkActions = IolinkActions()
    properties: IolinkProperties = IolinkProperties()


class DmpOpcuaInterface(_BaseOpcuaInterface):
    """OPC UA interface with the DMP action extension AND the OPC UA WoT
    binding vocabulary (OPC-10101) on its forms and endpoint metadata."""
    title: Title = Title()
    EndpointMetadata: OpcuaEndpointMetadata = OpcuaEndpointMetadata(
        base=Base(),
        contentType=ContentType(),
        security=security_t(),
        securityDefinitions=OpcuaSecurityDefinitions(),
    )
    InteractionMetadata: OpcuaInteractionMetadata = OpcuaInteractionMetadata()


class DmpModbusInterface(_BaseModbusInterface):
    """Modbus interface with the DMP action extension AND the Modbus binding
    vocabulary on its forms and endpoint metadata."""
    title: Title = Title()
    EndpointMetadata: ModbusEndpointMetadata = ModbusEndpointMetadata(
        base=Base(),
        contentType=ContentType(),
        security=security_t(),
        securityDefinitions=securityDefinitions(),
    )
    InteractionMetadata: ModbusInteractionMetadata = ModbusInteractionMetadata()


class DmpBacnetInterface(_BaseBacnetInterface):
    """BACnet interface with the DMP action extension AND the BACnet binding
    vocabulary on its forms."""
    InteractionMetadata: BacnetInteractionMetadata = BacnetInteractionMetadata()


class DmpIolinkInterface(_BaseIolinkInterface):
    """IO-Link (over Profinet REST) interface with the DMP action extension
    AND the IO-Link binding vocabulary on its forms."""
    InteractionMetadata: IolinkInteractionMetadata = IolinkInteractionMetadata()


# ═══════════════════════════════════════════════════════════════════════════════
# MQTT extension — transport vocabulary ONLY (the WoT MQTT binding terms);
# the structure is inherited from the generic layer above.
# ═══════════════════════════════════════════════════════════════════════════════

class MqttResponseForm(DmpResponseForm):
    """MQTT reply form: the WoT ExpectedResponse contentType + the reply
    DESTINATION (``href`` — a pub/sub transport needs an addressable reply
    topic; IDTA MQTT vocabulary qualifiers)."""
    semantic_id: str = AID_MQTT_RESPONSE_FORM

    href: Property = Property(
        semantic_id="https://www.w3.org/2019/wot/hypermedia#hasTarget")
    mqv_retain: Property = Property(
        semantic_id=AID_MQTT_RETAIN)
    mqv_control_packet: Property = Property(
        semantic_id=AID_MQTT_CONTROL_PACKET)


class MqttForm(DmpForm):
    """Generic DMP form + the WoT MQTT binding qualifiers. The correlated
    reply form is OPTIONAL here — property affordances (observe/subscribe)
    carry no reply; ACTION affordances use ``MqttActionForm``, which makes
    it required.

    MQTT 5 request/reply correlation (WoT MQTT binding): ``mqv_request_reply``
    marks the interaction as a correlated request/reply exchange and
    ``mqv_response_topic`` names the MQTT 5 Response Topic — the requester
    publishes the command with the response-topic property (and its own
    Correlation Data); the responder delivers the reply on that topic,
    echoing the correlation. Authored on the ACTION form; both terms are
    optional (absence = the legacy uncorrelated pub/sub convention).
    """
    mqv_retain: Property = Property(
        semantic_id=AID_MQTT_RETAIN)
    mqv_qos: Property = Property(
        semantic_id=AID_MQTT_QOS)
    mqv_control_packet: Property = Property(
        semantic_id=AID_MQTT_CONTROL_PACKET)
    mqv_request_reply: Optional[Property] = None
    mqv_response_topic: Optional[Property] = None
    response: Optional[MqttResponseForm] = None


class MqttActionForm(MqttForm):
    """MQTT form of an ACTION affordance: the correlated reply topic is
    REQUIRED — every delegated MQTT action declares the reply leg of the
    derived interaction (ADR-022)."""
    response: MqttResponseForm = MqttResponseForm()
    mqv_request_reply: Property = Property(
        semantic_id=AID_MQTT_REQUEST_REPLY)
    mqv_response_topic: Property = Property(
        semantic_id=AID_MQTT_RESPONSE_TOPIC)


class MqttAction(DmpAction):
    """Generic action affordance + MQTT transport vocabulary (the WoT MQTT
    binding terms on the form). The ActionAffordance terms — including
    ``synchronous`` — are inherited from the generic layer."""
    forms: MqttActionForm = MqttActionForm()


class MqttActions(DmpActions):
    """Dynamic map of MQTT actions (name → MqttAction)."""
    property_name: Dict[str, MqttAction] = {}


class MqttProperty(_BaseProperty):
    """Standard WoT PropertyDefinition + MQTT form.  The payload schema URL
    rides as a supplemental semantic id on the property itself."""
    forms: MqttForm = MqttForm()


class MqttProperties(_BaseProperties):
    """Dynamic map of MQTT properties (name → MqttProperty)."""
    property_name: Dict[str, MqttProperty] = {}


class MqttInteractionMetadata(DmpGenericInteractionMetadata):
    """Interaction metadata with MQTT-specialised actions/properties."""
    actions: MqttActions = MqttActions()
    properties: MqttProperties = MqttProperties()


class MqttInterface(_BaseMqttInterface):
    """MQTT interface with extended interaction metadata."""
    title: Title = Title()
    EndpointMetadata: EndpointMetadata_t = EndpointMetadata(
        base=Base(),
        contentType=ContentType(),
        security=security_t(),
        securityDefinitions=securityDefinitions(),
    )
    InteractionMetadata: MqttInteractionMetadata = MqttInteractionMetadata()


# ═══════════════════════════════════════════════════════════════════════════════
# Top-level AID submodel
# ═══════════════════════════════════════════════════════════════════════════════

class DmpAssetInterfacesDescription(_BaseAID):
    """DMP-extended Asset Interfaces Description — DICT-ONLY interface
    modeling, exactly the IDTA-generic shape.

    Every interface lives in its protocol family's ``InterfaceTemplateFor*``
    dict, keyed by its idShort (the DMP convention: the asset's one native
    MQTT interface is ``InterfaceTemplateForMQTT["interface_mqtt"]``). The
    typed singular of the pre-generic era is gone.

    Parse routing of interface children is deterministic WITHOUT a typed
    sibling: the six interface families share the ``…/Interface`` semanticId,
    but each carries a UNIQUE protocol-binding supplemental IRI (MQTT
    ``…/2011/mqtt``, OPC UA ``opcfoundation.org/UA/WoT-Binding/``, HTTP,
    Modbus, …), and the converter disambiguates children by those
    supplementals. The serialized JSON is unchanged by this consolidation —
    a dict entry serializes as a child with ``idShort`` = its dict key.

    There is no caller-facing REST side (ADR-022) — the DMP derives it.
    """
    InterfaceTemplateForHTTP: Dict[str, DmpHttpInterface] = {}
    InterfaceTemplateForMODBUS: Dict[str, DmpModbusInterface] = {}
    InterfaceTemplateForMQTT: Dict[str, MqttInterface] = {
        "interface_mqtt": MqttInterface(),
    }
    InterfaceTemplateForOPCUA: Dict[str, DmpOpcuaInterface] = {}
    InterfaceTemplateForBacnet: Dict[str, DmpBacnetInterface] = {}
    InterfaceTemplateForIOLINK_OVER_PROFINET_REST: Dict[str, DmpIolinkInterface] = {}
