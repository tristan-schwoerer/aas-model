"""The shape of a submodel template in AAS JSON: what the generator reads from it and the template export writes
back, so the two can be compared."""

from __future__ import annotations

import re

# Qualifiers that define an element (the generator keeps them); the others are notes for template editors.
DEFINING = ("SMT/Cardinality", "FormChoices", "Enumeration", "SMT/AllowedRange", "AllowedIdShort")
_PLACEHOLDER = re.compile(r"(__\d+__|\{\d+\})$")


def _keys(reference) -> str:
    return "".join(k.get("value", "") for k in (reference or {}).get("keys") or [])


def _english(texts) -> str:
    texts = [t for t in (texts or []) if t.get("text")]
    english = [t for t in texts if (t.get("language") or "").lower().startswith("en")]
    return (english or texts or [{}])[0].get("text", "")


_CONTAINERS = ("Submodel", "SubmodelElementCollection", "SubmodelElementList", "Entity")


def _children(element) -> list:
    if element.get("modelType") not in _CONTAINERS:
        return []  # a MultiLanguageProperty's value is a list too
    value = element.get("submodelElements") or element.get("statements") or element.get("value")
    return [c for c in value if isinstance(c, dict)] if isinstance(value, list) else []


def shape(element: dict) -> dict:
    """An element's defining parts, its children keyed by idShort (a placeholder suffix dropped) or list
    position."""
    qualifiers = {q.get("type"): (q.get("value") or "").strip() for q in element.get("qualifiers") or []
                  if q.get("type") in DEFINING}
    if "Enumeration" in qualifiers:
        qualifiers["FormChoices"] = ";".join(v.strip() for v in re.split(r"[;,]", qualifiers.pop("Enumeration")))
    if element.get("modelType") == "Submodel":
        qualifiers = {}  # whether an AAS holds the submodel is no part of the template
    else:
        qualifiers.setdefault("SMT/Cardinality", "One")
    if "FormChoices" in qualifiers:
        qualifiers["FormChoices"] = ";".join(v.strip() for v in qualifiers["FormChoices"].split(";"))
    if "SMT/AllowedRange" in qualifiers:
        qualifiers["SMT/AllowedRange"] = re.sub(r"\s+", "", qualifiers["SMT/AllowedRange"])
    children = _children(element)
    in_list = element.get("modelType") == "SubmodelElementList"
    return {
        "modelType": element.get("modelType"),
        "semanticId": _keys(element.get("semanticId")),
        "supplementalSemanticIds": sorted(_keys(s) for s in element.get("supplementalSemanticIds") or []),
        "description": _english(element.get("description")),
        "displayName": _english(element.get("displayName")),
        "valueType": element.get("valueType", ""),
        "typeValueListElement": element.get("typeValueListElement", ""),
        "valueTypeListElement": element.get("valueTypeListElement", ""),
        "semanticIdListElement": _keys(element.get("semanticIdListElement")),
        "qualifiers": qualifiers,
        "children": {(str(i) if in_list else _PLACEHOLDER.sub("", c.get("idShort", ""))): shape(c)
                     for i, c in enumerate(children)},
    }


def differences(expected: dict, actual: dict, path: str = "") -> list[str]:
    """Where two shapes differ, as ``path: what``."""
    found = []
    for key in expected.keys() - {"children"}:
        if expected[key] != actual.get(key):
            found.append(f"{path or '/'}: {key} {expected[key]!r} != {actual.get(key)!r}")
    ours, theirs = expected.get("children", {}), actual.get("children", {})
    for name in ours.keys() - theirs.keys():
        found.append(f"{path}/{name}: missing")
    for name in theirs.keys() - ours.keys():
        found.append(f"{path}/{name}: extra")
    for name in ours.keys() & theirs.keys():
        found.extend(differences(ours[name], theirs[name], f"{path}/{name}"))
    return found
