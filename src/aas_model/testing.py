"""Compact builders for constructing shared pydantic AID/AIMC models.

Building the nested pydantic AAS models by hand is verbose. These helpers let
tests (and small tools) construct a valid AID/AIMC from a terse spec — e.g. an
MQTT interface with ``StationState -> /DATA/State``, an observable OPC UA node,
or an AIMC mapping — using the same ``aas_model`` classes the parsers consume
(ADR-016). Not required at runtime by the management node; test/tool support.
"""

from __future__ import annotations

from aas_pydantic import Key, ModelReference, Property, Qualifier

from aas_pydantic.submodel_templates.asset_interfaces_description import (
    Title, EndpointMetadata, security_t, securityDefinitions,
    Base, ContentType, Href, Subprotocol, Type as AIDType, Observable as AIDObservable,
    forms as _BaseForm, property_name as _BaseProperty,
    properties as _BaseProperties,
    InteractionMetadata as _BaseInteractionMetadata,
)

from aas_model.submodel_templates.aid import (
    DmpAssetInterfacesDescription, MqttInterface, MqttInteractionMetadata,
    MqttProperties, MqttProperty, MqttForm, MqttActions, MqttAction,
    MqttResponseForm,
    DmpForm, DmpGenericInteractionMetadata, DmpHttpInterface,
    DmpModbusInterface, DmpBacnetInterface, DmpOpcuaInterface, OpcuaForm,
    MqttActionForm,
)
from aas_model.submodel_templates import (
    Aimc, AimcMappingConfiguration, AimcMappingConfigurations, Transformation,
    DmpResponseTransformation,
)
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import (
    Source, Sources, Sink, Sinks, SourceId, SinkId, Source_source, Sink_sink,
    DefaultPollingInterval,
)


def _prop(value: str) -> Property:
    return Property(value=value)


def _endpoint(base: str, content_type: str = "application/json") -> EndpointMetadata:
    return EndpointMetadata(
        base=Base(value=base),
        contentType=ContentType(value=content_type),
        security=security_t(),
        securityDefinitions=securityDefinitions(),
    )


# --------------------------------------------------------------------------- #
# AID
# --------------------------------------------------------------------------- #
def mqtt_property(name: str, href: str, *, qos: int = 0,
                  control_packet: str = "publish", retain: bool = True,
                  op: str | None = None, response: str | None = None) -> MqttProperty:
    form_kwargs = dict(
        href=Href(value=href),
        mqv_retain=_prop(str(retain).lower()),
        mqv_qos=_prop(str(qos)),
        mqv_control_packet=_prop(control_packet),
    )
    if op is not None:
        form_kwargs["op"] = _prop(op)
    if response is not None:
        form_kwargs["response"] = MqttResponseForm(
            href=Href(value=response), contentType=ContentType(value="application/json"),
            mqv_retain=_prop("false"), mqv_control_packet=_prop("publish"),
        )
        form_kwargs["mqv_request_reply"] = _prop("true")
        form_kwargs["mqv_response_topic"] = _prop(response)
    return MqttProperty(forms=MqttForm(**form_kwargs))


def mqtt_action(name: str, href: str, *, synchronous: bool = False,
                response: str | None = None) -> MqttAction:
    form_kwargs = dict(
        href=Href(value=href),
        op=_prop("invokeaction"),
        mqv_retain=_prop("false"),
        mqv_qos=_prop("2"),
        mqv_control_packet=_prop("subscribe"),
    )
    if response is not None:
        form_kwargs["response"] = MqttResponseForm(
            href=Href(value=response), contentType=ContentType(value="application/json"),
            mqv_retain=_prop("false"), mqv_control_packet=_prop("publish"),
        )
        form_kwargs["mqv_request_reply"] = _prop("true")
        form_kwargs["mqv_response_topic"] = _prop(response)
    return MqttAction(
        synchronous=_prop(str(synchronous).lower()),
        forms=MqttActionForm(**form_kwargs),
    )


def mqtt_interface(base: str, *, properties=None, actions=None, events=None) -> MqttInterface:
    meta = MqttInteractionMetadata()
    props = {}
    for n, v in (properties or {}).items():
        if isinstance(v, tuple):
            # (href, response[, op]) — a writable property declaring its
            # correlated ack topic (W2 write delegation)
            props[n] = mqtt_property(n, v[0], response=v[1] if len(v) > 1 else None,
                                     op=v[2] if len(v) > 2 else None)
        else:
            props[n] = mqtt_property(n, v)
    meta.properties = MqttProperties(property_name=props)
    acts = {}
    for n, v in (actions or {}).items():
        if isinstance(v, tuple):
            acts[n] = mqtt_action(n, v[0], response=v[1] if len(v) > 1 else None)
        else:
            acts[n] = mqtt_action(n, v)
    meta.actions = MqttActions(property_name=acts)
    return MqttInterface(
        title=Title(value="mqtt"),
        EndpointMetadata=_endpoint(base),
        InteractionMetadata=meta,
    )


def _gen_property(name: str, href: str | None = None, *, observable: bool = False,
                  subprotocol: str | None = None, op: str | None = None) -> _BaseProperty:
    form_kwargs = {"href": Href(value=href or ""), "security": security_t()}
    if op:
        form_kwargs["op"] = __import__("aas_pydantic", fromlist=["Property"]).Property(value=op)
    form = _BaseForm(**form_kwargs)
    if subprotocol is not None:
        form.subprotocol = Subprotocol(value=subprotocol)
    data = {"forms": form}
    if observable:
        data["observable"] = AIDObservable(value="true")
    return _BaseProperty(**data)


def _gen_interface(template_cls, base: str, *, properties=None, events=None,
                   actions=None, observable=(False, None), op: str | None = None,
                   meta_cls=None, actions_cls=None, action_cls=None, form_cls=None,
                   action_form_cls=None, properties_cls=None, property_cls=None,
                   form_extras=None):
    """Compose an interface from its protocol classes.

    ``meta_cls``/``actions_cls``/``action_cls``/``form_cls``/
    ``properties_cls``/``property_cls`` default to the generic DMP layer;
    protocol helpers pass their specialised classes so the affordances are
    built BEFORE interface validation (the after-validator stamps
    ``id_short`` = field name on every named-field child — post-construction
    assignment would leave the class defaults in place). ``form_extras(n,
    spec)`` returns extra form-field values for protocol-specific terms
    (e.g. the OPC UA ``uav_componentOf``)."""
    from aas_model.submodel_templates.aid import DmpAction, DmpActions
    from aas_pydantic.submodel_templates.asset_interfaces_description import (
        HtvMethodName,
    )
    meta = (meta_cls or DmpGenericInteractionMetadata)()
    properties_cls = properties_cls or type(meta.properties)
    actions_cls = actions_cls or DmpActions
    action_cls = action_cls or DmpAction
    form_cls = form_cls or DmpForm
    action_form_cls = action_form_cls or form_cls
    property_cls = property_cls or _BaseProperty
    obs_flags = observable if isinstance(observable, tuple) else (False, None)
    for n, h in (properties or {}).items():
        if property_cls is _BaseProperty:
            meta.properties.property_name[n] = _gen_property(
                n, h, observable=obs_flags[0], subprotocol=obs_flags[1], op=op)
        else:
            prop = property_cls(
                title=Title(value=n),
                forms=form_cls(
                    href=Href(value=h or ""), security=security_t(),
                    contentType=ContentType(value="application/json")))
            if obs_flags[0] and hasattr(prop, "observable"):
                prop.observable = AIDObservable(value="true")
            if obs_flags[1] is not None:
                prop.forms.subprotocol = Subprotocol(value=obs_flags[1])
            if op is not None and hasattr(prop.forms, "op"):
                prop.forms.op = Property(value=op)
            meta.properties.property_name[n] = prop
    if actions:
        acts = actions_cls(property_name={})
        for n, spec in actions.items():
            href, method = (spec[0], spec[1]) if isinstance(spec, tuple) else (spec, "POST")
            form = action_form_cls(
                href=Href(value=href), security=security_t(),
                op=Property(
                    semantic_id="https://www.w3.org/2019/wot/td#hasOperationType",
                    value="invokeaction"),
                contentType=ContentType(value="application/json"),
                htv_methodName=HtvMethodName(value=method))
            if form_extras:
                for fname, val in (form_extras(n, spec) or {}).items():
                    current = getattr(form, fname, None)
                    if isinstance(val, str) and current is not None and hasattr(current, "value"):
                        current.value = val
                    else:
                        setattr(form, fname, val)
            acts.property_name[n] = action_cls(title=Title(value=n), forms=form)
        meta.actions = acts
    return template_cls(
        title=Title(value="iface"),
        EndpointMetadata=_endpoint(base),
        InteractionMetadata=meta,
    )


def _opcua_form_extras(n, spec):
    """OPC-10101 §7.1.3: the owning Object NodeId (mandatory) + optional
    browsePath ride the protocol form."""
    extras = {}
    if len(spec) >= 3 and spec[2]:
        extras["uav_componentOf"] = spec[2]
    if len(spec) >= 4 and spec[3]:
        from aas_pydantic.submodel_templates.asset_interfaces_description import (
            UavBrowsePath,
        )
        extras["uav_browsePath"] = UavBrowsePath(value=spec[3])
    return extras


def opcua_interface(base: str, *, properties=None, actions=None, observable: bool = False,
                    subprotocol: str | None = None, op: str | None = None) -> DmpOpcuaInterface:
    """OPC UA interface. ``actions`` values are ``(href, method)`` or
    ``(href, method, componentOf[, browsePath])`` tuples — OPC UA actions
    carry the MANDATORY ``uav_componentOf`` owning-Object NodeId
    (OPC-10101 §7.1.3)."""
    from aas_model.submodel_templates.aid import (
        OpcuaAction, OpcuaActionForm, OpcuaActions, OpcuaForm,
        OpcuaInteractionMetadata, OpcuaProperties, OpcuaProperty,
    )
    return _gen_interface(
        DmpOpcuaInterface, base, properties=properties, actions=actions,
        observable=(observable, subprotocol), op=op,
        meta_cls=OpcuaInteractionMetadata, actions_cls=OpcuaActions,
        action_cls=OpcuaAction, form_cls=OpcuaForm,
        action_form_cls=OpcuaActionForm,
        properties_cls=OpcuaProperties, property_cls=OpcuaProperty,
        form_extras=_opcua_form_extras)


def http_interface(base: str, *, properties=None, actions=None) -> DmpHttpInterface:
    return _gen_interface(DmpHttpInterface, base, properties=properties, actions=actions)


def modbus_interface(base: str, *, properties=None, actions=None) -> DmpModbusInterface:
    from aas_model.submodel_templates.aid import (
        ModbusAction, ModbusActions, ModbusForm, ModbusInteractionMetadata,
        ModbusProperties, ModbusProperty,
    )
    return _gen_interface(
        DmpModbusInterface, base, properties=properties, actions=actions,
        meta_cls=ModbusInteractionMetadata, actions_cls=ModbusActions,
        action_cls=ModbusAction, form_cls=ModbusForm,
        properties_cls=ModbusProperties, property_cls=ModbusProperty)


def bacnet_interface(base: str, *, properties=None, actions=None) -> DmpBacnetInterface:
    from aas_model.submodel_templates.aid import (
        BacnetAction, BacnetActions, BacnetForm, BacnetInteractionMetadata,
        BacnetProperties, BacnetProperty,
    )
    return _gen_interface(
        DmpBacnetInterface, base, properties=properties, actions=actions,
        meta_cls=BacnetInteractionMetadata, actions_cls=BacnetActions,
        action_cls=BacnetAction, form_cls=BacnetForm,
        properties_cls=BacnetProperties, property_cls=BacnetProperty)


def build_aid(*, mqtt: MqttInterface | None = None,
              opcua: DmpOpcuaInterface | None = None,
              http: DmpHttpInterface | None = None,
              modbus: DmpModbusInterface | None = None,
              bacnet: DmpBacnetInterface | None = None,
              id_short: str = "AID") -> DmpAssetInterfacesDescription:
    """Compose an AID. All interfaces live in their ``InterfaceTemplateFor*``
    dicts (the DMP convention: the native MQTT interface is
    ``InterfaceTemplateForMQTT["interface_mqtt"]``)."""
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


def aimc_source(source_id: str, ref: ModelReference,
                polling_interval: float | None = None) -> Source:
    return Source(
        Source=Source_source(value=ref),
        SourceId=SourceId(value=source_id),
        PollingInterval=DefaultPollingInterval(value=str(polling_interval)) if polling_interval is not None else None,
    )


def aimc_sink(sink_id: str, ref: ModelReference) -> Sink:
    return Sink(Sink=Sink_sink(value=ref), SinkId=SinkId(value=sink_id))


def aimc_mapping(*, sources: list[Source], sinks: list[Sink],
                 transformation: str | None = None,
                 transformation_semantic_id: str | None = None,
                 response_transformation: str | None = None,
                 qualifiers: list | None = None,
                 default_polling_interval: float | None = None,
                 id_short: str = "mapping") -> AimcMappingConfiguration:
    kwargs = dict(
        id_short=id_short,
        Sources=Sources(value=sources),
        Sinks=Sinks(value=sinks),
    )
    if default_polling_interval is not None:
        kwargs["DefaultPollingInterval"] = DefaultPollingInterval(
            value=str(default_polling_interval))
    if transformation is not None:
        tblob = {"value": transformation.encode("utf-8")}
        if transformation_semantic_id:
            tblob["semantic_id"] = transformation_semantic_id
        kwargs["Transformation"] = Transformation(**tblob)
    if response_transformation is not None:
        kwargs["ResponseTransformation"] = DmpResponseTransformation(
            value=response_transformation.encode("utf-8"))
    if qualifiers is not None:
        kwargs["qualifiers"] = qualifiers
    return AimcMappingConfiguration(**kwargs)


def write_delegation_qualifier(
        path: str = "/properties/{aas_id_short}/Parameter") -> Qualifier:
    """The ``writeDelegation`` ConceptQualifier of a W2 write-delegation
    mapping; ``path`` is the derived caller surface (the ``{delegation_base}``
    macro inside the value resolves at build time)."""
    return Qualifier(
        type_="writeDelegation",
        value="{delegation_base}" + path if not path.startswith("{delegation_base}") else path,
        value_type="xs:string",
        kind="ConceptQualifier",
    )


def build_aimc(*mappings: AimcMappingConfiguration, id_short: str = "AIMC") -> Aimc:
    return Aimc(id_short=id_short,
                MappingConfigurations=AimcMappingConfigurations(value=list(mappings)))
