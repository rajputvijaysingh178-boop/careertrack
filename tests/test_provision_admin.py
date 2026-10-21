import pytest

from scripts.provision_admin import validate_target


def test_target_validation_requires_explicit_expected_neon_host():
    with pytest.raises(ValueError, match="CAREERTRACK_EXPECTED_TEST_HOST"):
        validate_target("postgresql://test.example/neondb", None)


def test_target_validation_accepts_matching_neon_hostname():
    validate_target(
        "postgresql://test.neon.tech/neondb",
        "TEST.NEON.TECH.",
    )


def test_target_validation_rejects_different_neon_hostname():
    with pytest.raises(ValueError, match="does not match"):
        validate_target(
            "postgresql://test.neon.tech/neondb",
            "production.example",
        )


def test_target_validation_rejects_non_neon_database():
    with pytest.raises(ValueError, match="Neon PostgreSQL"):
        validate_target("sqlite:///local.db", "(local)")
