"""AAU filling line instance."""

from aas_model.constants import BASE_URL, CSSX
from aas_pydantic.submodel_templates.hierarchical_structures import EntryNode, Node
from aas_pydantic.submodel_templates.nameplate import ManufacturerName, ManufacturerProductDesignation
from aas_model.resource_template import ResourceNameplate
from aas_model.resource_template.resources import CompositeResource
from aas_model.submodel_templates.hierarchical_structures import ResourceHierarchicalStructures


def aau_filling_line() -> CompositeResource:
    identity = "aauFillingLineAAS"
    serial = "AAU-FL-2024-001"
    resource_id = f"{BASE_URL}/aas/{identity}"
    children = (
        "syntegonStopperingSystemAAS", "cytivaCappingSystemAAS",
        "imaDispensingSystemAAS", "imaLoadingSystemAAS",
        "optimaUnloadingSystemAAS", "omronCameraSystemAAS", "planarTableAAS",
    )
    return CompositeResource(
        id_short=identity,
        id=resource_id,
        asset_type=f"{CSSX}#FillingLine",
        specific_asset_ids={"serialNumber": serial},
        nameplate=ResourceNameplate(
            URIOfTheProduct=resource_id,
            ManufacturerName=ManufacturerName(value={"en": "Aalborg University"}),
            ManufacturerProductDesignation=ManufacturerProductDesignation(value={"en": "AAU Filling Line"}),
            ManufacturerProductType="AAU Filling Line",
            OrderCodeOfManufacturer=serial,
            SerialNumber=serial,
            YearOfConstruction="2024",
            CountryOfOrigin="DK",
        ),
        hierarchical_structures=ResourceHierarchicalStructures(
            ArcheType="OneDown",
            EntryNode=EntryNode(
                global_asset_id=resource_id,
                Node={child: Node(global_asset_id=f"{BASE_URL}/aas/{child}") for child in children},
            ),
        ),
    )
