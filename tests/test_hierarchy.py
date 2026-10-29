"""HierarchicalStructures relate entities: every relationship of the catalog's resources is a ModelReference to an
entity that exists, in the same submodel (IsPartOf, HasPart) or in the related resource's (SameAs)."""

from __future__ import annotations

import json

from basyx.aas.adapter.json import json_serialization

from aas_model import build_from_model
from aas_model.resource_instances import RESOURCE_FACTORIES


def _submodels() -> dict:
    """Every built submodel of the catalog by its id."""
    found = {}
    for factory in RESOURCE_FACTORIES.values():
        document = json.loads(json_serialization.object_store_to_json(build_from_model(factory())))
        found.update({submodel["id"]: submodel for submodel in document["submodels"]})
    return found


def _resolve(submodels: dict, reference: dict):
    keys = reference["keys"]
    element = submodels.get(keys[0]["value"])
    for key in keys[1:]:
        children = (element or {}).get("submodelElements") or (element or {}).get("statements") or []
        element = next((c for c in children if c.get("idShort") == key["value"] and c["modelType"] == key["type"]),
                       None)
    return element


def _relationships(element: dict):
    for child in element.get("submodelElements") or element.get("statements") or []:
        if child["modelType"] == "RelationshipElement":
            yield child
        yield from _relationships(child)


def test_every_relationship_references_an_entity_that_exists():
    submodels = _submodels()
    hierarchies = [s for s in submodels.values() if s["idShort"] == "HierarchicalStructures"]
    assert hierarchies
    kinds = set()
    for hierarchy in hierarchies:
        for relationship in _relationships(hierarchy):
            kinds.add(relationship["idShort"].split("_")[0])
            for end in ("first", "second"):
                reference = relationship[end]
                assert reference["type"] == "ModelReference", (hierarchy["id"], relationship["idShort"])
                target = _resolve(submodels, reference)
                assert target is not None and target["modelType"] == "Entity", (
                    hierarchy["id"], relationship["idShort"], end, reference["keys"])
    assert kinds == {"PartOf", "HasPart", "SameAs"}


def test_a_node_is_the_entry_node_of_the_related_resource():
    submodels = _submodels()
    capping = next(s for s in submodels.values() if s["id"].endswith("cytivaCappingSystemAAS/submodels/"
                                                                       "HierarchicalStructures"))
    [same_as] = [r for r in _relationships(capping) if r["idShort"] == "SameAs"]
    line = _resolve(submodels, same_as["second"])
    assert line["globalAssetId"].endswith("/aauFillingLineAAS")
