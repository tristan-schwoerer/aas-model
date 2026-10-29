"""TimeSeries - generated from IDTA template.
Source: Time Series Data/1/1/2/IDTA 02008-1-1-2_Template_TimeSeriesData_forAASMetamodelV3.1.json
"""

from __future__ import annotations

from typing import ClassVar, Dict, Optional, TypeAlias
from aas_pydantic import (
    Blob, File, MultiLanguageProperty, Property, Submodel, SubmodelElementCollection,
)
from pydantic import Field as _Field
from aas_pydantic.aas_model import AasIdString

class Name(MultiLanguageProperty):
    id_short: AasIdString = "Name"
    semantic_id: str = "https://admin-shell.io/idta/TimeSeries/Metadata/Name/1/1"

class Description(MultiLanguageProperty):
    id_short: AasIdString = "Description"
    semantic_id: str = "https://admin-shell.io/idta/TimeSeries/Metadata/Description/1/1"

class Time(Property):
    id_short: AasIdString = "Time"
    semantic_id: str = "https://admin-shell.io/idta/TimeSeries/RelativePointInTime/1/1"
    value_type: str = "xs:long"

class SampleAccelerationX(Property):
    id_short: AasIdString = "sampleAccelerationX"
    semantic_id: str = "https://sample.com/AccelerationX/1/1"
    value_type: str = "xs:long"

class SampleAccelerationY(Property):
    id_short: AasIdString = "sampleAccelerationY"
    semantic_id: str = "https://sample.com/AccelerationY/1/1"
    value_type: str = "xs:long"

class SampleAccelerationZ(Property):
    id_short: AasIdString = "sampleAccelerationZ"
    semantic_id: str = "https://sample.com/AccelerationZ/1/1"
    value_type: str = "xs:long"

class Record(SubmodelElementCollection):
    id_short: AasIdString = "Record"
    semantic_id: str = "https://admin-shell.io/idta/TimeSeries/Record/1/1"
    Time: Dict[str, Time_t] = _Field(default_factory=dict, json_schema_extra={"idta_min_cardinality": 1, "idta_allowed_id_short": "Time(\\d{2,3})?"})
    sampleAccelerationX: Optional[SampleAccelerationX] = None
    sampleAccelerationY: Optional[SampleAccelerationY] = None
    sampleAccelerationZ: Optional[SampleAccelerationZ] = None

class Metadata(SubmodelElementCollection):
    id_short: AasIdString = "Metadata"
    semantic_id: str = "https://admin-shell.io/idta/TimeSeries/Metadata/1/1"
    Name: Name_t
    Description: Optional[Description_t] = None
    Record: Record_t

class Name_segment(MultiLanguageProperty):
    id_short: AasIdString = "Name"
    semantic_id: str = "https://admin-shell.io/idta/TimeSeries/Segment/Name/1/1"

class Description_segment(MultiLanguageProperty):
    id_short: AasIdString = "Description"
    semantic_id: str = "https://admin-shell.io/idta/TimeSeries/Segment/Description/1/1"

class RecordCount(Property):
    id_short: AasIdString = "RecordCount"
    semantic_id: str = "https://admin-shell.io/idta/TimeSeries/Segment/RecordCount/1/1"
    value_type: str = "xs:long"

class StartTime(Property):
    id_short: AasIdString = "StartTime"
    semantic_id: str = "https://admin-shell.io/idta/TimeSeries/Segment/StartTime/1/1"
    value_type: str = "xs:string"

class EndTime(Property):
    id_short: AasIdString = "EndTime"
    semantic_id: str = "https://admin-shell.io/idta/TimeSeries/Segment/EndTime/1/1"
    value_type: str = "xs:string"

class Duration(Property):
    id_short: AasIdString = "Duration"
    semantic_id: str = "https://admin-shell.io/idta/TimeSeries/Segment/Duration/1/1"
    value_type: str = "xs:string"

class SamplingInterval(Property):
    id_short: AasIdString = "SamplingInterval"
    semantic_id: str = "https://admin-shell.io/idta/TimeSeries/Segment/SamplingInterval/1/1"
    value_type: str = "xs:long"

class SamplingRate(Property):
    id_short: AasIdString = "SamplingRate"
    semantic_id: str = "https://admin-shell.io/idta/TimeSeries/Segment/SamplingRate/1/1"
    value_type: str = "xs:long"

class State(Property):
    id_short: AasIdString = "State"
    semantic_id: str = "https://admin-shell.io/idta/TimeSeries/Segment/State/1/1"
    value_type: str = "xs:string"

class LastUpdate(Property):
    id_short: AasIdString = "LastUpdate"
    semantic_id: str = "https://admin-shell.io/idta/TimeSeries/Segment/LastUpdate/1/1"
    value_type: str = "xs:string"

class File_time_series(File):
    id_short: AasIdString = "File"
    semantic_id: str = "https://admin-shell.io/idta/TimeSeries/File/1/1"
    content_type: str = "application/json"

class Blob_time_series(Blob):
    id_short: AasIdString = "Blob"
    semantic_id: str = "https://admin-shell.io/idta/TimeSeries/Blob/1/1"
    content_type: str = "application/json"

class ExternalSegment(SubmodelElementCollection):
    id_short: AasIdString = "ExternalSegment"
    semantic_id: str = "https://admin-shell.io/idta/TimeSeries/Segments/ExternalSegment/1/1"
    Name: Optional[Name_segment] = None
    Description: Optional[Description_segment] = None
    RecordCount: Optional[RecordCount_t] = None
    StartTime: Optional[StartTime_t] = None
    EndTime: Optional[EndTime_t] = None
    Duration: Optional[Duration_t] = None
    SamplingInterval: Optional[SamplingInterval_t] = None
    SamplingRate: Optional[SamplingRate_t] = None
    State: Optional[State_t] = None
    LastUpdate: Optional[LastUpdate_t] = None
    File: Optional[File_time_series] = None
    Blob: Optional[Blob_time_series] = None

class Endpoint(Property):
    id_short: AasIdString = "Endpoint"
    semantic_id: str = "https://admin-shell.io/idta/TimeSeries/Endpoint/1/1"
    value_type: str = "xs:string"

class Query(Property):
    id_short: AasIdString = "Query"
    semantic_id: str = "https://admin-shell.io/idta/TimeSeries/Query/1/1"
    value_type: str = "xs:string"

class LinkedSegment(SubmodelElementCollection):
    id_short: AasIdString = "LinkedSegment"
    semantic_id: str = "https://admin-shell.io/idta/TimeSeries/Segments/LinkedSegment/1/1"
    Name: Optional[Name_segment] = None
    Description: Optional[Description_segment] = None
    RecordCount: Optional[RecordCount_t] = None
    StartTime: Optional[StartTime_t] = None
    EndTime: Optional[EndTime_t] = None
    Duration: Optional[Duration_t] = None
    SamplingInterval: Optional[SamplingInterval_t] = None
    SamplingRate: Optional[SamplingRate_t] = None
    State: Optional[State_t] = None
    LastUpdate: Optional[LastUpdate_t] = None
    Endpoint: Endpoint_t
    Query: Query_t

class Records(SubmodelElementCollection):
    id_short: AasIdString = "Records"
    semantic_id: str = "https://admin-shell.io/idta/TimeSeries/Records/1/1"
    Record: Dict[str, Record_t] = {}

class InternalSegment(SubmodelElementCollection):
    id_short: AasIdString = "InternalSegment"
    semantic_id: str = "https://admin-shell.io/idta/TimeSeries/Segments/InternalSegment/1/1"
    Name: Optional[Name_segment] = None
    Description: Optional[Description_segment] = None
    RecordCount: Optional[RecordCount_t] = None
    StartTime: Optional[StartTime_t] = None
    EndTime: Optional[EndTime_t] = None
    Duration: Optional[Duration_t] = None
    SamplingInterval: Optional[SamplingInterval_t] = None
    SamplingRate: Optional[SamplingRate_t] = None
    State: Optional[State_t] = None
    LastUpdate: Optional[LastUpdate_t] = None
    Records: Records_t

class Segments(SubmodelElementCollection):
    id_short: AasIdString = "Segments"
    semantic_id: str = "https://admin-shell.io/idta/TimeSeries/Segments/1/1"
    ExternalSegment: Dict[str, ExternalSegment_t] = {}
    LinkedSegment: Dict[str, LinkedSegment_t] = {}
    InternalSegment: Dict[str, InternalSegment_t] = {}

class TimeSeries(Submodel):
    id_short: AasIdString = "TimeSeries"
    semantic_id: str = "https://admin-shell.io/idta/TimeSeries/1/1"
    description: str = "Contains time series data and references to time series data to discover and semantically describe them along the asset lifecycle."
    VERSION: ClassVar[str] = "1"
    REVISION: ClassVar[str] = "1"
    Metadata: Metadata_t
    Segments: Segments_t

# alias so field ``Time_t`` can name a class of the same id_short
Time_t: TypeAlias = Time
# alias so field ``Name_t`` can name a class of the same id_short
Name_t: TypeAlias = Name
# alias so field ``Description_t`` can name a class of the same id_short
Description_t: TypeAlias = Description
# alias so field ``Record_t`` can name a class of the same id_short
Record_t: TypeAlias = Record
# alias so field ``RecordCount_t`` can name a class of the same id_short
RecordCount_t: TypeAlias = RecordCount
# alias so field ``StartTime_t`` can name a class of the same id_short
StartTime_t: TypeAlias = StartTime
# alias so field ``EndTime_t`` can name a class of the same id_short
EndTime_t: TypeAlias = EndTime
# alias so field ``Duration_t`` can name a class of the same id_short
Duration_t: TypeAlias = Duration
# alias so field ``SamplingInterval_t`` can name a class of the same id_short
SamplingInterval_t: TypeAlias = SamplingInterval
# alias so field ``SamplingRate_t`` can name a class of the same id_short
SamplingRate_t: TypeAlias = SamplingRate
# alias so field ``State_t`` can name a class of the same id_short
State_t: TypeAlias = State
# alias so field ``LastUpdate_t`` can name a class of the same id_short
LastUpdate_t: TypeAlias = LastUpdate
# alias so field ``Endpoint_t`` can name a class of the same id_short
Endpoint_t: TypeAlias = Endpoint
# alias so field ``Query_t`` can name a class of the same id_short
Query_t: TypeAlias = Query
# alias so field ``Records_t`` can name a class of the same id_short
Records_t: TypeAlias = Records
# alias so field ``ExternalSegment_t`` can name a class of the same id_short
ExternalSegment_t: TypeAlias = ExternalSegment
# alias so field ``LinkedSegment_t`` can name a class of the same id_short
LinkedSegment_t: TypeAlias = LinkedSegment
# alias so field ``InternalSegment_t`` can name a class of the same id_short
InternalSegment_t: TypeAlias = InternalSegment
# alias so field ``Metadata_t`` can name a class of the same id_short
Metadata_t: TypeAlias = Metadata
# alias so field ``Segments_t`` can name a class of the same id_short
Segments_t: TypeAlias = Segments
# ── Resolve forward references (Pydantic circular refs) ──
Name.model_rebuild()
Description.model_rebuild()
Time.model_rebuild()
SampleAccelerationX.model_rebuild()
SampleAccelerationY.model_rebuild()
SampleAccelerationZ.model_rebuild()
Record.model_rebuild()
Metadata.model_rebuild()
Name_segment.model_rebuild()
Description_segment.model_rebuild()
RecordCount.model_rebuild()
StartTime.model_rebuild()
EndTime.model_rebuild()
Duration.model_rebuild()
SamplingInterval.model_rebuild()
SamplingRate.model_rebuild()
State.model_rebuild()
LastUpdate.model_rebuild()
File_time_series.model_rebuild()
Blob_time_series.model_rebuild()
ExternalSegment.model_rebuild()
Endpoint.model_rebuild()
Query.model_rebuild()
LinkedSegment.model_rebuild()
Records.model_rebuild()
InternalSegment.model_rebuild()
Segments.model_rebuild()
TimeSeries.model_rebuild()
