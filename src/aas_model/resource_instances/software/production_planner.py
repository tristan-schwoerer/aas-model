"""AAU production planner instance."""

from aas_model.constants import BASE_URL, BROKER, CSSX, SCHEMA_BASE, SITE
from aas_pydantic.submodel_templates.nameplate import ManufacturerName, ManufacturerProductDesignation
from aas_model.resource_template import ResourceNameplate
from aas_model.resource_template.resources import MqttSoftwareResource
from aas_model.resource_template.references import (
    MQTT_INTERFACE, action_member_ref, affordance_ref, capability_ref, operation_variable_ref, series_segment_ref,
    skill_ref,
)
from aas_model.submodel_templates.control_component_instance import (
    ExtendedSkill, SkillOperation, SkillInterfaceRelationship, OptionalVariable,
)
from aas_model.resource_template.operational import station_state
from aas_model.submodel_templates import DmpResponseSink, DmpResponseSource
from aas_model.submodel_templates.aimc import DmpMappingConfiguration
from aas_pydantic import Capability, Property
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import (
    Source as SourceReference, Sink as SinkReference, SourcesItem, SinksItem,
)
from aas_pydantic.submodel_templates.capability_description import (
    CapabilityContainer, CapabilitySet, CapabilityRelations, CapabilityRealizedBy,
)
from aas_model.json_schema_aid import datapoint_from_schema, load_schema, without
from aas_model.submodel_templates.aid import DmpActionInput, DmpActionOutput, MqttAction, MqttActionForm, MqttForm
from aas_pydantic.submodel_templates.asset_interfaces_description import Title


def production_planner() -> MqttSoftwareResource:
    identity = "productionPlannerAAS"
    serial = "AAU-PP-2024-001"
    resource = MqttSoftwareResource(
        id_short=identity, id=f"{BASE_URL}/aas/{identity}",
        asset_type=f"{CSSX}#ProductionPlanner", specific_asset_ids={"serialNumber": serial},
        nameplate=ResourceNameplate(
            URIOfTheProduct=f"{BASE_URL}/aas/{identity}",
            ManufacturerName=ManufacturerName(value={"en": "Aalborg University"}),
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "AAU Production Planner"}),
            ManufacturerProductType="AAU Production Planner",
            OrderCodeOfManufacturer=serial,
            SerialNumber=serial, YearOfConstruction="2024",
            CountryOfOrigin="DK",
        ),
    )
    input_url = f"{SCHEMA_BASE}/planningCommand.schema.json"
    output_url = f"{SCHEMA_BASE}/planningResponse.schema.json"
    mqtt = resource.asset_interfaces_description.InterfaceTemplateForMQTT["interface_mqtt"]
    mqtt.title.value = "AAU Production Planner"
    mqtt.EndpointMetadata.base.value = f"{BROKER}/{SITE}/ProductionPlanner/"
    action = MqttAction(
        title="Plan",
        synchronous="true",
        input=datapoint_from_schema(load_schema(input_url), cls=DmpActionInput, schema_url=input_url),
        output=datapoint_from_schema(
            without(load_schema(output_url), "additionalProperties"), cls=DmpActionOutput, schema_url=output_url
        ),
        forms=MqttActionForm(href="CMD/Plan", mqv_qos="2", mqv_responseTopic="DATA/Plan"),
    )
    mqtt.InteractionMetadata.actions.property_name["Plan"] = action
    # Unlike the orchestrator's State schema, the planner reports StationState.
    state_url = f"{SCHEMA_BASE}/stationState.schema.json"
    state = datapoint_from_schema(
        load_schema(state_url),
        key="StationState",
        schema_url=state_url,
        title=Title(value="StationState"),
        observable="true",
        readOnly="true",
        forms=MqttForm(href="DATA/State", mqv_retain="true", mqv_qos="0"),
    )
    mqtt.InteractionMetadata.properties.property_name["StationState"] = state
    resource.variables.State = station_state(occupation=False)
    plan = ExtendedSkill(
        Disabled="false", interface_reference=affordance_ref(MQTT_INTERFACE, "actions", "Plan")
    )
    plan.operation = SkillOperation(
        in_output_variable=[Property(id_short="Uuid", description="The UUID of the command")],
        output_variable=[Property(id_short="State", description="The state of the command being executed")],
    )
    plan.operation.input_variable = [
        Property(id_short="Assets", value="[]", description="JSON array of resource AAS identifiers."),
        Property(id_short="Order"),
    ]
    plan.operation.output_variable.extend([
        Property(id_short="ProcessAasId", qualifiers=[OptionalVariable()]),
        Property(id_short="ProductAasId", qualifiers=[OptionalVariable()]),
        Property(id_short="ErrorMessage", qualifiers=[OptionalVariable()]),
    ])
    cci = resource.control_component_instance
    cci.Skills.Skill["Plan"] = plan
    cci.Endpoints.Endpoint["Plan"] = SkillInterfaceRelationship(
        first=skill_ref("Plan"),
        second=affordance_ref(MQTT_INTERFACE, "actions", "Plan"),
    )
    mapping = DmpMappingConfiguration(
        id_short="Plan",
        DefaultPollingInterval="0.0",
        # AAS operation Properties are scalar; the native MQTT schema requires an array.
        Transformation="""function aimc_main(sources)
    return { Plan = { Uuid = sources.Uuid, Assets = json.decode(sources.Assets), Order = sources.Order } }
end
""",
        Sources=[
            SourcesItem(SourceId=name, Source=operation_variable_ref("Plan", name))
            for name in ("Uuid", "Assets", "Order")
        ],
        Sinks=[SinksItem(SinkId="Plan", Sink=action_member_ref(MQTT_INTERFACE, "Plan", "input"))],
        ResponseSources=[
            DmpResponseSource(SourceId="Reply", Source=action_member_ref(MQTT_INTERFACE, "Plan", "output")),
        ],
        ResponseTransformation=(
            "function aimc_main(sources) local reply = sources.Reply "
            "return { Uuid = reply.Uuid, State = reply.State, ProcessAasId = reply.ProcessAasId, "
            "ProductAasId = reply.ProductAasId, ErrorMessage = reply.ErrorMessage } end"
        ),
        ResponseSinks=[DmpResponseSink(SinkId=member, Sink=operation_variable_ref("Plan", member))
                       for member in ("Uuid", "State", "ProcessAasId", "ProductAasId", "ErrorMessage")],
    )
    resource.asset_interfaces_mapping_configuration.MappingConfigurations.value.append(mapping)
    resource.asset_interfaces_mapping_configuration.MappingConfigurations.value.append(
        DmpMappingConfiguration(
            id_short="StationState",
            DefaultPollingInterval="0.0",
            Transformation=(
                "function aimc_main(sources) return { Live = { PackMLState = sources.StationState.State } } end"
            ),
            Sources=[
                SourcesItem(
                    Source=SourceReference(value=affordance_ref(MQTT_INTERFACE, "properties", "StationState")),
                    SourceId="StationState",
                )
            ],
            Sinks=[SinksItem(Sink=SinkReference(value=series_segment_ref("State", "Station")), SinkId="Live")],
        )
    )
    resource.capability_description.CapabilitySet = {
        "Planning": CapabilitySet(
            id_short="Planning",
            CapabilityContainer={
                "Plan": CapabilityContainer(
                    id_short="Plan",
                    Capability=Capability(id_short="Capability", semantic_id=f"{CSSX}#Plan"),
                    CapabilityRelations=CapabilityRelations(
                        CapabilityRealizedBy={
                            "RealizedBy_Plan": CapabilityRealizedBy(
                                first=capability_ref("Planning", "Plan"),
                                second=skill_ref("Plan"),
                            )
                        }
                    ),
                )
            },
        )
    }
    return resource
