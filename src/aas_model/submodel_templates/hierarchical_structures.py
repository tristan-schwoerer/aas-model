"""The resource's HierarchicalStructures: the IDTA template (02011) with its relationships following from the
archetype.

A OneUp hierarchy relates its entry node to the nodes above it (``IsPartOf``), a OneDown hierarchy to the nodes
below it (``HasPart``). Authoring the entry node and its nodes is enough: the relationships are added unless
authored, named ``PartOf_<node>`` and ``HasPart_<node>``.
"""

from __future__ import annotations

import typing

from pydantic import model_validator

from aas_pydantic import ExternalReference, Key
from aas_pydantic.submodel_templates.hierarchical_structures import EntryNode, HierarchicalStructures

# The relationship classes the entry node declares (the generated template has two classes named IsPartOf).
IsPartOf = typing.get_args(EntryNode.model_fields["IsPartOf"].annotation)[1]
HasPart = typing.get_args(EntryNode.model_fields["HasPart"].annotation)[1]


def _asset(global_asset_id: str) -> ExternalReference:
    return ExternalReference(key=(Key(type_="GlobalReference", value=global_asset_id),))


class ResourceHierarchicalStructures(HierarchicalStructures):
    @model_validator(mode="after")
    def _relationships_follow_from_the_archetype(self):
        entry = self.EntryNode
        if entry.IsPartOf or entry.HasPart or entry.SameAs:
            return self
        archetype = self.ArcheType.value
        if archetype == "OneUp":
            entry.IsPartOf = {f"PartOf_{name}": IsPartOf(first=_asset(entry.global_asset_id),
                                                         second=_asset(node.global_asset_id))
                              for name, node in entry.Node.items()}
        elif archetype == "OneDown":
            entry.HasPart = {f"HasPart_{name}": HasPart(first=_asset(entry.global_asset_id),
                                                        second=_asset(node.global_asset_id))
                             for name, node in entry.Node.items()}
        return self
