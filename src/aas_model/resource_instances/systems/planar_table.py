"""Planar table instance."""

from aas_model.constants import BASE_URL, BROKER, CSSX, SITE
from aas_pydantic.submodel_templates.hierarchical_structures import EntryNode, Node
from aas_pydantic.submodel_templates.nameplate import ManufacturerName, ManufacturerProductDesignation
from aas_model.resource_template import ResourceNameplate
from aas_model.resource_template.operational import COMMAND_SCHEMA, COMMAND_SCHEMA_URL, MqttInterfaces
from aas_model.resource_template.resources import CompositeResource
from aas_model.resource_template.references import (
    MQTT_INTERFACE, action_member_ref, affordance_ref, operation_variable_ref, skill_ref,
)
from aas_model.submodel_templates.control_component_instance import (
    ExtendedSkill, SkillOperation, SkillInterfaceRelationship,
)
from aas_model.submodel_templates.aimc import DmpMappingConfiguration
from aas_pydantic import Property
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import (
    Sink as SinkReference, SourcesItem, SinksItem,
)
from aas_model.submodel_templates.aid import DmpActionInput, MqttAction, MqttActionForm
from aas_model.json_schema_aid import datapoint_from_schema
from aas_model.submodel_templates.hierarchical_structures import ResourceHierarchicalStructures


def planar_table() -> CompositeResource:
    identity = "planarTableAAS"
    serial = "PM-S1-2024-001"
    resource_id = f"{BASE_URL}/aas/{identity}"
    children = (
        "planarTableShuttle1AAS", "planarTableShuttle2AAS", "planarTableShuttle3AAS",
    )
    table = CompositeResource(
        id_short=identity,
        id=resource_id,
        asset_type=f"{CSSX}#PlanarTable",
        specific_asset_ids={"serialNumber": serial},
        nameplate=ResourceNameplate(
            URIOfTheProduct=resource_id,
            ManufacturerName=ManufacturerName(value={"en": "Planar Motors"}),
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "Planar Motors Table"}),
            ManufacturerProductType="Planar Motors Table",
            OrderCodeOfManufacturer=serial,
            SerialNumber=serial,
            YearOfConstruction="2024",
            CountryOfOrigin="DK",
        ),
        hierarchical_structures=ResourceHierarchicalStructures(
            ArcheType="OneDown",
            EntryNode=EntryNode(
                global_asset_id=resource_id,
                Node={child: Node(global_asset_id=f"{BASE_URL}/aas/{child}") for child in children},
            ),
        ),
        asset_interfaces_description=MqttInterfaces(id_short="AssetInterfacesDescription"),
    )
    mqtt = table.asset_interfaces_description.InterfaceTemplateForMQTT["interface_mqtt"]
    mqtt.title.value = "Planar Motors Table"
    mqtt.EndpointMetadata.base.value = f"{BROKER}/{SITE}/Planar/"
    # Halting the entire table is distinct from halting an individual shuttle.
    # Like every Halt it only invokes: CMD/Halt is not answered.
    name = "Halt"
    table.asset_interfaces_description.InterfaceTemplateForMQTT[
        "interface_mqtt"
    ].InteractionMetadata.actions.property_name[name] = MqttAction(
        title=name,
        synchronous="true",
        input=datapoint_from_schema(COMMAND_SCHEMA, cls=DmpActionInput, schema_url=COMMAND_SCHEMA_URL),
        forms=MqttActionForm(href=f"CMD/{name}", mqv_qos="2"),
    )
    skill = ExtendedSkill(
        Disabled="false", interface_reference=affordance_ref(MQTT_INTERFACE, "actions", name)
    )
    skill.operation = SkillOperation(input_variable=[Property(id_short="Uuid", description="The UUID of the command")])
    table.control_component_instance.Skills.Skill[name] = skill
    table.control_component_instance.Endpoints.Endpoint[name] = SkillInterfaceRelationship(
        first=skill_ref(name),
        second=affordance_ref(MQTT_INTERFACE, "actions", name),
    )
    table.asset_interfaces_mapping_configuration.MappingConfigurations.value.append(
        DmpMappingConfiguration(
            id_short=name,
            DefaultPollingInterval="0.0",
            Transformation=f"function aimc_main(sources) return {{ {name} = {{ Uuid = sources.Uuid }} }} end",
            Sources=[SourcesItem(SourceId="Uuid", Source=operation_variable_ref(name, "Uuid"))],
            Sinks=[SinksItem(Sink=SinkReference(value=action_member_ref(MQTT_INTERFACE, name, "input")), SinkId=name)],
        ),
    )
    return table
