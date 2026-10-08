"""OWNER: M1 - app entry point. Run: uvicorn app.main:app --reload"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
import app.models  # noqa: F401  (register all tables)
from app.routers import auth, users, companies, jobs, skills, blogs, materials, admin, bookmarks, applications, interviews, notes, reminders, documents, dashboard, interview_questions, prep, jd_analyzer, resume_match, recommendations

app = FastAPI(title=settings.APP_NAME)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

Base.metadata.create_all(bind=engine)  # dev only; switch to Alembic migrations later

for module in [auth, users, companies, jobs, skills, blogs, materials, admin, bookmarks, applications, interviews, notes, reminders, documents, dashboard, interview_questions, prep, jd_analyzer, resume_match, recommendations]:
    app.include_router(module.router)


@app.get("/")
def health():
    return {"app": settings.APP_NAME, "status": "running"}
