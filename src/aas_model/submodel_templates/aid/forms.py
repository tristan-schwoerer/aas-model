"""Forms: the AID form plus the WoT terms AID leaves out — ``op``, the
action's ``response`` and ``additionalResponses`` (docs/aid-extension.md
§3.4). Each binding's form adds its protocol's terms (the generated
``forms_<Protocol>``, e.g. ``bindings.mqtt.MqttForm``)."""

from __future__ import annotations

import warnings
from typing import ClassVar, List, Optional


from aas_pydantic import Property, SubmodelElementCollection, SubmodelElementList
from aas_pydantic.aas_model import AasIdString
from aas_pydantic.submodel_templates.asset_interfaces_description import (
    ContentType, Href, forms as _BaseForm,
)

from aas_model.constants import (
    AID_WOT_ADDITIONAL_RESPONSE, AID_WOT_ADDITIONAL_RESPONSES, AID_WOT_OPERATION_TYPE,
    AID_WOT_RESPONSE_FORM, AID_WOT_RESPONSE_SCHEMA, AID_WOT_RESPONSE_SUCCESS,
)
from aas_model.submodel_templates.aid.data_schema import DmpDataSchema
from aas_model.submodel_templates.aid.elements import StringList

# The binding-term prefixes of every protocol (AID's convention).
PROTOCOL_PREFIXES = ("htv_", "modv_", "mqv_", "uav_", "bacv_", "iolv_", "canv_", "snmpv_")


class Op(StringList):
    """``op`` (hctl:hasOperationType): the WoT operations a form serves, one
    string Property per operation (``readproperty``, ``invokeaction``, …).
    Absent, the affordance's default operations apply; present, it narrows
    them."""
    id_short: AasIdString = "op"
    semantic_id: str = AID_WOT_OPERATION_TYPE
    description: str = "The WoT operation types this form serves. Absent: the default operations of the affordance."


class AdditionalResponseSuccess(Property):
    id_short: AasIdString = "success"
    semantic_id: str = AID_WOT_RESPONSE_SUCCESS
    description: str = "The response reports success. Default false."
    value_type: str = "xs:boolean"


class AdditionalResponseSchema(DmpDataSchema):
    """The data schema of an additional response, written inline (TD names
    an entry of the Thing's ``schemaDefinitions`` instead)."""
    id_short: AasIdString = "schema"
    semantic_id: str = AID_WOT_RESPONSE_SCHEMA
    description: str = "Data schema of the additional response."


with warnings.catch_warnings():
    # The TD term is ``schema``; the field (= idShort) shadows pydantic's
    # deprecated ``BaseModel.schema()`` classmethod, which nothing here uses.
    warnings.filterwarnings("ignore", message='Field name "schema"', category=UserWarning)

    class AdditionalResponse(SubmodelElementCollection):
        """One WoT AdditionalExpectedResponse: a response other than the
        affordance's regular one, e.g. an error reply or a queryaction status."""
        semantic_id: str = AID_WOT_ADDITIONAL_RESPONSE
        description: str = "A response other than the regular one: whether it reports success, its content type and its data schema."
        success: Optional[AdditionalResponseSuccess] = None
        contentType: Optional[ContentType] = None
        schema: Optional[AdditionalResponseSchema] = None


class AdditionalResponses(SubmodelElementList):
    """``additionalResponses`` (hctl:additionalReturns) of a form."""
    id_short: AasIdString = "additionalResponses"
    semantic_id: str = AID_WOT_ADDITIONAL_RESPONSES
    description: str = "Responses of this form other than the regular one, e.g. error replies."
    type_value_list_element: str = "SubmodelElementCollection"
    semantic_id_list_element: str = AID_WOT_ADDITIONAL_RESPONSE
    item_type: ClassVar = AdditionalResponse
    value: List[AdditionalResponse] = []


class DmpForm(_BaseForm):
    """The AID form every protocol shares plus the optional WoT ``op`` and ``additionalResponses``; a binding's
    form adds its protocol's terms."""
    href: Href = Href()
    op: Optional[Op] = None
    additionalResponses: Optional[AdditionalResponses] = None


class DmpResponseForm(SubmodelElementCollection):
    """WoT ExpectedResponse (hctl:returns): the content type of an action's
    result when it differs from the form's. The result arrives over the same
    protocol and form."""
    id_short: AasIdString = "response"
    semantic_id: str = AID_WOT_RESPONSE_FORM
    description: str = "Expected response of the action: its content type. Absent: the form's content type."
    contentType: Optional[ContentType] = None


class DmpActionForm(DmpForm):
    """The form of an action: a form plus the optional WoT ``response``."""
    response: Optional[DmpResponseForm] = None


for _model in (AdditionalResponseSchema, AdditionalResponse, AdditionalResponses, DmpForm, DmpActionForm):
    _model.model_rebuild()
