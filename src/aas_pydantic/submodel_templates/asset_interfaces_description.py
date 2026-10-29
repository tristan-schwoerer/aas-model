"""AssetInterfacesDescription - generated from IDTA template.
Source: Asset Interfaces Description/1/2/IDTA 02017_Template_Asset Interfaces Description.json
"""

from __future__ import annotations

from typing import ClassVar, Dict, List, Optional, TypeAlias, Union
from aas_pydantic import (
    DynamicSubmodelElementCollection, File, Property, Range, ReferenceElement, Submodel, SubmodelElementCollection, SubmodelElementList,
)
from pydantic import Field as _Field
from aas_pydantic.aas_model import AasIdString

class Title(Property):
    id_short: AasIdString = "title"
    semantic_id: str = "https://www.w3.org/2019/wot/td#title"
    description: str = "Provides a human-readable title to give a human-readable context of the interface."
    value_type: str = "xs:string"

class Created(Property):
    id_short: AasIdString = "created"
    semantic_id: str = "http://purl.org/dc/terms/created"
    description: str = "Provides information when the AID Submodel was created."
    value_type: str = "xs:string"

class Modified(Property):
    id_short: AasIdString = "modified"
    semantic_id: str = "http://purl.org/dc/terms/modified"
    description: str = "Provides information when the AID Submodel was modified."
    value_type: str = "xs:string"

class Support(Property):
    id_short: AasIdString = "support"
    semantic_id: str = "https://www.w3.org/2019/wot/td#supportContact"
    description: str = "Provides an address on how to contact the maintainer of AID Submodel as URI scheme."
    value_type: str = "xs:string"

class Base(Property):
    id_short: AasIdString = "base"
    semantic_id: str = "https://www.w3.org/2019/wot/td#baseURI"
    description: str = "Defines asset connection entry point. Each protocol specifies a base pattern. Please see Annex B.1 of the AID document for more details."
    value_type: str = "xs:string"

class ContentType(Property):
    id_short: AasIdString = "contentType"
    semantic_id: str = "https://www.w3.org/2019/wot/hypermedia#forContentType"
    description: str = "Defines content type based on a media type (e.g., text/plain) and potential character decoding/encoding type (e.g., charset=utf-8) for the media type (see RFC2046) of the whole interface"
    value_type: str = "xs:string"

class securityItem(ReferenceElement):
    semantic_id: str = "https://www.w3.org/2019/wot/td#definesSecurityScheme"
    description: str = "Defines the security scheme according to W3C:"

class security(SubmodelElementList):
    id_short: AasIdString = "security"
    semantic_id: str = "https://www.w3.org/2019/wot/td#hasSecurityConfiguration"
    description: str = "Selects one or more of the security scheme(s) that can be applied at runtime from the collection of security schemes defines in securityDefinitions. "
    type_value_list_element: str = "ReferenceElement"
    semantic_id_list_element: str = "https://www.w3.org/2019/wot/td#definesSecurityScheme"
    order_relevant: bool = True
    item_type: ClassVar = securityItem
    value: List[securityItem] = []

class Scheme(Property):
    id_short: AasIdString = "scheme"
    semantic_id: str = "https://www.w3.org/2019/wot/security#SecurityScheme"
    description: str = "Defines the security mechanism that used during access. Supported modes one of nosec, basic, digest, bearer, psk, oauth2, apikey, combo, auto, uav_channelsec and uav_authentication_"
    value_type: str = "xs:string"

class nosec_sc(SubmodelElementCollection):
    id_short: AasIdString = "nosec_sc"
    semantic_id: str = "https://www.w3.org/2019/wot/security#NoSecurityScheme"
    description: str = "No security scheme definition"
    scheme: Scheme

class Proxy(Property):
    id_short: AasIdString = "proxy"
    semantic_id: str = "https://www.w3.org/2019/wot/security#proxy"
    description: str = "Provides address information of the proxy server the security configuration provides access to. "
    value_type: str = "xs:anyURI"

class auto_sc(SubmodelElementCollection):
    id_short: AasIdString = "auto_sc"
    semantic_id: str = "https://www.w3.org/2019/wot/security#AutoSecurityScheme"
    description: str = "Auto security scheme definition"
    scheme: Scheme
    proxy: Optional[Proxy] = None

class Name(Property):
    id_short: AasIdString = "name"
    semantic_id: str = "https://www.w3.org/2019/wot/security#name"
    description: str = "Name for query, header, cookie, or uri parameters"
    value_type: str = "xs:string"

class In(Property):
    id_short: AasIdString = "in"
    semantic_id: str = "https://www.w3.org/2019/wot/security#in"
    description: str = "Specifies the location of security authentication information. Proposed values are header, query, body, cookie or auto"
    value_type: str = "xs:string"

class basic_sc(SubmodelElementCollection):
    id_short: AasIdString = "basic_sc"
    semantic_id: str = "https://www.w3.org/2019/wot/security#BasicSecurityScheme"
    description: str = "Basic security scheme definition"
    scheme: Scheme
    name: Optional[Name] = None
    in_: Optional[In] = _Field(default=None, json_schema_extra={"aas_id_short": "in"})
    proxy: Optional[Proxy] = None

class oneOf(SubmodelElementList):
    id_short: AasIdString = "oneOf"
    semantic_id: str = "https://www.w3.org/2019/wot/security#oneOf"
    description: str = "Array of two or more strings identifying other named security scheme definitions, any one of which, when satisfied, will allow access. Only one may be chosen for use."
    type_value_list_element: str = "ReferenceElement"
    semantic_id_list_element: str = "https://www.w3.org/2019/wot/security#allOf"
    order_relevant: bool = True
    item_type: ClassVar = ReferenceElement
    value: List[ReferenceElement] = []

class allOf(SubmodelElementList):
    id_short: AasIdString = "allOf"
    semantic_id: str = "https://www.w3.org/2019/wot/security#allOf"
    description: str = "Array of two or more strings identifying other named security scheme definitions, all of which must be satisfied for access."
    type_value_list_element: str = "ReferenceElement"
    semantic_id_list_element: str = "https://www.w3.org/2019/wot/security#allOf"
    order_relevant: bool = True
    item_type: ClassVar = ReferenceElement
    value: List[ReferenceElement] = []

class combo_sc(SubmodelElementCollection):
    id_short: AasIdString = "combo_sc"
    semantic_id: str = "https://www.w3.org/2019/wot/security#ComboSecurityScheme"
    description: str = "Combo security scheme definiton"
    scheme: Scheme
    oneOf: oneOf_t
    allOf: allOf_t
    proxy: Optional[Proxy] = None

class apikey_sc(SubmodelElementCollection):
    id_short: AasIdString = "apikey_sc"
    semantic_id: str = "https://www.w3.org/2019/wot/security#APIKeySecurityScheme"
    description: str = "Apikey security scheme definition"
    scheme: Scheme
    name: Optional[Name] = None
    in_: Optional[In] = _Field(default=None, json_schema_extra={"aas_id_short": "in"})
    proxy: Optional[Proxy] = None

class Identity(Property):
    id_short: AasIdString = "identity"
    semantic_id: str = "https://www.w3.org/2019/wot/security#identity"
    description: str = "Identifier providing information which can be used for selection or confirmation."
    value_type: str = "xs:string"

class psk_sc(SubmodelElementCollection):
    id_short: AasIdString = "psk_sc"
    semantic_id: str = "https://www.w3.org/2019/wot/security#PSKSecurityScheme"
    description: str = "PSK security scheme definition"
    scheme: Scheme
    identity: Optional[Identity] = None
    proxy: Optional[Proxy] = None

class Qop(Property):
    id_short: AasIdString = "qop"
    semantic_id: str = "https://www.w3.org/2019/wot/security#qop"
    description: str = "Defines Quality of protection. Values is one of auth or auth-int"
    value_type: str = "xs:string"

class digest_sc(SubmodelElementCollection):
    id_short: AasIdString = "digest_sc"
    semantic_id: str = "https://www.w3.org/2019/wot/security#DigestSecurityScheme"
    description: str = "Digest security scheme definition"
    scheme: Scheme
    name: Optional[Name] = None
    in_: Optional[In] = _Field(default=None, json_schema_extra={"aas_id_short": "in"})
    qop: Optional[Qop] = None
    proxy: Optional[Proxy] = None

class Authorization(Property):
    id_short: AasIdString = "authorization"
    semantic_id: str = "https://www.w3.org/2019/wot/security#authorization"
    description: str = "Specifies URI of the authorization server"
    value_type: str = "xs:anyURI"

class Alg(Property):
    id_short: AasIdString = "alg"
    semantic_id: str = "https://www.w3.org/2019/wot/security#alg"
    description: str = "Defines Encoding, encryption, or digest algorithm (e.g. ES256, ES512-256)."
    value_type: str = "xs:string"

class Format(Property):
    id_short: AasIdString = "format"
    semantic_id: str = "https://www.w3.org/2019/wot/security#format"
    description: str = "Specifies format of security authentication information. Options as value are jwt, cwt, jwe or jws"
    value_type: str = "xs:string"

class bearer_sc(SubmodelElementCollection):
    id_short: AasIdString = "bearer_sc"
    semantic_id: str = "https://www.w3.org/2019/wot/security#BearerSecurityScheme"
    description: str = "bearer security scheme definition"
    scheme: Scheme
    name: Optional[Name] = None
    in_: Optional[In] = _Field(default=None, json_schema_extra={"aas_id_short": "in"})
    authorization: Optional[Authorization] = None
    alg: Optional[Alg] = None
    format: Optional[Format] = None
    proxy: Optional[Proxy] = None

class Token(Property):
    id_short: AasIdString = "token"
    semantic_id: str = "https://www.w3.org/2019/wot/security#token"
    description: str = "Specifies URI of the token server"
    value_type: str = "xs:anyURI"

class Refresh(Property):
    id_short: AasIdString = "refresh"
    semantic_id: str = "https://www.w3.org/2019/wot/security#refresh"
    description: str = "Specifies URI of the refresh server"
    value_type: str = "xs:anyURI"

class scopesItem(Property):
    value_type: str = "xs:string"

class scopes(SubmodelElementList):
    id_short: AasIdString = "scopes"
    semantic_id: str = "https://www.w3.org/2019/wot/security#scopes"
    description: str = "Set of authorization scope identifiers (as Property) provided as an array. These are provided in tokens returned by an authorization server and associated with forms in order to identify what resources a client may access and how."
    type_value_list_element: str = "Property"
    value_type_list_element: str = "xs:string"
    item_type: ClassVar = scopesItem
    value: List[scopesItem] = []

class Flow(Property):
    id_short: AasIdString = "flow"
    semantic_id: str = "https://www.w3.org/2019/wot/security#flow"
    description: str = "Defines authorization flow such as code or client "
    value_type: str = "xs:string"

class oauth2_sc(SubmodelElementCollection):
    id_short: AasIdString = "oauth2_sc"
    semantic_id: str = "https://www.w3.org/2019/wot/security#OAuth2SecurityScheme"
    description: str = "Oauth2 security scheme definition"
    scheme: Scheme
    token: Optional[Token] = None
    refresh: Optional[Refresh] = None
    authorization: Optional[Authorization] = None
    scopes: Optional[scopes_t] = None
    flow: Flow
    proxy: Optional[Proxy] = None

class securityDefinitions(SubmodelElementCollection):
    id_short: AasIdString = "securityDefinitions"
    semantic_id: str = "https://www.w3.org/2019/wot/td#definesSecurityScheme"
    description: str = "Defines the security scheme according to W3C:"
    nosec_sc: Optional[nosec_sc_t] = None
    auto_sc: Optional[auto_sc_t] = None
    basic_sc: Optional[basic_sc_t] = None
    combo_sc: Optional[combo_sc_t] = None
    apikey_sc: Optional[apikey_sc_t] = None
    psk_sc: Optional[psk_sc_t] = None
    digest_sc: Optional[digest_sc_t] = None
    bearer_sc: Optional[bearer_sc_t] = None
    oauth2_sc: Optional[oauth2_sc_t] = None

class ProtocolVersion(Property):
    id_short: AasIdString = "protocolVersion"
    semantic_id: str = "https://www.w3.org/2019/wot/td#versionInfo"
    description: str = "Used by multi-versioned protocols to indicate the specific protocol version of the interface"
    value_type: str = "xs:string"

class EndpointMetadata(SubmodelElementCollection):
    id_short: AasIdString = "EndpointMetadata"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/EndpointMetadata"
    description: str = "Provides the metadata of the asset\u2019s endpoint (base, content type that is used for interaction, etc)"
    base: Optional[Base] = None
    contentType: Optional[ContentType] = None
    security: security_t
    securityDefinitions: securityDefinitions_t
    protocolVersion: Optional[ProtocolVersion] = None

class Key(Property):
    id_short: AasIdString = "key"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/key"
    description: str = "Optional element when the idShort of {property_name} cannot be used to reflect the desired property name due to the idShort restrictions (e.g., payload message uses \u201ctemperature-value\u201d as key term)."
    supplemental_semantic_ids: List[str] = ["https://www.w3.org/2019/wot/td#name"]
    value_type: str = "xs:string"

class Type(Property):
    id_short: AasIdString = "type"
    semantic_id: str = "https://www.w3.org/1999/02/22-rdf-syntax-ns#type"
    description: str = "Indicates the abstract data type (one of object, array, string, number, integer, boolean, or null) of the described datapoint"
    value_type: str = "xs:string"

class Title_td(Property):
    id_short: AasIdString = "title"
    semantic_id: str = "https://www.w3.org/2019/wot/td#title"
    description: str = "Provides a human-readable title of this interaction (e.g., display a text for UI representation)"
    value_type: str = "xs:string"

class Observable(Property):
    id_short: AasIdString = "observable"
    semantic_id: str = "https://www.w3.org/2019/wot/td#isObservable"
    description: str = "An indicator that tells that the interaction datapoint can be observed with a, e.g., subscription mechanism by an underlying protocol."
    value_type: str = "xs:boolean"

class enumItem(Property):
    value_type: str = "xs:string"

class enum(SubmodelElementList):
    id_short: AasIdString = "enum"
    semantic_id: str = "https://www.w3.org/2019/wot/json-schema#enum"
    description: str = "Provides a list of restricted set of values that the asset can provide as datapoint value."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Enum"}
    type_value_list_element: str = "Property"
    value_type_list_element: str = "xs:string"
    item_type: ClassVar = enumItem
    value: List[enumItem] = []

class Const(Property):
    id_short: AasIdString = "const"
    semantic_id: str = "https://www.w3.org/2019/wot/json-schema#const"
    description: str = "Provides a constant value for defined datapoint. The data type should be identical to the one provided by the Property type."
    value_type: str = "xs:string"

class Default(Property):
    id_short: AasIdString = "default"
    semantic_id: str = "https://www.w3.org/2019/wot/json-schema#default"
    description: str = "Provides a default value that must of the type as the datapoint valueType. The data type should be identical to the one as provided by the Property type."
    value_type: str = "xs:string"

class Unit(Property):
    id_short: AasIdString = "unit"
    semantic_id: str = "https://schema.org/unitCode"
    description: str = "Provides information about the datapoint\u2019s unit."
    value_type: str = "xs:string"

class MinMax(Range):
    id_short: AasIdString = "min_max"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/minMaxRange"
    description: str = "Specifies a minimum and/or maximum numeric value for the datapoint. This term is only used when type element is number or integer. When it is number, the range data type has to be float and when it is integer, the range data type has to be integer "
    supplemental_semantic_ids: List[str] = ["https://www.w3.org/2019/wot/json-schema#minimum", "https://www.w3.org/2019/wot/json-schema#maximum"]
    value_type: str = "xs:string"

class LengthRange(Range):
    id_short: AasIdString = "lengthRange"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/lengthRange"
    description: str = "Specifies the minimum and maximum length of a string"
    supplemental_semantic_ids: List[str] = ["https://www.w3.org/2019/wot/json-schema#minLength", "https://www.w3.org/2019/wot/json-schema#maxLength"]
    value_type: str = "xs:unsignedInt"

class ValueSemantics(ReferenceElement):
    id_short: AasIdString = "valueSemantics"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/valueSemantics"
    description: str = "Provides additional semantic information of the value that is read/subscribed at runtime. "

class items(SubmodelElementCollection):
    id_short: AasIdString = "items"
    semantic_id: str = "https://www.w3.org/2019/wot/json-schema#items"
    description: str = "Used to define the data schema characteristics of an array payload"
    type: Optional[Type] = None
    unit: Optional[Unit] = None
    default: Optional[Default] = None
    enum: Optional[enum_t] = None
    const: Optional[Const] = None
    observable: Optional[Observable] = None
    title: Optional[Union[Title_td, Title]] = None
    min_max: Optional[MinMax] = None
    lengthRange: Optional[LengthRange] = None
    valueSemantics: Optional[ValueSemantics] = None

class ItemsRange(Range):
    id_short: AasIdString = "itemsRange"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/itemsRange"
    description: str = "Defines the minimum and maximum number of items that have to be in an array payload."
    supplemental_semantic_ids: List[str] = ["https://www.w3.org/2019/wot/json-schema#minItems", "https://www.w3.org/2019/wot/json-schema#maxItems"]
    value_type: str = "xs:unsignedInt"

class Key_asset_interfaces_description(Property):
    id_short: AasIdString = "key"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/key"
    description: str = "Optional element when the idShort of {property_name} cannot be used to reflect the desired property name due to the idShort restrictions (e.g., payload message uses \u201ctemperature-value\u201d as key term)."
    value_type: str = "xs:string"

class property_name_json_schema(SubmodelElementCollection):
    id_short: AasIdString = "property_name"
    semantic_id: str = "https://www.w3.org/2019/wot/json-schema#propertyName"
    description: str = "Defines a data element within an object-based datapoint.  "
    key: Optional[Union[Key_asset_interfaces_description, Key]] = None
    type: Optional[Type] = None
    title: Optional[Union[Title_td, Title]] = None
    enum: Optional[enum_t] = None
    const: Optional[Const] = None
    default: Optional[Default] = None
    unit: Optional[Unit] = None
    min_max: Optional[MinMax] = None
    lengthRange: Optional[LengthRange] = None
    items: Optional[items_t] = None
    itemsRange: Optional[ItemsRange] = None
    properties: Optional[properties_json_schema] = None
    valueSemantics: Optional[ValueSemantics] = None

class properties_json_schema(SubmodelElementCollection):
    id_short: AasIdString = "properties"
    semantic_id: str = "https://www.w3.org/2019/wot/json-schema#properties"
    description: str = "Nested definitions of a datapoint. Only applicable if type=object."
    property_name: Dict[str, property_name_json_schema] = _Field(default_factory=dict, json_schema_extra={"idta_min_cardinality": 1})

class Href(Property):
    id_short: AasIdString = "href"
    semantic_id: str = "https://www.w3.org/2019/wot/hypermedia#hasTarget"
    description: str = "Target IRI relative path or full IRI of asset\u2019s datapoint. The relative endpoint definition in href is always relative to base defined in EndpointMetadata"
    value_type: str = "xs:string"

class ContentType_for_content_type(Property):
    id_short: AasIdString = "contentType"
    semantic_id: str = "https://www.w3.org/2019/wot/hypermedia#forContentType"
    description: str = "Indicates the datapoint media type specified by IANA."
    value_type: str = "xs:string"

class Subprotocol(Property):
    id_short: AasIdString = "subprotocol"
    semantic_id: str = "https://www.w3.org/2019/wot/hypermedia#forSubProtocol"
    description: str = "Indicates the exact mechanism by which an interaction will be accomplished for a given protocol when there are multiple options."
    value_type: str = "xs:string"

class HtvMethodName(Property):
    id_short: AasIdString = "htv_methodName"
    semantic_id: str = "https://www.w3.org/2011/http#methodName"
    description: str = "Defines the action to be performed datapoint IRI"
    value_type: str = "xs:string"

class HtvFieldName(Property):
    id_short: AasIdString = "htv_fieldName"
    semantic_id: str = "https://www.w3.org/2011/http#fieldName"
    description: str = "Defines message header name "
    value_type: str = "xs:string"

class HtvFieldValue(Property):
    id_short: AasIdString = "htv_fieldValue"
    semantic_id: str = "https://www.w3.org/2011/http#fieldValue"
    description: str = "Defines message header value"
    value_type: str = "xs:string"

class htv_headersItem(SubmodelElementCollection):
    semantic_id: str = "https://www.w3.org/2011/http#headers"
    description: str = "Defines message header content "
    htv_fieldName: HtvFieldName
    htv_fieldValue: HtvFieldValue

class htv_headers(SubmodelElementList):
    id_short: AasIdString = "htv_headers"
    semantic_id: str = "https://www.w3.org/2011/http#headers"
    description: str = "Defines additional information to be sent within the HTTP header message. "
    type_value_list_element: str = "SubmodelElementCollection"
    semantic_id_list_element: str = "https://www.w3.org/2011/http#headers"
    order_relevant: bool = True
    ITEM_CARDINALITY: ClassVar[str] = 'OneToMany'
    item_type: ClassVar = htv_headersItem
    value: List[htv_headersItem] = []

class forms(SubmodelElementCollection):
    id_short: AasIdString = "forms"
    semantic_id: str = "https://www.w3.org/2019/wot/td#hasForm"
    description: str = "Contains information about datapoint resource location. "
    href: Union[Href, Href_has_target]
    contentType: Optional[Union[ContentType_for_content_type, ContentType]] = None
    subprotocol: Optional[Subprotocol] = None
    security: Optional[security_t] = None

class forms_HTTP(forms):
    href: Href
    htv_methodName: HtvMethodName
    htv_headers: Optional[htv_headers_t] = None

class property_name(SubmodelElementCollection):
    id_short: AasIdString = "property_name"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/PropertyDefinition"
    supplemental_semantic_ids: List[str] = ["https://www.w3.org/2019/wot/td#name"]
    description: str = "Defines an interaction property that covers usually a datapoint definition that can be read or subscribed to.  "
    key: Optional[Key] = None
    type: Optional[Type] = None
    title: Optional[Union[Title_td, Title]] = None
    observable: Optional[Observable] = None
    enum: Optional[enum_t] = None
    const: Optional[Const] = None
    default: Optional[Default] = None
    unit: Optional[Unit] = None
    min_max: Optional[MinMax] = None
    lengthRange: Optional[LengthRange] = None
    items: Optional[items_t] = None
    itemsRange: Optional[ItemsRange] = None
    properties: Optional[properties_json_schema] = None
    valueSemantics: Optional[ValueSemantics] = None
    forms: forms_t

class property_name_HTTP(property_name):
    forms: forms_HTTP

class properties(SubmodelElementCollection):
    id_short: AasIdString = "properties"
    semantic_id: str = "https://www.w3.org/2019/wot/td#PropertyAffordance"
    description: str = "Collection of asset\u2019s datapoint definitions as property SMC "
    property_name: Dict[str, property_name_t] = {}

class properties_HTTP(properties):
    property_name: Dict[str, property_name_HTTP] = {}

class actions(DynamicSubmodelElementCollection):
    id_short: AasIdString = "actions"
    semantic_id: str = "https://www.w3.org/2019/wot/td#ActionAffordance"
    description: str = "Collection of functions that can be done on asset as action SMC"

class events(DynamicSubmodelElementCollection):
    id_short: AasIdString = "events"
    semantic_id: str = "https://www.w3.org/2019/wot/td#EventAffordance"
    description: str = "Collection of events triggerable by datapoint state as event SMC"

class InteractionMetadata(SubmodelElementCollection):
    id_short: AasIdString = "InteractionMetadata"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/InteractionMetadata"
    supplemental_semantic_ids: List[str] = ["https://www.w3.org/2019/wot/td#InteractionAffordance"]
    description: str = "Provides the metadata of the actually interfaces such as which datapoints and functions are provided by the properties, actions, and events interaction abstraction. "
    properties: Optional[properties_t] = None
    actions: Optional[actions_t] = None
    events: Optional[events_t] = None

class InteractionMetadata_HTTP(InteractionMetadata):
    properties: Optional[properties_HTTP] = None

class FileName(File):
    id_short: AasIdString = "fileName"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/externalDescriptorName"
    content_type: str = "application/json"

class ExternalDescriptor(SubmodelElementCollection):
    id_short: AasIdString = "ExternalDescriptor"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/ExternalDescriptor"
    description: str = "Provides a place for existing description files (e.g., Thing Description, GSDML, etc,)."
    fileName: FileName

class InterfaceTemplateForHTTP(SubmodelElementCollection):
    id_short: AasIdString = "InterfaceTemplateForHTTP"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Interface"
    description: str = "Indicates the entry point for a particular asset interface"
    supplemental_semantic_ids: List[str] = ["http://www.w3.org/2011/http", "https://www.w3.org/2019/wot/td"]
    title: Title
    created: Optional[Created] = None
    modified: Optional[Modified] = None
    support: Optional[Support] = None
    EndpointMetadata: EndpointMetadata_t
    InteractionMetadata: InteractionMetadata_HTTP
    ExternalDescriptor: Optional[ExternalDescriptor_t] = None

class ModvMostSignificantByte(Property):
    id_short: AasIdString = "modv_mostSignificantByte"
    semantic_id: str = "https://www.w3.org/2019/wot/modbus#hasMostSignificantByte"
    description: str = "This property is only applicable for Modbus-based communication. When modv_mostSignificantByte is true, it describes that the byte order of the data in the Modbus message is the most significant byte first (i.e., Big-Endian). When false, it describes the least significant byte first (i.e., Little-Endian)."
    value_type: str = "xs:boolean"

class ModvMostSignificantWord(Property):
    id_short: AasIdString = "modv_mostSignificantWord"
    semantic_id: str = "https://www.w3.org/2019/wot/modbus#hasMostSignificantWord"
    description: str = "This property is only applicable for Modbus-based communication. When modv_mostSignificantWord is true, it describes that the word order of the data in the Modbus message is the most significant word first (i.e., no word swapping). When false, it describes the least significant word first (i.e. word swapping)."
    value_type: str = "xs:boolean"

class EndpointMetadata_MODBUS(EndpointMetadata):
    modv_mostSignificantByte: Optional[ModvMostSignificantByte] = None
    modv_mostSignificantWord: Optional[ModvMostSignificantWord] = None

class ModvFunction(Property):
    id_short: AasIdString = "modv_function"
    semantic_id: str = "https://www.w3.org/2019/wot/modbus#hasFunction"
    description: str = "Abstraction of the Modbus function code sent during a request. A function value can be either readCoil, readDeviceIdentification, readDiscreteInput, readHoldingRegisters, readInputRegisters, writeMultipleCoils, writeMultipleHoldingRegisters, writeSingleCoil, or  writeSingleHoldingRegister"
    value_type: str = "xs:string"

class ModvEntity(Property):
    id_short: AasIdString = "modv_entity"
    semantic_id: str = "https://www.w3.org/2019/wot/modbus#hasEntity"
    description: str = "A registry type to let the runtime automatically detect the right function code. An entity value can be Coil, DiscreteInput, HoldingRegister, or InputRegister"
    value_type: str = "xs:string"

class ModvZeroBasedAddressing(Property):
    id_short: AasIdString = "modv_zeroBasedAddressing"
    semantic_id: str = "https://www.w3.org/2019/wot/modbus#hasZeroBasedAddressingFlag"
    description: str = "Modbus implementations can differ in the way addressing works, as the first coil/register can be either referred to as True or False."
    value_type: str = "xs:boolean"

class ModvPollingTime(Property):
    id_short: AasIdString = "modv_pollingTime"
    semantic_id: str = "https://www.w3.org/2019/wot/modbus#hasPollingTime"
    description: str = "Modbus TCP maximum polling rate. The Modbus specification does not define a maximum or minimum allowed polling rate, however specific implementations might introduce such limits. Defined as integer of milliseconds."
    value_type: str = "xs:integer"

class ModvTimeout(Property):
    id_short: AasIdString = "modv_timeout"
    semantic_id: str = "https://www.w3.org/2019/wot/modbus#hasTimeout"
    description: str = "Modbus response maximum waiting time. Defines how much time in milliseconds the runtime should wait until it receives a reply from the device."
    value_type: str = "xs:integer"

class ModvType(Property):
    id_short: AasIdString = "modv_type"
    semantic_id: str = "https://www.w3.org/2019/wot/modbus#hasPayloadDataType"
    description: str = "Defines the data type of the modbus asset payload. type in terms of possible sign, base type. the modv_type offers a set a types defined in XML schema "
    value_type: str = "xs:string"

class forms_MODBUS(forms):
    href: Href
    modv_function: Optional[ModvFunction] = None
    modv_entity: Optional[ModvEntity] = None
    modv_zeroBasedAddressing: Optional[ModvZeroBasedAddressing] = None
    modv_pollingTime: Optional[ModvPollingTime] = None
    modv_timeout: Optional[ModvTimeout] = None
    modv_type: Optional[ModvType] = None
    modv_mostSignificantByte: Optional[ModvMostSignificantByte] = None
    modv_mostSignificantWord: Optional[ModvMostSignificantWord] = None

class property_name_MODBUS(property_name):
    forms: forms_MODBUS

class properties_MODBUS(properties):
    property_name: Dict[str, property_name_MODBUS] = {}

class InteractionMetadata_MODBUS(InteractionMetadata):
    description: str = "Provides the metadata of the actually interfaces such as which datapoints and functions are provided by the properties, actions, and events interaction abstraction"
    properties: Optional[properties_MODBUS] = None

class InterfaceTemplateForMODBUS(SubmodelElementCollection):
    id_short: AasIdString = "InterfaceTemplateForMODBUS"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Interface"
    description: str = "Indicates the entry point for a particular asset interface"
    supplemental_semantic_ids: List[str] = ["http://www.w3.org/2011/modbus", "https://www.w3.org/2019/wot/td"]
    title: Title
    created: Optional[Created] = None
    modified: Optional[Modified] = None
    support: Optional[Support] = None
    EndpointMetadata: EndpointMetadata_MODBUS
    InteractionMetadata: InteractionMetadata_MODBUS
    ExternalDescriptor: Optional[ExternalDescriptor_t] = None

class MqvRetain(Property):
    id_short: AasIdString = "mqv_retain"
    semantic_id: str = "https://www.w3.org/2019/wot/mqtt#hasRetainFlag"
    description: str = "It is an indicator that tells the broker to always retain last published payload. "
    value_type: str = "xs:boolean"

class MqvControlPacket(Property):
    id_short: AasIdString = "mqv_controlPacket"
    semantic_id: str = "https://www.w3.org/2019/wot/mqtt#ControlPacket"
    description: str = "Defines the method associated to the datapoint in relation to the broker"
    value_type: str = "xs:string"

class MqvQos(Property):
    id_short: AasIdString = "mqv_qos"
    semantic_id: str = "https://www.w3.org/2019/wot/mqtt#hasQoSFlag"
    description: str = "Defined the level of guarantee for message delivery between clients."
    value_type: str = "xs:string"

class forms_MQTT(forms):
    href: Href
    mqv_retain: Optional[MqvRetain] = None
    mqv_controlPacket: Optional[MqvControlPacket] = None
    mqv_qos: Optional[MqvQos] = None

class property_name_MQTT(property_name):
    description: str = "Current counter value"
    forms: forms_MQTT

class properties_MQTT(properties):
    property_name: Dict[str, property_name_MQTT] = {}

class InteractionMetadata_MQTT(InteractionMetadata):
    description: str = "Provides the metadata of the actually interfaces such as which datapoints and functions are provided by the properties, actions, and events interaction abstraction"
    properties: Optional[properties_MQTT] = None

class InterfaceTemplateForMQTT(SubmodelElementCollection):
    id_short: AasIdString = "InterfaceTemplateForMQTT"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Interface"
    description: str = "Indicates the entry point for a particular asset interface"
    supplemental_semantic_ids: List[str] = ["http://www.w3.org/2011/mqtt", "https://www.w3.org/2019/wot/td"]
    title: Title
    created: Optional[Created] = None
    modified: Optional[Modified] = None
    support: Optional[Support] = None
    EndpointMetadata: EndpointMetadata_t
    InteractionMetadata: InteractionMetadata_MQTT
    ExternalDescriptor: Optional[ExternalDescriptor_t] = None

class UavSecurityMode(Property):
    id_short: AasIdString = "uav_securityMode"
    semantic_id: str = "http://opcfoundation.org/UA/WoT-Binding/securityMode"
    value_type: str = "xs:string"

class UavSecurityPolicy(Property):
    id_short: AasIdString = "uav_securityPolicy"
    semantic_id: str = "http://opcfoundation.org/UA/WoT-Binding/securityPolicy"
    value_type: str = "xs:string"

class opcua_channel_sc(SubmodelElementCollection):
    id_short: AasIdString = "opcua_channel_sc"
    semantic_id: str = "http://opcfoundation.org/UA/WoT-Binding/OPCUASecurityChannelScheme"
    scheme: Scheme
    proxy: Optional[Proxy] = None
    uav_securityMode: UavSecurityMode
    uav_securityPolicy: UavSecurityPolicy

class UavUserIdentityToken(Property):
    id_short: AasIdString = "uav_userIdentityToken"
    semantic_id: str = "http://opcfoundation.org/UA/WoT-Binding/userIdentityToken"
    value_type: str = "xs:string"

class UavIssueToken(ReferenceElement):
    id_short: AasIdString = "uav_issueToken"
    semantic_id: str = "http://opcfoundation.org/UA/WoT-Binding/issueToken"

class opcua_authentication_sc(SubmodelElementCollection):
    id_short: AasIdString = "opcua_authentication_sc"
    semantic_id: str = "http://opcfoundation.org/UA/WoT-Binding/OPCUASecurityAuthenticationScheme"
    scheme: Scheme
    proxy: Optional[Proxy] = None
    uav_userIdentityToken: UavUserIdentityToken
    uav_issueToken: Optional[UavIssueToken] = None

class securityDefinitions_OPCUA(securityDefinitions):
    opcua_channel_sc: Optional[opcua_channel_sc_t] = None
    opcua_authentication_sc: Optional[opcua_authentication_sc_t] = None

class EndpointMetadata_OPCUA(EndpointMetadata):
    securityDefinitions: securityDefinitions_OPCUA

class UavBrowsePath(Property):
    id_short: AasIdString = "uav_browsePath"
    semantic_id: str = "http://opcfoundation.org/UA/WoT-Binding/browsePath"
    description: str = "Defines an absolute path of a datapoint, starting from the root node of an OPC UA address space. This term is only used for OPC UA interface. "
    value_type: str = "xs:string"

class forms_OPCUA(forms):
    href: Href
    uav_browsePath: Optional[UavBrowsePath] = None

class property_name_OPCUA(property_name):
    forms: forms_OPCUA

class properties_OPCUA(properties):
    property_name: Dict[str, property_name_OPCUA] = {}

class InteractionMetadata_OPCUA(InteractionMetadata):
    description: str = "Provides the metadata of the actually interfaces such as which datapoints and functions are provided by the properties, actions, and events interaction abstraction"
    properties: Optional[properties_OPCUA] = None

class InterfaceTemplateForOPCUA(SubmodelElementCollection):
    id_short: AasIdString = "InterfaceTemplateForOPCUA"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Interface"
    description: str = "Indicates the entry point for a particular asset interface"
    supplemental_semantic_ids: List[str] = ["http://opcfoundation.org/UA/WoT-Binding/", "https://www.w3.org/2019/wot/td"]
    title: Title
    created: Optional[Created] = None
    modified: Optional[Modified] = None
    support: Optional[Support] = None
    EndpointMetadata: EndpointMetadata_OPCUA
    InteractionMetadata: InteractionMetadata_OPCUA
    ExternalDescriptor: Optional[ExternalDescriptor_t] = None

class property_name_json_schema_Bacnet(property_name_json_schema):
    properties: Optional[properties_json_schema_Bacnet] = None
    observable: Optional[Observable] = None

class properties_json_schema_Bacnet(properties_json_schema):
    property_name: Dict[str, property_name_json_schema_Bacnet] = _Field(default_factory=dict, json_schema_extra={"idta_min_cardinality": 1})

class uriVariables(SubmodelElementCollection):
    id_short: AasIdString = "uriVariables"
    semantic_id: str = "https://www.w3.org/2019/wot/td#hasUriTemplateSchema"
    description: str = "Defines URI template variables according to RFC6570 as a collection based on an interaction affordance data schema"
    property_name: Dict[str, property_name_json_schema_Bacnet] = {}

class BacvUseService(Property):
    id_short: AasIdString = "bacv_useService"
    semantic_id: str = "http://www.w3.org/2022/bacnet#usesService"
    description: str = "Defines the BACnet service to use on a datapoint operation"
    value_type: str = "xs:string"
    FORM_CHOICES: ClassVar[tuple] = ('ReadProperty', 'WriteProperty', 'SubscribeCOV', 'GetEventInfo', 'AcknowlegeAlarm', 'AddListElement', 'RemoveListElement')

class BacvIsISO8601(Property):
    id_short: AasIdString = "bacv_isISO8601"
    semantic_id: str = "http://www.w3.org/2022/bacnet#isIso8601"
    description: str = "Defines if the data uses ISO8601 format"
    value_type: str = "xs:boolean"

class BacvHasBinaryRepresentation(Property):
    id_short: AasIdString = "bacv_hasBinaryRepresentation"
    semantic_id: str = "http://www.w3.org/2022/bacnet#hasBinaryRepresentation"
    description: str = "Defines the payload\u2019s binary representation type. This term is used when the payload is an OctetString."
    value_type: str = "xs:string"

class BacvHasFieldName(Property):
    id_short: AasIdString = "bacv_hasFieldName"
    semantic_id: str = "http://www.w3.org/2022/bacnet#hasfieldName"
    description: str = "Defines name of a Named Member of a Sequence or Choice data type."
    value_type: str = "xs:string"

class BacvHasContextTag(Property):
    id_short: AasIdString = "bacv_hasContextTag"
    semantic_id: str = "http://www.w3.org/2022/bacnet#hasContextTag"
    description: str = "Defines Context Tag for a Named Member of a Sequence or Choice data type."
    value_type: str = "xs:boolean"

class bacv_hasNamedMemberItem(SubmodelElementCollection):
    semantic_id: str = "http://www.w3.org/2022/bacnet#NamedMember"
    description: str = "Defines the Named Member of a Sequence or Choice data type."
    bacv_hasFieldName: BacvHasFieldName
    bacv_hasContextTag: Optional[BacvHasContextTag] = None
    bacv_hasDataType: Optional[bacv_hasDataType_t] = None

class bacv_hasNamedMember(SubmodelElementList):
    id_short: AasIdString = "bacv_hasNamedMember"
    semantic_id: str = "http://www.w3.org/2022/bacnet#hasNamedMember"
    type_value_list_element: str = "SubmodelElementCollection"
    semantic_id_list_element: str = "http://www.w3.org/2022/bacnet#NamedMember"
    order_relevant: bool = True
    ITEM_CARDINALITY: ClassVar[str] = 'OneToMany'
    item_type: ClassVar = bacv_hasNamedMemberItem
    value: List[bacv_hasNamedMemberItem] = []

class BacvHasLogicalVal(Property):
    id_short: AasIdString = "bacv_hasLogicalVal"
    semantic_id: str = "http://www.w3.org/2022/bacnet#hasLogicalVal"
    description: str = "Defines the logical value for a ValueMap"
    value_type: str = "xs:string"

class BacvHasProtocolVal(Property):
    id_short: AasIdString = "bacv_hasProtocolVal"
    semantic_id: str = "http://www.w3.org/2022/bacnet#hasProtocolVal"
    description: str = "Defines the protocol value for a ValueMap."
    value_type: str = "xs:integer"

class bacv_hasValueMapItem(SubmodelElementCollection):
    semantic_id: str = "http://www.w3.org/2022/bacnet#hasMapEntry"
    description: str = "Defines the value map for an Enumeration."
    bacv_hasLogicalVal: BacvHasLogicalVal
    bacv_hasProtocolVal: BacvHasProtocolVal

class bacv_hasValueMap(SubmodelElementList):
    id_short: AasIdString = "bacv_hasValueMap"
    semantic_id: str = "http://www.w3.org/2022/bacnet#hasValueMap"
    description: str = "Defines the value map of an enumeration."
    type_value_list_element: str = "SubmodelElementCollection"
    semantic_id_list_element: str = "http://www.w3.org/2022/bacnet#hasMapEntry"
    order_relevant: bool = True
    ITEM_CARDINALITY: ClassVar[str] = 'ZeroToMany'
    item_type: ClassVar = bacv_hasValueMapItem
    value: List[bacv_hasValueMapItem] = []

class bacv_hasMember(SubmodelElementCollection):
    id_short: AasIdString = "bacv_hasMember"
    semantic_id: str = "http://www.w3.org/2022/bacnet#hasMember"
    description: str = "Defines the member of a Sequence and List data type."
    bacv_isISO8601: Optional[BacvIsISO8601] = None
    bacv_hasBinaryRepresentation: Optional[BacvHasBinaryRepresentation] = None
    bacv_hasMember: Optional[bacv_hasMember_t] = None
    bacv_hasNamedMember: Optional[bacv_hasNamedMember_t] = None
    bacv_hasValueMap: Optional[bacv_hasValueMap_t] = None

class bacv_hasDataType(SubmodelElementCollection):
    id_short: AasIdString = "bacv_hasDataType"
    semantic_id: str = "http://www.w3.org/2022/bacnet#hasDataType"
    description: str = "Defines the type information of a BACnet payload. This SMC is used to abstract BACnet data model to human and machine readable model by still keeping its wire compatibility on the protocol."
    supplemental_semantic_ids: List[str] = ["http://www.w3.org/2022/bacnet#SequenceOf", "http://www.w3.org/2022/bacnet#Sequence", "http://www.w3.org/2022/bacnet#List", "http://www.w3.org/2022/bacnet#Choice", "http://www.w3.org/2022/bacnet#Date", "http://www.w3.org/2022/bacnet#Time", "http://www.w3.org/2022/bacnet#WeekNDay", "http://www.w3.org/2022/bacnet#Unsigned", "http://www.w3.org/2022/bacnet#Signed", "http://www.w3.org/2022/bacnet#Real", "http://www.w3.org/2022/bacnet#Double", "http://www.w3.org/2022/bacnet#Boolean", "http://www.w3.org/2022/bacnet#Enumerated", "http://www.w3.org/2022/bacnet#String", "http://www.w3.org/2022/bacnet#OctetString", "http://www.w3.org/2022/bacnet#BitString", "http://www.w3.org/2022/bacnet#Any", "http://www.w3.org/2022/bacnet#Null", "http://www.w3.org/2022/bacnet#ObjectIdentifier"]
    bacv_isISO8601: Optional[BacvIsISO8601] = None
    bacv_hasBinaryRepresentation: Optional[BacvHasBinaryRepresentation] = None
    bacv_hasMember: Optional[bacv_hasMember_t] = None
    bacv_hasNamedMember: Optional[bacv_hasNamedMember_t] = None
    bacv_hasValueMap: Optional[bacv_hasValueMap_t] = None

class forms_Bacnet(forms):
    href: Href
    bacv_useService: Optional[BacvUseService] = None
    bacv_hasDataType: Optional[bacv_hasDataType_t] = None

class property_name_Bacnet(property_name):
    properties: Optional[properties_json_schema_Bacnet] = None
    uriVariables: Optional[uriVariables_t] = None
    forms: forms_Bacnet

class properties_Bacnet(properties):
    property_name: Dict[str, property_name_Bacnet] = {}

class InteractionMetadata_Bacnet(InteractionMetadata):
    description: str = "Provides the metadata of the actually interfaces such as which datapoints and functions are provided by the properties, actions, and events interaction abstraction"
    properties: Optional[properties_Bacnet] = None

class InterfaceTemplateForBacnet(SubmodelElementCollection):
    id_short: AasIdString = "InterfaceTemplateForBacnet"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Interface"
    description: str = "Indicates the entry point for a particular asset interface"
    supplemental_semantic_ids: List[str] = ["http://www.w3.org/2022/bacnet", "https://www.w3.org/2019/wot/td"]
    title: Title
    created: Optional[Created] = None
    modified: Optional[Modified] = None
    support: Optional[Support] = None
    EndpointMetadata: EndpointMetadata_t
    InteractionMetadata: InteractionMetadata_Bacnet
    ExternalDescriptor: Optional[ExternalDescriptor_t] = None

class IolvMethod(Property):
    id_short: AasIdString = "iolv_method"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/hasMethod"
    description: str = "Defines the type of operation to execute on a datapoint"
    value_type: str = "xs:string"

class IolvAccessRights(Property):
    id_short: AasIdString = "iolv_accessRights"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/hasAccessRights"
    description: str = "Defines the type of operation that can be executed of a datapoint."
    value_type: str = "xs:string"

class IolvType(Property):
    id_short: AasIdString = "iolv_type"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/hasPayloadDataType"
    description: str = "Specifies the data type contained in the request or response payload. "
    value_type: str = "xs:string"

class IolvByteOffset(Property):
    id_short: AasIdString = "iolv_byteOffset"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/byteOffset"
    description: str = "For object type datapoints. Used to identify the starting point within a byte stream payload that represents a datapoint"
    value_type: str = "xs:nonNegativeInteger"

class IolvByteLength(Property):
    id_short: AasIdString = "iolv_byteLength"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/byteLength"
    description: str = "For object type datapoints. Used to identify the byte length within a byte stream payload that represents a datapoint."
    value_type: str = "xs:nonNegativeInteger"

class IolvBitOffset(Property):
    id_short: AasIdString = "iolv_bitOffset"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/bitOffset"
    description: str = "For object type datapoints. Used to identify the starting point within a bit stream payload that represents a datapoint."
    value_type: str = "xs:nonNegativeInteger"

class IolvBitLength(Property):
    id_short: AasIdString = "iolv_bitLength"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/bitLength"
    description: str = "For object type datapoints. Used to identify the bit length of a datapoint from the bit stream payload."
    value_type: str = "xs:nonNegativeInteger"

class IolvReferenceToCondition(ReferenceElement):
    id_short: AasIdString = "iolv_referenceToCondition"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/referenceToCondition"
    description: str = "Defined the reference to a condition that must be validated on a datapoint. "

class IolvEncodedPayload(Property):
    id_short: AasIdString = "iolv_encodedPayload"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/encodedPayload"
    description: str = "Specifies the presentation of the payload Logical encoding"
    value_type: str = "xs:string"

class IolvDecodedPayload(Property):
    id_short: AasIdString = "iolv_decodedPayload"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/decodedPayload"
    description: str = "Specifies the human readable meaning of the payload Logical encoding.  "
    value_type: str = "xs:integer"

class iolv_enumeratedValuesItem(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/enumeratedValue"
    description: str = "Defines the logical semantic to encoded payload provided a byte or byte stream."
    iolv_encodedPayload: IolvEncodedPayload
    iolv_decodedPayload: IolvDecodedPayload

class iolv_enumeratedValues(SubmodelElementList):
    id_short: AasIdString = "iolv_enumeratedValues"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/hasEnumeratedValues"
    description: str = "Contains a list of enumerated values that define the logical semantic to encoded payload provided a byte or byte stream"
    type_value_list_element: str = "SubmodelElementCollection"
    semantic_id_list_element: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/enumeratedValue"
    ITEM_CARDINALITY: ClassVar[str] = 'OneToMany'
    item_type: ClassVar = iolv_enumeratedValuesItem
    value: List[iolv_enumeratedValuesItem] = []

class IolvReferenceToProperty(ReferenceElement):
    id_short: AasIdString = "iolv_referenceToProperty"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/referenceToProperty"
    description: str = "Defined the reference to a nested datapoint of an object type datapoint. "

class iolv_payloadMappingItem(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/payloadMapping"
    description: str = "Defines the payload mapping associated to a datapoint."
    iolv_referenceToProperty: Optional[IolvReferenceToProperty] = None
    iolv_type: Optional[IolvType] = None
    iolv_byteOffset: Optional[IolvByteOffset] = None
    iolv_byteLength: Optional[IolvByteLength] = None
    iolv_bitOffset: Optional[IolvBitOffset] = None
    iolv_bitLength: Optional[IolvBitLength] = None
    iolv_enumeratedValues: Optional[iolv_enumeratedValues_t] = None

class iolv_payloadMapping(SubmodelElementList):
    id_short: AasIdString = "iolv_payloadMapping"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/hasPayloadMapping"
    description: str = "For object type datapoints. Used to provides logical mapping information for a complex payload from an IO-Link device."
    type_value_list_element: str = "SubmodelElementCollection"
    semantic_id_list_element: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/payloadMapping"
    item_type: ClassVar = iolv_payloadMappingItem
    value: List[iolv_payloadMappingItem] = []

class forms_IOLINK_OVER_PROFINET_REST(forms):
    href: Href
    iolv_method: Optional[IolvMethod] = None
    iolv_accessRights: Optional[IolvAccessRights] = None
    iolv_type: Optional[IolvType] = None
    iolv_byteOffset: Optional[IolvByteOffset] = None
    iolv_byteLength: Optional[IolvByteLength] = None
    iolv_bitOffset: Optional[IolvBitOffset] = None
    iolv_bitLength: Optional[IolvBitLength] = None
    iolv_referenceToCondition: Optional[IolvReferenceToCondition] = None
    iolv_enumeratedValues: Optional[iolv_enumeratedValues_t] = None
    iolv_payloadMapping: Optional[iolv_payloadMapping_t] = None

class property_name_IOLINK_OVER_PROFINET_REST(property_name):
    forms: forms_IOLINK_OVER_PROFINET_REST

class properties_IOLINK_OVER_PROFINET_REST(properties):
    property_name: Dict[str, property_name_IOLINK_OVER_PROFINET_REST] = {}

class InteractionMetadata_IOLINK_OVER_PROFINET_REST(InteractionMetadata):
    description: str = "Provides the metadata of the actually interfaces such as which datapoints and functions are provided by the properties, actions, and events interaction abstraction"
    properties: Optional[properties_IOLINK_OVER_PROFINET_REST] = None

class InterfaceTemplateForIOLINK_OVER_PROFINET_REST(SubmodelElementCollection):
    id_short: AasIdString = "InterfaceTemplateForIOLINK_OVER_PROFINET_REST"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Interface"
    description: str = "Indicates the entry point for a particular asset interface"
    supplemental_semantic_ids: List[str] = ["https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link", "https://www.w3.org/2019/wot/td"]
    title: Title
    created: Optional[Created] = None
    modified: Optional[Modified] = None
    support: Optional[Support] = None
    EndpointMetadata: EndpointMetadata_t
    InteractionMetadata: InteractionMetadata_IOLINK_OVER_PROFINET_REST
    ExternalDescriptor: Optional[ExternalDescriptor_t] = None

class forms_SNMP(forms):
    href: Href

class property_name_SNMP(property_name):
    forms: forms_SNMP

class properties_SNMP(properties):
    property_name: Dict[str, property_name_SNMP] = {}

class InteractionMetadata_SNMP(InteractionMetadata):
    description: str = "Provides the metadata of the actually interfaces such as which datapoints and functions are provided by the properties, actions, and events interaction abstraction"
    properties: Optional[properties_SNMP] = None

class InterfaceTemplateForSNMP(SubmodelElementCollection):
    id_short: AasIdString = "InterfaceTemplateForSNMP"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Interface"
    description: str = "Indicates the entry point for a particular asset interface"
    supplemental_semantic_ids: List[str] = ["https://admin-shell.io/idta/AssetInterfacesDescription/1/2/SNMP", "https://www.w3.org/2019/wot/td"]
    title: Title
    created: Optional[Created] = None
    modified: Optional[Modified] = None
    support: Optional[Support] = None
    EndpointMetadata: EndpointMetadata_t
    InteractionMetadata: InteractionMetadata_SNMP
    ExternalDescriptor: Optional[ExternalDescriptor_t] = None

class Href_has_target(Property):
    id_short: AasIdString = "href"
    semantic_id: str = "https://www.w3.org/2019/wot/hypermedia#hasTarget"
    description: str = "Target IRI relative path or full IRI of asset\u2019s datapoint. The relative endpoint definition in href is always relative to base defined in EndpointMetadata"
    value_type: str = "xs:string"
    ALLOWED_RANGE: ClassVar[tuple] = ('0x00000000', '0x1fffffff')

class CanvOffset(Property):
    id_short: AasIdString = "canv_offset"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/2/CAN/offset"
    description: str = "Offset to indicate the beginning of a data point in the message payload."
    value_type: str = "xs:nonNegativeInteger"
    ALLOWED_RANGE: ClassVar[tuple] = ('0', '63')

class CanvLength(Property):
    id_short: AasIdString = "canv_length"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/2/CAN/length"
    description: str = "Length of the data point in the message payload."
    value_type: str = "xs:nonNegativeInteger"
    ALLOWED_RANGE: ClassVar[tuple] = ('1', '64')

class CanvValueOffset(Property):
    id_short: AasIdString = "canv_valueOffset"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/2/CAN/value-offset"
    description: str = "A constant to add to the decoded data point in order to restore its actual value"
    value_type: str = "xs:double"

class CanvEncodedPayload(Property):
    id_short: AasIdString = "canv_encodedPayload"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/2/CAN/encodedPayload"
    description: str = "Specifies the presentation of the payload Logical encoding"
    value_type: str = "xs:string"

class CanvDecodedPayload(Property):
    id_short: AasIdString = "canv_decodedPayload"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/2/CAN/decodedPayload"
    description: str = "Specifies the presentation of the payload Logical encoding"
    value_type: str = "xs:integer"

class canv_enumeratedValuesItem(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/2/CAN/enumeratedValue"
    description: str = "Defines the logical semantic to encoded payload provided a byte or byte stream"
    canv_encodedPayload: CanvEncodedPayload
    canv_decodedPayload: CanvDecodedPayload

class canv_enumeratedValues(SubmodelElementList):
    id_short: AasIdString = "canv_enumeratedValues"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/2/CAN/hasEnumeratedValues"
    description: str = "Contains a list of enumerated values that define the logical semantic to encoded payload provided a byte or byte stream. "
    type_value_list_element: str = "SubmodelElementCollection"
    semantic_id_list_element: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/2/CAN/enumeratedValue"
    ITEM_CARDINALITY: ClassVar[str] = 'OneToMany'
    item_type: ClassVar = canv_enumeratedValuesItem
    value: List[canv_enumeratedValuesItem] = []

class CanvReferenceToProperty(ReferenceElement):
    id_short: AasIdString = "canv_referenceToProperty"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/2/CAN/referenceToProperty"
    description: str = "Defined the reference to a nested datapoint of an object type datapoint. "

class canv_payloadMappingItem(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/2/CAN/payloadMapping"
    description: str = "Defines the payload mapping associated to a datapoint."
    canv_referenceToProperty: CanvReferenceToProperty
    canv_offset: CanvOffset
    canv_length: CanvLength
    canv_valueOffset: Optional[CanvValueOffset] = None
    canv_enumeratedValues: Optional[canv_enumeratedValues_t] = None

class canv_payloadMapping(SubmodelElementList):
    id_short: AasIdString = "canv_payloadMapping"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/2/CAN/hasPayloadMapping"
    description: str = "For object type datapoints. Used to provide logical mapping information of a complex payload from a CAN device."
    type_value_list_element: str = "SubmodelElementCollection"
    semantic_id_list_element: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/2/CAN/payloadMapping"
    item_type: ClassVar = canv_payloadMappingItem
    value: List[canv_payloadMappingItem] = []

class forms_CAN(forms):
    href: Union[Href_has_target, Href]
    canv_offset: Optional[CanvOffset] = None
    canv_length: Optional[CanvLength] = None
    canv_valueOffset: Optional[CanvValueOffset] = None
    canv_enumeratedValues: Optional[canv_enumeratedValues_t] = None
    canv_payloadMapping: Optional[canv_payloadMapping_t] = None

class property_name_CAN(property_name):
    forms: forms_CAN

class properties_CAN(properties):
    property_name: Dict[str, property_name_CAN] = {}

class InteractionMetadata_CAN(InteractionMetadata):
    description: str = "Provides the metadata of the actually interfaces such as which datapoints and functions are provided by the properties, actions, and events interaction abstraction"
    properties: Optional[properties_CAN] = None

class InterfaceTemplateForCAN(SubmodelElementCollection):
    id_short: AasIdString = "InterfaceTemplateForCAN"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Interface"
    description: str = "Indicates the entry point for a particular asset interface"
    supplemental_semantic_ids: List[str] = ["https://admin-shell.io/idta/AssetInterfacesDescription/1/2/CAN", "https://www.w3.org/2019/wot/td"]
    title: Title
    created: Optional[Created] = None
    modified: Optional[Modified] = None
    support: Optional[Support] = None
    EndpointMetadata: EndpointMetadata_t
    InteractionMetadata: InteractionMetadata_CAN
    ExternalDescriptor: Optional[ExternalDescriptor_t] = None

class AssetInterfacesDescription(Submodel):
    id_short: AasIdString = "AssetInterfacesDescription"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/2/Submodel"
    description: str = "Definition of the Submodel Asset Interfaces Description identified by its semanticId."
    IDTA_ONE_OF: ClassVar[tuple] = ('InterfaceTemplateForHTTP', 'InterfaceTemplateForMODBUS', 'InterfaceTemplateForMQTT', 'InterfaceTemplateForOPCUA', 'InterfaceTemplateForBacnet', 'InterfaceTemplateForIOLINK_OVER_PROFINET_REST', 'InterfaceTemplateForSNMP', 'InterfaceTemplateForCAN')
    VERSION: ClassVar[str] = "1"
    REVISION: ClassVar[str] = "2"
    InterfaceTemplateForHTTP: Dict[str, InterfaceTemplateForHTTP_t] = {}
    InterfaceTemplateForMODBUS: Dict[str, InterfaceTemplateForMODBUS_t] = {}
    InterfaceTemplateForMQTT: Dict[str, InterfaceTemplateForMQTT_t] = {}
    InterfaceTemplateForOPCUA: Dict[str, InterfaceTemplateForOPCUA_t] = {}
    InterfaceTemplateForBacnet: Dict[str, InterfaceTemplateForBacnet_t] = {}
    InterfaceTemplateForIOLINK_OVER_PROFINET_REST: Dict[str, InterfaceTemplateForIOLINK_OVER_PROFINET_REST_t] = {}
    InterfaceTemplateForSNMP: Dict[str, InterfaceTemplateForSNMP_t] = {}
    InterfaceTemplateForCAN: Dict[str, InterfaceTemplateForCAN_t] = {}

# alias so field ``oneOf_t`` can name a class of the same id_short
oneOf_t: TypeAlias = oneOf
# alias so field ``allOf_t`` can name a class of the same id_short
allOf_t: TypeAlias = allOf
# alias so field ``scopes_t`` can name a class of the same id_short
scopes_t: TypeAlias = scopes
# alias so field ``nosec_sc_t`` can name a class of the same id_short
nosec_sc_t: TypeAlias = nosec_sc
# alias so field ``auto_sc_t`` can name a class of the same id_short
auto_sc_t: TypeAlias = auto_sc
# alias so field ``basic_sc_t`` can name a class of the same id_short
basic_sc_t: TypeAlias = basic_sc
# alias so field ``combo_sc_t`` can name a class of the same id_short
combo_sc_t: TypeAlias = combo_sc
# alias so field ``apikey_sc_t`` can name a class of the same id_short
apikey_sc_t: TypeAlias = apikey_sc
# alias so field ``psk_sc_t`` can name a class of the same id_short
psk_sc_t: TypeAlias = psk_sc
# alias so field ``digest_sc_t`` can name a class of the same id_short
digest_sc_t: TypeAlias = digest_sc
# alias so field ``bearer_sc_t`` can name a class of the same id_short
bearer_sc_t: TypeAlias = bearer_sc
# alias so field ``oauth2_sc_t`` can name a class of the same id_short
oauth2_sc_t: TypeAlias = oauth2_sc
# alias so field ``security_t`` can name a class of the same id_short
security_t: TypeAlias = security
# alias so field ``securityDefinitions_t`` can name a class of the same id_short
securityDefinitions_t: TypeAlias = securityDefinitions
# alias so field ``enum_t`` can name a class of the same id_short
enum_t: TypeAlias = enum
# alias so field ``items_t`` can name a class of the same id_short
items_t: TypeAlias = items
# alias so field ``htv_headers_t`` can name a class of the same id_short
htv_headers_t: TypeAlias = htv_headers
# alias so field ``forms_t`` can name a class of the same id_short
forms_t: TypeAlias = forms
# alias so field ``property_name_t`` can name a class of the same id_short
property_name_t: TypeAlias = property_name
# alias so field ``properties_t`` can name a class of the same id_short
properties_t: TypeAlias = properties
# alias so field ``actions_t`` can name a class of the same id_short
actions_t: TypeAlias = actions
# alias so field ``events_t`` can name a class of the same id_short
events_t: TypeAlias = events
# alias so field ``EndpointMetadata_t`` can name a class of the same id_short
EndpointMetadata_t: TypeAlias = EndpointMetadata
# alias so field ``ExternalDescriptor_t`` can name a class of the same id_short
ExternalDescriptor_t: TypeAlias = ExternalDescriptor
# alias so field ``opcua_channel_sc_t`` can name a class of the same id_short
opcua_channel_sc_t: TypeAlias = opcua_channel_sc
# alias so field ``opcua_authentication_sc_t`` can name a class of the same id_short
opcua_authentication_sc_t: TypeAlias = opcua_authentication_sc
# alias so field ``bacv_hasDataType_t`` can name a class of the same id_short
bacv_hasDataType_t: TypeAlias = bacv_hasDataType
# alias so field ``bacv_hasMember_t`` can name a class of the same id_short
bacv_hasMember_t: TypeAlias = bacv_hasMember
# alias so field ``bacv_hasNamedMember_t`` can name a class of the same id_short
bacv_hasNamedMember_t: TypeAlias = bacv_hasNamedMember
# alias so field ``bacv_hasValueMap_t`` can name a class of the same id_short
bacv_hasValueMap_t: TypeAlias = bacv_hasValueMap
# alias so field ``uriVariables_t`` can name a class of the same id_short
uriVariables_t: TypeAlias = uriVariables
# alias so field ``iolv_enumeratedValues_t`` can name a class of the same id_short
iolv_enumeratedValues_t: TypeAlias = iolv_enumeratedValues
# alias so field ``iolv_payloadMapping_t`` can name a class of the same id_short
iolv_payloadMapping_t: TypeAlias = iolv_payloadMapping
# alias so field ``canv_enumeratedValues_t`` can name a class of the same id_short
canv_enumeratedValues_t: TypeAlias = canv_enumeratedValues
# alias so field ``canv_payloadMapping_t`` can name a class of the same id_short
canv_payloadMapping_t: TypeAlias = canv_payloadMapping
# alias so field ``InterfaceTemplateForHTTP_t`` can name a class of the same id_short
InterfaceTemplateForHTTP_t: TypeAlias = InterfaceTemplateForHTTP
# alias so field ``InterfaceTemplateForMODBUS_t`` can name a class of the same id_short
InterfaceTemplateForMODBUS_t: TypeAlias = InterfaceTemplateForMODBUS
# alias so field ``InterfaceTemplateForMQTT_t`` can name a class of the same id_short
InterfaceTemplateForMQTT_t: TypeAlias = InterfaceTemplateForMQTT
# alias so field ``InterfaceTemplateForOPCUA_t`` can name a class of the same id_short
InterfaceTemplateForOPCUA_t: TypeAlias = InterfaceTemplateForOPCUA
# alias so field ``InterfaceTemplateForBacnet_t`` can name a class of the same id_short
InterfaceTemplateForBacnet_t: TypeAlias = InterfaceTemplateForBacnet
# alias so field ``InterfaceTemplateForIOLINK_OVER_PROFINET_REST_t`` can name a class of the same id_short
InterfaceTemplateForIOLINK_OVER_PROFINET_REST_t: TypeAlias = InterfaceTemplateForIOLINK_OVER_PROFINET_REST
# alias so field ``InterfaceTemplateForSNMP_t`` can name a class of the same id_short
InterfaceTemplateForSNMP_t: TypeAlias = InterfaceTemplateForSNMP
# alias so field ``InterfaceTemplateForCAN_t`` can name a class of the same id_short
InterfaceTemplateForCAN_t: TypeAlias = InterfaceTemplateForCAN
# ── Resolve forward references (Pydantic circular refs) ──
Title.model_rebuild()
Created.model_rebuild()
Modified.model_rebuild()
Support.model_rebuild()
Base.model_rebuild()
ContentType.model_rebuild()
securityItem.model_rebuild()
security.model_rebuild()
Scheme.model_rebuild()
nosec_sc.model_rebuild()
Proxy.model_rebuild()
auto_sc.model_rebuild()
Name.model_rebuild()
In.model_rebuild()
basic_sc.model_rebuild()
oneOf.model_rebuild()
allOf.model_rebuild()
combo_sc.model_rebuild()
apikey_sc.model_rebuild()
Identity.model_rebuild()
psk_sc.model_rebuild()
Qop.model_rebuild()
digest_sc.model_rebuild()
Authorization.model_rebuild()
Alg.model_rebuild()
Format.model_rebuild()
bearer_sc.model_rebuild()
Token.model_rebuild()
Refresh.model_rebuild()
scopesItem.model_rebuild()
scopes.model_rebuild()
Flow.model_rebuild()
oauth2_sc.model_rebuild()
securityDefinitions.model_rebuild()
ProtocolVersion.model_rebuild()
EndpointMetadata.model_rebuild()
Key.model_rebuild()
Type.model_rebuild()
Title_td.model_rebuild()
Observable.model_rebuild()
enumItem.model_rebuild()
enum.model_rebuild()
Const.model_rebuild()
Default.model_rebuild()
Unit.model_rebuild()
MinMax.model_rebuild()
LengthRange.model_rebuild()
ValueSemantics.model_rebuild()
items.model_rebuild()
ItemsRange.model_rebuild()
Key_asset_interfaces_description.model_rebuild()
property_name_json_schema.model_rebuild()
properties_json_schema.model_rebuild()
Href.model_rebuild()
ContentType_for_content_type.model_rebuild()
Subprotocol.model_rebuild()
HtvMethodName.model_rebuild()
HtvFieldName.model_rebuild()
HtvFieldValue.model_rebuild()
htv_headersItem.model_rebuild()
htv_headers.model_rebuild()
forms.model_rebuild()
forms_HTTP.model_rebuild()
property_name.model_rebuild()
property_name_HTTP.model_rebuild()
properties.model_rebuild()
properties_HTTP.model_rebuild()
actions.model_rebuild()
events.model_rebuild()
InteractionMetadata.model_rebuild()
InteractionMetadata_HTTP.model_rebuild()
FileName.model_rebuild()
ExternalDescriptor.model_rebuild()
InterfaceTemplateForHTTP.model_rebuild()
ModvMostSignificantByte.model_rebuild()
ModvMostSignificantWord.model_rebuild()
EndpointMetadata_MODBUS.model_rebuild()
ModvFunction.model_rebuild()
ModvEntity.model_rebuild()
ModvZeroBasedAddressing.model_rebuild()
ModvPollingTime.model_rebuild()
ModvTimeout.model_rebuild()
ModvType.model_rebuild()
forms_MODBUS.model_rebuild()
property_name_MODBUS.model_rebuild()
properties_MODBUS.model_rebuild()
InteractionMetadata_MODBUS.model_rebuild()
InterfaceTemplateForMODBUS.model_rebuild()
MqvRetain.model_rebuild()
MqvControlPacket.model_rebuild()
MqvQos.model_rebuild()
forms_MQTT.model_rebuild()
property_name_MQTT.model_rebuild()
properties_MQTT.model_rebuild()
InteractionMetadata_MQTT.model_rebuild()
InterfaceTemplateForMQTT.model_rebuild()
UavSecurityMode.model_rebuild()
UavSecurityPolicy.model_rebuild()
opcua_channel_sc.model_rebuild()
UavUserIdentityToken.model_rebuild()
UavIssueToken.model_rebuild()
opcua_authentication_sc.model_rebuild()
securityDefinitions_OPCUA.model_rebuild()
EndpointMetadata_OPCUA.model_rebuild()
UavBrowsePath.model_rebuild()
forms_OPCUA.model_rebuild()
property_name_OPCUA.model_rebuild()
properties_OPCUA.model_rebuild()
InteractionMetadata_OPCUA.model_rebuild()
InterfaceTemplateForOPCUA.model_rebuild()
property_name_json_schema_Bacnet.model_rebuild()
properties_json_schema_Bacnet.model_rebuild()
uriVariables.model_rebuild()
BacvUseService.model_rebuild()
BacvIsISO8601.model_rebuild()
BacvHasBinaryRepresentation.model_rebuild()
BacvHasFieldName.model_rebuild()
BacvHasContextTag.model_rebuild()
bacv_hasNamedMemberItem.model_rebuild()
bacv_hasNamedMember.model_rebuild()
BacvHasLogicalVal.model_rebuild()
BacvHasProtocolVal.model_rebuild()
bacv_hasValueMapItem.model_rebuild()
bacv_hasValueMap.model_rebuild()
bacv_hasMember.model_rebuild()
bacv_hasDataType.model_rebuild()
forms_Bacnet.model_rebuild()
property_name_Bacnet.model_rebuild()
properties_Bacnet.model_rebuild()
InteractionMetadata_Bacnet.model_rebuild()
InterfaceTemplateForBacnet.model_rebuild()
IolvMethod.model_rebuild()
IolvAccessRights.model_rebuild()
IolvType.model_rebuild()
IolvByteOffset.model_rebuild()
IolvByteLength.model_rebuild()
IolvBitOffset.model_rebuild()
IolvBitLength.model_rebuild()
IolvReferenceToCondition.model_rebuild()
IolvEncodedPayload.model_rebuild()
IolvDecodedPayload.model_rebuild()
iolv_enumeratedValuesItem.model_rebuild()
iolv_enumeratedValues.model_rebuild()
IolvReferenceToProperty.model_rebuild()
iolv_payloadMappingItem.model_rebuild()
iolv_payloadMapping.model_rebuild()
forms_IOLINK_OVER_PROFINET_REST.model_rebuild()
property_name_IOLINK_OVER_PROFINET_REST.model_rebuild()
properties_IOLINK_OVER_PROFINET_REST.model_rebuild()
InteractionMetadata_IOLINK_OVER_PROFINET_REST.model_rebuild()
InterfaceTemplateForIOLINK_OVER_PROFINET_REST.model_rebuild()
forms_SNMP.model_rebuild()
property_name_SNMP.model_rebuild()
properties_SNMP.model_rebuild()
InteractionMetadata_SNMP.model_rebuild()
InterfaceTemplateForSNMP.model_rebuild()
Href_has_target.model_rebuild()
CanvOffset.model_rebuild()
CanvLength.model_rebuild()
CanvValueOffset.model_rebuild()
CanvEncodedPayload.model_rebuild()
CanvDecodedPayload.model_rebuild()
canv_enumeratedValuesItem.model_rebuild()
canv_enumeratedValues.model_rebuild()
CanvReferenceToProperty.model_rebuild()
canv_payloadMappingItem.model_rebuild()
canv_payloadMapping.model_rebuild()
forms_CAN.model_rebuild()
property_name_CAN.model_rebuild()
properties_CAN.model_rebuild()
InteractionMetadata_CAN.model_rebuild()
InterfaceTemplateForCAN.model_rebuild()
AssetInterfacesDescription.model_rebuild()
