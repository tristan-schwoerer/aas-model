"""Modbus binding: AID's ``modv_*`` terms, on the form (the generated
``forms_MODBUS``) and the endpoint metadata (byte and word order)."""

from __future__ import annotations

from aas_pydantic.submodel_templates.asset_interfaces_description import (
    EndpointMetadata_MODBUS, InterfaceTemplateForMODBUS as _BaseInterface, Title, forms_MODBUS,
)

from aas_model.submodel_templates.aid.affordances import DmpInteractionMetadata
from aas_model.submodel_templates.aid.forms import DmpForm
from aas_model.submodel_templates.aid.interface import DmpEndpointMetadata


class ModbusForm(DmpForm, forms_MODBUS):
    """The form of a Modbus property: ``href`` addresses the register or coil."""


class DmpModbusEndpointMetadata(DmpEndpointMetadata, EndpointMetadata_MODBUS):
    """Modbus endpoint metadata, with the byte and word order of multi-register values."""


class ModbusInteractionMetadata(DmpInteractionMetadata):
    """Modbus interaction metadata: properties only. Modbus reads and writes registers and coils; it has no actions (an
    Operation writes a property's tag) and no events (an observation is polled)."""
    actions: None = None
    events: None = None


class DmpModbusInterface(_BaseInterface):
    title: Title = Title()
    EndpointMetadata: DmpModbusEndpointMetadata = DmpModbusEndpointMetadata()
    InteractionMetadata: ModbusInteractionMetadata = ModbusInteractionMetadata()
