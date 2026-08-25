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
AID_INPUT_SCHEMA = f"{BASE_URL}/aid/InputSchema/1/0"
AID_OUTPUT_SCHEMA = f"{BASE_URL}/aid/OutputSchema/1/0"
AID_SYNCHRONOUS = f"{BASE_URL}/aid/Synchronous/1/0"

# WoT Thing Description 2.0 ``ActionAffordance.input`` / ``.output`` vocabulary
# (w3.org — kept inline per the constants policy).  Shared by the MQTT and the
# REST action DataSchemas.
AID_ACTION_INPUT = "https://www.w3.org/2019/wot/td#hasInput"
AID_ACTION_OUTPUT = "https://www.w3.org/2019/wot/td#hasOutput"

# ═══════════════════════════════════════════════════════════════════════════════
# REST Asset Interfaces Description — operation-delegation interface
# ═══════════════════════════════════════════════════════════════════════════════

AID_REST_OPERATION = f"{BASE_URL}/aid/RestOperation/1/0"
AID_REST_PROPERTY = f"{BASE_URL}/aid/RestProperty/1/0"
AID_REST_FORM = f"{BASE_URL}/aid/RestForm/1/0"
AID_REST_HTTP_METHOD = f"{BASE_URL}/aid/RestMethod/1/0"

# WoT operation types for the REST delegation interface.
AID_WOT_WRITE_PROPERTY = "https://www.w3.org/2019/wot/td#writeProperty"
AID_WOT_INVOKE_ACTION = "https://www.w3.org/2019/wot/td#invokeAction"

# Property write-delegation qualifier — carried on a Property to signal that
# writes to it are forwarded to the referenced REST write endpoint (the
# ``interface_rest`` property describing the DMP route).  ``type_`` is the
# ConceptQualifier type string; the semantic id is optional.
WRITE_DELEGATION = "writeDelegation"
WRITE_DELEGATION_SEMANTIC = f"{BASE_URL}/aid/WriteDelegation/1/0"

