"""Shared utilities for aas_pydantic code generators."""

import json
import re
import keyword
import builtins

# ── Python identifier safety ──────────────────────────────────────────
_RESERVED = set(dir(builtins)) | set(keyword.kwlist)


def safe_name(name: str) -> str:
    """Append underscore if name collides with Python keyword or builtin."""
    if name in _RESERVED:
        return f"{name}_"
    return name


def snake(name: str) -> str:
    """CamelCase → snake_case, with Python keyword safety."""
    result = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    return safe_name(result)


def format_py(val):
    """Format a Python value as a repr/JSON literal."""
    if isinstance(val, str):
        return json.dumps(val)
    if isinstance(val, list):
        return json.dumps(val)
    return repr(val)


# ── IDTA template helpers ─────────────────────────────────────────────

def extract_semantic_id(el: dict) -> str:
    sid = el.get("semanticId", {})
    keys = sid.get("keys", [])
    return keys[0]["value"] if keys else ""


def extract_qualifiers(el: dict) -> list:
    """Return list of Qualifier constructor call strings."""
    quals = el.get("qualifiers", el.get("qualifier", []))
    if not isinstance(quals, list):
        return []
    result = []
    for q in quals:
        qtype = q.get("type", "")
        qval = q.get("value", "")
        qsid = extract_semantic_id(q)
        if qsid:
            result.append(f'Qualifier(type_={json.dumps(qtype)}, value={json.dumps(qval)}, semantic_id={json.dumps(qsid)})')
        else:
            result.append(f'Qualifier(type_={json.dumps(qtype)}, value={json.dumps(qval)})')
    return result


def extract_qualifiers_dict(el: dict) -> list:
    """Return list of raw qualifier dicts."""
    quals = el.get("qualifiers", el.get("qualifier", []))
    if not isinstance(quals, list):
        return []
    result = []
    for q in quals:
        d = {"type": q.get("type", ""), "value": q.get("value", "")}
        qsid = extract_semantic_id(q)
        if qsid:
            d["semantic_id"] = qsid
        result.append(d)
    return result


def extract_description(el: dict) -> str:
    """Extract English description from an IDTA element."""
    desc = el.get("description", "")
    if isinstance(desc, list):
        for d in desc:
            if d.get("language") == "en":
                return d.get("text", "")
    return desc if isinstance(desc, str) else ""


def extract_supplemental(el: dict) -> list:
    """Extract supplemental semantic IDs."""
    suppl = el.get("supplementalSemanticId", [])
    if isinstance(suppl, list):
        return [s.get("keys", [{}])[0].get("value", "") for s in suppl if s.get("keys")]
    return []
