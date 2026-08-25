"""HierarchicalStructures — generated from IDTA template."""

from __future__ import annotations

from typing import Any, ClassVar, List, Dict, Optional, TypeAlias
from aas_pydantic import (
    Entity, ExternalReference, Key, Property, RelationshipElement, Submodel, SubmodelElement, SubmodelElementCollection, SubmodelElementList,
)

class SameAs(RelationshipElement):
    semantic_id: str = "https://admin-shell.io/idta/HierarchicalStructures/SameAs/1/0"
    description: str = "Reference between two Entities in the same Submodel or across Submodels."
    first: ExternalReference = ExternalReference(
        key=(
            Key(type_="GlobalReference", value="https://admin-shell.io/SMT/General/IntentionallyEmpty"),
        ),
    ),
    second: ExternalReference = ExternalReference(
        key=(
            Key(type_="GlobalReference", value="https://admin-shell.io/SMT/General/IntentionallyEmpty"),
        ),
    ),

class IsPartOf(RelationshipElement):
    semantic_id: str = "https://admin-shell.io/idta/HierarchicalStructures/IsPartOf/1/0"
    description: str = "Modeling of logical connections between components and sub-components. Either this or \"HasPart\" must be used, not both."
    first: ExternalReference = ExternalReference(
        key=(
            Key(type_="GlobalReference", value="https://admin-shell.io/SMT/General/IntentionallyEmpty"),
        ),
    ),
    second: ExternalReference = ExternalReference(
        key=(
            Key(type_="GlobalReference", value="https://admin-shell.io/SMT/General/IntentionallyEmpty"),
        ),
    ),

class HasPart(RelationshipElement):
    semantic_id: str = "https://admin-shell.io/idta/HierarchicalStructures/HasPart/1/0"
    description: str = "Modeling of logical connections between components and sub-components. Either this or \"IsPartOf\" must be used, not both."
    first: ExternalReference = ExternalReference(
        key=(
            Key(type_="GlobalReference", value="https://admin-shell.io/SMT/General/IntentionallyEmpty"),
        ),
    ),
    second: ExternalReference = ExternalReference(
        key=(
            Key(type_="GlobalReference", value="https://admin-shell.io/SMT/General/IntentionallyEmpty"),
        ),
    ),

class BulkCount(Property):
    semantic_id: str = "https://admin-shell.io/idta/HierarchicalStructures/BulkCount/1/0"
    description: str = "To be used if bulk components are referenced, e.g., a 10x M4x30 screw."
    value_type: str = "xs:unsignedLong"

class Node(Entity):
    semantic_id: str = "https://admin-shell.io/idta/HierarchicalStructures/Node/1/0"
    description: str = "Base entry point for the Entity tree in this Submodel, this must be a Self-managed Entity reflecting the Assets administrated in the Asset Administration Shell this Submodel is part of. The idShort of the EntryNode can be picked freely and may reflect a name of the asset."
    entity_type: str = "SelfManagedEntity"
    global_asset_id: str = "https://admin-shell.io/idta/HierarchicalStructures/EntryNode/1/0"
    Node: Dict[str, Node_t] = {}
    SameAs: Dict[str, SameAs_t] = {}
    IsPartOf: Dict[str, IsPartOf_t] = {}
    HasPart: Dict[str, HasPart_t] = {}
    BulkCount: Optional[BulkCount_t] = None

class EntryNode(Entity):
    semantic_id: str = "https://admin-shell.io/idta/HierarchicalStructures/EntryNode/1/0"
    description: str = "Base entry point for the Entity tree in this Submodel, this must be a Self-managed Entity reflecting the Assets administrated in the AAS this Submodel is part of."
    entity_type: str = "SelfManagedEntity"
    global_asset_id: str = "https://admin-shell.io/idta/HierarchicalStructures/EntryNode/1/0"
    Node: Dict[str, Node_t] = {}
    SameAs: Dict[str, SameAs_t] = {}
    IsPartOf: Dict[str, IsPartOf_t] = {}
    HasPart: Dict[str, HasPart_t] = {}

class ArcheType(Property):
    semantic_id: str = "https://admin-shell.io/idta/HierarchicalStructures/ArcheType/1/0"
    description: str = "ArcheType of the Submodel, there are three allowed enumeration entries: 1. \u201cFull\u201d, 2. \u201cOneDown\u201d and 3. \u201cOneUp\u201d. "
    value_type: str = "xs:string"

class HierarchicalStructures(Submodel):
    semantic_id: str = "https://admin-shell.io/idta/HierarchicalStructures/1/1/Submodel"
    description: str = "The Submodel HierarchicalStructures identified by its semanticId. The Submodel idShort can be picked freely."
    VERSION: ClassVar[str] = "1"
    REVISION: ClassVar[str] = "0"
    EntryNode: EntryNode_t
    ArcheType: ArcheType_t

# ── Clash aliases: field name == element class name ──
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
EntryNode.model_rebuild()
ArcheType.model_rebuild()
HierarchicalStructures.model_rebuild()
