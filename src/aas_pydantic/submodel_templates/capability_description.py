"""CapabilityDescription — generated from IDTA template."""

from __future__ import annotations

from typing import Any, ClassVar, List, Dict, Optional, TypeAlias
from aas_pydantic import (
    Capability, ExternalReference, File, Key, ModelReference, MultiLanguageProperty, Property, Range, ReferenceElement, RelationshipElement, Submodel, SubmodelElement, SubmodelElementCollection, SubmodelElementList,
)

class CapabilityComment(MultiLanguageProperty):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/CapabilityComment/1/0"
    description: str = "Individual comment of the capability."

class SameProperty(RelationshipElement):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/SameProperty/1/0"
    description: str = "Relationship of the Property described in the Property container as first element and the identical property as second element in another Submodel or an external information source."
    first: ExternalReference = ExternalReference(
        key=(
            Key(type_="GlobalReference", value="urn:example:capability-description:same-property:first"),
        ),
    ),
    second: ExternalReference = ExternalReference(
        key=(
            Key(type_="GlobalReference", value="urn:example:capability-description:same-property:second"),
        ),
    ),

class PropertyRange(Range):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityPropertyEnumType/Range/1/0"
    description: str = "Range made of min and max values forming an interval. A valueId shall be set to define the semantic for the values."
    value_type: str = "xs:string"

class PropertyProperty(Property):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityPropertyType/Property/1/0"
    description: str = "Property with a value describing an information data point. A valueId shall be set to define the semantic for the value."
    value_type: str = "xs:string"

class PropertyMultiLanguageProperty(MultiLanguageProperty):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityPropertyType/MultiLanguageProperty/1/0"
    description: str = "Property with a value for one or more language entries with corresponding text describing an information data point. A valueId shall be set to define the semantic for the value."

class PropertySubmodelList(SubmodelElementList):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityPropertyType/SubmodelElementList/1/0"
    description: str = "A list of one or more elements defined by only the enum type CapabilityPropertyType. "
    value: List[Any] = []

class PropertyComment(MultiLanguageProperty):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/PropertyComment/1/0"
    description: str = "General description of the property."

class PropertyContainer(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/PropertyContainer/1/0"
    description: str = "Information for a certain property as defined by CapabilityPropertyType and its descriptive elements."
    SameProperty: Dict[str, SameProperty_t] = {}
    PropertyRange: Dict[str, PropertyRange_t] = {}
    PropertyProperty: Dict[str, PropertyProperty_t] = {}
    PropertyMultiLanguageProperty: Dict[str, PropertyMultiLanguageProperty_t] = {}
    PropertySubmodelList: Dict[str, PropertySubmodelList_t] = {}
    PropertyComment: Optional[PropertyComment_t] = None

class PropertySet(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/PropertySet/1/0"
    description: str = "Set of properties describing the capability in more detail, if existing."
    PropertyContainer: Dict[str, PropertyContainer_t] = {}

class CapabilityRealizedBy(RelationshipElement):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/CapabilityRealizedBy/1/0"
    description: str = "Relationship between the Capability element in the CapabilityContainer as first element and a Skill implementation, not defined in this Submodel template, as second element."
    first: ModelReference = ModelReference(
        key=(
            Key(type_="Submodel", value="https://admin-shell.io/idta/CapabilityDescription/1/0/Submodel"),
            Key(type_="SubmodelElementCollection", value="CapabilitySet"),
            Key(type_="SubmodelElementCollection", value="CapabilityContainer"),
            Key(type_="Capability", value="Capability"),
        ),
    ),
    second: ExternalReference = ExternalReference(
        key=(
            Key(type_="GlobalReference", value="urn:example:capability-description:capability-realized-by:skill"),
        ),
    ),

class CapabilityComposedOf(RelationshipElement):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/CapabilityComposedOf/1/0"
    description: str = "Relationship between a composed capability as first element and one of its minimum two subordinate capabilities as second element."
    first: ModelReference = ModelReference(
        key=(
            Key(type_="Submodel", value="https://admin-shell.io/idta/CapabilityDescription/1/0/Submodel"),
            Key(type_="SubmodelElementCollection", value="CapabilitySet"),
            Key(type_="SubmodelElementCollection", value="CapabilityContainer"),
            Key(type_="Capability", value="Capability"),
        ),
    ),
    second: ModelReference = ModelReference(
        key=(
            Key(type_="Submodel", value="https://admin-shell.io/idta/CapabilityDescription/1/0/Submodel"),
            Key(type_="SubmodelElementCollection", value="CapabilitySet"),
            Key(type_="SubmodelElementCollection", value="CapabilityContainer"),
            Key(type_="Capability", value="Capability"),
        ),
    ),

class ComposedOfComment(MultiLanguageProperty):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/ComposedOfComment/1/0"
    description: str = "Comment to describe the composition in human readable form."

class ComposedOfContainer(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/ComposedOfContainer/1/0"
    description: str = "Container corresponding to one composition for the Capability in the CapabilityContainer."
    CapabilityComposedOf: Dict[str, CapabilityComposedOf_t] = {}
    ComposedOfComment: Optional[ComposedOfComment_t] = None

class ComposedOfSet(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/ComposedOfSet/1/0"
    description: str = "If composition(s) for the Capability element in the CapabilityContainer exists, this set has to be created."
    ComposedOfContainer: Dict[str, ComposedOfContainer_t] = {}

class CapabilityGeneralizedBy(RelationshipElement):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/CapabilityGeneralizedBy/1/0"
    description: str = "Relationship between the Capability as first element, described in the CapabilityContainer, and a more general Capability as second element."
    first: ModelReference = ModelReference(
        key=(
            Key(type_="Submodel", value="https://admin-shell.io/idta/CapabilityDescription/1/0/Submodel"),
            Key(type_="SubmodelElementCollection", value="CapabilitySet"),
            Key(type_="SubmodelElementCollection", value="CapabilityContainer"),
            Key(type_="Capability", value="Capability"),
        ),
    ),
    second: ModelReference = ModelReference(
        key=(
            Key(type_="Submodel", value="https://admin-shell.io/idta/CapabilityDescription/1/0/Submodel"),
            Key(type_="SubmodelElementCollection", value="CapabilitySet"),
            Key(type_="SubmodelElementCollection", value="CapabilityContainer"),
            Key(type_="Capability", value="Capability"),
        ),
    ),

class GeneralizedBySet(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/GeneralizedBySet/1/0"
    description: str = "If generalization(s) for the Capability element in the CapabilityContainer exists, this set has to be created."
    CapabilityGeneralizedBy: Dict[str, CapabilityGeneralizedBy_t] = {}

class BasicConstraint(Property):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/PropertyConstraintType/BasicConstraint/1/0"
    description: str = "Property element which can be used to validate the constraint for the considered Properties in this PropertyConstraintContainer against other properties."
    value_type: str = "xs:string"

class CustomConstraint(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/PropertyConstraintType/CustomConstraint/1/0"
    description: str = "SubmodelElement which can be used to validate the constraint for the considered Properties in this PropertyConstraintContainer against other properties. This can be freely defined for the purpose of constraining a property and is not specified in this Submodel Template."
    pass

class OCLConstraint(File):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/PropertyConstraintType/OCLConstraint/1/0"
    description: str = "Object Contraint Language (OCL) as File element which can be used to validate the constraint for the considered Properties in this PropertyConstraintContainer against other properties."

class OperationConstraint(ReferenceElement):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/PropertyConstraintType/OperationConstraint/1/0"
    description: str = "Reference to an (external) Operation element which can be used to validate the constraint for the considered Properties in this PropertyConstraintContainer against other properties."

class ConstraintType(Property):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/ConstraintType/1/0"
    description: str = "Abstract Enum type of allowed SubmodelElements for these Properties constraints. Exactly one of the SubmodelElements below must be instanciated, e.g., similar to SubmodelElementList with exactly one element."
    value_type: str = "xs:string"

class PropertyConditionalType(Property):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/PropertyConditionalType/1/0"
    description: str = "Defines the type of the property conditions as defined in the ConceptDescription with the same name (PropertyConditionalType)."
    value_type: str = "xs:string"

class ConstraintHasProperty(RelationshipElement):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/ConstraintHasProperty/1/0"
    description: str = "Relates the PropertyConstraint as first element to a Property from a PropertyContainer as second element."
    first: ModelReference = ModelReference(
        key=(
            Key(type_="Submodel", value="https://admin-shell.io/idta/CapabilityDescription/1/0/Submodel"),
            Key(type_="SubmodelElementCollection", value="CapabilitySet"),
            Key(type_="SubmodelElementCollection", value="CapabilityContainer"),
            Key(type_="SubmodelElementCollection", value="CapabilityRelations"),
            Key(type_="SubmodelElementCollection", value="ConstraintSet"),
            Key(type_="SubmodelElementCollection", value="PropertyConstraintContainer"),
            Key(type_="Property", value="BasicConstraint"),
        ),
    ),
    second: ModelReference = ModelReference(
        key=(
            Key(type_="Submodel", value="https://admin-shell.io/idta/CapabilityDescription/1/0/Submodel"),
            Key(type_="SubmodelElementCollection", value="CapabilitySet"),
            Key(type_="SubmodelElementCollection", value="CapabilityContainer"),
            Key(type_="SubmodelElementCollection", value="PropertySet"),
            Key(type_="SubmodelElementCollection", value="PropertyContainer"),
            Key(type_="Property", value="PropertyProperty"),
        ),
    ),

class ConstraintPropertyRelations(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/ConstraintPropertyRelations/1/0"
    description: str = "Contains all relationships for the constraint in the PropertyConstraintContainer."
    ConstraintHasProperty: Dict[str, ConstraintHasProperty_t] = {}

class PropertyConstraintContainer(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/PropertyConstraintContainer/1/0"
    description: str = "If one or more constraints exist for a Capability Property, then for every constraint a PropertyConstraintContainer has to be created."
    BasicConstraint: BasicConstraint_t
    CustomConstraint: CustomConstraint_t
    OCLConstraint: OCLConstraint_t
    OperationConstraint: OperationConstraint_t
    ConstraintType: ConstraintType_t
    PropertyConditionalType: PropertyConditionalType_t
    ConstraintPropertyRelations: ConstraintPropertyRelations_t

class TransitionConstrainedBy(RelationshipElement):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/TransitionConstrainedBy/1/0"
    description: str = "Relates the constrained Capability as first element to a constraining Capability from another CapabilityContainer as second element."
    first: ModelReference = ModelReference(
        key=(
            Key(type_="Submodel", value="https://admin-shell.io/idta/CapabilityDescription/1/0/Submodel"),
            Key(type_="SubmodelElementCollection", value="CapabilitySet"),
            Key(type_="SubmodelElementCollection", value="CapabilityContainer"),
            Key(type_="Capability", value="Capability"),
        ),
    ),
    second: ModelReference = ModelReference(
        key=(
            Key(type_="Submodel", value="https://admin-shell.io/idta/CapabilityDescription/1/0/Submodel"),
            Key(type_="SubmodelElementCollection", value="CapabilitySet"),
            Key(type_="SubmodelElementCollection", value="CapabilityContainer"),
            Key(type_="Capability", value="Capability"),
        ),
    ),

class TransitionConditionalType(Property):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/TransitionConditionalType/1/0"
    description: str = "Defines the element TransitionConstrainedBy of TransitionConstraintType."
    value_type: str = "xs:string"

class TransitionConstraintContainer(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/TransitionConstraintContainer/1/0"
    description: str = "If one or more constraints exist for a Capability, then for every transitional constraint a TransitionConstraintContainer has to be created."
    TransitionConstrainedBy: TransitionConstrainedBy_t
    TransitionConditionalType: TransitionConditionalType_t

class ConstraintSet(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/ConstraintSet/1/0"
    description: str = "If constraint(s) for the Capability element in the CapabilityContainer exists, this set has to be created."
    PropertyConstraintContainer: Dict[str, PropertyConstraintContainer_t] = {}
    TransitionConstraintContainer: Dict[str, TransitionConstraintContainer_t] = {}

class CapabilityRelations(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/CapabilityRelations/1/0"
    description: str = "Collection of relationships for the capability, if existing."
    CapabilityRealizedBy: Dict[str, CapabilityRealizedBy_t] = {}
    ComposedOfSet: Optional[ComposedOfSet_t] = None
    GeneralizedBySet: Dict[str, GeneralizedBySet_t] = {}
    ConstraintSet: Dict[str, ConstraintSet_t] = {}

class CapabilityContainer(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/CapabilityContainer/1/0"
    description: str = "A Container for one capability and all its additional descriptive elements."
    Capability: Capability_t
    CapabilityComment: Optional[CapabilityComment_t] = None
    PropertySet: Dict[str, PropertySet_t] = {}
    CapabilityRelations: Optional[CapabilityRelations_t] = None

class CapabilitySet(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/CapabilitySet/1/0"
    description: str = "A Set of CapabilityContainer for a Use Case for the asset."
    CapabilityContainer: Dict[str, CapabilityContainer_t] = {}

class CapabilityDescription(Submodel):
    semantic_id: str = "https://admin-shell.io/idta/SubmodelTemplate/CapabilityDescription/1/0"
    description: str = "Definition of the Submodel CapabilityDescription identified by its semanticId. The Submodel idShort can be picked freely."
    VERSION: ClassVar[str] = "1"
    REVISION: ClassVar[str] = "0"
    CapabilitySet: Dict[str, CapabilitySet_t] = {}

# ── Clash aliases: field name == element class name ──
# alias so field ``SameProperty_t`` can name a class of the same id_short
SameProperty_t: TypeAlias = SameProperty
# alias so field ``PropertyRange_t`` can name a class of the same id_short
PropertyRange_t: TypeAlias = PropertyRange
# alias so field ``PropertyProperty_t`` can name a class of the same id_short
PropertyProperty_t: TypeAlias = PropertyProperty
# alias so field ``PropertyMultiLanguageProperty_t`` can name a class of the same id_short
PropertyMultiLanguageProperty_t: TypeAlias = PropertyMultiLanguageProperty
# alias so field ``PropertySubmodelList_t`` can name a class of the same id_short
PropertySubmodelList_t: TypeAlias = PropertySubmodelList
# alias so field ``PropertyComment_t`` can name a class of the same id_short
PropertyComment_t: TypeAlias = PropertyComment
# alias so field ``PropertyContainer_t`` can name a class of the same id_short
PropertyContainer_t: TypeAlias = PropertyContainer
# alias so field ``CapabilityComposedOf_t`` can name a class of the same id_short
CapabilityComposedOf_t: TypeAlias = CapabilityComposedOf
# alias so field ``ComposedOfComment_t`` can name a class of the same id_short
ComposedOfComment_t: TypeAlias = ComposedOfComment
# alias so field ``ComposedOfContainer_t`` can name a class of the same id_short
ComposedOfContainer_t: TypeAlias = ComposedOfContainer
# alias so field ``CapabilityGeneralizedBy_t`` can name a class of the same id_short
CapabilityGeneralizedBy_t: TypeAlias = CapabilityGeneralizedBy
# alias so field ``ConstraintHasProperty_t`` can name a class of the same id_short
ConstraintHasProperty_t: TypeAlias = ConstraintHasProperty
# alias so field ``BasicConstraint_t`` can name a class of the same id_short
BasicConstraint_t: TypeAlias = BasicConstraint
# alias so field ``CustomConstraint_t`` can name a class of the same id_short
CustomConstraint_t: TypeAlias = CustomConstraint
# alias so field ``OCLConstraint_t`` can name a class of the same id_short
OCLConstraint_t: TypeAlias = OCLConstraint
# alias so field ``OperationConstraint_t`` can name a class of the same id_short
OperationConstraint_t: TypeAlias = OperationConstraint
# alias so field ``ConstraintType_t`` can name a class of the same id_short
ConstraintType_t: TypeAlias = ConstraintType
# alias so field ``PropertyConditionalType_t`` can name a class of the same id_short
PropertyConditionalType_t: TypeAlias = PropertyConditionalType
# alias so field ``ConstraintPropertyRelations_t`` can name a class of the same id_short
ConstraintPropertyRelations_t: TypeAlias = ConstraintPropertyRelations
# alias so field ``TransitionConstrainedBy_t`` can name a class of the same id_short
TransitionConstrainedBy_t: TypeAlias = TransitionConstrainedBy
# alias so field ``TransitionConditionalType_t`` can name a class of the same id_short
TransitionConditionalType_t: TypeAlias = TransitionConditionalType
# alias so field ``PropertyConstraintContainer_t`` can name a class of the same id_short
PropertyConstraintContainer_t: TypeAlias = PropertyConstraintContainer
# alias so field ``TransitionConstraintContainer_t`` can name a class of the same id_short
TransitionConstraintContainer_t: TypeAlias = TransitionConstraintContainer
# alias so field ``CapabilityRealizedBy_t`` can name a class of the same id_short
CapabilityRealizedBy_t: TypeAlias = CapabilityRealizedBy
# alias so field ``ComposedOfSet_t`` can name a class of the same id_short
ComposedOfSet_t: TypeAlias = ComposedOfSet
# alias so field ``GeneralizedBySet_t`` can name a class of the same id_short
GeneralizedBySet_t: TypeAlias = GeneralizedBySet
# alias so field ``ConstraintSet_t`` can name a class of the same id_short
ConstraintSet_t: TypeAlias = ConstraintSet
# alias so field ``Capability_t`` can name a class of the same id_short
Capability_t: TypeAlias = Capability
# alias so field ``CapabilityComment_t`` can name a class of the same id_short
CapabilityComment_t: TypeAlias = CapabilityComment
# alias so field ``PropertySet_t`` can name a class of the same id_short
PropertySet_t: TypeAlias = PropertySet
# alias so field ``CapabilityRelations_t`` can name a class of the same id_short
CapabilityRelations_t: TypeAlias = CapabilityRelations
# alias so field ``CapabilityContainer_t`` can name a class of the same id_short
CapabilityContainer_t: TypeAlias = CapabilityContainer
# alias so field ``CapabilitySet_t`` can name a class of the same id_short
CapabilitySet_t: TypeAlias = CapabilitySet

# ── Resolve forward references (Pydantic circular refs) ──
CapabilityComment.model_rebuild()
SameProperty.model_rebuild()
PropertyRange.model_rebuild()
PropertyProperty.model_rebuild()
PropertyMultiLanguageProperty.model_rebuild()
PropertySubmodelList.model_rebuild()
PropertyComment.model_rebuild()
PropertyContainer.model_rebuild()
PropertySet.model_rebuild()
CapabilityRealizedBy.model_rebuild()
CapabilityComposedOf.model_rebuild()
ComposedOfComment.model_rebuild()
ComposedOfContainer.model_rebuild()
ComposedOfSet.model_rebuild()
CapabilityGeneralizedBy.model_rebuild()
GeneralizedBySet.model_rebuild()
BasicConstraint.model_rebuild()
CustomConstraint.model_rebuild()
OCLConstraint.model_rebuild()
OperationConstraint.model_rebuild()
ConstraintType.model_rebuild()
PropertyConditionalType.model_rebuild()
ConstraintHasProperty.model_rebuild()
ConstraintPropertyRelations.model_rebuild()
PropertyConstraintContainer.model_rebuild()
TransitionConstrainedBy.model_rebuild()
TransitionConditionalType.model_rebuild()
TransitionConstraintContainer.model_rebuild()
ConstraintSet.model_rebuild()
CapabilityRelations.model_rebuild()
CapabilityContainer.model_rebuild()
CapabilitySet.model_rebuild()
CapabilityDescription.model_rebuild()
