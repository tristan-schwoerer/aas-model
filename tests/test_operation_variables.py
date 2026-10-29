"""Skill Operation variables are any SubmodelElement (AAS ``OperationVariable.value``),
and each may be marked Optional; both survive the AAS JSON export and its parse."""

from __future__ import annotations

import json

from aas_pydantic import Property, SubmodelElementCollection, SubmodelElementList
from basyx.aas.adapter.json import json_serialization

from aas_model.builder import build_from_model
from aas_model.resource_instances import RESOURCE_FACTORIES
from aas_model.submodel_templates.control_component_instance import (
    OPERATION_VARIABLE_OPTIONAL, OptionalVariable,
)


class Result(SubmodelElementCollection):
    State: Property = Property(id_short="State")
    Detail: Property = Property(id_short="Detail", qualifiers=[OptionalVariable()])


def is_optional(element) -> bool:
    return any(q.semantic_id == OPERATION_VARIABLE_OPTIONAL and str(q.value).lower() == "true"
               for q in element.qualifiers)


def _exported_cci(resource) -> dict:
    doc = json.loads(json_serialization.object_store_to_json(build_from_model(resource)))
    return next(s for s in doc["submodels"] if s["idShort"] == "ControlComponentInstance")


def _operation(cci: dict, skill: str) -> dict:
    skills = next(e for e in cci["submodelElements"] if e["idShort"] == "Skills")
    return next(e for e in next(s for s in skills["value"] if s["idShort"] == skill)["value"]
                if e["modelType"] == "Operation")


def _optional(element: dict) -> bool:
    return any(q["semanticId"]["keys"][0]["value"] == OPERATION_VARIABLE_OPTIONAL and q["value"] == "true"
               for q in element.get("qualifiers", []))


def test_a_variable_is_marked_optional_by_its_qualifier():
    assert is_optional(Property(id_short="Outcome", qualifiers=[OptionalVariable()]))
    assert not is_optional(Property(id_short="State"))


def test_collection_and_list_variables_export_with_their_optional_marks():
    resource = RESOURCE_FACTORIES["imaDispensing"]()
    operation = resource.control_component_instance.Skills.Skill["Dispensing"].operation
    operation.output_variable = [*operation.output_variable, Result(id_short="Result"),
                                 SubmodelElementList(id_short="Samples", type_value_list_element="Property",
                                                     value_type_list_element="xs:int", qualifiers=[OptionalVariable()])]
    cci = _exported_cci(resource)
    outputs = {v["value"]["idShort"]: v["value"] for v in _operation(cci, "Dispensing")["outputVariables"]}
    assert outputs["Result"]["modelType"] == "SubmodelElementCollection"
    assert outputs["Samples"]["modelType"] == "SubmodelElementList"
    members = {m["idShort"]: m for m in outputs["Result"]["value"]}
    assert _optional(members["Detail"]) and not _optional(members["State"])
    assert _optional(outputs["Samples"]) and _optional(outputs["Outcome"]) and not _optional(outputs["State"])


def test_operation_aimc_uses_explicit_input_and_output_variable_references():
    resource = RESOURCE_FACTORIES["imaDispensing"]()
    operation = resource.control_component_instance.Skills.Skill["Dispensing"].operation
    mapping = next(mc for mc in resource.asset_interfaces_mapping_configuration
                   .MappingConfigurations.value if mc.id_short == "Dispensing")

    source_ids = [source.SourceId.value for source in mapping.Sources.value]
    declared_inputs = {variable.id_short for variable in (
        *operation.input_variable, *operation.in_output_variable,
    )}
    assert set(source_ids) == declared_inputs == {"Uuid", "Volume"}
    for source, variable in zip(mapping.Sources.value, source_ids):
        assert [(key.type_, key.value) for key in source.Source.value.key[-2:]] == [
            ("Operation", "operation"), ("Property", variable),
        ]

    sink_ids = [sink.SinkId.value for sink in mapping.ResponseSinks.value]
    declared_outputs = {variable.id_short for variable in (
        *operation.output_variable, *operation.in_output_variable,
    )}
    assert set(sink_ids) == declared_outputs == {"Uuid", "State", "Outcome"}
    for sink in mapping.ResponseSinks.value:
        assert [(key.type_, key.value) for key in sink.Sink.value.key[-2:]] == [
            ("Operation", "operation"), ("Property", sink.SinkId.value),
        ]
    assert b"Outputs" not in mapping.ResponseTransformation.value
    assert b"Uuid = sources.Uuid" in mapping.Transformation.value
    assert b"Volume = sources.Volume" in mapping.Transformation.value
