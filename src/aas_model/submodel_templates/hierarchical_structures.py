"""The resource's HierarchicalStructures: the IDTA template (02011) with its relationships following from the
archetype.

A OneUp hierarchy relates its entry node to the nodes above it (``IsPartOf``), a OneDown hierarchy to the nodes
below it (``HasPart``). Authoring the entry node and its nodes is enough: the relationships are added unless
authored, named ``PartOf_<node>`` and ``HasPart_<node>``. They relate the entities of this submodel (ModelReferences
to the entry node and the node), as the template means them; each node is also ``SameAs`` the entry node of the
related resource's HierarchicalStructures, a reference to the other AAS one can follow.

The related resource's submodel is found by the lab's convention: an asset's id is its AAS's id
(``{globalAssetId}/submodels/HierarchicalStructures``).
"""

from __future__ import annotations

import typing

from pydantic import model_validator

from aas_pydantic import Key, ModelReference
from aas_pydantic.submodel_templates.hierarchical_structures import EntryNode, HierarchicalStructures, SameAs

from aas_model.constants import HIERARCHICAL_STRUCTURES_SUBMODEL_ID

# The relationship classes the entry node declares (the generated template has two classes named IsPartOf).
IsPartOf = typing.get_args(EntryNode.model_fields["IsPartOf"].annotation)[1]
HasPart = typing.get_args(EntryNode.model_fields["HasPart"].annotation)[1]


def _entity(submodel_id: str, *path: str) -> ModelReference:
    """A ModelReference to the entity at ``path`` (entry node first) in the HierarchicalStructures ``submodel_id``."""
    return ModelReference(key=(Key(type_="Submodel", value=submodel_id),
                               *(Key(type_="Entity", value=name) for name in path)))


class ResourceHierarchicalStructures(HierarchicalStructures):
    @model_validator(mode="after")
    def _relationships_follow_from_the_archetype(self):
        entry = self.EntryNode
        if entry.IsPartOf or entry.HasPart or entry.SameAs:
            return self
        here = HIERARCHICAL_STRUCTURES_SUBMODEL_ID
        relation = {"OneUp": ("PartOf", IsPartOf, "IsPartOf"), "OneDown": ("HasPart", HasPart, "HasPart")}.get(
            self.ArcheType.value)
        for name, node in entry.Node.items():
            if relation is not None:
                prefix, cls, field = relation
                getattr(entry, field)[f"{prefix}_{name}"] = cls(
                    first=_entity(here, "EntryNode"), second=_entity(here, "EntryNode", name))
            if not node.SameAs:
                there = HIERARCHICAL_STRUCTURES_SUBMODEL_ID.replace("{aas_id}", node.global_asset_id)
                node.SameAs = {"SameAs": SameAs(first=_entity(here, "EntryNode", name),
                                                second=_entity(there, "EntryNode"))}
        return self
