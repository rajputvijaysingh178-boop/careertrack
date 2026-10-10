"""OWNER: M1 - create an admin account from the command line.
Usage:  python -m scripts.create_admin admin@example.com "StrongPass123" "Admin Name"
"""
import sys

from app.core.database import Base, SessionLocal, engine
import app.models  # noqa: F401
from app.core.security import hash_password
from app.models.user import User


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    email, password = sys.argv[1].strip().lower(), sys.argv[2]
    name = sys.argv[3] if len(sys.argv) > 3 else "Admin"
    if len(password) < 8:
        print("Password must be at least 8 characters")
        sys.exit(1)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.role, user.status = "ADMIN", "ACTIVE"
            user.password_hash = hash_password(password)
            print(f"Updated existing user {email} -> ADMIN")
        else:
            db.add(User(name=name, email=email, password_hash=hash_password(password), role="ADMIN", status="ACTIVE"))
            print(f"Created admin {email}")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
