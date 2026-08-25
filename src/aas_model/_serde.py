"""AAS-JSON <-> shared-model (de)serialization (ADR-016).

The registration service authors the AID/AIMC/resource submodels as pydantic
models and serializes them to AAS REST JSON via ``aas_pydantic.convert_model_to_aas``.
The management node fetches that same AAS REST JSON from BaSyx and must parse it
back into the *same* pydantic models — this module is the shared bridge.

Reverse path (management node / parse):
    AAS REST submodel dict -> basyx Submodel -> ``convert_submodel_to_model_instance``
    -> the shared pydantic model (Aid / Aimc / ...).

Forward path (registration service / author) is unchanged:
    ``convert_model_to_aas(model)`` from ``aas_pydantic`` (kept in the service);
    this module focuses on the shared *parse* API plus schema production for the
    lockstep tests.
"""

from __future__ import annotations

import io
import json
from typing import Any, Type

import basyx.aas.adapter.json as bjson
from basyx.aas import model as basyx_model
from basyx.aas.model.provider import DictIdentifiableStore

from aas_pydantic import convert_submodel_to_model_instance


def _load_basyx_submodel(submodel: dict[str, Any]) -> basyx_model.Submodel:
    """Load a single AAS REST submodel dict into a basyx Submodel."""
    store = DictIdentifiableStore()
    bjson.read_aas_json_file_into(
        store, io.StringIO(json.dumps({"submodels": [submodel]}))
    )
    sm = next(iter(store))
    if not isinstance(sm, basyx_model.Submodel):
        raise ValueError("expected a basyx Submodel, got " + type(sm).__name__)
    return sm


def parse_submodel_dict(
    submodel: dict[str, Any], model_type: Type[basyx_model.Submodel]
):
    """Parse an AAS REST submodel dict into the given shared pydantic model."""
    return convert_submodel_to_model_instance(_load_basyx_submodel(submodel), model_type)


def parse_submodel_json(data: str, model_type: Type[basyx_model.Submodel]):
    """Parse an AAS REST submodel JSON string into the given shared model."""
    return parse_submodel_dict(json.loads(data), model_type)
