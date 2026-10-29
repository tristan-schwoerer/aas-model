"""The pydantic → BaSyx conversion (convert_pydantic_model): what an authored model becomes in the AAS."""

from __future__ import annotations

import json
from typing import Dict, List

import pytest
from basyx.aas import model
from basyx.aas.adapter.json import json_serialization
from pydantic import Field

from aas_pydantic import (
    AAS, ExternalReference, Key, Operation, Property, Qualifier, Range, ReferenceElement,
    Submodel, SubmodelElementCollection, SubmodelElementList, convert_model_to_aas,
)
from aas_pydantic.convert_pydantic_model import convert_model_to_submodel
from aas_model import build_from_model
from aas_model.resource_instances import RESOURCE_FACTORIES


def _element(submodel: model.Submodel, id_short: str):
    return submodel.get_referable(id_short)


def _markers(element) -> list[tuple[str, str, str]]:
    return [(spec.data_specification.key[0].value, spec.data_specification_content.preferred_name.get("en"),
             spec.data_specification_content.value) for spec in element.embedded_data_specifications]


def test_a_submodel_keeps_its_qualifiers_and_supplemental_semantic_ids():
    sm = convert_model_to_submodel(Submodel(
        id_short="SM", id="urn:sm", supplemental_semantic_ids=["urn:extra"],
        qualifiers=[Qualifier(type_="t", value_type="xs:string", value="v")],
    ))
    assert [q.type for q in sm.qualifier] == ["t"]
    assert [r.key[0].value for r in sm.supplemental_semantic_id] == ["urn:extra"]


@pytest.mark.parametrize("name", sorted(RESOURCE_FACTORIES))
def test_building_a_resource_twice_gives_the_same_aas(name):
    resource = RESOURCE_FACTORIES[name]()
    first = json_serialization.object_store_to_json(build_from_model(resource))
    assert json_serialization.object_store_to_json(build_from_model(resource)) == first


def test_an_absent_optional_element_has_no_marker():
    class Holder(Submodel):
        present: Property = Property(value="x")
        absent: ReferenceElement | None = None

    markers = _markers(convert_model_to_submodel(Holder(id_short="Holder", id="urn:holder")))
    assert ("present", "attribute", "present") in markers
    assert not [m for m in markers if m[2] == "absent" and m[1] == "attribute"]


def test_a_default_factory_field_has_no_default_marker():
    class Holder(Submodel):
        names: List[Property] = Field(default_factory=list)

    holder = Holder(id_short="Holder", id="urn:holder", names=[Property(value="a")])
    assert not [m for m in _markers(convert_model_to_submodel(holder)) if m[2] == "PydanticUndefined"]


def test_the_shell_names_its_submodels_by_their_id():
    class Shell(AAS):
        first: Submodel
        second: Submodel

    shell = Shell(id_short="Shell", id="urn:shell",
                  first=Submodel(id_short="Same", id="urn:sm1"), second=Submodel(id_short="Same", id="urn:sm2"))
    store = convert_model_to_aas(shell)
    assert {o.id for o in store} == {"urn:shell", "urn:sm1", "urn:sm2"}
    aas = next(o for o in store if o.id == "urn:shell")
    assert {(key, value) for key, kind, value in _markers(aas) if kind == "attribute"} == {
        ("urn:sm1", "first"), ("urn:sm2", "second")}
    # No asset type is invented for a shell that declares none.
    assert aas.asset_information.asset_type is None


class Item(SubmodelElementCollection):
    semantic_id: str = "urn:item"
    supplemental_semantic_ids: List[str] = ["urn:item-extra"]
    note: Property = Property(value="x")


def test_list_items_keep_their_shared_semantic_id_and_supplementals():
    class Holder(Submodel):
        items: SubmodelElementList = SubmodelElementList(value=[Item(), Item()])

    store = model.DictIdentifiableStore([convert_model_to_submodel(Holder(id_short="Holder", id="urn:holder"))])
    [items] = json.loads(json_serialization.object_store_to_json(store))["submodels"][0]["submodelElements"]
    for item in items["value"]:
        assert "idShort" not in item
        assert item["semanticId"]["keys"][0]["value"] == "urn:item"
        assert [r["keys"][0]["value"] for r in item["supplementalSemanticIds"]] == ["urn:item-extra"]


def test_list_items_with_differing_semantic_ids_are_an_error():
    class Other(SubmodelElementCollection):
        semantic_id: str = "urn:other"
        note: Property = Property(value="y")

    class Holder(Submodel):
        items: SubmodelElementList = SubmodelElementList(value=[Item(), Other()])

    with pytest.raises(ValueError, match="AASd-107/114"):
        convert_model_to_submodel(Holder(id_short="Holder", id="urn:holder"))


def test_a_list_of_reference_elements_declares_its_item_type():
    reference = ExternalReference(key=(Key(type_="GlobalReference", value="urn:x"),))

    class Holder(Submodel):
        refs: SubmodelElementList = SubmodelElementList(value=[ReferenceElement(value=reference)])

    refs = _element(convert_model_to_submodel(Holder(id_short="Holder", id="urn:holder")), "refs")
    assert refs.type_value_list_element is model.ReferenceElement
    assert refs.value_type_list_element is None


@pytest.mark.parametrize("value_type, low, high, expected", [
    ("xs:boolean", "false", "true", (False, True)),
    ("xs:int", "1", "5", (1, 5)),
    ("xs:double", 0.5, "2.5", (0.5, 2.5)),
    ("xs:gYear", "2020", "2030", None),
])
def test_range_bounds_are_values_of_its_value_type(value_type, low, high, expected):
    class Holder(Submodel):
        span: Range = Range(value_type=value_type, min=low, max=high)

    span = _element(convert_model_to_submodel(Holder(id_short="Holder", id="urn:holder")), "span")
    if expected is not None:
        assert (span.min, span.max) == expected
    assert span.value_type is model.datatypes.XSD_TYPE_CLASSES[value_type]


def test_an_operation_leaves_out_a_variable_without_value():
    class Holder(Submodel):
        op: Operation = Operation(input_variable=[ReferenceElement(id_short="Empty"), Property(id_short="P")])

    op = _element(convert_model_to_submodel(Holder(id_short="Holder", id="urn:holder")), "op")
    assert [v.id_short for v in op.input_variable] == ["P"]
    assert ("op", "class", "Operation") in _markers(op)


def test_a_key_without_type_in_an_external_reference_is_a_global_reference():
    class Holder(Submodel):
        ref: ReferenceElement = ReferenceElement(value=ExternalReference(key=(Key(value="urn:x"),)))

    ref = _element(convert_model_to_submodel(Holder(id_short="Holder", id="urn:holder")), "ref")
    assert ref.value.key[0].type is model.KeyTypes.GLOBAL_REFERENCE


def test_a_typed_qualifier_without_value_has_none():
    sm = convert_model_to_submodel(Submodel(
        id_short="SM", id="urn:sm", qualifiers=[Qualifier(type_="limit", value_type="xs:int", value="")]))
    assert [q.value for q in sm.qualifier] == [None]


def test_a_property_value_that_does_not_parse_is_an_error():
    class Holder(Submodel):
        count: Property = Property(value_type="xs:int", value="many")

    with pytest.raises(ValueError, match="'many' is not a xs:int"):
        convert_model_to_submodel(Holder(id_short="Holder", id="urn:holder"))


def test_an_identifiable_given_only_its_id_keeps_its_class_id_short():
    class Named(Submodel):
        id_short: str = "Named"

    assert Named(id="urn:named").id_short == "Named"


def test_temporary_list_item_names_never_reach_the_json():
    class Holder(Submodel):
        items: SubmodelElementList = SubmodelElementList(value=[Item(id_short="First")])
        nested: Dict[str, SubmodelElementCollection] = {}

    store = model.DictIdentifiableStore([convert_model_to_submodel(Holder(id_short="Holder", id="urn:holder"))])
    from aas_pydantic.convert_util import strip_temp_id_short_attributes
    strip_temp_id_short_attributes(store)
    assert "temp_id_short_attribute" not in json.dumps(json.loads(json_serialization.object_store_to_json(store)))
