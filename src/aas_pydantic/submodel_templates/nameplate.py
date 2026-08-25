"""Nameplate — generated from IDTA template."""

from __future__ import annotations

from typing import Any, ClassVar, List, Dict, Optional, TypeAlias
from aas_pydantic import (
    File, MultiLanguageProperty, Property, Submodel, SubmodelElement, SubmodelElementCollection, SubmodelElementList,
)

class URIOfTheProduct(Property):
    semantic_id: str = "0112/2///61987#ABN590#002"
    supplemental_semantic_ids: List[str] = ["0173-1#02-ABH173#003"]
    value_type: str = "xs:anyURI"

class ManufacturerName(MultiLanguageProperty):
    semantic_id: str = "0112/2///61987#ABA565#009"
    supplemental_semantic_ids: List[str] = ["0173-1#02-AAO677#004"]

class ManufacturerProductDesignation(MultiLanguageProperty):
    semantic_id: str = "0112/2///61987#ABA567#009"
    supplemental_semantic_ids: List[str] = ["0173-1#02-AAW338#003"]

class Street(MultiLanguageProperty):
    semantic_id: str = "0173-1#02-AAO128#002"

class Zipcode(MultiLanguageProperty):
    semantic_id: str = "0173-1#02-AAO129#002"

class CityTown(MultiLanguageProperty):
    semantic_id: str = "0173-1#02-AAO132#002"

class NationalCode(MultiLanguageProperty):
    semantic_id: str = "0173-1#02-AAO134#002"

class AddressOfAdditionalLink(Property):
    semantic_id: str = "0173-1#02-AAQ326#002"
    value_type: str = "xs:string"

class AddressInformation(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/AddressInformation"
    description: str = "Note: this set of information is defined by SMT drop-in \"Address Information\""
    supplemental_semantic_ids: List[str] = ["https://admin-shell.io/smt-dropin/smt-dropin-use/1/0", "0112/2///61360_7#AAS002#001", "0173-1#02-AAQ837#008/0173-1#01-ADR448#008"]
    Street: Street_t
    Zipcode: Zipcode_t
    CityTown: CityTown_t
    NationalCode: NationalCode_t
    AddressOfAdditionalLink: Optional[AddressOfAdditionalLink_t] = None

class ManufacturerProductRoot(MultiLanguageProperty):
    semantic_id: str = "0112/2///61360_7#AAS011#001"
    supplemental_semantic_ids: List[str] = ["0173-1#02-AAU732#003"]

class ManufacturerProductFamily(MultiLanguageProperty):
    semantic_id: str = "0112/2///61987#ABP464#002"
    supplemental_semantic_ids: List[str] = ["0173-1#02-AAU731#003"]

class ManufacturerProductType(Property):
    semantic_id: str = "0112/2///61987#ABA300#008"
    supplemental_semantic_ids: List[str] = ["0173-1#02-AAO057#004"]
    value_type: str = "xs:string"

class OrderCodeOfManufacturer(Property):
    semantic_id: str = "0112/2///61987#ABA950#008"
    supplemental_semantic_ids: List[str] = ["0173-1#02-AAO227#004"]
    value_type: str = "xs:string"

class ProductArticleNumberOfManufacturer(Property):
    semantic_id: str = "0112/2///61987#ABA581#007"
    supplemental_semantic_ids: List[str] = ["0173-1#02-AAO676#005"]
    value_type: str = "xs:string"

class SerialNumber(Property):
    semantic_id: str = "0112/2///61987#ABA951#009"
    supplemental_semantic_ids: List[str] = ["0173-1#02-AAM556#004"]
    value_type: str = "xs:string"

class YearOfConstruction(Property):
    semantic_id: str = "0112/2///61987#ABP000#002"
    supplemental_semantic_ids: List[str] = ["0173-1#02-AAP906#003"]
    value_type: str = "xs:string"

class DateOfManufacture(Property):
    semantic_id: str = "0112/2///61987#ABB757#007"
    supplemental_semantic_ids: List[str] = ["0173-1#02-AAR972#004"]
    value_type: str = "xs:date"

class HardwareVersion(Property):
    semantic_id: str = "0112/2///61987#ABA926#008"
    supplemental_semantic_ids: List[str] = ["0173-1#02-AAN270#004"]
    value_type: str = "xs:string"

class FirmwareVersion(Property):
    semantic_id: str = "0112/2///61987#ABA302#006"
    supplemental_semantic_ids: List[str] = ["0173-1#02-AAM985#004"]
    value_type: str = "xs:string"

class SoftwareVersion(Property):
    semantic_id: str = "0112/2///61987#ABA601#008"
    supplemental_semantic_ids: List[str] = ["0173-1#02-AAM737#004"]
    value_type: str = "xs:string"

class CountryOfOrigin(Property):
    semantic_id: str = "0112/2///61987#ABP462#001"
    description: str = "Note: Country codes defined accord. to DIN EN ISO 3166-1 alpha-2 codes"
    supplemental_semantic_ids: List[str] = ["0173-1#02-AAO259#007"]
    value_type: str = "xs:string"

class UniqueFacilityIdentifier(Property):
    semantic_id: str = "https://admin-shell.io/idta/nameplate/3/0/UniqueFacilityIdentifier"
    value_type: str = "xs:string"

class CompanyLogo(File):
    semantic_id: str = "0112/2///61987#ABP463#001"
    supplemental_semantic_ids: List[str] = ["0173-1#02-ABI776#002"]
    content_type: str = "image/png"

class MarkingName(Property):
    semantic_id: str = "0112/2///61987#ABA231#009"
    supplemental_semantic_ids: List[str] = ["0173-1#02-ABI190#003"]
    value_type: str = "xs:string"

class DesignationOfCertificateOrApproval(Property):
    semantic_id: str = "0112/2///61987#ABH783#003"
    description: str = "Note: Approval identifier, reference to the certificate number, to be entered without spaces "
    supplemental_semantic_ids: List[str] = ["0173-1#02-ABI975#002"]
    value_type: str = "xs:string"

class IssueDate(Property):
    semantic_id: str = "0112/2///61987#ABO097#001"
    description: str = "Note: format by lexical representation: CCYY-MM-DD Note: to be specified to the day "
    supplemental_semantic_ids: List[str] = ["0173-1#02-ABL774#001"]
    value_type: str = "xs:date"

class ExpiryDate(Property):
    semantic_id: str = "0112/2///61987#ABH830#002"
    description: str = "Note: format by lexical representation: CCYY-MM-DD Note: to be specified to the day "
    supplemental_semantic_ids: List[str] = ["0173-1#02-ABL775#001"]
    value_type: str = "xs:date"

class MarkingFile(File):
    semantic_id: str = "0112/2///61987#ABO100#002"
    supplemental_semantic_ids: List[str] = ["0173-1#02-ABI191#003"]
    content_type: str = "image/png"

class MarkingAdditionalText(Property):
    semantic_id: str = "0112/2///61987#ABB146#007"
    supplemental_semantic_ids: List[str] = ["0173-1#02-ABI192#003"]
    value_type: str = "xs:string"

class MarkingsItem(SubmodelElementCollection):
    semantic_id: str = "0112/2///61360_7#AAS009#001"
    description: str = "Note: CE marking is declared as mandatory according to the Blue Guide of the EU-Commission"
    supplemental_semantic_ids: List[str] = ["0173-1#02-ABI564#003/0173-1#01-AHF850#003"]
    MarkingName: MarkingName_t
    DesignationOfCertificateOrApproval: Optional[DesignationOfCertificateOrApproval_t] = None
    IssueDate: Optional[IssueDate_t] = None
    ExpiryDate: Optional[ExpiryDate_t] = None
    MarkingFile: MarkingFile_t
    MarkingAdditionalText: Dict[str, MarkingAdditionalText_t] = {}

class Markings(SubmodelElementList):
    semantic_id: str = "0112/2///61360_7#AAS006#001"
    description: str = "Note: CE marking is declared as mandatory according to EU Blue Guide"
    supplemental_semantic_ids: List[str] = ["0173-1#02-ABI563#003/0173-1#01-AHF849#003"]
    item_type: ClassVar = MarkingsItem
    value: List[MarkingsItem] = []

class ArbitraryProperty(Property):
    semantic_id: str = "https://admin-shell.io/SMT/General/ArbitraryProp"
    description: str = "Note: Every property can be used."
    value_type: str = "xs:string"

class ArbitraryMLP(MultiLanguageProperty):
    semantic_id: str = "https://admin-shell.io/SMT/General/ArbitraryMLP"
    description: str = "Note: Every multilanguage property can be used."

class ArbitraryFile(File):
    semantic_id: str = "https://admin-shell.io/SMT/General/ArbitraryFile"
    description: str = "Note: Every file can be used."
    content_type: str = "application/pdf"

class GuidelineForConformityDeclaration(Property):
    semantic_id: str = "0173-1#02-AAO856#002"
    value_type: str = "xs:string"

class GuidelineSpecificPropertiesItem(SubmodelElementCollection):
    semantic_id: str = "0173-1#01-AHD205#004"
    GuidelineForConformityDeclaration: GuidelineForConformityDeclaration_t
    ArbitraryProperty: Dict[str, ArbitraryProperty_t] = {}
    ArbitraryFile: Dict[str, ArbitraryFile_t] = {}
    ArbitraryMLP: Dict[str, ArbitraryMLP_t] = {}

class GuidelineSpecificProperties(SubmodelElementList):
    semantic_id: str = "0173-1#02-ABI219#003/0173-1#01-AHD205#004"
    item_type: ClassVar = GuidelineSpecificPropertiesItem
    value: List[GuidelineSpecificPropertiesItem] = []

class AssetSpecificProperties(SubmodelElementCollection):
    semantic_id: str = "0173-1#02-ABI218#003/0173-1#01-AGZ672#004"
    ArbitraryProperty: Dict[str, ArbitraryProperty_t] = {}
    ArbitraryMLP: Dict[str, ArbitraryMLP_t] = {}
    ArbitraryFile: Dict[str, ArbitraryFile_t] = {}
    GuidelineSpecificProperties: Optional[GuidelineSpecificProperties_t] = None

class Nameplate(Submodel):
    semantic_id: str = "https://admin-shell.io/idta/nameplate/3/0/Nameplate"
    description: str = "Contains the nameplate information attached to the product"
    VERSION: ClassVar[str] = "3"
    REVISION: ClassVar[str] = "0"
    URIOfTheProduct: URIOfTheProduct_t
    ManufacturerName: ManufacturerName_t
    ManufacturerProductDesignation: ManufacturerProductDesignation_t
    AddressInformation: AddressInformation_t
    ManufacturerProductRoot: Optional[ManufacturerProductRoot_t] = None
    ManufacturerProductFamily: Optional[ManufacturerProductFamily_t] = None
    ManufacturerProductType: Optional[ManufacturerProductType_t] = None
    OrderCodeOfManufacturer: OrderCodeOfManufacturer_t
    ProductArticleNumberOfManufacturer: Optional[ProductArticleNumberOfManufacturer_t] = None
    SerialNumber: Optional[SerialNumber_t] = None
    YearOfConstruction: Optional[YearOfConstruction_t] = None
    DateOfManufacture: Optional[DateOfManufacture_t] = None
    HardwareVersion: Optional[HardwareVersion_t] = None
    FirmwareVersion: Optional[FirmwareVersion_t] = None
    SoftwareVersion: Optional[SoftwareVersion_t] = None
    CountryOfOrigin: Optional[CountryOfOrigin_t] = None
    UniqueFacilityIdentifier: Optional[UniqueFacilityIdentifier_t] = None
    CompanyLogo: Optional[CompanyLogo_t] = None
    Markings: Optional[Markings_t] = None
    AssetSpecificProperties: Optional[AssetSpecificProperties_t] = None

# ── Clash aliases: field name == element class name ──
# alias so field ``Street_t`` can name a class of the same id_short
Street_t: TypeAlias = Street
# alias so field ``Zipcode_t`` can name a class of the same id_short
Zipcode_t: TypeAlias = Zipcode
# alias so field ``CityTown_t`` can name a class of the same id_short
CityTown_t: TypeAlias = CityTown
# alias so field ``NationalCode_t`` can name a class of the same id_short
NationalCode_t: TypeAlias = NationalCode
# alias so field ``AddressOfAdditionalLink_t`` can name a class of the same id_short
AddressOfAdditionalLink_t: TypeAlias = AddressOfAdditionalLink
# alias so field ``MarkingName_t`` can name a class of the same id_short
MarkingName_t: TypeAlias = MarkingName
# alias so field ``DesignationOfCertificateOrApproval_t`` can name a class of the same id_short
DesignationOfCertificateOrApproval_t: TypeAlias = DesignationOfCertificateOrApproval
# alias so field ``IssueDate_t`` can name a class of the same id_short
IssueDate_t: TypeAlias = IssueDate
# alias so field ``ExpiryDate_t`` can name a class of the same id_short
ExpiryDate_t: TypeAlias = ExpiryDate
# alias so field ``MarkingFile_t`` can name a class of the same id_short
MarkingFile_t: TypeAlias = MarkingFile
# alias so field ``MarkingAdditionalText_t`` can name a class of the same id_short
MarkingAdditionalText_t: TypeAlias = MarkingAdditionalText
# alias so field ``GuidelineForConformityDeclaration_t`` can name a class of the same id_short
GuidelineForConformityDeclaration_t: TypeAlias = GuidelineForConformityDeclaration
# alias so field ``ArbitraryProperty_t`` can name a class of the same id_short
ArbitraryProperty_t: TypeAlias = ArbitraryProperty
# alias so field ``ArbitraryFile_t`` can name a class of the same id_short
ArbitraryFile_t: TypeAlias = ArbitraryFile
# alias so field ``ArbitraryMLP_t`` can name a class of the same id_short
ArbitraryMLP_t: TypeAlias = ArbitraryMLP
# alias so field ``GuidelineSpecificProperties_t`` can name a class of the same id_short
GuidelineSpecificProperties_t: TypeAlias = GuidelineSpecificProperties
# alias so field ``URIOfTheProduct_t`` can name a class of the same id_short
URIOfTheProduct_t: TypeAlias = URIOfTheProduct
# alias so field ``ManufacturerName_t`` can name a class of the same id_short
ManufacturerName_t: TypeAlias = ManufacturerName
# alias so field ``ManufacturerProductDesignation_t`` can name a class of the same id_short
ManufacturerProductDesignation_t: TypeAlias = ManufacturerProductDesignation
# alias so field ``AddressInformation_t`` can name a class of the same id_short
AddressInformation_t: TypeAlias = AddressInformation
# alias so field ``ManufacturerProductRoot_t`` can name a class of the same id_short
ManufacturerProductRoot_t: TypeAlias = ManufacturerProductRoot
# alias so field ``ManufacturerProductFamily_t`` can name a class of the same id_short
ManufacturerProductFamily_t: TypeAlias = ManufacturerProductFamily
# alias so field ``ManufacturerProductType_t`` can name a class of the same id_short
ManufacturerProductType_t: TypeAlias = ManufacturerProductType
# alias so field ``OrderCodeOfManufacturer_t`` can name a class of the same id_short
OrderCodeOfManufacturer_t: TypeAlias = OrderCodeOfManufacturer
# alias so field ``ProductArticleNumberOfManufacturer_t`` can name a class of the same id_short
ProductArticleNumberOfManufacturer_t: TypeAlias = ProductArticleNumberOfManufacturer
# alias so field ``SerialNumber_t`` can name a class of the same id_short
SerialNumber_t: TypeAlias = SerialNumber
# alias so field ``YearOfConstruction_t`` can name a class of the same id_short
YearOfConstruction_t: TypeAlias = YearOfConstruction
# alias so field ``DateOfManufacture_t`` can name a class of the same id_short
DateOfManufacture_t: TypeAlias = DateOfManufacture
# alias so field ``HardwareVersion_t`` can name a class of the same id_short
HardwareVersion_t: TypeAlias = HardwareVersion
# alias so field ``FirmwareVersion_t`` can name a class of the same id_short
FirmwareVersion_t: TypeAlias = FirmwareVersion
# alias so field ``SoftwareVersion_t`` can name a class of the same id_short
SoftwareVersion_t: TypeAlias = SoftwareVersion
# alias so field ``CountryOfOrigin_t`` can name a class of the same id_short
CountryOfOrigin_t: TypeAlias = CountryOfOrigin
# alias so field ``UniqueFacilityIdentifier_t`` can name a class of the same id_short
UniqueFacilityIdentifier_t: TypeAlias = UniqueFacilityIdentifier
# alias so field ``CompanyLogo_t`` can name a class of the same id_short
CompanyLogo_t: TypeAlias = CompanyLogo
# alias so field ``Markings_t`` can name a class of the same id_short
Markings_t: TypeAlias = Markings
# alias so field ``AssetSpecificProperties_t`` can name a class of the same id_short
AssetSpecificProperties_t: TypeAlias = AssetSpecificProperties

# ── Resolve forward references (Pydantic circular refs) ──
URIOfTheProduct.model_rebuild()
ManufacturerName.model_rebuild()
ManufacturerProductDesignation.model_rebuild()
Street.model_rebuild()
Zipcode.model_rebuild()
CityTown.model_rebuild()
NationalCode.model_rebuild()
AddressOfAdditionalLink.model_rebuild()
AddressInformation.model_rebuild()
ManufacturerProductRoot.model_rebuild()
ManufacturerProductFamily.model_rebuild()
ManufacturerProductType.model_rebuild()
OrderCodeOfManufacturer.model_rebuild()
ProductArticleNumberOfManufacturer.model_rebuild()
SerialNumber.model_rebuild()
YearOfConstruction.model_rebuild()
DateOfManufacture.model_rebuild()
HardwareVersion.model_rebuild()
FirmwareVersion.model_rebuild()
SoftwareVersion.model_rebuild()
CountryOfOrigin.model_rebuild()
UniqueFacilityIdentifier.model_rebuild()
CompanyLogo.model_rebuild()
MarkingName.model_rebuild()
DesignationOfCertificateOrApproval.model_rebuild()
IssueDate.model_rebuild()
ExpiryDate.model_rebuild()
MarkingFile.model_rebuild()
MarkingAdditionalText.model_rebuild()
MarkingsItem.model_rebuild()
Markings.model_rebuild()
ArbitraryProperty.model_rebuild()
ArbitraryMLP.model_rebuild()
ArbitraryFile.model_rebuild()
GuidelineForConformityDeclaration.model_rebuild()
GuidelineSpecificPropertiesItem.model_rebuild()
GuidelineSpecificProperties.model_rebuild()
AssetSpecificProperties.model_rebuild()
Nameplate.model_rebuild()
