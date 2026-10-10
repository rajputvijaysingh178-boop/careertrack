from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.application import Application
from app.models.company import Company
from app.models.interview_question import InterviewQuestion
from app.models.job import Job
from app.models.skill import JobSkill, Skill
from app.models.user import User
from app.services.jd_analyzer_service import JDAnalyzerService
from app.services.prep_plan_service import PrepPlanService
from app.services.prep_workspace_service import PrepWorkspaceService
from app.services.recommendation_service import RecommendationService
from app.services.resume_match_service import ResumeMatchService
from app.services.skill_gap_service import SkillGapService


def test_member_three_features_share_job_application_and_skill_data():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    try:
        user = User(name="Prep user", email="prep@example.test", password_hash="hash")
        company = Company(name="Prep Co")
        db.add_all([user, company])
        db.flush()
        job = Job(company_id=company.id, title="Python Engineer",
                  description="Build Python services with FastAPI and SQL.", status="ACTIVE")
        suggested_job = Job(company_id=company.id, title="Platform Engineer",
                            description="Build Python services with SQL.", status="ACTIVE")
        python = Skill(name="Python", category="Backend")
        fastapi = Skill(name="FastAPI", category="Backend")
        sql = Skill(name="SQL", category="Data")
        db.add_all([job, suggested_job, python, fastapi, sql])
        db.flush()
        db.add_all([JobSkill(job_id=job.id, skill_id=python.id),
                    JobSkill(job_id=job.id, skill_id=fastapi.id), JobSkill(job_id=job.id, skill_id=sql.id)])
        db.add_all([JobSkill(job_id=suggested_job.id, skill_id=python.id),
                    JobSkill(job_id=suggested_job.id, skill_id=sql.id)])
        application = Application(user_id=user.id, job_id=job.id, company_id=company.id,
                                  job_title=job.title, company_name=company.name,
                                  jd_text=job.description, status="APPLIED")
        db.add(application)
        db.add(InterviewQuestion(job_id=job.id, skill_id=python.id, category="Python",
                                 question="How does Python manage memory?", difficulty="MEDIUM"))
        db.commit()

        jd = JDAnalyzerService(db).analyze(job.description)
        assert {item["name"].lower() for item in jd["skills"]} >= {"python", "fastapi", "sql"}

        profile = RecommendationService(db)
        profile.set_my_skills(user.id, ["Python", "SQL"])
        recommendations = profile.recommend_jobs(user.id)
        assert recommendations["jobs"][0]["job_id"] == suggested_job.id

        gap = SkillGapService(db).gap(user, application_id=application.id)
        assert any(item["name"].lower() == "fastapi" for item in gap["missing"])

        workspace = PrepWorkspaceService(db).build_workspace(application_id=application.id, user=user)
        assert workspace["application_id"] == application.id
        assert workspace["counts"]["questions"] == 1

        plan = PrepPlanService(db).generate(user, application_id=application.id, days=5)
        assert plan["source"] == "rules"
        assert len(plan["plan"]) == 5
        assert any(day["questions"] for day in plan["plan"])

        match = ResumeMatchService(db).match(user, application_id=application.id,
                                             resume_text="Python SQL backend development")
        assert "Python" in [item["name"] for item in match["matched"]]
        history = ResumeMatchService(db).history(user.id)
        assert history[0]["application_id"] == application.id
    finally:
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
