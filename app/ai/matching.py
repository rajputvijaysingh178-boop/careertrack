"""OWNER: M3 - weighted skill matching (used by Resume-JD match, Skill Gap and Job Recommendation).
Pure python: no DB, no AI.
"""
from typing import Iterable, List

from app.ai.skill_extractor import canonical_key

WEIGHTS = {"REQUIRED": 3, "PREFERRED": 2, "OPTIONAL": 1}


def _importance(value) -> str:
    v = str(value or "REQUIRED").upper()
    return v if v in WEIGHTS else "REQUIRED"


def match_skills(job_skills: List[dict], candidate_skills: Iterable[str]) -> dict:
    """job_skills: [{"name": "Python", "importance": "REQUIRED"}, ...]

    match_percent = (weight of matched job skills / total weight) * 100
    REQUIRED=3, PREFERRED=2, OPTIONAL=1
    """
    cand_names = [c for c in candidate_skills if c and str(c).strip()]
    cand_keys = {canonical_key(c) for c in cand_names}

    matched, missing = [], []
    total_w = matched_w = 0
    job_keys = set()
    for js in job_skills:
        name = js.get("name")
        if not name:
            continue
        imp = _importance(js.get("importance"))
        w = WEIGHTS[imp]
        key = canonical_key(name)
        if key in job_keys:          # ignore duplicates
            continue
        job_keys.add(key)
        total_w += w
        item = {"name": name, "importance": imp}
        if key in cand_keys:
            matched_w += w
            matched.append(item)
        else:
            missing.append(item)

    percent = round(100 * matched_w / total_w) if total_w else 0
    extra = [c for c in cand_names if canonical_key(c) not in job_keys]
    label = "Strong match" if percent >= 75 else "Moderate match" if percent >= 50 else "Low match"

    tips: List[str] = []
    for m in missing:
        if m["importance"] == "REQUIRED":
            tips.append(f"Add or build hands-on experience with {m['name']} (required for this role).")
    for m in missing:
        if m["importance"] != "REQUIRED":
            tips.append(f"Consider learning {m['name']} ({m['importance'].lower()}).")
    if matched:
        names = ", ".join(m["name"] for m in matched[:3])
        tips.append(f"Highlight your {names} experience near the top of your resume.")
    if percent >= 75:
        tips.append("You are a strong fit: apply and focus on interview preparation.")

    return {"match_percent": percent, "label": label, "matched": matched, "missing": missing,
            "extra_skills": extra, "recommendations": tips}
