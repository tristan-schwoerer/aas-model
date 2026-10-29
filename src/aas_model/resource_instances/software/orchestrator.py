"""AAU orchestrator instance, including its native HTTP API."""

from aas_pydantic import Capability, Property
from aas_pydantic.submodel_templates.asset_interfaces_description import (
    Base, ContentType, EndpointMetadata, Href, HtvMethodName, Key as AIDKey, Title, Title as AIDTitle,
    securityDefinitions, security_t,
)
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import (
    Source as SourceReference, Sink as SinkReference, SourcesItem, SinksItem,
)
from aas_pydantic.submodel_templates.capability_description import (
    CapabilityContainer, CapabilitySet, CapabilityRelations, CapabilityRealizedBy,
)

from aas_model.json_schema_aid import datapoint_from_schema, load_schema, populate_datapoint
from aas_model.constants import BASE_URL, BROKER, CSSX, SCHEMA_BASE, SITE
from aas_pydantic.submodel_templates.nameplate import ManufacturerName, ManufacturerProductDesignation
from aas_model.resource_template import ResourceNameplate
from aas_model.resource_template.resources import MqttSoftwareResource
from aas_model.resource_template.operational import COMMAND_RESPONSE_SCHEMA, COMMAND_RESPONSE_SCHEMA_URL, station_state
from aas_model.resource_template.references import (
    MQTT_INTERFACE, action_member_ref, affordance_ref, capability_ref, operation_variable_ref, series_segment_ref,
    skill_ref,
)
from aas_model.submodel_templates.control_component_instance import (
    ExtendedSkill, SkillOperation, SkillInterfaceRelationship,
)
from aas_model.submodel_templates import DmpResponseSink, DmpResponseSource
from aas_model.submodel_templates.aimc import DmpMappingConfiguration
from aas_model.submodel_templates.aid import (
    DmpAction, DmpActionInput, DmpActionOutput, DmpActions, DmpHttpInterface, HttpActionForm, HttpForm, MqttAction,
    MqttActionForm, MqttForm,
)
try:
    from aas_model.submodel_templates.aid import DmpProperties, DmpProperty, ReadOnly, Synchronous
except ImportError:
    # The committed AID template does not yet include generic property extensions.
    from aas_pydantic.submodel_templates.asset_interfaces_description import (
        properties as DmpProperties, property_name as DmpProperty,
    )
    ReadOnly = None
    Synchronous = Property


def orchestrator() -> MqttSoftwareResource:
    identity = "orchestratorAAS"
    serial = "AAU-BT-2024-001"
    resource = MqttSoftwareResource(
        id_short=identity, id=f"{BASE_URL}/aas/{identity}",
        asset_type=f"{CSSX}#Orchestrator", specific_asset_ids={"serialNumber": serial},
        nameplate=ResourceNameplate(
            URIOfTheProduct=f"{BASE_URL}/aas/{identity}",
            ManufacturerName=ManufacturerName(value={"en": "Aalborg University"}),
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "AAU Orchestrator"}),
            ManufacturerProductType="AAU Orchestrator",
            OrderCodeOfManufacturer=serial,
            SerialNumber=serial, YearOfConstruction="2024",
            CountryOfOrigin="DK",
        ),
    )
    aid = resource.asset_interfaces_description
    mqtt = aid.InterfaceTemplateForMQTT["interface_mqtt"]
    mqtt.title.value = "AAU Orchestrator"
    mqtt.EndpointMetadata.base.value = f"{BROKER}/{SITE}/Orchestrator/"
    interaction = aid.InterfaceTemplateForMQTT["interface_mqtt"].InteractionMetadata
    cci = resource.control_component_instance
    mappings = resource.asset_interfaces_mapping_configuration.MappingConfigurations.value
    for name in ("Start", "Stop", "Suspend", "Unsuspend", "Reset"):
        input_url = f"{SCHEMA_BASE}/orchestrationCommand.schema.json" if name in (
            "Start", "Unsuspend",
        ) else f"{SCHEMA_BASE}/command.schema.json"
        action = MqttAction(
            title=name,
            synchronous="true",
            input=datapoint_from_schema(load_schema(input_url), cls=DmpActionInput, schema_url=input_url),
            output=datapoint_from_schema(
                COMMAND_RESPONSE_SCHEMA, cls=DmpActionOutput, schema_url=COMMAND_RESPONSE_SCHEMA_URL
            ),
            forms=MqttActionForm(href=f"CMD/{name}", mqv_qos="2", mqv_responseTopic=f"DATA/{name}"),
        )
        interaction.actions.property_name[name] = action
        skill = ExtendedSkill(
            Disabled="false", interface_reference=affordance_ref(MQTT_INTERFACE, "actions", name)
        )
        skill.operation = SkillOperation(
            in_output_variable=[Property(id_short="Uuid", description="The UUID of the command")],
            output_variable=[Property(id_short="State", description="The state of the command being executed")],
        )
        mapping = DmpMappingConfiguration(
            id_short=name, DefaultPollingInterval="0.0",
            Transformation=f"function aimc_main(sources) return {{ {name} = {{ Uuid = sources.Uuid }} }} end",
            Sources=[SourcesItem(SourceId=variable, Source=operation_variable_ref(name, variable))
                     for variable in (("Uuid", "Process") if name in ("Start", "Unsuspend") else ("Uuid",))],
            Sinks=[SinksItem(Sink=SinkReference(value=action_member_ref(MQTT_INTERFACE, name, "input")), SinkId=name)],
            ResponseSources=[
                DmpResponseSource(SourceId="Reply", Source=action_member_ref(MQTT_INTERFACE, name, "output")),
            ],
            ResponseTransformation=(
                "function aimc_main(sources) local reply = sources.Reply "
                "return { Uuid = reply.Uuid, State = reply.State } end"
            ),
            ResponseSinks=[DmpResponseSink(SinkId=member, Sink=operation_variable_ref(name, member))
                           for member in ("Uuid", "State")],
        )
        if name in ("Start", "Unsuspend"):
            skill.operation.input_variable = [Property(id_short="Process")]
            mapping.Transformation.value = (
                f"function aimc_main(sources) "
                f"return {{ {name} = {{ Uuid = sources.Uuid, Process = sources.Process }} }} end"
            ).encode("utf-8")
        cci.Skills.Skill[name] = skill
        cci.Endpoints.Endpoint[name] = SkillInterfaceRelationship(
            first=skill_ref(name),
            second=affordance_ref(MQTT_INTERFACE, "actions", name),
        )
        mappings.append(mapping)
    resource.capability_description.CapabilitySet = {
        "Coordination": CapabilitySet(
            id_short="Coordination",
            CapabilityContainer={
                "Orchestrate": CapabilityContainer(
                    id_short="Orchestrate",
                    Capability=Capability(id_short="Capability", semantic_id=f"{CSSX}#Orchestrate"),
                    CapabilityRelations=CapabilityRelations(
                        CapabilityRealizedBy={
                            "RealizedBy_Start": CapabilityRealizedBy(
                                first=capability_ref("Coordination", "Orchestrate"),
                                second=skill_ref("Start"),
                            ),
                        }
                    ),
                )
            },
        )
    }

    state_url = f"{SCHEMA_BASE}/state.schema.json"
    resource.variables.State = station_state(occupation=False)
    state = datapoint_from_schema(
        load_schema(state_url),
        key="State",
        schema_url=state_url,
        title=Title(value="State"),
        observable="true",
        readOnly="true",
        forms=MqttForm(href="DATA/State", mqv_retain="true", mqv_qos="0"),
    )
    interaction.properties.property_name["State"] = state
    # Software doesn't have station ProcessQueue; declare only actual telemetry.
    mappings.append(
        DmpMappingConfiguration(
            id_short="StationState",
            DefaultPollingInterval="0.0",
            Transformation="function aimc_main(sources) return { Live = { PackMLState = sources.State.State } } end",
            Sources=[
                SourcesItem(
                    Source=SourceReference(value=affordance_ref(MQTT_INTERFACE, "properties", "State")),
                    SourceId="State",
                )
            ],
            Sinks=[SinksItem(Sink=SinkReference(value=series_segment_ref("State", "Station")), SinkId="Live")],
        )
    )

    http = DmpHttpInterface(
        id_short="interface_http",
        title=AIDTitle(value="Orchestrator REST API"),
        EndpointMetadata=EndpointMetadata(
            base=Base(value="http://orchestrator:8090"),
            contentType=ContentType(value="application/json"),
            security=security_t(), securityDefinitions=securityDefinitions(),
        ),
    )
    http.InteractionMetadata.actions = DmpActions(id_short="actions")
    http.InteractionMetadata.properties = DmpProperties(id_short="properties")
    for name in ("Start", "Stop", "Reset"):
        action = DmpAction(
            id_short=name,
            title=AIDTitle(id_short="title", value=name),
            synchronous=Synchronous(id_short="synchronous", value="true"),
            forms=HttpActionForm(href=f"/operations/{name}", htv_methodName="POST"),
        )
        input_schema = "orchestrationCommand" if name == "Start" else "command"
        input_url = f"{SCHEMA_BASE}/{input_schema}.schema.json"
        output_url = f"{SCHEMA_BASE}/commandResponse.schema.json"
        action.input = datapoint_from_schema(load_schema(input_url), cls=DmpActionInput, schema_url=input_url)
        action.input.id_short = "input"
        action.output = datapoint_from_schema(load_schema(output_url), cls=DmpActionOutput, schema_url=output_url)
        action.output.id_short = "output"
        http.InteractionMetadata.actions.property_name[name] = action
    health = DmpProperty(id_short="Health", **({"readOnly": ReadOnly(value="true")} if ReadOnly else {}), forms=HttpForm(
        href=Href(value="/health"), htv_methodName=HtvMethodName(value="GET"),
    ))
    health.key = AIDKey(id_short="key", value="Health")
    health.title = AIDTitle(id_short="title", value="Health")
    state_url = f"{SCHEMA_BASE}/state.schema.json"
    populate_datapoint(health, load_schema(state_url), schema_url=state_url)
    http.InteractionMetadata.properties.property_name["Health"] = health
    aid.InterfaceTemplateForHTTP["interface_http"] = http
    return resource
