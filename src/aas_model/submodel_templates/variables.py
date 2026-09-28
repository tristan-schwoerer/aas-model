"""
Variables submodel — Pydantic model for asset variable definitions.

The Variables submodel contains named variable definitions. Each variable
carries its ontology concept as a supplemental semantic id on the
``variable`` Property, whose VALUE is the live data the AIMC mappings sink
into.

This is a custom (non-IDTA) submodel until an IDTA Variables template
is standardized. It follows the same structural pattern as generated
aas_pydantic templates.

Structure::

    Variables
    └── variable[]                (VariableProp — a plain Property, OR
                                   VariableItem — a group of them)

A variable is a **plain Property** by default: the value itself is the live
data the AIMC mappings sink into, addressed directly as
``Variables/<name>``. Nest it in a ``VariableItem`` only when the variable
genuinely groups several children (e.g. a structured reading), in which case
the group is an SMC addressed as ``Variables/<name>``.

Both forms live in the same ``variable`` map, so a submodel can mix them::

    Variables
    ├── PackMLState              (Property)
    └── Grouped                  (SMC)
        └── variable             (Property)
"""

from __future__ import annotations

from typing import ClassVar, Dict, Optional, Union
from aas_pydantic import (
    Submodel, SubmodelElementCollection,
    Property, ModelReference, Key, ReferenceElement,
)

from aas_model.constants import BASE_URL

SM_VARIABLES = f"{BASE_URL}/submodels/Variables/1/0"

VAR_INTERFACE_REF = f"{BASE_URL}/variables/InterfaceReference/1/0"
VAR_ITEM = f"{BASE_URL}/variables/VariableItem/1/0"
VAR_SEMANTIC_ID = f"{BASE_URL}/variables/VariableSemanticId/1/0"

AID_SUBMODEL_REF = "{aas_id}/submodels/AssetInterfacesDescription"


class VariableProp(Property):
    """The live value of a single variable (leaf child).

    The ontology concept this variable is grounded in rides as a
    supplemental semantic id; the value itself is the live data the AIMC
    mappings sink into (initially empty).
    """
    semantic_id: str = VAR_SEMANTIC_ID
    description: str = "Live value of this variable; its ontology concept rides as a supplemental semantic id."


class InterfaceRef(ReferenceElement):
    """Reference to the AID interface that provides live data for a variable."""
    semantic_id: str = VAR_INTERFACE_REF
    description: str = "Reference to the AID interface that provides live data for this variable."
    value: ModelReference = ModelReference(key=(Key(type_="Submodel", value=AID_SUBMODEL_REF),))


class VariableItem(SubmodelElementCollection):
    """A group of variables — use ONLY when several children belong together.

    A single variable needs no wrapper: declare it as a plain ``VariableProp``
    in the ``Variables.variable`` map and address it as ``Variables/<name>``.
    Wrapping every variable in a one-child SMC hides the value one level deeper
    than the AIMC sink reference points at.
    """
    model_config = {"validate_default": True}
    semantic_id: str = VAR_ITEM
    description: str = "A group of variables that belong together."

    interface_reference: Optional[InterfaceRef] = None

    # Keys are child id_shorts → a plain VariableProp child, or a nested
    # VariableItem when the child itself groups further children. There is no
    # single dedicated value child: a group with one value is just that value.
    value: Dict[str, "VariableEntry"] = {}


# A variable entry is EITHER a plain Property (the normal case) OR a
# VariableItem group. Both forms are accepted in the same map, so a submodel
# can mix flat variables with logically grouped ones.
VariableEntry = Union[VariableProp, VariableItem]


class Variables(Submodel):
    """
    Variables submodel — asset variable definitions.

    Contains named variables with semantic identifiers and optional
    references to AID properties for live-data mapping via AIMC/DataBridge.
    """
    semantic_id: str = SM_VARIABLES
    description: str = "Asset variable definitions with semantic concepts and live-data interface references."
    VERSION: ClassVar[str] = "1"
    REVISION: ClassVar[str] = "0"

    # Keys are variable id_shorts → a plain VariableProp, or a VariableItem
    # when the variable groups several children.
    variable: Dict[str, VariableEntry] = {}
