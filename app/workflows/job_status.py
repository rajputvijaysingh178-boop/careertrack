"""OWNER: M1 - job status workflow. Pure python (the exception is imported lazily).

DRAFT --publish--> ACTIVE (live now) or PUBLISHED (scheduled: posted_date in the future)
PUBLISHED --(posted_date reached)--> ACTIVE
ACTIVE / PUBLISHED --(expiry_date passed)--> EXPIRED
any --close--> CLOSED          any --unpublish--> DRAFT
EXPIRED --reopen--> ACTIVE
"""
from typing import List

ALLOWED = {
    "DRAFT": ["PUBLISHED", "ACTIVE", "CLOSED"],
    "PUBLISHED": ["ACTIVE", "EXPIRED", "CLOSED", "DRAFT"],
    "ACTIVE": ["EXPIRED", "CLOSED", "DRAFT"],
    "EXPIRED": ["ACTIVE", "CLOSED", "DRAFT"],
    "CLOSED": ["DRAFT"],
}
ALL_STATUSES: List[str] = list(ALLOWED)
LIVE_STATUSES = ("PUBLISHED", "ACTIVE")


def can_transition(old: str, new: str) -> bool:
    return new in ALLOWED.get(old, [])


def validate_transition(old: str, new: str) -> None:
    if not can_transition(old, new):
        from fastapi import HTTPException
        raise HTTPException(400, f"Invalid job status change: {old} -> {new}")
