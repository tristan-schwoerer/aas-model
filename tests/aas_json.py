"""Look into what a model is built into: the AAS JSON, as the AAS REST API serves it."""

from __future__ import annotations

import json
from typing import Any, Union

from basyx.aas import model
from basyx.aas.adapter.json import json_serialization


def published(*objects: model.Identifiable) -> dict:
    """The AAS JSON environment of BaSyx identifiables (a built store's contents)."""
    return json.loads(json_serialization.object_store_to_json(model.DictIdentifiableStore(objects)))


def submodel_json(submodel: model.Submodel) -> dict:
    """A built submodel as AAS JSON."""
    [document] = published(submodel)["submodels"]
    return document


def children(element: dict) -> list:
    return element.get("submodelElements") or element.get("statements") or (
        element["value"] if isinstance(element.get("value"), list) else [])


def name_of(element: dict) -> Union[str, None]:
    """An element's idShort or, for a list item (AASd-120), its English displayName."""
    if "idShort" in element:
        return element["idShort"]
    return next((n["text"] for n in element.get("displayName", []) if n["language"] == "en"), None)


def element(container: dict, *path: Union[str, int]) -> dict:
    """The element at ``path`` below ``container``: each step an idShort (a list item's displayName), or an index
    into a list."""
    for step in path:
        items = children(container)
        if isinstance(step, int):
            container = items[step]
            continue
        found = [item for item in items if name_of(item) == step]
        if len(found) != 1:
            raise KeyError(f"{step!r} in {name_of(container)!r}: found {len(found)} of {[name_of(i) for i in items]}")
        container = found[0]
    return container


def value(container: dict, *path: Union[str, int]) -> Any:
    """The value of the element at ``path``."""
    return element(container, *path).get("value")


def names(container: dict, *path: Union[str, int]) -> list:
    """The names of the children of the element at ``path``."""
    return [name_of(item) for item in children(element(container, *path))]


def semantic_id(element_json: dict) -> Union[str, None]:
    reference = element_json.get("semanticId")
    return reference["keys"][0]["value"] if reference else None
