"""CAN binding (AID 1.2 Annex E.2): forms address a frame by its 29-bit
identifier (``can://0x1f2b3a00``) and a datapoint by the generated ``canv_*``
terms; ``base`` is unused for CAN.

The DMP does not consume CAN (it is not IP-based; a gateway at the bus does),
but an asset's AID describes all its interfaces, and a CAN AID is what
configures such a gateway."""

from __future__ import annotations

from aas_pydantic.submodel_templates.asset_interfaces_description import (
    EndpointMetadata_t, InterfaceTemplateForCAN as _BaseInterface, Title, forms_CAN,
)

from aas_model.submodel_templates.aid.affordances import DmpInteractionMetadata
from aas_model.submodel_templates.aid.forms import DmpActionForm, DmpForm
from aas_model.submodel_templates.aid.interface import DmpEndpointMetadata



class CanForm(DmpForm, forms_CAN):
    """The form of a CAN property or event."""


class CanActionForm(DmpActionForm, forms_CAN):
    """The form of a CAN action."""

class DmpCanInterface(_BaseInterface):
    title: Title = Title()
    EndpointMetadata: EndpointMetadata_t = DmpEndpointMetadata()
    InteractionMetadata: DmpInteractionMetadata = DmpInteractionMetadata()
