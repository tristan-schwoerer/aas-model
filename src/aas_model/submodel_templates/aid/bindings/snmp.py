"""SNMP binding (AID 1.2 Annex E.1): v1/v2c, base ``snmp://{address}:{port}``,
forms addressing one OID each. Annex E.1 defines the form terms below; the
generated template carries none."""

from __future__ import annotations

from typing import Dict, Optional

from aas_pydantic import Property
from aas_pydantic.aas_model import AasIdString
from aas_pydantic.submodel_templates.asset_interfaces_description import (
    EndpointMetadata_t, InterfaceTemplateForSNMP as _BaseSnmpInterface, Title, forms_SNMP,
)

from aas_model.submodel_templates.aid.affordances import DmpInteractionMetadata, DmpProperties, DmpProperty
from aas_model.submodel_templates.aid.forms import DmpForm
from aas_model.submodel_templates.aid.interface import DmpEndpointMetadata


class SnmpvPduType(Property):
    """The PDU type of the interaction, ``snmpv:GetRequestPDU`` (read, the
    default of readproperty) or ``snmpv:SetRequestPDU`` (write, the default
    of writeproperty)."""
    id_short: AasIdString = "snmpv_pduType"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/2/SNMP/pduType"
    description: str = "SNMP PDU type of the interaction: snmpv:GetRequestPDU or snmpv:SetRequestPDU."


class SnmpvVersion(Property):
    """``snmpv:SNMPv1`` or ``snmpv:SNMPv2c`` (the default)."""
    id_short: AasIdString = "snmpv_version"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/2/SNMP/version"
    description: str = "SNMP protocol version of the interaction: snmpv:SNMPv1 or snmpv:SNMPv2c (default)."


class SnmpForm(DmpForm, forms_SNMP):
    """The form of an SNMP property: one OID (``href``) and its PDU type and
    protocol version."""
    snmpv_pduType: Optional[SnmpvPduType] = None
    snmpv_version: Optional[SnmpvVersion] = None


class SnmpProperty(DmpProperty):
    forms: SnmpForm = SnmpForm()


class SnmpProperties(DmpProperties):
    """Dynamic map of SNMP properties (name → SnmpProperty)."""
    property_name: Dict[str, SnmpProperty] = {}


class SnmpInteractionMetadata(DmpInteractionMetadata):
    properties: Optional[SnmpProperties] = None


class DmpSnmpInterface(_BaseSnmpInterface):
    title: Title = Title()
    EndpointMetadata: EndpointMetadata_t = DmpEndpointMetadata()
    InteractionMetadata: SnmpInteractionMetadata = SnmpInteractionMetadata()
