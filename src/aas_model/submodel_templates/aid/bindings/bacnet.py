"""BACnet binding: AID's ``bacv_*`` terms are on the generated form."""

from __future__ import annotations

from aas_pydantic.submodel_templates.asset_interfaces_description import (
    EndpointMetadata_t, InterfaceTemplateForBacnet as _BaseInterface, Title, forms_Bacnet,
)

from aas_model.submodel_templates.aid.affordances import DmpInteractionMetadata
from aas_model.submodel_templates.aid.forms import DmpActionForm, DmpForm
from aas_model.submodel_templates.aid.interface import DmpEndpointMetadata



class BacnetForm(DmpForm, forms_Bacnet):
    """The form of a BACnet property or event."""


class BacnetActionForm(DmpActionForm, forms_Bacnet):
    """The form of a BACnet action."""

class DmpBacnetInterface(_BaseInterface):
    title: Title = Title()
    EndpointMetadata: EndpointMetadata_t = DmpEndpointMetadata()
    InteractionMetadata: DmpInteractionMetadata = DmpInteractionMetadata()
