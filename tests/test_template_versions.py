"""Regenerated models stay tied to their selected IDTA source releases."""

import importlib
import json
import re
from pathlib import Path
import runpy

import pytest

from aas_model.json_schema_aid import datapoint_from_schema, schema_from_datapoint
from aas_json import element, value
from aas_model.submodel_templates.aid import DmpAssetInterfacesDescription
from aas_pydantic import Submodel
from aas_pydantic.submodel_templates.asset_interfaces_description import (
    AssetInterfacesDescription,
    EndpointMetadata,
    property_name as PropertyDefinition,
)
from aas_pydantic.submodel_templates.nameplate import AddressInformation
from test_serde import _roundtrip


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = runpy.run_path(str(ROOT / "scripts" / "idta_generate.py"))


@pytest.mark.parametrize("relative_path", GENERATOR["TEMPLATES"])
def test_generated_model_matches_its_selected_template(relative_path):
    path = Path(GENERATOR["TEMPLATE_ROOT"]) / relative_path
    source = json.loads(path.read_text(encoding="utf-8-sig"))["submodels"][0]
    class_name = GENERATOR["safe_name"](source["idShort"])
    module_name = GENERATOR["snake"](class_name)
    module = importlib.import_module(f"aas_pydantic.submodel_templates.{module_name}")
    model = getattr(module, class_name)

    assert model.model_fields["semantic_id"].default == GENERATOR["extract_semantic_id"](source)
    # The version is the template's administration, else the one its semanticId ends in (…/1/1/Submodel).
    administration = source.get("administration") or {}
    version = re.search(r"/(\d+)/(\d+)(?:/Submodel)?$", model.model_fields["semantic_id"].default)
    expected = ((administration["version"], administration["revision"]) if administration.get("version")
                else version.groups())
    assert (model.VERSION, model.REVISION) == expected
    assert f"Source: {relative_path}" in module.__doc__


def test_latest_nameplate_retains_the_fork_address_dropin():
    assert {"Street", "Zipcode", "CityTown", "NationalCode", "AddressOfAdditionalLink"} <= (
        AddressInformation.model_fields.keys()
    )
    relative_path = next(path for path in GENERATOR["TEMPLATES"] if path.startswith("Digital nameplate/"))
    source = json.loads((Path(GENERATOR["TEMPLATE_ROOT"]) / relative_path).read_text())
    address = next(
        child for child in source["submodels"][0]["submodelElements"]
        if child["idShort"] == "AddressInformation"
    )
    assert "value" in address
    assert "submodelElements" not in address


def test_aid_12_exposes_new_protocols_and_endpoint_metadata():
    assert AssetInterfacesDescription.model_fields["semantic_id"].default.endswith("/1/2/Submodel")
    assert {"InterfaceTemplateForCAN", "InterfaceTemplateForSNMP"} <= (
        AssetInterfacesDescription.model_fields.keys()
    )
    assert "protocolVersion" in EndpointMetadata.model_fields
    assert not EndpointMetadata.model_fields["base"].is_required()


@pytest.mark.parametrize("protocol", ["CAN", "SNMP"])
def test_new_protocol_interfaces_are_exported(protocol):
    from aas_model.testing import _endpoint
    from aas_pydantic.submodel_templates import asset_interfaces_description as aid

    family = f"InterfaceTemplateFor{protocol}"
    interface = getattr(aid, family)(
        title=aid.Title(value=protocol),
        EndpointMetadata=_endpoint(f"{protocol.lower()}://example.test"),
        InteractionMetadata=aid.InteractionMetadata(),
    )
    interface.EndpointMetadata.protocolVersion = aid.ProtocolVersion(value="1")
    submodel = DmpAssetInterfacesDescription(id_short="AID", **{family: {"native": interface}})

    native = element(_roundtrip(submodel), "native")

    assert value(native, "EndpointMetadata", "protocolVersion") == "1"
    assert [r["keys"][0]["value"] for r in native.get("supplementalSemanticIds", [])] \
        == interface.supplemental_semantic_ids


def test_enum_constraints_survive_and_are_exported():
    schema = {
        "type": "object",
        "properties": {
            "state": {"type": "string", "enum": ["IDLE", "RUNNING"]},
            "reasons": {"type": "array", "items": {
                "type": "string", "enum": ["WAIT", "READY"],
            }},
        },
    }
    datapoint = datapoint_from_schema(schema)

    class PayloadSchema(Submodel):
        payload: PropertyDefinition

    submodel = PayloadSchema(id_short="PayloadSchema", payload=datapoint)
    restored = schema_from_datapoint(datapoint)
    assert restored["properties"]["state"]["enum"] == ["IDLE", "RUNNING"]
    assert restored["properties"]["reasons"]["items"]["enum"] == ["WAIT", "READY"]
    payload = element(_roundtrip(submodel), "payload", "properties")
    assert [m["value"] for m in element(payload, "state", "enum")["value"]] == ["IDLE", "RUNNING"]
    assert [m["value"] for m in element(payload, "reasons", "items", "enum")["value"]] == ["WAIT", "READY"]


@pytest.mark.parametrize("family, obsolete, corrected, minimum_count", [
    ("MTP", '"type": "Cardinality"', '"type": "SMT/Cardinality"', 13),
    (
        "Technical Data for Automated Guided Vehicles",
        "https://admin-shell.io/SubmodelTemplates/SMT/Cardinality/1/0",
        "https://admin-shell.io/SubmodelTemplates/Cardinality/1/0",
        92,
    ),
])
def test_latest_auxiliary_templates_retain_prior_cardinality_fixes(
    family, obsolete, corrected, minimum_count,
):
    folder = Path(GENERATOR["TEMPLATE_ROOT"]) / family / "1" / "0" / "2"
    paths = sorted(folder.glob("*.json"))
    assert len(paths) == 2
    documents = []
    for path in paths:
        source = path.read_text(encoding="utf-8")
        assert obsolete not in source, path.name
        assert source.count(corrected) >= minimum_count, path.name
        documents.append(json.loads(source))
    assert documents[0] == documents[1]
