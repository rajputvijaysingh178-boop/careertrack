"""OWNER: M2 - scheduled reminder state update (delivery can be attached later)."""
from app.core.database import SessionLocal
from app.core.time import utcnow
from app.models.reminder import Reminder


def send_due_reminders():
    db = SessionLocal()
    try:
        rows = db.query(Reminder).filter(Reminder.status == "PENDING",
                                         Reminder.reminder_time <= utcnow()).all()
        for row in rows:
            row.status = "DUE"
        db.commit()
        return len(rows)
    finally:
        db.close()
