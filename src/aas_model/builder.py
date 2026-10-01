"""
AAS Builder — validate JSON, convert to BaSyx DictObjectStore.

Pydantic validates + coerces.  aas_pydantic.convert_model_to_aas() handles
conversion (submodels + AAS shell + asset information).  ID injection is
done post-validation via the model-walking id_injector module — no raw-dict
heuristics.

Templates are full model dumps — the user trims what they don't need.
Pydantic class defaults fill in anything omitted at registration time.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Dict, Any

from aas_pydantic import convert_model_to_aas

from aas_model.resource_template.asset import ResourceTypeAAS
from aas_model.id_injector import inject_ids
from aas_model.constants import BASE_URL, SITE, DELEGATION_BASE

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Deep merge — instance config overlaid on type defaults
# ═══════════════════════════════════════════════════════════════════════════════

# id_short placeholders injected by id_preprocessor (before the merge runs).
_PLACEHOLDER_RE = re.compile(r"^elem\d+$")


def deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge *override* into *base*.

    Dicts are merged recursively — keys present in both are resolved by
    merging their values.  Scalars, lists, and ``None`` values in the
    override replace the base value outright.

    This allows station configs to specify only the fields they want to
    change, while preserving specialized subtypes (e.g. CoordinateValue)
    and default entries (e.g. y/yaw when only x is overridden) from the
    type defaults.

    id_short placeholders (``elemN``) injected by ``ensure_id_shorts`` are
    never allowed to clobber a proper id_short already present in the base
    defaults.
    """
    result = {**base}
    for key, value in override.items():
        if (
            key == "id_short"
            and isinstance(value, str)
            and _PLACEHOLDER_RE.match(value)
            and key in result
        ):
            continue
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════════

def merge_instance_config(data: Dict[str, Any]) -> Dict[str, Any]:
    """Base ResourceTypeAAS defaults deep-merged under the instance config.

    The base dump carries the ``modelType`` discriminators of the specialized
    submodel types (Position, Coordinate, Variable, ...) and every default
    value, so a minimal config round-trips into the concrete types and any
    omitted field falls back to its default.

    ``delegation_base`` is build-time metadata (the resource's DMP /
    operation-delegation base URL) — consumed by the callers and not a model
    field, so it is popped here before validation.
    """
    data = dict(data)
    data.pop("delegation_base", None)
    base = ResourceTypeAAS(
        id_short=data["id_short"],
        id=data.get("id") or f"{BASE_URL}/aas/{data['id_short']}",
        asset_type=data.get("asset_type", ""),
    ).model_dump()
    return deep_merge(base, data)


def build_from_dict(data: Dict[str, Any]) -> Any:
    """Validate JSON dict → BaSyx DictObjectStore (with injected ids).

    Constructs type defaults from ResourceTypeAAS, then deep-merges the
    instance config on top.  This preserves specialised subtypes and
    default entries the instance config does not mention.

    The optional ``delegation_base`` config key overrides the resource's
    operation-delegation (DMP) base URL.
    """
    delegation_base = data.get("delegation_base") or DELEGATION_BASE
    asset = ResourceTypeAAS.model_validate(merge_instance_config(data))
    inject_ids(asset, delegation_base=delegation_base)
    return convert_model_to_aas(asset)


def build_from_json(path: str):
    """Load JSON file → validated + injected → BaSyx DictObjectStore."""
    with open(path) as f:
        return build_from_dict(json.load(f))


# ═══════════════════════════════════════════════════════════════════════════════
# Template generation — full model dump, user trims what they don't need
# ═══════════════════════════════════════════════════════════════════════════════

def generate_station_template(
    *,
    aas_id_short: str,
    aas_id: str = "",
    asset_type: str,
    delegation_base: str = DELEGATION_BASE,
) -> dict:
    """Dump the full ResourceTypeAAS model with identity fields filled in.

    Returns every submodel, every property, with all class defaults — the
    complete shape of a Resource AAS.  The user trims unwanted sections,
    adds instance-specific skills/parameters, and saves as a station config.
    Omitted fields fall back to class defaults at registration time.

    ``delegation_base`` is emitted as a top-level config key so each resource
    can point its skill Operation delegation at its own DMP.
    """
    if not aas_id:
        aas_id = f"{BASE_URL}/aas/{aas_id_short}"

    asset = ResourceTypeAAS(
        id_short=aas_id_short,
        id=aas_id,
        asset_type=asset_type,
        derived_from=f"{BASE_URL}/aas/templates/resource",
    )
    template = asset.model_dump()
    template["delegation_base"] = delegation_base
    return template


# ═══════════════════════════════════════════════════════════════════════════════
# Full instance construction (used by services that need a live model object)
# ═══════════════════════════════════════════════════════════════════════════════


def build_resource_type_aas(
    *,
    aas_id: str = "",
    aas_id_short: str = "",
    asset_type: str = "",
    global_asset_id: str = "",
    serial_number: str = "",
    location: str = "",
    station_name: str = "",
    site_path: str = SITE,
    broker_host: str = "192.168.0.104",
    broker_port: int = 1883,
    delegation_base: str = DELEGATION_BASE,
) -> ResourceTypeAAS:
    """Build a fully-populated ResourceTypeAAS with station overrides.

    Constructs from class defaults, then applies station-specific values.
    Returns the validated Pydantic model instance (not a dict).
    ``delegation_base`` is the resource's DMP / operation-delegation base URL.
    """
    if not station_name:
        station_name = aas_id_short or "station"
    if not aas_id:
        aas_id = f"{BASE_URL}/aas/{aas_id_short or station_name}"
    if not aas_id_short:
        aas_id_short = station_name
    if not global_asset_id:
        global_asset_id = f"{BASE_URL}/assets/{aas_id_short}"

    topic_base = f"/{site_path}/{station_name}" if site_path else f"/{station_name}"
    broker_uri = f"mqtt://{broker_host}:{broker_port}{topic_base}"

    asset = ResourceTypeAAS(
        id_short=aas_id_short,
        id=aas_id,
        asset_type=asset_type,
        derived_from=f"{BASE_URL}/aas/templates/resource",
    )
    if serial_number or location:
        sids = {}
        if serial_number:
            sids["serialNumber"] = serial_number
            asset.nameplate.SerialNumber.value = serial_number
        if location:
            sids["location"] = location
        asset.specific_asset_ids = sids

    aid = asset.asset_interfaces_description
    if aid:
        iface = aid.InterfaceTemplateForMQTT.get("interface_mqtt")
        if iface is not None and hasattr(iface, "EndpointMetadata"):
            iface.EndpointMetadata.base.value = broker_uri
        if hasattr(iface, "title"):
            iface.title.value = station_name
    # The CCI ``endpoints`` container holds per-skill native-interface
    # relationships (see resource_template/control_component_instance.py) —
    # no broker endpoint to patch here.

    inject_ids(asset, delegation_base=delegation_base)
    return asset
