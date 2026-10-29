"""AID 1.2 SNMP and CAN interfaces authored with the DMP extension classes."""

import json

from basyx.aas import model
from basyx.aas.adapter.json import json_serialization

from aas_model.submodel_templates.aid import (
    CanForm, DmpAssetInterfacesDescription, DmpCanInterface, DmpProperties, DmpProperty, ReadOnly,
)
from aas_model.testing import build_aid, snmp_interface
from aas_pydantic.convert_pydantic_model import convert_model_to_submodel
from aas_pydantic.submodel_templates.asset_interfaces_description import (
    CanvLength, CanvOffset, CanvValueOffset, Href, Title,
)


def _serialized(aid: DmpAssetInterfacesDescription) -> dict:
    aid.id = "urn:test:aid"
    store = model.DictIdentifiableStore([convert_model_to_submodel(model_submodel=aid)])
    return json.loads(json_serialization.object_store_to_json(store))["submodels"][0]


def _child(element: dict, id_short: str) -> dict:
    for child in element.get("submodelElements", element.get("value", [])):
        if child.get("idShort") == id_short:
            return child
    raise AssertionError(f"{id_short} missing")


def _semantic(element: dict) -> str:
    return element["semanticId"]["keys"][0]["value"]


def test_snmp_forms_carry_the_binding_terms_of_annex_e1():
    aid = build_aid(snmp=snmp_interface("snmp://10.0.0.5:161/", properties={
        "Contact": ("1.3.6.1.2.1.1.4.0", {"pduType": "snmpv:SetRequestPDU", "version": "snmpv:SNMPv1"})}))
    interface = _child(_serialized(aid), "interface_snmp")
    assert interface["supplementalSemanticIds"][0]["keys"][0]["value"] == \
        "https://admin-shell.io/idta/AssetInterfacesDescription/1/2/SNMP"
    form = _child(_child(_child(_child(interface, "InteractionMetadata"), "properties"), "Contact"), "forms")
    assert _child(form, "href")["value"] == "1.3.6.1.2.1.1.4.0"
    assert _semantic(_child(form, "snmpv_pduType")) == "https://admin-shell.io/idta/AssetInterfacesDescription/1/2/SNMP/pduType"
    assert _child(form, "snmpv_version")["value"] == "snmpv:SNMPv1"


def test_can_properties_use_the_extended_interaction_metadata():
    form = CanForm(href=Href(value="can://0x1f2b3a00"), canv_offset=CanvOffset(value="0"),
                   canv_length=CanvLength(value="16"), canv_valueOffset=CanvValueOffset(value="-50"))
    temperature = DmpProperty(title=Title(value="Temperature"), readOnly=ReadOnly(value="true"), forms=form)
    can = DmpCanInterface(title=Title(value="can"))
    can.InteractionMetadata.properties = DmpProperties(property_name={"Temperature": temperature})
    aid = DmpAssetInterfacesDescription(id_short="AID")
    aid.InterfaceTemplateForCAN["interface_can"] = can
    interface = _child(_serialized(aid), "interface_can")
    assert interface["supplementalSemanticIds"][0]["keys"][0]["value"] == \
        "https://admin-shell.io/idta/AssetInterfacesDescription/1/2/CAN"
    property_ = _child(_child(_child(interface, "InteractionMetadata"), "properties"), "Temperature")
    assert _child(property_, "readOnly")["value"] == "true"
    form = _child(property_, "forms")
    assert [_child(form, term)["value"] for term in ("canv_offset", "canv_length")] == ["0", "16"]
