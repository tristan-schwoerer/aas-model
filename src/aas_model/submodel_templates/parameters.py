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
    └── parameter[]            (ParamProp — a plain Property, OR
                                ParameterItem — a group of them)

A parameter is a **plain Property** by default: a leaf parameter is addressed
directly as ``Parameters/<name>``. Nest it in a ``ParameterItem`` only when
the parameter genuinely groups several children (e.g. ``Location`` with its
x/y/yaw coordinates), in which case the group is an SMC addressed as
``Parameters/<name>``.

Both forms live in the same ``parameter`` map, so a submodel can mix them::

    Parameters
    ├── Parameter              (Property)
    └── Location               (SMC)
        └── x                  (SMC)
            └── parameter      (Property)
"""

from __future__ import annotations

from typing import ClassVar, Dict, Optional, Union
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
    A parameter GROUP — use when several children belong together (e.g. a
    position with x/y/yaw).

    A single (leaf) parameter needs no wrapper: declare it as a plain
    ``ParamProp`` in the ``Parameters.parameter`` map and address it as
    ``Parameters/<name>``. ``semantic_id`` is used (SMC-level) for ontology
    alignment on the group.
    """
    model_config = {"validate_default": True}
    semantic_id: str = PARAM_ITEM
    description: str = "A group of parameter values that belong together."

    parameter: Optional[ParamProp] = None
    interface_reference: Optional[ParamReference] = None

    # Keys are child id_shorts → a plain ParamProp child, or a nested
    # ParameterItem when the child itself groups further children.
    value: Dict[str, "ParameterEntry"] = {}

# A parameter entry is EITHER a plain Property (the normal case) OR a
# ParameterItem group. Both forms are accepted in the same map, so a submodel
# can mix flat parameters with logically grouped ones.
ParameterEntry = Union[ParamProp, ParameterItem]

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

    # Keys are parameter id_shorts → a plain ParamProp, or a ParameterItem
    # when the parameter groups several children.
    parameter: Dict[str, ParameterEntry] = {}
