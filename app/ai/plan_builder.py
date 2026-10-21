"""OWNER: M3 - rule-based N-day interview preparation plan (pure python)."""
from typing import Iterable, List, Optional

from app.ai.knowledge import GENERIC_TOPICS
from app.ai.skill_extractor import canonical_key, topics_for

_ORDER = {"REQUIRED": 0, "PREFERRED": 1, "OPTIONAL": 2}


def build_plan(skills: List[dict], days: int = 7, known: Optional[Iterable[str]] = None) -> List[dict]:
    """skills: [{"name","importance"}]; known: skills the candidate already has (get lighter revision).

    Returns [{"day", "title", "skills", "topics", "tasks"}] with exactly `days` entries:
    study days (highest-priority skills first) -> revision day(s) if time is left -> final mock-interview day.
    """
    days = max(3, min(int(days), 30))
    known_keys = {canonical_key(k) for k in (known or [])}
    study_days = days - 1

    ordered = sorted(
        enumerate(skills),
        key=lambda t: (_ORDER.get(str(t[1].get("importance", "REQUIRED")).upper(), 1),
                       canonical_key(t[1]["name"]) in known_keys, t[0]))
    units = []
    for _, s in ordered:
        name = s["name"]
        units.append({"skill": name, "topics": topics_for(name) or list(GENERIC_TOPICS),
                      "known": canonical_key(name) in known_keys})
    if not units:
        units = [{"skill": "Role fundamentals", "topics": list(GENERIC_TOPICS), "known": False}]

    # not enough skills for the days -> split the skills that have the most topics
    while len(units) < study_days:
        idx = max(range(len(units)), key=lambda i: len(units[i]["topics"]))
        u = units[idx]
        if len(u["topics"]) < 2:
            break
        half = (len(u["topics"]) + 1) // 2
        units[idx:idx + 1] = [{**u, "topics": u["topics"][:half]}, {**u, "topics": u["topics"][half:]}]

    parts_total, parts_seen = {}, {}
    for u in units:
        parts_total[u["skill"]] = parts_total.get(u["skill"], 0) + 1

    # distribute units over study days
    n = len(units)
    if n <= study_days:
        buckets = [[u] for u in units]
    else:
        buckets = [units[i * n // study_days:(i + 1) * n // study_days] for i in range(study_days)]

    plan: List[dict] = []
    for bucket in buckets:
        names: List[str] = []
        topics: List[str] = []
        for u in bucket:
            if u["skill"] not in names:
                names.append(u["skill"])
            topics.extend(u["topics"])
        title = " & ".join(names)
        if len(bucket) == 1 and parts_total[bucket[0]["skill"]] > 1:
            k = parts_seen[bucket[0]["skill"]] = parts_seen.get(bucket[0]["skill"], 0) + 1
            title += f" (part {k})"
        all_known = all(u["known"] for u in bucket)
        tasks = [
            ("Quick revision (you already know this): " if all_known else "Learn / revise: ") + ", ".join(topics),
            f"Answer at least 5 interview questions on {', '.join(names)} out loud",
            f"Build or review one small hands-on example using {', '.join(names)}",
            "Write short notes in your own words for quick revision",
        ]
        plan.append({"title": title, "skills": names, "topics": topics, "tasks": tasks})

    top_names: List[str] = []
    for u in units:
        if u["skill"] not in top_names:
            top_names.append(u["skill"])
    while len(plan) < study_days:
        plan.append({"title": "Revision & practice questions", "skills": top_names[:3], "topics": [],
                     "tasks": ["Re-attempt questions you answered badly",
                               f"Revise notes for: {', '.join(top_names[:3])}",
                               "Review your 'need to improve' list from earlier days"]})
    plan.append({"title": "Mock interview & final revision", "skills": top_names[:5], "topics": [],
                 "tasks": [f"Do a timed mock interview covering: {', '.join(top_names[:5])}",
                           "Prepare a 2-minute self introduction and a project walkthrough",
                           "Review company notes, JD and your questions to ask the interviewer"]})
    for i, d in enumerate(plan, start=1):
        d["day"] = i
    return plan
