"""
Variables submodel — Pydantic model for an asset's runtime data.

This is a custom (non-IDTA) submodel until an IDTA Variables template
is standardized. It follows the same structural pattern as generated
aas_pydantic templates.

Structure::

    Variables
    ├── State            (discrete status that changes on events)
    ├── Measurements     (values sampled from the asset)
    └── Log              (what the mappings log explicitly)

A group holds TimeSeries SMCs (``TimeSeriesCollection``): the AIMC mappings
write their rows into a series' LinkedSegment, so the AAS describes the
history rather than holding the current value. Data that is not a time
series (the latest camera image) is a plain ``VariableProp`` in its group,
or a ``VariableItem`` when several values belong together.
"""

from __future__ import annotations

from typing import ClassVar, Dict, Optional, Union
from aas_pydantic import Property, Submodel, SubmodelElementCollection
from aas_pydantic.aas_model import AasIdString

from aas_model.constants import BASE_URL
from aas_model.submodel_templates.time_series import TimeSeriesCollection

SM_VARIABLES = f"{BASE_URL}/submodels/Variables/1/0"

VAR_ITEM = f"{BASE_URL}/variables/VariableItem/1/0"
VAR_SEMANTIC_ID = f"{BASE_URL}/variables/VariableSemanticId/1/0"
VAR_STATE = f"{BASE_URL}/variables/State/1/0"
VAR_MEASUREMENTS = f"{BASE_URL}/variables/Measurements/1/0"
VAR_LOG = f"{BASE_URL}/variables/Log/1/0"



class VariableProp(Property):
    """A value that is not a time series, kept current by the AIMC mapping sinking into it.

    The ontology concept it is grounded in rides as a supplemental semantic id.
    """
    semantic_id: str = VAR_SEMANTIC_ID
    description: str = "Live value of this variable; its ontology concept rides as a supplemental semantic id."


class VariableItem(SubmodelElementCollection):
    """Values that belong together. A single value needs no wrapper: it is a plain ``VariableProp``."""
    model_config = {"validate_default": True}
    semantic_id: str = VAR_ITEM
    description: str = "A group of variables that belong together."

    value: Dict[str, Union[VariableProp, "VariableItem"]] = {}


# A group entry is a time series, or a plain element for data that is not one.
GroupEntry = Union[TimeSeriesCollection, VariableProp, VariableItem]


class StateGroup(SubmodelElementCollection):
    """Discrete status that changes on events (PackML state, occupation)."""
    id_short: AasIdString = "State"
    semantic_id: str = VAR_STATE
    value: Dict[str, GroupEntry] = {}


class MeasurementsGroup(SubmodelElementCollection):
    """Values sampled from the asset (weight, position, inspection results)."""
    id_short: AasIdString = "Measurements"
    semantic_id: str = VAR_MEASUREMENTS
    value: Dict[str, GroupEntry] = {}


class LogGroup(SubmodelElementCollection):
    """What the mappings log explicitly, such as Operation invocations."""
    id_short: AasIdString = "Log"
    semantic_id: str = VAR_LOG
    value: Dict[str, GroupEntry] = {}


class Variables(Submodel):
    """Variables submodel — an asset's runtime data, as time series of its state, measurements and logs."""
    semantic_id: str = SM_VARIABLES
    description: str = "An asset's runtime data: time series of its state, measurements and logs."
    VERSION: ClassVar[str] = "1"
    REVISION: ClassVar[str] = "0"

    # Present only when authored, like every other container.
    State: Optional[StateGroup] = None
    Measurements: Optional[MeasurementsGroup] = None
    Log: Optional[LogGroup] = None
