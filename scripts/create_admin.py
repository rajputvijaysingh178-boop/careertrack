"""Legacy admin command disabled in favor of the guarded provisioner.

Use ``python -m scripts.provision_admin`` after configuring the intended target
and ``CAREERTRACK_EXPECTED_TEST_HOST``. This legacy command accepted passwords
on the command line and could modify an unverified database target.
"""


def main() -> None:
    raise SystemExit(
        "This legacy admin command is disabled. Use scripts.provision_admin "
        "with CAREERTRACK_EXPECTED_TEST_HOST configured."
    )


if __name__ == "__main__":
    main()
