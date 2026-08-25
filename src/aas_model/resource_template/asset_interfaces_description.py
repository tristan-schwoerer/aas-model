"""Asset Interfaces Description partial — mandatory Resource actions/properties.

Built on our MQTT-extended AID (``aas_model.submodel_templates.mqtt_aid``), which
inherits from the generated IDTA AssetInterfacesDescription.  Every Resource
must expose the Halt / Occupy / Release actions and a StationState property.

Named-field style: children are DIRECT named fields (no ``value`` wrapper);
dynamic action/property maps are ``Dict[str, X]`` fields on the ``actions`` /
``properties`` containers.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from aas_pydantic import Property

from ..constants import BROKER, SITE, SCHEMA_BASE
from aas_model.json_schema_aid import datapoint_from_schema, load_schema, populate_datapoint
from aas_model.submodel_templates.mqtt_aid import (
    MqttAssetInterfacesDescription, MqttAction, MqttActionInput, MqttActionOutput,
    MqttProperty, MqttResponseForm,
)
from aas_model.submodel_templates.rest_aid import (
    RestInterface, RestAction, RestActionInput, RestActionOutput,
    RestProperty,
)
from aas_pydantic.submodel_templates.asset_interfaces_description import (
    Key as AIDKey,
    Title as AIDTitle,
)
from ._helpers import put, DEFAULT_SKILLS

# The StationState payload is described by ``stationState.schema.json`` — embed
# its object-schema structure (State enum, ProcessQueue array, TimeStamp) into
# the AID so the interface describes the message instead of only pointing at
# the schema URL.  The schema URL rides as a supplemental semantic id on the
# DataSchema it represents (the property itself for a property; the
# ``input``/``output`` DataSchemas for an action).
_STATION_STATE_SCHEMA = load_schema(f"{SCHEMA_BASE}/stationState.schema.json")

# Action command/response payloads — embedded as the WoT ``input``/``output``
# DataSchemas of every MQTT action (Halt / Occupy / Release / Stoppering).
_COMMAND_SCHEMA = load_schema(f"{SCHEMA_BASE}/command.schema.json")
_COMMAND_RESPONSE_SCHEMA = load_schema(f"{SCHEMA_BASE}/commandResponse.schema.json")

# Published schema URLs carried as supplemental semantic ids on the DataSchemas.
COMMAND_SCHEMA_URL = f"{SCHEMA_BASE}/command.schema.json"
COMMAND_RESPONSE_SCHEMA_URL = f"{SCHEMA_BASE}/commandResponse.schema.json"
STATION_STATE_SCHEMA_URL = f"{SCHEMA_BASE}/stationState.schema.json"


def mqtt_action(
    name: str,
    *,
    synchronous: bool = False,
    has_response: bool = True,
    input_schema: Optional[Dict[str, Any]] = _COMMAND_SCHEMA,
    output_schema: Optional[Dict[str, Any]] = _COMMAND_RESPONSE_SCHEMA,
    input_schema_url: str = COMMAND_SCHEMA_URL,
    output_schema_url: str = COMMAND_RESPONSE_SCHEMA_URL,
) -> MqttAction:
    """Build a standard MQTT action with default form settings.

    ``input_schema`` / ``output_schema`` (already-dereferenced JSON Schema
    dicts) embed the action's WoT ``input`` / ``output`` DataSchemas — by
    default the standard command / commandResponse schemas, so every MQTT
    action carries them (Halt, with ``has_response=False``, has no output).
    Pass ``None`` to omit one.  Each schema URL rides as a supplemental
    semantic id on the DataSchema it represents (``input`` / ``output``),
    not as a separate URL Property.
    """
    action = MqttAction()
    action.key = AIDKey(value=name)
    action.title = AIDTitle(value=name)
    action.synchronous.value = str(synchronous).lower()
    if input_schema is not None:
        action.input = datapoint_from_schema(
            input_schema, cls=MqttActionInput, schema_url=input_schema_url
        )
    if has_response and output_schema is not None:
        action.output = datapoint_from_schema(
            output_schema, cls=MqttActionOutput, schema_url=output_schema_url
        )
    forms = action.forms
    forms.href.value = f"/CMD/{name}"
    forms.op.value = "invokeAction"
    forms.mqv_retain.value = "false"
    forms.mqv_control_packet.value = "subscribe"
    forms.mqv_qos.value = "2"
    if has_response:
        # Build on the class defaults so the children keep their semanticIds
        # (href → hasTarget, content_type → forContentType, …) — constructing
        # bare ``Property(value=...)`` instances would strip them.
        resp = MqttResponseForm()
        resp.href.value = f"/DATA/{name}"
        resp.contentType.value = "application/json"
        resp.mqv_control_packet.value = "publish"
        resp.mqv_retain.value = "false"
        forms.response = resp
    return action


def mqtt_property(
    name: str, href: str, *, retain: bool = True, qos: int = 0,
    schema: Optional[Dict[str, Any]] = None,
    schema_url: str = STATION_STATE_SCHEMA_URL,
) -> MqttProperty:
    """Build a standard MQTT property with default form settings.

    ``schema`` (an already-dereferenced JSON Schema dict, e.g. from
    :func:`~templates.json_schema_aid.load_schema`) embeds the payload's
    object-schema structure (``type``/``properties``/``items``/``enum``/…)
    into the property via ``populate_datapoint``, leaving the forms untouched.
    The schema URL rides as a supplemental semantic id on the property itself.
    """
    prop = MqttProperty()
    prop.key = AIDKey(value=name)
    prop.title = AIDTitle(value=name)
    forms = prop.forms
    forms.href.value = href
    forms.mqv_retain.value = str(retain).lower()
    forms.mqv_control_packet.value = "publish"
    forms.mqv_qos.value = str(qos)
    if schema is not None:
        populate_datapoint(prop, schema, schema_url=schema_url)
    return prop


def rest_action(
    name: str,
    *,
    synchronous: bool = True,
    has_response: bool = True,
    input_schema: Optional[Dict[str, Any]] = _COMMAND_SCHEMA,
    output_schema: Optional[Dict[str, Any]] = _COMMAND_RESPONSE_SCHEMA,
    input_schema_url: str = COMMAND_SCHEMA_URL,
    output_schema_url: str = COMMAND_RESPONSE_SCHEMA_URL,
) -> RestAction:
    """Build a standard REST operation-delegation action.

    Describes the generated endpoint BaSyx forwards an AAS Operation
    invocation to — POST ``/operations/{aas_id_short}/{name}`` relative to the
    interface's base (the resource's DMP / operation-delegation service),
    matching the BaSyx operation-delegation example
    (``http://…/operations/<operation>``).  Uses the same command /
    commandResponse DataSchemas as the native MQTT action, so the AIMC
    transformation between the two is a field passthrough.
    """
    action = RestAction()
    action.key = AIDKey(value=name)
    action.title = AIDTitle(value=name)
    action.synchronous.value = str(synchronous).lower()
    if input_schema is not None:
        action.input = datapoint_from_schema(
            input_schema, cls=RestActionInput, schema_url=input_schema_url
        )
    if has_response and output_schema is not None:
        action.output = datapoint_from_schema(
            output_schema, cls=RestActionOutput, schema_url=output_schema_url
        )
    forms = action.forms
    forms.href.value = f"/operations/{{aas_id_short}}/{name}"
    forms.op.value = "invokeAction"
    forms.contentType.value = "application/json"
    forms.htv_methodName.value = "POST"
    return action


def rest_property(
    name: str, *,
    value_type: str = "xs:string",
    schema: Optional[Dict[str, Any]] = None,
    schema_url: str = "",
) -> RestProperty:
    """Build a standard REST write-delegation property.

    Describes the generated endpoint a write to the AAS property is forwarded
    to — PUT ``/properties/{aas_id_short}/{name}`` relative to the interface's
    base (the resource's DMP).  ``op`` carries the WoT ``writeProperty``
    operation type.  An optional payload ``schema`` (JSON Schema dict) is
    embedded like the MQTT/REST action DataSchemas.
    """
    prop = RestProperty()
    prop.key = AIDKey(value=name)
    prop.title = AIDTitle(value=name)
    if schema is not None:
        populate_datapoint(prop, schema, schema_url=schema_url)
    elif value_type:
        prop.type = Property(value=value_type)
    forms = prop.forms
    forms.href.value = f"/properties/{{aas_id_short}}/{name}"
    forms.op.value = "writeProperty"
    forms.contentType.value = "application/json"
    forms.htv_methodName.value = "PUT"
    return prop


def rest_interface(actions, properties=()) -> RestInterface:
    """Build the REST operation-delegation interface for the given actions
    and write-able properties.

    ``actions`` is a sequence of ``(name, synchronous, has_response)`` tuples;
    ``properties`` is a sequence of ``(name, value_type)`` tuples (or
    ``(name, value_type, schema, schema_url)``).  The base is the resource's
    DMP / operation-delegation service URL; each href is relative to it.
    """
    iface = RestInterface()
    iface.title.value = "Operation Delegation"
    # ``{delegation_base}`` macro — resolved by id_injector to the resource's
    # DMP/operation-delegation base URL (default: constants.DELEGATION_BASE).
    iface.EndpointMetadata.base.value = "{delegation_base}"
    iface.EndpointMetadata.contentType.value = "application/json"
    im = iface.InteractionMetadata
    for name, synchronous, has_response in actions:
        put(
            im.actions.property_name, name,
            rest_action(name, synchronous=synchronous, has_response=has_response),
        )
    for entry in properties:
        if len(entry) >= 4:
            name, value_type, schema, schema_url = entry
        else:
            name, value_type = entry
            schema, schema_url = None, ""
        put(
            im.properties.property_name, name,
            rest_property(name, value_type=value_type, schema=schema, schema_url=schema_url),
        )
    return iface


def _datapoint_schema_url(dp) -> str:
    """The JSON Schema URL carried as a supplemental semantic id of *dp*, or
    ``""`` when none is present."""
    for sid in (dp.supplemental_semantic_ids or []):
        if isinstance(sid, str) and "schema" in sid:
            return sid
    return ""


def ensure_aid_datapoint_schemas(aid) -> None:
    """Populate config-provided datapoint DataSchemas from their schema URL.

    Config actions may declare ``input`` / ``output`` (and properties the
    property itself) with just ``supplemental_semantic_ids`` naming the JSON
    Schema URL — this fills their object-schema structure from that schema
    (the same way ``mqtt_action``/``mqtt_property`` build the defaults), so a
    config-only action like Stoppering gets the same embedded DataSchemas
    without hand-writing the schema structure in the config.
    """
    for iface in (getattr(aid, "interface_mqtt", None),
                  getattr(aid, "interface_rest", None)):
        if iface is None:
            continue
        imd = getattr(iface, "InteractionMetadata", None)
        if imd is None:
            continue
        actions = getattr(getattr(imd, "actions", None), "property_name", None) or {}
        for action in actions.values():
            for fname in ("input", "output"):
                dp = getattr(action, fname, None)
                if dp is None or getattr(dp, "type", None) is not None:
                    continue
                url = _datapoint_schema_url(dp)
                if url:
                    populate_datapoint(dp, load_schema(url), schema_url=url)
        props = getattr(getattr(imd, "properties", None), "property_name", None) or {}
        for prop in props.values():
            if getattr(prop, "type", None) is not None:
                continue
            url = _datapoint_schema_url(prop)
            if url:
                populate_datapoint(prop, load_schema(url), schema_url=url)


def asset_interfaces_description() -> MqttAssetInterfacesDescription:
    """AssetInterfacesDescription with mandatory Resource actions/properties."""
    aid = MqttAssetInterfacesDescription(id_short="AssetInterfacesDescription")
    iface = aid.interface_mqtt
    ep = iface.EndpointMetadata
    ep.base.value = f"{BROKER}/{SITE}/{{station_name}}"
    ep.contentType.value = "application/json"
    im = iface.InteractionMetadata
    put(
        im.actions.property_name, "Halt",
        mqtt_action("Halt", synchronous=True, has_response=False),
    )
    put(
        im.actions.property_name, "Occupy",
        mqtt_action("Occupy", synchronous=True),
    )
    put(
        im.actions.property_name, "Release",
        mqtt_action("Release", synchronous=True),
    )
    put(
        im.properties.property_name, "StationState",
        mqtt_property("StationState", "/DATA/State", schema=_STATION_STATE_SCHEMA),
    )
    # REST operation-delegation interface mirroring the default skills.
    aid.interface_rest = rest_interface(DEFAULT_SKILLS)
    return aid
