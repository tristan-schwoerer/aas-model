"""CapabilityDescription - generated from IDTA template.
Source: Capability Description/1/0/1/IDTA 02020_Template_Capability_Description.json
"""

from __future__ import annotations

from typing import Any, ClassVar, Dict, List, Optional, TypeAlias
from aas_pydantic import (
    Capability, DynamicSubmodelElementCollection, File, MultiLanguageProperty, Property, Range, ReferenceElement, RelationshipElement, Submodel, SubmodelElementCollection, SubmodelElementList,
)
from pydantic import Field as _Field
from aas_pydantic.aas_model import AasIdString

class CapabilityComment(MultiLanguageProperty):
    id_short: AasIdString = "CapabilityComment"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/CapabilityComment/1/0"
    description: str = "Individual comment of the capability."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Capability Comment"}

class SameProperty(RelationshipElement):
    id_short: AasIdString = "SameProperty"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/SameProperty/1/0"
    description: str = "Relationship of the Property described in the Property container as first element and the identical property as second element in another Submodel or an external information source."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Same Property"}

class PropertyRange(Range):
    id_short: AasIdString = "PropertyRange"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityPropertyEnumType/Range/1/0"
    description: str = "Range made of min and max values forming an interval. A valueId shall be set to define the semantic for the values."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Property Range"}
    value_type: str = "xs:string"

class PropertyProperty(Property):
    id_short: AasIdString = "PropertyProperty"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityPropertyType/Property/1/0"
    description: str = "Property with a value describing an information data point. A valueId shall be set to define the semantic for the value."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Property Property"}
    value_type: str = "xs:string"

class PropertyMultiLanguageProperty(MultiLanguageProperty):
    id_short: AasIdString = "PropertyMultiLanguageProperty"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityPropertyType/MultiLanguageProperty/1/0"
    description: str = "Property with a value for one or more language entries with corresponding text describing an information data point. A valueId shall be set to define the semantic for the value."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Property Multi Language Property"}

class PropertySubmodelList(SubmodelElementList):
    id_short: AasIdString = "PropertySubmodelList"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityPropertyType/SubmodelElementList/1/0"
    description: str = "A list of one or more elements defined by only the enum type CapabilityPropertyType. "
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Property Submodel List"}
    type_value_list_element: str = "SubmodelElement"
    ITEM_CARDINALITY: ClassVar[str] = 'ZeroToMany'
    value: List[Any] = []

class PropertyComment(MultiLanguageProperty):
    id_short: AasIdString = "PropertyComment"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/PropertyComment/1/0"
    description: str = "General description of the property."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Property Comment"}

class PropertyContainer(SubmodelElementCollection):
    id_short: AasIdString = "PropertyContainer"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/PropertyContainer/1/0"
    description: str = "Information for a certain property as defined by CapabilityPropertyType and its descriptive elements."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Property Container"}
    SameProperty: Dict[str, SameProperty_t] = {}
    PropertyRange: Dict[str, PropertyRange_t] = {}
    PropertyProperty: Dict[str, PropertyProperty_t] = {}
    PropertyMultiLanguageProperty: Dict[str, PropertyMultiLanguageProperty_t] = {}
    PropertySubmodelList: Dict[str, PropertySubmodelList_t] = {}
    PropertyComment: Optional[PropertyComment_t] = None

class PropertySet(SubmodelElementCollection):
    id_short: AasIdString = "PropertySet"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/PropertySet/1/0"
    description: str = "Set of properties describing the capability in more detail, if existing."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Property Set"}
    PropertyContainer: Dict[str, PropertyContainer_t] = _Field(default_factory=dict, json_schema_extra={"idta_min_cardinality": 1})

class CapabilityRealizedBy(RelationshipElement):
    id_short: AasIdString = "CapabilityRealizedBy"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/CapabilityRealizedBy/1/0"
    description: str = "Relationship between the Capability element in the CapabilityContainer as first element and a Skill implementation, not defined in this Submodel template, as second element."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Capability Realized By"}

class CapabilityComposedOf(RelationshipElement):
    id_short: AasIdString = "CapabilityComposedOf"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/CapabilityComposedOf/1/0"
    description: str = "Relationship between a composed capability as first element and one of its minimum two subordinate capabilities as second element."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Capability Composed Of"}

class ComposedOfComment(MultiLanguageProperty):
    id_short: AasIdString = "ComposedOfComment"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/ComposedOfComment/1/0"
    description: str = "Comment to describe the composition in human readable form."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Composed Of Comment"}

class ComposedOfContainer(SubmodelElementCollection):
    id_short: AasIdString = "ComposedOfContainer"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/ComposedOfContainer/1/0"
    description: str = "Container corresponding to one composition for the Capability in the CapabilityContainer."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Composed Of Container"}
    CapabilityComposedOf: Dict[str, CapabilityComposedOf_t] = _Field(default_factory=dict, json_schema_extra={"idta_min_cardinality": 2})
    ComposedOfComment: Optional[ComposedOfComment_t] = None

class ComposedOfSet(SubmodelElementCollection):
    id_short: AasIdString = "ComposedOfSet"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/ComposedOfSet/1/0"
    description: str = "If composition(s) for the Capability element in the CapabilityContainer exists, this set has to be created."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Composed Of Set"}
    ComposedOfContainer: Dict[str, ComposedOfContainer_t] = _Field(default_factory=dict, json_schema_extra={"idta_min_cardinality": 1})

class CapabilityGeneralizedBy(RelationshipElement):
    id_short: AasIdString = "CapabilityGeneralizedBy"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/CapabilityGeneralizedBy/1/0"
    description: str = "Relationship between the Capability as first element, described in the CapabilityContainer, and a more general Capability as second element."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Capability Generalized By"}

class GeneralizedBySet(SubmodelElementCollection):
    id_short: AasIdString = "GeneralizedBySet"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/GeneralizedBySet/1/0"
    description: str = "If generalization(s) for the Capability element in the CapabilityContainer exists, this set has to be created."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Generalized By Set"}
    CapabilityGeneralizedBy: Dict[str, CapabilityGeneralizedBy_t] = _Field(default_factory=dict, json_schema_extra={"idta_min_cardinality": 1})

class BasicConstraint(Property):
    id_short: AasIdString = "BasicConstraint"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/PropertyConstraintType/BasicConstraint/1/0"
    description: str = "Property element which can be used to validate the constraint for the considered Properties in this PropertyConstraintContainer against other properties."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Basic Constraint"}
    value_type: str = "xs:string"

class CustomConstraint(DynamicSubmodelElementCollection):
    id_short: AasIdString = "CustomConstraint"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/PropertyConstraintType/CustomConstraint/1/0"
    description: str = "SubmodelElement which can be used to validate the constraint for the considered Properties in this PropertyConstraintContainer against other properties. This can be freely defined for the purpose of constraining a property and is not specified in this Submodel Template."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Custom Constraint"}

class OCLConstraint(File):
    id_short: AasIdString = "OCLConstraint"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/PropertyConstraintType/OCLConstraint/1/0"
    description: str = "Object Contraint Language (OCL) as File element which can be used to validate the constraint for the considered Properties in this PropertyConstraintContainer against other properties."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "OCL Constraint"}
    content_type: str = "application/octet-stream"

class OperationConstraint(ReferenceElement):
    id_short: AasIdString = "OperationConstraint"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/PropertyConstraintType/OperationConstraint/1/0"
    description: str = "Reference to an (external) Operation element which can be used to validate the constraint for the considered Properties in this PropertyConstraintContainer against other properties."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Operation Constraint"}

class ConstraintType(Property):
    id_short: AasIdString = "ConstraintType"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/ConstraintType/1/0"
    description: str = "Abstract Enum type of allowed SubmodelElements for these Properties constraints. Exactly one of the SubmodelElements below must be instanciated, e.g., similar to SubmodelElementList with exactly one element."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Constraint Type"}
    value_type: str = "xs:string"
    FORM_CHOICES: ClassVar[tuple] = ('OperationConstraint', 'OCLConstraint', 'BasicConstraint', 'CustomConstraint')

class PropertyConditionalType(Property):
    id_short: AasIdString = "PropertyConditionalType"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/PropertyConditionalType/1/0"
    description: str = "Defines the type of the property conditions as defined in the ConceptDescription with the same name (PropertyConditionalType)."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Property Conditional Type"}
    value_type: str = "xs:string"

class ConstraintHasProperty(RelationshipElement):
    id_short: AasIdString = "ConstraintHasProperty"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/ConstraintHasProperty/1/0"
    description: str = "Relates the PropertyConstraint as first element to a Property from a PropertyContainer as second element."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Constraint Has Property"}

class ConstraintPropertyRelations(SubmodelElementCollection):
    id_short: AasIdString = "ConstraintPropertyRelations"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/ConstraintPropertyRelations/1/0"
    description: str = "Contains all relationships for the constraint in the PropertyConstraintContainer."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Constraint Property Relations"}
    ConstraintHasProperty: Dict[str, ConstraintHasProperty_t] = _Field(default_factory=dict, json_schema_extra={"idta_min_cardinality": 1})

class PropertyConstraintContainer(SubmodelElementCollection):
    id_short: AasIdString = "PropertyConstraintContainer"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/PropertyConstraintContainer/1/0"
    description: str = "If one or more constraints exist for a Capability Property, then for every constraint a PropertyConstraintContainer has to be created."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Property Constraint Container"}
    IDTA_ONE_OF: ClassVar[tuple] = ('BasicConstraint', 'CustomConstraint', 'OCLConstraint', 'OperationConstraint')
    BasicConstraint: Optional[BasicConstraint_t] = None
    CustomConstraint: Optional[CustomConstraint_t] = None
    OCLConstraint: Optional[OCLConstraint_t] = None
    OperationConstraint: Optional[OperationConstraint_t] = None
    ConstraintType: ConstraintType_t
    PropertyConditionalType: PropertyConditionalType_t
    ConstraintPropertyRelations: ConstraintPropertyRelations_t

class TransitionConstrainedBy(RelationshipElement):
    id_short: AasIdString = "TransitionConstrainedBy"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/TransitionConstrainedBy/1/0"
    description: str = "Relates the constrained Capability as first element to a constraining Capability from another CapabilityContainer as second element."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Transition Constrained By"}

class TransitionConditionalType(Property):
    id_short: AasIdString = "TransitionConditionalType"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/TransitionConditionalType/1/0"
    description: str = "Defines the element TransitionConstrainedBy of TransitionConstraintType."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Transition Conditional Type"}
    value_type: str = "xs:string"

class TransitionConstraintContainer(SubmodelElementCollection):
    id_short: AasIdString = "TransitionConstraintContainer"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/TransitionConstraintContainer/1/0"
    description: str = "If one or more constraints exist for a Capability, then for every transitional constraint a TransitionConstraintContainer has to be created."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Transition Constraint Container"}
    TransitionConstrainedBy: TransitionConstrainedBy_t
    TransitionConditionalType: TransitionConditionalType_t

class ConstraintSet(SubmodelElementCollection):
    id_short: AasIdString = "ConstraintSet"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/ConstraintSet/1/0"
    description: str = "If constraint(s) for the Capability element in the CapabilityContainer exists, this set has to be created."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Constraint Set"}
    PropertyConstraintContainer: Dict[str, PropertyConstraintContainer_t] = {}
    TransitionConstraintContainer: Dict[str, TransitionConstraintContainer_t] = {}

class CapabilityRelations(SubmodelElementCollection):
    id_short: AasIdString = "CapabilityRelations"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/CapabilityRelations/1/0"
    description: str = "Collection of relationships for the capability, if existing."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Capability Relations"}
    CapabilityRealizedBy: Dict[str, CapabilityRealizedBy_t] = {}
    ComposedOfSet: Optional[ComposedOfSet_t] = None
    GeneralizedBySet: Dict[str, GeneralizedBySet_t] = {}
    ConstraintSet: Dict[str, ConstraintSet_t] = {}

class CapabilityContainer(SubmodelElementCollection):
    id_short: AasIdString = "CapabilityContainer"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/CapabilityContainer/1/0"
    description: str = "A Container for one capability and all its additional descriptive elements."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Capability Container"}
    Capability: Capability_t
    CapabilityComment: Optional[CapabilityComment_t] = None
    PropertySet: Dict[str, PropertySet_t] = {}
    CapabilityRelations: Optional[CapabilityRelations_t] = None

class CapabilitySet(SubmodelElementCollection):
    id_short: AasIdString = "CapabilitySet"
    semantic_id: str = "https://admin-shell.io/idta/CapabilityDescription/CapabilitySet/1/0"
    description: str = "A Set of CapabilityContainer for a Use Case for the asset."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Capability Set"}
    CapabilityContainer: Dict[str, CapabilityContainer_t] = _Field(default_factory=dict, json_schema_extra={"idta_min_cardinality": 1})

class CapabilityDescription(Submodel):
    id_short: AasIdString = "CapabilityDescription"
    semantic_id: str = "https://admin-shell.io/idta/SubmodelTemplate/CapabilityDescription/1/0"
    description: str = "Definition of the Submodel CapabilityDescription identified by its semanticId. The Submodel idShort can be picked freely."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Submodel Template Capability Description"}
    VERSION: ClassVar[str] = "1"
    REVISION: ClassVar[str] = "0"
    CapabilitySet: Dict[str, CapabilitySet_t] = _Field(default_factory=dict, json_schema_extra={"idta_min_cardinality": 1})

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
