#!/usr/bin/env python3
"""Export pydantic submodel classes as AAS submodel templates (AAS JSON): the inverse of ``idta_generate.py``.

Each class becomes ``<snake_name>.json``, an AAS environment with a Type shell and the class's submodel template
(``aas_pydantic.convert_model_to_submodel_template``), the way IDTA publishes theirs. Run from the repository root:

    python scripts/export_templates.py                                   # the pinned TEMPLATES into templates/
    python scripts/export_templates.py module:Class                      # one class into templates/
    python scripts/export_templates.py module:Class /tmp/out             # one class into another directory
"""

from __future__ import annotations

import importlib
import json
import os
import sys

from basyx.aas import model
from basyx.aas.adapter.json import json_serialization

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aas_pydantic import Submodel, convert_model_to_submodel_template  # noqa: E402
from aas_model.constants import BASE_URL  # noqa: E402
from idta_generate import snake  # noqa: E402

OUTPUT_ROOT = os.path.join(_ROOT, "templates")
# Our extensions of the IDTA templates, published as templates of their own.
TEMPLATES = (
    "aas_model.submodel_templates.aid:DmpAssetInterfacesDescription",
    "aas_model.submodel_templates.aimc:DmpAimc",
    "aas_model.submodel_templates.time_series:TimeSeriesSubmodel",
)


def _class(path: str) -> type:
    module_name, separator, class_name = path.partition(":")
    if not separator:
        raise SystemExit(f"{path!r}: name the class as module:Class")
    cls = getattr(importlib.import_module(module_name), class_name)
    if not (isinstance(cls, type) and issubclass(cls, Submodel)):
        raise SystemExit(f"{path!r} is no Submodel class")
    return cls


def export_template(path: str, output_dir: str) -> str:
    """Write the template of the class ``path`` (``module:Class``) into ``output_dir``; return the file."""
    cls = _class(path)
    version = "/".join(v for v in (getattr(cls, "VERSION", ""), getattr(cls, "REVISION", "")) if v)
    suffix = f"{cls.__name__}/{version}" if version else cls.__name__
    submodel = convert_model_to_submodel_template(cls, f"{BASE_URL}/templates/submodel/{suffix}")
    shell = model.AssetAdministrationShell(
        model.AssetInformation(model.AssetKind.TYPE, global_asset_id=f"{BASE_URL}/templates/asset/{suffix}"),
        f"{BASE_URL}/templates/aas/{suffix}", id_short=f"{cls.__name__}AAS",
        submodel={model.ModelReference.from_referable(submodel)},
    )
    text = json_serialization.object_store_to_json(model.DictIdentifiableStore([shell, submodel]))
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"{snake(cls.__name__)}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(json.loads(text), indent=2, ensure_ascii=False) + "\n")
    print(f"✅ {out_path}")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        export_template(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else OUTPUT_ROOT)
    else:
        for template in TEMPLATES:
            export_template(template, OUTPUT_ROOT)
        print(f"\nExported {len(TEMPLATES)} templates into {OUTPUT_ROOT}")
