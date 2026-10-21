import pytest
from pydantic import ValidationError

from app.core.security import hash_password, verify_password
from app.schemas.user import PasswordChange, UserRegister


def test_registration_rejects_password_over_bcrypt_byte_limit():
    # 36 characters, but 72 UTF-8 bytes.
    exact_limit = "é" * 36
    UserRegister(name="Test", email="test@example.com", password=exact_limit)

    with pytest.raises(ValidationError, match="72 UTF-8 bytes"):
        UserRegister(name="Test", email="test@example.com", password="é" * 37)


def test_password_change_rejects_password_over_bcrypt_byte_limit():
    with pytest.raises(ValidationError, match="72 UTF-8 bytes"):
        PasswordChange(current_password="current", new_password="é" * 37)


def test_hashing_refuses_to_silently_truncate_password_bytes():
    with pytest.raises(ValueError, match="72 UTF-8 bytes"):
        hash_password("é" * 37)


def test_password_at_byte_limit_still_hashes_and_verifies():
    password = "é" * 36
    assert verify_password(password, hash_password(password))
