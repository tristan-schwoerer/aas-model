"""Tests for aas_model: AAS-JSON -> shared-model reverse parsing (ADR-016).

These lock the management node's parse to the same models the registration
service authors, using the real BaSyx REST fixtures.
"""

from __future__ import annotations

import json
from pathlib import Path

from aas_json import parse_submodel_dict
from aas_model.submodel_templates import (
    Aimc, AimcMappingConfiguration, DmpEvaluation, DmpResponseSink, DmpResponseSource, DmpSource,
)
from aas_model.submodel_templates.aid import DmpAssetInterfacesDescription
from aas_model.resource_template.references import variable_ref
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import SinksItem, SourcesItem

HERE = Path(__file__).parent


def _load(name: str) -> dict:
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def test_aimc_reverse_parses_to_shared_model():
    model = parse_submodel_dict(_load("data_aimc.json"), Aimc)
    assert isinstance(model, Aimc)
    mcs = model.MappingConfigurations.value
    assert len(mcs) == 5
    # The Transformation blob (Lua) is preserved.
    assert mcs[0].Transformation is not None
    assert mcs[0].Sources.value and mcs[0].Sinks.value


def test_aid_reverse_parses_to_shared_model_with_mqtt_actions():
    model = parse_submodel_dict(_load("data_aid.json"), DmpAssetInterfacesDescription)
    assert isinstance(model, DmpAssetInterfacesDescription)
    assert model.InterfaceTemplateForMQTT["interface_mqtt"] is not None
    im = model.InterfaceTemplateForMQTT["interface_mqtt"].InteractionMetadata
    actions = list(im.actions.property_name.keys())
    props = list(im.properties.property_name.keys())
    # The registration-service MQTT action extensions round-trip.
    assert {"Halt", "Occupy", "Release", "Stoppering"} <= set(actions)
    assert "StationState" in props


def test_round_trip_preserves_semantic_id():
    m = parse_submodel_dict(_load("data_aimc.json"), Aimc)
    assert m.semantic_id == (
        "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/Submodel"
    )


def test_aimc_response_sources_and_sinks_round_trip():
    from aas_model.testing import aimc_ref
    from aas_model.resource_template import ResourceTypeAAS
    from aas_model.submodel_templates import AimcMappingConfigurations
    from aas_model.constants import BASE_URL
    from aas_pydantic.convert_pydantic_model import convert_model_to_aas
    from aas_pydantic.convert_util import strip_temp_id_short_attributes
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
    store = convert_model_to_aas(asset)
    strip_temp_id_short_attributes(store)
    doc = json.loads(json_serialization.object_store_to_json(store))
    serialized = next(s for s in doc["submodels"] if s.get("idShort") == "AIMC")
    back = parse_submodel_dict(serialized, Aimc)

    response_mapping = back.MappingConfigurations.value[0]
    assert response_mapping.ResponseSources.value[0].SourceId.value == "DeviceState"
    assert response_mapping.ResponseSources.value[0].Source.value.key[-1].value == "State"
    assert response_mapping.ResponseSinks.value[0].SinkId.value == "PackMLState"
    assert response_mapping.ResponseSinks.value[0].Sink.value.key[-1].value == "PackMLState"


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
    from aas_pydantic.convert_util import strip_temp_id_short_attributes
    from basyx.aas.adapter.json import json_serialization

    serialized_mapping = AimcMappingConfiguration(Sources=[mapping.Sources.value[0]], Sinks=mapping.Sinks.value)
    aimc = Aimc(id_short="AIMC", MappingConfigurations=AimcMappingConfigurations(value=[serialized_mapping]))
    asset = ResourceTypeAAS(id_short="EvaluationRoundTrip", id=f"{BASE_URL}/aas/EvaluationRoundTrip",
                            asset_type="EvaluationRoundTrip", asset_interfaces_mapping_configuration=aimc)
    store = convert_model_to_aas(asset)
    strip_temp_id_short_attributes(store)
    doc = json.loads(json_serialization.object_store_to_json(store))
    serialized = next(s for s in doc["submodels"] if s.get("idShort") == "AIMC")
    source = serialized["submodelElements"][0]["value"][0]["value"]
    sources = next(e for e in source if e["idShort"] == "Sources")["value"]
    evaluation = next(e for e in sources[0]["value"] if e["idShort"] == "Evaluation")
    assert evaluation["semanticId"]["keys"][0]["value"] == AIMC_EVALUATION
    assert evaluation["value"] == [next(e for e in evaluation["value"] if e["idShort"] == "Mode")]
    assert evaluation["value"][0]["value"] == "OnChange"

    # parsed back, the Source still carries its Evaluation; a plain IDTA Source stays without one
    restored = parse_submodel_dict(serialized, Aimc).MappingConfigurations.value[0].Sources.value
    assert restored[0].Evaluation.Mode.value == "OnChange"
    assert type(restored[0]).__name__ == "DmpSource"


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


def test_protocol_specific_endpoint_and_form_terms_round_trip():
    """The AID's own protocol vocabulary (modv_*, uav_*, OPC UA security
    schemes) on the extended forms and endpoint metadata survives a round
    trip. The Modbus interface is authored as AID Annex B describes it: the
    unit ID in the base, the register address and quantity in the href."""
    from aas_model.submodel_templates.aid import DmpModbusInterface, DmpOpcuaInterface, ModbusForm
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

    # serialize → parse back: the protocol terms survive (they previously
    # could not even be authored — extra_forbidden on the generic classes)
    doc = _roundtrip(aid)
    back = parse_submodel_dict(doc, DmpAssetInterfacesDescription)

    mb = back.InterfaceTemplateForMODBUS["interface_modbus"]
    assert isinstance(mb, DmpModbusInterface)
    assert mb.EndpointMetadata.modv_mostSignificantByte.value == "false"
    coil = mb.InteractionMetadata.properties.property_name["Coil1"]
    assert isinstance(coil.forms, ModbusForm)
    assert coil.forms.modv_function.value == "writeSingleCoil"

    oc = back.InterfaceTemplateForOPCUA["interface_opcua"]
    assert isinstance(oc, DmpOpcuaInterface)
    security = oc.EndpointMetadata.securityDefinitions
    assert security.opcua_channel_sc.uav_securityMode.value == "SignAndEncrypt"
    assert security.opcua_channel_sc.uav_securityPolicy.value == "Basic256Sha256"


def _roundtrip(aid_model) -> dict:
    import json

    from aas_pydantic.convert_pydantic_model import convert_model_to_aas
    from aas_pydantic.convert_util import strip_temp_id_short_attributes
    from basyx.aas.adapter.json import json_serialization

    from aas_model.constants import BASE_URL
    from aas_model.resource_template import ResourceTypeAAS
    asset = ResourceTypeAAS(
        id_short="RoundTrip",
        id=f"{BASE_URL}/aas/RoundTrip",
        asset_type="RoundTrip",
    )
    asset.asset_interfaces_description = aid_model
    store = convert_model_to_aas(asset)
    strip_temp_id_short_attributes(store)
    doc = json.loads(json_serialization.object_store_to_json(store))
    return next(s for s in doc["submodels"]
                if s.get("idShort") == aid_model.id_short)
