"""A class exported as an AAS submodel template (convert_model_to_submodel_template) is the template it was generated
from (idta_generate.py), and a class exported and generated back is the class again."""

from __future__ import annotations

import importlib
import importlib.util
import json
import re
import sys
import typing
from pathlib import Path

import pytest
from basyx.aas import model
from basyx.aas.adapter.json import json_serialization

from aas_pydantic import aas_model, convert_model_to_submodel_template
from template_shape import differences, shape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import idta_generate as generator  # noqa: E402

# What a generated class does not carry back to its template, by element path (an InterfaceTemplateFor* stands for
# every protocol):
KNOWN = (
    # A Capability is the author's concept: the field is the generic Capability, without the template's metadata.
    r"/CapabilityContainer/Capability: (semanticId|displayName|description) ",
    # A list of mixed example items (Range, Property, MLP) has no item type, so no example item.
    r"/PropertySubmodelList/\d+: missing",
    # A recursive definition is the class it repeats; a deeper copy's own description is not kept.
    r"/EntryNode/Node/Node: description ",
    r"/property_name/properties/property_name/properties: description ",
    r"/uriVariables/property_name/properties: description ",
    # One concept within a variant is one class: where a template defines it differently in two places, the
    # class holds both (the form's security takes the endpoint's description and item cardinality; BACnet's
    # schema property and data type members their other definition's terms).
    r"/forms/security: description ",
    r"/forms/security/0: qualifiers ",
    r"/properties/property_name/observable: extra",
    r"/uriVariables/property_name/properties/property_name: extra",
    r"/bacv_hasDataType/(.+/)?bacv_hasNamedMember(/0/bacv_hasDataType)?: (description|supplementalSemanticIds) ",
    # A copy the template leaves undescribed is described as its other copies are.
    r": (description|displayName) '' != ",
)


def _json(submodel) -> dict:
    return json.loads(json_serialization.object_store_to_json(model.DictIdentifiableStore([submodel])))[
        "submodels"][0]


@pytest.mark.parametrize("template", generator.TEMPLATES)
def test_a_generated_class_exports_as_its_template(template):
    source = json.loads((Path(generator.TEMPLATE_ROOT) / template).read_text(encoding="utf-8-sig"))["submodels"][0]
    name = generator.safe_name(source["idShort"])
    cls = getattr(importlib.import_module(f"aas_pydantic.submodel_templates.{generator.snake(name)}"), name)
    exported = _json(convert_model_to_submodel_template(cls, "urn:test:template"))
    unexpected = [d for d in differences(shape(source), shape(exported))
                  if not any(re.search(pattern, d) for pattern in KNOWN)]
    assert not unexpected, "\n".join(unexpected[:20])


def test_a_template_is_a_template():
    from aas_pydantic.submodel_templates.time_series import TimeSeries
    exported = convert_model_to_submodel_template(TimeSeries, "urn:test:template")
    assert exported.kind is model.ModellingKind.TEMPLATE
    assert (exported.administration.version, exported.administration.revision) == ("1", "1")
    document = _json(exported)
    assert "embeddedDataSpecifications" not in json.dumps(document)  # no class markers
    cardinalities = [q["value"] for e in document["submodelElements"] for q in e.get("qualifiers", [])
                     if q["type"] == "SMT/Cardinality"]
    assert cardinalities and all(c in ("One", "ZeroToOne", "ZeroToMany", "OneToMany") for c in cardinalities)


# ── Our extensions: exported and generated back ─────────────────────────────

def _structure(cls: type, seen=()) -> dict:
    """A class's elements as the template carries them: name, kind, cardinality, semanticId and value type."""
    if cls in seen:
        return {}
    result = {}
    for name, field in cls.model_fields.items():
        annotation = aas_model._resolve_annotation(aas_model._field_annotation(cls, name))
        origin = typing.get_origin(annotation)
        shape_ = "map" if origin is dict else "list" if origin is list else "single"
        element = aas_model._container_item_type(annotation) if shape_ != "single" else annotation
        if typing.get_origin(element) in (typing.Union, aas_model._UnionType):
            element = next((a for a in typing.get_args(element) if isinstance(a, type)), None)
        if not (isinstance(element, type) and issubclass(element, aas_model.SubmodelElement)) or name == "value":
            continue
        kind = next(b.__name__ for b in element.__mro__ if b.__module__ == aas_model.__name__)
        result[aas_model._aas_field_name(cls, name)] = (
            kind, shape_, field.is_required(), element.model_fields["semantic_id"].default,
            element.model_fields["value_type"].default if "value_type" in element.model_fields else "",
            _structure(element, seen + (cls,)) if issubclass(element, aas_model.SubmodelElementCollection) else {},
        )
    return result


def _round_trip(cls: type, tmp_path: Path):
    exported = convert_model_to_submodel_template(cls, f"urn:test:{cls.__name__}")
    store = model.DictIdentifiableStore([exported])
    source = tmp_path / "template.json"
    source.write_text(json_serialization.object_store_to_json(store))
    generator.gen_template(str(source), str(tmp_path))
    spec = importlib.util.spec_from_file_location(f"exported_{cls.__name__}", tmp_path / f"{generator.snake(
        generator.safe_name(exported.id_short))}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return getattr(module, generator.safe_name(exported.id_short))


@pytest.mark.parametrize("path", [
    "aas_model.submodel_templates.aimc:DmpAimc",
    "aas_model.submodel_templates.time_series:TimeSeriesSubmodel",
])
def test_our_extension_generated_back_from_its_template_is_the_same_class(path, tmp_path):
    module, name = path.split(":")
    cls = getattr(importlib.import_module(module), name)
    assert _structure(_round_trip(cls, tmp_path)) == _structure(cls)


@pytest.mark.parametrize("path", __import__("export_templates").TEMPLATES)
def test_the_published_templates_are_aas_their_readers_accept(path, tmp_path):
    from basyx.aas.adapter.json import read_aas_json_file
    import export_templates
    written = Path(export_templates.export_template(path, str(tmp_path)))
    with written.open(encoding="utf-8") as f:
        store = read_aas_json_file(f, failsafe=False)  # BaSyx checks the metamodel constraints while reading
    [submodel] = [o for o in store if isinstance(o, model.Submodel)]
    [shell] = [o for o in store if isinstance(o, model.AssetAdministrationShell)]
    assert submodel.kind is model.ModellingKind.TEMPLATE
    assert shell.asset_information.asset_kind is model.AssetKind.TYPE
    assert {r.key[0].value for r in shell.submodel} == {submodel.id}
