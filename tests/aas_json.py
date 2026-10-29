"""Parse AAS REST JSON back into the shared pydantic models, to check that what is built reads back the same."""

from __future__ import annotations

import io
import json
from typing import Any, Type

import basyx.aas.adapter.json as bjson
from basyx.aas import model as basyx_model
from basyx.aas.model.provider import DictIdentifiableStore

from aas_pydantic import convert_submodel_to_model_instance


def parse_submodel_dict(submodel: dict[str, Any], model_type: Type[Any]):
    """Parse an AAS REST submodel dict into ``model_type``."""
    store = DictIdentifiableStore()
    bjson.read_aas_json_file_into(store, io.StringIO(json.dumps({"submodels": [submodel]})))
    loaded = next(iter(store))
    if not isinstance(loaded, basyx_model.Submodel):
        raise ValueError("expected a basyx Submodel, got " + type(loaded).__name__)
    return convert_submodel_to_model_instance(loaded, model_type)
