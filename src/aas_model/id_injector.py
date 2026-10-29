"""Give an authored AAS its ids, and resolve what was written against them.

A resource is authored without ids: the shell's id follows from its idShort (``{BASE_URL}/aas/<idShort>``) and
each submodel's from the shell's (``{aas_id}/submodels/<idShort>``, see ``constants``). References and values
written against those (``{aas_id}``, ``{aas_id_short}``) are resolved once the ids are known. idShorts need no
injection: a child's idShort is its map key or field name (``aas_pydantic``).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from aas_pydantic.aas_model import AAS, Property, Qualifier, Reference, Submodel

from aas_model.constants import BASE_URL
from aas_model.invocation_authoring import resolve_invocation_addresses

_MACROS = ("{aas_id}", "{aas_id_short}")


def inject_ids(aas: AAS) -> None:
    """Set the ids of ``aas`` and its submodels unless authored, resolve the identity macros in its references,
    Property values and qualifiers, and fill its Operations' invocation addresses. Mutates ``aas``; idempotent."""
    if not aas.id or aas.id == aas.id_short:
        aas.id = f"{BASE_URL}/aas/{aas.id_short}"
    submodels = [value for name in type(aas).model_fields
                 if isinstance(value := getattr(aas, name), Submodel)]
    for submodel in submodels:
        if not submodel.id or submodel.id == submodel.id_short:
            submodel.id = f"{aas.id}/submodels/{submodel.id_short}"
    _resolve_macros(aas, aas.id, aas.id_short)
    resolve_invocation_addresses(aas)
    # An AID's interfaces reference their nosec_sc once its id is final.
    for submodel in submodels:
        select = getattr(submodel, "select_nosec", None)
        if callable(select):
            select()


def _resolve(value: str, aas_id: str, aas_id_short: str) -> str:
    return value.replace("{aas_id}", aas_id).replace("{aas_id_short}", aas_id_short)


def _resolve_macros(model: Any, aas_id: str, aas_id_short: str) -> None:
    """Resolve the identity macros at every depth. An invocationDelegation qualifier is filled by
    ``resolve_invocation_addresses``."""
    if isinstance(model, Reference):
        for key in model.key:
            if key.value and any(macro in key.value for macro in _MACROS):
                key.value = _resolve(key.value, aas_id, aas_id_short)
    elif isinstance(model, (Qualifier, Property)):
        if isinstance(model, Qualifier) and model.type_ == "invocationDelegation":
            return
        if isinstance(model.value, str) and any(macro in model.value for macro in _MACROS):
            model.value = _resolve(model.value, aas_id, aas_id_short)
    elif isinstance(model, BaseModel):
        for field_name in type(model).model_fields:
            _resolve_macros(getattr(model, field_name, None), aas_id, aas_id_short)
    elif isinstance(model, dict):
        for value in model.values():
            _resolve_macros(value, aas_id, aas_id_short)
    elif isinstance(model, (list, tuple)):
        for value in model:
            _resolve_macros(value, aas_id, aas_id_short)
