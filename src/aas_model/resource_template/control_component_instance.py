"""Control Component Instance partial — mandatory Resource skills + MQTT endpoint.

Built on our extended CCI (``aas_model.submodel_templates.control_component_instance``),
which extends the generated IDTA ControlComponentInstance Skill with:
- an ``interface_reference`` pointing at the skill's NATIVE interface (the AID
  MQTT action — read by BT_Controller for MQTT topic resolution),
- an ``operation`` (AAS Operation) whose ``invocationDelegation`` qualifier
  carries the generated operation-delegation REST endpoint,
- an ``Endpoints`` container that holds, per skill, an annotated
  RelationshipElement (``this skill has this native interface``) instead of
  generic endpoint/interface ReferenceElements.

Named-field style: children are DIRECT named fields (no ``value``/``submodel_element``
wrapper); dynamic maps (endpoints/skills) are ``Dict[str, X]`` fields.
"""

from __future__ import annotations

from aas_pydantic import (
    Key, ModelReference, ReferenceElement, Qualifier,
)
from aas_pydantic.submodel_templates.control_component_instance import (
    ControlComponentInstance, Type_instance,
)

from aas_model.submodel_templates.control_component_instance import (
    ExtendedSkill, ExtendedSkills, SkillOperation, OperationVariableProp,
    SkillInterfaceRelationship, ResourceEndpoints,
)
from ._helpers import put, DEFAULT_SKILLS

# ── Reference paths (self-referential — {aas_id} resolved by id_injector) ──
CCI_SUBMODEL_REF = "{aas_id}/submodels/ControlComponentInstance"
AID_SUBMODEL_REF = "{aas_id}/submodels/AssetInterfacesDescription"

# Native AID MQTT action path: .../interface_mqtt/InteractionMetadata/actions/<name>
_NATIVE_ACTION_PATH = (
    Key(type_="Submodel", value=AID_SUBMODEL_REF),
    Key(type_="SubmodelElementCollection", value="interface_mqtt"),
    Key(type_="SubmodelElementCollection", value="InteractionMetadata"),
    Key(type_="SubmodelElementCollection", value="actions"),
)

# CCI skill path: .../Skills/<name>
_SKILL_PATH = (
    Key(type_="Submodel", value=CCI_SUBMODEL_REF),
    Key(type_="SubmodelElementCollection", value="Skills"),
)


def native_action_ref(name: str) -> ModelReference:
    """Reference to the skill's native AID MQTT action (interface_mqtt)."""
    return ModelReference(key=_NATIVE_ACTION_PATH + (Key(type_="SubmodelElementCollection", value=name),))


def skill_ref(name: str) -> ModelReference:
    """Reference to the skill SMC inside this CCI submodel."""
    return ModelReference(key=_SKILL_PATH + (Key(type_="SubmodelElementCollection", value=name),))


def _operation_variable(
    name: str, *, value_type: str = "xs:string", description: str = "",
) -> OperationVariableProp:
    v = OperationVariableProp()
    v.id_short = name
    v.value_type = value_type
    if description:
        v.description = description
    return v


def skill_operation(
    name: str, *, synchronous: bool = True, has_response: bool = True,
) -> SkillOperation:
    """The skill's AAS Operation — invoked by clients, delegated to the
    operation-delegation service via the ``invocationDelegation`` qualifier.

    The input/inoutput/output variables mirror the native MQTT action's
    command / commandResponse payloads (Uuid inout, State/Outcome output) so
    the operation can also be rendered and manually invoked from the AAS Web
    GUI.  The delegation endpoint uses the ``{delegation_base}`` /
    ``{aas_id_short}`` macros (resolved by id_injector — ``delegation_base``
    defaults to ``constants.DELEGATION_BASE`` and can be overridden per
    resource config to point at that resource's DMP).
    """
    op = SkillOperation()
    op.qualifiers = [
        Qualifier(
            type_="invocationDelegation",
            value=f"{{delegation_base}}/operations/{{aas_id_short}}/{name}",
            value_type="xs:string",
            kind="ConceptQualifier",
        ),
        Qualifier(
            type_="Synchronous" if synchronous else "Asynchronous",
            value=str(synchronous).lower(),
            # xs:string (not xs:boolean): the aas_pydantic Qualifier value is
            # a str, and basyx's trivial_cast rejects string literals for
            # xs:boolean values.
            value_type="xs:string",
            kind="ConceptQualifier",
        ),
    ]
    op.in_output_variable = [
        _operation_variable("Uuid", description="The UUID of the command"),
    ]
    if has_response:
        op.output_variable = [
            _operation_variable("State", description="The state of the command being executed"),
            _operation_variable(
                "Outcome", value_type="xs:integer",
                description="Optional FOND outcome discriminator",
            ),
        ]
    return op


def skill_interface_relationship(name: str) -> SkillInterfaceRelationship:
    """Annotated relationship: THIS skill has THIS native interface in the AID.

    ``first`` = the skill SMC in the CCI, ``second`` = the skill's native
    MQTT action in the AID.  Both use the ``{aas_id}`` macro.
    """
    rel = SkillInterfaceRelationship()
    rel.first = skill_ref(name)
    rel.second = native_action_ref(name)
    return rel


def extended_skill(
    name: str, *,
    synchronous: bool = True,
    has_response: bool = True,
    disabled: bool = False,
) -> ExtendedSkill:
    """Build a standard ExtendedSkill for the CCI.

    Sets the native-interface reference (``interface_reference`` → the AID
    MQTT action) and the delegated Operation (``operation``).
    """
    skill = ExtendedSkill()
    skill.Disabled.value = str(disabled).lower()
    skill.interface_reference.value = native_action_ref(name)
    skill.operation = skill_operation(
        name, synchronous=synchronous, has_response=has_response)
    return skill


class ResourceControlComponentInstance(ControlComponentInstance):
    """CCI variant that uses ExtendedSkills + the per-skill endpoint
    relationships and default-constructs its mandatory children."""
    Endpoints: ResourceEndpoints = ResourceEndpoints()
    Skills: ExtendedSkills = ExtendedSkills()
    Type: Type_instance = Type_instance(
        value=ModelReference(
            key=(Key(type_="Submodel", value="{aas_id}/submodels/ControlComponentType"),)
        )
    )


def control_component_instance() -> ResourceControlComponentInstance:
    """ControlComponentInstance with mandatory Resource skills + MQTT endpoint.

    Default skills: Halt (no response), Occupy, Release.  Each carries its
    native-interface reference and its delegated Operation; the Endpoints
    container holds the annotated skill ↔ native-interface relationships.
    """
    skills = ExtendedSkills()
    endpoints = ResourceEndpoints()
    for name, synchronous, has_response in DEFAULT_SKILLS:
        put(skills.Skill, name, extended_skill(
            name, synchronous=synchronous, has_response=has_response))
        put(endpoints.Endpoint, name, skill_interface_relationship(name))

    return ResourceControlComponentInstance(
        id_short="ControlComponentInstance",
        Skills=skills,
        Endpoints=endpoints,
    )
