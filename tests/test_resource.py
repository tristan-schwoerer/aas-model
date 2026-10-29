"""Python authoring -> Resource config JSON -> BaSyx AAS."""

import json
import re

import pytest
from basyx.aas import model
from basyx.aas.adapter.json import json_serialization
from pydantic import ValidationError

from aas_model import Resource, ResourceTypeAAS, build_from_model, inject_ids
from aas_model.constants import BASE_URL
from aas_model.submodel_templates.parameters import Position
from aas_model.resource_template import MqttOperationalStation as Station
from aas_model.resource_instances.stopperingModule import syntegon_stoppering
from aas_model.submodel_templates.control_component_instance import ExtendedSkill, SkillOperation
from aas_model.submodel_templates.variables import VariableProp
from aas_pydantic import Capability, Property, Submodel
from aas_pydantic.submodel_templates.capability_description import (
    CapabilityContainer, CapabilityDescription, CapabilitySet,
)
from aas_pydantic.convert_util import strip_temp_id_short_attributes
from aas_model.constants import BASE_URL
from aas_model.invocation_authoring import operation_path


def _document(store):
    strip_temp_id_short_attributes(store)
    document = json.loads(json_serialization.object_store_to_json(store))
    # Registration imports the base Resource schema, intentionally erasing the
    # Python subclass name stored in authoring-only IEC 61360 metadata.
    for referable in (*document.get("assetAdministrationShells", []), *document.get("submodels", [])):
        for specification in referable.get("embeddedDataSpecifications", []):
            content = specification.get("dataSpecificationContent", {})
            if content.get("preferredName") == [{"language": "en", "text": "class"}]:
                content["value"] = "<authoring-class>"

    def normalize(value):
        # The fork generates random data-specification IDs; shell references
        # and top-level submodels are unordered collections in BaSyx.
        if isinstance(value, dict):
            result = {key: normalize(child) for key, child in value.items()}
            for key in ("submodels", "submodel"):
                if isinstance(result.get(key), list):
                    result[key].sort(key=lambda child: json.dumps(child, sort_keys=True))
            return result
        if isinstance(value, list):
            return [normalize(child) for child in value]
        if isinstance(value, str) and re.fullmatch(r"[0-9a-f]{32}", value):
            return "generated-id"
        return value

    return normalize(document)


def test_resource_keeps_existing_public_type_name():
    assert ResourceTypeAAS is Resource


def test_resource_instance_package_exports_the_module_factory():
    from aas_model.resource_instances import syntegon_stoppering as package_factory

    assert package_factory is syntegon_stoppering


def test_resource_defaults_are_independent_and_their_invocation_urls_resolve_when_built():
    first = Station(id_short="First")
    second = Station(id_short="Second")
    first.variables.variable["PackMLState"].value = "IDLE"
    first.parameters.parameter["Location"].x.parameter.value = 100.0

    assert second.variables.variable["PackMLState"].value == ""
    assert second.parameters.parameter["Location"].x.parameter.value == 480.0
    for resource in (first, second):
        resource = resource.model_copy(deep=True)
        inject_ids(resource)
        for name, skill in resource.control_component_instance.Skills.Skill.items():
            invocation = next(q for q in skill.operation.qualifiers if q.type_ == "invocationDelegation")
            assert invocation.value == "http://dmp:8080" + operation_path(
                f"{BASE_URL}/aas/{resource.id_short}/submodels/ControlComponentInstance", f"Skills.{name}.operation")


def test_resource_aid_defaults_populate_optional_mqtt_containers_and_round_trip():
    resource = Station(id_short="AIDContainers")
    interface = resource.asset_interfaces_description.InterfaceTemplateForMQTT["interface_mqtt"]
    interaction = interface.InteractionMetadata

    assert set(interaction.actions.property_name) == {"Halt", "Occupy", "Release"}
    assert set(interaction.properties.property_name) == {"StationState"}

    restored = Resource.model_validate_json(resource.model_dump_json())
    restored_interaction = restored.asset_interfaces_description.InterfaceTemplateForMQTT[
        "interface_mqtt"
    ].InteractionMetadata
    assert set(restored_interaction.actions.property_name) == {"Halt", "Occupy", "Release"}
    assert set(restored_interaction.properties.property_name) == {"StationState"}


def test_resolving_one_resource_does_not_change_reference_defaults_for_the_next():
    first = Station(id_short="FirstIdentity")
    inject_ids(first)
    second = Station(id_short="SecondIdentity")
    native = second.control_component_instance.Skills.Skill["Halt"].interface_reference.value
    mapping = second.asset_interfaces_mapping_configuration.MappingConfigurations.value[0]

    assert native.key[0].value == "{aas_id}/submodels/AssetInterfacesDescription"
    assert mapping.Sources.value[0].Source.value.key[0].value == native.key[0].value
    assert mapping.Sinks.value[0].Sink.value.key[0].value == "{aas_id}/submodels/Variables"


@pytest.mark.parametrize("factory", [lambda: Station(id_short="Generic"), syntegon_stoppering])
def test_complete_resource_json_round_trip(factory):
    resource = factory()
    resource.parameters.parameter["Location"].x.parameter.value = 123.5
    resource.parameters.parameter["Location"].y.parameter.value = 456.5
    resource.parameters.parameter["Location"].yaw.parameter.value = 90.0
    encoded = resource.model_dump_json()
    restored = Resource.model_validate_json(encoded)

    assert restored.model_dump(mode="json") == json.loads(encoded)
    assert isinstance(restored.parameters.parameter["Location"], Position)
    assert restored.parameters.parameter["Location"].x.parameter.value == 123.5
    assert restored.parameters.parameter["Location"].y.parameter.value == 456.5
    assert restored.parameters.parameter["Location"].yaw.parameter.value == 90.0
    assert isinstance(restored.variables.variable["PackMLState"], VariableProp)
    assert isinstance(restored.capability_description, CapabilityDescription)
    halt = restored.control_component_instance.Skills.Skill["Halt"]
    assert isinstance(halt, ExtendedSkill)
    assert isinstance(halt.operation, SkillOperation)


def test_python_resource_and_restored_config_build_the_same_aas():
    resource = syntegon_stoppering()
    restored = Resource.model_validate_json(resource.model_dump_json())

    assert _document(build_from_model(resource)) == _document(build_from_model(restored))


def test_build_from_model_resolves_references_without_mutating_resource():
    resource = syntegon_stoppering()
    before = resource.model_dump_json()
    store = build_from_model(resource)
    shell = next(obj for obj in store if isinstance(obj, model.AssetAdministrationShell))

    assert resource.model_dump_json() == before
    assert shell.id == f"{BASE_URL}/aas/{resource.id_short}"
    assert len(shell.submodel) == 8
    assert all(reference.resolve(store) is not None for reference in shell.submodel)
    submodels = {obj.id_short: obj for obj in store if isinstance(obj, model.Submodel)}
    assert "CapabilityDescription" in submodels
    cci = submodels["ControlComponentInstance"]
    skills = next(element for element in cci.submodel_element if element.id_short == "Skills")
    stoppering = next(element for element in skills.value if element.id_short == "Stoppering")
    native = next(element for element in stoppering.value if element.id_short == "interface_reference")
    assert native.value.resolve(store).id_short == "Stoppering"


def test_json_import_and_model_build_preserve_authored_container_structure():
    resource = Resource(id_short="ExactStructure")
    resource.variables.variable = {"Custom": VariableProp(id_short="Custom", value="READY")}
    resource.parameters.parameter = {}
    restored = Resource.model_validate_json(resource.model_dump_json())
    store = build_from_model(restored)
    submodels = {obj.id_short: obj for obj in store if isinstance(obj, model.Submodel)}

    assert set(restored.variables.variable) == {"Custom"}
    assert restored.parameters.parameter == {}
    assert {element.id_short for element in submodels["Variables"].submodel_element} == {"Custom"}
    assert not submodels["Parameters"].submodel_element


def test_pydantic_dict_and_json_loading_build_the_same_aas():
    resource = syntegon_stoppering()
    encoded = resource.model_dump_json()
    expected = _document(build_from_model(resource))

    assert _document(build_from_model(Resource.model_validate(json.loads(encoded)))) == expected
    assert _document(build_from_model(Resource.model_validate_json(encoded))) == expected


@pytest.mark.parametrize("source", ["dict", "file"])
def test_pydantic_loading_preserves_empty_containers_without_default_overlay(source, tmp_path):
    resource = syntegon_stoppering()
    resource.variables.variable.clear()
    resource.variables.State = None
    resource.variables.Log = None
    resource.parameters.parameter.clear()
    resource.asset_interfaces_description.InterfaceTemplateForMQTT.clear()
    resource.control_component_instance.Skills.Skill.clear()
    resource.control_component_instance.Endpoints.Endpoint.clear()
    resource.asset_interfaces_mapping_configuration.MappingConfigurations.value.clear()
    encoded = resource.model_dump_json()
    data = json.loads(encoded)

    if source == "dict":
        restored = Resource.model_validate(data)
    else:
        path = tmp_path / "resource.json"
        path.write_text(encoded, encoding="utf-8")
        restored = Resource.model_validate_json(path.read_text(encoding="utf-8"))
        assert path.read_text(encoding="utf-8") == encoded
    store = build_from_model(restored)

    submodels = {obj.id_short: obj for obj in store if isinstance(obj, model.Submodel)}
    assert not submodels["Variables"].submodel_element
    assert not submodels["Parameters"].submodel_element
    assert not submodels["AssetInterfacesDescription"].submodel_element
    cci = {child.id_short: child for child in submodels["ControlComponentInstance"].submodel_element}
    assert not cci["Skills"].value
    assert not cci["Endpoints"].value
    mappings = next(iter(submodels["AssetInterfacesMappingConfiguration"].submodel_element))
    assert not mappings.value


def test_pydantic_rejects_invalid_exported_field_types():
    resource = Station(id_short="Invalid")
    resource.parameters.parameter["Location"].x.parameter.value = "not a float"

    with pytest.warns(UserWarning, match="Expected `float`"):
        encoded = resource.model_dump_json()
    with pytest.raises(ValidationError):
        Resource.model_validate_json(encoded)


def test_pydantic_import_preserves_explicitly_empty_invocation_qualifiers():
    resource = syntegon_stoppering()
    data = json.loads(resource.model_dump_json())
    data["control_component_instance"]["Skills"]["Skill"]["Halt"]["operation"]["qualifiers"] = []

    restored = Resource.model_validate_json(json.dumps(data))

    assert restored.control_component_instance.Skills.Skill["Halt"].operation.qualifiers == []


def test_build_from_model_keeps_resource_subclass_fields():
    class Diagnostics(Submodel):
        status: Property = Property(value="READY")

    class Instrument(Resource):
        diagnostics: Diagnostics

    resource = Instrument(id_short="Instrument", diagnostics=Diagnostics(id_short="Diagnostics"))
    restored = Instrument.model_validate_json(resource.model_dump_json())
    store = build_from_model(restored)
    diagnostics = next(obj for obj in store if obj.id_short == "Diagnostics")

    assert isinstance(diagnostics, model.Submodel)
    assert next(iter(diagnostics.submodel_element)).value == "READY"


def test_concrete_resources_are_fresh_instances():
    first = syntegon_stoppering()
    first.nameplate.SerialNumber.value = "changed"
    first.control_component_instance.Skills.Skill.clear()
    second = syntegon_stoppering()

    assert second.nameplate.SerialNumber.value == "SYN-SS-2024-001"
    assert set(second.control_component_instance.Skills.Skill) == {"Halt", "Occupy", "Release", "Stoppering"}


def test_build_from_model_does_not_revalidate_or_serialize_the_model(monkeypatch):
    resource = syntegon_stoppering()

    def unexpected_validation(*args, **kwargs):
        raise AssertionError("Building a typed model must not serialize or revalidate it")

    monkeypatch.setattr(Resource, "model_validate", unexpected_validation)
    monkeypatch.setattr(Resource, "model_dump", unexpected_validation)

    assert len(build_from_model(resource)) == 9


def test_resource_capability_description_defaults_are_independent():
    first = Resource(id_short="First")
    second = Resource(id_short="Second")
    first.capability_description.CapabilitySet["Processing"] = CapabilitySet(id_short="Processing")

    assert second.capability_description.CapabilitySet == {}
    assert CapabilityDescription(id_short="CapabilityDescription").id_short == "CapabilityDescription"


def test_authored_capability_survives_json_and_aas_construction():
    capabilities = CapabilityDescription(id_short="CapabilityDescription")
    capabilities.CapabilitySet["Processing"] = CapabilitySet(
        id_short="Processing",
        CapabilityContainer={"Stoppering": CapabilityContainer(
            id_short="Stoppering",
            Capability=Capability(id_short="Capability", semantic_id="urn:test:capability:stoppering"),
        )},
    )
    resource = Resource(id_short="CapableResource", capability_description=capabilities)
    encoded = resource.model_dump_json()
    restored = Resource.model_validate_json(encoded)
    store = build_from_model(restored)
    submodel = store.get_item(f"{BASE_URL}/aas/CapableResource/submodels/CapabilityDescription")

    assert restored.model_dump(mode="json") == json.loads(encoded)
    assert isinstance(restored.capability_description.CapabilitySet["Processing"], CapabilitySet)
    processing = next(iter(submodel.submodel_element))
    container = next(iter(processing.value))
    capability = next(child for child in container.value if isinstance(child, model.Capability))
    assert capability.semantic_id.key[0].value == "urn:test:capability:stoppering"
    assert resource.model_dump_json() == encoded


def test_resource_can_explicitly_omit_capability_description():
    resource = Resource(id_short="WithoutCapabilities", capability_description=None)
    restored = Resource.model_validate_json(resource.model_dump_json())
    store = build_from_model(restored)

    assert restored.capability_description is None
    assert all(obj.id_short != "CapabilityDescription" for obj in store)


def test_build_preserves_explicit_identifiers_outside_the_default_namespace():
    resource = Resource(id_short="ExternalIdentity", id="urn:aas:external")
    resource.nameplate.id = "urn:submodel:nameplate"
    restored = Resource.model_validate_json(resource.model_dump_json())
    store = build_from_model(restored)

    assert store.get_item("urn:aas:external").id_short == "ExternalIdentity"
    assert store.get_item("urn:submodel:nameplate").id_short == "Nameplate"
    assert store.get_item("urn:aas:external/submodels/Variables").id_short == "Variables"
