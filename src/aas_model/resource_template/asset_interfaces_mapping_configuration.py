"""AIMC partial — mandatory Resource live-data mappings (Variables + Skills).

Maps the Resource's mandatory variables AND skills via IDTA AIMC 2.0
MappingConfigurations:

- **Variables** — ``PackMLState``/``OccupationState`` read from the AID
  ``StationState`` property (``/DATA/State``); the Lua ``transformation``
  picks the JSON field of the payload each variable maps to:

      sources.StationState.State         → PackMLState
      sources.StationState.ProcessQueue  → OccupationState

- **Skills** — each skill is a BIDIRECTIONAL mapping expressed as TWO plain
  (directional) IDTA MappingConfigurations, one per direction:

  - the *request* mapping (``<name>Request``) maps the REST
    operation-delegation action (``interface_rest``) → native MQTT action
    (``interface_mqtt``);
  - the *response* mapping (``<name>``) maps the native MQTT action back to
    the REST operation-delegation action.

  Each direction carries its own Lua transformation blob.  The management
  node identifies the two directions from the Source/Sink references
  (REST→MQTT = request, MQTT→REST = response) and pairs them per skill.

All references use the ``{aas_id}`` / ``{aas_id_short}`` macros (resolved by
id_injector), so the AIMC always points at this AAS's own submodels.

Named-field style: children are DIRECT named fields on the container (no
``value``/``submodel_element`` wrapper).
"""

from __future__ import annotations

from aas_pydantic import (
    Key, ModelReference, ReferenceElement,
)
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import (
    Source, Sink, Sources, Sinks,
    Source_source, Sink_sink,
    SourceId, SinkId,
    DefaultPollingInterval,
)

from aas_model.submodel_templates.aimc import (
    Aimc, AimcMappingConfiguration, AimcMappingConfigurations,
    Transformation,
)
from ._helpers import DEFAULT_SKILLS

# ── Reference paths (self-referential — {aas_id} resolved by id_injector) ──
AID_REF = "{aas_id}/submodels/AssetInterfacesDescription"
VARIABLES_REF = "{aas_id}/submodels/Variables"

AID_PROPERTY_PATH = (
    Key(type_="Submodel", value=AID_REF),
    Key(type_="SubmodelElementCollection", value="interface_mqtt"),
    Key(type_="SubmodelElementCollection", value="InteractionMetadata"),
    Key(type_="SubmodelElementCollection", value="properties"),
)

AID_MQTT_ACTION_PATH = (
    Key(type_="Submodel", value=AID_REF),
    Key(type_="SubmodelElementCollection", value="interface_mqtt"),
    Key(type_="SubmodelElementCollection", value="InteractionMetadata"),
    Key(type_="SubmodelElementCollection", value="actions"),
)

AID_REST_ACTION_PATH = (
    Key(type_="Submodel", value=AID_REF),
    Key(type_="SubmodelElementCollection", value="interface_rest"),
    Key(type_="SubmodelElementCollection", value="InteractionMetadata"),
    Key(type_="SubmodelElementCollection", value="actions"),
)

AID_REST_PROPERTY_PATH = (
    Key(type_="Submodel", value=AID_REF),
    Key(type_="SubmodelElementCollection", value="interface_rest"),
    Key(type_="SubmodelElementCollection", value="InteractionMetadata"),
    Key(type_="SubmodelElementCollection", value="properties"),
)

VARIABLE_PATH = (
    Key(type_="Submodel", value=VARIABLES_REF),
)


def _property_ref(property_name: str) -> ModelReference:
    """Reference to an AID property (source) — e.g. .../properties/StationState."""
    return ModelReference(key=AID_PROPERTY_PATH + (Key(type_="SubmodelElementCollection", value=property_name),))


def _variable_ref(variable_name: str) -> ModelReference:
    """Reference to a Variables submodel element (sink) — e.g. .../Variables/PackMLState."""
    return ModelReference(key=VARIABLE_PATH + (Key(type_="SubmodelElementCollection", value=variable_name),))


def _mqtt_action_ref(name: str) -> ModelReference:
    """Reference to a skill's native MQTT action (interface_mqtt)."""
    return ModelReference(key=AID_MQTT_ACTION_PATH + (Key(type_="SubmodelElementCollection", value=name),))


def _rest_action_ref(name: str) -> ModelReference:
    """Reference to a skill's REST operation-delegation action (interface_rest)."""
    return ModelReference(key=AID_REST_ACTION_PATH + (Key(type_="SubmodelElementCollection", value=name),))


def _rest_property_ref(name: str) -> ModelReference:
    """Reference to a property's REST write-delegation endpoint (interface_rest)."""
    return ModelReference(key=AID_REST_PROPERTY_PATH + (Key(type_="SubmodelElementCollection", value=name),))


def source(name: str, ref: ModelReference) -> Source:
    """A single AID source: the affordance reference + a stable source id."""
    return Source(
        id_short=name,
        Source=Source_source(value=ref),
        SourceId=SourceId(value=name),
    )


def sink(name: str, ref: ModelReference) -> Sink:
    """A single sink: the submodel element reference + a stable sink id."""
    return Sink(
        id_short=name,
        Sink=Sink_sink(value=ref),
        SinkId=SinkId(value=name),
    )


def mapping_configuration(
    *,
    id_short: str,
    sources: list[Source],
    sinks: list[Sink],
    transformation: str,
) -> AimcMappingConfiguration:
    """One MappingConfiguration: AID sources, AAS sinks and the Lua mapping."""
    return AimcMappingConfiguration(
        id_short=id_short,
        DefaultPollingInterval=DefaultPollingInterval(value="0.0"),
        Transformation=Transformation(value=transformation),
        Sources=Sources(value=sources),
        Sinks=Sinks(value=sinks),
    )


_DEFAULT_TRANSFORMATION = """\
function aimc_main(sources)
    return {
        PackMLState     = sources.StationState.State,
        OccupationState = sources.StationState.ProcessQueue,
    }
end
"""


def _skill_response_transformation(name: str) -> str:
    """Lua for the ResponseMapping direction: native MQTT response payload
    (/DATA/<name>) -> REST operation-delegation response.

    Both payloads carry the command / commandResponse fields, so the mapping
    is a field passthrough; the request direction is a separate blob (see
    ``_skill_request_transformation``).
    """
    return f"""\
-- Skill '{name}' ResponseMapping: native MQTT response -> REST operation-delegation.
-- aimc_main rebuilds the OperationVariables from the native MQTT response
-- payload (/DATA/{name}):
function aimc_main(sources)
    local mqtt = sources.{name}
    return {{
        {name} = {{
            Uuid    = mqtt.Uuid,
            State   = mqtt.State,
            Outcome = mqtt.Outcome,
        }},
    }}
end
"""


def _skill_request_transformation(name: str) -> str:
    """Lua for the RequestMapping direction: REST operation-delegation call ->
    native MQTT command message (/CMD/<name>).

    The DMP receives the AAS OperationVariables (``rest.<name>``, an array of
    ``{{ value: {{ modelType, idShort, valueType, value }} }}`` objects) and
    packs them into the native command message carrying the correlation Uuid.
    """
    return f"""\
-- Skill '{name}' RequestMapping: REST operation-delegation -> native MQTT.
-- The DMP packs the AAS OperationVariables (rest.<name>) into the native
-- command message sent to /CMD/{name}, keeping the correlation Uuid:
function aimc_main(sources)
    local rest = sources.{name}
    return {{
        {name} = {{
            Uuid = rest.Uuid,
        }},
    }}
end
"""


def variables_mapping_configuration() -> AimcMappingConfiguration:
    """The mandatory Variables mapping: StationState property → PackMLState /
    OccupationState."""
    return mapping_configuration(
        id_short="MQTT",
        sources=[
            source("StationState", _property_ref("StationState")),
        ],
        sinks=[
            sink("PackMLState", _variable_ref("PackMLState")),
            sink("OccupationState", _variable_ref("OccupationState")),
        ],
        transformation=_DEFAULT_TRANSFORMATION,
    )


def skill_mapping_configuration(name: str) -> AimcMappingConfiguration:
    """One skill's RESPONSE direction MappingConfiguration: native MQTT action
    → REST operation-delegation action, with the response-direction Lua blob.

    A skill's operation delegation is bidirectional and expressed as TWO plain
    (directional) IDTA MappingConfigurations: this response mapping plus the
    request mapping from ``skill_request_mapping_configuration``.  The
    management node pairs them via the Source/Sink references."""
    return mapping_configuration(
        id_short=name,
        sources=[
            source(name, _mqtt_action_ref(name)),
        ],
        sinks=[
            sink(name, _rest_action_ref(name)),
        ],
        transformation=_skill_response_transformation(name),
    )


def skill_request_mapping_configuration(name: str) -> AimcMappingConfiguration:
    """One skill's REQUEST direction MappingConfiguration: REST
    operation-delegation action → native MQTT action, with the
    request-direction Lua blob.

    Pairs with ``skill_mapping_configuration`` (the response direction) to
    form the skill's bidirectional operation-delegation mapping."""
    return mapping_configuration(
        id_short=f"{name}Request",
        sources=[
            source(name, _rest_action_ref(name)),
        ],
        sinks=[
            sink(name, _mqtt_action_ref(name)),
        ],
        transformation=_skill_request_transformation(name),
    )


def _property_write_transformation(name: str) -> str:
    """Lua converting between a property's REST write-delegation endpoint and
    its native MQTT action (write: REST → MQTT; acknowledgement: MQTT → REST)."""
    return f"""\
-- Property '{name}': REST write-delegation endpoint <-> native MQTT action.
-- Write (REST -> MQTT): the DMP packs the written value into the native
--   command message, e.g.:
--     command = {{ Uuid = <correlation>, {name} = rest.{name} }}
-- Ack   (MQTT -> REST): aimc_main maps the MQTT response/ack to the REST
--   write response:
function aimc_main(sources)
    local mqtt = sources.{name}
    return {{
        {name} = {{
            Value   = mqtt.{name},
            State   = mqtt.State,
        }},
    }}
end
"""


def property_mapping_configuration(name: str) -> AimcMappingConfiguration:
    """One property-write MappingConfiguration: native MQTT action → REST
    write-delegation property, with the write↔ack Lua transformation."""
    return mapping_configuration(
        id_short=name,
        sources=[
            source(name, _mqtt_action_ref(name)),
        ],
        sinks=[
            sink(name, _rest_property_ref(name)),
        ],
        transformation=_property_write_transformation(name),
    )


def asset_interfaces_mapping_configuration() -> Aimc:
    """AIMC submodel with the mandatory Resource mappings.

    The Variables mapping (PackMLState/OccupationState ← StationState) plus,
    per default skill, TWO plain IDTA MappingConfigurations — the request
    direction (``<name>Request``: REST operation-delegation → native MQTT
    action) and the response direction (``<name>``: native MQTT action →
    REST operation-delegation).  Resource configs add their own skill /
    property mappings to ``MappingConfigurations``.
    """
    mcs = [variables_mapping_configuration()]
    for name, _synchronous, _has_response in DEFAULT_SKILLS:
        mcs.append(skill_request_mapping_configuration(name))
        mcs.append(skill_mapping_configuration(name))
    return Aimc(
        id_short="AssetInterfacesMappingConfiguration",
        MappingConfigurations=AimcMappingConfigurations(value=mcs),
    )
