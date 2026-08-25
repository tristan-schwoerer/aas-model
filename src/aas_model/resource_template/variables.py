"""Variables partial — mandatory Resource variables (PackMLState, OccupationState).

Built on our custom Variables submodel (``aas_model.submodel_templates.variables``),
which follows the same structural pattern as generated aas_pydantic templates.
"""

from __future__ import annotations

from aas_pydantic import Key, ModelReference

from aas_model.submodel_templates.variables import (
    Variables, VariableItem, VariableProp, InterfaceRef, AID_SUBMODEL_REF,
)


def variable(semantic_id: str, interface: ModelReference | None = None) -> VariableItem:
    """Build a leaf VariableItem: ontology concept + reference to the AID
    interface, both as direct children of the top-level VariableItem."""
    if interface is None:
        interface = ModelReference(key=(Key(type_="Submodel", value=AID_SUBMODEL_REF),))
    return VariableItem(
        variable=VariableProp(value=semantic_id),
        interface_reference=InterfaceRef(value=interface),
    )


def variables() -> Variables:
    """Variables submodel with the mandatory Resource variables."""
    return Variables(
        id_short="Variables",
        variable={
            "PackMLState": variable(
                "https://w3id.org/2026/apex/semantic/state/operational",
            ),
            "OccupationState": variable(
                "https://w3id.org/2026/apex/semantic/state/occupied",
            ),
        },
    )
