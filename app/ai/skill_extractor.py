"""OWNER: M3 - rule-based skill extraction (works without any AI).

Matches skill names + aliases inside free text using whole-word, case-insensitive regex.
Skill names coming from the DB (M1's `skills` table) are merged with the built-in knowledge base.
"""
import re
from typing import Dict, Iterable, List, Optional

from app.ai.knowledge import SKILLS


def _alias_pattern(alias: str) -> "re.Pattern":
    # whole-word match that also works for names with symbols (C++, CI/CD, Node.js)
    return re.compile(r"(?<![A-Za-z0-9])" + re.escape(alias) + r"(?![A-Za-z0-9])", re.IGNORECASE)


# alias (lowercase) -> canonical key (lowercase skill name)
_ALIAS_TO_KEY: Dict[str, str] = {}
for _name, _info in SKILLS.items():
    _ALIAS_TO_KEY[_name.lower()] = _name.lower()
    for _a in _info["aliases"]:
        _ALIAS_TO_KEY[_a.lower()] = _name.lower()


def canonical_key(name: str) -> str:
    """'K8s' -> 'kubernetes', 'fast api' -> 'fastapi', unknown -> lowercase text."""
    key = (name or "").strip().lower()
    return _ALIAS_TO_KEY.get(key, key)


def build_catalog(extra_skills: Optional[Iterable[str]] = None) -> Dict[str, dict]:
    """Return {key: {"name", "category", "patterns": [compiled...]}} (built-in + extra skill names)."""
    catalog: Dict[str, dict] = {}
    for name, info in SKILLS.items():
        aliases = {name.lower(), *[a.lower() for a in info["aliases"]]}
        catalog[name.lower()] = {"name": name, "category": info["category"], "aliases": aliases}
    for raw in extra_skills or []:
        raw = (raw or "").strip()
        if not raw:
            continue
        key = canonical_key(raw)
        if key in catalog:
            catalog[key]["aliases"].add(raw.lower())
        else:
            catalog[key] = {"name": raw, "category": "other", "aliases": {raw.lower()}}
    for entry in catalog.values():
        # longest alias first so "rest assured" wins over shorter ones
        entry["patterns"] = [_alias_pattern(a) for a in sorted(entry["aliases"], key=len, reverse=True)]
    return catalog


def find_mentions(text: str, catalog: Dict[str, dict]) -> List[dict]:
    """[{key, name, category, count, first_pos}] sorted by first appearance."""
    found = []
    for key, entry in catalog.items():
        count, first = 0, None
        for pat in entry["patterns"]:
            for m in pat.finditer(text):
                count += 1
                first = m.start() if first is None else min(first, m.start())
        if count:
            found.append({"key": key, "name": entry["name"], "category": entry["category"],
                          "count": count, "first_pos": first})
    found.sort(key=lambda d: d["first_pos"])
    return found


def extract_skills(text: str, known_skills: Optional[Iterable[str]] = None) -> List[str]:
    """Skill names found in `text`, in order of first appearance."""
    if not text:
        return []
    return [m["name"] for m in find_mentions(text, build_catalog(known_skills))]


def topics_for(skill_name: str) -> List[str]:
    key = canonical_key(skill_name)
    for name, info in SKILLS.items():
        if name.lower() == key:
            return list(info["topics"])
    return []
