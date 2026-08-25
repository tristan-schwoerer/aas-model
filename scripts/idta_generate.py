#!/usr/bin/env python3
"""Generate aas_pydantic models from IDTA submodel template JSON.

Emits the basyx/IDTA-aligned container structure:

    Submodel:  submodel_element: Dict[str, SubmodelElement] = { child: Elem(...) }
    SMC:       value:            Dict[str, SubmodelElement] = { child: Elem(...) }
    SML:       value:            List[Any]                   = [ Item(...) ]

Child elements are pre-populated from the template's example element(s) as
typed instances, with all semantic_id / description / value_type metadata.
The dict key IS the child's id_short: every instance carries
``id_short=<key>`` so key == Python variable name == model id_short ==
basyx id_short (one canonical name per element).

There is no cardinality analysis, no field renames, no Pydantic name-collision
workarounds: the container structure makes the generator template-agnostic.
Subclasses may narrow the container element type, e.g.
``value: Dict[str, Parameter]`` (see the handwritten Variables/Parameters
submodels).
"""

import json
import keyword
import os
import re
import sys

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


def safe_name(name: str) -> str:
    # IDTA placeholders like ``Mode__00__`` mean "a repeatable instance whose
    # id_short the user picks" — strip the ``__NN__`` suffix so class and field
    # names are the clean base name (``Mode`` → field ``mode``).
    name = re.sub(r"__\d+__$", "", name or "")
    return re.sub(r"[^0-9a-zA-Z_]", "_", name)


def snake(name: str) -> str:
    s = re.sub(r"(?<!^)(?=[A-Z])", "_", name)
    return s.replace("-", "_").lower()


def field_name(name: str) -> str:
    """snake_case field name that is a valid Python identifier (reserved words
    get a trailing underscore, e.g. W3C ``in`` → ``in_``).  IDTA ``__NN__``
    placeholder suffixes (``Mode__00__``) are stripped first (→ ``mode``)."""
    name = re.sub(r"__\d+__$", "", name or "")
    s = snake(name)
    if keyword.iskeyword(s):
        s += "_"
    return s


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


_CLASH_RE = re.compile(r"^    (\w+): (\w+) = (\w+)\(")
_DICT_CLASH_RE = re.compile(r"^    (\w+): Dict\[str, (\w+)\] = \{\}")
_LAMBDA_CLASH_RE = re.compile(
    r"^    (\w+): (\w+) = Field\(default_factory=lambda: (\w+)\(\)\)$"
)
_OPT_CLASH_RE = re.compile(r"^    (\w+): Optional\[(\w+)\] = None$")
_REQUIRED_CLASH_RE = re.compile(r"^    (\w+): (\w+)$")


def _rewrite_clash_fields(body: list, aliases_emitted: set):
    """Rewrite values-class field lines where the field name equals its type
    annotation (pydantic rejects ``security: security = security()`` and
    crashes on the multi-cardinality ``property_name: Dict[str,
    property_name] = {}`` form — the field name == element class name makes
    pydantic's schema gather fail with ``KeyError: 'type'``).

    The type is aliased as a ``TypeAlias`` (``security_t: TypeAlias =
    security``) emitted once, before the first values class that needs it —
    the aliased class is always already defined at that point (child
    containers precede the parent values class in definition order)."""
    new_body = []
    alias_lines = []
    for line in body:
        m = _CLASH_RE.match(line)
        if m and m.group(1) == m.group(2) == m.group(3):
            t = m.group(1)
            alias = f"{t}_t"
            if alias not in aliases_emitted:
                aliases_emitted.add(alias)
                alias_lines.append(f"{alias}: TypeAlias = {t}")
            new_body.append(line.replace(f"{t}: {t} = {t}(", f"{t}: {alias} = {alias}("))
            continue
        m = _DICT_CLASH_RE.match(line)
        if m and m.group(1) == m.group(2):
            t = m.group(1)
            alias = f"{t}_t"
            if alias not in aliases_emitted:
                aliases_emitted.add(alias)
                alias_lines.append(f"{alias}: TypeAlias = {t}")
            new_body.append(line.replace(
                f"{t}: Dict[str, {t}] = {{}}",
                f"{t}: Dict[str, {alias}] = {{}}",
            ))
            continue
        # lazy lambda form produced for fields referencing recursive containers
        # (e.g. ``properties: properties = Field(default_factory=lambda:
        # properties())``) — same field-name/type clash, same alias fix.
        m = _LAMBDA_CLASH_RE.match(line)
        if m and m.group(1) == m.group(2) == m.group(3):
            t = m.group(1)
            alias = f"{t}_t"
            if alias not in aliases_emitted:
                aliases_emitted.add(alias)
                alias_lines.append(f"{alias}: TypeAlias = {t}")
            new_body.append(line.replace(
                f"{t}: {t} = Field(default_factory=lambda: {t}())",
                f"{t}: {alias} = Field(default_factory=lambda: {alias}())",
            ))
            continue
        # optional single-cardinality child whose field name equals its type
        # annotation (``enum: Optional[enum] = None``) — pydantic resolves the
        # self-referential name to NoneType, silently dropping the child.
        m = _OPT_CLASH_RE.match(line)
        if m and m.group(1) == m.group(2):
            t = m.group(1)
            alias = f"{t}_t"
            if alias not in aliases_emitted:
                aliases_emitted.add(alias)
                alias_lines.append(f"{alias}: TypeAlias = {t}")
            new_body.append(line.replace(
                f"{t}: Optional[{t}] = None",
                f"{t}: Optional[{alias}] = None",
            ))
            continue
        # required (no-default) single-cardinality child whose field name equals
        # its type annotation (``forms: forms``) — same self-reference clash,
        # same alias fix.
        m = _REQUIRED_CLASH_RE.match(line)
        if m and m.group(1) == m.group(2):
            t = m.group(1)
            alias = f"{t}_t"
            if alias not in aliases_emitted:
                aliases_emitted.add(alias)
                alias_lines.append(f"{alias}: TypeAlias = {t}")
            new_body.append(line.replace(
                f"{t}: {t}",
                f"{t}: {alias}",
            ))
            continue
        new_body.append(line)
    return new_body, alias_lines


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


def extract_description(el: dict) -> str:
    d = el.get("description")
    if isinstance(d, list):  # AAS JSON: [{"language": "en", "text": "..."}]
        return d[0].get("text", "") if d else ""
    if isinstance(d, dict):
        texts = d.get("texts") or []
        return texts[0].get("text", "") if texts else ""
    return ""


def extract_value_type(el: dict) -> str:
    return el.get("valueType", "")


def extract_cardinality(el: dict) -> str:
    """Cardinality qualifier value (e.g. ``ZeroToMany``, ``ZeroToOne``, ``One``)
    — how many instances of this element a container may hold.

    Templates encode it under the standard qualifier ``type``
    ``SMT/Cardinality``."""
    for q in (el.get("qualifiers") or []):
        if q.get("type") == "SMT/Cardinality":
            return (q.get("value") or "").strip()
    return ""


# Cardinalities that allow more than one instance of an element → the
# values model field becomes a dynamic ``Dict[str, Element]`` (name-keyed),
# so MANY instances are possible — exactly like the pre-values-model dicts.
_MULTI_CARDINALITY = {
    "ZeroToMany", "OneToMany",  # standard SMT encodings
    "TwoToMany", "Three",       # other >1 encodings in the wild
    "Recursive",                # recursive structures allow unbounded nesting
}


def emit_reference(ref: dict, indent: str) -> list:
    """Source lines constructing a pydantic Reference from an AAS JSON
    reference dict (``{"type": ..., "keys": [...]}``)."""
    cls = "ModelReference" if ref.get("type") == "ModelReference" else "ExternalReference"
    key_src = [
        f'{indent}        Key(type_={json.dumps(k.get("type", ""))}, '
        f'value={json.dumps(k.get("value", ""))}),'
        for k in (ref.get("keys") or [])
    ]
    lines = [f"{indent}{cls}("]
    if key_src:
        lines.append(f"{indent}    key=(")
        lines.extend(key_src)
        lines.append(f"{indent}    ),")
    lines.append(f"{indent})")
    return lines


def is_placeholder_endpoint(ref) -> bool:
    """True when a RelationshipElement endpoint is a template placeholder.

    Several templates (e.g. HSEM ``SameAs``) declare ``first``/``second`` as a
    ``ModelReference`` whose only key is a ``GlobalReference`` "EMPTY" — a
    ModelReference's FIRST key must be an Identifiable (AASd-123), so such
    endpoints carry no real target and would make the generated class fail
    validation at import.  Skip them (endpoints stay unset/None).
    """
    if not isinstance(ref, dict):
        return True
    if ref.get("type") == "ModelReference":
        keys = ref.get("keys") or []
        if keys and keys[0].get("type") == "GlobalReference":
            return True
    return False


def emit_leaf_instance(el: dict, indent: str) -> list:
    """Source lines constructing a leaf element instance.

    No ``id_short`` is emitted — the dict key is the single source of truth
    for the id_short (stamped at the container boundary on construction).
    """
    mt = el.get("modelType", "Property")
    cls = ELEMENT_MAP.get(mt, "Property")
    lines = [f"{indent}{cls}("]
    args = []
    sid = extract_semantic_id(el)
    desc = extract_description(el)
    vt = extract_value_type(el)
    ct = el.get("contentType") or el.get("content_type")
    if sid:
        args.append(f'semantic_id={json.dumps(sid)}')
    if desc:
        args.append(f'description={json.dumps(desc)}')
    if vt and cls in ("Property", "Range"):
        args.append(f'value_type={json.dumps(vt)}')
    if ct and cls in ("File", "Blob"):
        # File/Blob need a content type — basyx rejects empty content types
        # (and the converter drops Blobs without one).
        args.append(f'content_type={json.dumps(ct)}')
    for i, a in enumerate(args):
        lines.append(f"{indent}    {a}{',' if i < len(args) - 1 else ','}")
    if cls == "RelationshipElement":
        # Endpoints are References in basyx — emit the template's reference.
        for key_name in ("first", "second"):
            ref = el.get(key_name)
            if isinstance(ref, dict) and not is_placeholder_endpoint(ref):
                ref_src = emit_reference(ref, indent + "    ")
                lines.append(f"{indent}    {key_name}=" + ref_src[0].lstrip())
                lines.extend(ref_src[1:])
                lines[-1] = lines[-1] + ","
    lines.append(f"{indent})")
    return lines


def children_of(el: dict) -> list:
    return [
        c
        for c in (el.get("submodelElements") or el.get("value")
                  or el.get("statements") or [])
        if isinstance(c, dict)
    ]


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
    order = []
    entity_classes = set()
    sml_classes = set()
    leaf_bases = {}  # dedicated leaf element class name → base (leaf) class name
    _used_leaf_types = {
        "Submodel", "SubmodelElement", "SubmodelElementCollection",
        "SubmodelElementList",
    }

    def register(name, meta, body, is_entity=False, is_sml=False):
        if name not in classes:
            classes[name] = (meta, body)
            order.append(name)
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

    def leaf_class_for(c: dict, leaf_cls: str) -> str:
        """Register (once) a dedicated subclass of *leaf_cls* carrying the
        element's template defaults — concept semanticId, description,
        supplemental semanticIds, ``value_type`` (Property/Range),
        ``content_type`` (File/Blob), and RelationshipElement endpoints —
        and return its name.

        The class name is the CamelCased id_short (``year_of_construction`` →
        ``YearOfConstruction``).  Class-level defaults survive ANY construction
        path (config dict, partial instance, converter) because pydantic
        validates against the class instead of discarding an instance default.

        A dedicated leaf class is REUSED only when the same (id_short,
        semanticId, base type) recurs; a same-named leaf with a DIFFERENT
        semanticId or modelType gets its own disambiguated class (e.g. CCI
        ``Type`` → ``Type`` Property + ``Type_instance`` ReferenceElement).
        Falls back to the generic *leaf_cls* only when there is no concept
        semanticId or the element has no idShort."""
        sid = extract_semantic_id(c)
        elem_name = to_camel(safe_name(c.get("idShort", "")))
        if not sid or not elem_name or elem_name == leaf_cls:
            return leaf_cls
        if elem_name in leaf_bases:
            # Reuse ONLY the identical (semanticId, base type); otherwise the
            # plain name belongs to a *different* element's class.
            existing = _name_identity.get(elem_name)
            if existing == (elem_name, sid) and leaf_bases[elem_name] == leaf_cls:
                return elem_name
            name = _disambiguated_leaf_name(elem_name, sid, leaf_cls)
        elif elem_name in classes:
            # Plain name owned by a container — keep the leaf's concept
            # semanticId on its own disambiguated class instead of degrading
            # to the generic leaf.
            name = _disambiguated_leaf_name(elem_name, sid, leaf_cls)
        else:
            identity = _name_identity.get(elem_name)
            if identity is not None and identity != (elem_name, sid):
                name = _disambiguated_leaf_name(elem_name, sid, leaf_cls)
            else:
                name = elem_name
        meta = [f'    semantic_id: str = {json.dumps(sid)}']
        desc = extract_description(c)
        if desc:
            meta.append(f'    description: str = {json.dumps(desc)}')
        supp = extract_supplemental_semantic_ids(c)
        if supp:
            meta.append(f'    supplemental_semantic_ids: List[str] = {json.dumps(supp)}')
        vt = extract_value_type(c)
        if vt and leaf_cls in ("Property", "Range"):
            meta.append(f'    value_type: str = {json.dumps(vt)}')
        ct = c.get("contentType") or c.get("content_type")
        if ct and leaf_cls in ("File", "Blob"):
            meta.append(f'    content_type: str = {json.dumps(ct)}')
        if leaf_cls == "RelationshipElement":
            for key_name in ("first", "second"):
                ref = c.get(key_name)
                if isinstance(ref, dict) and not is_placeholder_endpoint(ref):
                    ref_src = emit_reference(ref, "    ")
                    ref_cls = ref_src[0].lstrip().rstrip("(").strip()
                    meta.append(f"    {key_name}: {ref_cls} = " + ref_src[0].lstrip())
                    meta.extend(ref_src[1:])
                    meta[-1] = meta[-1] + ","
        register(name, meta, [])
        leaf_bases[name] = leaf_cls
        # Reserve the name so a later container/leaf of the same base id_short
        # dedups (``SerialNumber_2``) instead of silently shadowing this class.
        _name_identity.setdefault(name, (elem_name, sid))
        return name

    def walk(el: dict, stack: tuple = (), name: str = None) -> list:
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
        kids = children_of(el)
        stack_map = {(b, s): r for b, s, r in stack}
        lines = []
        for c in kids:
            child_name = safe_name(c.get("idShort", ""))
            child_sid = extract_semantic_id(c)
            child_resolved = resolve_class_name(child_name, child_sid)
            skey = field_name(c.get("idShort", child_name))  # field = id_short
            mt = c.get("modelType", "")
            card = extract_cardinality(c)
            multi = card in _MULTI_CARDINALITY
            # A missing ``SMT/Cardinality`` qualifier defaults to ``One`` — the
            # element is mandatory (the only missing-qualifier cases in the
            # templates are ``forms`` / ``fileName`` / ``definesSecurityScheme``
            # / ``iolv_payloadMappingElement``).
            required = card in ("One", None, "")
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
                        lines.append(
                            f"    {skey}: Dict[str, {stack_map[(child_name, child_sid)]}] = {{}}"
                        )
                        continue
                    walk(c, stack + ((child_name, child_sid, child_resolved),))
                    lines.append(f"    {skey}: Dict[str, {child_resolved}] = {{}}")
                elif mt == "SubmodelElementList":
                    _walk_sml(c, stack)
                    lines.append(f"    {skey}: Dict[str, {child_resolved}] = {{}}")
                else:
                    leaf_cls = ELEMENT_MAP.get(mt, "Property")
                    _used_leaf_types.add(leaf_cls)
                    elem_cls = leaf_class_for(c, leaf_cls)
                    lines.append(f"    {skey}: Dict[str, {elem_cls}] = {{}}")
                continue
            if mt in ("SubmodelElementCollection", "Entity"):
                if (child_name, child_sid) in stack_map:
                    # Recursive single-cardinality child (AID object schema:
                    # ``property_name → properties → property_name``).  These
                    # are ZeroToOne in the templates — optional, so not
                    # instantiated unless set (this also breaks the recursion
                    # cleanly).
                    rec = stack_map[(child_name, child_sid)]
                    lines.append(f"    {skey}: Optional[{rec}] = None")
                    continue
                walk(c, stack + ((child_name, child_sid, child_resolved),))
                if required:
                    lines.append(f"    {skey}: {child_resolved}")
                else:
                    lines.append(f"    {skey}: Optional[{child_resolved}] = None")
            elif mt == "SubmodelElementList":
                _walk_sml(c, stack)
                if required:
                    lines.append(f"    {skey}: {child_resolved}")
                else:
                    lines.append(f"    {skey}: Optional[{child_resolved}] = None")
            else:
                leaf_cls = ELEMENT_MAP.get(mt, "Property")
                _used_leaf_types.add(leaf_cls)
                elem_cls = leaf_class_for(c, leaf_cls)
                if required:
                    lines.append(f"    {skey}: {elem_cls}")
                else:
                    lines.append(f"    {skey}: Optional[{elem_cls}] = None")
        if not lines:
            lines.append("    pass")
        # container class: attributes (semantic_id, ...) + the typed child
        # fields directly (no ``value``/``submodel_element``/``statements``
        # wrapper).  Required children have NO default — pydantic enforces they
        # are provided.
        meta = [f'    semantic_id: str = {json.dumps(extract_semantic_id(el))}']
        desc = extract_description(el)
        if desc:
            meta.append(f'    description: str = {json.dumps(desc)}')
        supp = extract_supplemental_semantic_ids(el)
        if supp:
            meta.append(f'    supplemental_semantic_ids: List[str] = {json.dumps(supp)}')
        is_entity = mt_el == "Entity"
        if is_entity:
            _used_leaf_types.add("Entity")
            meta.append(
                f'    entity_type: str = {json.dumps(el.get("entityType", "CoManagedEntity"))}'
            )
            gid = el.get("globalAssetId")
            if gid:
                meta.append(f'    global_asset_id: str = {json.dumps(gid)}')
        register(cname, meta, lines, is_entity=is_entity)
        return lines

    def _walk_sml(c: dict, stack: tuple):
        """Register an SML class with a typed ``value: List[Item]`` (AASd-108:
        homogeneous lists only — heterogeneous ones start empty)."""
        cname = resolve_class_name(safe_name(c.get("idShort", "")),
                                   extract_semantic_id(c))
        item_kids = children_of(c)
        sub_meta = [f'    semantic_id: str = {json.dumps(extract_semantic_id(c))}']
        desc = extract_description(c)
        if desc:
            sub_meta.append(f'    description: str = {json.dumps(desc)}')
        supp = extract_supplemental_semantic_ids(c)
        if supp:
            sub_meta.append(f'    supplemental_semantic_ids: List[str] = {json.dumps(supp)}')
        item_classes = set()  # for AASd-108 homogeneity check
        stack_map = {(b, s): r for b, s, r in stack}
        for item in item_kids:
            imt = item.get("modelType", "")
            if imt in ("SubmodelElementCollection", "Entity"):
                item_name = safe_name(item.get("idShort", f"{cname}Item"))
                item_sid = extract_semantic_id(item)
                if (item_name, item_sid) in stack_map:
                    # Recursive item — skip entirely.
                    continue
                item_resolved = resolve_class_name(item_name, item_sid)
                walk(item, stack + ((item_name, item_sid, item_resolved),),
                     name=item_name)
                item_classes.add(item_resolved)
            else:
                leaf_cls = ELEMENT_MAP.get(imt, "Property")
                _used_leaf_types.add(leaf_cls)
                item_classes.add(leaf_cls)
        if item_classes and len(item_classes) == 1:
            # Homogeneous list — declare item_type so back-conversion can
            # restore item types (AASd-114 strips item semanticIds in basyx),
            # but start EMPTY: the template's example items are empty
            # scaffolding and would leak into every generated instance (e.g.
            # nameplate ``Markings`` carrying an empty ``marking_name`` SMC).
            item_cls = next(iter(item_classes))
            sub_meta.append(f"    item_type: ClassVar = {item_cls}")
            sml_body = [f"    value: List[{item_cls}] = []"]
        else:
            # Heterogeneous or empty (e.g. CapabilityPropertyType lists
            # Range/Property/MLP exemplars) — basyx cannot represent a
            # mixed-type SML (AASd-108), so start empty; users populate it
            # with a homogeneous list.
            sml_body = ["    value: List[Any] = []"]
        register(cname, sub_meta, sml_body, is_sml=True)

    sm_meta = [f'    semantic_id: str = {json.dumps(extract_semantic_id(sm))}']
    desc = extract_description(sm)
    if desc:
        sm_meta.append(f'    description: str = {json.dumps(desc)}')
    walk(sm)

    admin = sm.get("administration", {})
    sm_meta.append(f'    VERSION: ClassVar[str] = "{admin.get("version", "1")}"')
    sm_meta.append(f'    REVISION: ClassVar[str] = "{admin.get("revision", "0")}"')
    # prepend the Submodel-level meta (walk registered semantic_id/description)
    existing = classes[sm_name][0]
    classes[sm_name] = (sm_meta, classes[sm_name][1])

    # ── Assemble file ──
    # Build the body first (clash aliases are emitted during assembly), then
    # derive the imports from the assembled text so nothing is missed.
    body = []
    aliases_emitted = set()
    for name in order:
        meta, cbody = classes[name]
        if name == sm_name:
            base = "Submodel"
        elif name in entity_classes:
            base = "Entity"
        elif name in sml_classes:
            base = "SubmodelElementList"
        elif name in leaf_bases:
            base = leaf_bases[name]
        else:
            base = "SubmodelElementCollection"
        # pydantic rejects a field whose name equals its type annotation
        # (e.g. ``items: items``) — alias the type as a TypeAlias, emitted
        # once, before the first class needing it.  The aliased class is
        # always already defined at that point (children precede the parent
        # container in order).
        cbody, alias_lines = _rewrite_clash_fields(cbody, aliases_emitted)
        for a in alias_lines:
            body.append(f"# alias so field ``{a.split(':')[0]}`` can name a class of the same id_short")
            body.append(f"{a}")
        body.append(f"class {name}({base}):")
        body.extend(meta)
        body.extend(cbody)
        body.append('')

    body.append('# ── Resolve forward references (Pydantic circular refs) ──')
    for name in order:
        body.append(f'{name}.model_rebuild()')
    body.append('')

    all_src = "\n".join(body)
    lines = []
    lines.append(f'"""{sm_name} — generated from IDTA template."""')
    lines.append('')
    lines.append('from __future__ import annotations')
    lines.append('')
    typing_names = ["Any", "ClassVar", "List"]
    if "Dict[" in all_src:
        typing_names.append("Dict")
    if "Optional[" in all_src:
        typing_names.append("Optional")
    if ": TypeAlias" in all_src:
        typing_names.append("TypeAlias")
    lines.append(f"from typing import {', '.join(typing_names)}")
    lines.append('from aas_pydantic import (')
    aas_types = {"Submodel", "SubmodelElement", "SubmodelElementCollection",
                 "SubmodelElementList", "Entity", "Qualifier",
                 "ExternalReference", "ModelReference", "Key"}
    aas_types |= set(ELEMENT_MAP.values())
    imports = sorted(t for t in _used_leaf_types if t in aas_types)
    # Reference endpoints (first/second) use ExternalReference/ModelReference/Key.
    if "ExternalReference(" in all_src:
        imports = sorted(set(imports) | {"ExternalReference", "Key"})
    if "ModelReference(" in all_src:
        imports = sorted(set(imports) | {"ModelReference", "Key"})
    lines.append('    ' + ', '.join(imports) + ',')
    lines.append(')')
    if "Field(default_factory" in all_src:
        lines.append('from pydantic import Field')
    lines.append('')

    lines.extend(body)

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"{snake(sm_name)}.py")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    print(f"✅ {out_path}")
    print(f"   {sm_name}(Submodel) + {len(order) - 1} classes")


if __name__ == "__main__":
    # Resolve relative to the aas-model repo root (scripts/ is one level down),
    # so this works from any working directory.
    _ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _TMPL_ROOT = os.path.join(_ROOT, "submodel-templates", "published")
    _OUT_ROOT = os.path.join(_ROOT, "src", "aas_pydantic", "submodel_templates")

    if len(sys.argv) >= 2:
        tmpl = sys.argv[1]
        if not os.path.isabs(tmpl):
            tmpl = os.path.join(_TMPL_ROOT, tmpl)
        gen_template(tmpl, sys.argv[2] if len(sys.argv) > 2 else _OUT_ROOT)
    else:
        TEMPLATES = [
            ("Capability Description/1/0/IDTA 02020_Template_Capability_Description.json",),
            ("Control Component Instance/2/0/1/IDTA 02016-2-0-1 _Template_ControlComponentInstance_forAASMetamodelV3.1.json",),
            ("Control Component Type/2/0/1/IDTA 02015-2-0-1 _Template_ControlComponentType_forAASMetamodelV3.1.json",),
            ("Hierarchical Structures enabling Bills of Material/1/1/1/IDTA 02011-1-1-1_Template_HSEBoM_forAASMetamodelV3.1.json",),
            ("Digital nameplate/3/0/1/IDTA 02006-3-0-1_Template_Digital Nameplate.json",),
            ("Asset Interfaces Mapping Configuration/2/0/IDTA 02027_Template_AIMC.json",),
            ("Asset Interfaces Description/1/1/IDTA 02017-1-1_Template_Asset Interfaces Description.json",),
        ]
        n = 0
        for rel in TEMPLATES:
            tmpl_path = os.path.join(_TMPL_ROOT, rel[0])
            if not os.path.exists(tmpl_path):
                print(f"⚠️  Skipping missing template: {tmpl_path}")
                continue
            gen_template(tmpl_path, _OUT_ROOT)
            n += 1
        print(f"\n✅ Generated {n} templates into {_OUT_ROOT}")
