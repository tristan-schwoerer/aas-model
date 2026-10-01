"""Resource AAS — Pydantic model for a Resource AAS with type-level defaults.

All Resources must implement certain skills (Halt, Occupy, Release), expose
a StationState property, track PackMLState, and declare a Location.  These
defaults are baked into the Pydantic model so individual station configs
only need to specify the delta.

Each submodel's station-agnostic defaults live in its own module under
``resource_template/``:

    nameplate                    — generated IDTA Nameplate + year/country
    asset_interfaces_description — MQTT-extended AID + Halt/Occupy/Release + StationState
    control_component_instance   — extended CCI + Halt/Occupy/Release skills + MQTT endpoint
    variables                    — custom Variables + PackMLState/OccupationState
    parameters                   — custom Parameters + Location

This module composes them into ``ResourceTypeAAS``.  Station configs override
fields via model_validate() — missing fields fall back to these defaults.

Container-style: children live in ``value`` / ``submodel_element`` dicts
keyed by id_short (basyx/IDTA-aligned).
"""

from __future__ import annotations

from typing import Optional

from aas_pydantic import AAS

from aas_pydantic.submodel_templates.nameplate import Nameplate
from aas_pydantic.submodel_templates.capability_description import CapabilityDescription
from aas_pydantic.submodel_templates.hierarchical_structures import HierarchicalStructures

from aas_model.submodel_templates.aid import DmpAssetInterfacesDescription
from aas_model.submodel_templates.variables import Variables
from aas_model.submodel_templates import Aimc

from aas_model.resource_template.nameplate import nameplate
from aas_model.resource_template.asset_interfaces_description import asset_interfaces_description
from aas_model.resource_template.asset_interfaces_mapping_configuration import asset_interfaces_mapping_configuration
from aas_model.resource_template.control_component_instance import (
    ResourceControlComponentInstance, control_component_instance,
)
from aas_model.resource_template.variables import variables
from aas_model.resource_template.parameters import ResourceParameters, resource_parameters


# ═══════════════════════════════════════════════════════════════════════════════
# Submodel field names — documented for reference (model walking replaces old injection)
# ═══════════════════════════════════════════════════════════════════════════════

SUBMODEL_FIELDS = (
    "nameplate", "asset_interfaces_description", "control_component_instance",
    "capability_description", "hierarchical_structures", "variables", "parameters",
    "asset_interfaces_mapping_configuration",
)


# ═══════════════════════════════════════════════════════════════════════════════
# ResourceTypeAAS — the type model with defaults
# ═══════════════════════════════════════════════════════════════════════════════


class ResourceTypeAAS(AAS):
    """Resource AAS type — all Resources share these defaults.

    Individual stations override via JSON config.  Fields not specified
    in the station config fall back to the defaults below.

    Mandatory for all resources:
        - Halt, Occupy, Release actions (MQTT + CCI skills)
        - StationState property
        - PackMLState and OccupationState variables
        - Location parameter
    """

    model_config = {"extra": "forbid"}

    # ── Nameplate ─────────────────────────────────────────────────────────
    nameplate: Nameplate = nameplate()

    # ── Asset Interfaces Description ──────────────────────────────────────
    asset_interfaces_description: DmpAssetInterfacesDescription = asset_interfaces_description()

    # ── Control Component Instance ────────────────────────────────────────
    control_component_instance: ResourceControlComponentInstance = control_component_instance()

    # ── Variables ─────────────────────────────────────────────────────────
    variables: Variables = variables()

    # ── Parameters ────────────────────────────────────────────────────────
    parameters: ResourceParameters = resource_parameters()
    # ── Asset Interfaces Mapping Configuration ──────────────────────────────
    asset_interfaces_mapping_configuration: Aimc = asset_interfaces_mapping_configuration()
    # ── Optional submodels (no defaults — stations opt in) ────────────────
    capability_description: Optional[CapabilityDescription] = None
    hierarchical_structures: Optional[HierarchicalStructures] = None
