"""OWNER: M3 - rule-based Job Description analyzer (pure python, no DB, no AI).

analyze_jd(text) ->
  {skills[{name, category, importance, mentions, score}], required_skills, preferred_skills,
   tools, experience{min,max,text}, responsibilities, interview_topics[{skill, topics}], source}
"""
import re
from typing import Iterable, List, Optional

from app.ai.knowledge import TOOL_CATEGORIES
from app.ai.skill_extractor import build_catalog, find_mentions, topics_for

PREFERRED_RE = re.compile(
    r"\b(preferred|nice[- ]to[- ]have|good[- ]to[- ]have|bonus|added advantage|an advantage|"
    r"a plus|plus point|desirable|optional)\b", re.IGNORECASE)
RESP_HEAD = ("responsibilit", "duties", "what you will do", "what you'll do", "day to day", "your role")
REQ_HEAD = ("requirement", "qualification", "must have", "must-have", "required", "skills",
            "what we are looking", "what we're looking", "who you are", "experience")
BULLET_RE = re.compile(r"^\s*(?:[-*\u2022\u00b7\u25cf\u25aa]|\d+[.)])\s+")
EXP_RANGE_RE = re.compile(r"(\d+)\s*\+?\s*(?:-|\u2013|\u2014|to)\s*(\d+)\s*\+?\s*(?:years?|yrs?)", re.IGNORECASE)
EXP_MIN_RE = re.compile(r"(\d+)\s*\+?\s*(?:years?|yrs?)", re.IGNORECASE)


def _units(text: str) -> List[str]:
    units: List[str] = []
    for line in re.split(r"[\r\n]+", text):
        line = line.strip()
        if not line:
            continue
        units.extend(p.strip() for p in re.split(r"(?<=[.;!?])\s+", line) if p.strip())
    return units


def _heading_section(unit: str) -> Optional[str]:
    """Return 'preferred' / 'resp' / 'required' / 'other' if `unit` is a heading line, else None."""
    stripped = unit.strip()
    clean = stripped.rstrip(":").strip().lower()
    is_heading = stripped.endswith(":") and len(stripped) <= 60
    short = len(clean.split()) <= 4
    if not (is_heading or short):
        return None
    if PREFERRED_RE.search(clean):
        return "preferred"
    if any(k in clean for k in RESP_HEAD):
        return "resp"
    if any(k in clean for k in REQ_HEAD):
        return "required"
    return "other" if is_heading else None


def extract_experience(text: str) -> Optional[dict]:
    m = EXP_RANGE_RE.search(text)
    if m:
        return {"min": int(m.group(1)), "max": int(m.group(2)), "text": m.group(0)}
    m = EXP_MIN_RE.search(text)
    if m:
        return {"min": int(m.group(1)), "max": None, "text": m.group(0)}
    return None


def analyze_jd(text: str, extra_skills: Optional[Iterable[str]] = None) -> dict:
    text = text or ""
    catalog = build_catalog(extra_skills)
    stats = {}  # key -> {"required": n, "preferred": n}
    responsibilities: List[str] = []
    section: Optional[str] = None

    for unit in _units(text):
        head = _heading_section(unit)
        has_skill = bool(find_mentions(unit, catalog))
        if head is not None and not has_skill:
            section = None if head == "other" else head
            continue
        body = BULLET_RE.sub("", unit)
        if section == "resp" and len(body) >= 15:
            responsibilities.append(body.rstrip("."))
        # "Preferred: AWS, Docker" (heading + skills on one line) -> preferred for this line only
        is_pref = section == "preferred" or bool(PREFERRED_RE.search(body))
        for m in find_mentions(body, catalog):
            s = stats.setdefault(m["key"], {"required": 0, "preferred": 0})
            s["preferred" if is_pref else "required"] += 1

    overall = {m["key"]: m for m in find_mentions(text, catalog)}  # total mention counts + order
    skills = []
    for key, m in overall.items():
        st = stats.get(key, {"required": 1, "preferred": 0})
        importance = "REQUIRED" if st["required"] > 0 else "PREFERRED"
        raw = m["count"] * 2 + (3 if importance == "REQUIRED" else 1)
        skills.append({"name": m["name"], "category": m["category"], "importance": importance,
                       "mentions": m["count"], "_raw": raw, "_pos": m["first_pos"]})
    skills.sort(key=lambda s: (-s["_raw"], s["_pos"]))
    top = skills[0]["_raw"] if skills else 1
    for s in skills:
        s["score"] = round(100 * s["_raw"] / top)
        del s["_raw"], s["_pos"]

    return {
        "skills": skills,
        "required_skills": [s["name"] for s in skills if s["importance"] == "REQUIRED"],
        "preferred_skills": [s["name"] for s in skills if s["importance"] == "PREFERRED"],
        "tools": [s["name"] for s in skills if s["category"] in TOOL_CATEGORIES],
        "experience": extract_experience(text),
        "responsibilities": responsibilities[:10],
        "interview_topics": [{"skill": s["name"], "topics": topics_for(s["name"])}
                             for s in skills if topics_for(s["name"])],
        "source": "rules",
    }
