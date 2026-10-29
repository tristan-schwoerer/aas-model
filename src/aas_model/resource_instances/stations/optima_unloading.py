"""Optima unloading station instance."""

from aas_pydantic import Property
from aas_model.constants import BASE_URL, BROKER, SITE
from aas_model.resource_instances.site import SITE_ADDRESS
from aas_pydantic.submodel_templates.nameplate import Nameplate, ManufacturerName, ManufacturerProductDesignation
from aas_pydantic.submodel_templates.hierarchical_structures import EntryNode, Node
from aas_model.resource_template.operational import (
    OperationalMqttControlComponent, OperationalMqttInterfaces, OperationalMqttMappings, OperationalVariables,
)
from aas_model.resource_template.resources import UnloadingStation
from aas_model.constants import SCHEMA_BASE
from aas_model.json_schema_aid import datapoint_from_schema, load_schema
from aas_model.submodel_templates import AimcMappingConfiguration, DmpResponseSink, DmpResponseSource
from aas_model.resource_template.references import (
    MQTT_INTERFACE, action_member_ref, affordance_ref, capability_ref, operation_variable_ref, skill_ref,
)
from aas_model.submodel_templates.control_component_instance import (
    ExtendedSkill, SkillOperation, SkillInterfaceRelationship, OptionalVariable,
)
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import SourcesItem, SinksItem
from aas_pydantic.submodel_templates.capability_description import CapabilityRelations, CapabilityRealizedBy
from aas_model.submodel_templates.aid import DmpActionInput, DmpActionOutput, MqttAction, MqttActionForm
from aas_model.submodel_templates.hierarchical_structures import ResourceHierarchicalStructures


def optima_unloading() -> UnloadingStation:
    identity = "optimaUnloadingSystemAAS"
    serial = "OPTIMA-ULS-2024-001"
    parent = "aauFillingLineAAS"
    resource_id = f"{BASE_URL}/aas/{identity}"
    resource = UnloadingStation(
        id_short=identity,
        id=resource_id,
        specific_asset_ids={"serialNumber": serial},
        nameplate=Nameplate(
            URIOfTheProduct=resource_id,
            ManufacturerName=ManufacturerName(value={"en": "Optima"}),
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "Optima Unloading System"}),
            ManufacturerProductType="Optima Unloading System",
            AddressInformation=SITE_ADDRESS.model_copy(deep=True),
            OrderCodeOfManufacturer=serial,
            SerialNumber=serial,
            YearOfConstruction="2024",
            CountryOfOrigin="DE",
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
    mqtt.title.value = "Optima Unloading System"
    mqtt.EndpointMetadata.base.value = f"{BROKER}/{SITE}/Unloading/"
    resource.parameters.parameter["Location"].y.parameter.value = 240.0
    mqtt_actions = resource.asset_interfaces_description.InterfaceTemplateForMQTT[
        "interface_mqtt"
    ].InteractionMetadata.actions.property_name
    cci = resource.control_component_instance
    mappings = resource.asset_interfaces_mapping_configuration.MappingConfigurations.value
    for name in ("Unloading", "Scrap"):
        input_url = f"{SCHEMA_BASE}/command.schema.json"
        output_url = f"{SCHEMA_BASE}/commandResponse.schema.json"
        mqtt_actions[name] = MqttAction(
            title=name,
            synchronous="true",
            input=datapoint_from_schema(load_schema(input_url), cls=DmpActionInput, schema_url=input_url),
            output=datapoint_from_schema(load_schema(output_url), cls=DmpActionOutput, schema_url=output_url),
            forms=MqttActionForm(href=f"CMD/{name}", mqv_qos="2", mqv_responseTopic=f"DATA/{name}"),
        )
        operation = SkillOperation(
            in_output_variable=[Property(id_short="Uuid", description="The UUID of the command")],
            output_variable=[
                Property(id_short="State", description="The state of the command being executed"),
                Property(id_short="Outcome", value="0", value_type="xs:integer", qualifiers=[OptionalVariable()]),
            ],
        )
        skill = ExtendedSkill(interface_reference=affordance_ref(MQTT_INTERFACE, "actions", name), operation=operation)
        cci.Skills.Skill[name] = skill
        cci.Endpoints.Endpoint[name] = SkillInterfaceRelationship(
            first=skill_ref(name), second=affordance_ref(MQTT_INTERFACE, "actions", name)
        )
        mappings.append(AimcMappingConfiguration(
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
        ))
        container = resource.capability_description.CapabilitySet["Handling"].CapabilityContainer[name]
        container.CapabilityRelations = CapabilityRelations(
            CapabilityRealizedBy={
                f"RealizedBy_{name}": CapabilityRealizedBy(
                    first=capability_ref("Handling", name), second=skill_ref(name)
                )
            }
        )
    return resource
