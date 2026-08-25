# IDTA Submodel Regeneration

This directory (and the `submodel-templates` submodule) let you **regenerate the
generated IDTA pydantic classes** in `src/aas_pydantic/submodel_templates/` from
the official IDTA template JSON, so `aas_model` stays current with the published
submodel templates.

## Layout

- `../submodel-templates/` — git submodule → the IDTA `submodel-templates` repo
  (this project's fork): the published template JSONs are the raw source.
- `idta_generate.py` — the generator (from `aas_pydantic`/`aas_registration_service`
  tooling). Maps IDTA template JSON → pydantic container classes.
- `_generator_utils.py` — helpers used by the generator (pure stdlib).

## Regenerate

```bash
# from the aas-model repo root:
python scripts/idta_generate.py                 # all 7 templates -> src/aas_pydantic/submodel_templates/
python scripts/idta_generate.py '<Template Path>'  # a single template (path relative to submodel-templates/published)
```

## ⚠️ CRITICAL — read this before regenerating

The generator in this directory emits **container-style** classes (lowercase
`value:`/`submodel_element:` dict fields). **The committed/vendored
`src/aas_pydantic/submodel_templates/` models use **named-field style** with
`_t` TypeAlias clash aliases (e.g. `MappingConfigurations: MappingConfigurations_t`),
which the project submodels (`aas_model/submodel_templates/*`) **subclass and
depend on.**

Running the generator **unconditionally overwrites** the vendored files with the
container style and **breaks** the named-field subclasses (and therefore the
registration service + management-node parse path).

Therefore:
1. **Do not** run `idta_generate.py` blindly and commit the output as-is.
2. Regenerate into a **separate** output dir first
   (`python scripts/idta_generate.py <tmpl> /tmp/gen`) and **review the diff**
   against the committed named-field files before adopting.
3. When the IDTA templates change, reconcile the smaller, targeted edits into the
   named-field files by hand (or port the named-field generation into the
   generator) rather than regenerating wholesale.

The `_t` clash-alias / named-field scheme is the style this repo consumes; keep
regeneration aligned with it.
