"""AIMC submodel — Asset Interfaces Mapping Configuration (IDTA 02027 2/0 based).

Maps AID interface sources (properties) to AAS sinks (Variables / Skills /
Parameters) so the DataBridge can route live data.  The mapping between a
source's payload fields and each sink is expressed in the ``Transformation``
Lua script (``aimc_main(sources)``).

The concepts come from the generated IDTA AIMC 2.0 template:
``MappingConfiguration`` carries ``default_polling_interval``, a
``Transformation`` (a Blob of Lua source, ``text/plain``), ``Sources[]`` and
``Sinks[]``.  This module subclasses the generated ``Transformation`` (a Blob
of Lua source, ``text/plain``) and narrows the mapping configuration to use it,
while inheriting ``Sources``/``Sinks`` straight from the generated container
class.

Named-field style: containers hold their children as DIRECT named fields
(no ``value``/``submodel_element`` wrapper).

Structure (IDTA 02027 2/0)::

    AssetInterfacesMappingConfiguration
    └── MappingConfigurations[]              (SML)
        └── MappingConfiguration             (SMC)
            ├── default_polling_interval     (Property)
            ├── transformation               (Transformation — Blob, text/plain Lua)
            ├── Sources[]                    (SML)
            │   └── Source                   (SMC: source ref + polling_interval + source_id)
            └── Sinks[]                      (SML)
                └── Sink                     (SMC: sink ref + sink_id)
"""

from __future__ import annotations

from typing import ClassVar, List

from pydantic import model_validator
from aas_pydantic import (
    Submodel,
)
from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import (
    Sources,
    Sinks,
    Sources_t, Sinks_t,
    MappingConfiguration as _BaseMappingConfiguration,
    MappingConfigurations as _BaseMappingConfigurations,
    Transformation as _BaseTransformation,
    Transformation_t,
)

AIMC_SUBMODEL = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/Submodel"
AIMC_MAPPING_CONFIGURATIONS = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/1/0/MappingConfigurations"
AIMC_MAPPING_CONFIGURATION = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration"
AIMC_TRANSFORMATION = "https://admin-shell.io/idta/AssetInterfacesMappingConfiguration/2/0/MappingConfiguration/Transformation"


class Transformation(_BaseTransformation):
    """The AIMC transformation — the Lua ``aimc_main(sources)`` script.

    Subclasses the generated AIMC ``Transformation`` (a Blob) so it matches
    the ``Transformation_t`` annotation on ``AimcMappingConfiguration``; the
    script is stored as bytes.  A plain Lua string is accepted on input and
    encoded, so configs can be authored as text.
    """
    semantic_id: str = AIMC_TRANSFORMATION
    description: str = (
        "The transformation allows for transforming incoming data before "
        "writing it to the sinks. The transformation must contain an "
        '"aimc_main(sources)" entrypoint function in Lua.'
    )
    content_type: str = "text/plain"

    @model_validator(mode="before")
    @classmethod
    def _coerce_text_to_bytes(cls, data):
        if isinstance(data, dict) and isinstance(data.get("value"), str):
            return {**data, "value": data["value"].encode("utf-8")}
        return data


class AimcMappingConfiguration(_BaseMappingConfiguration):
    """A single mapping: AID sources → AAS sinks + a Lua transformation.

    ``Sources``/``Sinks`` are required (One) in the template — provided here
    so the variant constructs; ``Transformation`` is narrowed to the
    dedicated Blob concept."""
    Sources: Sources_t = Sources()
    Sinks: Sinks_t = Sinks()
    Transformation: Transformation_t = Transformation()


class AimcMappingConfigurations(_BaseMappingConfigurations):
    """List of MappingConfigurations (narrowed to the Transformation variant)."""
    item_type: ClassVar = AimcMappingConfiguration
    value: List[AimcMappingConfiguration] = []


class Aimc(Submodel):
    """Asset Interfaces Mapping Configuration — maps AID sources to AAS sinks."""
    semantic_id: str = AIMC_SUBMODEL
    description: str = (
        "Maps AID interface affordances (sources) to submodel elements "
        "(sinks) for live-data routing via the DataBridge."
    )
    VERSION: ClassVar[str] = "2"
    REVISION: ClassVar[str] = "0"

    MappingConfigurations: AimcMappingConfigurations = AimcMappingConfigurations()


AimcMappingConfiguration.model_rebuild()
AimcMappingConfigurations.model_rebuild()
Aimc.model_rebuild()
