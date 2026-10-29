#!/usr/bin/env python3
"""Generate aas_pydantic models from IDTA submodel template JSON.

Emits named-field pydantic models from IDTA templates:

    Submodel:  ManufacturerName: ManufacturerName
    SMC:       InterfaceTemplateForMQTT: InterfaceTemplateForMQTT
    SML:       value: List[Item]

Container children are emitted as direct fields using their idShort spelling.
Required and optional fields follow SMT/Cardinality; multi-cardinality
elements become dynamic name-keyed maps, while SubmodelElementLists retain
their list behavior. IDTA example children define the class metadata, including
semantic_id, description, value_type, and supplemental semantic IDs.
"""

import io
import json
import keyword
import os
import re
import sys
import tokenize
from dataclasses import dataclass

# modelType → Python type name
ELEMENT_MAP = {
    "Property": "Property",
    "MultiLanguageProperty": "MultiLanguageProperty",
    "Range": "Range",
    "ReferenceElement": "ReferenceElement",
    "RelationshipElement": "RelationshipElement",
    "File": "File",
    "Blob": "Blob",
    "Capability": "Capability",
    "Operation": "Operation",
}


# IDTA placeholder suffixes (``Mode__00__``, ``Doc{00}``): a repeatable instance whose idShort the author picks.
_PLACEHOLDER = re.compile(r"(__\d+__|\{\d+\})$")


def safe_name(name: str) -> str:
    # Strip the placeholder suffix so class and field names are the clean base name.
    name = _PLACEHOLDER.sub("", name or "")
    return re.sub(r"[^0-9a-zA-Z_]", "_", name)


_CONCRETE_ID_SHORT = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")


def id_short_default(el: dict) -> list:
    """The class-level ``id_short`` default: the template's idShort when it is
    a concrete name. Placeholders (``{property_name}``, ``Mode__00__``) and
    missing idShorts (SML items) get none, since the instance name is chosen
    by the author (a dict key or a list position)."""
    raw = el.get("idShort") or ""
    if not _CONCRETE_ID_SHORT.fullmatch(raw) or _PLACEHOLDER.search(raw):
        return []
    return [f"    id_short: AasIdString = {json.dumps(raw)}"]


def snake(name: str) -> str:
    s = re.sub(r"(?<!^)(?=[A-Z])", "_", name)
    return s.replace("-", "_").lower()


def field_name(name: str) -> str:
    """Preserve idShort spelling while producing a valid Python identifier.

    IDTA ``__NN__`` placeholder suffixes are stripped; invalid characters are
    replaced with underscores and Python keywords receive a trailing underscore.
    """
    s = safe_name(name)
    if s and s[0].isdigit():
        s = f"_{s}"
    if keyword.iskeyword(s):
        s += "_"
    return s


_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_ROOT = os.path.join(_ROOT, "submodel-templates", "published")
OUTPUT_ROOT = os.path.join(_ROOT, "src", "aas_pydantic", "submodel_templates")
TEMPLATES = (
    "Capability Description/1/0/1/IDTA 02020_Template_Capability_Description.json",
    "Control Component Instance/2/0/1/IDTA 02016-2-0-1 _Template_ControlComponentInstance_forAASMetamodelV3.1.json",
    "Control Component Type/2/0/2/IDTA 02015-2-0-2 _Template_ControlComponentType_forAASMetamodelV3.1.json",
    "Hierarchical Structures enabling Bills of Material/1/1/2/IDTA 02011-1-1-2_Template_HSEBoM_forAASMetamodelV3.1.json",
    "Digital nameplate/3/0/2/IDTA 02006-3-0-2_Template_Digital Nameplate.json",
    "Asset Interfaces Mapping Configuration/2/1/IDTA 02027_Template_AIMC.json",
    "Asset Interfaces Description/1/2/IDTA 02017_Template_Asset Interfaces Description.json",
    "Time Series Data/1/1/2/IDTA 02008-1-1-2_Template_TimeSeriesData_forAASMetamodelV3.1.json",
)


# Children a template declares mandatory each although only one of them applies: they become optional, and
# the container requires one of them (``IDTA_ONE_OF``, checked by ``validate_idta_cardinality``).
# AID: an asset has at least one interface, of any protocol (every InterfaceTemplateFor* is OneToMany).
# CapabilityDescription: a PropertyConstraintContainer holds the constraint its ConstraintType names.
# A pattern's group names a variant (the AID's protocol): the elements below an alternative are defined per
# variant, and where their definitions differ each variant gets its own subclass of a shared base
# (``forms_MQTT(forms)``, see ``_variant_classes``).
ALTERNATIVES = {
    "AssetInterfacesDescription": re.compile(r"InterfaceTemplateFor(.+)"),
    "PropertyConstraintContainer": re.compile(r"BasicConstraint|CustomConstraint|OCLConstraint|OperationConstraint"),
}


def to_camel(name: str) -> str:
    """CamelCase a (snake_case) id_short for a dedicated leaf class name:
    ``year_of_construction`` → ``YearOfConstruction``, ``u_r_i_of_the_product``
    → ``URIOfTheProduct``.  The class name therefore never equals the
    snake_case field name (pydantic rejects field==annotation self-refs), and
    each element's template defaults live on its own named class."""
    parts = re.split(r"[^0-9a-zA-Z]+", name or "")
    return "".join(p[:1].upper() + p[1:] for p in parts if p)


def sid_namespace_suffix(base_name: str, sid: str) -> str:
    """Readable disambiguation suffix for a class whose id_short collides with
    another element of a *different* semanticId (e.g. AID's nested object-
    schema ``properties`` / ``property_name`` under ``json-schema#properties``
    / ``json-schema#propertyName``).  Prefers the semanticId fragment when it
    differs from the id_short (``json-schema#propertyName`` →
    ``property_name_json_schema``); otherwise uses the last namespace path
    segment (``.../ControlComponent/Skill/Errors/2/0`` → ``Errors_skill``)."""
    frag = sid.split("#")[-1] if "#" in sid else ""
    path = [p for p in sid.split("#")[0].split("/") if p and not p.isdigit()]
    if frag and snake(frag) != snake(base_name):
        return snake(frag)
    ns = path if frag else (path[:-1] if path else [])
    return snake(ns[-1]) if ns else ""


# Metadata lines that describe an element rather than define it.
_DESCRIPTIVE = ("    description:", "    TEMPLATE_DISPLAY_NAME:")


def _structural(meta) -> tuple:
    return tuple(line for line in meta if not line.startswith(_DESCRIPTIVE))


def _with_descriptions(meta: list, *others: list) -> list:
    """``meta`` with the description and display name an other copy of the element has where it has none
    (a template often describes an element in one place only)."""
    merged = list(meta)
    for other in others:
        for line in other:
            key = line.split(":")[0]
            if line.startswith(_DESCRIPTIVE) and not any(m.split(":")[0] == key for m in merged):
                merged.append(line)
    return merged


_ITEM_TYPE = "    item_type: ClassVar = "


def _meta_refs(meta, mapping: dict) -> list:
    """``meta`` with the class an SML's ``item_type`` names mapped (a provisional name to its final one)."""
    return [_ITEM_TYPE + str(mapping.get(line[len(_ITEM_TYPE):], line[len(_ITEM_TYPE):]))
            if line.startswith(_ITEM_TYPE) else line for line in meta]


def _variant_classes(order: list, classes: dict) -> tuple[list, dict]:
    """Resolve the variants of a class (``forms@MQTT``, ``forms@HTTP``, …) into final classes.

    A variant is defined per alternative (an AID protocol). Variants whose definitions agree, also through their
    children, are one class; descriptions alone do not set them apart. Where they differ, the class is a shared
    base holding what all variants have in common, and each variant that adds to it a subclass named after its
    alternative (``forms_MQTT(forms)``); a variant adding nothing is the base. Agreement is decided bottom-up by
    refining a partition until it is stable, so a split child splits its parents.

    Returns the classes to emit, ``(name, base or None, meta, fields)`` in definition order, and the final name
    of every provisional one."""
    group = {name: name.split("@")[0] for name in order}
    ctx = {name: name.split("@")[1] if "@" in name else "" for name in order}

    # Partition the provisional classes by structure, refined through their children until stable.
    ident = {name: group[name] for name in order}
    while True:
        refined = {name: (group[name], tuple(_meta_refs(_structural(classes[name][0]), ident)), tuple(
            (f.name, f.shape, f.required, f.aas_id_short, f.minimum, f.allowed_id_short, f.cardinality,
             tuple(ident.get(t, t) for t in f.types)) for f in classes[name][1]))
            for name in order}
        if len(set(refined.values())) == len(set(ident.values())):
            break
        ident = refined
    members = {}  # group → its distinct identities in definition order, each with its first provisional class
    for name in order:
        members.setdefault(group[name], {}).setdefault(ident[name], name)

    def described(identity, final):
        copies = [_meta_refs(classes[name][0], final) for name in order if ident[name] == identity]
        return _with_descriptions(copies[0], *copies[1:])

    # Name the variants; one adding nothing to its group's shared definition is the base.
    def resolve(is_base):
        final = {}
        for base, variants in members.items():
            for identity, first in variants.items():
                own = len(variants) > 1 and identity not in is_base
                if own and not ctx[first]:
                    raise ValueError(f"{base}: a definition outside every alternative differs from one inside")
                final.update({name: f"{base}_{ctx[first]}" if own else base
                              for name in order if ident[name] == identity})
        base_of = {final[name]: group[name] for name in order}

        def mapped(fields):
            return [FieldSpec(f.name, tuple(dict.fromkeys(final.get(t, t) for t in f.types)), f.shape,
                              f.required, f.aas_id_short, f.minimum, f.allowed_id_short, f.cardinality)
                    for f in fields]

        emitted, found = [], set()
        for base, variants in members.items():
            definitions = [(identity, final[first], described(identity, final), mapped(classes[first][1]))
                           for identity, first in variants.items()]
            if len(definitions) == 1:
                _, name, meta, fields = definitions[0]
                emitted.append((name, None, meta, fields))
                continue
            # The shared base: the metadata and fields every variant has, a field whose type differs typed by
            # its classes' own base (``forms``), or by the union of their types.
            common_meta = [line for line in definitions[0][2] if all(line in meta for *_, meta, _ in definitions)]
            # The base is described as the first variant describing it is; a variant describing it otherwise
            # keeps its own.
            for key in _DESCRIPTIVE:
                values = [line for *_, meta, _ in definitions for line in meta if line.startswith(key)]
                if values and values[0] not in common_meta:
                    common_meta.append(values[0])
            by_name = [{f.name: f for f in fields} for *_, fields in definitions]
            common = []
            for f in definitions[0][3]:
                specs = [variant.get(f.name) for variant in by_name]
                if any(spec is None for spec in specs):
                    continue
                if len({spec.shape for spec in specs}) > 1:
                    raise ValueError(f"{base}.{f.name}: the variants hold it differently")
                types = tuple(dict.fromkeys(base_of.get(t, t) for spec in specs for t in spec.types))
                common.append(FieldSpec(f.name, types, f.shape, all(spec.required for spec in specs),
                                        f.aas_id_short, f.minimum, f.allowed_id_short, f.cardinality))
            emitted.append((base, None, common_meta, common))
            shared = {f.name: f for f in common}
            for identity, name, meta, fields in definitions:
                own_fields = [f for f in fields if shared.get(f.name) != f]
                own_meta = [line for line in meta if line not in common_meta]
                if not own_fields and not _structural(own_meta):
                    found.add(identity)
                    if name == base:
                        # Its descriptions are the base's.
                        emitted[-1] = (base, None, _with_descriptions(common_meta, meta), common)
                    continue
                emitted.append((name, base, own_meta, own_fields))
        return emitted, final, found

    # First assume the variant most alternatives share is the base and keep it where that holds (a variant
    # referring to itself, as a recursive schema does, adds nothing only once it is the base); then add the
    # variants found to add nothing, until none is.
    split = {base: variants for base, variants in members.items() if len(variants) > 1}
    is_base = {max(variants, key=lambda identity: sum(ident[n] == identity for n in order))
               for variants in split.values()}
    while True:
        emitted, final, found = resolve(is_base)
        if is_base <= found:
            break
        is_base &= found
    while True:
        based = {group[next(n for n in order if ident[n] == identity)] for identity in is_base}
        new = {identity for identity in found - is_base
               if group[next(n for n in order if ident[n] == identity)] not in based}
        if not new:
            break
        is_base |= new
        emitted, final, found = resolve(is_base)

    # In definition order: a class where its first copy is, a shared base where its group first is.
    order_index = {}
    for i, name in enumerate(order):
        order_index.setdefault(group[name], i)
        order_index.setdefault(final[name], i)
    emitted.sort(key=lambda item: order_index[item[0]])
    return emitted, final


@dataclass(frozen=True)
class FieldSpec:
    name: str
    types: tuple[str, ...]
    shape: str = "single"
    required: bool = False
    aas_id_short: str = ""
    minimum: int = 0
    allowed_id_short: str = ""
    cardinality: str = ""

    def render(self, aliases: set[str]) -> str:
        types = list(self.types)
        if len(types) == 1 and types[0] == self.name:
            aliases.add(self.name)
            types[0] = f"{self.name}_t"
        annotation = types[0] if len(types) == 1 else f"Union[{', '.join(types)}]"
        if self.shape == "map":
            annotation = f"Dict[str, {annotation}]"
        elif self.shape == "list":
            annotation = f"List[{annotation}]"
        elif not self.required:
            annotation = f"Optional[{annotation}]"

        extra = {}
        if self.aas_id_short:
            extra["aas_id_short"] = self.aas_id_short
        if self.minimum:
            extra["idta_min_cardinality"] = self.minimum
        if self.allowed_id_short:
            extra["idta_allowed_id_short"] = self.allowed_id_short
        if self.cardinality:
            extra["idta_cardinality"] = self.cardinality
        if self.shape == "map":
            default = (f"_Field(default_factory=dict, json_schema_extra={json.dumps(extra)})"
                       if extra else "{}")
        elif self.shape == "list":
            default = "[]"
        elif extra:
            args = "" if self.required else "default=None, "
            default = f"_Field({args}json_schema_extra={json.dumps(extra)})"
        elif self.required:
            default = None
        else:
            default = "None"
        suffix = f" = {default}" if default is not None else ""
        return f"    {self.name}: {annotation}{suffix}"


def merge_fields(class_name: str, bodies: list, compatible=None) -> list[FieldSpec]:
    """Merge repeated definitions of one semantic container concept.

    Fields present in every variant stay required only when they are required
    in every variant. Dynamic maps and list fields keep their empty-container
    defaults when absent from another variant. Conflicting field types or
    repeatable metadata are rejected instead of silently choosing one variant.
    """
    variants = []
    field_order = []
    for body in bodies:
        fields = {}
        for field in body:
            if field.name in fields:
                raise ValueError(f"Duplicate field {class_name}.{field.name}")
            fields[field.name] = field
            if field.name not in field_order:
                field_order.append(field.name)
        variants.append(fields)

    merged = []
    for name in field_order:
        definitions = [variant[name] for variant in variants if name in variant]
        first = definitions[0]
        types = list(dict.fromkeys(t for spec in definitions for t in spec.types))
        if any(spec.shape != first.shape for spec in definitions) or (
            len({spec.types for spec in definitions}) > 1 and (
                first.shape != "single" or compatible is None or
                not all(compatible(types[0], candidate) for candidate in types[1:])
            )
        ):
            raise ValueError(
                f"Incompatible field types for {class_name}.{name}: "
                f"{', '.join(sorted(types))}"
            )
        if first.shape in ("map", "list"):
            if any((spec.aas_id_short, spec.minimum, spec.allowed_id_short, spec.cardinality) !=
                   (first.aas_id_short, first.minimum, first.allowed_id_short, first.cardinality)
                   for spec in definitions[1:]):
                raise ValueError(
                    f"Incompatible repeatable defaults for {class_name}.{name}"
                )
            merged.append(first)
            continue
        required_everywhere = (
            len(definitions) == len(variants)
            and all(spec.required for spec in definitions)
        )
        merged.append(FieldSpec(name, tuple(types), required=required_everywhere,
                                aas_id_short=first.aas_id_short,
                                minimum=first.minimum))
    return merged


def extract_semantic_id(el: dict) -> str:
    sem = el.get("semanticId") or {}
    for k in sem.get("keys", []) or []:
        if k.get("value"):
            return k.get("value", "")
    return ""


def extract_supplemental_semantic_ids(el: dict) -> list:
    """Supplemental semanticIds (list of IRIs) from ``supplementalSemanticIds``.
    These disambiguate elements that share a main semanticId — e.g. the AID
    ``InterfaceTemplateFor*`` all use ``.../Interface`` but each protocol has a
    unique supplemental IRI (per the IDTA PDF; the published JSON had OPC UA /
    BACnet copy-pasted from MQTT and is patched in the vendored copy)."""
    out = []
    for s in (el.get("supplementalSemanticIds") or []):
        for k in (s.get("keys") or []):
            if k.get("value"):
                out.append(k["value"])
    return out


def _lang_strings(value) -> list:
    if isinstance(value, dict):  # older exports: {"texts": [...]}
        value = value.get("texts")
    return [t for t in (value or []) if isinstance(t, dict) and t.get("text")]


def extract_description(el: dict) -> str:
    """The English description, else the first one (AAS JSON: [{"language": "en", "text": "..."}])."""
    texts = _lang_strings(el.get("description"))
    english = [t for t in texts if (t.get("language") or "").lower().startswith("en")]
    return (english or texts or [{}])[0].get("text", "")


def extract_display_name(el: dict) -> dict:
    return {t.get("language") or "en": t["text"] for t in _lang_strings(el.get("displayName"))}


def extract_value_type(el: dict) -> str:
    return el.get("valueType", "")


def metadata_lines(el: dict, *, include_empty_semantic_id: bool = True) -> list:
    """Class defaults common to leaves, containers, and list wrappers."""
    lines = id_short_default(el)
    sid = extract_semantic_id(el)
    if sid or include_empty_semantic_id:
        lines.append(f'    semantic_id: str = {json.dumps(sid)}')
    desc = extract_description(el)
    if desc:
        lines.append(f'    description: str = {json.dumps(desc)}')
    # The template's display name labels the template element (``Capability Set``), not an instance of it: an
    # instance named by its idShort would show that label in its place. The template export restores it.
    display_name = extract_display_name(el)
    if display_name:
        lines.append(f'    TEMPLATE_DISPLAY_NAME: ClassVar[Dict[str, str]] = '
                     f'{json.dumps(display_name, ensure_ascii=False)}')
    supp = extract_supplemental_semantic_ids(el)
    if supp:
        lines.append(f'    supplemental_semantic_ids: List[str] = {json.dumps(supp)}')
    return lines


# SMT/Cardinality values → the minimum number of instances, and whether more than one is allowed (a dynamic
# ``Dict[str, Element]`` map). A missing qualifier means ``One``.
_CARDINALITIES = {
    "One": (1, False), "ZeroToOne": (0, False),
    "ZeroToMany": (0, True), "OneToMany": (1, True), "TwoToMany": (2, True),
    "Recursive": (0, True),  # a recursive structure: unbounded nesting
}


def extract_cardinality(el: dict) -> str:
    """The element's ``SMT/Cardinality``. An unknown value, or the legacy ``Multiplicity`` qualifier (which older
    templates used instead), fails the run rather than silently making the element optional."""
    qualifiers = el.get("qualifiers") or []
    if any(q.get("type") == "Multiplicity" for q in qualifiers):
        raise ValueError(f"{el.get('idShort')!r} uses the legacy Multiplicity qualifier; use SMT/Cardinality")
    values = [(q.get("value") or "").strip() for q in qualifiers if q.get("type") == "SMT/Cardinality"]
    if len(values) > 1:
        raise ValueError(f"{el.get('idShort')!r} has {len(values)} SMT/Cardinality qualifiers (AASd-021)")
    if values and values[0] not in _CARDINALITIES:
        raise ValueError(f"{el.get('idShort')!r} has the unknown SMT/Cardinality {values[0]!r}")
    return values[0] if values else "One"


def _qualifier(el: dict, *types: str) -> str:
    return next(((q.get("value") or "").strip() for q in (el.get("qualifiers") or []) if q.get("type") in types), "")


def form_choices(el: dict) -> tuple:
    """The values a Property may take (``FormChoices`` ``a;b``, ``Enumeration`` ``a, b``)."""
    value = _qualifier(el, "FormChoices", "Enumeration")
    return tuple(v.strip() for v in re.split(r"[;,]", value) if v.strip()) if value else ()


def allowed_range(el: dict) -> tuple:
    """``SMT/AllowedRange`` ``[low, high]`` (integers, decimal or hexadecimal)."""
    match = re.fullmatch(r"\[\s*([^,\]]+?)\s*,\s*([^\]]+?)\s*\]", _qualifier(el, "SMT/AllowedRange"))
    return match.groups() if match else ()


def allowed_id_short(el: dict) -> str:
    """``AllowedIdShort`` as a regular expression. IDTA writes an optional part in brackets (``Time[\\d{2,3}]``:
    ``Time``, ``Time01``, …), which as a regex would be a character class."""
    value = _qualifier(el, "AllowedIdShort")
    return re.sub(r"\[(.+)\]$", r"(\1)?", value) if value else ""


def children_of(el: dict) -> list:
    return [
        c
        for c in (el.get("submodelElements") or el.get("value")
                  or el.get("statements") or [])
        if isinstance(c, dict)
    ]


_RESERVED_FIELDS = {
    "id", "id_short", "description", "display_name", "semantic_id",
    "supplemental_semantic_ids", "qualifiers", "entity_type", "global_asset_id",
    "type_value_list_element", "value_type_list_element",
    "semantic_id_list_element", "order_relevant", "value",
}


def element_field(name: str, raw: str, types: tuple[str, ...], *,
                  shape: str = "single", required: bool = False,
                  minimum: int = 0, allowed_id_short: str = "", cardinality: str = "") -> FieldSpec:
    """Represent a child before formatting its Python declaration."""
    renamed = field_name(raw) != raw and not _PLACEHOLDER.search(raw)
    return FieldSpec(name, types, shape=shape, required=required,
                     aas_id_short=raw if renamed else "", minimum=minimum,
                     allowed_id_short=allowed_id_short, cardinality=cardinality)


# Names a generated module imports; no generated class may take one.
_IMPORTED_NAMES = {
    "Any", "ClassVar", "Dict", "List", "Optional", "Union", "TypeAlias", "_Field", "AasIdString",
    "Submodel", "SubmodelElement", "SubmodelElementCollection", "DynamicSubmodelElementCollection",
    "SubmodelElementList", "Entity", *ELEMENT_MAP.values(),
}


def gen_template(template_path: str, output_dir: str):
    with open(template_path) as f:
        data = json.load(f)
    submodels = data.get("submodels", [])
    if not submodels:
        print(f"No submodels in {template_path}")
        return
    sm = submodels[0]
    sm_name = safe_name(sm["idShort"])

    # ── SemanticId-aware class naming ──
    # IDTA templates may use one id_short for several distinct element types
    # distinguished by semanticId (AID: ``properties`` = td#PropertyAffordance
    # vs json-schema#properties; ``property_name`` = PropertyDefinition vs
    # json-schema#propertyName; CCT: Type/Errors vs Skill/Errors).  The first
    # occurrence in document order keeps the plain class name (so every
    # top-level name stays stable — subclasses like mqtt_aid.py keep working);
    # later occurrences with a different semanticId get a disambiguated name
    # via :func:`sid_namespace_suffix`.  All template detail is preserved: the
    # id_short stays the field name and default instance id_short, and each
    # distinct semanticId lives on its own class.
    primary_sid = {}

    def _prescan_primary(el):
        if not isinstance(el, dict):
            return
        nm = safe_name(el.get("idShort", ""))
        if nm and el.get("modelType") in (
            "Submodel", "SubmodelElementCollection", "Entity", "SubmodelElementList",
        ):
            s = extract_semantic_id(el)
            if s and nm not in primary_sid:
                primary_sid[nm] = s
        for c in children_of(el):
            _prescan_primary(c)

    _prescan_primary(sm)

    # resolved class name → (base id_short, semanticId); guards uniqueness
    _name_identity = {}

    def check_class_name(name: str) -> None:
        if not name.isidentifier() or keyword.iskeyword(name):
            raise ValueError(f"Invalid class name from template idShort: {name!r}")

    def resolve_class_name(base: str, sid: str) -> str:
        """Class name for an element with id_short *base* and semanticId *sid*:
        plain name for the primary (document-first) occurrence, disambiguated
        otherwise.  Deterministic — the same (base, sid) always resolves to the
        same name, so recursion-stack lookups and definitions agree."""
        if sid == primary_sid.get(base, sid):
            cand = base
        else:
            suf = sid_namespace_suffix(base, sid)
            cand = f"{base}_{suf}" if suf else base
        i = 2
        c = cand
        while c in _name_identity and _name_identity[c] != (base, sid):
            c = f"{cand}_{i}"
            i += 1
        _name_identity.setdefault(c, (base, sid))
        return c

    # name → (meta_lines, body_lines); order of definition
    classes = {}
    class_body_variants = {}
    order = []
    entity_classes = set()
    sml_classes = set()
    leaf_bases = {}  # dedicated leaf element class name → base (leaf) class name
    leaf_identities = {}  # full definition (including metadata) → class name

    def register(name, meta, body, is_entity=False, is_sml=False):
        if name in leaf_bases or (
            name in classes and (is_entity != (name in entity_classes) or
                                 is_sml != (name in sml_classes))
        ):
            raise ValueError(f"Conflicting element types for generated class {name}")
        if name not in classes:
            classes[name] = (meta, body)
            class_body_variants[name] = [body]
            order.append(name)
        else:
            class_body_variants[name].append(body)
            classes[name] = (
                classes[name][0],
                merge_fields(
                    name, class_body_variants[name],
                    compatible=lambda a, b: all(
                        item in leaf_bases for item in (a, b)
                    ) and leaf_bases[a] == leaf_bases[b] and
                    _name_identity.get(a) == _name_identity.get(b),
                ),
            )
        if is_entity:
            entity_classes.add(name)
        if is_sml:
            sml_classes.add(name)

    def _disambiguated_leaf_name(base_name: str, sid: str, leaf_cls: str) -> str:
        """Unique class name for a leaf whose plain CamelCase name is owned by
        a DIFFERENT element (same id_short, different semanticId — e.g. CCI's
        ``Type``: ReferenceElement ``Instance/Type`` vs Property
        ``Skill/Parameter/Type``).  Uses the semanticId namespace suffix
        (``Type`` + ``.../Instance/Type/2/0`` → ``Type_instance``), then
        numeric dedup."""
        suf = sid_namespace_suffix(base_name, sid) or leaf_cls
        cand = f"{base_name}_{suf}"
        i = 2
        c = cand
        while c in leaf_bases or c in classes or (
            c in _name_identity and _name_identity[c] != (base_name, sid)
        ):
            c = f"{cand}_{i}"
            i += 1
        return c

    def leaf_class_for(c: dict, leaf_cls: str, name: str = "") -> str:
        """Register a leaf subclass for each distinct set of template defaults.

        Matching occurrences reuse a class; different semantic IDs, model
        types, or metadata receive disambiguated names. The authored Capability
        field retains its generic type for existing consumers.
        """
        sid = extract_semantic_id(c)
        elem_name = name or to_camel(safe_name(c.get("idShort", "")))
        # Capability is an author-supplied concept in existing subclasses;
        # specializing its field would reject authored Capability instances.
        if not elem_name or (elem_name == leaf_cls and leaf_cls == "Capability") or (
            not sid and not extract_description(c) and not extract_value_type(c)
            and not extract_supplemental_semantic_ids(c) and not extract_display_name(c)
            and not form_choices(c) and not allowed_range(c)
            and not (c.get("contentType") or c.get("content_type"))
        ):
            return leaf_cls
        check_class_name(elem_name)
        # A template's values are examples (a relationship's endpoints, a Property's value): an instance sets its
        # own, so none of them is a default. A File's or Blob's contentType is: an AIMC Transformation is text.
        meta = metadata_lines(c, include_empty_semantic_id=False)
        vt = extract_value_type(c)
        if vt and leaf_cls in ("Property", "Range"):
            meta.append(f'    value_type: str = {json.dumps(vt)}')
        ct = c.get("contentType") or c.get("content_type")
        if ct and leaf_cls in ("File", "Blob"):
            meta.append(f'    content_type: str = {json.dumps(ct)}')
        choices = form_choices(c)
        if choices and leaf_cls == "Property":
            meta.append(f"    FORM_CHOICES: ClassVar[tuple] = {choices!r}")
        bounds = allowed_range(c)
        if bounds and leaf_cls == "Property":
            meta.append(f"    ALLOWED_RANGE: ClassVar[tuple] = {bounds!r}")
        identity = (elem_name, sid, leaf_cls, tuple(meta))
        if identity in leaf_identities:
            return leaf_identities[identity]
        # The same element, described in one place only: one class, with the description.
        for (other_name, other_sid, other_cls, other_meta), existing in leaf_identities.items():
            if ((other_name, other_sid, other_cls, _structural(other_meta)) == (elem_name, sid, leaf_cls,
                                                                                _structural(meta))
                    and (set(other_meta) <= set(meta) or set(meta) <= set(other_meta))):
                merged = _with_descriptions(list(other_meta), meta)
                classes[existing] = (merged, classes[existing][1])
                leaf_identities[identity] = existing
                return existing
        if (elem_name == leaf_cls or elem_name in classes or
                (_name_identity.get(elem_name) is not None and
                 _name_identity[elem_name] != (elem_name, sid))):
            name = _disambiguated_leaf_name(elem_name, sid, leaf_cls)
        else:
            name = elem_name
        register(name, meta, [])
        leaf_bases[name] = leaf_cls
        leaf_identities[identity] = name
        # Reserve the name so a later container/leaf of the same base id_short
        # dedups (``SerialNumber_2``) instead of silently shadowing this class.
        _name_identity.setdefault(name, (elem_name, sid))
        return name

    def leaf_annotation(c: dict, cls: str) -> tuple[str, ...]:
        """Accept an existing authored primary leaf alongside its variant."""
        primary = to_camel(safe_name(c.get("idShort", "")))
        if primary == cls:
            return (cls,)
        if (primary != cls and primary in leaf_bases and cls in leaf_bases and
                leaf_bases[primary] == leaf_bases[cls] and
                _name_identity.get(primary) == _name_identity.get(cls)):
            return (cls, primary)
        return (cls,)

    def provisional(name: str, ctx: str) -> str:
        return f"{name}@{ctx}" if ctx else name

    def walk(el: dict, stack: tuple = (), name: str = None, ctx: str = "") -> list:
        """Register the ``{Name}`` container class for *el* with its children
        as DIRECT named fields (field name == id_short) — no ``value`` /
        ``submodel_element`` / ``statements`` wrapper (the standardized
        containers are abolished).

        Children whose template cardinality allows more than one
        (``SMT/Cardinality`` ZeroToMany/OneToMany) become dynamic
        ``Dict[str, Element]`` maps — MANY instances keyed by name.

        ``name`` overrides the class name (used for SML items whose template
        idShort is missing — falls back to ``{ListName}Item``).  ``stack``
        holds ``(id_short, semanticId, resolved_class_name)`` tuples of the
        elements currently being defined.  Recursion is detected by the pair
        (id_short, semanticId) — NOT the bare id_short — so a same-named child
        of a *different* semanticId (AID's nested object-schema ``properties``)
        is a real class, not a false recursion.  Recursive multi-cardinality
        children (HSEM ``Node`` in ``Node``) become empty ``Dict[str, Node]``
        maps; recursive single-cardinality children (AID's ``property_name`` →
        ``properties`` → ``property_name``) are optional (``Optional[X] =
        None``) so nesting stays representable without recursing forever.

        Single-cardinality children obey the template's ``SMT/Cardinality``:
        ``One`` (or a missing qualifier, which the templates use for mandatory
        elements) is required with NO default — pydantic rejects a constructed
        instance that omits it, so a mandatory element must be explicitly
        configured or the build fails; ``ZeroToOne`` is ``Optional[X] = None``
        and only present once set.
        """
        cname = resolve_class_name(name or safe_name(el.get("idShort", "")),
                                   extract_semantic_id(el))
        mt_el = el.get("modelType", "")
        check_class_name(cname)
        cname = provisional(cname, ctx)
        kids = children_of(el)
        stack_map = {(b, s): r for b, s, r in stack}
        fields = []
        field_id_shorts = {}
        alternatives = ALTERNATIVES.get(el.get("idShort", ""))
        one_of = []
        for c in kids:
            child_name = safe_name(c.get("idShort", ""))
            child_sid = extract_semantic_id(c)
            variant = alternatives.fullmatch(c.get("idShort", "")) if alternatives else None
            child_ctx = (variant.group(1) if variant and variant.groups() else ctx)
            child_resolved = provisional(resolve_class_name(child_name, child_sid), child_ctx)
            skey = field_name(c.get("idShort", child_name))  # field = id_short
            if skey in _RESERVED_FIELDS:
                raise ValueError(f"Child field reserved by AAS model: {skey} in {cname}")
            raw_name = c.get("idShort", child_name)
            if skey in field_id_shorts:
                raise ValueError(f"Duplicate or colliding idShorts in {cname}: {raw_name!r} and {field_id_shorts[skey]!r}")
            field_id_shorts[skey] = raw_name
            mt = c.get("modelType", "")
            if mt not in ELEMENT_MAP and mt not in (
                "SubmodelElementCollection", "Entity", "SubmodelElementList"
            ):
                raise ValueError(f"Unsupported modelType {mt!r} for {cname}.{skey}")
            if mt == "Operation" and any(c.get(k) for k in (
                "inputVariables", "outputVariables", "inoutputVariables", "inOutputVariables"
            )):
                raise ValueError(f"Operation variables are not supported for {cname}.{skey}")
            cardinality = extract_cardinality(c)
            minimum, multi = _CARDINALITIES[cardinality]
            recorded = cardinality if cardinality == "Recursive" else ""
            required = minimum > 0 and not multi
            if alternatives and alternatives.fullmatch(raw_name):
                required, minimum = False, 0
                one_of.append(skey)
            if multi:
                # multi-cardinality → dynamic name-keyed map of this element.
                # Generic-leaf elements get a dedicated subclass carrying the
                # concept semanticId (e.g. ``class SameAs(RelationshipElement)``
                # with ``semantic_id``) — back-conversion groups by the
                # resolved element class, so no ``_multi_cardinality`` ClassVar
                # is needed.
                if mt in ("SubmodelElementCollection", "Entity"):
                    if (child_name, child_sid) in stack_map:
                        # recursive child (e.g. HSEM Node in Node) — an empty
                        # Dict[str, <container>] map; no instantiation, so the
                        # default cannot recurse.
                        fields.append(element_field(
                            skey, raw_name, (stack_map[(child_name, child_sid)],),
                            shape="map", minimum=minimum, allowed_id_short=allowed_id_short(c),
                            cardinality=recorded,
                        ))
                        continue
                    walk(c, stack + ((child_name, child_sid, child_resolved),), ctx=child_ctx)
                    fields.append(element_field(skey, raw_name, (child_resolved,), shape="map",
                                                minimum=minimum, allowed_id_short=allowed_id_short(c), cardinality=recorded))
                elif mt == "SubmodelElementList":
                    _walk_sml(c, stack, child_ctx)
                    fields.append(element_field(skey, raw_name, (child_resolved,), shape="map",
                                                minimum=minimum, allowed_id_short=allowed_id_short(c), cardinality=recorded))
                else:
                    leaf_cls = ELEMENT_MAP.get(mt, "Property")
                    elem_cls = leaf_class_for(c, leaf_cls)
                    fields.append(element_field(skey, raw_name, (elem_cls,), shape="map",
                                                minimum=minimum, allowed_id_short=allowed_id_short(c), cardinality=recorded))
                continue
            if mt in ("SubmodelElementCollection", "Entity"):
                if (child_name, child_sid) in stack_map:
                    # Recursive single-cardinality child (AID object schema:
                    # ``property_name → properties → property_name``).  These
                    # are ZeroToOne in the templates — optional, so not
                    # instantiated unless set (this also breaks the recursion
                    # cleanly).
                    rec = stack_map[(child_name, child_sid)]
                    fields.append(element_field(skey, raw_name, (rec,)))
                    continue
                walk(c, stack + ((child_name, child_sid, child_resolved),), ctx=child_ctx)
                fields.append(element_field(skey, raw_name, (child_resolved,),
                                            required=required))
            elif mt == "SubmodelElementList":
                _walk_sml(c, stack, child_ctx)
                fields.append(element_field(skey, raw_name, (child_resolved,),
                                            required=required))
            else:
                leaf_cls = ELEMENT_MAP.get(mt, "Property")
                types = leaf_annotation(c, leaf_class_for(c, leaf_cls))
                fields.append(element_field(skey, raw_name, types,
                                            required=required))
        # container class: attributes (semantic_id, ...) + the typed child
        # fields directly (no ``value``/``submodel_element``/``statements``
        # wrapper).  Required children have NO default — pydantic enforces they
        # are provided.
        meta = metadata_lines(el)
        if one_of:
            meta.append(f"    IDTA_ONE_OF: ClassVar[tuple] = {tuple(one_of)!r}")
        is_entity = mt_el == "Entity"
        if is_entity:
            # Its globalAssetId is an example: the instance names its asset.
            meta.append(
                f'    entity_type: str = {json.dumps(el.get("entityType", "CoManagedEntity"))}'
            )
        register(cname, meta, fields, is_entity=is_entity)
        return fields

    def _walk_sml(c: dict, stack: tuple, ctx: str = ""):
        """Register an SML class with a typed ``value: List[Item]`` (AASd-108:
        homogeneous lists only — heterogeneous ones start empty)."""
        cname = resolve_class_name(safe_name(c.get("idShort", "")),
                                   extract_semantic_id(c))
        check_class_name(cname)
        cname = provisional(cname, ctx)
        item_kids = children_of(c)
        sub_meta = metadata_lines(c)
        declared_item = c.get("typeValueListElement")
        if declared_item:
            sub_meta.append(f'    type_value_list_element: str = {json.dumps(declared_item)}')
        declared_value_type = c.get("valueTypeListElement")
        if declared_value_type:
            sub_meta.append(f'    value_type_list_element: str = {json.dumps(declared_value_type)}')
        declared_sid = extract_semantic_id({"semanticId": c.get("semanticIdListElement")})
        if declared_sid:
            sub_meta.append(f'    semantic_id_list_element: str = {json.dumps(declared_sid)}')
        if "orderRelevant" in c:
            sub_meta.append(f'    order_relevant: bool = {bool(c["orderRelevant"])}')
        item_classes = set()  # for AASd-108 homogeneity check
        stack_map = {(b, s): r for b, s, r in stack}
        for item in item_kids:
            imt = item.get("modelType", "")
            if imt not in ELEMENT_MAP and imt not in (
                "SubmodelElementCollection", "Entity", "SubmodelElementList"
            ):
                raise ValueError(f"Unsupported list item modelType {imt!r} for {cname}")
            if imt in ("SubmodelElementCollection", "Entity"):
                item_name = safe_name(item.get("idShort", f"{cname.split('@')[0]}Item"))
                item_sid = extract_semantic_id(item)
                if (item_name, item_sid) in stack_map:
                    # Recursive item — skip entirely.
                    continue
                item_resolved = provisional(resolve_class_name(item_name, item_sid), ctx)
                walk(item, stack + ((item_name, item_sid, item_resolved),),
                     name=item_name, ctx=ctx)
                item_classes.add(item_resolved)
            elif imt == "SubmodelElementList":
                item_classes.add("SubmodelElementList")
            else:
                item_classes.add(ELEMENT_MAP[imt])
        if declared_item in ELEMENT_MAP and not any(
            item.get("modelType") in ("SubmodelElementCollection", "Entity")
            for item in item_kids
        ):
            item_classes = {ELEMENT_MAP[declared_item]}
        if len(item_classes) == 1 and next(iter(item_classes)) in ELEMENT_MAP.values():
            # Leaf items: a class of their own when the template describes them (a semanticId, a description,
            # the list's value type), named after the list.
            leaf_cls = next(iter(item_classes))
            example = next((item for item in item_kids if item.get("modelType") == leaf_cls), {})
            described = {**example, "valueType": example.get("valueType") or declared_value_type or ""}
            described.pop("idShort", None)
            item_classes = {leaf_class_for(described, leaf_cls, name=f"{cname.split('@')[0]}Item")}
        item_cardinality = next((_qualifier(item, "SMT/Cardinality") for item in item_kids), "")
        if item_cardinality:
            if item_cardinality not in _CARDINALITIES:
                raise ValueError(f"{cname}: its items have the unknown SMT/Cardinality {item_cardinality!r}")
            # How many items the list holds (``OneToMany``: at least one).
            sub_meta.append(f"    ITEM_CARDINALITY: ClassVar[str] = {item_cardinality!r}")
        if item_classes and len(item_classes) == 1:
            # Homogeneous list — declare item_type so back-conversion can
            # restore item types (AASd-114 strips item semanticIds in basyx),
            # but start EMPTY: the template's example items are empty
            # scaffolding and would leak into every generated instance (e.g.
            # nameplate ``Markings`` carrying an empty ``marking_name`` SMC).
            item_cls = next(iter(item_classes))
            sub_meta.append(f"    item_type: ClassVar = {item_cls}")
            sml_body = [FieldSpec("value", (item_cls,), shape="list")]
        else:
            # Heterogeneous or empty (e.g. CapabilityPropertyType lists
            # Range/Property/MLP exemplars) — basyx cannot represent a
            # mixed-type SML (AASd-108), so start empty; users populate it
            # with a homogeneous list.
            sml_body = [FieldSpec("value", ("Any",), shape="list")]
        register(cname, sub_meta, sml_body, is_sml=True)

    walk(sm)
    # The submodel's metadata as the walk registered it (with its IDTA_ONE_OF), plus its version.
    sm_meta = list(classes[sm_name][0])

    admin = sm.get("administration") or {}
    version, revision = admin.get("version"), admin.get("revision")
    if not (version and revision):
        # Unknown when the semanticId does not carry it either; never invented.
        match = re.search(r"/(\d+)/(\d+)(?:/Submodel)?$", extract_semantic_id(sm))
        version, revision = match.groups() if match else ("", "")
    sm_meta.append(f'    VERSION: ClassVar[str] = "{version}"')
    sm_meta.append(f'    REVISION: ClassVar[str] = "{revision}"')
    classes[sm_name] = (sm_meta, classes[sm_name][1])

    # ── Assemble file ──
    # Build the body first, then derive imports from the assembled text.
    body = []
    aliases_emitted = set()
    alias_definitions = []
    emitted, _ = _variant_classes(order, classes)
    kind_names = {name.split("@")[0] for name in entity_classes}, {name.split("@")[0] for name in sml_classes}
    shared_bases = {parent for _, parent, _, _ in emitted if parent}
    for name, parent, meta, cbody in emitted:
        if parent:
            base = parent
        elif name == sm_name:
            base = "Submodel"
        elif name in kind_names[0]:
            base = "Entity"
        elif name in kind_names[1]:
            base = "SubmodelElementList"
        elif name in leaf_bases:
            base = leaf_bases[name]
        elif not cbody and name not in shared_bases:
            # The template declares no children: an instance holds whatever elements it needs.
            base = "DynamicSubmodelElementCollection"
        else:
            base = "SubmodelElementCollection"
        if name in _IMPORTED_NAMES:
            raise ValueError(f"Generated class {name} would shadow an imported name")
        body.append(f"class {name}({base}):")
        body.extend(meta)
        if not cbody and not meta:
            body.append('    pass')
        for field in cbody:
            # Pydantic resolves a same-named annotation to the field itself.
            # Postponed annotations allow the alias to follow all classes.
            if (field.types == (field.name,) and
                    field.name not in aliases_emitted):
                alias_definitions.extend((
                    f"# alias so field ``{field.name}_t`` can name a class of the same id_short",
                    f"{field.name}_t: TypeAlias = {field.name}",
                ))
            body.append(field.render(aliases_emitted))
        body.append('')

    # Postponed annotations let aliases follow their definitions. This matters
    # for recursive/list graphs where a same-named referenced container is
    # registered later in document traversal order.
    body.extend(alias_definitions)

    body.append('# ── Resolve forward references (Pydantic circular refs) ──')
    for name, _, _, _ in emitted:
        body.append(f'{name}.model_rebuild()')
    body.append('')

    all_src = "\n".join(body)
    lines = []
    template_abs = os.path.abspath(template_path)
    relative_to = (
        TEMPLATE_ROOT
        if os.path.commonpath((TEMPLATE_ROOT, template_abs)) == TEMPLATE_ROOT
        else _ROOT
    )
    source_path = os.path.relpath(template_abs, relative_to)
    lines.append(f'"""{sm_name} - generated from IDTA template.')
    lines.append(f"Source: {source_path}")
    lines.append('"""')
    lines.append('')
    lines.append('from __future__ import annotations')
    lines.append('')
    # Import exactly the names the generated code uses.
    used = {t.string for t in tokenize.generate_tokens(io.StringIO(all_src).readline) if t.type == tokenize.NAME}
    typing_names = [n for n in ("Any", "ClassVar", "Dict", "List", "Optional", "TypeAlias", "Union") if n in used]
    lines.append(f"from typing import {', '.join(typing_names)}")
    lines.append('from aas_pydantic import (')
    imports = sorted(n for n in _IMPORTED_NAMES - {"Any", "ClassVar", "Dict", "List", "Optional", "Union",
                                                   "TypeAlias", "_Field", "AasIdString"} if n in used)
    lines.append('    ' + ', '.join(imports) + ',')
    lines.append(')')
    if "_Field(" in all_src:
        # Under a private name: a template may name an element ``field``.
        lines.append('from pydantic import Field as _Field')
    if ": AasIdString" in all_src:
        lines.append('from aas_pydantic.aas_model import AasIdString')
    lines.append('')

    lines.extend(body)

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"{snake(sm_name)}.py")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    print(f"✅ {out_path}")
    print(f"   {sm_name}(Submodel) + {len(emitted) - 1} classes")


if __name__ == "__main__":
    # Resolve relative to the aas-model repo root (scripts/ is one level down),
    # so this works from any working directory.
    if len(sys.argv) >= 2:
        tmpl = sys.argv[1]
        if not os.path.isabs(tmpl):
            tmpl = os.path.join(TEMPLATE_ROOT, tmpl)
        gen_template(tmpl, sys.argv[2] if len(sys.argv) > 2 else OUTPUT_ROOT)
    else:
        for template in TEMPLATES:
            gen_template(os.path.join(TEMPLATE_ROOT, template), OUTPUT_ROOT)
        print(f"\nGenerated {len(TEMPLATES)} templates into {OUTPUT_ROOT}")
