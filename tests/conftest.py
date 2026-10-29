"""Tests that generate and load template modules register their classes in aas_pydantic's class registries, which
resolve a class by its name or semanticId; each test leaves the registries as it found them."""

import pytest

from aas_pydantic import aas_model

_REGISTRIES = (aas_model._ELEMENT_CLASS_REGISTRY, aas_model._ELEMENT_CLASSES_BY_NAME, aas_model._SEMANTIC_ID_REGISTRY)


@pytest.fixture(autouse=True)
def _restored_class_registries():
    saved = [{key: list(value) if isinstance(value, list) else value for key, value in registry.items()}
             for registry in _REGISTRIES]
    yield
    for registry, before in zip(_REGISTRIES, saved):
        registry.clear()
        registry.update(before)
