"""Compact builders for constructing shared pydantic AID/AIMC models.

Building the nested pydantic AAS models by hand is verbose. These helpers let
tests (and small tools) construct a valid AID/AIMC from a terse spec — e.g. an
MQTT interface with ``StationState -> /DATA/State``, an observable OPC UA node,
or an AIMC mapping — using the same ``aas_model`` classes the parsers consume
(ADR-016). Not required at runtime by the management node; test/tool support.
"""

from __future__ import annotations

from aas_pydantic import Key, ModelReference, Property

from aas_pydantic.submodel_templates.asset_interfaces_description import (
    Title, EndpointMetadata, security_t, securityDefinitions, Base, ContentType, Href, HtvMethodName,
    MqvControlPacket, MqvQos, MqvRetain, Subprotocol, Observable as AIDObservable, UavBrowsePath,
)

from aas_model.submodel_templates.aid import (
    DmpAssetInterfacesDescription, DmpAction, DmpActionForm, DmpActions, DmpEvent, DmpEventData, DmpEvents,
    DmpForm, DmpInteractionMetadata, DmpProperties, DmpProperty, DmpHttpInterface, DmpModbusInterface,
    DmpSnmpInterface, SnmpForm, SnmpInteractionMetadata, SnmpProperties, SnmpProperty, SnmpvPduType, SnmpvVersion,
    DmpBacnetInterface, DmpOpcuaInterface, MqttAction, MqttActionForm, MqttForm, OpcuaForm, OpcuaActionForm,
    HttpForm, HttpActionForm, ModbusForm, ModbusInteractionMetadata, BacnetForm, BacnetInteractionMetadata, MqttActions, MqttInteractionMetadata,
    MqttInterface, MqvResponseTopic, OpcuaAction, OpcuaActions, OpcuaEvent, OpcuaEventData, OpcuaEvents,
    OpcuaInteractionMetadata, Synchronous, UavComponentOf, UavEventType, Op,
)


def _endpoint(base: str, content_type: str = "application/json") -> EndpointMetadata:
    return EndpointMetadata(
        base=Base(value=base),
        contentType=ContentType(value=content_type),
        security=security_t(),
        securityDefinitions=securityDefinitions(),
    )


# --------------------------------------------------------------------------- #
# AID — only what differs from the WoT defaults is authored
# --------------------------------------------------------------------------- #
def mqtt_property(name: str, href: str, *, qos: int = 0, retain: bool = True,
                  control_packet: str | None = None, op: str | None = None) -> DmpProperty:
    """An observable MQTT property on ``href``."""
    form = MqttForm(href=Href(value=href), mqv_qos=MqvQos(value=str(qos)))
    if retain:
        form.mqv_retain = MqvRetain(value="true")
    if control_packet is not None:
        form.mqv_controlPacket = MqvControlPacket(value=control_packet)
    if op is not None:
        form.op = Op(value=[Property(value=op)])
    return DmpProperty(title=Title(value=name), observable=AIDObservable(value="true"), forms=form)


def mqtt_action(name: str, href: str, *, synchronous: bool = False,
                response: str | None = None) -> MqttAction:
    """An MQTT action requested on ``href``; ``response`` is the MQTT 5
    response topic of a request/reply action."""
    form = MqttActionForm(href=Href(value=href), mqv_qos=MqvQos(value="2"))
    if response is not None:
        form.mqv_responseTopic = MqvResponseTopic(value=response)
    return MqttAction(title=Title(value=name), synchronous=Synchronous(value=str(synchronous).lower()),
                      forms=form)


def mqtt_event(name: str, href: str, data_schema: dict | None = None, *,
               qos: int = 1) -> DmpEvent:
    """An MQTT event affordance published on ``href``; ``data_schema`` is the
    JSON Schema of each notification."""
    from aas_model.json_schema_aid import datapoint_from_schema
    return DmpEvent(
        title=Title(value=name),
        data=(datapoint_from_schema(data_schema, key="data", cls=DmpEventData)
              if data_schema is not None else None),
        forms=MqttForm(href=Href(value=href), mqv_qos=MqvQos(value=str(qos))),
    )


def mqtt_interface(base: str, *, properties=None, actions=None, events=None) -> MqttInterface:
    """``properties`` maps a name to an href or ``(href, op)``; ``actions`` to
    an href or ``(href, response_topic)``; ``events`` to an href or
    ``(href, data_schema)``."""
    props = {n: mqtt_property(n, *(v if isinstance(v, tuple) else (v,))[:1],
                              op=v[1] if isinstance(v, tuple) and len(v) > 1 else None)
             for n, v in (properties or {}).items()}
    acts = {n: mqtt_action(n, v[0] if isinstance(v, tuple) else v,
                           response=v[1] if isinstance(v, tuple) and len(v) > 1 else None)
            for n, v in (actions or {}).items()}
    meta = MqttInteractionMetadata(
        properties=DmpProperties(property_name=props),
        actions=MqttActions(property_name=acts),
        events=DmpEvents(property_name={
            n: mqtt_event(n, *(v if isinstance(v, tuple) else (v,))) for n, v in events.items()
        }) if events else None,
    )
    return MqttInterface(
        title=Title(value="mqtt"),
        EndpointMetadata=_endpoint(base),
        InteractionMetadata=meta,
    )


def _gen_interface(template_cls, base: str, *, properties=None, actions=None,
                   observable: bool = False, subprotocol: str | None = None,
                   op: str | None = None, meta_cls=DmpInteractionMetadata,
                   properties_cls=DmpProperties, property_cls=DmpProperty, form_cls=DmpForm,
                   action_form_cls=DmpActionForm, actions_cls=DmpActions, action_cls=DmpAction,
                   form_extras=None, action_extras=None):
    """Compose an interface. ``actions`` values are ``(href, method, …)``
    tuples or an href (POST); ``form_extras(n, spec)``/``action_extras(n,
    spec)`` add protocol terms to an action's form or to the action itself
    (e.g. OPC UA ``uav_browsePath``/``uav_componentOf``). The affordances
    are built before the interface, whose validator stamps the idShorts."""
    meta = meta_cls()
    if properties:
        props = {}
        for n, h in properties.items():
            form = form_cls(href=Href(value=h or ""), contentType=ContentType(value="application/json"))
            if subprotocol is not None:
                form.subprotocol = Subprotocol(value=subprotocol)
            if op is not None:
                form.op = Op(value=[Property(value=op)])
            props[n] = property_cls(title=Title(value=n), forms=form,
                                    observable=AIDObservable(value="true") if observable else None)
        meta.properties = properties_cls(property_name=props)
    if actions:
        acts = {}
        for n, spec in actions.items():
            href, method = (spec[0], spec[1]) if isinstance(spec, tuple) else (spec, "POST")
            form = action_form_cls(href=Href(value=href), contentType=ContentType(value="application/json"))
            # htv_methodName is an HTTP term: other protocols' forms carry none.
            if method and template_cls is DmpHttpInterface:
                form.htv_methodName = HtvMethodName(value=method)
            for fname, val in ((form_extras(n, spec) or {}) if form_extras else {}).items():
                setattr(form, fname, val)
            acts[n] = action_cls(title=Title(value=n), forms=form,
                                 **((action_extras(n, spec) or {}) if action_extras else {}))
        meta.actions = actions_cls(property_name=acts)
    return template_cls(
        title=Title(value="iface"),
        EndpointMetadata=_endpoint(base),
        InteractionMetadata=meta,
    )


def _opcua_action_extras(n, spec):
    """OPC 10101 §7.1.3: the owning Object NodeId (mandatory) is an
    affordance-level term of the action."""
    return {"uav_componentOf": UavComponentOf(value=spec[2])} if len(spec) >= 3 and spec[2] else {}


def _opcua_form_extras(n, spec):
    """The optional absolute browse path of the Method."""
    return {"uav_browsePath": UavBrowsePath(value=spec[3])} if len(spec) >= 4 and spec[3] else {}


def opcua_event(name: str, notifier: str, fields: dict, *,
                event_type: str | None = None) -> OpcuaEvent:
    """An OPC UA event affordance on the event notifier ``notifier`` (a
    NodeId, e.g. ``i=2253`` for the Server object). ``fields`` maps each
    notification field to its JSON Schema, or to ``(schema, browse_path)``
    when the field is not the namespace-0 BrowseName of the same name
    (e.g. ``0:ToState/0:Id``); ``event_type`` is the EventType NodeId the
    subscription is filtered to."""
    from aas_model.json_schema_aid import datapoint_from_schema
    schemas = {n: ({**v[0], "uav_eventField": v[1]} if isinstance(v, tuple) else v) for n, v in fields.items()}
    data = datapoint_from_schema({"type": "object", "properties": schemas}, key="data", cls=OpcuaEventData)
    return OpcuaEvent(
        title=Title(value=name),
        uav_eventType=UavEventType(value=event_type) if event_type else None,
        data=data,
        forms=OpcuaForm(href=Href(value=f"/?id={notifier}"),
                        contentType=ContentType(value="application/octet-stream")),
    )


def opcua_interface(base: str, *, properties=None, actions=None, events=None,
                    observable: bool = False, subprotocol: str | None = None,
                    op: str | None = None) -> DmpOpcuaInterface:
    """OPC UA interface. ``actions`` values are ``(href, method)`` or
    ``(href, method, componentOf[, browsePath])`` tuples — OPC UA actions
    carry the mandatory ``uav_componentOf`` owning-Object NodeId
    (OPC 10101 §7.1.3). ``events`` values are ``(notifier, fields[,
    event_type])`` tuples (see :func:`opcua_event`)."""
    interface = _gen_interface(
        DmpOpcuaInterface, base, properties=properties, actions=actions,
        observable=observable, subprotocol=subprotocol, op=op,
        meta_cls=OpcuaInteractionMetadata, actions_cls=OpcuaActions,
        action_cls=OpcuaAction, form_cls=OpcuaForm, action_form_cls=OpcuaActionForm,
        form_extras=_opcua_form_extras, action_extras=_opcua_action_extras)
    if events:
        # Assigned after validation, so the container is named here.
        interface.InteractionMetadata.events = OpcuaEvents(id_short="events", property_name={
            n: opcua_event(n, v[0], v[1], event_type=v[2] if len(v) > 2 else None)
            for n, v in events.items()})
    return interface


def http_interface(base: str, *, properties=None, actions=None) -> DmpHttpInterface:
    return _gen_interface(DmpHttpInterface, base, properties=properties, actions=actions,
                          form_cls=HttpForm, action_form_cls=HttpActionForm)


def modbus_interface(base: str, *, properties=None) -> DmpModbusInterface:
    return _gen_interface(DmpModbusInterface, base, properties=properties, form_cls=ModbusForm,
                          meta_cls=ModbusInteractionMetadata)


def bacnet_interface(base: str, *, properties=None) -> DmpBacnetInterface:
    return _gen_interface(DmpBacnetInterface, base, properties=properties, form_cls=BacnetForm,
                          meta_cls=BacnetInteractionMetadata)


def snmp_interface(base: str, *, properties=None, observable: bool = False) -> DmpSnmpInterface:
    """SNMP v1/v2c interface (AID 1.2 Annex E.1), base ``snmp://{address}:{port}``.
    ``properties`` maps a name to its OID href, or to ``(href, terms)`` where
    ``terms`` sets ``pduType`` and/or ``version`` (e.g. ``"snmpv:SNMPv1"``)."""
    interface = _gen_interface(DmpSnmpInterface, base, observable=observable, properties={
        n: (v[0] if isinstance(v, tuple) else v) for n, v in (properties or {}).items()},
        meta_cls=SnmpInteractionMetadata, properties_cls=SnmpProperties, property_cls=SnmpProperty,
        form_cls=SnmpForm)
    for n, v in (properties or {}).items():
        terms = v[1] if isinstance(v, tuple) else {}
        form = interface.InteractionMetadata.properties.property_name[n].forms
        form.contentType = None
        if "pduType" in terms:
            form.snmpv_pduType = SnmpvPduType(value=terms["pduType"])
        if "version" in terms:
            form.snmpv_version = SnmpvVersion(value=terms["version"])
    return interface


def build_aid(*, mqtt: MqttInterface | None = None,
              opcua: DmpOpcuaInterface | None = None,
              http: DmpHttpInterface | None = None,
              modbus: DmpModbusInterface | None = None,
              bacnet: DmpBacnetInterface | None = None,
              snmp: DmpSnmpInterface | None = None,
              id_short: str = "AID") -> DmpAssetInterfacesDescription:
    """Compose an AID. All interfaces live in their ``InterfaceTemplateFor*``
    dicts under ``interface_<protocol>``."""
    aid = DmpAssetInterfacesDescription(id_short=id_short)
    if mqtt is not None:
        aid.InterfaceTemplateForMQTT["interface_mqtt"] = mqtt
    if opcua is not None:
        aid.InterfaceTemplateForOPCUA["interface_opcua"] = opcua
    if http is not None:
        aid.InterfaceTemplateForHTTP["interface_http"] = http
    if modbus is not None:
        aid.InterfaceTemplateForMODBUS["interface_modbus"] = modbus
    if bacnet is not None:
        aid.InterfaceTemplateForBacnet["interface_bacnet"] = bacnet
    if snmp is not None:
        aid.InterfaceTemplateForSNMP["interface_snmp"] = snmp
    return aid


# --------------------------------------------------------------------------- #
# AIMC
# --------------------------------------------------------------------------- #
def aimc_ref(*values: str) -> ModelReference:
    return ModelReference(
        key=tuple(
            Key(type_="Submodel" if i == 0 else "SubmodelElementCollection", value=v)
            for i, v in enumerate(values)
        )
    )
