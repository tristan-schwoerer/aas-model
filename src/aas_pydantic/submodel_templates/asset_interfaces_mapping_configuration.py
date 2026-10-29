"""AssetInterfacesMappingConfiguration - generated from IDTA template.
Source: Asset Interfaces Mapping Configuration/2/1/IDTA 02027_Template_AIMC.json
"""

from __future__ import annotations

from typing import ClassVar, Dict, List, Optional, TypeAlias
from aas_pydantic import (
    Blob, Property, ReferenceElement, Submodel, SubmodelElementCollection, SubmodelElementList,
)
from aas_pydantic.aas_model import AasIdString

class DefaultPollingInterval(Property):
    id_short: AasIdString = "DefaultPollingInterval"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/DefaultPollingInterval"
    description: str = "The DefaultPollingInterval defines the default time interval in seconds for fetching new data from the synchronous data sources defined in this MappingConfiguration. It must be greater than zero for synchronous protocols (e.g. HTTP) that need polling and is ignored for asynchronous protocols (e.g. MQTT)."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Default polling interval"}
    value_type: str = "xs:double"

class Transformation(Blob):
    id_short: AasIdString = "Transformation"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Transformation"
    description: str = "The transformation allows for transforming incoming data before writing it to the sinks. The transformation must contain an \"aimc_main(sources)\" entrypoint function in Lua."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Transformation"}
    content_type: str = "text/plain"

class Source(ReferenceElement):
    id_short: AasIdString = "Source"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Source/Source"
    description: str = "This holds a reference to the respective SubmodelElement used as data source. A data source can be any SubmodelElement including those defined in the InteractionMetadata of AID Submodels for fetching live-data from assets."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Source"}

class PollingInterval(Property):
    id_short: AasIdString = "PollingInterval"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Source/PollingInterval"
    description: str = "The PollingInterval defines the time interval in seconds for fetching new data from the given synchronous data source. It must be greater than zero for synchronous protocols (e.g. HTTP) that need polling and is ignored for asynchronous protocols (e.g. MQTT). It overwrites the DefaultPollingInterval of the respective MappingConfiguration of this source."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Polling interval"}
    value_type: str = "xs:double"

class SourceId(Property):
    id_short: AasIdString = "SourceId"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Source/SourceId"
    description: str = "This is a unique and non-empty identifier that facilitates data access in the Lua transformation or establishes a relationship to a corresponding sink when no transformation is given. It must only be unique with respect to the Sources-list of the parent MappingConfiguration and not globally."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Source ID"}
    value_type: str = "xs:string"

class SourcesItem(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Source"
    description: str = "A data source is defined by a Source reference, PollingInterval and SourceId."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Source"}
    Source: Source_t
    PollingInterval: Optional[PollingInterval_t] = None
    SourceId: SourceId_t

class Sources(SubmodelElementList):
    id_short: AasIdString = "Sources"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Sources"
    description: str = "This list includes all data sources that are used in this MappingConfiguration."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Sources"}
    type_value_list_element: str = "SubmodelElementCollection"
    semantic_id_list_element: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Source"
    order_relevant: bool = False
    ITEM_CARDINALITY: ClassVar[str] = 'OneToMany'
    item_type: ClassVar = SourcesItem
    value: List[SourcesItem] = []

class Sink(ReferenceElement):
    id_short: AasIdString = "Sink"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Sink/Sink"
    description: str = "This holds a reference to the respective SubmodelElement used as data sink for live-data."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Sink"}

class SinkId(Property):
    id_short: AasIdString = "SinkId"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Sink/SinkId"
    description: str = "This is a unique and non-empty identifier that facilitates data writing in the Lua transformation or establishes a relationship to a corresponding source when no transformation is given. It must only be unique with respect to the Sinks-list of the containing MappingConfiguration and not globally."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Sink ID"}
    value_type: str = "xs:string"

class SinksItem(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Sink"
    description: str = "A data sink is defined by a Sink reference and SinkId."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Sink"}
    Sink: Sink_t
    SinkId: SinkId_t

class Sinks(SubmodelElementList):
    id_short: AasIdString = "Sinks"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Sinks"
    description: str = "This list includes all data sinks that are used in this MappingConfiguration."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Sinks"}
    type_value_list_element: str = "SubmodelElementCollection"
    semantic_id_list_element: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Sink"
    ITEM_CARDINALITY: ClassVar[str] = 'OneToMany'
    item_type: ClassVar = SinksItem
    value: List[SinksItem] = []

class MappingConfigurationsItem(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration"
    description: str = "A MappingConfiguration defines one logical unit of sources (inputs) and sinks (outputs) that are in relation to one another. The relation can be expressed via a transformation."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Mapping configuration"}
    DefaultPollingInterval: Optional[DefaultPollingInterval_t] = None
    Transformation: Optional[Transformation_t] = None
    Sources: Sources_t
    Sinks: Sinks_t

class MappingConfigurations(SubmodelElementList):
    id_short: AasIdString = "MappingConfigurations"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/1/0/MappingConfigurations"
    description: str = "List of MappingConfigurations that each map and transform data from their sources to their sinks."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Mapping configurations"}
    type_value_list_element: str = "SubmodelElementCollection"
    semantic_id_list_element: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration"
    order_relevant: bool = False
    ITEM_CARDINALITY: ClassVar[str] = 'ZeroToMany'
    item_type: ClassVar = MappingConfigurationsItem
    value: List[MappingConfigurationsItem] = []

class AssetInterfacesMappingConfiguration(Submodel):
    id_short: AasIdString = "AssetInterfacesMappingConfiguration"
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/Submodel"
    description: str = "The AIMC 2.0 is used to describe how data is mapped from asset to AAS or from AAS to AAS."
    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = {"en": "Asset interfaces mapping configuration"}
    VERSION: ClassVar[str] = "2"
    REVISION: ClassVar[str] = "0"
    MappingConfigurations: MappingConfigurations_t

# alias so field ``Source_t`` can name a class of the same id_short
Source_t: TypeAlias = Source
# alias so field ``PollingInterval_t`` can name a class of the same id_short
PollingInterval_t: TypeAlias = PollingInterval
# alias so field ``SourceId_t`` can name a class of the same id_short
SourceId_t: TypeAlias = SourceId
# alias so field ``Sink_t`` can name a class of the same id_short
Sink_t: TypeAlias = Sink
# alias so field ``SinkId_t`` can name a class of the same id_short
SinkId_t: TypeAlias = SinkId
# alias so field ``DefaultPollingInterval_t`` can name a class of the same id_short
DefaultPollingInterval_t: TypeAlias = DefaultPollingInterval
# alias so field ``Transformation_t`` can name a class of the same id_short
Transformation_t: TypeAlias = Transformation
# alias so field ``Sources_t`` can name a class of the same id_short
Sources_t: TypeAlias = Sources
# alias so field ``Sinks_t`` can name a class of the same id_short
Sinks_t: TypeAlias = Sinks
# alias so field ``MappingConfigurations_t`` can name a class of the same id_short
MappingConfigurations_t: TypeAlias = MappingConfigurations
# ── Resolve forward references (Pydantic circular refs) ──
DefaultPollingInterval.model_rebuild()
Transformation.model_rebuild()
Source.model_rebuild()
PollingInterval.model_rebuild()
SourceId.model_rebuild()
SourcesItem.model_rebuild()
Sources.model_rebuild()
Sink.model_rebuild()
SinkId.model_rebuild()
SinksItem.model_rebuild()
Sinks.model_rebuild()
MappingConfigurationsItem.model_rebuild()
MappingConfigurations.model_rebuild()
AssetInterfacesMappingConfiguration.model_rebuild()
