"""Create or repair only the configured admin account after host confirmation."""
import argparse
import os

from sqlalchemy import func
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import engine
from app.core.security import hash_password
from app.models.user import User


def validate_target(database_url: str, expected_host: str | None) -> None:
    """Refuse provisioning unless the configured target is the confirmed Neon host."""
    if not expected_host or not expected_host.strip():
        raise ValueError("Set CAREERTRACK_EXPECTED_TEST_HOST before provisioning.")
    target = make_url(database_url)
    if not target.drivername.startswith(("postgres",)) or not target.host:
        raise ValueError("Admin provisioning requires a Neon PostgreSQL database.")
    if not target.host.casefold().endswith(".neon.tech"):
        raise ValueError("Configured database host is not a Neon host.")
    if target.host.rstrip(".").casefold() != expected_host.strip().rstrip(".").casefold():
        raise ValueError("Configured database host does not match CAREERTRACK_EXPECTED_TEST_HOST.")


def validate_admin(name: str, email: str, password: str) -> tuple[str, str, str]:
    normalized_email = (email or "").strip().lower()
    normalized_name = (name or "").strip() or "Admin"
    if not normalized_email or not password:
        raise ValueError("ADMIN_EMAIL and ADMIN_PASSWORD must be configured.")
    password_bytes = password.encode("utf-8")
    if len(password_bytes) < 12 or len(password_bytes) > 72:
        raise ValueError("ADMIN_PASSWORD must be 12 to 72 UTF-8 bytes for PostgreSQL provisioning.")
    return normalized_name, normalized_email, password


def provision_one_admin(db: Session, name: str, email: str, password: str) -> bool:
    """Upsert the configured email only. Returns True if a row was created."""
    user = db.query(User).filter(func.lower(User.email) == email).one_or_none()
    created = user is None
    if created:
        user = User(name=name, email=email)
        db.add(user)
    user.name = name
    user.email = email
    user.password_hash = hash_password(password)
    user.role = "ADMIN"
    user.status = "ACTIVE"
    db.flush()
    return created


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Provision only the configured admin account after Neon host confirmation"
    )
    parser.parse_args()
    try:
        database_url = settings.sqlalchemy_database_url
        validate_target(
            database_url,
            os.environ.get("CAREERTRACK_EXPECTED_TEST_HOST"),
        )
        name, email, password = validate_admin(
            settings.ADMIN_NAME,
            settings.ADMIN_EMAIL,
            settings.ADMIN_PASSWORD,
        )
    except ValueError as exc:
        parser.error(str(exc))

    created = False
    try:
        # No create_all or seed operation: only the existing users row is touched.
        with Session(engine) as db, db.begin():
            created = provision_one_admin(db, name, email, password)
    except Exception:
        # Avoid emitting SQL parameters, hashes, URLs, or credentials in an error.
        print("Admin provisioning failed; the transaction was rolled back.")
        raise SystemExit(1)
    finally:
        engine.dispose()

    print("Configured admin account created and activated." if created else
          "Configured admin account password and status updated.")


if __name__ == "__main__":
    main()
