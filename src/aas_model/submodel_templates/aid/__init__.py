"""
DMP-extended AssetInterfacesDescription — extensions over the generated IDTA AID.

The design and the reasons for every term are in ``docs/aid-extension.md``.
In short:

- The generated IDTA template
  (``aas_pydantic.submodel_templates.asset_interfaces_description``) stays
  pristine, and everything AID 1.2 defines is used as it is: the generated
  ``forms`` already carries every protocol's binding terms
  (``htv_methodName``, ``modv_*``, ``mqv_controlPacket``, ``uav_browsePath``,
  ``bacv_*``, …), and the generated ``EndpointMetadata`` and
  ``securityDefinitions`` cover every protocol.
- This module only adds what AID leaves out (Annex D "EXTERNAL", or not
  mentioned): action and event members, the form's ``op``, ``response`` and
  ``additionalResponses``, and the TD DataSchema terms on every data schema
  (``required``, ``oneOf``, exclusive bounds, ``multipleOf``, ``pattern``,
  ``format``, content terms, ``readOnly``/``writeOnly``; ``items`` holding a
  full schema). They carry their W3C IRIs.
- Terms no specification defines carry ids in this project's namespace:
  ``mqv_responseTopic`` (MQTT 5 request/reply) and the OPC UA event terms
  ``uav_eventType``/``uav_eventField``. ``uav_componentOf`` is OPC 10101's.

Absent terms take their WoT TD defaults; in particular a form without ``op``
serves the affordance's default operations (docs/aid-extension.md §3.4).

Layout: ``data_schema`` (the DataSchema at every depth), ``forms``,
``affordances`` (properties, actions, events), ``interface`` (shared endpoint
metadata), ``bindings/<protocol>`` (each protocol's terms and interface class)
and ``submodel`` (the AID). Everything is re-exported here.

Named-field style: containers hold their child elements as DIRECT named
fields (field name == id_short) — no ``value``/``submodel_element`` wrapper.
"""

from __future__ import annotations

from aas_model.submodel_templates.aid.elements import (
    StringList,
)
from aas_model.submodel_templates.aid.data_schema import (
    Required, ExclusiveMinimum, ExclusiveMaximum, MultipleOf, Pattern, SchemaFormat,
    ContentEncoding, ContentMediaType, ReadOnly, WriteOnly, DataSchemaTerms, DmpDataSchema,
    DmpItems, DmpSchemaProperties, DmpOneOfBranch, OneOf,
)
from aas_model.submodel_templates.aid.forms import (
    Op, AdditionalResponseSuccess, AdditionalResponseSchema, AdditionalResponse,
    AdditionalResponses, DmpForm, DmpResponseForm, DmpActionForm,
)
from aas_model.submodel_templates.aid.affordances import (
    DmpProperty, DmpProperties, Safe, Idempotent, Synchronous, DmpActionInput, DmpActionOutput,
    DmpAction, DmpActions, DmpEventSubscription, DmpEventData, DmpEventDataResponse,
    DmpEventCancellation, DmpEvent, DmpEvents, DmpInteractionMetadata,
)
from aas_model.submodel_templates.aid.interface import (
    DmpEndpointMetadata,
)
from aas_model.submodel_templates.aid.bindings.http import (
    HttpForm, HttpActionForm, DmpHttpInterface,
)
from aas_model.submodel_templates.aid.bindings.modbus import (
    ModbusForm, ModbusInteractionMetadata, DmpModbusEndpointMetadata, DmpModbusInterface,
)
from aas_model.submodel_templates.aid.bindings.bacnet import (
    BacnetForm, BacnetInteractionMetadata, DmpBacnetInterface,
)
from aas_model.submodel_templates.aid.bindings.iolink import (
    IolinkForm, IolinkInteractionMetadata, DmpIolinkInterface,
)
from aas_model.submodel_templates.aid.bindings.can import (
    CanForm, CanInteractionMetadata, DmpCanInterface,
)
from aas_model.submodel_templates.aid.bindings.mqtt import (
    MqvResponseTopic, MqttForm, MqttActionForm, MqttAction, MqttActions, MqttInteractionMetadata,
    MqttInterface,
)
from aas_model.submodel_templates.aid.bindings.opcua import (
    UavComponentOf, OpcuaForm, OpcuaActionForm, DmpOpcuaEndpointMetadata, OpcuaAction, OpcuaActions, UavEventType, UavEventField,
    OpcuaEventField, OpcuaEventFields, OpcuaEventData, OpcuaEvent, OpcuaEvents,
    OpcuaInteractionMetadata, DmpOpcuaInterface,
)
from aas_model.submodel_templates.aid.bindings.snmp import (
    SnmpvPduType, SnmpvVersion, SnmpForm, SnmpProperty, SnmpProperties, SnmpInteractionMetadata,
    DmpSnmpInterface,
)
from aas_model.submodel_templates.aid.submodel import (
    DmpAssetInterfacesDescription,
)

__all__ = [
    "StringList",
    "Required", "ExclusiveMinimum", "ExclusiveMaximum", "MultipleOf", "Pattern", "SchemaFormat", "ContentEncoding", "ContentMediaType", "ReadOnly", "WriteOnly", "DataSchemaTerms", "DmpDataSchema", "DmpItems", "DmpSchemaProperties", "DmpOneOfBranch", "OneOf",
    "Op", "AdditionalResponseSuccess", "AdditionalResponseSchema", "AdditionalResponse", "AdditionalResponses", "DmpForm", "DmpResponseForm", "DmpActionForm",
    "DmpProperty", "DmpProperties", "Safe", "Idempotent", "Synchronous", "DmpActionInput", "DmpActionOutput", "DmpAction", "DmpActions", "DmpEventSubscription", "DmpEventData", "DmpEventDataResponse", "DmpEventCancellation", "DmpEvent", "DmpEvents", "DmpInteractionMetadata",
    "DmpEndpointMetadata",
    "HttpForm", "HttpActionForm", "DmpHttpInterface",
    "ModbusForm", "ModbusInteractionMetadata", "DmpModbusEndpointMetadata", "DmpModbusInterface",
    "BacnetForm", "BacnetInteractionMetadata", "DmpBacnetInterface",
    "IolinkForm", "IolinkInteractionMetadata", "DmpIolinkInterface",
    "CanForm", "CanInteractionMetadata", "DmpCanInterface",
    "MqvResponseTopic", "MqttForm", "MqttActionForm", "MqttAction", "MqttActions", "MqttInteractionMetadata", "MqttInterface",
    "UavComponentOf", "OpcuaForm", "OpcuaActionForm", "DmpOpcuaEndpointMetadata", "OpcuaAction", "OpcuaActions", "UavEventType", "UavEventField", "OpcuaEventField", "OpcuaEventFields", "OpcuaEventData", "OpcuaEvent", "OpcuaEvents", "OpcuaInteractionMetadata", "DmpOpcuaInterface",
    "SnmpvPduType", "SnmpvVersion", "SnmpForm", "SnmpProperty", "SnmpProperties", "SnmpInteractionMetadata", "DmpSnmpInterface",
    "DmpAssetInterfacesDescription",
]
