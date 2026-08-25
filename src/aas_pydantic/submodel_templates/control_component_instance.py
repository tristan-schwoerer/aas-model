"""ControlComponentInstance — generated from IDTA template."""

from __future__ import annotations

from typing import Any, ClassVar, List, Dict, TypeAlias
from aas_pydantic import (
    Property, ReferenceElement, Submodel, SubmodelElement, SubmodelElementCollection, SubmodelElementList,
)

class InterfaceReference(ReferenceElement):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Instance/Endpoint/InterfaceReference/2/0"
    description: str = "A reference to an interface description (SMC Interface) in a Control Component Type submodel that specifies the semantics of the interface."

class EndpointReference(ReferenceElement):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Instance/Endpoint/Reference/2/0"
    description: str = "A reference to a technical control endpoint that adheres to the semantics of the referenced interface."

class Endpoint(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Instance/Endpoint/2/0"
    description: str = "A control endpoint supported by the instance of the component."
    InterfaceReference: InterfaceReference_t
    EndpointReference: EndpointReference_t

class Endpoints(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Instance/Endpoints/2/0"
    description: str = "Collection of references to control endpoints supported by the instance of the component"
    Endpoint: Dict[str, Endpoint_t] = {}

class Disabled(Property):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Skill/Disabled/2/0"
    description: str = "Boolean property that defines if the skill is (currently) disabled, e.g. not licensed, tested, suitable."
    value_type: str = "xs:boolean"

class Mode(Property):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Skill/Mode/2/0"
    description: str = "Name of the operation, operating, operational or execution modes (depending on the standard), in which the skill is available/allowed to execute."
    value_type: str = "xs:string"

class Modes(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Skill/Modes/2/0"
    description: str = "Collection of operation, operating, operational or execution modes (depending on the standard), in which the skill is available/allowed to execute."
    Mode: Dict[str, Mode_t] = {}

class Direction(Property):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Skill/Parameter/Direction/2/0"
    description: str = "Indicates whether the parameter is an input (In) or an output (Out) of the skill. An InOut parameter can be set from outside and can also be changed from skill itself. "
    value_type: str = "xs:string"

class Type(Property):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Skill/Parameter/Type/2/0"
    description: str = "Data type as string used to interpret the parameter. "
    value_type: str = "xs:string"

class Values(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Skill/Parameter/Values/2/0"
    description: str = "Collection of properties of the accepted values that the parameter may take."
    pass

class Parameter(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Skill/Parameter/2/0"
    description: str = "Parameter used for the configuration of the skill."
    Direction: Direction_t
    Type: Type_t
    Values: Values_t

class Parameters(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Skill/Parameters/2/0"
    description: str = "Collection of parameters used for the configuration of the skill."
    Parameter: Dict[str, Parameter_t] = {}

class ErrorReference(ReferenceElement):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Skill/ErrorReference/2/0"

class Errors(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Skill/Errors/2/0"
    description: str = "Collection of references to the error codes of the component that may be raised by this skill."
    ErrorReference: Dict[str, ErrorReference_t] = {}

class SkillReference(ReferenceElement):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Skill/SkillReference/2/0"

class Uses(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Skill/Uses/2/0"
    description: str = "Collection of references to other skills, that this skill uses."
    SkillReference: Dict[str, SkillReference_t] = {}

class Skill(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Skill/2/0"
    description: str = "Contains the basic information to call (request the execution of) a skill, e.g. its signature"
    Disabled: Disabled_t
    Modes: Modes_t
    Parameters: Parameters_t
    Errors: Errors_t
    Uses: Uses_t

class Skills(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Skills/2/0"
    description: str = "Collection of skills offered by the component instance"
    Skill: Dict[str, Skill_t] = {}

class Type_instance(ReferenceElement):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Instance/Type/2/0"
    description: str = "Reference between the component instance and its respective ControlComponentType Submodel."

class ControlComponentInstance(Submodel):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Instance/2/0"
    description: str = "A ControlComponentInstance Submodel."
    VERSION: ClassVar[str] = "2"
    REVISION: ClassVar[str] = "0"
    Endpoints: Endpoints_t
    Skills: Skills_t
    Type: Type_instance

# ── Clash aliases: field name == element class name ──
# alias so field ``InterfaceReference_t`` can name a class of the same id_short
InterfaceReference_t: TypeAlias = InterfaceReference
# alias so field ``EndpointReference_t`` can name a class of the same id_short
EndpointReference_t: TypeAlias = EndpointReference
# alias so field ``Endpoint_t`` can name a class of the same id_short
Endpoint_t: TypeAlias = Endpoint
# alias so field ``Mode_t`` can name a class of the same id_short
Mode_t: TypeAlias = Mode
# alias so field ``Direction_t`` can name a class of the same id_short
Direction_t: TypeAlias = Direction
# alias so field ``Type_t`` can name a class of the same id_short
Type_t: TypeAlias = Type
# alias so field ``Values_t`` can name a class of the same id_short
Values_t: TypeAlias = Values
# alias so field ``Parameter_t`` can name a class of the same id_short
Parameter_t: TypeAlias = Parameter
# alias so field ``ErrorReference_t`` can name a class of the same id_short
ErrorReference_t: TypeAlias = ErrorReference
# alias so field ``SkillReference_t`` can name a class of the same id_short
SkillReference_t: TypeAlias = SkillReference
# alias so field ``Disabled_t`` can name a class of the same id_short
Disabled_t: TypeAlias = Disabled
# alias so field ``Modes_t`` can name a class of the same id_short
Modes_t: TypeAlias = Modes
# alias so field ``Parameters_t`` can name a class of the same id_short
Parameters_t: TypeAlias = Parameters
# alias so field ``Errors_t`` can name a class of the same id_short
Errors_t: TypeAlias = Errors
# alias so field ``Uses_t`` can name a class of the same id_short
Uses_t: TypeAlias = Uses
# alias so field ``Skill_t`` can name a class of the same id_short
Skill_t: TypeAlias = Skill
# alias so field ``Endpoints_t`` can name a class of the same id_short
Endpoints_t: TypeAlias = Endpoints
# alias so field ``Skills_t`` can name a class of the same id_short
Skills_t: TypeAlias = Skills

# ── Resolve forward references (Pydantic circular refs) ──
InterfaceReference.model_rebuild()
EndpointReference.model_rebuild()
Endpoint.model_rebuild()
Endpoints.model_rebuild()
Disabled.model_rebuild()
Mode.model_rebuild()
Modes.model_rebuild()
Direction.model_rebuild()
Type.model_rebuild()
Values.model_rebuild()
Parameter.model_rebuild()
Parameters.model_rebuild()
ErrorReference.model_rebuild()
Errors.model_rebuild()
SkillReference.model_rebuild()
Uses.model_rebuild()
Skill.model_rebuild()
Skills.model_rebuild()
Type_instance.model_rebuild()
ControlComponentInstance.model_rebuild()
