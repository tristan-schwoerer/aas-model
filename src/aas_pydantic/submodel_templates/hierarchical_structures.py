"""HierarchicalStructures - generated from IDTA template.
Source: Hierarchical Structures enabling Bills of Material/1/1/2/IDTA 02011-1-1-2_Template_HSEBoM_forAASMetamodelV3.1.json
"""

from __future__ import annotations

from typing import ClassVar, Dict, Optional, TypeAlias
from aas_pydantic import (
    Entity, Property, RelationshipElement, Submodel,
)
from pydantic import Field as _Field
from aas_pydantic.aas_model import AasIdString

class SameAs(RelationshipElement):
    id_short: AasIdString = "SameAs"
    semantic_id: str = "https://admin-shell.io/idta/HierarchicalStructures/SameAs/1/0"
    description: str = "Reference between two Entities in the same Submodel or across Submodels."

class IsPartOf(RelationshipElement):
    id_short: AasIdString = "IsPartOf"
    semantic_id: str = "https://admin-shell.io/idta/HierarchicalStructures/IsPartOf/1/0"
    description: str = "Modeling of logical connections between components and sub-components. Either this or \"HasPart\" must be used, not both."

class HasPart(RelationshipElement):
    id_short: AasIdString = "HasPart"
    semantic_id: str = "https://admin-shell.io/idta/HierarchicalStructures/HasPart/1/0"
    description: str = "Modeling of logical connections between components and sub-components. Either this or \"IsPartOf\" must be used, not both."

class BulkCount(Property):
    id_short: AasIdString = "BulkCount"
    semantic_id: str = "https://admin-shell.io/idta/HierarchicalStructures/BulkCount/1/0"
    description: str = "To be used if bulk components are referenced, e.g., a 10x M4x30 screw."
    value_type: str = "xs:unsignedLong"

class Node(Entity):
    id_short: AasIdString = "Node"
    semantic_id: str = "https://admin-shell.io/idta/HierarchicalStructures/Node/1/0"
    description: str = "Base entry point for the Entity tree in this Submodel, this must be a Self-managed Entity reflecting the Assets administrated in the Asset Administration Shell this Submodel is part of. The idShort of the EntryNode can be picked freely and may reflect a name of the asset."
    entity_type: str = "SelfManagedEntity"
    Node: Dict[str, Node_t] = {}
    SameAs: Dict[str, SameAs_t] = {}
    IsPartOf: Dict[str, IsPartOf_t] = {}
    HasPart: Dict[str, HasPart_t] = {}
    BulkCount: Optional[BulkCount_t] = None

class IsPartOf_hierarchical_structures(RelationshipElement):
    id_short: AasIdString = "IsPartOf"
    semantic_id: str = "https://admin-shell.io/idta/HierarchicalStructures/IsPartOf/1/0"
    description: str = "Modeling of logical connections between asset and sub-asset. Either this or \"HasPart\" must be used, not both."

class EntryNode(Entity):
    id_short: AasIdString = "EntryNode"
    semantic_id: str = "https://admin-shell.io/idta/HierarchicalStructures/EntryNode/1/0"
    description: str = "Base entry point for the Entity tree in this Submodel, this must be a Self-managed Entity reflecting the Assets administrated in the AAS this Submodel is part of."
    entity_type: str = "SelfManagedEntity"
    Node: Dict[str, Node_t] = _Field(default_factory=dict, json_schema_extra={"idta_min_cardinality": 1})
    SameAs: Dict[str, SameAs_t] = {}
    IsPartOf: Dict[str, IsPartOf_hierarchical_structures] = {}
    HasPart: Dict[str, HasPart_t] = {}

class ArcheType(Property):
    id_short: AasIdString = "ArcheType"
    semantic_id: str = "https://admin-shell.io/idta/HierarchicalStructures/ArcheType/1/0"
    description: str = "ArcheType of the Submodel, there are three allowed enumeration entries: 1. \u201cFull\u201d, 2. \u201cOneDown\u201d and 3. \u201cOneUp\u201d. "
    value_type: str = "xs:string"
    FORM_CHOICES: ClassVar[tuple] = ('Full', 'OneDown', 'OneUp')

class HierarchicalStructures(Submodel):
    id_short: AasIdString = "HierarchicalStructures"
    semantic_id: str = "https://admin-shell.io/idta/HierarchicalStructures/1/1/Submodel"
    description: str = "The Submodel HierarchicalStructures identified by its semanticId. The Submodel idShort can be picked freely."
    VERSION: ClassVar[str] = "1"
    REVISION: ClassVar[str] = "1"
    EntryNode: EntryNode_t
    ArcheType: ArcheType_t

# alias so field ``Node_t`` can name a class of the same id_short
Node_t: TypeAlias = Node
# alias so field ``SameAs_t`` can name a class of the same id_short
SameAs_t: TypeAlias = SameAs
# alias so field ``IsPartOf_t`` can name a class of the same id_short
IsPartOf_t: TypeAlias = IsPartOf
# alias so field ``HasPart_t`` can name a class of the same id_short
HasPart_t: TypeAlias = HasPart
# alias so field ``BulkCount_t`` can name a class of the same id_short
BulkCount_t: TypeAlias = BulkCount
# alias so field ``EntryNode_t`` can name a class of the same id_short
EntryNode_t: TypeAlias = EntryNode
# alias so field ``ArcheType_t`` can name a class of the same id_short
ArcheType_t: TypeAlias = ArcheType
# ── Resolve forward references (Pydantic circular refs) ──
SameAs.model_rebuild()
IsPartOf.model_rebuild()
HasPart.model_rebuild()
BulkCount.model_rebuild()
Node.model_rebuild()
IsPartOf_hierarchical_structures.model_rebuild()
EntryNode.model_rebuild()
ArcheType.model_rebuild()
HierarchicalStructures.model_rebuild()
