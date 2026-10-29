"""IO-Link (over PROFINET REST) binding: AID's ``iolv_*`` terms are on the
generated form."""

from __future__ import annotations

from aas_pydantic.submodel_templates.asset_interfaces_description import (
    EndpointMetadata_t, InterfaceTemplateForIOLINK_OVER_PROFINET_REST as _BaseInterface, Title, forms_IOLINK_OVER_PROFINET_REST,
)

from aas_model.submodel_templates.aid.affordances import DmpInteractionMetadata
from aas_model.submodel_templates.aid.forms import DmpForm
from aas_model.submodel_templates.aid.interface import DmpEndpointMetadata


class IolinkForm(DmpForm, forms_IOLINK_OVER_PROFINET_REST):
    """The form of a IO-Link property."""


class IolinkInteractionMetadata(DmpInteractionMetadata):
    """IO-Link interaction metadata: properties only. The binding describes the device's process and parameter data,
    neither actions nor events."""
    actions: None = None
    events: None = None


class DmpIolinkInterface(_BaseInterface):
    title: Title = Title()
    EndpointMetadata: EndpointMetadata_t = DmpEndpointMetadata()
    InteractionMetadata: IolinkInteractionMetadata = IolinkInteractionMetadata()
