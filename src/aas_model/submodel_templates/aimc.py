"""DMP-extended AssetInterfacesMappingConfiguration — extensions over the
generated IDTA AIMC.

Layering (DMP v3): the generated IDTA template
(``aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration``)
stays PRISTINE — the DMP extension lives HERE:

- **``DmpMappingConfiguration``** adds the OPTIONAL ``ResponseTransformation``
  blob: the correlated-REPLY direction of an operation mapping. A mapping
  whose SOURCE references an Operation SubmodelElement (the ``Operation`` key
  type classifies it as an interaction, ADR-022) carries the REQUEST
  transformation in the IDTA ``Transformation`` blob and, optionally, the
  RESPONSE transformation in ``ResponseTransformation`` — both directions of
  the bi-directional action contract are then authored explicitly. When the
  response blob is absent the reply passes through unchanged (one-MC
  authoring default).

The semantic id mirrors the IDTA ``Transformation`` vocabulary member
(``.../MappingConfiguration/ResponseTransformation``).
"""

from __future__ import annotations

from typing import ClassVar, List, Optional

from aas_pydantic.submodel_templates.asset_interfaces_mapping_configuration import (
    AssetInterfacesMappingConfiguration as _BaseAimc,
    MappingConfiguration as _BaseMappingConfiguration,
    MappingConfigurations as _BaseMappingConfigurations,
    Blob,
)

from aas_model.constants import AIMC_RESPONSE_TRANSFORMATION


class DmpResponseTransformation(Blob):
    """The correlated-REPLY transformation of an operation mapping: device
    response → caller-facing reply (same ``aimc_main(sources)`` Lua contract,
    keyed by the action name)."""
    semantic_id: str = AIMC_RESPONSE_TRANSFORMATION
    description: str = "The optional response-direction transformation of an operation mapping: the correlated reply from the asset's command affordance is transformed before it is returned to the caller. Must contain an \"aimc_main(sources)\" entrypoint function in Lua. When absent the reply passes through unchanged."
    content_type: str = "text/plain"


class DmpMappingConfiguration(_BaseMappingConfiguration):
    """IDTA MappingConfiguration + the optional response-direction blob."""
    ResponseTransformation: Optional[DmpResponseTransformation] = None


class DmpMappingConfigurations(_BaseMappingConfigurations):
    """IDTA MappingConfigurations list over the DMP-extended configuration."""
    item_type: ClassVar = DmpMappingConfiguration
    value: List[DmpMappingConfiguration] = []


class DmpAimc(_BaseAimc):
    """IDTA AssetInterfacesMappingConfiguration over the DMP-extended list."""
    MappingConfigurations: DmpMappingConfigurations = DmpMappingConfigurations()
