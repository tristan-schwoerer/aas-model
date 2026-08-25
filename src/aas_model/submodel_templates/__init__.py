"""
Custom aas_pydantic submodel templates — project-specific and IDTA-extended models.

These models follow the same pattern as aas_pydantic generated templates:
- Submodel/SubmodelElementCollection base classes
- Inline semantic_id, description, qualifiers on every class and leaf element
- Typed leaf elements (Property, ReferenceElement, File, etc.) with defaults

Modules:
    mqtt_aid           — MQTT-extended AssetInterfacesDescription
    execution_model    — Skills ExecutionModel (parameters, conditions, effects)
    skills             — Extended CCI Skill with ExecutionModel
    variables          — Variables submodel (custom, not yet IDTA)
    parameters         — Parameters submodel (custom, not yet IDTA)
"""

from aas_model.submodel_templates.mqtt_aid import (
    MqttAssetInterfacesDescription,
    MqttAction,
    MqttProperty,
    MqttForm,
    MqttResponseForm,
)
from .control_component_instance import (
    ExecutionModel,
    ExecutionModelParameter,
    Fluent,
    Term,
    ExtendedSkill,
    ExtendedSkills,
    SkillOperation,
    OperationVariableProp,
    SkillInterfaceRelationship,
    ResourceEndpoints,
)
from .rest_aid import RestInterface, RestAction, RestProperty, RestForm, RestProperties
from .variables import Variables
from .parameters import Parameters
from .aimc import Aimc

__all__ = [
    # MQTT AID
    "MqttAssetInterfacesDescription",
    "MqttAction",
    "MqttProperty",
    "MqttForm",
    "MqttResponseForm",
    # Execution model
    "ExecutionModel",
    "ExecutionModelParameter",
    "Fluent",
    "Term",
    # Skills
    "ExtendedSkill",
    "ExtendedSkills",
    "SkillOperation",
    "OperationVariableProp",
    "SkillInterfaceRelationship",
    "ResourceEndpoints",
    # REST AID interface
    "RestInterface",
    "RestAction",
    "RestProperty",
    "RestForm",
    "RestProperties",
    # Custom submodels
    "Variables",
    "Parameters",
    "Aimc",
]
