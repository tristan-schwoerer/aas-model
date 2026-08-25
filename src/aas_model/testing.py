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
    Title, EndpointMetadata, security_t, securityDefinitions,
    Base, ContentType, Href, Subprotocol, Type as AIDType, Observable as AIDObservable,
    forms as _BaseForm, property_name as _BaseProperty,
    properties as _BaseProperties, actions as _BaseActions,
    InteractionMetadata as _BaseInteractionMetadata,
    InterfaceTemplateForOPCUA, InterfaceTemplateForHTTP,
    InterfaceTemplateForMODBUS, InterfaceTemplateForOPCUA_t, InterfaceTemplateForHTTP_t,
    InterfaceTemplateForMODBUS_t, HtvMethodName,
)

from aas_model.submodel_templates.mqtt_aid import (
    MqttAssetInterfacesDescription, MqttInterface, MqttInteractionMetadata,
    MqttProperties, MqttProperty, MqttForm, MqttActions, MqttAction,
    MqttResponseForm,
)
from aas_model.submodel_templates.rest_aid import (
    RestInterface, RestProperties, RestProperty, RestForm, RestActions,
    RestAction, RestInteractionMetadata,
)
from aas_model.submodel_templates.aimc import (
    Aimc, AimcMappingConfiguration, AimcMappingConfigurations, Transformation,
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
                  control_packet: str = "publish", retain: bool = True) -> MqttProperty:
    return MqttProperty(
        forms=MqttForm(
            href=Href(value=href),
            mqv_retain=_prop(str(retain).lower()),
            mqv_qos=_prop(str(qos)),
            mqv_control_packet=_prop(control_packet),
        )
    )


def mqtt_action(name: str, href: str, *, synchronous: bool = False,
                response: str | None = None) -> MqttAction:
    form_kwargs = dict(
        href=Href(value=href),
        op=_prop("invokeAction"),
        mqv_retain=_prop("false"),
        mqv_qos=_prop("2"),
        mqv_control_packet=_prop("subscribe"),
    )
    if response is not None:
        form_kwargs["response"] = MqttResponseForm(
            href=Href(value=response), contentType=ContentType(value="application/json"),
            mqv_retain=_prop("false"), mqv_control_packet=_prop("publish"),
        )
    return MqttAction(
        synchronous=_prop(str(synchronous).lower()),
        forms=MqttForm(**form_kwargs),
    )


def mqtt_interface(base: str, *, properties=None, actions=None, events=None) -> MqttInterface:
    meta = MqttInteractionMetadata()
    meta.properties = MqttProperties(property_name={n: mqtt_property(n, h) for n, h in (properties or {}).items()})
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


def rest_action(name: str, href: str, *, method: str = "POST",
                response: bool = True) -> RestAction:
    return RestAction(
        synchronous=_prop("true"),
        forms=RestForm(href=Href(value=href), op=_prop("invokeAction"),
                       htv_methodName=HtvMethodName(value=method)),
    )


def rest_interface(base: str, *, actions=None) -> RestInterface:
    meta = RestInteractionMetadata()
    meta.actions = RestActions(property_name={n: rest_action(n, h) for n, h in (actions or {}).items()})
    return RestInterface(
        title=Title(value="rest"),
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
                   observable=(False, None), op: str | None = None):
    meta = _BaseInteractionMetadata()
    meta.properties = _BaseProperties(property_name={})
    obs_flags = observable if isinstance(observable, tuple) else (False, None)
    for n, h in (properties or {}).items():
        meta.properties.property_name[n] = _gen_property(
            n, None, observable=obs_flags[0], subprotocol=obs_flags[1], op=op)
    return template_cls(
        title=Title(value="iface"),
        EndpointMetadata=_endpoint(base),
        InteractionMetadata=meta,
    )


def opcua_interface(base: str, *, properties=None, observable: bool = False,
                    subprotocol: str | None = None, op: str | None = None) -> InterfaceTemplateForOPCUA:
    return _gen_interface(InterfaceTemplateForOPCUA, base, properties=properties,
                          observable=(observable, subprotocol), op=op)


def http_interface(base: str, *, properties=None) -> InterfaceTemplateForHTTP:
    return _gen_interface(InterfaceTemplateForHTTP, base, properties=properties)


def modbus_interface(base: str, *, properties=None) -> InterfaceTemplateForMODBUS:
    return _gen_interface(InterfaceTemplateForMODBUS, base, properties=properties)


def build_aid(*, mqtt: MqttInterface | None = None,
              rest: RestInterface | None = None,
              opcua: InterfaceTemplateForOPCUA | None = None,
              http: InterfaceTemplateForHTTP | None = None,
              modbus: InterfaceTemplateForMODBUS | None = None,
              id_short: str = "AID") -> MqttAssetInterfacesDescription:
    """Compose an AID. MQTT/REST go to the typed fields (``interface_*``); the
    generic protocol interfaces into their ``InterfaceTemplateFor*`` dicts."""
    aid = MqttAssetInterfacesDescription(id_short=id_short)
    if mqtt is not None:
        aid.interface_mqtt = mqtt
    if rest is not None:
        aid.interface_rest = rest
    if opcua is not None:
        aid.InterfaceTemplateForOPCUA["interface_opcua"] = opcua
    if http is not None:
        aid.InterfaceTemplateForHTTP["interface_http"] = http
    if modbus is not None:
        aid.InterfaceTemplateForMODBUS["interface_modbus"] = modbus
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
    return AimcMappingConfiguration(**kwargs)


def build_aimc(*mappings: AimcMappingConfiguration, id_short: str = "AIMC") -> Aimc:
    return Aimc(id_short=id_short,
                MappingConfigurations=AimcMappingConfigurations(value=list(mappings)))
