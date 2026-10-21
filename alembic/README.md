# CareerTrack Alembic migrations

The versioned migration in `versions/` creates the current 22-table model schema
on a **new, empty database**. It is an immutable schema snapshot and is
forward-only; its downgrade intentionally refuses to drop application tables.

Alembic requires `CAREERTRACK_ALEMBIC_DATABASE_URL` explicitly. It never falls
back to `DATABASE_URL` or `.env`. PostgreSQL additionally requires
`CAREERTRACK_ALEMBIC_EXPECTED_HOST`, which must exactly match the URL hostname
before an engine is opened. SQLite migrations need no expected-host value.

For an existing database, do not run the initial upgrade over the current
tables. Verify that the complete schema matches the revision and only then use
`alembic stamp 20261012_0001` to record the baseline. A partially matching or
drifted schema needs a separately reviewed reconciliation revision; stamping
or applying the empty-database revision is unsafe in that case. See
`DEPLOYMENT.md` for the test procedure, production backup guidance, and
rollback/recovery strategy.
