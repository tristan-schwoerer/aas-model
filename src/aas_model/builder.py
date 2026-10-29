"""Convert typed Resources into AAS objects without changing the source model."""

from __future__ import annotations

from basyx.aas.model import DictIdentifiableStore, Identifiable

from aas_pydantic import convert_model_to_aas

from aas_model.resource_template.resources import Resource
from aas_model.id_injector import inject_ids


def build_from_model(resource: Resource) -> DictIdentifiableStore[Identifiable]:
    """Build a BaSyx store from a Resource without mutating the authored model.

    Pydantic owns model construction and JSON loading. Building only resolves
    IDs/references on a copy and converts it through the aas_pydantic fork.
    Mutations to typed element dictionaries are validated as a complete graph
    before export; inserting into a Python dict alone bypasses Pydantic.
    """
    type(resource).model_validate_json(resource.model_dump_json())
    asset = resource.model_copy(deep=True)
    inject_ids(asset)
    return convert_model_to_aas(asset)
