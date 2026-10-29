"""Cytiva capping station instance."""

from aas_pydantic import Property
from aas_model.constants import BASE_URL, BROKER, SITE
from aas_pydantic.submodel_templates.nameplate import ManufacturerName, ManufacturerProductDesignation
from aas_model.resource_template import ResourceNameplate
from aas_pydantic.submodel_templates.hierarchical_structures import EntryNode, Node
from aas_model.resource_template.operational import (
    OperationalMqttControlComponent, OperationalMqttInterfaces, OperationalMqttMappings, OperationalVariables,
)
from aas_model.resource_template.resources import CappingStation
from aas_model.constants import SCHEMA_BASE
from aas_model.json_schema_aid import datapoint_from_schema, load_schema
from aas_model.resource_template.references import (
    MQTT_INTERFACE, action_member_ref, affordance_ref, capability_ref, operation_variable_ref, skill_ref,
)
from aas_model.submodel_templates.control_component_instance import (
    ExtendedSkill, SkillOperation, SkillInterfaceRelationship, OptionalVariable,
)
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import SourcesItem, SinksItem
from aas_model.submodel_templates import AimcMappingConfiguration, DmpResponseSink, DmpResponseSource
from aas_pydantic.submodel_templates.capability_description import CapabilityRealizedBy, CapabilityRelations
from aas_model.submodel_templates.aid import DmpActionInput, DmpActionOutput, MqttAction, MqttActionForm
from aas_model.submodel_templates.hierarchical_structures import ResourceHierarchicalStructures


def cytiva_capping() -> CappingStation:
    identity = "cytivaCappingSystemAAS"
    parent = "aauFillingLineAAS"
    resource_id = f"{BASE_URL}/aas/{identity}"
    resource = CappingStation(
        id_short=identity,
        id=resource_id,
        nameplate=ResourceNameplate(
            URIOfTheProduct=resource_id,
            ManufacturerName=ManufacturerName(value={"en": "Cytiva"}),
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "Cytiva Capping System"}),
            ManufacturerProductType="Cytiva Capping System",
            # The legacy serial duplicates the Syntegon asset and is unreliable.
            OrderCodeOfManufacturer="",
            YearOfConstruction="2024",
            CountryOfOrigin="DK",
        ),
        hierarchical_structures=ResourceHierarchicalStructures(
            ArcheType="OneUp",
            EntryNode=EntryNode(
                global_asset_id=resource_id, Node={parent: Node(global_asset_id=f"{BASE_URL}/aas/{parent}")}
            ),
        ),
        asset_interfaces_description=OperationalMqttInterfaces(id_short="AssetInterfacesDescription"),
        control_component_instance=OperationalMqttControlComponent(id_short="ControlComponentInstance"),
        asset_interfaces_mapping_configuration=OperationalMqttMappings(
            id_short="AssetInterfacesMappingConfiguration",
        ),
        variables=OperationalVariables(),
    )
    mqtt = resource.asset_interfaces_description.InterfaceTemplateForMQTT["interface_mqtt"]
    mqtt.title.value = "Cytiva Capping System"
    mqtt.EndpointMetadata.base.value = f"{BROKER}/{SITE}/Capping/"
    resource.parameters.parameter["Location"].x.parameter.value = 240.0
    resource.parameters.parameter["Location"].y.parameter.value = 240.0
    name = "Capping"
    input_url = f"{SCHEMA_BASE}/command.schema.json"
    output_url = f"{SCHEMA_BASE}/commandResponse.schema.json"
    mqtt.InteractionMetadata.actions.property_name[name] = MqttAction(
        title=name,
        synchronous="true",
        input=datapoint_from_schema(load_schema(input_url), cls=DmpActionInput, schema_url=input_url),
        output=datapoint_from_schema(load_schema(output_url), cls=DmpActionOutput, schema_url=output_url),
        forms=MqttActionForm(href=f"CMD/{name}", mqv_qos="2", mqv_responseTopic=f"DATA/{name}"),
    )
    cci = resource.control_component_instance
    skill = ExtendedSkill(interface_reference=affordance_ref(MQTT_INTERFACE, "actions", name),
        operation=SkillOperation(
            in_output_variable=[Property(id_short="Uuid", description="The UUID of the command")],
            output_variable=[
                Property(id_short="State", description="The state of the command being executed"),
                Property(id_short="Outcome", value="0", value_type="xs:integer", qualifiers=[OptionalVariable()]),
            ],
        ),
    )
    cci.Skills.Skill[name] = skill
    cci.Endpoints.Endpoint[name] = SkillInterfaceRelationship(
        first=skill_ref(name), second=affordance_ref(MQTT_INTERFACE, "actions", name)
    )
    resource.asset_interfaces_mapping_configuration.MappingConfigurations.value.append(
        AimcMappingConfiguration(
            id_short=name, DefaultPollingInterval="0.0",
            Sources=[SourcesItem(SourceId="Uuid", Source=operation_variable_ref(name, "Uuid"))],
            Sinks=[SinksItem(Sink=action_member_ref(MQTT_INTERFACE, name, "input"), SinkId=name)],
            Transformation=(
                f"function aimc_main(sources) return {{ {name} = {{ Uuid = sources.Uuid }} }} end"
            ),
            ResponseSources=[
                DmpResponseSource(SourceId="Reply", Source=action_member_ref(MQTT_INTERFACE, name, "output")),
            ],
            ResponseTransformation=(
                "function aimc_main(sources) local reply = sources.Reply "
                "return { Uuid = reply.Uuid, State = reply.State, Outcome = reply.Outcome } end"
            ),
            ResponseSinks=[DmpResponseSink(SinkId=member, Sink=operation_variable_ref(name, member))
                           for member in ("Uuid", "State", "Outcome")],
        ),
    )
    container = resource.capability_description.CapabilitySet["Processing"].CapabilityContainer[name]
    container.CapabilityRelations = CapabilityRelations(
        CapabilityRealizedBy={
            f"RealizedBy_{name}": CapabilityRealizedBy(first=capability_ref("Processing", name), second=skill_ref(name))
        }
    )
    return resource
