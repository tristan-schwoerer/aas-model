"""
Parameters submodel — Pydantic model for asset parameter definitions.

The Parameters submodel defines hierarchical key-value parameters with
semantic identifiers. Parameters are similar to Variables but represent
static or configurable values (e.g., physical location, calibration data)
rather than live telemetry.

This is a custom (non-IDTA) submodel. It follows the same structural
pattern as generated aas_pydantic templates.

Structure::

    Parameters
    └── parameters[]             (ParameterItem — hierarchical, can nest)
        ├── parameter            (Property — leaf value)
        └── interface_reference  (ReferenceElement — optional AID link)

Single (leaf) parameters hold ``parameter`` + ``interface_reference`` directly
on the top-level ParameterItem.  Only genuinely structured parameters nest
further via ``value`` (e.g. Location → Position → {x, y, yaw}).
"""

from __future__ import annotations

from typing import ClassVar, Dict, Optional
from aas_pydantic import (
    Submodel, SubmodelElementCollection,
    Property, ReferenceElement, ModelReference, Key
)

from aas_model.constants import BASE_URL

SM_PARAMETERS = f"{BASE_URL}/submodels/Parameters/1/0"

PARAM_ITEM = f"{BASE_URL}/parameters/ParameterItem/1/0"
PARAM_SEMANTIC_ID = f"{BASE_URL}/aparameters/ParameterSemanticId/1/0"
PARAM_INTERFACE_REF = f"{BASE_URL}/aparameters/InterfaceReference/1/0"

AID_SUBMODEL_REF = "{aas_id}/submodels/AssetInterfacesDescription"

"""Generic Template Definition"""

class ParamReference(ReferenceElement):
    semantic_id: str = PARAM_INTERFACE_REF
    description: str = "Reference to the AID interface that provides a live connection to this parameter."
    value: ModelReference = ModelReference(key=(Key(type_="Submodel", value=AID_SUBMODEL_REF),
                                                Key(type_="SubmodelElementCollection", value="InterfaceMQTT"),
                                                Key(type_="SubmodelElementCollection", value="InteractionMetadata"),
                                                Key(type_="SubmodelElementCollection", value="properties"),
                                                ))

class ParamProp(Property):
    semantic_id: str = PARAM_SEMANTIC_ID
    description: str = "A description of this Parameter"
    value_type: str = "xs:float"
    value: str = "0.0"


class ParameterItem(SubmodelElementCollection):
    """
    A parameter definition — can contain nested sub-parameters or leaf values.

    Single (leaf) parameters hold their ``parameter`` Property and
    ``interface_reference`` directly on the top-level ParameterItem; only
    genuinely structured parameters nest further via ``value`` (e.g. Location
    → Position → {x, y, yaw}).  ``semantic_id`` is used (SMC-level) for
    ontology alignment.
    """
    model_config = {"validate_default": True}
    semantic_id: str = PARAM_ITEM
    description: str = "A named parameter with optional semanticId and potential nested children."

    parameter: Optional[ParamProp] = None
    interface_reference: Optional[ParamReference] = None

    # Keys are child id_shorts → nested ParameterItems (only for structured
    # parameters that genuinely nest further).
    value: Dict[str, ParameterItem] = {}

class Parameters(Submodel):
    """
    Parameters submodel — hierarchical asset parameter definitions.

    Contains static/configurable parameters with semantic identifiers.
    Supports recursive nesting (e.g., Location → Position → {X, Y, Yaw}).
    """
    semantic_id: str = SM_PARAMETERS
    description: str = "Hierarchical asset parameter definitions with semantic identifiers."
    VERSION: ClassVar[str] = "1"
    REVISION: ClassVar[str] = "0"

    # Keys are parameter id_shorts → dynamic map of ParameterItem.
    parameter: Dict[str, ParameterItem] = {}
