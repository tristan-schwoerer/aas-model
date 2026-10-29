"""How the shared models serialize to AAS JSON: the AIMC's DMP additions and the AID's protocol terms."""

from __future__ import annotations

import json

from aas_json import element, value
from aas_model.submodel_templates import (
    Aimc, AimcMappingConfiguration, DmpEvaluation, DmpResponseSink, DmpResponseSource, DmpSource,
)
from aas_model.submodel_templates.aid import DmpAssetInterfacesDescription
from aas_model.resource_template.references import variable_ref
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import SinksItem, SourcesItem


def test_aimc_response_sources_and_sinks_are_exported():
    from aas_model.testing import aimc_ref
    from aas_model.resource_template import ResourceTypeAAS
    from aas_model.submodel_templates import AimcMappingConfigurations
    from aas_model.constants import BASE_URL
    from aas_pydantic.convert_pydantic_model import convert_model_to_aas
    from basyx.aas.adapter.json import json_serialization

    action_output = aimc_ref(
        "{aas_id}/submodels/AssetInterfacesDescription", "interface_mqtt",
        "InteractionMetadata", "actions", "Halt", "output", "State")
    operation = aimc_ref(
        "{aas_id}/submodels/ControlComponentInstance", "Skills", "Halt",
        "operation")
    variables = aimc_ref("{aas_id}/submodels/Variables", "PackMLState")
    mapping = AimcMappingConfiguration(
        id_short="Halt",
        Sources=[SourcesItem(SourceId="Halt", Source=operation)],
        Sinks=[
            SinksItem(
                SinkId="Halt",
                Sink=aimc_ref(
                    "{aas_id}/submodels/AssetInterfacesDescription",
                    "interface_mqtt",
                    "InteractionMetadata",
                    "actions",
                    "Halt",
                ),
            )
        ],
        Transformation="function aimc_main(sources) return sources end",
        ResponseSources=[DmpResponseSource(SourceId="DeviceState", Source=action_output)],
        ResponseSinks=[DmpResponseSink(SinkId="PackMLState", Sink=variables)],
        DefaultPollingInterval="0.0",
    )
    aimc = Aimc(id_short="AIMC", MappingConfigurations=AimcMappingConfigurations(
        value=[mapping]))
    asset = ResourceTypeAAS(
        id_short="RoundTrip", id=f"{BASE_URL}/aas/RoundTrip", asset_type="RoundTrip",
        asset_interfaces_mapping_configuration=aimc)
    doc = json.loads(json_serialization.object_store_to_json(convert_model_to_aas(asset)))
    serialized = next(s for s in doc["submodels"] if s.get("idShort") == "AIMC")

    halt = element(serialized, "MappingConfigurations", "Halt")
    source = element(halt, "ResponseSources", 0)
    assert value(source, "SourceId") == "DeviceState"
    assert value(source, "Source")["keys"][-1]["value"] == "State"
    sink = element(halt, "ResponseSinks", 0)
    assert value(sink, "SinkId") == "PackMLState"
    assert value(sink, "Sink")["keys"][-1]["value"] == "PackMLState"


def test_aimc_response_endpoints_are_optional():
    from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import (
        SourcesItem as Source, SinksItem as Sink, Source as SourceReference, Sink as SinkReference, SourceId, SinkId,
    )
    from aas_pydantic import ModelReference, Key

    mapping = AimcMappingConfiguration(
        Sources=[
            Source(
                Source=SourceReference(value=ModelReference(key=(Key(type_="Submodel", value="urn:source"),))),
                SourceId=SourceId(value="s"),
            )
        ],
        Sinks=[
            Sink(
                Sink=SinkReference(value=ModelReference(key=(Key(type_="Submodel", value="urn:sink"),))),
                SinkId=SinkId(value="t"),
            )
        ],
    )
    assert mapping.ResponseSources is None
    assert mapping.ResponseSinks is None


def test_a_sources_evaluation_serializes_inside_the_idta_source():
    from aas_pydantic import ModelReference, Key

    mapping = AimcMappingConfiguration(
        Sources=[
            DmpSource(
                SourceId="state",
                Source=ModelReference(key=(Key(type_="Submodel", value="urn:source"),)),
                Evaluation=DmpEvaluation(Mode="OnChange"),
            ),
            SourcesItem(SourceId="plain", Source=ModelReference(key=(Key(type_="Submodel", value="urn:plain"),))),
        ],
        Sinks=[SinksItem(SinkId="target", Sink=ModelReference(key=(Key(type_="Submodel", value="urn:sink"),)))],
    )
    from aas_model.constants import AIMC_EVALUATION, AIMC_EVALUATION_MODE, BASE_URL
    evaluated = mapping.Sources.value[0]
    assert evaluated.Evaluation.semantic_id == AIMC_EVALUATION
    assert evaluated.Evaluation.Mode.semantic_id == AIMC_EVALUATION_MODE
    assert evaluated.Evaluation.Mode.value == "OnChange"
    assert mapping.Sources.value[1].Evaluation is None, "a plain IDTA Source has no Evaluation"

    from aas_model.resource_template import ResourceTypeAAS
    from aas_model.submodel_templates import Aimc, AimcMappingConfigurations
    from aas_pydantic.convert_pydantic_model import convert_model_to_aas
    from basyx.aas.adapter.json import json_serialization

    serialized_mapping = AimcMappingConfiguration(Sources=[mapping.Sources.value[0]], Sinks=mapping.Sinks.value)
    aimc = Aimc(id_short="AIMC", MappingConfigurations=AimcMappingConfigurations(value=[serialized_mapping]))
    asset = ResourceTypeAAS(id_short="EvaluationRoundTrip", id=f"{BASE_URL}/aas/EvaluationRoundTrip",
                            asset_type="EvaluationRoundTrip", asset_interfaces_mapping_configuration=aimc)
    doc = json.loads(json_serialization.object_store_to_json(convert_model_to_aas(asset)))
    serialized = next(s for s in doc["submodels"] if s.get("idShort") == "AIMC")
    source = serialized["submodelElements"][0]["value"][0]["value"]
    sources = next(e for e in source if e["idShort"] == "Sources")["value"]
    evaluation = next(e for e in sources[0]["value"] if e["idShort"] == "Evaluation")
    assert evaluation["semanticId"]["keys"][0]["value"] == AIMC_EVALUATION
    assert evaluation["value"] == [next(e for e in evaluation["value"] if e["idShort"] == "Mode")]
    assert evaluation["value"][0]["value"] == "OnChange"


def test_resource_sources_may_carry_an_evaluation():

    mapping = AimcMappingConfiguration(
        id_short="Evaluated",
        Sources=[
            DmpSource(SourceId="state", Source=variable_ref("PackMLState"), Evaluation=DmpEvaluation(Mode="OnChange")),
            DmpSource(
                SourceId="limit", Source=variable_ref("Limit"), Evaluation=DmpEvaluation(Mode="ReadAtEvaluation")
            ),
        ],
        Sinks=[SinksItem(SinkId="result", Sink=variable_ref("Result"))],
        Transformation="function aimc_main(sources) return sources end",
        DefaultPollingInterval="0.0",
    )
    assert [item.Evaluation.Mode.value for item in mapping.Sources.value] == ["OnChange", "ReadAtEvaluation"]
    plain = AimcMappingConfiguration(
        id_short="Plain",
        Sources=[SourcesItem(SourceId="state", Source=variable_ref("PackMLState"))],
        Sinks=[SinksItem(SinkId="result", Sink=variable_ref("Result"))],
        Transformation="",
        DefaultPollingInterval="0.0",
    )
    assert plain.Sources.value[0].Evaluation is None, "an IDTA Source becomes a DmpSource without an Evaluation"


def test_protocol_specific_endpoint_and_form_terms_are_exported():
    """The AID's own protocol vocabulary (modv_*, uav_*, OPC UA security
    schemes) on the extended forms and endpoint metadata is exported. The Modbus interface is authored as AID Annex B describes it: the
    unit ID in the base, the register address and quantity in the href."""
    from aas_model.testing import modbus_interface, opcua_interface
    from aas_pydantic import Property

    aid = DmpAssetInterfacesDescription(id_short="AssetInterfacesDescription")
    modbus = modbus_interface("modbus+tcp://192.168.0.70:502/1/", properties={"Coil1": "0?quantity=1"})
    modbus.EndpointMetadata.modv_mostSignificantByte = Property(
        semantic_id="https://www.w3.org/2019/wot/modbus#hasMostSignificantByte",
        value="false")
    modbus.InteractionMetadata.properties.property_name["Coil1"].forms.modv_function = Property(
        semantic_id="https://www.w3.org/2019/wot/modbus#hasFunction",
        value="writeSingleCoil")
    aid.InterfaceTemplateForMODBUS["interface_modbus"] = modbus

    opcua = opcua_interface(
        "opc.tcp://192.168.0.90:4840",
        actions={"Calibrate": ("/?id=ns=2;s=RunCalibration", "POST",
                               "ns=1;s=CalibrationObject")})
    from aas_pydantic.submodel_templates.asset_interfaces_description import (
        Scheme, UavSecurityMode, UavSecurityPolicy, opcua_channel_sc,
    )
    # named-field convention: field name == id_short — stamp it (post-
    # validation mutation bypasses the model's automatic stamping)
    channel = opcua_channel_sc(
        scheme=Scheme(value="opcua_channel_sc"),
        uav_securityMode=UavSecurityMode(value="SignAndEncrypt"),
        uav_securityPolicy=UavSecurityPolicy(value="Basic256Sha256"))
    channel.id_short = "opcua_channel_sc"
    opcua.EndpointMetadata.securityDefinitions.opcua_channel_sc = channel
    aid.InterfaceTemplateForOPCUA["interface_opcua"] = opcua

    # The protocol terms are exported (they previously could not even be authored — extra_forbidden on the
    # generic classes).
    doc = _roundtrip(aid)
    modbus = element(doc, "interface_modbus")
    assert value(modbus, "EndpointMetadata", "modv_mostSignificantByte") == "false"
    assert value(modbus, "InteractionMetadata", "properties", "Coil1", "forms", "modv_function") == "writeSingleCoil"
    channel = element(doc, "interface_opcua", "EndpointMetadata", "securityDefinitions", "opcua_channel_sc")
    assert value(channel, "uav_securityMode") == "SignAndEncrypt"
    assert value(channel, "uav_securityPolicy") == "Basic256Sha256"


def _roundtrip(aid_model) -> dict:
    import json

    from aas_pydantic.convert_pydantic_model import convert_model_to_aas
    from basyx.aas.adapter.json import json_serialization

    from aas_model.constants import BASE_URL
    from aas_model.resource_template import ResourceTypeAAS
    asset = ResourceTypeAAS(
        id_short="RoundTrip",
        id=f"{BASE_URL}/aas/RoundTrip",
        asset_type="RoundTrip",
    )
    asset.asset_interfaces_description = aid_model
    doc = json.loads(json_serialization.object_store_to_json(convert_model_to_aas(asset)))
    return next(s for s in doc["submodels"]
                if s.get("idShort") == aid_model.id_short)
