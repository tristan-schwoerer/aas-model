"""HTTP binding: AID's ``htv_*`` form terms (the generated ``forms_HTTP``);
actions use ``htv_methodName``, events a ``subprotocol`` (``longpoll``/``sse``)."""

from __future__ import annotations

from typing import Optional

from aas_pydantic.submodel_templates.asset_interfaces_description import (
    EndpointMetadata_t, HtvMethodName, InterfaceTemplateForHTTP as _BaseInterface, Title, forms_HTTP,
)

from aas_model.submodel_templates.aid.affordances import DmpInteractionMetadata
from aas_model.submodel_templates.aid.forms import DmpActionForm, DmpForm
from aas_model.submodel_templates.aid.interface import DmpEndpointMetadata


class HttpForm(DmpForm, forms_HTTP):
    """The form of an HTTP property or event. AID makes ``htv_methodName`` mandatory; absent, the WoT HTTP
    binding's defaults apply (GET to read, PUT to write)."""
    htv_methodName: Optional[HtvMethodName] = None


class HttpActionForm(DmpActionForm, forms_HTTP):
    """The form of an HTTP action; absent, ``htv_methodName`` is POST (WoT HTTP binding)."""
    htv_methodName: Optional[HtvMethodName] = None


class DmpHttpInterface(_BaseInterface):
    title: Title = Title()
    EndpointMetadata: EndpointMetadata_t = DmpEndpointMetadata()
    InteractionMetadata: DmpInteractionMetadata = DmpInteractionMetadata()
