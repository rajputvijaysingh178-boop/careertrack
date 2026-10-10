"""OWNER: M3 - READ-ONLY lookups into tables owned by M1 / M2.

M3 never imports M1/M2 models. It reads their tables with plain SQL using the column names agreed in the
project document (jobs, companies, skills, job_skills, materials, blogs, applications, bookmarks).
If a table/column is missing the lookup logs a warning and returns an empty result, so M3 keeps
working while the other members are still building their parts.
"""
import logging
from datetime import date
from typing import Dict, Iterable, List, Optional

from sqlalchemy import bindparam, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

log = logging.getLogger(__name__)
ACTIVE_STATUSES = ("PUBLISHED", "ACTIVE")


class PrepLookupRepository:
    def __init__(self, db: Session):
        self.db = db

    # ---------------------------------------------------------------- helpers
    def _rows(self, sql: str, params: Optional[dict] = None) -> List[dict]:
        try:
            result = self.db.execute(text(sql), params or {})
            return [dict(r._mapping) for r in result]
        except SQLAlchemyError as exc:
            self.db.rollback()
            log.warning("PrepLookup query failed (%s): %s", sql.split("FROM")[-1].strip()[:40], exc)
            return []

    def _rows_in(self, sql: str, key: str, values: Iterable, params: Optional[dict] = None) -> List[dict]:
        values = list(values)
        if not values:
            return []
        try:
            stmt = text(sql).bindparams(bindparam(key, expanding=True))
            result = self.db.execute(stmt, {key: values, **(params or {})})
            return [dict(r._mapping) for r in result]
        except SQLAlchemyError as exc:
            self.db.rollback()
            log.warning("PrepLookup IN-query failed: %s", exc)
            return []

    def _columns(self, table: str) -> set:
        try:
            return {c["name"] for c in inspect(self.db.get_bind()).get_columns(table)}
        except Exception:
            return set()

    # ---------------------------------------------------------------- skills
    def list_skills(self) -> List[dict]:
        return self._rows("SELECT id, name, category FROM skills")

    def skill_names(self) -> List[str]:
        return [r["name"] for r in self.list_skills() if r.get("name")]

    def skills_by_names(self, names: Iterable[str]) -> Dict[str, dict]:
        """lowercase name -> skill row, for the names that exist in the skills table."""
        wanted = {n.strip().lower() for n in names if n and n.strip()}
        return {r["name"].lower(): r for r in self.list_skills() if r["name"].lower() in wanted}

    def skill_names_by_ids(self, ids: Iterable[int]) -> List[str]:
        return [r["name"] for r in self._rows_in("SELECT id, name FROM skills WHERE id IN :ids", "ids", ids)]

    # ---------------------------------------------------------------- jobs
    def get_job(self, job_id: int) -> Optional[dict]:
        rows = self._rows("SELECT id, company_id, title, description, status FROM jobs WHERE id = :id",
                          {"id": job_id})
        if not rows:
            return None
        job = rows[0]
        job["company_name"] = self.company_name(job.get("company_id"))
        return job

    def company_name(self, company_id: Optional[int]) -> Optional[str]:
        if not company_id:
            return None
        rows = self._rows("SELECT name FROM companies WHERE id = :id", {"id": company_id})
        return rows[0]["name"] if rows else None

    def company_names(self, ids: Iterable[int]) -> Dict[int, str]:
        rows = self._rows_in("SELECT id, name FROM companies WHERE id IN :ids", "ids", set(ids))
        return {r["id"]: r["name"] for r in rows}

    def job_skills(self, job_id: int) -> List[dict]:
        return self._rows(
            "SELECT s.id AS skill_id, s.name AS name, s.category AS category, js.importance AS importance "
            "FROM job_skills js JOIN skills s ON s.id = js.skill_id WHERE js.job_id = :j", {"j": job_id})

    def skills_for_jobs(self, job_ids: Iterable[int]) -> Dict[int, List[dict]]:
        rows = self._rows_in(
            "SELECT js.job_id AS job_id, s.name AS name, js.importance AS importance "
            "FROM job_skills js JOIN skills s ON s.id = js.skill_id WHERE js.job_id IN :ids", "ids", job_ids)
        out: Dict[int, List[dict]] = {}
        for r in rows:
            out.setdefault(r["job_id"], []).append({"name": r["name"], "importance": r["importance"]})
        return out

    def active_jobs(self, limit: int = 500) -> List[dict]:
        rows = self._rows(
            "SELECT id, company_id, title, status, expiry_date FROM jobs "
            "WHERE UPPER(status) IN ('PUBLISHED', 'ACTIVE') "
            "AND (expiry_date IS NULL OR expiry_date >= :today) LIMIT :lim",
            {"today": date.today().isoformat(), "lim": limit})
        return rows

    # ---------------------------------------------------------------- applications / bookmarks (M2)
    def get_application(self, application_id: int) -> Optional[dict]:
        cols = self._columns("applications")
        wanted = [c for c in ("id", "user_id", "job_id", "company_id") if c in cols or not cols]
        jd_col = next((c for c in ("jd_text", "job_description", "jd_snapshot", "jd") if c in cols), None)
        select = wanted + ([jd_col] if jd_col else [])
        rows = self._rows(f"SELECT {', '.join(select)} FROM applications WHERE id = :id", {"id": application_id})
        if not rows:
            return None
        row = rows[0]
        row["jd_text"] = row.pop(jd_col, None) if jd_col else None
        return row

    def excluded_job_ids(self, user_id: int) -> set:
        """Jobs the user already applied to or ignored."""
        ids = {r["job_id"] for r in self._rows("SELECT job_id FROM applications WHERE user_id = :u", {"u": user_id})}
        ids |= {r["job_id"] for r in self._rows(
            "SELECT job_id FROM bookmarks WHERE user_id = :u AND UPPER(type) = 'IGNORE'", {"u": user_id})}
        return {i for i in ids if i is not None}

    # ---------------------------------------------------------------- materials / blogs (M1)
    def materials_for(self, job_id: Optional[int], company_id: Optional[int], skill_ids: Iterable[int]) -> List[dict]:
        base = "SELECT id, title, description, type, file_url, skill_id, job_id, company_id FROM materials WHERE "
        conds, params = [], {}
        if job_id:
            conds.append("job_id = :job_id")
            params["job_id"] = job_id
        if company_id:
            conds.append("company_id = :company_id")
            params["company_id"] = company_id
        skill_ids = list(skill_ids)
        if skill_ids:
            sql = base + " OR ".join(conds + ["skill_id IN :sids"])
            return self._rows_in(sql, "sids", skill_ids, params)
        if not conds:
            return []
        return self._rows(base + " OR ".join(conds), params)

    def blogs_for(self, keywords: Iterable[str], limit: int = 10) -> List[dict]:
        kws = [k.lower() for k in keywords if k]
        if not kws:
            return []
        rows = self._rows("SELECT id, title, slug, category FROM blogs WHERE UPPER(status) = 'PUBLISHED' LIMIT 500")
        hits = []
        for r in rows:
            hay = f"{r.get('title') or ''} {r.get('category') or ''}".lower()
            if any(k in hay for k in kws):
                hits.append(r)
        return hits[:limit]
