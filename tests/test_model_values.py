"""How authored values become elements, and how elements survive their pydantic JSON and the AAS."""

from __future__ import annotations

from basyx.aas import model
from basyx.aas.adapter.json import json_serialization
import json

from aas_pydantic import Property, Submodel
from aas_pydantic.convert_pydantic_model import convert_model_to_submodel
from aas_pydantic.convert_util import strip_temp_id_short_attributes
from aas_pydantic.submodel_templates.nameplate import ManufacturerName
from aas_model.submodel_templates.aid import DmpAssetInterfacesDescription, DmpProperty, MqttForm
from aas_model.testing import build_aid, mqtt_interface
from aas_json import parse_submodel_dict


def test_a_number_or_bool_is_written_as_the_property_value():
    assert Property(value=5, value_type="xs:int").value == "5"
    assert Property(value=2.5, value_type="xs:double").value == "2.5"
    assert Property(value=True, value_type="xs:boolean").value == "true"


def test_a_language_map_is_a_multi_language_property_value():
    class Maker(Submodel):
        ManufacturerName: ManufacturerName

    maker = Maker(id_short="Maker", ManufacturerName={"en": "Acme", "de": "Acme GmbH"})
    assert isinstance(maker.ManufacturerName, ManufacturerName)
    assert maker.ManufacturerName.value == {"en": "Acme", "de": "Acme GmbH"}


def _aid_with_mqtt_property():
    interface = mqtt_interface("mqtt://broker:1883/")
    interface.InteractionMetadata.properties.property_name["State"] = DmpProperty(
        forms=MqttForm(href="DATA/State", mqv_qos="1", mqv_retain="true"))
    return build_aid(mqtt=interface)


def test_a_subclass_in_a_named_field_survives_the_json_round_trip():
    aid = _aid_with_mqtt_property()
    restored = DmpAssetInterfacesDescription.model_validate_json(aid.model_dump_json())
    form = restored.InterfaceTemplateForMQTT["interface_mqtt"].InteractionMetadata.properties.property_name[
        "State"].forms
    assert type(form) is MqttForm
    assert form.mqv_qos.value == "1"


def test_the_aas_is_read_back_as_the_classes_its_markers_name():
    aid = _aid_with_mqtt_property()
    aid.id = "urn:aid"
    store = model.DictIdentifiableStore([convert_model_to_submodel(aid)])
    strip_temp_id_short_attributes(store)
    document = json.loads(json_serialization.object_store_to_json(store))["submodels"][0]
    restored = parse_submodel_dict(document, DmpAssetInterfacesDescription)
    form = restored.InterfaceTemplateForMQTT["interface_mqtt"].InteractionMetadata.properties.property_name[
        "State"].forms
    assert type(form) is MqttForm
    assert form.mqv_retain.value == "true"
