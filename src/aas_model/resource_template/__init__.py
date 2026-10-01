"""AAS templates — top-level Pydantic models for complete AAS types.

Partially-filled submodels (station-agnostic defaults) live in sibling
modules: ``nameplate``, ``asset_interfaces_description``,
``control_component_instance``, ``variables``, ``parameters``.  Each uses
either our modified shared models (``aas_model.submodel_templates``) or the
generated aas_pydantic templates as its base.
"""

from .asset import ResourceTypeAAS
from .nameplate import nameplate
from .asset_interfaces_description import (
    asset_interfaces_description, mqtt_action, mqtt_property,
)
from .control_component_instance import (
    ResourceControlComponentInstance, control_component_instance, extended_skill,
    skill_operation, skill_interface_relationship, native_action_ref, skill_ref,
)
from .asset_interfaces_mapping_configuration import (
    asset_interfaces_mapping_configuration,
    skill_operation_mapping_configuration,
    operation_ref,
    variables_mapping_configuration,
)
from .variables import variables, variable
from .parameters import Position, ResourceParameters, resource_parameters

__all__ = [
    "ResourceTypeAAS",
    "nameplate",
    "asset_interfaces_description",
    "mqtt_action",
    "mqtt_property",
    "ResourceControlComponentInstance",
    "control_component_instance",
    "extended_skill",
    "skill_operation",
    "skill_interface_relationship",
    "native_action_ref",
    "skill_ref",
    "asset_interfaces_mapping_configuration",
    "skill_operation_mapping_configuration",
    "operation_ref",
    "variables_mapping_configuration",
    "write_delegation_qualifier",
    "variables",
    "variable",
    "Position",
    "ResourceParameters",
    "resource_parameters",
]
