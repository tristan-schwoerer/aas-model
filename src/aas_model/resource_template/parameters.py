from typing import Literal, Dict
from pydantic import model_validator
from aas_pydantic import Property, ModelReference, Key
from aas_model.submodel_templates.parameters import (
    Parameters, ParameterItem, ParamReference,
)
from ..constants import BASE_URL


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
    """A single position coordinate: typed property + AID interface reference.

    A leaf ParameterItem — ``parameter`` and ``interface_reference`` are direct
    children (no extra wrapper).  Carries its own semantic id (distinct from
    the generic ``ParameterItem``) so back-conversion resolves the concrete
    type.  Instantiate with the axis and value: ``Coordinate("x", 480.0)``.
    """
    semantic_id: str = PARAM_COORDINATE
    parameter: CoordinateProp = CoordinateProp()
    interface_reference: CoordinateRef = CoordinateRef()

    #Convenience Constructor
    def __init__(self, axis: str = "x", val: float = 0.0, **data):
        data.setdefault("id_short", axis)
        data.setdefault("parameter", CoordinateProp(axis, val))
        data.setdefault("interface_reference", CoordinateRef(axis))
        super().__init__(**data)

    @model_validator(mode="before")
    @classmethod
    def _axis_from_container_key(cls, data):
        """Stamp the inner parameter's id_short from the container key.

        The container key (x/y/yaw) is stamped as ``id_short`` before
        validation, so a config like ``{"y": {"parameter": {"value":
        "0.0"}}}`` gets ``parameter.id_short="y"`` without repeating the
        axis inside each coordinate.  (The ``interface_reference`` is not
        injected here — the base-defaults merge always supplies it, and a
        before-validator-added instance is unreliable in the validator
        chain.)
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
    parameter: Dict[str, ParameterItem] = {
        "Location": Position()
    }


def resource_parameters() -> ResourceParameters:
    """Fresh Resource Parameters submodel with the mandatory Location parameter.

    ``id_short`` is passed explicitly — the Identifiable before-validator
    requires it on the raw input (class-level defaults run too late).
    """
    return ResourceParameters(id_short="Parameters")
