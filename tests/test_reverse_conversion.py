"""An AAS read back into pydantic (convert_store_to_model) and built again is the AAS it was: back and forth, with
the class markers telling the classes."""

from __future__ import annotations

import io
import json

import pytest
from basyx.aas import model
from basyx.aas.adapter.json import json_serialization, read_aas_json_file

from aas_model import Resource, build_from_model
from aas_model.resource_instances import RESOURCE_FACTORIES
from aas_pydantic import convert_store_to_model
from aas_pydantic.convert_util import strip_temp_id_short_attributes


def _published(resource) -> str:
    store = build_from_model(resource)
    strip_temp_id_short_attributes(store)
    return json_serialization.object_store_to_json(store)


def _document(text: str) -> dict:
    document = json.loads(text)
    # The shell's submodel references are a set in BaSyx.
    for shell in document.get("assetAdministrationShells", []):
        shell["submodels"].sort(key=lambda reference: reference["keys"][0]["value"])
    return document


@pytest.mark.parametrize("name", sorted(RESOURCE_FACTORIES))
@pytest.mark.parametrize("as_resource", [False, True], ids=["own type", "Resource"])
def test_a_published_resource_read_back_builds_the_same_aas(name, as_resource):
    resource = RESOURCE_FACTORIES[name]()
    published = _published(resource)
    store = read_aas_json_file(io.StringIO(published), failsafe=False)
    restored = convert_store_to_model(store, Resource if as_resource else type(resource))
    # Read as a Resource, it is the class its marker names.
    assert type(restored) is type(resource)
    assert _document(_published(restored)) == _document(published)


def test_submodels_are_read_back_as_the_classes_their_markers_name():
    resource = RESOURCE_FACTORIES["cytivaCapping"]()
    store = read_aas_json_file(io.StringIO(_published(resource)), failsafe=False)
    restored = convert_store_to_model(store, Resource)
    for field in ("asset_interfaces_description", "control_component_instance", "variables",
                  "asset_interfaces_mapping_configuration"):
        assert type(getattr(restored, field)) is type(getattr(resource, field)), field
    assert restored.specific_asset_ids == resource.specific_asset_ids
    assert restored.asset_type == resource.asset_type


def test_a_list_item_is_named_by_its_class_marker():
    resource = RESOURCE_FACTORIES["syntegonStoppering"]()
    store = read_aas_json_file(io.StringIO(_published(resource)), failsafe=False)
    restored = convert_store_to_model(store, type(resource))
    names = [m.id_short for m in restored.asset_interfaces_mapping_configuration.MappingConfigurations.value]
    assert names == [m.id_short for m in resource.asset_interfaces_mapping_configuration.MappingConfigurations.value]


def test_a_store_without_the_aas_is_an_error():
    with pytest.raises(ValueError, match="expected one AAS"):
        convert_store_to_model(model.DictIdentifiableStore(), Resource)


def test_a_named_list_item_is_shown_by_its_name_and_read_back_without_it():
    resource = RESOURCE_FACTORIES["syntegonStoppering"]()
    document = json.loads(_published(resource))
    aimc = next(s for s in document["submodels"] if s["idShort"] == "AssetInterfacesMappingConfiguration")
    [mappings] = aimc["submodelElements"]
    names = [m.id_short for m in resource.asset_interfaces_mapping_configuration.MappingConfigurations.value]
    assert [item["displayName"] for item in mappings["value"]] == [[{"language": "en", "text": n}] for n in names]
    assert all("idShort" not in item for item in mappings["value"])
    restored = convert_store_to_model(read_aas_json_file(io.StringIO(json.dumps(document)), failsafe=False),
                                      type(resource))
    assert {m.display_name for m in restored.asset_interfaces_mapping_configuration.MappingConfigurations.value} \
        == {None}
