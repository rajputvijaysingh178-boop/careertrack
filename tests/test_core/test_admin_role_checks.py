from types import SimpleNamespace

from fastapi import HTTPException

from app.core.dependencies import is_admin, require_admin
from app.services.prep_target import is_admin as prep_is_admin


def test_only_exact_admin_role_is_privileged():
    for checker in (is_admin, prep_is_admin):
        assert checker(SimpleNamespace(role="ADMIN"))
        assert checker(SimpleNamespace(role="admin"))
        assert not checker(SimpleNamespace(role="NOTADMIN"))
        assert not checker(SimpleNamespace(role="SUPERADMIN"))
        assert not checker(SimpleNamespace(role="USER"))
        assert not checker(None)


def test_admin_guard_rejects_ordinary_users_and_accepts_admins():
    admin = SimpleNamespace(role="ADMIN")
    assert require_admin(admin) is admin
    try:
        require_admin(SimpleNamespace(role="USER"))
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("ordinary users must not invoke admin operations")
