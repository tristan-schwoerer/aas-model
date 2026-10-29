"""
Shared constants for the templates package.

All project-specific semantic IDs are defined here.
IDTA-defined semantic IDs (admin-shell.io/idta/...) stay in their generated templates.
Third-party semantic IDs (w3.org, schema.org, purl.org, etc.) stay inline in their modules.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# Base URLs
# ═══════════════════════════════════════════════════════════════════════════════

BASE_URL = "https://smartproductionlab.aau.dk"
SCHEMA_BASE = "https://aausmartproductionlab.github.io/AP2030-UNS/MQTTSchemas"

# ═══════════════════════════════════════════════════════════════════════════════
# Infrastructure defaults
# ═══════════════════════════════════════════════════════════════════════════════

BROKER = "mqtt://192.168.0.104:1883"
SITE = "NN/Nybrovej/InnoLab"

# Shared invocation service origin. Resource-specific identity belongs in
# authored URL path segments, never in a per-resource host/config setting.
INVOCATION_ORIGIN = "http://dmp:8080"
# An Operation's invocationDelegation URL: the origin and the path the Operation is invoked at in the AAS API,
# filled in once the Operation's submodel id and idShortPath are known (invocation_authoring).
INVOCATION_URL_TEMPLATE = f"{INVOCATION_ORIGIN}{{operation_path}}"

# ═══════════════════════════════════════════════════════════════════════════════
# Ontology
# ═══════════════════════════════════════════════════════════════════════════════

CSSX = "http://www.w3id.org/aau-ra/cssx"

# The concepts of an operational device's state: its PackML state and its occupation (the process queue).
STATE_OPERATIONAL = "https://w3id.org/2026/apex/semantic/state/operational"
STATE_OCCUPIED = "https://w3id.org/2026/apex/semantic/state/occupied"

# ═══════════════════════════════════════════════════════════════════════════════
# Submodel ids
# ═══════════════════════════════════════════════════════════════════════════════
# The id injector gives each submodel of a resource the id ``{aas_id}/submodels/<idShort>``; references into a
# resource's own submodels are authored against these and resolved with it.

AID_SUBMODEL_ID = "{aas_id}/submodels/AssetInterfacesDescription"
CCI_SUBMODEL_ID = "{aas_id}/submodels/ControlComponentInstance"
CONTROL_COMPONENT_TYPE_SUBMODEL_ID = "{aas_id}/submodels/ControlComponentType"
VARIABLES_SUBMODEL_ID = "{aas_id}/submodels/Variables"
CAPABILITIES_SUBMODEL_ID = "{aas_id}/submodels/CapabilityDescription"
HIERARCHICAL_STRUCTURES_SUBMODEL_ID = "{aas_id}/submodels/HierarchicalStructures"

# ═══════════════════════════════════════════════════════════════════════════════
# AID extension (docs/aid-extension.md) — WoT TD terms AID 1.2 does not carry.
# IRIs are those of the TD 1.1 JSON-LD context (td:, hctl:, jsonschema:).
# ═══════════════════════════════════════════════════════════════════════════════

WOT_TD = "https://www.w3.org/2019/wot/td#"
WOT_HCTL = "https://www.w3.org/2019/wot/hypermedia#"
WOT_JSONSCHEMA = "https://www.w3.org/2019/wot/json-schema#"

# Affordance members. AID gives a property member its own id
# (``…/1/0/PropertyDefinition``) and the TD class to the container; actions
# and events follow the same pattern with ids in this project's namespace.
AID_ACTION_DEFINITION = f"{BASE_URL}/aid/ActionDefinition/1/0"
AID_EVENT_DEFINITION = f"{BASE_URL}/aid/EventDefinition/1/0"
AID_WOT_NAME = f"{WOT_TD}name"

# ActionAffordance
AID_ACTION_INPUT = f"{WOT_TD}hasInputSchema"
AID_ACTION_OUTPUT = f"{WOT_TD}hasOutputSchema"
AID_WOT_SAFE = f"{WOT_TD}isSafe"
AID_WOT_IDEMPOTENT = f"{WOT_TD}isIdempotent"
AID_SYNCHRONOUS = f"{WOT_TD}isSynchronous"

# EventAffordance
AID_EVENT_SUBSCRIPTION = f"{WOT_TD}hasSubscriptionSchema"
AID_EVENT_DATA = f"{WOT_TD}hasNotificationSchema"
AID_EVENT_DATA_RESPONSE = f"{WOT_TD}hasNotificationResponseSchema"
AID_EVENT_CANCELLATION = f"{WOT_TD}hasCancellationSchema"

# DataSchema terms AID marks EXTERNAL (TD 1.1 context, jsonschema: prefix).
# readOnly/writeOnly apply to any data schema, not only to properties.
AID_WOT_READ_ONLY = f"{WOT_JSONSCHEMA}readOnly"
AID_WOT_WRITE_ONLY = f"{WOT_JSONSCHEMA}writeOnly"
AID_WOT_DATA_SCHEMA = f"{WOT_JSONSCHEMA}DataSchema"
AID_WOT_REQUIRED = f"{WOT_JSONSCHEMA}required"
AID_WOT_ONE_OF = f"{WOT_JSONSCHEMA}oneOf"
AID_WOT_ITEMS = f"{WOT_JSONSCHEMA}items"
AID_WOT_EXCLUSIVE_MINIMUM = f"{WOT_JSONSCHEMA}exclusiveMinimum"
AID_WOT_EXCLUSIVE_MAXIMUM = f"{WOT_JSONSCHEMA}exclusiveMaximum"
AID_WOT_MULTIPLE_OF = f"{WOT_JSONSCHEMA}multipleOf"
AID_WOT_PATTERN = f"{WOT_JSONSCHEMA}pattern"
AID_WOT_FORMAT = f"{WOT_JSONSCHEMA}format"
AID_WOT_CONTENT_ENCODING = f"{WOT_JSONSCHEMA}contentEncoding"
AID_WOT_CONTENT_MEDIA_TYPE = f"{WOT_JSONSCHEMA}contentMediaType"

# Form
AID_WOT_OPERATION_TYPE = f"{WOT_HCTL}hasOperationType"
AID_WOT_RESPONSE_FORM = f"{WOT_HCTL}returns"
AID_WOT_ADDITIONAL_RESPONSES = f"{WOT_HCTL}additionalReturns"
AID_WOT_ADDITIONAL_RESPONSE = f"{WOT_HCTL}AdditionalExpectedResponse"
AID_WOT_RESPONSE_SUCCESS = f"{WOT_HCTL}isSuccess"
AID_WOT_RESPONSE_SCHEMA = f"{WOT_HCTL}hasAdditionalOutputSchema"

# MQTT 5 request/reply. The WoT MQTT binding has no request/reply; the request
# carries this topic as its Response Topic and the reply echoes the request's
# Correlation Data.
AID_MQTT_RESPONSE_TOPIC = f"{BASE_URL}/aid/MqttResponseTopic/1/0"

# OPC UA. OPC 10101 v1.00 defines uav:componentOf but no event vocabulary, so
# the event terms live in this project's namespace: the EventType a
# subscription is filtered to (where clause, OfType) and, per data-schema
# property, the field's browse path relative to the event (select clause).
AID_OPCUA_COMPONENT_OF = "http://opcfoundation.org/UA/WoT-Binding/componentOf"
AID_OPCUA_EVENT_TYPE = f"{BASE_URL}/aid/OpcuaEventType/1/0"
AID_OPCUA_EVENT_FIELD = f"{BASE_URL}/aid/OpcuaEventField/1/0"

# ═══════════════════════════════════════════════════════════════════════════════
# AIMC — DMP extensions of the IDTA MappingConfiguration
# ═══════════════════════════════════════════════════════════════════════════════
# IDTA AIMC 2.0 defines Sources, Sinks, Transformation and DefaultPollingInterval.
# Everything an operation mapping adds lives in this project's namespace, so a
# standard AIMC consumer can tell the additions apart. Per invocation:
# command (IDTA Sources/Transformation/Sinks) → response (Response*).

# Response: members of the action's output, the Lua that builds the caller's
# reply, and the elements it writes.
AIMC_RESPONSE_SOURCES = f"{BASE_URL}/aimc/ResponseSources/1/0"
AIMC_RESPONSE_SOURCE = f"{BASE_URL}/aimc/ResponseSource/1/0"
AIMC_RESPONSE_SOURCE_REFERENCE = f"{BASE_URL}/aimc/ResponseSource/Source/1/0"
AIMC_RESPONSE_SOURCE_ID = f"{BASE_URL}/aimc/ResponseSource/SourceId/1/0"
AIMC_RESPONSE_TRANSFORMATION = f"{BASE_URL}/aimc/ResponseTransformation/1/0"
AIMC_RESPONSE_SINKS = f"{BASE_URL}/aimc/ResponseSinks/1/0"
AIMC_RESPONSE_SINK = f"{BASE_URL}/aimc/ResponseSink/1/0"
AIMC_RESPONSE_SINK_REFERENCE = f"{BASE_URL}/aimc/ResponseSink/Sink/1/0"
AIMC_RESPONSE_SINK_ID = f"{BASE_URL}/aimc/ResponseSink/SinkId/1/0"

# Which source updates execute an ordinary mapping.
# A Source's Evaluation: whether it triggers its mapping and how its value is obtained.
AIMC_EVALUATION = f"{BASE_URL}/aimc/Evaluation/1/0"
AIMC_EVALUATION_MODE = f"{BASE_URL}/aimc/Evaluation/Mode/1/0"

# How long a mapping an Operation triggers waits for the device's terminal reply.
AIMC_INVOCATION_TIMEOUT = f"{BASE_URL}/aimc/InvocationTimeout/1/0"

# ═══════════════════════════════════════════════════════════════════════════════
# TimeSeries — DMP profile of IDTA 02008 (TimeSeries SMCs in Variables)
# ═══════════════════════════════════════════════════════════════════════════════
# A TimeSeries SMC is shaped exactly like the IDTA submodel; only the SMC
# itself and the DMP additions (the LinkedSegment's write target, Record fields,
# groups and references) carry ids in this project's namespace.

# The InfluxDB 2 instance every LinkedSegment of this workspace points at.
INFLUX_ORIGIN = "http://influxdb:8086"
INFLUX_ORG = "ap2030"
INFLUX_BUCKET = "ap2030"

TS_COLLECTION = f"{BASE_URL}/variables/TimeSeries/1/0"
TS_RECORD_FIELD = f"{BASE_URL}/timeseries/RecordField/1/0"
TS_RECORD_GROUP = f"{BASE_URL}/timeseries/RecordGroup/1/0"
TS_RECORD_REFERENCE = f"{BASE_URL}/timeseries/RecordReference/1/0"
TS_RECORD_RANGE = f"{BASE_URL}/timeseries/RecordRange/1/0"
TS_RECORD_FILE = f"{BASE_URL}/timeseries/RecordFile/1/0"
TS_RECORD_TEXT = f"{BASE_URL}/timeseries/RecordText/1/0"
TS_INFLUX_TARGET = f"{BASE_URL}/timeseries/InfluxDb2Target/1/0"
TS_INFLUX_TARGET_BUCKET = f"{BASE_URL}/timeseries/InfluxDb2Target/Bucket/1/0"
TS_INFLUX_TARGET_MEASUREMENT = f"{BASE_URL}/timeseries/InfluxDb2Target/Measurement/1/0"
TS_INFLUX_TARGET_TAGS = f"{BASE_URL}/timeseries/InfluxDb2Target/Tags/1/0"
TS_INFLUX_TARGET_TAG = f"{BASE_URL}/timeseries/InfluxDb2Target/Tag/1/0"
TS_INFLUX_TARGET_WRITE_MODE = f"{BASE_URL}/timeseries/InfluxDb2Target/WriteMode/1/0"
