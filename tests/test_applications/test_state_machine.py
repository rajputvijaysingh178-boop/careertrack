import pytest
from app.workflows.application_state_machine import can_transition, validate_transition
from fastapi import HTTPException


def test_valid_transition():
    assert can_transition("APPLIED", "HR_CONTACTED")


def test_invalid_transition():
    with pytest.raises(HTTPException):
        validate_transition("APPLIED", "ACCEPTED")
