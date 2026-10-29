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

from pydantic import model_validator
from aas_pydantic import (
    Submodel, SubmodelElementCollection,
    Property, ReferenceElement, ModelReference, Key
)

from aas_model.constants import AID_SUBMODEL_ID, BASE_URL

SM_PARAMETERS = f"{BASE_URL}/submodels/Parameters/1/0"

PARAM_ITEM = f"{BASE_URL}/parameters/ParameterItem/1/0"
PARAM_SEMANTIC_ID = f"{BASE_URL}/aparameters/ParameterSemanticId/1/0"
PARAM_INTERFACE_REF = f"{BASE_URL}/aparameters/InterfaceReference/1/0"


"""Generic Template Definition"""

class ParamReference(ReferenceElement):
    semantic_id: str = PARAM_INTERFACE_REF
    description: str = "Reference to the AID interface that provides a live connection to this parameter."
    value: ModelReference = ModelReference(key=(Key(type_="Submodel", value=AID_SUBMODEL_ID),
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


# ── The lab's parameters ──────────────────────────────────────────────────────

PARAM_POSITION = f"{BASE_URL}/parameters/Position/1/0"
PARAM_POSITION_COORDINATE = f"{BASE_URL}/parameters/Position/Coordinate/1/0"
PARAM_COORDINATE = f"{BASE_URL}/parameters/Coordinate/1/0"


class CoordinateProp(Property):
    """Typed Property for a single position coordinate (value_type=xs:float).

    Instantiate with the axis and value: ``CoordinateProp("x", 480.0)``.
    (The ``id_short`` is only a model-side convenience — the converter stamps
    the child's id_short from its field name, so no Literal constraint.)
    """
    semantic_id: str = PARAM_POSITION_COORDINATE
    description: str = "The value of one coordinate part of a position"
    value_type: str = "xs:float"
    value: float = 0.0

    #Convenience Constructor
    def __init__(self, axis: str = "x", value: float = 0.0, **data):
        data.setdefault("id_short", axis)
        data.setdefault("value", value)
        super().__init__(**data)


class CoordinateRef(ParamReference):
    """Reference to the AID interface for a single coordinate (x/y/yaw)."""
    description: str = "A Reference to the interface of the coordinate"

    #Convenience Constructor
    def __init__(self, axis: str = "x", **data):
        data.setdefault(
            "value",
            ModelReference(
                key=ParamReference.model_fields["value"].default.key
                + (Key(type_="SubmodelElementCollection", value=axis),)
            ),
        )
        super().__init__(**data)


class Coordinate(ParameterItem):
    """A position coordinate with an optional live AID interface reference.

    A leaf ParameterItem — ``parameter`` and ``interface_reference`` are direct
    children (no extra wrapper).  Carries its own semantic id (distinct from
    the generic ``ParameterItem``) so back-conversion resolves the concrete
    type. Static/home coordinates do not advertise a nonexistent interface.
    Instantiate with the axis and value: ``Coordinate("x", 480.0)``.
    """
    semantic_id: str = PARAM_COORDINATE
    parameter: CoordinateProp = CoordinateProp()
    interface_reference: Optional[CoordinateRef] = None

    #Convenience Constructor
    def __init__(self, axis: str = "x", val: float = 0.0, **data):
        data.setdefault("id_short", axis)
        data.setdefault("parameter", CoordinateProp(axis, val))
        super().__init__(**data)

    @model_validator(mode="before")
    @classmethod
    def _axis_from_container_key(cls, data):
        """Stamp the inner parameter's id_short from the container key.

        The container key (x/y/yaw) is stamped as ``id_short`` before
        validation, so a config like ``{"y": {"parameter": {"value":
        "0.0"}}}`` gets ``parameter.id_short="y"`` without repeating the
        axis inside each coordinate. Any explicitly authored interface
        reference is preserved in exported model JSON.
        """
        if not isinstance(data, dict):
            return data
        axis = data.get("id_short")
        if axis not in ("x", "y", "yaw"):
            return data
        out = dict(data)
        param = out.get("parameter")
        if isinstance(param, dict) and "id_short" not in param:
            out["parameter"] = {**param, "id_short": axis}
        return out


class Position(ParameterItem):
    """2D position and orientation.

    Children are DIRECT named fields with x, y, yaw defaults (no ``value``
    wrapper).
    """
    semantic_id: str = PARAM_POSITION
    id_short: str = "Location"
    description: str = "2D position with X, Y coordinates and Yaw orientation."

    x: Coordinate = Coordinate("x", 480.0)
    y: Coordinate = Coordinate("y", 120.0)
    yaw: Coordinate = Coordinate("yaw", 0.0)

class ResourceParameters(Parameters):
    """
        The parameter SM for a generic Resource
    """
    id_short: str = "Parameters"
    parameter: Dict[str, ParameterEntry] = {
        "Location": Position()
    }
