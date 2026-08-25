"""Schema-lockstep golden test (ADR-016, Phase 4).

Changes to any shared submodel model change its JSON schema. This test pins the
schema of the AID and AIMC submodels to a checked-in golden file, so a generator
change is *forced* to break CI until the snapshot is intentionally updated —
proving the management node's parse (which validates against these models) stays
in lockstep with the authoring side.
"""

from __future__ import annotations

import json
from pathlib import Path

from aas_model.submodel_templates import Aimc
from aas_model.submodel_templates.mqtt_aid import MqttAssetInterfacesDescription

HERE = Path(__file__).parent
GOLDEN = HERE / "schema_snapshots.json"


def _schemas() -> dict:
    return {
        "Aimc": Aimc.model_json_schema(),
        "MqttAssetInterfacesDescription": MqttAssetInterfacesDescription.model_json_schema(),
    }


def test_schemas_match_golden_snapshot():
    if not GOLDEN.exists():
        GOLDEN.write_text(json.dumps(_schemas(), indent=2, sort_keys=True) + "\n")
        raise AssertionError(
            "schema snapshot created — review and commit schema_snapshots.json"
        )
    golden = json.loads(GOLDEN.read_text())
    assert _schemas() == golden, (
        "A shared model schema changed. The management node validates AID/AIMC "
        "against these models (ADR-016); update schema_snapshots.json only if the "
        "change is intended AND the management-node parser is updated in the same "
        "change."
    )
