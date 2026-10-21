"""OWNER: M3
Responsibility: JD Analyzer. Rule-based first (always works), optional AI enrichment on top.
"""
from sqlalchemy.orm import Session

from app.ai.jd_parser import analyze_jd
from app.ai.llm_client import LLMUnavailable, complete_json
from app.ai.prompts import SYSTEM_JSON, jd_analysis_prompt
from app.ai.skill_extractor import canonical_key, topics_for
from app.core.exceptions import NotFoundError
from app.repositories.prep_lookup_repository import PrepLookupRepository


class JDAnalyzerService:
    def __init__(self, db: Session):
        self.db = db
        self.lookup = PrepLookupRepository(db)

    def analyze(self, jd_text: str, use_ai: bool = False) -> dict:
        result = analyze_jd(jd_text, self.lookup.skill_names())
        result["ai_used"] = False
        if use_ai:
            try:
                self._merge_ai(result, complete_json(jd_analysis_prompt(jd_text), SYSTEM_JSON))
                result["source"], result["ai_used"] = "rules+ai", True
            except LLMUnavailable as exc:
                result["ai_error"] = str(exc)            # fall back silently to rule-based result
        return result

    def analyze_job(self, job_id: int, use_ai: bool = False) -> dict:
        job = self.lookup.get_job(job_id)
        if not job:
            raise NotFoundError("Job")
        return {"job_id": job_id, "title": job.get("title"), "company": job.get("company_name"),
                **self.analyze(job.get("description") or "", use_ai)}

    # ------------------------------------------------------------------ AI merge (defensive)
    @staticmethod
    def _merge_ai(result: dict, ai: dict) -> None:
        existing = {canonical_key(s["name"]): s for s in result["skills"]}
        for item in ai.get("skills") or []:
            if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                continue
            imp = str(item.get("importance", "REQUIRED")).upper()
            imp = imp if imp in ("REQUIRED", "PREFERRED", "OPTIONAL") else "REQUIRED"
            key = canonical_key(item["name"])
            if key in existing:
                existing[key]["importance"] = imp
            else:
                new = {"name": item["name"], "category": "other", "importance": imp, "mentions": 1, "score": 30}
                result["skills"].append(new)
                existing[key] = new
        result["required_skills"] = [s["name"] for s in result["skills"] if s["importance"] == "REQUIRED"]
        result["preferred_skills"] = [s["name"] for s in result["skills"] if s["importance"] != "REQUIRED"]

        if not result["responsibilities"] and isinstance(ai.get("responsibilities"), list):
            result["responsibilities"] = [str(r) for r in ai["responsibilities"]][:10]
        if isinstance(ai.get("tools"), list):
            for t in ai["tools"]:
                if isinstance(t, str) and t not in result["tools"]:
                    result["tools"].append(t)
        have = {t["skill"].lower() for t in result["interview_topics"]}
        for t in ai.get("interview_topics") or []:
            if isinstance(t, dict) and isinstance(t.get("skill"), str) and t["skill"].lower() not in have \
                    and isinstance(t.get("topics"), list):
                result["interview_topics"].append({"skill": t["skill"], "topics": [str(x) for x in t["topics"]]})
        for s in result["skills"]:                       # topics for skills the AI added
            if s["name"].lower() not in {t["skill"].lower() for t in result["interview_topics"]} and topics_for(s["name"]):
                result["interview_topics"].append({"skill": s["name"], "topics": topics_for(s["name"])})
        exp = ai.get("experience")
        if result["experience"] is None and isinstance(exp, dict) and isinstance(exp.get("min"), int):
            result["experience"] = {"min": exp["min"], "max": exp.get("max") if isinstance(exp.get("max"), int) else None,
                                    "text": "AI estimate"}
