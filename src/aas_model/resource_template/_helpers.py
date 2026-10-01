"""Shared helpers for building partially-filled submodel templates.

Used by the individual partial submodel modules under ``resource_template/``
to stamp id_shorts and insert elements into values models / dynamic dict
containers.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from aas_pydantic import SubmodelElement


def put(container: Any, key: str, element: SubmodelElement) -> SubmodelElement:
    """Assign *element* into *container* under *key*, stamping its id_short
    from the key.

    *container* is a values model (``setattr`` onto an existing field) or a
    dynamic ``Dict[str, X]`` map (``container[key] = ...``).  The key is the
    single source of truth for the id_short.
    """
    element.id_short = key
    if isinstance(container, BaseModel):
        setattr(container, key, element)
    else:
        container[key] = element
    return element


# The mandatory default Resource skills, mirrored across the CCI (skills +
# endpoints relationships), the AID (native MQTT actions) and the AIMC (one
# operation-delegation mapping per skill, DMP v3).
# Each entry is ``(name, synchronous, has_response)``. ``has_response`` is
# TRUE for every skill: the delegated operation completes through the
# command affordance's DECLARED reply topic (correlated by Uuid) — an
# undeclared response form leaves the interaction unresolved.
DEFAULT_SKILLS = (
    ("Halt", True, True),
    ("Occupy", True, True),
    ("Release", True, True),
)
