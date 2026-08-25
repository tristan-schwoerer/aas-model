"""Property write-delegation machinery — mirror of the skill Operation delegation.

A Property (in the Parameters or Variables submodel) can be marked write-able
back to the asset by carrying a ``writeDelegation`` ConceptQualifier whose value
references the generated REST write endpoint::

    {delegation_base}/properties/{aas_id_short}/{property}

This is the "references a REST interface through a Qualifier" trigger.  When
such a qualifier is present, :func:`ensure_property_write_delegation` wires the
rest of the machinery automatically (idempotently):

- a matching ``interface_rest`` property — ``PUT /properties/{asset}/{property}``
  with the WoT ``writeProperty`` op — describing the DMP route,
- an AIMC MappingConfiguration mapping the native MQTT action to the REST
  property, with the write↔ack Lua transformation.

Configs only need to add the qualifier; the REST interface and AIMC entries are
derived from it (macros resolved by the id_injector).
"""

from __future__ import annotations

from typing import Any, Dict

from aas_pydantic import Qualifier

from aas_model.constants import WRITE_DELEGATION, WRITE_DELEGATION_SEMANTIC
from aas_model.resource_template.asset_interfaces_description import rest_property
from aas_model.resource_template.asset_interfaces_mapping_configuration import property_mapping_configuration
from aas_model.resource_template._helpers import put


def write_delegation_qualifier(name: str) -> Qualifier:
    """The ``writeDelegation`` qualifier a property carries to opt into
    write-back to the asset.  The value references the generated REST write
    endpoint (``{delegation_base}`` / ``{aas_id_short}`` macros are resolved by
    the id_injector)."""
    return Qualifier(
        type_=WRITE_DELEGATION,
        value=f"{{delegation_base}}/properties/{{aas_id_short}}/{name}",
        value_type="xs:string",
        semantic_id=WRITE_DELEGATION_SEMANTIC,
        kind="ConceptQualifier",
    )


def _has_write_delegation(el: Any) -> bool:
    return any(
        getattr(q, "type_", None) == WRITE_DELEGATION
        for q in (getattr(el, "qualifiers", None) or [])
    )


def _write_delegated_items(*submodels) -> Dict[str, Any]:
    """Collect ``{name: item}`` for every top-level parameter/variable that
    carries a ``writeDelegation`` qualifier — on the item SMC itself or on its
    leaf ``parameter``/``variable`` property."""
    result: Dict[str, Any] = {}
    for sm in submodels:
        if sm is None:
            continue
        for field in ("parameter", "variable"):
            container = getattr(sm, field, None) or {}
            for name, item in container.items():
                if _has_write_delegation(item):
                    result[name] = item
                    continue
                leaf = getattr(item, "parameter", None) or getattr(item, "variable", None)
                if leaf is not None and _has_write_delegation(leaf):
                    result[name] = item
    return result


def ensure_property_write_delegation(asset) -> None:
    """Auto-wire the write-delegation machinery for every property carrying a
    ``writeDelegation`` qualifier.

    Adds the REST write property to ``interface_rest`` and the AIMC
    mapping configuration — both idempotently (a config that already declares
    them is left untouched).
    """
    writable = _write_delegated_items(
        getattr(asset, "parameters", None),
        getattr(asset, "variables", None),
    )
    if not writable:
        return
    aid = getattr(asset, "asset_interfaces_description", None)
    aimc = getattr(asset, "asset_interfaces_mapping_configuration", None)
    if aid is None:
        return

    if aid.interface_rest is None:
        from aas_model.submodel_templates.rest_aid import RestInterface
        aid.interface_rest = RestInterface()
        aid.interface_rest.title.value = "Operation Delegation"
        aid.interface_rest.EndpointMetadata.base.value = "{delegation_base}"
        aid.interface_rest.EndpointMetadata.contentType.value = "application/json"

    props = aid.interface_rest.InteractionMetadata.properties.property_name
    covered = {
        s.SinkId.value
        for mc in aimc.MappingConfigurations.value
        for s in mc.Sinks.value
    } if aimc is not None else set()

    for name in writable:
        if name not in props:
            put(props, name, rest_property(name))
        if aimc is not None and name not in covered:
            aimc.MappingConfigurations.value.append(
                property_mapping_configuration(name))
