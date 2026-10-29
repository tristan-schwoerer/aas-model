"""Omron inspection camera instance."""

from aas_pydantic import Property
from aas_model.constants import CSSX, SCHEMA_BASE
from aas_model.constants import BASE_URL, BROKER, SITE
from aas_pydantic.submodel_templates.nameplate import ManufacturerName, ManufacturerProductDesignation
from aas_model.resource_template import ResourceNameplate
from aas_pydantic.submodel_templates.hierarchical_structures import EntryNode, Node
from aas_model.resource_template.operational import (
    OperationalMqttControlComponent, OperationalMqttInterfaces, OperationalMqttMappings, OperationalVariables,
)
from aas_model.resource_template.resources import InspectionStation
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import SourcesItem, SinksItem
from aas_model.submodel_templates import AimcMappingConfiguration, DmpResponseSink, DmpResponseSource
from aas_model.resource_template.references import (
    MQTT_INTERFACE, action_member_ref, affordance_ref, capability_ref, operation_variable_ref, series_segment_ref,
    skill_ref, variable_ref,
)
from aas_model.submodel_templates.control_component_instance import (
    ExtendedSkill, SkillOperation, SkillInterfaceRelationship, OptionalVariable,
)
from aas_pydantic.submodel_templates.capability_description import CapabilityRelations, CapabilityRealizedBy
from aas_model.json_schema_aid import datapoint_from_schema, load_schema
from aas_model.submodel_templates.variables import MeasurementsGroup, VariableProp
from aas_model.submodel_templates.time_series import (
    DmpLinkedSegment, InfluxDb2Target, RecordField, TimeSeriesCollection, TimeSeriesMetadata, TimeSeriesRecord,
    TimeSeriesSegments,
)
from aas_pydantic.submodel_templates.time_series import Name
from aas_model.submodel_templates.aid import DmpActionInput, DmpActionOutput, MqttAction, MqttActionForm, MqttForm
from aas_pydantic.submodel_templates.asset_interfaces_description import Title
from aas_model.submodel_templates.hierarchical_structures import ResourceHierarchicalStructures


def omron_camera() -> InspectionStation:
    identity = "omronCameraSystemAAS"
    serial = "OMRON-CAM-2024-001"
    parent = "aauFillingLineAAS"
    resource_id = f"{BASE_URL}/aas/{identity}"
    resource = InspectionStation(
        id_short=identity,
        id=resource_id,
        specific_asset_ids={"serialNumber": serial},
        nameplate=ResourceNameplate(
            URIOfTheProduct=resource_id,
            ManufacturerName=ManufacturerName(value={"en": "Omron"}),
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "Omron Camera System"}),
            ManufacturerProductType="Omron Camera System",
            OrderCodeOfManufacturer=serial,
            SerialNumber=serial,
            YearOfConstruction="2024",
            CountryOfOrigin="JP",
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
    mqtt.title.value = "Omron Camera System"
    mqtt.EndpointMetadata.base.value = f"{BROKER}/{SITE}/QualityControl/"
    position = resource.parameters.parameter["Location"]
    position.x.parameter.value = 480.0
    position.y.parameter.value = 240.0
    name = "Capture"
    interaction = resource.asset_interfaces_description.InterfaceTemplateForMQTT[
        "interface_mqtt"
    ].InteractionMetadata
    input_url = f"{SCHEMA_BASE}/command.schema.json"
    output_url = f"{SCHEMA_BASE}/commandResponse.schema.json"
    interaction.actions.property_name[name] = MqttAction(
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
    mappings = resource.asset_interfaces_mapping_configuration.MappingConfigurations.value
    mappings.append(AimcMappingConfiguration(
        id_short=name, DefaultPollingInterval="0.0",
        Sources=[SourcesItem(SourceId="Uuid", Source=operation_variable_ref(name, "Uuid"))],
        Sinks=[SinksItem(Sink=action_member_ref(MQTT_INTERFACE, name, "input"), SinkId=name)],
        Transformation=(
            f"function aimc_main(sources) return {{ {name} = {{ Uuid = sources.Uuid }} }} end"
        ),
        ResponseSources=[DmpResponseSource(SourceId="Reply", Source=action_member_ref(MQTT_INTERFACE, name, "output"))],
        ResponseTransformation=(
            "function aimc_main(sources) local reply = sources.Reply "
            "return { Uuid = reply.Uuid, State = reply.State, Outcome = reply.Outcome } end"
        ),
        ResponseSinks=[DmpResponseSink(SinkId=member, Sink=operation_variable_ref(name, member))
                       for member in ("Uuid", "State", "Outcome")],
    ))
    container = resource.capability_description.CapabilitySet["Inspection"].CapabilityContainer[name]
    container.CapabilityRelations = CapabilityRelations(
        CapabilityRealizedBy={
            f"RealizedBy_{name}": CapabilityRealizedBy(first=capability_ref("Inspection", name), second=skill_ref(name))
        }
    )

    for observation in ("Image", "QualityResult"):
        url = f"{SCHEMA_BASE}/{observation[0].lower() + observation[1:]}.schema.json"
        interaction.properties.property_name[observation] = datapoint_from_schema(
            load_schema(url),
            key=observation,
            schema_url=url,
            title=Title(value=observation),
            observable="true",
            readOnly="true",
            forms=MqttForm(href=f"DATA/{observation}", mqv_retain="true", mqv_qos="0"),
        )
    # The latest image, as a Property: images have no place in a time series. Each quality result, one row into
    # Variables/Measurements/QualityResult.
    resource.variables.Measurements = MeasurementsGroup(value={
        "Image": VariableProp(id_short="Image", supplemental_semantic_ids=[f"{CSSX}#Image"]),
        "QualityResult": TimeSeriesCollection(
            Metadata=TimeSeriesMetadata(Name=Name(value={"en": "Quality results"}), Record=TimeSeriesRecord(field={
                "Uuid": RecordField(value_type="xs:string", description="The inspected product's Uuid"),
                "Result": RecordField(value_type="xs:string", supplemental_semantic_ids=[f"{CSSX}#QualityResult"],
                                      description="Ok or NotOk"),
            })),
            Segments=TimeSeriesSegments(LinkedSegment={
                "Live": DmpLinkedSegment(InfluxDb2Target=InfluxDb2Target(Measurement="inspection_quality")),
            }),
        ),
    })
    mappings.extend([
        AimcMappingConfiguration(
            id_short="Image", DefaultPollingInterval="0.0",
            Sources=[SourcesItem(SourceId="Image", Source=affordance_ref(MQTT_INTERFACE, "properties", "Image"))],
            Sinks=[SinksItem(SinkId="Image", Sink=variable_ref("Measurements", "Image"))],
            Transformation="function aimc_main(sources) return { Image = sources.Image.Image } end",
        ),
        AimcMappingConfiguration(
            id_short="QualityResult", DefaultPollingInterval="0.0",
            Sources=[SourcesItem(SourceId="QualityResult",
                                 Source=affordance_ref(MQTT_INTERFACE, "properties", "QualityResult"))],
            Sinks=[SinksItem(SinkId="Live", Sink=series_segment_ref("Measurements", "QualityResult"))],
            Transformation="function aimc_main(sources) local result = sources.QualityResult "
                           "return { Live = { Uuid = result.Uuid, Result = result.Result } } end",
        ),
    ])
    return resource
