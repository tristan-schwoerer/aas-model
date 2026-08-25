"""aas_model package — shared AAS submodel models (ADR-016).

Re-exports the (moved) registration-service submodel templates so consumers
use ``from aas_model.submodel_templates import Aimc, ...``, and exposes the
shared AAS-JSON<->model bridge from :mod:`aas_model._serde`.
"""

from aas_model import _serde  # noqa: F401  (public parse API)
from aas_model.submodel_templates import *  # noqa: F401,F403
from aas_model.constants import *  # noqa: F401,F403
