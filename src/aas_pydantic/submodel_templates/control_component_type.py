"""ControlComponentType — generated from IDTA template."""

from __future__ import annotations

from typing import Any, ClassVar, List, Dict, Optional, TypeAlias
from aas_pydantic import (
    Property, ReferenceElement, Submodel, SubmodelElement, SubmodelElementCollection, SubmodelElementList,
)

class InterfaceProfile(Property):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Type/Interface/Profile/2/0"
    description: str = "The profile according to which the referred control interface operates."
    value_type: str = "xs:string"

class InterfaceProfileSupplement(Property):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Type/Interface/ProfileSupplement/2/0"
    description: str = "Supplemental information to further specify the interface."
    value_type: str = "xs:string"

class InterfaceReference(ReferenceElement):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Type/Interface/Reference/2/0"
    description: str = "A reference to a control interface supported by the component type and described by the interfaceProfile and the optional supplement"

class Interface(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Type/Interface/2/0"
    description: str = "An interface description"
    InterfaceProfile: InterfaceProfile_t
    InterfaceProfileSupplement: Optional[InterfaceProfileSupplement_t] = None
    InterfaceReference: Optional[InterfaceReference_t] = None

class Interfaces(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Type/Interfaces/2/0"
    description: str = "Collection of references to control interfaces supported by the component type, e.g. to elements of the Interface Metadata SMC of the Asset Interface Description submodel, the MTP submodel or OPC UA Server Datasheet submodel."
    Interface: Dict[str, Interface_t] = {}

class ErrorCode(Property):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Type/Error/Code/2/0"
    description: str = "The error code."
    value_type: str = "xs:string"

class Error(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Type/Error/2/0"
    description: str = "A container representing an error."
    ErrorCode: ErrorCode_t

class Errors(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Type/Errors/2/0"
    description: str = "Collection of all possible error codes that may appear in components of this type."
    Error: Dict[str, Error_t] = {}

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
    description: str = "A reference to an SMC \u201cError\u201d (Table 5) that that can be "

class Errors_skill(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Skill/Errors/2/0"
    description: str = "Collection of references to the error codes of the component that may be raised by this skill."
    ErrorReference: Dict[str, ErrorReference_t] = {}

class SkillReference(ReferenceElement):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Skill/SkillReference/2/0"
    description: str = "A reference to an SMC \u201cSkill\u201d (Table 7) of this or another "

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
    Errors: Errors_skill
    Uses: Uses_t

class Skills(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Skills/2/0"
    description: str = "Collection of skills offered by the component type"
    Skill: Dict[str, Skill_t] = {}

class ControlComponentType(Submodel):
    semantic_id: str = "https://admin-shell.io/idta/ControlComponent/Type/2/0"
    VERSION: ClassVar[str] = "2"
    REVISION: ClassVar[str] = "0"
    Interfaces: Interfaces_t
    Errors: Errors_t
    Skills: Skills_t

# ── Clash aliases: field name == element class name ──
# alias so field ``InterfaceProfile_t`` can name a class of the same id_short
InterfaceProfile_t: TypeAlias = InterfaceProfile
# alias so field ``InterfaceProfileSupplement_t`` can name a class of the same id_short
InterfaceProfileSupplement_t: TypeAlias = InterfaceProfileSupplement
# alias so field ``InterfaceReference_t`` can name a class of the same id_short
InterfaceReference_t: TypeAlias = InterfaceReference
# alias so field ``Interface_t`` can name a class of the same id_short
Interface_t: TypeAlias = Interface
# alias so field ``ErrorCode_t`` can name a class of the same id_short
ErrorCode_t: TypeAlias = ErrorCode
# alias so field ``Error_t`` can name a class of the same id_short
Error_t: TypeAlias = Error
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
# alias so field ``Uses_t`` can name a class of the same id_short
Uses_t: TypeAlias = Uses
# alias so field ``Skill_t`` can name a class of the same id_short
Skill_t: TypeAlias = Skill
# alias so field ``Interfaces_t`` can name a class of the same id_short
Interfaces_t: TypeAlias = Interfaces
# alias so field ``Errors_t`` can name a class of the same id_short
Errors_t: TypeAlias = Errors
# alias so field ``Skills_t`` can name a class of the same id_short
Skills_t: TypeAlias = Skills

# ── Resolve forward references (Pydantic circular refs) ──
InterfaceProfile.model_rebuild()
InterfaceProfileSupplement.model_rebuild()
InterfaceReference.model_rebuild()
Interface.model_rebuild()
Interfaces.model_rebuild()
ErrorCode.model_rebuild()
Error.model_rebuild()
Errors.model_rebuild()
Disabled.model_rebuild()
Mode.model_rebuild()
Modes.model_rebuild()
Direction.model_rebuild()
Type.model_rebuild()
Values.model_rebuild()
Parameter.model_rebuild()
Parameters.model_rebuild()
ErrorReference.model_rebuild()
Errors_skill.model_rebuild()
SkillReference.model_rebuild()
Uses.model_rebuild()
Skill.model_rebuild()
Skills.model_rebuild()
ControlComponentType.model_rebuild()
