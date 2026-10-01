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

# Operation delegation — base URL of the per-asset DMP (Data Mapping
# Processor) REST endpoints.  BaSyx invokes the per-skill Operation's
# ``invocationDelegation`` qualifier (and property ``writeDelegation``) at
# ``{DELEGATION_BASE}/operations/{aas_id_short}/{skill}`` resp.
# ``/properties/{aas_id_short}/{property}``; the AID REST interface describes
# these generated endpoints.
#
# The default derives the DMP hostname from the asset id_short — unique per
# asset — so no per-resource configuration is needed and the runtime
# registration handler can create the K8s Service under the same name:
# ``dmp-<aas_id_short>`` lowercased (K8s Service/DNS-1123 names must be
# lowercase).  Macros resolved by the id_injector:
#   {dmp_host}       → ``dmp-<aas_id_short lowercased>``
#   {aas_id_short}   → the AAS id_short
#   {delegation_base}→ this value with the macros above resolved
# Override per resource via the top-level ``delegation_base`` config key,
# e.g. an Ingress/LoadBalancer URL, or a cross-namespace FQDN:
# ``http://{dmp_host}.robotics.svc.cluster.local:8080``.
DELEGATION_BASE = "http://{dmp_host}:8080"

# ═══════════════════════════════════════════════════════════════════════════════
# Ontology
# ═══════════════════════════════════════════════════════════════════════════════

CSSX = "http://www.w3id.org/aau-ra/cssx"

# ═══════════════════════════════════════════════════════════════════════════════
# MQTT Asset Interfaces Description — extended fields
# ═══════════════════════════════════════════════════════════════════════════════

AID_MQTT_RESPONSE_FORM = f"{BASE_URL}/aid/MqttResponseForm/1/0"
AID_MQTT_RETAIN = f"{BASE_URL}/aid/MqttRetain/1/0"
AID_MQTT_CONTROL_PACKET = f"{BASE_URL}/aid/MqttControlPacket/1/0"
AID_MQTT_QOS = f"{BASE_URL}/aid/MqttQos/1/0"
# WoT MQTT binding (MQTT 5) request/reply correlation: ``requestReply``
# marks the action as a correlated request/reply interaction and
# ``responseTopic`` names the MQTT 5 Response Topic the reply is
# delivered on (the requester sets it as the PUBLISH response-topic
# property; the responder echoes the request's Correlation Data).
AID_MQTT_REQUEST_REPLY = f"{BASE_URL}/aid/MqttRequestReply/1/0"
AID_MQTT_RESPONSE_TOPIC = f"{BASE_URL}/aid/MqttResponseTopic/1/0"
AID_INPUT_SCHEMA = f"{BASE_URL}/aid/InputSchema/1/0"
AID_OUTPUT_SCHEMA = f"{BASE_URL}/aid/OutputSchema/1/0"
AID_SYNCHRONOUS = "https://www.w3.org/2019/wot/td#synchronous"
AID_WOT_SAFE = "https://www.w3.org/2019/wot/td#safe"
AID_WOT_IDEMPOTENT = "https://www.w3.org/2019/wot/td#idempotent"

# WoT Thing Description 2.0 ``ActionAffordance.input`` / ``.output`` vocabulary
# (w3.org — kept inline per the constants policy).  Shared by the MQTT and the
# generic (Dmp) action DataSchemas.
AID_ACTION_INPUT = "https://www.w3.org/2019/wot/td#hasInput"
AID_ACTION_OUTPUT = "https://www.w3.org/2019/wot/td#hasOutput"
AID_WOT_OPERATION_TYPE = "https://www.w3.org/2019/wot/td#hasOperationType"
AID_WOT_RESPONSE_FORM = "https://www.w3.org/2019/wot/hypermedia#response"

# AIMC mapping extension (DMP v3, ADR-022): the OPTIONAL correlated-reply
# direction of an operation mapping — mirrors the IDTA ``Transformation``
# vocabulary member.  Authored on ``DmpMappingConfiguration``; when absent the
# reply passes through unchanged.
AIMC_RESPONSE_TRANSFORMATION = ("https://admin-shell.io/idta/"
                                "AssetInterfacesMappingConfiguration/2/0/"
                                "MappingConfiguration/ResponseTransformation")

# Property write-delegation (``writeDelegation`` ConceptQualifier, DMP v3):
# configs author the qualifier directly — the convention is documented in
# resource_template/property_delegation.py (external-caller documentation
# only; the DMP wires its write-through routes from it).

