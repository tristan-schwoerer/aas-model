"""Time Series is usable independently and is not a Resource default."""

import json

import pytest
from basyx.aas import model
from basyx.aas.adapter.json import json_serialization

from aas_model import Resource, inject_ids
from aas_json import parse_submodel_dict
from aas_pydantic import AAS, convert_model_to_aas
from aas_pydantic.convert_util import strip_temp_id_short_attributes
from aas_pydantic.submodel_templates.time_series import (
    EndTime, Endpoint, ExternalSegment, File_time_series, InternalSegment, LinkedSegment, Metadata,
    Name, Query, Record, Records, SampleAccelerationX, Segments, Time, TimeSeries,
)


@pytest.fixture
def series():
    return TimeSeries(
        id_short="TimeSeries",
        Metadata=Metadata(
            Name=Name(value={"en": "Acceleration samples"}),
            Record=Record(Time={"RelativeTime": Time(value="0")}),
        ),
        Segments=Segments(
            InternalSegment={"Measurements": InternalSegment(
                Records=Records(Record={
                    "Sample0001": Record(
                        Time={"RelativeTime": Time(value="1")},
                        sampleAccelerationX=SampleAccelerationX(value="12"),
                    ),
                }),
            )},
            ExternalSegment={"Archive": ExternalSegment(File=File_time_series(
                content_type="application/json", value="https://example.test/series.json",
            ))},
            LinkedSegment={"Database": LinkedSegment(
                Endpoint=Endpoint(value="https://example.test/timeseries"),
                Query=Query(value="SELECT acceleration FROM measurements"),
                EndTime=EndTime(value="2"),
            )},
        ),
    )


def test_time_series_json_roundtrip_retains_segment_types(series):
    encoded = series.model_dump_json()
    restored = TimeSeries.model_validate_json(encoded)

    assert restored.model_dump(mode="json") == json.loads(encoded)
    assert isinstance(restored.Metadata, Metadata)
    assert isinstance(restored.Segments.InternalSegment["Measurements"], InternalSegment)
    assert isinstance(restored.Segments.ExternalSegment["Archive"], ExternalSegment)
    assert isinstance(restored.Segments.LinkedSegment["Database"], LinkedSegment)
    assert restored.Segments.LinkedSegment["Database"].EndTime.semantic_id.endswith("/EndTime/1/1")


def test_time_series_standalone_aas_roundtrip(series):
    class SeriesShell(AAS):
        time_series: TimeSeries

    asset = SeriesShell(id_short="SeriesShell", id="urn:test:series-shell", time_series=series)
    inject_ids(asset)
    store = convert_model_to_aas(asset)
    strip_temp_id_short_attributes(store)
    document = json.loads(json_serialization.object_store_to_json(store))
    restored = parse_submodel_dict(document["submodels"][0], TimeSeries)

    assert len(store) == 2
    shell = next(obj for obj in store if isinstance(obj, model.AssetAdministrationShell))
    assert len(shell.submodel) == 1
    assert next(iter(shell.submodel)).resolve(store).id_short == "TimeSeries"
    assert restored.Metadata.Name.value == {"en": "Acceleration samples"}
    record = restored.Segments.InternalSegment["Measurements"].Records.Record["Sample0001"]
    assert record.Time["RelativeTime"].value == "1"
    assert record.sampleAccelerationX.value == "12"
    assert restored.Segments.ExternalSegment["Archive"].File.value == "https://example.test/series.json"
    assert restored.Segments.LinkedSegment["Database"].Query.value == "SELECT acceleration FROM measurements"


def test_time_series_is_not_part_of_resource():
    assert "time_series" not in Resource.model_fields
    assert "TimeSeries" not in Resource.model_fields
    resource = Resource(id_short="WithoutTimeSeries")
    assert all(not isinstance(value, TimeSeries) for value in vars(resource).values())
