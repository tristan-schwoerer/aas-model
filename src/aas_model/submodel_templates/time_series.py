"""TimeSeries SMC — the DMP profile of IDTA 02008 (Time Series Data 1.1).

Layering: the generated IDTA template
(``aas_pydantic.submodel_templates.time_series``) stays PRISTINE. This module
shapes one time series as an SMC inside ``Variables`` instead of a submodel of
its own: the SMC carries this project's id with the IDTA TimeSeries id as a
supplemental id, and everything inside it keeps the IDTA ids, so splitting it
out into a TimeSeries submodel stays mechanical.

Structure::

    <series>                     TimeSeriesCollection (TS_COLLECTION + IDTA TimeSeries)
    ├── Metadata
    │   ├── Name
    │   └── Record               the row schema: one row = one sample
    │       ├── Time             UtcTime (xs:dateTime)
    │       ├── <field>          RecordField: one InfluxDB field, named by its idShortPath
    │       ├── <range>          RecordRange: two fields, <path>.min and <path>.max
    │       ├── <file>           RecordFile: one string field, the file's path or URL
    │       ├── <text>           RecordText: one string field per declared language, <path>.en
    │       ├── <group>          RecordGroup of further fields (Position.X)
    │       └── <reference>      RecordReference to an AAS element, resolved as if inline
    └── Segments
        └── LinkedSegment[]
            ├── Endpoint         InfluxDB 2 query URL (IDTA)
            ├── Query            Flux for the web UI (IDTA)
            └── InfluxDb2Target  Bucket, Measurement, Tags, WriteMode (DMP extension, InfluxDB 2)

A series groups what is sampled together, never one variable each. The DMP
addresses the LinkedSegment; it reads the Record as the row shape and writes or
reads one point per row. A field's InfluxDB field is its idShortPath below the
Record (list members by index, ``Waypoints[0].x``), so renaming a field starts a
new InfluxDB field. A RecordReference counts exactly as if the referenced
element were declared at its place: a Property is one field, an SMC or SML a
group, an Operation a group of its input, InOut and output variables. The tags
name the AAS that owns the series (``{aas_id_short}``, resolved when the
resource is built). The WriteMode says how the DMP writes a row: Synchronous
(the default) waits for InfluxDB to acknowledge each point, so a failed write
fails the evaluation; Asynchronous hands the point to a batching buffer and
goes on, for logs and other rows whose loss must not stop the data flow.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import ClassVar, Dict, List, Literal, Optional, TypeAlias, Union

from pydantic import field_validator, model_validator

from aas_pydantic import (
    File, MultiLanguageProperty, Property, Range, ReferenceElement, SubmodelElementCollection,
)
from aas_pydantic.aas_model import AasIdString
from aas_pydantic.submodel_templates.time_series import (
    Endpoint, Endpoint_t, LinkedSegment as _LinkedSegment, Metadata as _Metadata, Query, Segments as _Segments, State,
    TimeSeries as _TimeSeries, InternalSegment as _InternalSegment, Records as _Records,
)

from aas_model.constants import (
    INFLUX_BUCKET, INFLUX_ORG, INFLUX_ORIGIN,
    TS_COLLECTION, TS_INFLUX_TARGET, TS_INFLUX_TARGET_BUCKET,
    TS_INFLUX_TARGET_MEASUREMENT, TS_INFLUX_TARGET_TAG, TS_INFLUX_TARGET_TAGS, TS_INFLUX_TARGET_WRITE_MODE,
    TS_RECORD_FIELD, TS_RECORD_FILE, TS_RECORD_GROUP, TS_RECORD_RANGE, TS_RECORD_REFERENCE,
    TS_RECORD_TEXT,
)

IDTA_TIME_SERIES = "https://admin-shell.io/idta/TimeSeries/1/1"
IDTA_RECORD = "https://admin-shell.io/idta/TimeSeries/Record/1/1"
IDTA_UTC_TIME = "https://admin-shell.io/idta/TimeSeries/UtcTime/1/1"

# Measurement names, tag keys and values are spliced into Flux string literals.
_IDENTIFIER = re.compile(r"^[A-Za-z0-9_.\-{}]+$")


# ── Record ───────────────────────────────────────────────────────────────────

class UtcTime(Property):
    """The row's time. A value the transformation returns is the point's time;
    without one the DMP stamps the time of evaluation."""
    id_short: AasIdString = "Time"
    semantic_id: str = IDTA_UTC_TIME
    value_type: str = "xs:dateTime"


class RecordField(Property):
    """One field of the row. The concept it measures rides as a supplemental
    semantic id, as on a ``VariableProp``."""
    semantic_id: str = TS_RECORD_FIELD


class RecordRange(Range):
    """A band of the row: two fields, ``<path>.min`` and ``<path>.max``, of its valueType."""
    semantic_id: str = TS_RECORD_RANGE


class RecordFile(File):
    """A file belonging to the row: one string field, its path or URL. The
    file itself stays in the AAS or wherever the path points."""
    KEEP_WITHOUT_VALUE: ClassVar[bool] = True
    semantic_id: str = TS_RECORD_FILE


class RecordText(MultiLanguageProperty):
    """A text in several languages: one string field per language, ``<path>.en``.
    Its value declares the languages, each with the field's label in it."""
    semantic_id: str = TS_RECORD_TEXT

    @field_validator("value")
    @classmethod
    def _declares_its_languages(cls, value):
        if not value or any(not language or not label for language, label in value.items()):
            raise ValueError("a Record text declares at least one language, each with a label")
        return value


class RecordGroup(SubmodelElementCollection):
    """Fields that belong together within a row (``Position.X``)."""
    semantic_id: str = TS_RECORD_GROUP
    field: Dict[str, "RecordEntry"] = {}


class RecordReference(ReferenceElement):
    """An AAS element whose structure is part of the row, as if declared at this
    place under this idShort: a Property, an SMC or SML, or an Operation (its
    input, InOut and output variables). The DMP resolves it; values still come
    from the transformation."""
    semantic_id: str = TS_RECORD_REFERENCE


RecordEntry = Union[RecordField, RecordRange, RecordFile, RecordText, RecordGroup, RecordReference]


class TimeSeriesRecord(SubmodelElementCollection):
    id_short: AasIdString = "Record"
    semantic_id: str = IDTA_RECORD
    Time: UtcTime = UtcTime()
    field: Dict[str, RecordEntry] = {}

    @model_validator(mode="after")
    def _time_is_not_a_field(self):
        if "Time" in self.field:
            raise ValueError("'Time' is the row's time, not a field")
        return self


class TimeSeriesMetadata(_Metadata):
    Record: TimeSeriesRecord


# ── LinkedSegment write target (DMP extension) ───────────────────────────────

def _check_identifier(kind: str, value: str) -> str:
    if not _IDENTIFIER.match(value):
        raise ValueError(f"{kind} {value!r} must match {_IDENTIFIER.pattern}")
    return value


class Bucket(Property):
    """The InfluxDB bucket; by default the workspace's."""
    id_short: AasIdString = "Bucket"
    semantic_id: str = TS_INFLUX_TARGET_BUCKET
    value: str = INFLUX_BUCKET

    @field_validator("value")
    @classmethod
    def _is_an_identifier(cls, value):
        return _check_identifier("bucket", value)


class Measurement(Property):
    id_short: AasIdString = "Measurement"
    semantic_id: str = TS_INFLUX_TARGET_MEASUREMENT

    @field_validator("value")
    @classmethod
    def _is_an_identifier(cls, value):
        return _check_identifier("measurement", value)


class Tag(Property):
    """One series tag: the idShort is the tag key, the value its value."""
    semantic_id: str = TS_INFLUX_TARGET_TAG

    @field_validator("value")
    @classmethod
    def _is_an_identifier(cls, value):
        return _check_identifier("tag value", value)


class Tags(SubmodelElementCollection):
    id_short: AasIdString = "Tags"
    semantic_id: str = TS_INFLUX_TARGET_TAGS
    tag: Dict[str, Tag] = {}

    @field_validator("tag")
    @classmethod
    def _keys_are_identifiers(cls, tag):
        for key in tag:
            _check_identifier("tag key", key)
        return tag


WriteModeValue = Literal["Synchronous", "Asynchronous"]


class TargetWriteMode(Property):
    """How the DMP writes a row: ``Synchronous`` waits for InfluxDB's
    acknowledgement of each point; ``Asynchronous`` batches points and does
    not wait. Absent means Synchronous."""
    id_short: AasIdString = "WriteMode"
    semantic_id: str = TS_INFLUX_TARGET_WRITE_MODE
    value: WriteModeValue = "Synchronous"


# Aliases, so a field can carry the name of its class and a default (as in the generated templates).
Bucket_t: TypeAlias = Bucket
Tags_t: TypeAlias = Tags


class InfluxDb2Target(SubmodelElementCollection):
    """Where the DMP writes and reads the segment's points on InfluxDB 2. Each
    database has its own target, told apart by semanticId; a segment carries
    exactly one. The IDTA Query is for people and the web UI; the DMP never
    parses it."""
    id_short: AasIdString = "InfluxDb2Target"
    semantic_id: str = TS_INFLUX_TARGET
    Bucket: Bucket_t = Bucket()
    Measurement: Measurement
    # The series names the AAS that owns it (``{aas_id_short}``, resolved when the resource is built).
    Tags: Tags_t = Tags(tag={"asset": Tag(value="{aas_id_short}")})
    WriteMode: Optional[TargetWriteMode] = None


def _flux_query(bucket: str, measurement: str, tags: Dict[str, str]) -> str:
    """A segment's Query: its points in the web UI's time range, one field per selected Record field
    (``{{y-value}}``, substituted by the UI)."""
    lines = [
        f'from(bucket: "{bucket}")',
        "  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)",
        f'  |> filter(fn: (r) => r["_measurement"] == "{measurement}")',
        *(f'  |> filter(fn: (r) => r["{key}"] == "{value}")' for key, value in tags.items()),
        '  |> filter(fn: (r) => r["_field"] == "{{y-value}}")',
    ]
    return "\n".join(lines)


def _check_time(kind: str, value: Optional[str]) -> Optional[str]:
    """A segment time: an xs:dateTime with an offset, the format of a UtcTime series."""
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{kind} {value!r} is not an xs:dateTime") from None
    if parsed.tzinfo is None:
        raise ValueError(f"{kind} {value!r} needs an offset, e.g. Z")
    return value


class DmpLinkedSegment(_LinkedSegment):
    """A segment on the workspace's InfluxDB 2. Its StartTime and EndTime bound what the DMP reads: a segment
    with an EndTime is ``Completed`` and read-only, one without is ``InProgress`` and open for writes. The
    Query (for the web UI) and the State follow from the target and the times unless authored."""
    Endpoint: Endpoint_t = Endpoint(value=f"{INFLUX_ORIGIN}/api/v2/query?org={INFLUX_ORG}")
    InfluxDb2Target: InfluxDb2Target

    @model_validator(mode="before")
    @classmethod
    def _query_from_the_target(cls, data):
        target = data.get("InfluxDb2Target") if isinstance(data, dict) else None
        if isinstance(target, InfluxDb2Target) and "Query" not in data:
            tags = {key: tag.value for key, tag in target.Tags.tag.items()}
            data = {**data, "Query": Query(value=_flux_query(target.Bucket.value, target.Measurement.value, tags))}
        return data

    @model_validator(mode="after")
    def _times_and_state(self):
        start = _check_time("StartTime", self.StartTime.value if self.StartTime else None)
        end = _check_time("EndTime", self.EndTime.value if self.EndTime else None)
        if start and end and datetime.fromisoformat(end) <= datetime.fromisoformat(start):
            raise ValueError("EndTime must lie after StartTime")
        if self.State is None:
            self.State = State(value="Completed" if end else "InProgress")
        return self


class TimeSeriesRecords(_Records):
    """The rows of an InternalSegment, each a record of the profile."""
    Record: Dict[str, TimeSeriesRecord] = {}


class TimeSeriesInternalSegment(_InternalSegment):
    Records: TimeSeriesRecords


class TimeSeriesSegments(_Segments):
    LinkedSegment: Dict[str, DmpLinkedSegment] = {}
    InternalSegment: Dict[str, TimeSeriesInternalSegment] = {}


class TimeSeriesCollection(SubmodelElementCollection):
    semantic_id: str = TS_COLLECTION
    supplemental_semantic_ids: List[str] = [IDTA_TIME_SERIES]
    Metadata: TimeSeriesMetadata
    Segments: TimeSeriesSegments


class TimeSeriesSubmodel(_TimeSeries):
    """The profile as the IDTA 02008 submodel: a series of its own rather than one in Variables (and the class its
    template is exported from)."""
    Metadata: TimeSeriesMetadata
    Segments: TimeSeriesSegments


RecordGroup.model_rebuild()
TimeSeriesRecord.model_rebuild()
