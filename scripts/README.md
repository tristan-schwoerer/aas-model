# IDTA Submodel Regeneration

`idta_generate.py` regenerates the IDTA pydantic model modules in
`src/aas_pydantic/submodel_templates/` from the JSON templates in the
`submodel-templates` submodule.

## Layout

- `../submodel-templates/published/` contains the source template JSON.
- `idta_generate.py` maps template elements to pydantic container and leaf
  classes. Its default `TEMPLATES` tuple pins the source paths used by the
  package; generated module docstrings record each source path relative to
  `published/`.
- `../src/aas_pydantic/submodel_templates/` contains the generated modules.

## Regenerate

Run from the repository root:

```bash
python scripts/idta_generate.py
python scripts/idta_generate.py '<Template Path>'
python scripts/idta_generate.py '<Template Path>' /tmp/generated-models
```

A relative template path is resolved under `submodel-templates/published/`.
Without arguments the generator writes all pinned templates to
`src/aas_pydantic/submodel_templates/`. A missing pinned input fails the run
rather than silently generating a partial package.

## Generated model behavior

- Container children are direct named fields. Safe `idShort` spellings retain
  their original casing (for example, `ManufacturerName`); invalid identifier
  characters are sanitized, placeholder suffixes (`__00__`, `{00}`) are
  stripped, and Python keywords receive a trailing underscore.
- `SMT/Cardinality`: `One` (or no qualifier) is a required field, `ZeroToOne`
  an optional one, and `ZeroToMany`/`OneToMany`/`TwoToMany`/`Recursive` a
  dynamic `Dict[str, Element]` map (its minimum checked by
  `validate_idta_cardinality`). Any other value, or the legacy `Multiplicity`
  qualifier, fails the run. A `SubmodelElementList` stays a list, typed when
  its items are homogeneous.
- Semantic IDs, supplemental semantic IDs, value types, content types, the
  English description and the display name are kept on the generated classes.
  The display name labels the template element (`Capability Set`), so it is a
  `TEMPLATE_DISPLAY_NAME` ClassVar, not an instance default: an instance is
  shown by its idShort, and the template export carries the label. A template's example values (a Property's value, a relationship's endpoints,
  an Entity's `globalAssetId`) are not defaults. Pydantic field/type name
  collisions use `_t: TypeAlias` aliases.
- Qualifiers that restrict a value are kept: `FormChoices`/`Enumeration` as
  `FORM_CHOICES`, `SMT/AllowedRange` as `ALLOWED_RANGE` (checked by `Property`),
  `AllowedIdShort` on a map's keys (IDTA's `[…]` meaning "optional"). The
  editorial ones (`EditIdShort`, `PresetIdShort`, `Form*`, `Comment`, …) are not.
- A template collection without children is open (`DynamicSubmodelElementCollection`).
- `ALTERNATIVES` names children a template marks mandatory each though one of
  them applies: they become optional and the container requires one
  (`IDTA_ONE_OF`). A pattern group names a variant (the AID's protocol): the
  elements below it are defined per variant, and where definitions differ each
  variant is a subclass of a shared base (`forms_MQTT(forms)`); the variant most
  of them share is the base itself. A copy of an element lacking a description
  another copy has is the same element.
- `VERSION`/`REVISION` come from the template's administration, else from its
  semanticId (`…/1/1/Submodel`), else they are empty.
- Repeated container definitions of one concept within a variant are merged
  into one field union; conflicting field types or repeatable defaults fail
  generation instead of dropping a definition.

Cardinality and list behavior intentionally follow the generator's current
policy; the generator does not rewrite template structures to make a particular
release importable. Review generated diffs and run the focused generator tests
before adopting an upstream template release. Do not generate into the package
directory while another integration is preparing its target-model changes.

# Template export

`export_templates.py` is the inverse of `idta_generate.py`: it writes a pydantic
submodel class as the AAS submodel template it describes, so our extensions can
be shared in the format IDTA publishes theirs. Each class becomes
`templates/<snake_name>.json`, an AAS environment with a Type shell and the
submodel template (`kind: Template`, no class markers).

```bash
python scripts/export_templates.py                                   # the pinned TEMPLATES into templates/
python scripts/export_templates.py module:Class                      # one class into templates/
python scripts/export_templates.py module:Class /tmp/out             # one class into another directory
```

`TEMPLATES` pins what we publish: the DMP's AID (`DmpAssetInterfacesDescription`)
and AIMC (`DmpAimc`), and our TimeSeries profile as the IDTA 02008 submodel
(`TimeSeriesSubmodel`). Ids are `{BASE_URL}/templates/{submodel,aas,asset}/<Class>/<version>/<revision>`.

The export follows the generator's rules backwards (see
`aas_pydantic/convert_pydantic_type.py`): a field's cardinality, a map as one
placeholder element (`Skill__00__`), lists with their attributes and an example
item where the item is described, the value-restricting qualifiers, a class's
defaults as example values, and an element that repeats an element it is nested
in (a data schema in a data schema) without its children. `tests/test_template_export.py`
checks that every pinned IDTA template exports from its generated class as the
template it was generated from (the known differences are listed there), and
that our extensions generate back to the same classes.
