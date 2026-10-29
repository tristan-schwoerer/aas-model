"""What every interface shares: its endpoint metadata."""

from __future__ import annotations

from typing import Optional

from aas_pydantic import Key, ModelReference, ReferenceElement
from aas_pydantic.submodel_templates.asset_interfaces_description import (
    Base, ContentType, EndpointMetadata, Scheme, nosec_sc, security_t,
    securityDefinitions, securityDefinitions_t,
)


class DmpEndpointMetadata(EndpointMetadata):
    """The AID EndpointMetadata with its mandatory children present: ``base``
    and ``contentType`` to be filled in, and ``security`` and
    ``securityDefinitions``, filled with ``nosec_sc`` when nothing is selected
    (:func:`select_nosec`)."""
    base: Optional[Base] = Base()
    contentType: Optional[ContentType] = ContentType()
    security: security_t = security_t()
    securityDefinitions: securityDefinitions_t = securityDefinitions()



def nosec_reference(aid_id: str, interface: str) -> ModelReference:
    """Reference to the ``nosec_sc`` of ``interface`` in the AID ``aid_id``."""
    return ModelReference(key=(
        Key(type_="Submodel", value=aid_id),
        Key(type_="SubmodelElementCollection", value=interface),
        Key(type_="SubmodelElementCollection", value="EndpointMetadata"),
        Key(type_="SubmodelElementCollection", value="securityDefinitions"),
        Key(type_="SubmodelElementCollection", value="nosec_sc"),
    ))


def select_nosec(metadata: EndpointMetadata, aid_id: str, interface: str) -> None:
    """AID 1.1 §2.24-2.25: ``security`` holds at least one reference into
    ``securityDefinitions``, and an interface without security references a
    ``nosec_sc``. Metadata that selects nothing gets that ``nosec_sc`` (AID
    demands it, so it is no default left unauthored); one that selects a scheme
    keeps its selection. The secrets of a scheme never go into the AID: the
    consumer holds them (aas-camel-dmp PLAN H4, security)."""
    if metadata.security.value:
        return
    if metadata.securityDefinitions.nosec_sc is None:
        metadata.securityDefinitions.nosec_sc = nosec_sc(scheme=Scheme(value="nosec"))
    item = getattr(type(metadata.security), "item_type", ReferenceElement)
    metadata.security.value = [item(value=nosec_reference(aid_id, interface))]
