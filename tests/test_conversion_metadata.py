import os
from pathlib import Path
import subprocess
import sys
from typing import ClassVar

from basyx.aas import model
from basyx.aas.model import datatypes

from aas_pydantic import aas_model
from aas_pydantic.convert_pydantic_model import create_submodel_element


class PropertyList(aas_model.SubmodelElementList):
    item_type: ClassVar = aas_model.Property


def test_qualifier_supplemental_and_referred_semantic_ids_are_written():
    element = aas_model.ReferenceElement(
        id_short="Reference",
        value=aas_model.ModelReference(key=(aas_model.Key(type_="Submodel", value="urn:submodel"),),
                                       referred_semantic_id="urn:referred-semantic"),
        qualifiers=[aas_model.Qualifier(type_="constraint", value_type="xs:string", value="active",
                                        value_id="urn:value-id", semantic_id="urn:qualifier-semantic")],
        supplemental_semantic_ids=["urn:supplemental"],
    )
    built = create_submodel_element("Reference", element)
    assert built.supplemental_semantic_id[0].key[0].value == "urn:supplemental"
    qualifier = next(iter(built.qualifier))
    assert qualifier.value_id.key[0].value == "urn:value-id"
    assert qualifier.semantic_id.key[0].value == "urn:qualifier-semantic"
    assert built.value.referred_semantic_id.key[0].value == "urn:referred-semantic"


def test_submodel_element_list_metadata_is_written():
    entries = PropertyList(
        id_short="Entries", value_type_list_element="xs:int", semantic_id_list_element="urn:item-semantic",
        order_relevant=False, supplemental_semantic_ids=["urn:list-supplemental"],
        value=[aas_model.Property(value_type="xs:int", value="7", semantic_id="urn:item-semantic")],
    )
    built = create_submodel_element("Entries", entries)
    assert built.semantic_id_list_element.key[0].value == "urn:item-semantic"
    assert built.value_type_list_element is datatypes.Int
    assert built.type_value_list_element is model.Property
    assert built.order_relevant is False
    assert built.supplemental_semantic_id[0].key[0].value == "urn:list-supplemental"


def test_file_and_blob_qualifiers_and_supplemental_ids_are_written():
    for element in (
        aas_model.File(id_short="File", content_type="text/plain", value="data.txt",
                       qualifiers=[aas_model.Qualifier(type_="format", value_type="xs:string", value="raw")],
                       supplemental_semantic_ids=["urn:file-supp"]),
        aas_model.Blob(id_short="Blob", content_type="application/octet-stream", value=b"data",
                       qualifiers=[aas_model.Qualifier(type_="format", value_type="xs:string", value="raw")],
                       supplemental_semantic_ids=["urn:blob-supp"]),
    ):
        built = create_submodel_element(element.id_short, element)
        assert next(iter(built.qualifier)).value == "raw"
        assert built.supplemental_semantic_id[0].key[0].value == element.supplemental_semantic_ids[0]


def test_validation_is_not_disabled_by_optimized_python():
    script = """
from pydantic import ValidationError
from aas_pydantic import Key, ModelReference, Property

for constructor in (
    lambda: Property(id_short=""),
    lambda: ModelReference(key=(Key(type_="Property", value="urn:item"),)),
):
    try:
        constructor()
    except ValidationError:
        pass
    else:
        raise RuntimeError("invalid input was accepted")
"""
    result = subprocess.run(
        [sys.executable, "-O", "-c", script],
        capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
    )
    assert result.returncode == 0, result.stderr
