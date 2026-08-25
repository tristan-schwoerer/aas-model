"""aas_model — the shared AAS data-model package (ADR-016).

Single source of truth for the whole AAS data model, used by BOTH consumers:

* the **registration service** authors/instantiates AAS through it
  (``aas_model.builder`` / ``aas_model.resource_template`` …), and
* the **aas-camel-dmp management node** parses AAS JSON back into the same
  models through it (``aas_model._serde``).

It bundles the model base framework + generated IDTA templates (vendored
``aas_pydantic``), the project-specific submodel templates
(``aas_model.submodel_templates``), the resource/instantiation templates
(``aas_model.resource_template``), the build/schema helpers (``builder``,
``id_injector``, ``json_schema_aid``, ``schema_parser``) and the parse bridge
(``_serde``).
"""

from aas_model import _serde  # noqa: F401  (public parse API)
from aas_model.constants import *  # noqa: F401,F403
from aas_model import builder  # noqa: F401
from aas_model.builder import (  # noqa: F401
    build_from_dict,
    build_from_json,
    build_resource_type_aas,
    generate_station_template,
    merge_instance_config,
)
from aas_model.id_injector import inject_ids  # noqa: F401
from aas_model.resource_template import (  # noqa: F401
    ResourceTypeAAS,
    nameplate,
    asset_interfaces_description,
    asset_interfaces_mapping_configuration,
    control_component_instance,
    variables,
    parameters,
)
from aas_model.submodel_templates import *  # noqa: F401,F403
