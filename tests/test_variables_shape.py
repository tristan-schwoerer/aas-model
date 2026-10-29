"""Variables / Parameters container shape.

A variable or parameter is a **plain Property** by default; it is only wrapped
in an SMC group when it genuinely combines several children. Both forms live in
the same map, so the AIMC sink reference addresses the element it means.

These tests drive the production path (Python Resource -> exported JSON ->
Pydantic -> BaSyx), without merging any JSON overrides into defaults.
"""

from __future__ import annotations

import pytest

from aas_json import parse_submodel_dict
from aas_model import Resource, build_from_model
from aas_model.submodel_templates.parameters import ParamProp, ParameterItem, ResourceParameters
from aas_model.submodel_templates.variables import (
    VariableItem, VariableProp, Variables,
)

VAR_SEMANTIC_ID = VariableProp.model_fields["semantic_id"].default
VAR_ITEM_SEMANTIC_ID = VariableItem.model_fields["semantic_id"].default


def _publish(**submodels):
    """Export an authored Resource and build it as the registration service does."""
    asset = Resource(id_short="shapeTestAAS", **submodels)
    restored = Resource.model_validate_json(asset.model_dump_json())
    return {sm.id_short: sm for sm in build_from_model(restored)}


def _variables(variables: dict) -> dict:
    return _publish(variables=Variables(id_short="Variables", variable=variables))


def test_leaf_variable_is_a_plain_property_not_a_collection():
    sm = _variables({"PackMLState": VariableProp(
        value="IDLE", supplemental_semantic_ids=["urn:x"]
    )})["Variables"]
    element = next(e for e in sm.submodel_element if e.id_short == "PackMLState")
    assert type(element).__name__ == "Property"
    assert element.value == "IDLE"


def test_a_grouped_variable_is_still_a_collection():
    sm = _variables({"Grouped": VariableItem(value={
        "Inner": VariableProp(value="B"),
    })})["Variables"]
    grouped = next(e for e in sm.submodel_element if e.id_short == "Grouped")
    assert type(grouped).__name__ == "SubmodelElementCollection"
    assert [c.id_short for c in grouped.value] == ["Inner"]


def test_flat_and_grouped_entries_coexist_in_one_map():
    sm = _variables({
        "Alpha": VariableProp(value="IDLE"),
        "Grouped": VariableItem(value={"Inner": VariableProp(value="B")}),
    })["Variables"]
    by_type = {type(e).__name__: e.id_short for e in sm.submodel_element}
    assert by_type["Property"] == "Alpha"
    assert by_type["SubmodelElementCollection"] == "Grouped"


def test_leaf_parameter_is_a_plain_property_and_a_group_stays_a_collection():
    sm = _publish(parameters=ResourceParameters(id_short="Parameters", parameter={
        "Leaf": ParamProp(value="1.0"),
        "Spot": ParameterItem(value={"x": ParamProp(value="2.0")}),
    }))["Parameters"]
    by_id = {e.id_short: type(e).__name__ for e in sm.submodel_element}
    assert set(by_id) == {"Leaf", "Spot"}
    assert by_id["Leaf"] == "Property"
    assert by_id["Spot"] == "SubmodelElementCollection"


def test_legacy_single_child_wrapper_is_rejected_loudly():
    """The old shape is a modelling mistake now; it must fail rather than be
    silently coerced into an empty Property."""
    with pytest.raises(Exception):
        _variables({"PackMLStateTimer": {"variable": {"value": ""}}})


def test_variable_submodel_round_trips_through_rest_json():
    rest = {
        "modelType": "Submodel", "id": "urn:sm:Variables", "idShort": "Variables",
        "submodelElements": [
            {"modelType": "Property", "idShort": "PackMLState", "valueType": "xs:string",
             "value": "IDLE",
             "semanticId": {"type": "ExternalReference", "keys": [
                 {"type": "GlobalReference", "value": VAR_SEMANTIC_ID}]}},
            {"modelType": "SubmodelElementCollection", "idShort": "Grouped",
             "value": [{"modelType": "Property", "idShort": "Inner",
                        "valueType": "xs:string", "value": "B",
                        "semanticId": {"type": "ExternalReference", "keys": [
                            {"type": "GlobalReference", "value": VAR_SEMANTIC_ID}]}}],
             "semanticId": {"type": "ExternalReference", "keys": [
                 {"type": "GlobalReference", "value": VAR_ITEM_SEMANTIC_ID}]}},
        ],
    }
    back = parse_submodel_dict(rest, Variables)
    assert {k: type(v).__name__ for k, v in back.variable.items()} == {
        "PackMLState": "VariableProp", "Grouped": "VariableItem"}
    assert back.variable["PackMLState"].value == "IDLE"
    assert {k: type(v).__name__ for k, v in back.variable["Grouped"].value.items()} == {
        "Inner": "VariableProp"}


def test_resource_defaults_author_flat_variables():
    from aas_model.resource_template import MqttOperationalStation as Station
    asset = Station(id_short="shapeTestAAS")
    assert {k: type(v).__name__ for k, v in asset.variables.variable.items()} == {
        "PackMLState": "VariableProp", "OccupationState": "VariableProp"}
    # Location is a real group, so it stays a collection
    assert isinstance(asset.parameters.parameter["Location"], ParameterItem)
