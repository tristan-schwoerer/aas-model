"""AssetInterfacesDescription — generated from IDTA template."""

from __future__ import annotations

from typing import Any, ClassVar, List, Dict, Optional, TypeAlias
from aas_pydantic import (
    File, Property, Range, ReferenceElement, Submodel, SubmodelElement, SubmodelElementCollection, SubmodelElementList,
)

class Title(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/td#title"
    description: str = "Provides a human-readable title to give a human-readable context of the interface."
    value_type: str = "xs:string"

class Created(Property):
    semantic_id: str = "http://purl.org/dc/terms/created"
    description: str = "Provides information when the AID Submodel was created."
    value_type: str = "xs:dateTime"

class Modified(Property):
    semantic_id: str = "http://purl.org/dc/terms/modified"
    description: str = "Provides information when the AID Submodel was modified."
    value_type: str = "xs:dateTime"

class Support(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/td#supportContact"
    description: str = "Provides an address on how to contact the maintainer of AID Submodel as URI scheme."
    value_type: str = "xs:anyURI"

class Base(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/td#baseURI"
    description: str = "Defines asset connection entry point. The base pattern for HTTP is defined in Qalifier."
    value_type: str = "xs:anyURI"

class ContentType(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/hypermedia#forContentType"
    description: str = "Defines content type based on a media type (e.g., text/plain) and potential character decoding/encoding type (e.g., charset=utf-8) for the media type (see RFC2046) of the whole interface."
    value_type: str = "xs:string"

class security(SubmodelElementList):
    semantic_id: str = "https://www.w3.org/2019/wot/td#hasSecurityConfiguration"
    description: str = "Selects one or more of the security scheme(s) that can be applied at runtime from the collection of security schemes defines in securityDefinitions. "
    item_type: ClassVar = ReferenceElement
    value: List[ReferenceElement] = []

class Scheme(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/security#SecurityScheme"
    description: str = "Defines the security mechanism that used during access. the scheme for nosec_sc is nosec"
    value_type: str = "xs:string"

class nosec_sc(SubmodelElementCollection):
    semantic_id: str = "https://www.w3.org/2019/wot/security#NoSecurityScheme"
    description: str = "This SubmodelElements holds the information about security mechanism based on nosec security."
    scheme: Scheme

class Proxy(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/security#proxy"
    description: str = "Provides address information of the proxy server the security configuration provides access to."
    value_type: str = "xs:string"

class auto_sc(SubmodelElementCollection):
    semantic_id: str = "https://www.w3.org/2019/wot/security#AutoSecurityScheme"
    description: str = "This SubmodelElements holds the information about security mechanism based on auto security."
    scheme: Scheme
    proxy: Optional[Proxy] = None

class Name(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/security#name"
    description: str = "Name for query, header, cookie, or uri parameters"
    value_type: str = "xs:string"

class In(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/security#in"
    description: str = "Specifies the location of security authentication information. Proposed values are header, query, body, cookie or auto"
    value_type: str = "xs:string"

class basic_sc(SubmodelElementCollection):
    semantic_id: str = "https://www.w3.org/2019/wot/security#BasicSecurityScheme"
    description: str = "This SubmodelElements holds the information about security mechanism based on basic security."
    scheme: Scheme
    name: Optional[Name] = None
    in_: Optional[In] = None
    proxy: Optional[Proxy] = None

class oneOf(SubmodelElementList):
    semantic_id: str = "https://www.w3.org/2019/wot/security#oneOf"
    description: str = "Specifies alternative security schemes where at least one listed scheme can be used."
    value: List[Any] = []

class allOf(SubmodelElementList):
    semantic_id: str = "https://www.w3.org/2019/wot/security#allOf"
    description: str = "Specifies a combined security configuration where all listed schemes are applied together."
    value: List[Any] = []

class combo_sc(SubmodelElementCollection):
    semantic_id: str = "https://www.w3.org/2019/wot/security#ComboSecurityScheme"
    description: str = "This SubmodelElements holds the information about security mechanism based on combo security."
    scheme: Scheme
    oneOf: oneOf_t
    allOf: allOf_t
    proxy: Optional[Proxy] = None

class apikey_sc(SubmodelElementCollection):
    semantic_id: str = "https://www.w3.org/2019/wot/security#APIKeySecurityScheme"
    description: str = "This SubmodelElements holds the information about security mechanism based on apikey security."
    scheme: Scheme
    name: Optional[Name] = None
    in_: Optional[In] = None
    proxy: Optional[Proxy] = None

class Identity(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/security#identity"
    description: str = "Identifier providing information which can be used for selection or confirmation."
    value_type: str = "xs:string"

class psk_sc(SubmodelElementCollection):
    semantic_id: str = "https://www.w3.org/2019/wot/security#PSKSecurityScheme"
    description: str = "This SubmodelElements holds the information about security mechanism based on psk security."
    scheme: Scheme
    identity: Optional[Identity] = None
    proxy: Optional[Proxy] = None

class Qop(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/security#qop"
    description: str = "Defines Quality of protection. Values is one of auth or auth-int"
    value_type: str = "xs:string"

class digest_sc(SubmodelElementCollection):
    semantic_id: str = "https://www.w3.org/2019/wot/security#DigestSecurityScheme"
    description: str = "This SubmodelElements holds the information about security mechanism based on digest security."
    scheme: Scheme
    name: Optional[Name] = None
    in_: Optional[In] = None
    qop: Optional[Qop] = None
    proxy: Optional[Proxy] = None

class Authorization(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/security#authorization"
    description: str = "Specifies URI of the authorization server."
    value_type: str = "xs:string"

class Alg(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/security#alg"
    description: str = "Defines Encoding, encryption, or digest algorithm (e.g. ES256, ES512-256)."
    value_type: str = "xs:string"

class Format(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/security#format"
    description: str = "Specifies format of security authentication information. Options as value are jwt, cwt, jwe or jws"
    value_type: str = "xs:string"

class bearer_sc(SubmodelElementCollection):
    semantic_id: str = "https://www.w3.org/2019/wot/security#BearerSecurityScheme"
    description: str = "This SubmodelElements holds the information about security mechanism based on bearer security."
    scheme: Scheme
    name: Optional[Name] = None
    in_: Optional[In] = None
    authorization: Optional[Authorization] = None
    alg: Optional[Alg] = None
    format: Optional[Format] = None
    proxy: Optional[Proxy] = None

class Token(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/security#token"
    description: str = "Specifies URI of the token server."
    value_type: str = "xs:anyURI"

class Refresh(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/security#refresh"
    description: str = "Specifies URI of the refresh server."
    value_type: str = "xs:anyURI"

class scopes(SubmodelElementList):
    semantic_id: str = "https://www.w3.org/2019/wot/security#scopes"
    description: str = "Set of authorization scope identifiers (as Property) provided as an array. These are provided in tokens returned by an authorization server and associated with forms in order to identify what resources a client may access and how."
    value: List[Any] = []

class Flow(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/security#flow"
    description: str = "Defines authorization flow such as code or client."
    value_type: str = "xs:string"

class oauth2_sc(SubmodelElementCollection):
    semantic_id: str = "https://www.w3.org/2019/wot/security#OAuth2SecurityScheme"
    description: str = "This SubmodelElements holds the information about security mechanism based on oauth2 security."
    scheme: Scheme
    token: Optional[Token] = None
    refresh: Optional[Refresh] = None
    authorization: Optional[Authorization] = None
    scopes: Optional[scopes_t] = None
    flow: Optional[Flow] = None
    proxy: Optional[Proxy] = None

class securityDefinitions(SubmodelElementCollection):
    semantic_id: str = "https://www.w3.org/2019/wot/td#definesSecurityScheme"
    description: str = "Defines the security scheme according to W3C"
    nosec_sc: Optional[nosec_sc_t] = None
    auto_sc: Optional[auto_sc_t] = None
    basic_sc: Optional[basic_sc_t] = None
    combo_sc: Optional[combo_sc_t] = None
    apikey_sc: Optional[apikey_sc_t] = None
    psk_sc: Optional[psk_sc_t] = None
    digest_sc: Optional[digest_sc_t] = None
    bearer_sc: Optional[bearer_sc_t] = None
    oauth2_sc: Optional[oauth2_sc_t] = None

class EndpointMetadata(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/EndpointMetadata"
    description: str = "Provides the metadata of the asset\u2019s endpoint (base, content type that is used for interaction, etc)"
    base: Base
    contentType: ContentType
    security: security_t
    securityDefinitions: securityDefinitions_t

class Key(Property):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/key"
    description: str = "Optional element when the idShort of {property_name} cannot be used to reflect the desired property name due to the idShort restrictions (e.g., payload message uses \u201ctemperature-value\u201d as key term)."
    supplemental_semantic_ids: List[str] = ["https://www.w3.org/2019/wot/td#name"]
    value_type: str = "xs:string"

class Type(Property):
    semantic_id: str = "https://www.w3.org/1999/02/22-rdf-syntax-ns#type"
    description: str = "Indicates the abstract data type (one of object, array, string, number, integer, boolean, or null) of the described datapoint."
    value_type: str = "xs:string"

class Observable(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/td#isObservable"
    description: str = "An indicator that tells that the interaction datapoint can be observed with a, e.g., subscription mechanism by an underlying protocol."
    value_type: str = "xs:boolean"

class Const(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/json-schema#const"
    description: str = "Provides a constant value for defined datapoint. The data type should be identical to the one provided by the Property type."
    value_type: str = "xs:int"

class enum(SubmodelElementList):
    semantic_id: str = "https://www.w3.org/2019/wot/json-schema#enum"
    description: str = "Provides a list of restricted set of values that the asset can provide as datapoint value."
    value: List[Any] = []

class Default(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/json-schema#default"
    description: str = "Provides a default value that must of the type as the datapoint valueType. The data type should be identical to the one as provided by the Property type."
    value_type: str = "xs:string"

class Unit(Property):
    semantic_id: str = "https://schema.org/unitCode"
    description: str = "Provides information about the datapoint\u2019s unit."
    value_type: str = "xs:string"

class MinMax(Range):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/minMaxRange"
    description: str = "Specifies a minimum and/or maximum numeric value for the datapoint. This term is only used when type element is number or integer. When it is number, the range data type has to be float and when it is integer, the range data type has to be integer "
    supplemental_semantic_ids: List[str] = ["https://www.w3.org/2019/wot/json-schema#minimum", "https://www.w3.org/2019/wot/json-schema#maximum"]
    value_type: str = "xs:string"

class LengthRange(Range):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/lengthRange"
    description: str = "Specifies the minimum and maximum length of a string."
    supplemental_semantic_ids: List[str] = ["https://www.w3.org/2019/wot/json-schema#minLength", "https://www.w3.org/2019/wot/json-schema#maxLength"]
    value_type: str = "xs:string"

class ValueSemantics(ReferenceElement):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/valueSemantics"
    description: str = "Provides additional semantic information of the value that is read/subscribed at runtime. "

class items(SubmodelElementCollection):
    semantic_id: str = "https://www.w3.org/2019/wot/json-schema#items"
    description: str = "Used to define the data schema characteristics (as specified within Section 2.9) of an array payload."
    type: Optional[Type] = None
    title: Optional[Title] = None
    observable: Optional[Observable] = None
    const: Optional[Const] = None
    enum: Optional[enum_t] = None
    default: Optional[Default] = None
    unit: Optional[Unit] = None
    min_max: Optional[MinMax] = None
    lengthRange: Optional[LengthRange] = None
    valueSemantics: Optional[ValueSemantics] = None

class ItemsRange(Range):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/itemsRange"
    description: str = "Defines the minimum and maximum number of items that have to be in an array payload."
    supplemental_semantic_ids: List[str] = ["https://www.w3.org/2019/wot/json-schema#minItems", "https://www.w3.org/2019/wot/json-schema#maxItems"]
    value_type: str = "xs:string"

class property_name_json_schema(SubmodelElementCollection):
    semantic_id: str = "https://www.w3.org/2019/wot/json-schema#propertyName"
    description: str = "Defines a data element within an object-based datapoint.  "
    key: Optional[Key] = None
    type: Optional[Type] = None
    title: Optional[Title] = None
    observable: Optional[Observable] = None
    const: Optional[Const] = None
    enum: Optional[enum_t] = None
    default: Optional[Default] = None
    unit: Optional[Unit] = None
    min_max: Optional[MinMax] = None
    lengthRange: Optional[LengthRange] = None
    items: Optional[items_t] = None
    itemsRange: Optional[ItemsRange] = None
    properties: Optional[properties_json_schema] = None
    valueSemantics: Optional[ValueSemantics] = None

class properties_json_schema(SubmodelElementCollection):
    semantic_id: str = "https://www.w3.org/2019/wot/json-schema#properties"
    description: str = "Nested definitions of a datapoint. Only applicable if type=object."
    property_name: Dict[str, property_name_json_schema] = {}

class Href(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/hypermedia#hasTarget"
    description: str = "Indicates target IRI relative path or full IRI of asset\u2019s datapoint. The relative endpoint definition in href is always relative to base defined in EndpointMetadata. "
    value_type: str = "xs:string"

class Subprotocol(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/hypermedia#forSubProtocol"
    description: str = "Indicates the exact mechanism by which an interaction will be accomplished for a given protocol when there are multiple options."
    value_type: str = "xs:string"

class HtvMethodName(Property):
    semantic_id: str = "https://www.w3.org/2011/http#methodName"
    description: str = "Defines the action to be performed datapoint IRI"
    value_type: str = "xs:string"

class HtvFieldName(Property):
    semantic_id: str = "https://www.w3.org/2011/http#fieldName"
    description: str = "Defines message header name "
    value_type: str = "xs:string"

class HtvFieldValue(Property):
    semantic_id: str = "https://www.w3.org/2011/http#fieldValue"
    description: str = "Defines message header value"
    value_type: str = "xs:string"

class htv_header(SubmodelElementCollection):
    semantic_id: str = "https://www.w3.org/2011/http#headers"
    description: str = "Defines message header content "
    htv_fieldName: HtvFieldName
    htv_fieldValue: HtvFieldValue

class htv_headers(SubmodelElementList):
    semantic_id: str = "https://www.w3.org/2011/http#headers"
    description: str = "Defines additional information to be sent within the HTTP header message."
    item_type: ClassVar = htv_header
    value: List[htv_header] = []

class forms(SubmodelElementCollection):
    semantic_id: str = "https://www.w3.org/2019/wot/td#hasForm"
    description: str = "Contains information about datapoint resource location. Note, forms is only available at the top level {property_name}"
    href: Href
    contentType: Optional[ContentType] = None
    subprotocol: Optional[Subprotocol] = None
    security: security_t
    htv_methodName: Optional[HtvMethodName] = None
    htv_headers: Optional[htv_headers_t] = None

class property_name(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/PropertyDefinition"
    description: str = "Defines an interaction property that covers usually a datapoint definition that can be read or subscribed to.  "
    supplemental_semantic_ids: List[str] = ["https://www.w3.org/2019/wot/td#name"]
    key: Optional[Key] = None
    type: Optional[Type] = None
    title: Optional[Title] = None
    observable: Optional[Observable] = None
    const: Optional[Const] = None
    enum: Optional[enum_t] = None
    default: Optional[Default] = None
    unit: Optional[Unit] = None
    min_max: Optional[MinMax] = None
    lengthRange: Optional[LengthRange] = None
    items: Optional[items_t] = None
    itemsRange: Optional[ItemsRange] = None
    properties: Optional[properties_json_schema] = None
    valueSemantics: Optional[ValueSemantics] = None
    forms: forms_t

class properties(SubmodelElementCollection):
    semantic_id: str = "https://www.w3.org/2019/wot/td#PropertyAffordance"
    description: str = "Collection of asset\u2019s datapoint definitions"
    property_name: Dict[str, property_name_t] = {}

class actions(SubmodelElementCollection):
    semantic_id: str = "https://www.w3.org/2019/wot/td#ActionAffordance"
    description: str = "Collection of functions that can be done on asset as action SMC"
    pass

class events(SubmodelElementCollection):
    semantic_id: str = "https://www.w3.org/2019/wot/td#EventAffordance"
    description: str = "Collection of events triggerable by datapoint state as event SMC"
    pass

class InteractionMetadata(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/InteractionMetadata"
    description: str = "Provides the metadata of the actually interfaces such as which datapoints and functions are provided by the properties, actions, and events interaction abstraction. "
    supplemental_semantic_ids: List[str] = ["https://www.w3.org/2019/wot/td#InteractionAffordance"]
    properties: Optional[properties_t] = None
    actions: Optional[actions_t] = None
    events: Optional[events_t] = None

class FileName(File):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/externalDescriptorName"
    description: str = "File reference (local in AASX or outside) to an external descriptor description (e.g., Thing Description, GSDML, MTP, etc,).  "
    content_type: str = "application/json"

class ExternalDescriptor(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/ExternalDescriptor"
    description: str = "Provides a place for existing description files (e.g., Thing Description, GSDML, etc,)."
    fileName: FileName

class InterfaceTemplateForHTTP(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Interface"
    description: str = "Indicates entry point for HTTP interface."
    supplemental_semantic_ids: List[str] = ["http://www.w3.org/2011/http", "https://www.w3.org/2019/wot/td"]
    title: Title
    created: Optional[Created] = None
    modified: Optional[Modified] = None
    support: Optional[Support] = None
    EndpointMetadata: EndpointMetadata_t
    InteractionMetadata: InteractionMetadata_t
    ExternalDescriptor: Optional[ExternalDescriptor_t] = None

class ModvMostSignificantByte(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/modbus#hasMostSignificantByte"
    description: str = "This property is only applicable for Modbus-based communication. When modv_mostSignificantByte is true, it describes that the byte order of the data in the Modbus message is the most significant byte first (i.e., Big-Endian). When false, it describes the least significant byte first (i.e., Little-Endian)."
    value_type: str = "xs:string"

class ModvMostSignificantWord(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/modbus#hasMostSignificantWord"
    description: str = "This property is only applicable for Modbus-based communication. When modv_mostSignificantWord is true, it describes that the word order of the data in the Modbus message is the most significant word first (i.e., no word swapping). When false, it describes the least significant word first (i.e. word swapping)."
    value_type: str = "xs:string"

class ModvFunction(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/modbus#hasFunction"
    description: str = "Abstraction of the Modbus function code sent during a request. A function value can be either readCoil, readDeviceIdentification, readDiscreteInput, readHoldingRegisters, readInputRegisters, writeMultipleCoils, writeMultipleHoldingRegisters, writeSingleCoil, or  writeSingleHoldingRegister"
    value_type: str = "xs:string"

class ModvEntity(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/modbus#hasEntity"
    description: str = "A registry type to let the runtime automatically detect the right function code. An entity value can be Coil, DiscreteInput, HoldingRegister, or InputRegister"
    value_type: str = "xs:string"

class ModvZeroBasedAddressing(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/modbus#hasZeroBasedAddressingFlag"
    description: str = "Modbus implementations can differ in the way addressing works, as the first coil/register can be either referred to as True or False."
    value_type: str = "xs:string"

class ModvPollingTime(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/modbus#hasPollingTime"
    description: str = "Modbus TCP maximum polling rate. The Modbus specification does not define a maximum or minimum allowed polling rate, however specific implementations might introduce such limits. Defined as integer of milliseconds."
    value_type: str = "xs:string"

class ModvTimeout(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/modbus#hasTimeout"
    description: str = "Modbus response maximum waiting time. Defines how much time in milliseconds the runtime should wait until it receives a reply from the device."
    value_type: str = "xs:string"

class ModvType(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/modbus#hasPayloadDataType"
    description: str = "Defines the data type of the modbus asset payload. type in terms of possible sign, base type. the modv_type offers a set a types defined in XML schema defined in [12]. The set of supported types value are as follows:  xsd:float, xs:short ,xs:unsignedInt,,xs:string, xs:byte, xs:int, xs:boolean, xs:integer,xs:double, xs:hexbinary, xs:decimal, xs:long, xs:unsignedbyte, xs:unsignedshort, xs:unsignedint, xs:unsignedlong, "
    value_type: str = "xs:string"

class InterfaceTemplateForMODBUS(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Interface"
    description: str = "Indicates entry point for MODBUS interface."
    supplemental_semantic_ids: List[str] = ["http://www.w3.org/2011/modbus", "https://www.w3.org/2019/wot/td"]
    title: Title
    created: Optional[Created] = None
    modified: Optional[Modified] = None
    support: Optional[Support] = None
    EndpointMetadata: EndpointMetadata_t
    InteractionMetadata: InteractionMetadata_t
    ExternalDescriptor: Optional[ExternalDescriptor_t] = None

class MqvRetain(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/mqtt#hasRetainFlag"
    description: str = "It is an indicator that tells the broker to always retain last published payload. "
    value_type: str = "xs:string"

class MqvControlPacket(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/mqtt#ControlPacket"
    description: str = "Defines the method associated to the datapoint in relation to the broker"
    value_type: str = "xs:string"

class MqvQos(Property):
    semantic_id: str = "https://www.w3.org/2019/wot/mqtt#hasQoSFlag"
    description: str = "Defined the level of guarantee for message delivery between clients"
    value_type: str = "xs:string"

class InterfaceTemplateForMQTT(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Interface"
    description: str = "Indicates entry point for MQTT interface."
    supplemental_semantic_ids: List[str] = ["http://www.w3.org/2011/mqtt", "https://www.w3.org/2019/wot/td"]
    title: Title
    created: Optional[Created] = None
    modified: Optional[Modified] = None
    support: Optional[Support] = None
    EndpointMetadata: EndpointMetadata_t
    InteractionMetadata: InteractionMetadata_t
    ExternalDescriptor: Optional[ExternalDescriptor_t] = None

class UavSecurityMode(Property):
    semantic_id: str = "http://opcfoundation.org/UA/WoT-Binding/securityMode "
    description: str = "Provides information about the security modes supported by the OPC UA server endpoint(e.g None, Sign,SignAndEncrypt)"
    value_type: str = "xs:string"

class UavSecurityPolicy(Property):
    semantic_id: str = "http://opcfoundation.org/UA/WoT-Binding/securityPolicy"
    description: str = "Provides information about which policy options are available from the supported endpoints of the OPC UA server(e.g None, Basic256Sha256)"
    value_type: str = "xs:string"

class opcua_channel_sc(SubmodelElementCollection):
    semantic_id: str = "http://opcfoundation.org/UA/WoT-Binding/OPCUASecurityChannelScheme"
    description: str = "This SubmodelElements holds the information about security mechanism based on opcua_channel security."
    scheme: Scheme
    proxy: Optional[Proxy] = None
    uav_securityMode: UavSecurityMode
    uav_securityPolicy: UavSecurityPolicy

class UavUserIdentityToken(Property):
    semantic_id: str = "http://opcfoundation.org/UA/WoT-Binding/userIdentityToken"
    description: str = "Provides information about which policy options are available from the supported endpoints of the OPC UA server (e.g Anonymous)"
    value_type: str = "xs:string"

class UavIssueToken(ReferenceElement):
    semantic_id: str = "http://opcfoundation.org/UA/WoT-Binding/issueToken"
    description: str = "Provides reference to security scheme within SecurityDefinition SMC that holds information about the token to use (e.g OAuth2)."

class opcua_authentication_sc(SubmodelElementCollection):
    semantic_id: str = "http://opcfoundation.org/UA/WoT-Binding/OPCUASecurityAuthenticationScheme "
    description: str = "This SubmodelElements holds the information about security mechanism based on opcua_authentication security."
    scheme: Scheme
    proxy: Optional[Proxy] = None
    uav_userIdentityToken: UavUserIdentityToken
    uav_issueToken: Optional[UavIssueToken] = None

class UavBrowsePath(Property):
    semantic_id: str = "http://opcfoundation.org/UA/WoT-Binding/browsePath"
    description: str = "Defines an absolute path of a datapoint, starting from the root node of an OPC UA address space. This term is only used for OPC UA interface. "
    value_type: str = "xs:string"

class InterfaceTemplateForOPCUA(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Interface"
    description: str = "Indicates entry point for OPC UA interface."
    supplemental_semantic_ids: List[str] = ["http://opcfoundation.org/UA/WoT-Binding/", "https://www.w3.org/2019/wot/td"]
    title: Title
    created: Optional[Created] = None
    modified: Optional[Modified] = None
    support: Optional[Support] = None
    EndpointMetadata: EndpointMetadata_t
    InteractionMetadata: InteractionMetadata_t
    ExternalDescriptor: Optional[ExternalDescriptor_t] = None

class uriVariables(SubmodelElementCollection):
    semantic_id: str = "https://www.w3.org/2019/wot/td#hasUriTemplateSchema"
    description: str = "Defines URI template variables according to RFC6570 as a collection based on an interaction affordance data schema"
    property_name: Dict[str, property_name_json_schema] = {}

class BacvUseService(Property):
    semantic_id: str = "http://www.w3.org/2022/bacnet#usesService"
    description: str = "Defines the BACnet service to use on a datapoint operation."
    value_type: str = "xs:string"

class BacvIsISO8601(Property):
    semantic_id: str = "http://www.w3.org/2022/bacnet#isIso8601"
    description: str = "Defines if the data uses ISO8601 format"
    value_type: str = "xs:boolean"

class BacvHasBinaryRepresentation(Property):
    semantic_id: str = "http://www.w3.org/2022/bacnet#hasBinaryRepresentation"
    description: str = "Defines the payload\u2019s binary representation type. This term is used when the payload is an OctetString"
    value_type: str = "xs:boolean"

class BacvHasFieldName(Property):
    semantic_id: str = "http://www.w3.org/2022/bacnet#hasfieldName"
    description: str = "Defines name of a Named Member of a Sequence or Choice data type."
    value_type: str = "xs:string"

class BacvHasContextTag(Property):
    semantic_id: str = "http://www.w3.org/2022/bacnet#hasContextTag"
    description: str = "Defines Context Tag for a Named Member of a Sequence or Choice data type."
    value_type: str = "xs:boolean"

class properties_named_member(SubmodelElementCollection):
    semantic_id: str = "http://www.w3.org/2022/bacnet#NamedMember"
    description: str = "Defines the Named Member of a Sequence or Choice data type."
    bacv_hasFieldName: BacvHasFieldName
    bacv_hasContextTag: BacvHasContextTag
    bacv_hasDataType: Optional[bacv_hasDataType_t] = None

class bacv_hasNamedMember(SubmodelElementList):
    semantic_id: str = "http://www.w3.org/2022/bacnet#hasNamedMember"
    description: str = "Defines the Named Member of a Sequence or Choice data type."
    item_type: ClassVar = properties_named_member
    value: List[properties_named_member] = []

class BacvHasLogicalVal(Property):
    semantic_id: str = "http://www.w3.org/2022/bacnet#hasLogicalVal"
    description: str = "Defines the logical value for a ValueMap."
    value_type: str = "xs:string"

class BacvHasProtocolVal(Property):
    semantic_id: str = "http://www.w3.org/2022/bacnet#hasProtocolVal"
    description: str = "Defines the protocol value for a ValueMap."
    value_type: str = "xs:integer"

class properties_has_map_entry(SubmodelElementCollection):
    semantic_id: str = "http://www.w3.org/2022/bacnet#hasMapEntry"
    description: str = "Defines the value map for an Enumeration."
    bacv_hasLogicalVal: BacvHasLogicalVal
    bacv_hasProtocolVal: BacvHasProtocolVal

class bacv_hasValueMap(SubmodelElementList):
    semantic_id: str = "http://www.w3.org/2022/bacnet#hasValueMap"
    description: str = "Defines the value map of an enumeration."
    item_type: ClassVar = properties_has_map_entry
    value: List[properties_has_map_entry] = []

class bacv_hasMember(SubmodelElementCollection):
    semantic_id: str = "http://www.w3.org/2022/bacnet#hasMember"
    description: str = "Defines the member of a Sequence and List data type."
    bacv_isISO8601: Optional[BacvIsISO8601] = None
    bacv_hasBinaryRepresentation: Optional[BacvHasBinaryRepresentation] = None
    bacv_hasMember: Optional[bacv_hasMember_t] = None
    bacv_hasNamedMember: bacv_hasNamedMember_t
    bacv_hasValueMap: Optional[bacv_hasValueMap_t] = None

class bacv_hasDataType(SubmodelElementCollection):
    semantic_id: str = "http://www.w3.org/2022/bacnet#hasDataType"
    description: str = "Defines the type information of a BACnet payload. This SMC is used to abstract BACnet data model to human and machine readable model by still keeping its wire compatibility on the protocol."
    supplemental_semantic_ids: List[str] = ["http://www.w3.org/2022/bacnet#SequenceOf", "http://www.w3.org/2022/bacnet#Sequence", "http://www.w3.org/2022/bacnet#List", "http://www.w3.org/2022/bacnet#Choice", "http://www.w3.org/2022/bacnet#Date", "http://www.w3.org/2022/bacnet#Time", "http://www.w3.org/2022/bacnet#WeekNDay", "http://www.w3.org/2022/bacnet#Unsigned", "http://www.w3.org/2022/bacnet#Signed", "http://www.w3.org/2022/bacnet#Real", "http://www.w3.org/2022/bacnet#Double", "http://www.w3.org/2022/bacnet#Boolean", "http://www.w3.org/2022/bacnet#Enumerated", "http://www.w3.org/2022/bacnet#String", "http://www.w3.org/2022/bacnet#OctetString", "http://www.w3.org/2022/bacnet#BitString", "http://www.w3.org/2022/bacnet#Any", "http://www.w3.org/2022/bacnet#Null", "http://www.w3.org/2022/bacnet#ObjectIdentifier"]
    bacv_isISO8601: Optional[BacvIsISO8601] = None
    bacv_hasBinaryRepresentation: Optional[BacvHasBinaryRepresentation] = None
    bacv_hasMember: Optional[bacv_hasMember_t] = None
    bacv_hasNamedMember: bacv_hasNamedMember_t
    bacv_hasValueMap: Optional[bacv_hasValueMap_t] = None

class InterfaceTemplateForBacnet(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Interface"
    description: str = "Indicates entry point for BACnet interface."
    supplemental_semantic_ids: List[str] = ["http://www.w3.org/2022/bacnet", "https://www.w3.org/2019/wot/td"]
    title: Title
    created: Optional[Created] = None
    modified: Optional[Modified] = None
    support: Optional[Support] = None
    EndpointMetadata: EndpointMetadata_t
    InteractionMetadata: InteractionMetadata_t
    ExternalDescriptor: Optional[ExternalDescriptor_t] = None

class IolvMethod(Property):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/hasMethod"
    description: str = "Defines the type of operation to execute on a datapoint"
    value_type: str = "xs:string"

class IolvAccessRigths(Property):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/hasAccessRights"
    description: str = "Defines the type of operation that can be executed of a datapoint."
    value_type: str = "xs:string"

class IolvType(Property):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/hasPayloadDataType"
    description: str = "Specifies the data type contained in the request or response payload. "
    value_type: str = "xs:string"

class IolvByteOffset(Property):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/byteOffset"
    description: str = "For object type datapoints. Used to identify the starting point within a byte stream payload that represents a datapoint."
    value_type: str = "xs:string"

class IolvByteLength(Property):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/byteLength"
    description: str = "For object type datapoints. Used to identify the byte length within a byte stream payload that represents a datapoint."
    value_type: str = "xs:string"

class IolvBitOffset(Property):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/bitOffset"
    description: str = "For object type datapoints. Used to identify the starting point within a bit stream payload that represents a datapoint."
    value_type: str = "xs:integer"

class IolvBitLength(Property):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/bitLength"
    description: str = "For object type datapoints. Used to identify the bit length of a datapoint from the bit stream payload."
    value_type: str = "xs:string"

class IolvEncodedPayload(Property):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/encodedPayload"
    description: str = "Specifies the presentation of the payload Logical encoding.  "
    value_type: str = "xs:string"

class IolvDecodedPayload(Property):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/decodedPayload"
    description: str = "Specifies the human readable meaning of the payload Logical encoding.  "
    value_type: str = "xs:integer"

class iolv_enumeratedValue(SubmodelElementCollection):
    semantic_id: str = "http://www.w3.org/2022/wot/iolink#EnumeratedValue"
    description: str = "Defines the logical semantic to encoded payload provided a byte or byte stream."
    iolv_encodedPayload: IolvEncodedPayload
    iolv_decodedPayload: IolvDecodedPayload

class iolv_enumeratedValues(SubmodelElementList):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/hasEnumeratedValues"
    description: str = "Contains a list of enumerated values that define the logical semantic to encoded payload provided a byte or byte stream. "
    item_type: ClassVar = iolv_enumeratedValue
    value: List[iolv_enumeratedValue] = []

class IolvReferenceToProperty(ReferenceElement):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/referenceToProperty"
    description: str = "Defined the reference to a nested datapoint of an object type datapoint. "

class iolv_payloadMappingElement(SubmodelElementCollection):
    semantic_id: str = "http://www.w3.org/2022/wot/iolink#PayloadMapping"
    description: str = "Defines the payload mapping associated to a datapoint."
    iolv_referenceToProperty: Optional[IolvReferenceToProperty] = None
    iolv_type: Optional[IolvType] = None
    iolv_byteOffset: Optional[IolvByteOffset] = None
    iolv_byteLength: Optional[IolvByteLength] = None
    iolv_bitOffset: Optional[IolvBitOffset] = None
    iolv_bitLength: Optional[IolvBitLength] = None
    iolv_enumeratedValues: Optional[iolv_enumeratedValues_t] = None

class iolv_payloadMapping(SubmodelElementList):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link/hasPayloadMapping"
    description: str = "For object type datapoints. Used to provides logical mapping information of a complex payload from a IO lInk device."
    item_type: ClassVar = iolv_payloadMappingElement
    value: List[iolv_payloadMappingElement] = []

class InterfaceTemplateForIOLINK_OVER_PROFINET_REST(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/Interface"
    description: str = "Indicates entry point for IO Link over HTTP and PROFINET interface."
    supplemental_semantic_ids: List[str] = ["https://admin-shell.io/idta/AssetInterfacesDescription/1/1/IO-Link", "https://www.w3.org/2019/wot/td"]
    title: Title
    created: Optional[Created] = None
    modified: Optional[Modified] = None
    support: Optional[Support] = None
    EndpointMetadata: EndpointMetadata_t
    InteractionMetadata: InteractionMetadata_t
    ExternalDescriptor: Optional[ExternalDescriptor_t] = None

class AssetInterfacesDescription(Submodel):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesDescription/1/1/Submodel"
    description: str = "Definition of the Submodel Asset Interfaces Description identified by its semanticId. The Submodel idShort can be picked freely."
    VERSION: ClassVar[str] = "1"
    REVISION: ClassVar[str] = "1"
    InterfaceTemplateForHTTP: Dict[str, InterfaceTemplateForHTTP_t] = {}
    InterfaceTemplateForMODBUS: Dict[str, InterfaceTemplateForMODBUS_t] = {}
    InterfaceTemplateForMQTT: Dict[str, InterfaceTemplateForMQTT_t] = {}
    InterfaceTemplateForOPCUA: Dict[str, InterfaceTemplateForOPCUA_t] = {}
    InterfaceTemplateForBacnet: Dict[str, InterfaceTemplateForBacnet_t] = {}
    InterfaceTemplateForIOLINK_OVER_PROFINET_REST: Dict[str, InterfaceTemplateForIOLINK_OVER_PROFINET_REST_t] = {}

# ── Clash aliases: field name == element class name ──
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
# alias so field ``InteractionMetadata_t`` can name a class of the same id_short
InteractionMetadata_t: TypeAlias = InteractionMetadata
# alias so field ``ExternalDescriptor_t`` can name a class of the same id_short
ExternalDescriptor_t: TypeAlias = ExternalDescriptor
# alias so field ``bacv_hasDataType_t`` can name a class of the same id_short
bacv_hasDataType_t: TypeAlias = bacv_hasDataType
# alias so field ``bacv_hasMember_t`` can name a class of the same id_short
bacv_hasMember_t: TypeAlias = bacv_hasMember
# alias so field ``bacv_hasNamedMember_t`` can name a class of the same id_short
bacv_hasNamedMember_t: TypeAlias = bacv_hasNamedMember
# alias so field ``bacv_hasValueMap_t`` can name a class of the same id_short
bacv_hasValueMap_t: TypeAlias = bacv_hasValueMap
# alias so field ``iolv_enumeratedValues_t`` can name a class of the same id_short
iolv_enumeratedValues_t: TypeAlias = iolv_enumeratedValues
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

# ── Resolve forward references (Pydantic circular refs) ──
Title.model_rebuild()
Created.model_rebuild()
Modified.model_rebuild()
Support.model_rebuild()
Base.model_rebuild()
ContentType.model_rebuild()
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
scopes.model_rebuild()
Flow.model_rebuild()
oauth2_sc.model_rebuild()
securityDefinitions.model_rebuild()
EndpointMetadata.model_rebuild()
Key.model_rebuild()
Type.model_rebuild()
Observable.model_rebuild()
Const.model_rebuild()
enum.model_rebuild()
Default.model_rebuild()
Unit.model_rebuild()
MinMax.model_rebuild()
LengthRange.model_rebuild()
ValueSemantics.model_rebuild()
items.model_rebuild()
ItemsRange.model_rebuild()
property_name_json_schema.model_rebuild()
properties_json_schema.model_rebuild()
Href.model_rebuild()
Subprotocol.model_rebuild()
HtvMethodName.model_rebuild()
HtvFieldName.model_rebuild()
HtvFieldValue.model_rebuild()
htv_header.model_rebuild()
htv_headers.model_rebuild()
forms.model_rebuild()
property_name.model_rebuild()
properties.model_rebuild()
actions.model_rebuild()
events.model_rebuild()
InteractionMetadata.model_rebuild()
FileName.model_rebuild()
ExternalDescriptor.model_rebuild()
InterfaceTemplateForHTTP.model_rebuild()
ModvMostSignificantByte.model_rebuild()
ModvMostSignificantWord.model_rebuild()
ModvFunction.model_rebuild()
ModvEntity.model_rebuild()
ModvZeroBasedAddressing.model_rebuild()
ModvPollingTime.model_rebuild()
ModvTimeout.model_rebuild()
ModvType.model_rebuild()
InterfaceTemplateForMODBUS.model_rebuild()
MqvRetain.model_rebuild()
MqvControlPacket.model_rebuild()
MqvQos.model_rebuild()
InterfaceTemplateForMQTT.model_rebuild()
UavSecurityMode.model_rebuild()
UavSecurityPolicy.model_rebuild()
opcua_channel_sc.model_rebuild()
UavUserIdentityToken.model_rebuild()
UavIssueToken.model_rebuild()
opcua_authentication_sc.model_rebuild()
UavBrowsePath.model_rebuild()
InterfaceTemplateForOPCUA.model_rebuild()
uriVariables.model_rebuild()
BacvUseService.model_rebuild()
BacvIsISO8601.model_rebuild()
BacvHasBinaryRepresentation.model_rebuild()
BacvHasFieldName.model_rebuild()
BacvHasContextTag.model_rebuild()
properties_named_member.model_rebuild()
bacv_hasNamedMember.model_rebuild()
BacvHasLogicalVal.model_rebuild()
BacvHasProtocolVal.model_rebuild()
properties_has_map_entry.model_rebuild()
bacv_hasValueMap.model_rebuild()
bacv_hasMember.model_rebuild()
bacv_hasDataType.model_rebuild()
InterfaceTemplateForBacnet.model_rebuild()
IolvMethod.model_rebuild()
IolvAccessRigths.model_rebuild()
IolvType.model_rebuild()
IolvByteOffset.model_rebuild()
IolvByteLength.model_rebuild()
IolvBitOffset.model_rebuild()
IolvBitLength.model_rebuild()
IolvEncodedPayload.model_rebuild()
IolvDecodedPayload.model_rebuild()
iolv_enumeratedValue.model_rebuild()
iolv_enumeratedValues.model_rebuild()
IolvReferenceToProperty.model_rebuild()
iolv_payloadMappingElement.model_rebuild()
iolv_payloadMapping.model_rebuild()
InterfaceTemplateForIOLINK_OVER_PROFINET_REST.model_rebuild()
AssetInterfacesDescription.model_rebuild()
