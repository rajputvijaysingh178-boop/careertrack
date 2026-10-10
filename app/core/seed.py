"""OWNER: M1 - startup seeding: default skills and the first admin account."""
import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.skill import Skill
from app.models.user import User

log = logging.getLogger(__name__)

DEFAULT_SKILLS = [
    ("Python", "Language"), ("Java", "Language"), ("JavaScript", "Language"), ("TypeScript", "Language"),
    ("SQL", "Database"), ("PostgreSQL", "Database"), ("MySQL", "Database"), ("MongoDB", "Database"),
    ("Redis", "Database"), ("FastAPI", "Framework"), ("Django", "Framework"), ("Flask", "Framework"),
    ("React", "Framework"), ("Node.js", "Framework"), ("Pandas", "Framework"),
    ("Playwright", "Testing"), ("Selenium", "Testing"), ("Pytest", "Testing"), ("API Testing", "Testing"),
    ("Test Automation", "Testing"), ("Manual Testing", "Testing"), ("Postman", "Tool"),
    ("REST API", "Concept"), ("System Design", "Concept"), ("Microservices", "Concept"), ("Agile", "Concept"),
    ("Docker", "DevOps"), ("Kubernetes", "DevOps"), ("CI/CD", "DevOps"), ("Jenkins", "DevOps"),
    ("Git", "DevOps"), ("Linux", "DevOps"), ("Terraform", "DevOps"), ("AWS", "Cloud"), ("Azure", "Cloud"),
    ("GCP", "Cloud"), ("GenAI", "AI"), ("LLM", "AI"), ("RAG", "AI"), ("Prompt Engineering", "AI"),
    ("LangChain", "AI"), ("Agentic AI", "AI"), ("Machine Learning", "AI"), ("Data Science", "AI"),
]


def seed_default_skills(db: Session) -> int:
    """Insert missing default skills. Returns how many were added."""
    have = {row[0].lower() for row in db.query(Skill.name).all()}
    added = 0
    for name, category in DEFAULT_SKILLS:
        if name.lower() not in have:
            db.add(Skill(name=name, category=category))
            added += 1
    if added:
        db.commit()
    return added


def ensure_admin(db: Session) -> bool:
    """Create the admin from ADMIN_EMAIL / ADMIN_PASSWORD (.env) if it does not exist yet."""
    email, password = settings.ADMIN_EMAIL.strip().lower(), settings.ADMIN_PASSWORD
    if not email or not password:
        return False
    if db.query(User).filter(User.email == email).first():
        return False
    db.add(User(name=settings.ADMIN_NAME or "Admin", email=email, password_hash=hash_password(password),
                role="ADMIN", status="ACTIVE"))
    db.commit()
    log.info("Created admin account %s", email)
    return True
