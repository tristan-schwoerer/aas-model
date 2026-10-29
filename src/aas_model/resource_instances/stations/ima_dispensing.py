"""IMA dispensing station instance: the PackML contract, a Dispensing skill
with a configurable volume and the scale's live weight, all over OPC UA."""

from aas_pydantic import Property
from aas_model.constants import BASE_URL, CSSX, SCHEMA_BASE
from aas_model.resource_instances.site import SITE_ADDRESS
from aas_pydantic.submodel_templates.nameplate import Nameplate, ManufacturerName, ManufacturerProductDesignation
from aas_pydantic.submodel_templates.hierarchical_structures import EntryNode, Node
from aas_model.resource_template.operational import (
    COMMAND_RESPONSE_SCHEMA, COMMAND_RESPONSE_SCHEMA_URL, OPCUA_STATION, OperationalOpcuaControlComponent,
    OperationalOpcuaInterfaces, OperationalOpcuaMappings, OperationalVariables,
)
from aas_model.resource_template.resources import DispensingStation
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import SourcesItem, SinksItem
from aas_model.resource_template.references import (
    OPCUA_INTERFACE, action_member_ref, affordance_ref, capability_ref, operation_variable_ref, series_segment_ref,
    skill_ref,
)
from aas_model.submodel_templates.control_component_instance import (
    ExtendedSkill, SkillOperation, SkillInterfaceRelationship, OptionalVariable,
)
from aas_model.submodel_templates import AimcMappingConfiguration, DmpResponseSink, DmpResponseSource
from aas_pydantic.submodel_templates.capability_description import CapabilityRelations, CapabilityRealizedBy
from aas_model.json_schema_aid import datapoint_from_schema, load_schema
from aas_model.submodel_templates.variables import MeasurementsGroup
from aas_model.submodel_templates.aid import DmpActionInput, DmpActionOutput, DmpForm, OpcuaAction, OpcuaActionForm
from aas_pydantic.submodel_templates.asset_interfaces_description import Title
from aas_model.submodel_templates.time_series import (
    DmpLinkedSegment, InfluxDb2Target, RecordField, TimeSeriesCollection, TimeSeriesMetadata, TimeSeriesRecord,
    TimeSeriesSegments,
)
from aas_pydantic.submodel_templates.time_series import Name
from aas_model.submodel_templates.hierarchical_structures import ResourceHierarchicalStructures


# The Dispensing Method's InputArguments: the command plus the volume to fill.
DISPENSE_COMMAND = {
    "type": "object",
    "properties": {
        "Uuid": {"type": "string", "description": "The UUID of the command"},
        "Volume": {"type": "number", "minimum": 0, "unit": "ml", "description": "The volume to dispense"},
    },
    "required": ["Uuid", "Volume"],
}


def ima_dispensing() -> DispensingStation:
    identity = "imaDispensingSystemAAS"
    serial = "IMA-DS-2024-001"
    parent = "aauFillingLineAAS"
    resource_id = f"{BASE_URL}/aas/{identity}"
    resource = DispensingStation(
        id_short=identity,
        id=resource_id,
        specific_asset_ids={"serialNumber": serial},
        nameplate=Nameplate(
            URIOfTheProduct=resource_id,
            ManufacturerName=ManufacturerName(value={"en": "IMA"}),
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "IMA Dispensing System"}),
            ManufacturerProductType="IMA Dispensing System",
            AddressInformation=SITE_ADDRESS.model_copy(deep=True),
            OrderCodeOfManufacturer=serial,
            SerialNumber=serial,
            YearOfConstruction="2024",
            CountryOfOrigin="IT",
        ),
        hierarchical_structures=ResourceHierarchicalStructures(
            ArcheType="OneUp",
            EntryNode=EntryNode(
                global_asset_id=resource_id, Node={parent: Node(global_asset_id=f"{BASE_URL}/aas/{parent}")}
            ),
        ),
        asset_interfaces_description=OperationalOpcuaInterfaces(id_short="AssetInterfacesDescription"),
        control_component_instance=OperationalOpcuaControlComponent(id_short="ControlComponentInstance"),
        asset_interfaces_mapping_configuration=OperationalOpcuaMappings(
            id_short="AssetInterfacesMappingConfiguration",
        ),
        variables=OperationalVariables(),
    )
    opcua = resource.asset_interfaces_description.InterfaceTemplateForOPCUA[OPCUA_INTERFACE]
    opcua.title.value = "IMA Dispensing System"
    opcua.EndpointMetadata.base.value = "opc.tcp://dispensing-station:4840/dispensing/"
    resource.parameters.parameter["Location"].x.parameter.value = 240.0
    interaction = opcua.InteractionMetadata
    mappings = resource.asset_interfaces_mapping_configuration.MappingConfigurations.value

    # Dispensing: the Method Station.Dispensing(Uuid, Volume) -> commandResponse.
    name = "Dispensing"
    interaction.actions.property_name[name] = OpcuaAction(
        title=name,
        uav_componentOf=OPCUA_STATION,
        synchronous="true",
        input=datapoint_from_schema(DISPENSE_COMMAND, cls=DmpActionInput),
        output=datapoint_from_schema(
            COMMAND_RESPONSE_SCHEMA, cls=DmpActionOutput, schema_url=COMMAND_RESPONSE_SCHEMA_URL
        ),
        forms=OpcuaActionForm(href=f"/?id={f'{OPCUA_STATION}.{name}'}"),
    )
    cci = resource.control_component_instance
    cci.Skills.Skill[name] = ExtendedSkill(
        interface_reference=affordance_ref(OPCUA_INTERFACE, "actions", name),
        operation=SkillOperation(
            input_variable=[
                Property(
                    id_short="Volume", value="1.0", value_type="xs:double", description="The volume to dispense in ml"
                )
            ],
            in_output_variable=[Property(id_short="Uuid", description="The UUID of the command")],
            output_variable=[
                Property(id_short="State", description="The state of the command being executed"),
                Property(id_short="Outcome", value="0", value_type="xs:integer", qualifiers=[OptionalVariable()]),
            ],
        ),
    )
    cci.Endpoints.Endpoint[name] = SkillInterfaceRelationship(
        first=skill_ref(name),
        second=affordance_ref(OPCUA_INTERFACE, "actions", name),
    )
    # The mapping addresses the members of the Method's arguments: each
    # InputArgument is a Sink, each OutputArgument a ResponseSource, and the
    # Operation (its InOut and output variables) is the ResponseSink.
    command = ("Uuid", "Volume")
    reply = ("Uuid", "State", "Outcome")
    mappings.append(AimcMappingConfiguration(
        id_short=name, DefaultPollingInterval="0.0",
        Sources=[SourcesItem(SourceId=member, Source=operation_variable_ref(name, member)) for member in command],
        Sinks=[SinksItem(SinkId=member,
            Sink=action_member_ref(OPCUA_INTERFACE, name, "input", member),
        ) for member in command],
        Transformation=(
            "function aimc_main(sources) "
            "return { Uuid = sources.Uuid, Volume = sources.Volume } end"
        ),
        ResponseSources=[
            DmpResponseSource(SourceId=member, Source=action_member_ref(OPCUA_INTERFACE, name, "output", member))
            for member in reply],
        # Outcome is an Optional output (as in the commandResponse): a nil Outcome is left out.
        ResponseTransformation=(
            "function aimc_main(sources) return { Uuid = sources.Uuid, "
            "State = sources.State, Outcome = sources.Outcome } end"
        ),
        ResponseSinks=[
            DmpResponseSink(SinkId=member, Sink=operation_variable_ref(name, member)) for member in reply
        ],
    ))
    container = resource.capability_description.CapabilitySet["Processing"].CapabilityContainer[name]
    container.CapabilityRelations = CapabilityRelations(
        CapabilityRealizedBy={
            f"RealizedBy_{name}": CapabilityRealizedBy(first=capability_ref("Processing", name), second=skill_ref(name))
        }
    )

    # Weight: the scale's reading, sampled every 100 ms while it changes.
    weight = load_schema(f"{SCHEMA_BASE}/weight.schema.json")["properties"]["Weight"]
    interaction.properties.property_name["Weight"] = datapoint_from_schema(
        {**weight, "unit": "g"},
        key="Weight",
        title=Title(value="Weight"),
        observable="true",
        readOnly="true",
        forms=DmpForm(href=f"/?id={f'{OPCUA_STATION}.Weight'}"),
    )
    # One row per sample into Variables/Measurements/Weight.
    resource.variables.Measurements = MeasurementsGroup(value={"Weight": TimeSeriesCollection(
        Metadata=TimeSeriesMetadata(Name=Name(value={"en": "Dispensed weight"}), Record=TimeSeriesRecord(field={
            "Weight": RecordField(value_type="xs:double", supplemental_semantic_ids=[f"{CSSX}#Weight"],
                                  description="Weight in g"),
        })),
        Segments=TimeSeriesSegments(LinkedSegment={
            "Live": DmpLinkedSegment(InfluxDb2Target=InfluxDb2Target(Measurement="dispensing_weight")),
        }),
    )})
    mappings.append(
        AimcMappingConfiguration(
            id_short="Weight",
            DefaultPollingInterval="0.0",
            Sources=[
                SourcesItem(
                    Source=affordance_ref(OPCUA_INTERFACE, "properties", "Weight"),
                    SourceId="Weight",
                    PollingInterval="0.1",
                )
            ],
            Sinks=[SinksItem(Sink=series_segment_ref("Measurements", "Weight"), SinkId="Live")],
            Transformation="function aimc_main(sources) return { Live = { Weight = sources.Weight } } end",
        )
    )
    return resource
