"""OWNER: M1 - app entry point. Run: uvicorn app.main:app --reload"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from pathlib import Path
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import Base, engine
import app.models  # noqa: F401  (register all tables)
from app.routers import auth, users, companies, jobs, skills, blogs, materials, admin, bookmarks, applications, interviews, notes, reminders, documents, dashboard, interview_questions, prep, jd_analyzer, resume_match, recommendations

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = None
    if settings.ENABLE_SCHEDULER:
        from app.tasks.expire_jobs import expire_jobs
        from app.tasks.send_reminders import send_due_reminders
        scheduler = BackgroundScheduler()
        scheduler.add_job(expire_jobs, "interval", hours=1, id="job-expiry", replace_existing=True)
        scheduler.add_job(send_due_reminders, "interval", minutes=1, id="application-reminders", replace_existing=True)
        scheduler.start()
    app.state.scheduler = scheduler
    try:
        yield
    finally:
        if scheduler:
            scheduler.shutdown(wait=False)


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_list, allow_methods=["*"], allow_headers=["*"])

if settings.should_auto_create_schema:
    Base.metadata.create_all(bind=engine)  # local SQLite convenience; Neon must be upgraded explicitly

for module in [auth, users, companies, jobs, skills, blogs, materials, admin, bookmarks, applications, interviews, notes, reminders, documents, dashboard, interview_questions, prep, jd_analyzer, resume_match, recommendations]:
    app.include_router(module.router)

app.mount("/tracker", StaticFiles(directory=Path(__file__).resolve().parent.parent / "frontend" / "tracker",
                                   html=True), name="tracker")


@app.get("/")
def health():
    return {"app": settings.APP_NAME, "status": "running"}
