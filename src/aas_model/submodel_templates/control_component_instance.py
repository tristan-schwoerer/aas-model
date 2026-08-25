"""
Extended Skills — Pydantic model extending CCI Skill with ExecutionModel.

The IDTA ControlComponentInstance template defines a Skill SMC with basic
fields (disabled, modes, parameters, errors, uses). This module extends it
with:
- interface_reference: ReferenceElement pointing to the AID action

These extensions are read by the BT_Controller at runtime for state grounding
and by the operation delegation service for MQTT topic resolution.

Named-field style: containers hold their children as DIRECT named fields
(no ``value``/``submodel_element`` wrapper); dynamic name-keyed maps are
``Dict[str, X]`` fields.
"""

from __future__ import annotations

from typing import ClassVar, Dict, List, Optional

from pydantic import model_validator
from aas_pydantic import (
    SubmodelElementCollection,
    Property, ReferenceElement, Operation, RelationshipElement, Qualifier,
)

from aas_pydantic.submodel_templates.control_component_instance import (
    Skill as _BaseSkill,
    Skills as _BaseSkills,
    Disabled, Modes, Parameters, Errors, Uses,
    Disabled_t, Modes_t, Parameters_t, Errors_t, Uses_t,
    Endpoints as _BaseEndpoints,
)

from aas_model.constants import (
    BASE_URL, CSSX
)


EXECUTION_MODEL = f"{BASE_URL}/ExectionModel"
EXEC_MODEL_REF_STEP = f"{BASE_URL}/execution/ModelRefStep/1/0"
EXEC_AAS_REF = f"{BASE_URL}/execution/AasRef/1/0"
EXEC_SUBMODEL_REF = f"{BASE_URL}/execution/SubmodelRef/1/0"
EXEC_ELEMENT_REF = f"{BASE_URL}/execution/ElementRef/1/0"
EXEC_PROPERTY_REF = f"{BASE_URL}/execution/PropertyRef/1/0"
EXEC_PARAM_KEY = f"{BASE_URL}/execution/ParameterKey/1/0"
EXEC_PARAM_SEMANTIC_ID = f"{BASE_URL}/execution/ParameterSemanticId/1/0"
EXEC_OPERATOR = f"{BASE_URL}/execution/Operator/1/0"
EXEC_WHEN_CONDITION = f"{BASE_URL}/execution/WhenCondition/1/0"

# Predicate condition (redesigned — Phase 5)
EXEC_PREDICATE = f"{CSSX}/Predicate"

# LogicTerms
EXEC_LOGIC_TERM = f"{BASE_URL}/LogicTerm"
EXEC_LOGIC_TERM_AND = f"{EXEC_LOGIC_TERM}/And"
EXEC_LOGIC_TERM_OR = f"{EXEC_LOGIC_TERM}/Or"
EXEC_LOGIC_TERM_NOT = f"{EXEC_LOGIC_TERM}/Not"
EXEC_LOGIC_TERM_IMPLY = f"{EXEC_LOGIC_TERM}/Imply"
EXEC_LOGIC_TERM_EXISTS = f"{EXEC_LOGIC_TERM}/Exists"
EXEC_LOGIC_TERM_FOR_ALL = f"{EXEC_LOGIC_TERM}/Forall"
EXEC_LOGIC_TERM_WHEN = f"{EXEC_LOGIC_TERM}/When"
EXEC_LOGIC_TERM_AT_START = f"{EXEC_LOGIC_TERM}/AtStart"
EXEC_LOGIC_TERM_OVER_ALL = f"{EXEC_LOGIC_TERM}/OverAll"
EXEC_LOGIC_TERM_AT_END = f"{EXEC_LOGIC_TERM}/AtEnd"
EXEC_LOGIC_TERM_INCREASE = f"{EXEC_LOGIC_TERM}/Increase"
EXEC_LOGIC_TERM_DECREASE = f"{EXEC_LOGIC_TERM}/Decrease"

# ArithmeticTerms
EXEC_ARITHMETIC_TERM = f"{BASE_URL}/ArithmeticTerms"
EXEC_ARITHMETIC_TERM_PLUS = f"{EXEC_ARITHMETIC_TERM}/Plus"
EXEC_ARITHMETIC_TERM_MINUS = f"{EXEC_ARITHMETIC_TERM}/Minus"
EXEC_ARITHMETIC_TERM_DIVIDE = f"{EXEC_ARITHMETIC_TERM}/Divide"
EXEC_ARITHMETIC_TERM_MULTIPLY = f"{EXEC_ARITHMETIC_TERM}/Multiply"
EXEC_ARITHMETIC_TERM_GREATER = f"{EXEC_ARITHMETIC_TERM}/Greater"
EXEC_ARITHMETIC_TERM_LESS = f"{EXEC_ARITHMETIC_TERM}/Less"
EXEC_ARITHMETIC_TERM_GREATER_EQUAL = f"{EXEC_ARITHMETIC_TERM}/GreaterEqual"
EXEC_ARITHMETIC_TERM_EQUAL = f"{EXEC_ARITHMETIC_TERM}/Equal"
EXEC_ARITHMETIC_TERM_LESS_EQUAL = f"{EXEC_ARITHMETIC_TERM}/LessEqual"
EXEC_ARITHMETIC_TERM_NOT_EQUAL = f"{EXEC_ARITHMETIC_TERM}/NotEqual"


EXTENDED_SKILLS = f"{BASE_URL}/ControlComponent/Skills/2/0"
EXTENDED_SKILL = f"{BASE_URL}/ControlComponent/Skill/2/0"
EXTENDED_SKILL_INTERFACE_REF = f"{BASE_URL}/ControlComponent/Skill/1/0"

# Skill Operation (operation delegation) + endpoint relationships
SKILL_OPERATION = f"{BASE_URL}/ControlComponent/Skill/Operation/2/0"
SKILL_OPERATION_VARIABLE = f"{BASE_URL}/ControlComponent/Skill/OperationVariable/1/0"
SKILL_INVOCATION_DELEGATION = f"{BASE_URL}/ControlComponent/Skill/InvocationDelegation/1/0"
SKILL_INTERFACE_RELATIONSHIP = f"{BASE_URL}/ControlComponent/Skill/NativeInterface/1/0"


class OperationVariableProp(Property):
    """A single input/inoutput/output variable of a skill's Operation.

    Mirrors the command / commandResponse schemas the native MQTT action
    carries (e.g. ``Uuid``, ``State``, ``Outcome``) so the AAS Web GUI can
    render and manually invoke the operation.
    """
    semantic_id: str = SKILL_OPERATION_VARIABLE
    description: str = "An operation variable of the skill's operation."


class SkillOperation(Operation):
    """The skill's AAS Operation — the executable entry point for clients.

    Invoking it is delegated to the OperationDelegation/DMP service via the
    ``invocationDelegation`` qualifier (which carries the generated REST
    endpoint).  The input/inoutput/output variables mirror the native MQTT
    action's command / commandResponse payloads (e.g. ``Uuid``, ``State``,
    ``Outcome``) so the operation can also be rendered and invoked manually
    from the AAS Web GUI.
    """
    semantic_id: str = SKILL_OPERATION
    description: str = "Operation to invoke this skill (delegated via operation delegation)."

    input_variable: List[OperationVariableProp] = []
    output_variable: List[OperationVariableProp] = []
    in_output_variable: List[OperationVariableProp] = []

    @model_validator(mode="before")
    @classmethod
    def _strip_variable_discriminators(cls, data):
        """Strip the ``modelType`` discriminator the base Operation serializer
        tags onto each variable item — the declared element type is
        authoritative and ``extra="forbid"`` would otherwise reject it on the
        dump → validate round-trip."""
        if not isinstance(data, dict):
            return data
        out = dict(data)
        for fname in ("input_variable", "output_variable", "in_output_variable"):
            vals = out.get(fname)
            if not isinstance(vals, list):
                continue
            out[fname] = [
                {k: v for k, v in item.items() if k not in ("modelType", "model_type")}
                if isinstance(item, dict) else item
                for item in vals
            ]
        return out


class SkillInterfaceRelationship(RelationshipElement):
    """Annotated relationship: THIS skill has THIS native interface in the AID.

    ``first`` references the skill SMC (``ControlComponentInstance/skills/<skill>``),
    ``second`` references its native action in the AID
    (``AssetInterfacesDescription/interface_mqtt/interaction_metadata/actions/<skill>``).
    Replaces the generic Endpoint ``interface_reference``/``endpoint_reference``
    ReferenceElements for the per-skill native-interface linkage.
    """
    semantic_id: str = SKILL_INTERFACE_RELATIONSHIP
    description: str = "This skill has this native interface in the AID submodel."


class ResourceEndpoints(_BaseEndpoints):
    """Endpoints container holding one annotated native-interface relationship
    per skill (keyed by skill name) instead of generic Endpoint SMCs."""
    Endpoint: Dict[str, SkillInterfaceRelationship] = {}


class ExtendedSkill(_BaseSkill):
    """Skill children + the interface-reference + operation extensions, as
    DIRECT named fields.  The IDTA template marks ``Disabled``/``Modes``/
    ``Parameters``/``Errors``/``Uses`` as mandatory (One) — provided here so
    the MQTT-extended skill constructs; stations override ``Modes`` etc. via
    config.

    ``interface_reference`` points at the skill's NATIVE interface (the AID
    action it maps to — read by BT_Controller for MQTT topic resolution);
    ``operation`` is the AAS Operation exposed to clients and delegated to
    OperationDelegation."""
    semantic_id: str = EXTENDED_SKILL
    Disabled: Disabled_t = Disabled()
    Modes: Modes_t = Modes()
    Parameters: Parameters_t = Parameters()
    Errors: Errors_t = Errors()
    Uses: Uses_t = Uses()
    interface_reference: ReferenceElement = ReferenceElement(
        semantic_id=EXTENDED_SKILL_INTERFACE_REF,
        description="Reference to the corresponding AID action interface for MQTT topic resolution.",
    )
    operation: Optional[SkillOperation] = None


class ExtendedSkills(_BaseSkills):
    """Dynamic map of extended skills offered by the component instance
    (name → ExtendedSkill)."""
    semantic_id: str = EXTENDED_SKILLS
    Skill: Dict[str, ExtendedSkill] = {}


# ═══════════════════════════════════════════════════════════════════════════════
# Parameter references
# ═══════════════════════════════════════════════════════════════════════════════

class ExecParamModelRef(ReferenceElement):
    semantic_id: str = EXEC_MODEL_REF_STEP
    description: str = "The refereable to be used as a parameter within predicates"


class ExecutionModelParameter(ReferenceElement):
    """
    A parameter of the skill's execution model.

    Parameters are always reference elements pointing to either:
    - semanticId-only: points to an ontology concept (ExternalReference)
    - modelRef: points to a specific AAS/SubmodelElement (ModelReference)
    """
    semantic_id: str = f"{EXECUTION_MODEL}/Parameter"
    description: str = "A parameter of the skill execution model (semantic concept or model reference)."

    # Cardinality OneToMany → list of model references
    model_ref: List[ExecParamModelRef] = []


# ═══════════════════════════════════════════════════════════════════════════════
# Term tree — conditions and effects
# ═══════════════════════════════════════════════════════════════════════════════
class Fluent(SubmodelElementCollection):
    """
    An atomic fluent (predicate/arithmetic term) in the term tree.

    The SMC itself IS the predicate or arithmetic operation — its supplemental_semantic_ids carries
    the specific predicate URI (e.g., cssx:Operational), and its id_short
    gives it a human-readable display name.
    """
    semantic_id: str = EXEC_PREDICATE
    description: str = "Atomic predicate or arithmetic/numeric term"
    supplemental_semantic_ids: List[str] = []

    parameters: Dict[int, ReferenceElement] = {}
    comparison_values: Optional[Dict[str, Property | ReferenceElement]] = None


class Term(SubmodelElementCollection):
    """
    Recursive term node — either atomic predicate or logic/FOND operator.

    For atomic predicates, this wraps a PredicateCondition.
    For logic operators (and, or, not), ``term`` holds nested Terms.
    For FOND (oneOf), ``term`` are wrapped with when-condition strings.
    """
    semantic_id: str = f"{CSSX}/Term"
    supplemental_semantic_ids: List[str] = []  # The semantic Id of the actual logical or arithmetic term this collection represents
    description: str = "A node in the condition/effect term tree (atomic fluent or logic operator)."

    # Dynamic map: child terms/fluents keyed by name (recursive → dict default
    # cannot recurse).
    term: Dict[str, Fluent | Term] = {}


# ═══════════════════════════════════════════════════════════════════════════════
# Condition and effect groups
# ═══════════════════════════════════════════════════════════════════════════════

class PreConditions(SubmodelElementCollection):
    """Preconditions that must hold before the skill can execute."""
    semantic_id: str = f"{CSSX}PreConditions"
    description: str = "Conditions that must be satisfied before skill execution."
    term: Dict[str, Term] = {}


class InvariantConditions(SubmodelElementCollection):
    """Conditions that must hold throughout skill execution."""
    semantic_id: str = f"{CSSX}InvariantConditions"
    description: str = "Conditions that must hold throughout skill execution (invariants)."
    term: Dict[str, Term] = {}


class PostConditions(SubmodelElementCollection):
    """Conditions that must hold after skill execution."""
    semantic_id: str = f"{CSSX}PostConditions"
    description: str = "Conditions that must be satisfied after skill execution."
    term: Dict[str, Term] = {}


class Conditions(SubmodelElementCollection):
    """All condition groups for the skill."""
    semantic_id: str = f"{CSSX}SkillConditions"
    description: str = "Condition groups (pre, invariant, post) for skill execution."
    pre_conditions: Optional[PreConditions] = None
    invariant_conditions: Optional[InvariantConditions] = None
    post_conditions: Optional[PostConditions] = None


class StartEffects(SubmodelElementCollection):
    """Effects applied at the start of skill execution."""
    semantic_id: str = f"{CSSX}StartEffects"
    description: str = "Effects applied when the skill starts."
    term: Dict[str, Term] = {}


class ContinuousEffects(SubmodelElementCollection):
    """Effects applied continuously during skill execution."""
    semantic_id: str = f"{CSSX}ContinuousEffects"
    description: str = "Effects applied continuously during skill execution."
    term: Dict[str, Term] = {}


class EndEffects(SubmodelElementCollection):
    """Effects applied at the end of skill execution."""
    semantic_id: str = f"{CSSX}EndEffects"
    description: str = "Effects applied when the skill completes."
    term: Dict[str, Term] = {}


class Effects(SubmodelElementCollection):
    """All effect groups for the skill."""
    semantic_id: str = f"{CSSX}SkillEffects"
    description: str = "Effect groups (start, continuous, end) for skill execution."
    start_effects: Optional[StartEffects] = None
    continuous_effects: Optional[ContinuousEffects] = None
    end_effects: Optional[EndEffects] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Top-level ExecutionModel
# ═══════════════════════════════════════════════════════════════════════════════

class ExecutionModel(SubmodelElementCollection):
    """
    Symbolic execution model for a skill.

    Encodes the planning-level semantics: what parameters the skill binds,
    what conditions must hold, and what effects it produces. This is the
    runtime contract between the Planner and the BT_Controller.

    The BT_Controller reads this model at execution time to:
    1. Ground effect terms against parameter bindings
    2. Apply symbolic state updates via the knowledge graph
    3. Branch on FOND (oneOf) outcomes
    """
    semantic_id: str = f"{CSSX}ExecutionModel"
    description: str = (
        "Symbolic execution model: parameters, conditions, and effects. "
        "Read by the BT_Controller at runtime for state grounding."
    )

    parameters: List[ExecutionModelParameter] = []
    conditions: Optional[Conditions] = None
    effects: Optional[Effects] = None


# Ensure forward references are resolved (Pydantic v2)
Fluent.model_rebuild()
Term.model_rebuild()
Conditions.model_rebuild()
Effects.model_rebuild()
ExecutionModel.model_rebuild()
ExtendedSkill.model_rebuild()
ExtendedSkills.model_rebuild()
