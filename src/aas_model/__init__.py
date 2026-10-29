"""aas_model — the shared AAS data model (ADR-016) of the lab's resources.

Resources are authored as pydantic models and built into BaSyx AAS objects; the registration service restores
an exported Resource from JSON and builds it the same way.

* ``aas_pydantic`` (vendored): the model base framework and the generated IDTA templates.
* ``aas_model.submodel_templates``: our extensions of those templates and the project's own submodels.
* ``aas_model.resource_template``: the lab's resource types, the operational contract and the references.
* ``aas_model.resource_instances``: the concrete resources of the lab.
* ``builder.build_from_model``: a Resource into a BaSyx store; ``id_injector`` gives it its ids on the way and
  ``invocation_authoring`` its Operations' invocation addresses.
* ``json_schema_aid``: JSON Schemas into AID data schemas, and back.
"""

from aas_model.constants import *  # noqa: F401,F403
from aas_model import builder  # noqa: F401
from aas_model.builder import build_from_model  # noqa: F401
from aas_model.id_injector import inject_ids  # noqa: F401
from aas_model.resource_template import Resource, ResourceTypeAAS  # noqa: F401
from aas_model.submodel_templates import *  # noqa: F401,F403
