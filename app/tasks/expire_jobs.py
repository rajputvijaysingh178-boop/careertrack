"""OWNER: M1 - scheduled task: job expiry.

Rules (from the project document):  expiry_date < today  ->  status EXPIRED
Also: PUBLISHED (scheduled) jobs whose posted_date has arrived become ACTIVE.

Run once:  python -c "from app.tasks.expire_jobs import expire_jobs; print(expire_jobs())"
It also runs automatically every hour inside the API (see app/main.py, ENABLE_SCHEDULER).
"""
import logging

log = logging.getLogger(__name__)


def expire_jobs() -> dict:
    from app.core.database import SessionLocal
    from app.services.job_service import JobService
    db = SessionLocal()
    try:
        result = JobService(db).run_maintenance()
        if result["activated"] or result["expired"]:
            log.info("Job maintenance: %s", result)
        return result
    finally:
        db.close()
