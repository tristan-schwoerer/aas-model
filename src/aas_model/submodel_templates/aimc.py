"""DMP-extended AssetInterfacesMappingConfiguration — extensions over the
generated IDTA AIMC.

Layering (DMP v3): the generated IDTA template
(``aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration``)
stays PRISTINE — the DMP extension lives HERE. A plain IDTA AIMC (Sources,
Sinks, Transformation, DefaultPollingInterval) remains a valid DMP input for
data mappings; every addition is optional and carries a semantic id in this
project's namespace (``constants.AIMC_*``).

An operation mapping (its Sources address its individual AAS Operation
variables, ADR-022) invokes one action affordance whose terminal reply is its
result (OPC UA Method, MQTT 5 request/reply on the correlation data, HTTP):

1. **command** — the IDTA ``Transformation`` turns the caller's variables into
   the command; the IDTA ``Sinks`` address the action;
2. **response** — ``ResponseSources`` select the action's output or members
   of it, the ``ResponseTransformation`` maps them, and ``ResponseSinks``
   route each result to an explicit Operation output or InOut variable; other
   sinks are written best effort. The three are authored together. An Operation
   with output or InOut variables needs them; nothing is matched by name.
   Without them the Operation answers with no outputs (an invoke-only action
   such as Halt).

Multi-step device sequences (set parameters, trigger, poll a status, read a
result, reset) are not modelled here; the higher-level control orchestrates
them through ordinary mappings.
"""

from __future__ import annotations

import re

from typing import ClassVar, List, Optional

from pydantic import field_validator, model_validator

from aas_pydantic import (
    Property, ReferenceElement, SubmodelElementCollection, SubmodelElementList,
)

from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import (
    AssetInterfacesMappingConfiguration as _BaseAimc,
    MappingConfigurationsItem as _BaseMappingConfiguration,
    MappingConfigurations as _BaseMappingConfigurations,
    Blob,
)

from aas_model.constants import (
    AIMC_RESPONSE_SOURCE_REFERENCE,
    AIMC_RESPONSE_SOURCE_ID,
    AIMC_RESPONSE_SINK_REFERENCE,
    AIMC_RESPONSE_SINK_ID,
    AIMC_RESPONSE_SINK,
    AIMC_RESPONSE_SINKS,
    AIMC_RESPONSE_SOURCE,
    AIMC_RESPONSE_SOURCES,
    AIMC_RESPONSE_TRANSFORMATION,
    AIMC_EVALUATION,
    AIMC_EVALUATION_MODE,
    AIMC_INVOCATION_TIMEOUT,
)
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import (
    SourcesItem as _SourcesItem,
    Sources as _BaseSources,
    SinksItem as _SinksItem,
    Sinks as _BaseSinks,
    SinkId as _SinkId,
    SourceId as _SourceId,
)


class _NamedByItsId(SubmodelElementCollection):
    """A source or sink, named after its ``SourceId``/``SinkId`` unless named otherwise. Its name stays out of
    the AAS's idShorts (AASd-120: list items have none): it names it in the pydantic JSON and is its displayName."""
    ID_FIELD: ClassVar[str]

    @model_validator(mode="after")
    def _named_after_its_id(self):
        unnamed = self.id_short == SubmodelElementCollection.model_fields["id_short"].default
        identifier = getattr(self, self.ID_FIELD, None)
        if unnamed and identifier is not None and identifier.value:
            self.id_short = identifier.value
        return self


class DmpResponseTransformation(Blob):
    """Response phase: the action's reply, projected by the ResponseSources →
    the ResponseSink values keyed by SinkId; the SinkId of the ResponseSink
    selecting the Operation carries the caller's outputs. Called as
    ``aimc_main(sources)``."""
    semantic_id: str = AIMC_RESPONSE_TRANSFORMATION
    description: str = "The response-direction transformation of an operation mapping: the action's reply, projected by the response sources, is transformed into the response sink values; the response sink selecting the Operation receives the caller's outputs. Must contain an \"aimc_main(sources)\" entrypoint function in Lua. Authored together with the response sources and sinks; without them the Operation answers with no outputs."
    content_type: str = "text/plain"


class DmpResponseSourceReference(ReferenceElement):
    semantic_id: str = AIMC_RESPONSE_SOURCE_REFERENCE
    description: str = "Reference to a SubmodelElement used as a correlated response source."


class DmpResponseSourceId(_SourceId):
    semantic_id: str = AIMC_RESPONSE_SOURCE_ID


class DmpResponseSource(_NamedByItsId):
    """A response source: the action's output, or a member of it."""
    semantic_id: str = AIMC_RESPONSE_SOURCE
    description: str = "A response source: the output of the invoked action, or a member of it."
    ID_FIELD: ClassVar[str] = "SourceId"
    Source: DmpResponseSourceReference
    SourceId: DmpResponseSourceId


class DmpResponseSources(SubmodelElementList):
    semantic_id: str = AIMC_RESPONSE_SOURCES
    description: str = "Response sources selected for the correlated response transformation."
    item_type: ClassVar = DmpResponseSource
    value: List[DmpResponseSource] = []


class DmpResponseSinkReference(ReferenceElement):
    semantic_id: str = AIMC_RESPONSE_SINK_REFERENCE
    description: str = "Reference to a SubmodelElement used as a correlated response sink."


class DmpResponseSinkId(_SinkId):
    semantic_id: str = AIMC_RESPONSE_SINK_ID


class DmpResponseSink(_NamedByItsId):
    semantic_id: str = AIMC_RESPONSE_SINK
    description: str = "A correlated response sink reference and its transformation identifier."
    ID_FIELD: ClassVar[str] = "SinkId"
    Sink: DmpResponseSinkReference
    SinkId: DmpResponseSinkId


class DmpResponseSinks(SubmodelElementList):
    semantic_id: str = AIMC_RESPONSE_SINKS
    description: str = "Response sinks written from the correlated response transformation."
    item_type: ClassVar = DmpResponseSink
    value: List[DmpResponseSink] = []


EVALUATION_MODES = ("OnUpdate", "OnChange", "Cached", "ReadAtEvaluation")


class DmpEvaluationMode(Property):
    id_short: str = "Mode"
    semantic_id: str = AIMC_EVALUATION_MODE
    description: str = ("OnUpdate: every new value evaluates the mapping. OnChange: only a value that differs from "
                        "the previous one. Cached: never; the latest observed or polled value is used. "
                        "ReadAtEvaluation: never; the source is read once per evaluation.")
    value_type: str = "xs:string"


class DmpEvaluation(SubmodelElementCollection):
    """Whether a Source triggers its mapping and how its value is obtained. Without it a Source is OnUpdate;
    an Operation is always its mapping's only trigger, and its mapping's further Sources are ReadAtEvaluation."""
    semantic_id: str = AIMC_EVALUATION
    description: str = "How the Source contributes to its mapping's evaluations."
    Mode: DmpEvaluationMode


# BaSyx Go waits at most 15 minutes for a delegated Operation.
MAX_INVOCATION_TIMEOUT_SECONDS = 15 * 60
_DURATION = re.compile(r"^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$")


def invocation_timeout_seconds(value: str) -> int:
    """The seconds of an InvocationTimeout: an xs:duration of whole hours, minutes and seconds (``PT2M``), above
    zero and at most 15 minutes."""
    match = _DURATION.match(value or "")
    if not match or not any(match.groups()):
        raise ValueError(f"InvocationTimeout {value!r} must be an xs:duration such as PT30S or PT2M")
    hours, minutes, seconds = match.groups()
    total = int(hours or 0) * 3600 + int(minutes or 0) * 60 + int(seconds or 0)
    if not 0 < total <= MAX_INVOCATION_TIMEOUT_SECONDS:
        raise ValueError(f"InvocationTimeout {value!r} must lie above zero and at most PT15M")
    return total


class DmpInvocationTimeout(Property):
    """How long the DMP waits for the device's terminal reply to the action an Operation invokes (default PT30S).
    A caller invoking through BaSyx Go must allow at least as long (its clientTimeoutDuration)."""
    id_short: str = "InvocationTimeout"
    semantic_id: str = AIMC_INVOCATION_TIMEOUT
    value_type: str = "xs:duration"

    @field_validator("value")
    @classmethod
    def _is_a_timeout(cls, value):
        if value is not None:
            invocation_timeout_seconds(value)
        return value


class DmpSource(_NamedByItsId, _SourcesItem):
    """IDTA Source + the optional Evaluation."""
    ID_FIELD: ClassVar[str] = "SourceId"
    Evaluation: Optional[DmpEvaluation] = None


class DmpSink(_NamedByItsId, _SinksItem):
    """IDTA Sink, named after its SinkId."""
    ID_FIELD: ClassVar[str] = "SinkId"


def _fields(model) -> dict:
    """A model's field values, nested models kept as they are."""
    return {name: getattr(model, name) for name in type(model).model_fields}


class DmpSources(_BaseSources):
    """IDTA Sources whose items may carry an Evaluation. Plain IDTA Sources items are accepted and become
    DmpSource items, so parsing a serialized AIMC keeps every Source's Evaluation."""
    item_type: ClassVar = DmpSource
    value: List[DmpSource] = []

    @field_validator("value", mode="before")
    @classmethod
    def _as_dmp_sources(cls, value):
        if not isinstance(value, list):
            return value
        return [item if isinstance(item, DmpSource) or not isinstance(item, _SourcesItem)
                else DmpSource(**_fields(item)) for item in value]


class DmpSinks(_BaseSinks):
    """IDTA Sinks over DmpSink items; plain IDTA Sinks items become DmpSink items."""
    item_type: ClassVar = DmpSink
    value: List[DmpSink] = []

    @field_validator("value", mode="before")
    @classmethod
    def _as_dmp_sinks(cls, value):
        if not isinstance(value, list):
            return value
        return [item if isinstance(item, DmpSink) or not isinstance(item, _SinksItem)
                else DmpSink(**_fields(item)) for item in value]


class DmpMappingConfiguration(_BaseMappingConfiguration):
    """IDTA MappingConfiguration + optional correlated response mapping; its Sources may carry an Evaluation."""
    Sources: DmpSources
    Sinks: DmpSinks

    @field_validator("Sources", mode="before")
    @classmethod
    def _as_dmp_sources(cls, value):
        if isinstance(value, _BaseSources) and not isinstance(value, DmpSources):
            return DmpSources(**_fields(value))
        return value

    @field_validator("Sinks", mode="before")
    @classmethod
    def _as_dmp_sinks(cls, value):
        if isinstance(value, _BaseSinks) and not isinstance(value, DmpSinks):
            return DmpSinks(**_fields(value))
        return value

    ResponseTransformation: Optional[DmpResponseTransformation] = None
    ResponseSources: Optional[DmpResponseSources] = None
    ResponseSinks: Optional[DmpResponseSinks] = None
    InvocationTimeout: Optional[DmpInvocationTimeout] = None


class DmpMappingConfigurations(_BaseMappingConfigurations):
    """IDTA MappingConfigurations list over the DMP-extended configuration."""
    item_type: ClassVar = DmpMappingConfiguration
    value: List[DmpMappingConfiguration] = []


class DmpAimc(_BaseAimc):
    """IDTA AssetInterfacesMappingConfiguration over the DMP-extended list."""
    MappingConfigurations: DmpMappingConfigurations = DmpMappingConfigurations()
