"""Three planar movers sharing the PlanarShuttle type: MoveToPosition and the reported Location over MQTT."""

from aas_pydantic import Property
from aas_pydantic.submodel_templates.asset_interfaces_description import Title
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import SinksItem, SourcesItem
from aas_pydantic.submodel_templates.capability_description import CapabilityRealizedBy, CapabilityRelations
from aas_pydantic.submodel_templates.hierarchical_structures import EntryNode, Node
from aas_pydantic.submodel_templates.nameplate import ManufacturerName, ManufacturerProductDesignation
from aas_model.resource_template import ResourceNameplate
from aas_pydantic.submodel_templates.time_series import Name

from aas_model.constants import BASE_URL, BROKER, SCHEMA_BASE, SITE
from aas_model.json_schema_aid import datapoint_from_schema, load_schema
from aas_model.resource_template.operational import COMMAND_RESPONSE_SCHEMA, COMMAND_RESPONSE_SCHEMA_URL
from aas_model.resource_template.references import (
    MQTT_INTERFACE, action_member_ref, affordance_ref, capability_ref, operation_variable_ref, series_segment_ref,
    skill_ref,
)
from aas_model.submodel_templates.hierarchical_structures import ResourceHierarchicalStructures
from aas_model.resource_template.resources import PlanarShuttle
from aas_model.submodel_templates import AimcMappingConfiguration, DmpResponseSink, DmpResponseSource
from aas_model.submodel_templates.aid import DmpActionInput, DmpActionOutput, MqttAction, MqttActionForm, MqttForm
from aas_model.submodel_templates.control_component_instance import (
    ExtendedSkill, OptionalVariable, SkillInterfaceRelationship, SkillOperation,
)
from aas_model.submodel_templates.time_series import (
    DmpLinkedSegment, InfluxDb2Target, RecordField, TimeSeriesCollection, TimeSeriesMetadata, TimeSeriesRecord,
    TimeSeriesSegments,
)
from aas_model.submodel_templates.variables import MeasurementsGroup


def planar_shuttle_1() -> PlanarShuttle:
    return _planar_shuttle(1, x=480.0)


def planar_shuttle_2() -> PlanarShuttle:
    return _planar_shuttle(2, x=240.0)


def planar_shuttle_3() -> PlanarShuttle:
    return _planar_shuttle(3, x=480.0)


def _planar_shuttle(number: int, x: float) -> PlanarShuttle:
    """Shuttle *number*, the table's Xbot<number>, starting at *x*."""
    identity = f"planarTableShuttle{number}AAS"
    parent = "planarTableAAS"
    resource_id = f"{BASE_URL}/aas/{identity}"
    # The legacy shuttles shared one serial; their individual serials are unknown.
    resource = PlanarShuttle(
        id_short=identity,
        id=resource_id,
        nameplate=ResourceNameplate(
            URIOfTheProduct=resource_id,
            ManufacturerName=ManufacturerName(value={"en": "Planar Motors"}),
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "Planar Motors Shuttle"}),
            ManufacturerProductType="Planar Motors Shuttle",
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
    )
    mqtt = resource.asset_interfaces_description.InterfaceTemplateForMQTT[MQTT_INTERFACE]
    mqtt.title.value = "Planar Motors Shuttle"
    mqtt.EndpointMetadata.base.value = f"{BROKER}/{SITE}/Planar/Xbot{number}/"
    resource.parameters.parameter["Location"].x.parameter.value = x
    interaction = mqtt.InteractionMetadata
    mappings = resource.asset_interfaces_mapping_configuration.MappingConfigurations.value

    # MoveToPosition: the device's motion topics are CMD/XYMotion and DATA/XYMotion.
    name = "MoveToPosition"
    input_url = f"{SCHEMA_BASE}/moveToPosition.schema.json"
    interaction.actions.property_name[name] = MqttAction(
        title=name,
        synchronous="false",
        input=datapoint_from_schema(load_schema(input_url), cls=DmpActionInput, schema_url=input_url),
        output=datapoint_from_schema(
            COMMAND_RESPONSE_SCHEMA, cls=DmpActionOutput, schema_url=COMMAND_RESPONSE_SCHEMA_URL
        ),
        forms=MqttActionForm(href="CMD/XYMotion", mqv_qos="2", mqv_responseTopic="DATA/XYMotion"),
    )
    cci = resource.control_component_instance
    cci.Skills.Skill[name] = ExtendedSkill(
        interface_reference=affordance_ref(MQTT_INTERFACE, "actions", name),
        operation=SkillOperation(
            # ProductID is not sent to the device; the reply echoes the caller's value.
            in_output_variable=[
                Property(id_short="Uuid", description="The UUID of the command"),
                Property(id_short="ProductID", description="The product the shuttle carries",
                         qualifiers=[OptionalVariable()]),
            ],
            input_variable=[
                Property(id_short=axis, value_type="xs:double", value="0.0") for axis in ("X", "Y", "Theta")
            ],
            output_variable=[
                Property(id_short="State", description="The state of the command being executed"),
                Property(id_short="Outcome", value_type="xs:integer", value="0", qualifiers=[OptionalVariable()]),
            ],
        ),
    )
    cci.Endpoints.Endpoint[name] = SkillInterfaceRelationship(
        first=skill_ref(name), second=affordance_ref(MQTT_INTERFACE, "actions", name)
    )
    mappings.append(AimcMappingConfiguration(
        id_short=name, DefaultPollingInterval="0.0",
        Sources=[SourcesItem(SourceId=member, Source=operation_variable_ref(name, member))
                 for member in ("Uuid", "ProductID", "X", "Y", "Theta")],
        Sinks=[SinksItem(SinkId=name, Sink=action_member_ref(MQTT_INTERFACE, name, "input"))],
        Transformation="""function aimc_main(sources)
    return { MoveToPosition = { Uuid = sources.Uuid, Position = {sources.X, sources.Y, sources.Theta} } }
end
""",
        ResponseSources=[
            DmpResponseSource(SourceId="Reply", Source=action_member_ref(MQTT_INTERFACE, name, "output")),
        ],
        ResponseTransformation=(
            "function aimc_main(sources, requestSources) local reply = sources.Reply "
            "return { Uuid = reply.Uuid, State = reply.State, Outcome = reply.Outcome, "
            "ProductID = requestSources.ProductID } end"
        ),
        ResponseSinks=[DmpResponseSink(SinkId=member, Sink=operation_variable_ref(name, member))
                       for member in ("Uuid", "State", "Outcome", "ProductID")],
    ))
    container = resource.capability_description.CapabilitySet["Transport"].CapabilityContainer[name]
    container.CapabilityRelations = CapabilityRelations(
        CapabilityRealizedBy={
            f"RealizedBy_{name}": CapabilityRealizedBy(first=capability_ref("Transport", name), second=skill_ref(name))
        }
    )

    # Location: the reported position, as Properties and, one row per report, into Variables/Measurements/Location.
    location_url = f"{SCHEMA_BASE}/positionStamped.schema.json"
    interaction.properties.property_name["Location"] = datapoint_from_schema(
        load_schema(location_url),
        key="Location",
        schema_url=location_url,
        title=Title(value="Location"),
        observable="true",
        readOnly="true",
        forms=MqttForm(href="DATA/Location", mqv_retain="true", mqv_qos="0"),
    )
    resource.variables.Measurements = MeasurementsGroup(value={"Location": TimeSeriesCollection(
        Metadata=TimeSeriesMetadata(Name=Name(value={"en": "Shuttle position"}), Record=TimeSeriesRecord(field={
            axis: RecordField(value_type="xs:double") for axis in ("x", "y", "yaw")
        })),
        Segments=TimeSeriesSegments(LinkedSegment={
            "Live": DmpLinkedSegment(InfluxDb2Target=InfluxDb2Target(Measurement="transport_position")),
        }),
    )})
    mappings.extend([
        AimcMappingConfiguration(
            id_short="Location", DefaultPollingInterval="0.0",
            Sources=[SourcesItem(SourceId="Location", Source=affordance_ref(MQTT_INTERFACE, "properties", "Location"))],
            Sinks=[SinksItem(SinkId="Live", Sink=series_segment_ref("Measurements", "Location"))],
            Transformation="""function aimc_main(sources)
    local position = sources.Location.Position
    return { Live = { x = position[1], y = position[2], yaw = position[3] or 0.0 } }
end
""",
        ),
    ])
    return resource
