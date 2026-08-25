"""Tests for aas_model: AAS-JSON -> shared-model reverse parsing (ADR-016).

These lock the management node's parse to the same models the registration
service authors, using the real BaSyx REST fixtures.
"""

from __future__ import annotations

import json
from pathlib import Path

from aas_model._serde import parse_submodel_dict
from aas_model.submodel_templates import Aimc
from aas_model.submodel_templates.mqtt_aid import MqttAssetInterfacesDescription

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
    model = parse_submodel_dict(_load("data_aid.json"), MqttAssetInterfacesDescription)
    assert isinstance(model, MqttAssetInterfacesDescription)
    assert model.interface_mqtt is not None
    im = model.interface_mqtt.InteractionMetadata
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
