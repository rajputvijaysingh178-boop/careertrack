import pytest

from scripts.create_admin import main


def test_legacy_admin_command_fails_closed_without_database_access():
    with pytest.raises(SystemExit, match="scripts.provision_admin"):
        main()
