"""Variables partial — mandatory Resource variables (PackMLState, OccupationState).

Built on our custom Variables submodel (``aas_model.submodel_templates.variables``),
which follows the same structural pattern as generated aas_pydantic templates.
"""

from __future__ import annotations

from aas_model.submodel_templates.variables import (
    Variables, VariableProp,
)


def variable(semantic_id: str) -> VariableProp:
    """Build a leaf variable as a plain Property.

    The ontology concept URI rides as a supplemental semantic id; the
    Property's VALUE is the live value the AIMC mappings sink into. A leaf
    variable is a direct child of the submodel, so an AIMC sink addresses it
    as ``Variables/<name>`` with no extra wrapper level. It deliberately
    carries NO ``interface_reference`` — with AIMC-driven mappings the
    live-data linkage lives in the AIMC submodel, so a static AID reference
    would point nowhere.

    Use ``VariableItem`` instead when a variable genuinely groups several
    children.
    """
    return VariableProp(
        value="",
        supplemental_semantic_ids=[semantic_id],
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
