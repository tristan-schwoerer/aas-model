"""
Variables submodel — Pydantic model for asset variable definitions.

The Variables submodel contains named variable definitions. Each variable
has a semantic_id and optional InterfaceReference that maps it to an
AID property for live data via DataBridge/AIMC.

This is a custom (non-IDTA) submodel until an IDTA Variables template
is standardized. It follows the same structural pattern as generated
aas_pydantic templates.

Structure::

    Variables
    └── variables[]               (VariableItem)
        ├── variable              (Property — ontology concept URI)
        └── interface_reference   (ReferenceElement → AID property)

Single (leaf) variables hold ``variable`` + ``interface_reference`` directly
on the top-level VariableItem.  Only genuinely structured variables nest
further via ``value`` (like the Location parameter).
"""

from __future__ import annotations

from typing import ClassVar, Dict, Optional
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
    """The semantic concept URI of a single variable (leaf child)."""
    semantic_id: str = VAR_SEMANTIC_ID
    description: str = "Semantic identifier (ontology concept URI) for this variable."


class InterfaceRef(ReferenceElement):
    """Reference to the AID interface that provides live data for a variable."""
    semantic_id: str = VAR_INTERFACE_REF
    description: str = "Reference to the AID interface that provides live data for this variable."
    value: ModelReference = ModelReference(key=(Key(type_="Submodel", value=AID_SUBMODEL_REF),))


class VariableItem(SubmodelElementCollection):
    """A single variable definition.

    Single (leaf) variables hold their ``variable`` Property and
    ``interface_reference`` directly on the top-level VariableItem; structured
    variables nest further via ``value`` (like the Location parameter).
    """
    model_config = {"validate_default": True}
    semantic_id: str = VAR_ITEM
    description: str = "A named variable with semantic concept and optional live-data interface reference."

    variable: Optional[VariableProp] = None
    interface_reference: Optional[InterfaceRef] = None

    # Keys are child id_shorts → nested VariableItems (only for structured
    # variables that genuinely nest further).
    value: Dict[str, VariableItem] = {}


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

    # Keys are variable id_shorts → dynamic map of VariableItem.
    variable: Dict[str, VariableItem] = {}
