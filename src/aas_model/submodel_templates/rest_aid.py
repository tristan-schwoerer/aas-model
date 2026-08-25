"""REST-extended AssetInterfacesDescription interface — operation delegation.

Mirrors ``mqtt_aid.py`` but for the generated REST/HTTP operation-delegation
endpoints.  Each Resource skill is exposed as an AAS Operation (in the CCI)
whose ``invocationDelegation`` qualifier points at the OperationDelegation
service; this interface describes those generated REST endpoints so the AIMC
can map the native MQTT action to its operation-delegation REST counterpart.

Named-field style: containers hold their child elements as DIRECT named
fields (field name == id_short) — no ``value``/``submodel_element`` wrapper.
Dynamic name-keyed maps (REST actions keyed by action name) stay
``Dict[str, Item]`` fields directly on the container.
"""

from __future__ import annotations

from typing import Dict, Optional

from aas_pydantic import (
    SubmodelElementCollection, Property,
)

from aas_pydantic.submodel_templates.asset_interfaces_description import (
    actions as _BaseActions,
    properties as _BaseProperties,
    InteractionMetadata as _BaseInteractionMetadata,
    InterfaceTemplateForHTTP as _BaseHttpInterface,
    property_name_json_schema as _BaseDataSchema,
    Title, Base, ContentType, EndpointMetadata, Href,
    HtvMethodName,
    security_t, securityDefinitions,
    EndpointMetadata_t,
)

from aas_model.constants import (
    AID_REST_FORM, AID_REST_HTTP_METHOD, AID_REST_OPERATION, AID_REST_PROPERTY,
    AID_SYNCHRONOUS, AID_ACTION_INPUT, AID_ACTION_OUTPUT,
)


class RestActionInput(_BaseDataSchema):
    """WoT ``input`` DataSchema of a REST action (td#hasInput) — the command's
    JSON Schema structure (same as the native MQTT action)."""
    semantic_id: str = AID_ACTION_INPUT
    description: str = "Data schema describing the input of the action."


class RestActionOutput(_BaseDataSchema):
    """WoT ``output`` DataSchema of a REST action (td#hasOutput) — the
    response's JSON Schema structure (same as the native MQTT action)."""
    semantic_id: str = AID_ACTION_OUTPUT
    description: str = "Data schema describing the output of the action."


# ═══════════════════════════════════════════════════════════════════════════════
# Delta — REST-specific form fields
# ═══════════════════════════════════════════════════════════════════════════════

class RestForm(SubmodelElementCollection):
    """REST operation-delegation form (HTTP POST to the delegation endpoint).

    ``href`` is relative to the interface's ``endpoint_metadata.base`` (the
    operation-delegation service base URL); ``htv_method_name`` carries the
    HTTP method (POST).
    """
    semantic_id: str = AID_REST_FORM

    href: Href = Href()
    security: security_t = security_t()
    op: Property = Property(
        semantic_id="https://www.w3.org/2019/wot/td#hasOperationType")
    contentType: ContentType = ContentType()
    htv_methodName: HtvMethodName = HtvMethodName(
        semantic_id=AID_REST_HTTP_METHOD)


# ═══════════════════════════════════════════════════════════════════════════════
# Delta — REST action (same WoT input/output DataSchemas as the MQTT action)
# ═══════════════════════════════════════════════════════════════════════════════

# ``actions`` carries no children in the generated template, so the REST
# action is built on the WoT PropertyDefinition (like MqttAction) plus the
# REST form.
from aas_pydantic.submodel_templates.asset_interfaces_description import (
    property_name as _BaseProperty,
)


class RestAction(_BaseProperty):
    """Standard WoT PropertyDefinition + input/output DataSchemas + REST form.

    Describes one generated operation-delegation endpoint: BaSyx forwards an
    AAS Operation invocation here (POST), and the endpoint returns the
    operation result.  ``synchronous`` mirrors the native action's flag.
    """
    semantic_id: str = AID_REST_OPERATION
    description: str = "Generated REST operation-delegation endpoint for a skill."

    synchronous: Property = Property(semantic_id=AID_SYNCHRONOUS)
    input: Optional[RestActionInput] = None
    output: Optional[RestActionOutput] = None
    forms: RestForm = RestForm()


class RestActions(_BaseActions):
    """Dynamic map of REST actions (name → RestAction)."""
    property_name: Dict[str, RestAction] = {}


class RestProperty(_BaseProperty):
    """Standard WoT PropertyDefinition + REST write-delegation form.

    Describes one generated REST write-delegation endpoint: writing the AAS
    property is forwarded here (PUT) so the DMP can push it to the asset.
    """
    semantic_id: str = AID_REST_PROPERTY
    description: str = "Generated REST write-delegation endpoint for a property."

    forms: RestForm = RestForm()


class RestProperties(_BaseProperties):
    """Dynamic map of REST properties (name → RestProperty)."""
    property_name: Dict[str, RestProperty] = {}


class RestInteractionMetadata(_BaseInteractionMetadata):
    """Interaction metadata with REST-specialised actions and properties."""
    actions: RestActions = RestActions()
    properties: RestProperties = RestProperties()


class RestInterface(_BaseHttpInterface):
    """REST interface with extended interaction metadata."""
    title: Title = Title()
    EndpointMetadata: EndpointMetadata_t = EndpointMetadata(
        base=Base(),
        contentType=ContentType(),
        security=security_t(),
        securityDefinitions=securityDefinitions(),
    )
    InteractionMetadata: RestInteractionMetadata = RestInteractionMetadata()
