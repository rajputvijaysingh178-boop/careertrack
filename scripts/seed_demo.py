"""OWNER: M1 - fill the database with demo data so M2 and M3 can test against real jobs.
Usage:  python -m scripts.seed_demo        (safe to run twice: skips if the demo companies exist)

Demo logins:  admin@careertrack.dev / Admin@12345     user@careertrack.dev / User@12345
"""
from datetime import date, datetime, timedelta

from app.core.database import Base, SessionLocal, engine
import app.models  # noqa: F401
from app.core.security import hash_password
from app.core.seed import seed_default_skills
from app.models.blog import Blog
from app.models.company import Company
from app.models.job import Job
from app.models.material import Material
from app.models.skill import JobSkill, Skill
from app.models.user import User

COMPANIES = [
    ("Cognizant", "IT Services", "Hyderabad", "10000+"), ("Deloitte", "Consulting", "Bengaluru", "10000+"),
    ("TCS", "IT Services", "Hyderabad", "10000+"), ("Accenture", "Consulting", "Pune", "10000+"),
    ("Infosys", "IT Services", "Chennai", "10000+"),
]

# company, title, location, work_mode, exp_min, exp_max, sal_min, sal_max, job_type, required, preferred
JOBS = [
    ("Cognizant", "GenAI QA Engineer", "Hyderabad", "HYBRID", 1, 3, 6, 10, "QA",
     ["Python", "Playwright", "API Testing", "GenAI", "LLM"], ["Selenium", "Docker"]),
    ("Deloitte", "QA Automation Engineer", "Bengaluru", "HYBRID", 2, 5, 8, 14, "QA",
     ["Selenium", "Python", "API Testing", "Test Automation", "CI/CD"], ["Docker", "AWS"]),
    ("TCS", "Python Developer", "Hyderabad", "ONSITE", 1, 3, 4, 8, "Backend",
     ["Python", "SQL", "REST API", "Git"], ["Django", "Docker"]),
    ("Accenture", "AI Engineer", "Pune", "HYBRID", 2, 4, 10, 18, "AI",
     ["Python", "Machine Learning", "LLM", "RAG", "Prompt Engineering"], ["LangChain", "AWS"]),
    ("Infosys", "QA Automation", "Chennai", "ONSITE", 1, 3, 4, 7, "QA",
     ["Selenium", "Java", "Test Automation", "Manual Testing"], ["Jenkins"]),
    ("Cognizant", "Python Backend Developer", "Hyderabad", "REMOTE", 2, 5, 9, 15, "Backend",
     ["Python", "FastAPI", "PostgreSQL", "Docker", "REST API"], ["AWS", "Redis"]),
    ("Deloitte", "DevOps Engineer", "Bengaluru", "HYBRID", 3, 6, 12, 20, "DevOps",
     ["Docker", "Kubernetes", "CI/CD", "AWS", "Linux"], ["Terraform"]),
    ("Accenture", "Data Scientist", "Hyderabad", "HYBRID", 2, 5, 10, 16, "Data Science",
     ["Python", "Machine Learning", "SQL", "Pandas"], ["GenAI"]),
]

BLOGS = [
    ("Top 30 Python Interview Questions", "Python", ["Python", "Interview", "Backend", "Beginner"]),
    ("How to Prepare for a QA Automation Interview", "QA", ["QA", "Automation", "Interview"]),
    ("Top Playwright Interview Questions", "QA", ["Playwright", "Interview", "Testing"]),
]

MATERIALS = [
    ("Python Official Tutorial", "https://docs.python.org/3/tutorial/", "ARTICLE", "Python"),
    ("Playwright for Python Guide", "https://playwright.dev/python/docs/intro", "ARTICLE", "Playwright"),
    ("SQL Tutorial", "https://www.w3schools.com/sql/", "ARTICLE", "SQL"),
    ("FastAPI Tutorial", "https://fastapi.tiangolo.com/tutorial/", "ARTICLE", "FastAPI"),
]


def jd(title, company, exp, required, preferred) -> str:
    return (f"{title} at {company}\n\nResponsibilities:\n"
            f"- Design, build and maintain solutions using {', '.join(required[:3])}\n"
            f"- Collaborate with product and engineering teams in an agile environment\n"
            f"- Review code, write documentation and improve quality continuously\n\n"
            f"Requirements:\n- {exp[0]}-{exp[1]} years of relevant experience\n"
            f"- Strong hands-on skills in {', '.join(required)}\n"
            f"- Good communication and problem solving skills\n\n"
            f"Preferred Skills:\n" + "\n".join(f"- {p}" for p in preferred) + "\n")


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Company).filter(Company.name == "Cognizant").first():
            print("Demo data already exists - nothing to do.")
            return
        seed_default_skills(db)
        for email, name, role, pw in (("admin@careertrack.dev", "Demo Admin", "ADMIN", "Admin@12345"),
                                      ("user@careertrack.dev", "Demo User", "USER", "User@12345")):
            if not db.query(User).filter(User.email == email).first():
                db.add(User(name=name, email=email, password_hash=hash_password(pw), role=role, status="ACTIVE"))
        db.flush()
        admin = db.query(User).filter(User.email == "admin@careertrack.dev").first()

        companies = {}
        for name, industry, location, size in COMPANIES:
            c = Company(name=name, industry=industry, location=location, company_size=size, status="ACTIVE",
                        website=f"https://www.{name.lower()}.com", description=f"{name} - {industry}")
            db.add(c)
            companies[name] = c
        db.flush()

        skills = {s.name.lower(): s for s in db.query(Skill).all()}
        today = date.today()
        for i, (company, title, loc, mode, e1, e2, s1, s2, jtype, req, pref) in enumerate(JOBS):
            job = Job(company_id=companies[company].id, title=title, description=jd(title, company, (e1, e2), req, pref),
                      location=loc, work_mode=mode, employment_type="FULL_TIME", job_type=jtype,
                      experience_min=e1, experience_max=e2, salary_min=s1, salary_max=s2,
                      application_url=f"https://careers.{company.lower()}.com/jobs/{1000 + i}",
                      posted_date=today - timedelta(days=i), expiry_date=today + timedelta(days=30),
                      status="ACTIVE", created_by=admin.id)
            db.add(job)
            db.flush()
            for names, importance in ((req, "REQUIRED"), (pref, "PREFERRED")):
                for n in names:
                    skill = skills.get(n.lower())
                    if skill:
                        db.add(JobSkill(job_id=job.id, skill_id=skill.id, importance=importance))

        for title, category, tags in BLOGS:
            db.add(Blog(title=title, slug=title.lower().replace(" ", "-"), category=category, tags=tags,
                        content=f"{title}\n\nThis is a demo article. Replace it with real content from the admin panel.",
                        author_id=admin.id, status="PUBLISHED", published_at=datetime.now()))
        for title, url, type_, skill_name in MATERIALS:
            skill = skills.get(skill_name.lower())
            db.add(Material(title=title, file_url=url, type=type_, skill_id=skill.id if skill else None,
                            created_by=admin.id))
        db.commit()
        print("Demo data created.\n  admin@careertrack.dev / Admin@12345\n  user@careertrack.dev  / User@12345")
    finally:
        db.close()


if __name__ == "__main__":
    main()
