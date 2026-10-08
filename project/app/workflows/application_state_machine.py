"""OWNER: M2 - application lifecycle. Backend must reject invalid transitions."""
from app.core.exceptions import InvalidTransitionError

ALLOWED: dict[str, list[str]] = {
    "SAVED": ["APPLIED"],
    "APPLIED": ["APPLICATION_VIEWED", "SHORTLISTED", "HR_CONTACTED", "REJECTED"],
    "APPLICATION_VIEWED": ["SHORTLISTED", "REJECTED"],
    "SHORTLISTED": ["HR_CONTACTED", "REJECTED"],
    "HR_CONTACTED": ["INTERVIEW_SCHEDULED", "REJECTED"],
    "INTERVIEW_SCHEDULED": ["INTERVIEW_1", "ON_HOLD", "REJECTED"],
    "INTERVIEW_1": ["INTERVIEW_2", "HR_ROUND", "ON_HOLD", "REJECTED"],
    "INTERVIEW_2": ["HR_ROUND", "ON_HOLD", "REJECTED"],
    "HR_ROUND": ["OFFER_RECEIVED", "ON_HOLD", "REJECTED"],
    "ON_HOLD": ["INTERVIEW_1", "INTERVIEW_2", "HR_ROUND", "REJECTED"],
    "OFFER_RECEIVED": ["ACCEPTED", "DECLINED"],
    "ACCEPTED": [],
    "DECLINED": [],
    "REJECTED": [],
}


def can_transition(old: str, new: str) -> bool:
    return new in ALLOWED.get(old, [])


def validate_transition(old: str, new: str) -> None:
    if not can_transition(old, new):
        raise InvalidTransitionError(old, new)
