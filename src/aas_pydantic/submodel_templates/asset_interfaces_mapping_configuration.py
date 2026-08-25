"""AssetInterfacesMappingConfiguration — generated from IDTA template."""

from __future__ import annotations

from typing import Any, ClassVar, List, Optional, TypeAlias
from aas_pydantic import (
    Blob, Property, ReferenceElement, Submodel, SubmodelElement, SubmodelElementCollection, SubmodelElementList,
)

class DefaultPollingInterval(Property):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/DefaultPollingInterval"
    description: str = "The DefaultPollingInterval defines the default time interval in seconds for fetching new data from the synchronous data sources defined in this MappingConfiguration. It must be greater than zero for synchronous protocols (e.g. HTTP) that need polling and is ignored for asynchronous protocols (e.g. MQTT)."
    value_type: str = "xs:double"

class Transformation(Blob):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Transformation"
    description: str = "The transformation allows for transforming incoming data before writing it to the sinks. The transformation must contain an \"aimc_main(sources)\" entrypoint function in Lua."
    content_type: str = "text/plain"

class Source_source(ReferenceElement):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Source/Source"
    description: str = "This holds a reference to the respective SubmodelElement used as data source. A data source can be any SubmodelElement including those defined in the InteractionMetadata of AID Submodels for fetching live-data from assets."

class PollingInterval(Property):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Source/PollingInterval"
    description: str = "The PollingInterval defines the time interval in seconds for fetching new data from the given synchronous data source. It must be greater than zero for synchronous protocols (e.g. HTTP) that need polling and is ignored for asynchronous protocols (e.g. MQTT). It overwrites the DefaultPollingInterval of the respective MappingConfiguration of this source."
    value_type: str = "xs:double"

class SourceId(Property):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Source/SourceId"
    description: str = "This is a unique and non-empty identifier that facilitates data access in the Lua transformation or establishes a relationship to a corresponding sink when no transformation is given. It must only be unique with respect to the Sources-list of the parent MappingConfiguration and not globally."
    value_type: str = "xs:string"

class Source(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Source"
    description: str = "A data source is defined by a Source reference, PollingInterval and SourceId."
    Source: Source_source
    PollingInterval: Optional[PollingInterval_t] = None
    SourceId: SourceId_t

class Sources(SubmodelElementList):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Sources"
    description: str = "This list includes all data sources that are used in this MappingConfiguration."
    item_type: ClassVar = Source
    value: List[Source] = []

class Sink_sink(ReferenceElement):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Sink/Sink"
    description: str = "This holds a reference to the respective SubmodelElement used as data sink for live-data."

class SinkId(Property):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Sink/SinkId"
    description: str = "This is a unique and non-empty identifier that facilitates data writing in the Lua transformation or establishes a relationship to a corresponding source when no transformation is given. It must only be unique with respect to the Sinks-list of the containing MappingConfiguration and not globally."
    value_type: str = "xs:string"

class Sink(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Sink"
    description: str = "A data sink is defined by a Sink reference and SinkId."
    Sink: Sink_sink
    SinkId: SinkId_t

class Sinks(SubmodelElementList):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Sinks"
    description: str = "This list includes all data sinks that are used in this MappingConfiguration."
    item_type: ClassVar = Sink
    value: List[Sink] = []

class MappingConfiguration(SubmodelElementCollection):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration"
    description: str = "A MappingConfiguration defines one logical unit of sources (inputs) and sinks (outputs) that are in relation to one another. The relation can be expressed via a transformation."
    DefaultPollingInterval: Optional[DefaultPollingInterval_t] = None
    Transformation: Optional[Transformation_t] = None
    Sources: Sources_t
    Sinks: Sinks_t

class MappingConfigurations(SubmodelElementList):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/1/0/MappingConfigurations"
    description: str = "List of MappingConfigurations that each map and transform data from their sources to their sinks."
    item_type: ClassVar = MappingConfiguration
    value: List[MappingConfiguration] = []

class AssetInterfacesMappingConfiguration(Submodel):
    semantic_id: str = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/Submodel"
    description: str = "The AIMC 2.0 is used to describe how data is mapped from asset to AAS or from AAS to AAS."
    VERSION: ClassVar[str] = "2"
    REVISION: ClassVar[str] = "0"
    MappingConfigurations: MappingConfigurations_t

# ── Clash aliases: field name == element class name ──
# alias so field ``PollingInterval_t`` can name a class of the same id_short
PollingInterval_t: TypeAlias = PollingInterval
# alias so field ``SourceId_t`` can name a class of the same id_short
SourceId_t: TypeAlias = SourceId
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
Source_source.model_rebuild()
PollingInterval.model_rebuild()
SourceId.model_rebuild()
Source.model_rebuild()
Sources.model_rebuild()
Sink_sink.model_rebuild()
SinkId.model_rebuild()
Sink.model_rebuild()
Sinks.model_rebuild()
MappingConfiguration.model_rebuild()
MappingConfigurations.model_rebuild()
AssetInterfacesMappingConfiguration.model_rebuild()
