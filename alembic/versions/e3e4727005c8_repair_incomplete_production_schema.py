
"""Repair incomplete production schema.

Revision ID: e3e4727005c8
Revises: dd796c1ce9ec
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e3e4727005c8"
down_revision: Union[str, None] = "dd796c1ce9ec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLES = (
    "applications",
    "bookmarks",
    "documents",
    "interviews",
    "notes",
    "reminders",
)


def upgrade() -> None:
    # Safety check: do not modify these tables if data has appeared.
    connection = op.get_bind()

    for table in TABLES:
        count = connection.execute(
            sa.text(f'SELECT COUNT(*) FROM "{table}"')
        ).scalar_one()

        if count != 0:
            raise RuntimeError(
                f"Safety stop: {table} contains {count} rows. "
                "No schema repair was performed. Review the data first."
            )

    # APPLICATIONS
    op.add_column(
        "applications",
        sa.Column("user_id", sa.Integer(), nullable=False),
    )
    op.add_column(
        "applications",
        sa.Column("job_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "applications",
        sa.Column("company_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "applications",
        sa.Column("applied_date", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "applications",
        sa.Column("status", sa.String(32), nullable=False),
    )
    op.add_column(
        "applications",
        sa.Column("source", sa.String(100), nullable=True),
    )
    op.add_column(
        "applications",
        sa.Column("application_url", sa.String(1000), nullable=True),
    )
    op.add_column(
        "applications",
        sa.Column("resume_version", sa.String(255), nullable=True),
    )
    op.add_column(
        "applications",
        sa.Column("salary_expectation", sa.Float(), nullable=True),
    )
    op.add_column(
        "applications",
        sa.Column("hr_name", sa.String(200), nullable=True),
    )
    op.add_column(
        "applications",
        sa.Column("hr_contact", sa.String(255), nullable=True),
    )
    op.add_column(
        "applications",
        sa.Column("job_title", sa.String(200), nullable=False),
    )
    op.add_column(
        "applications",
        sa.Column("company_name", sa.String(200), nullable=True),
    )
    op.add_column(
        "applications",
        sa.Column("jd_text", sa.Text(), nullable=True),
    )
    op.add_column(
        "applications",
        sa.Column("skills", sa.Text(), nullable=True),
    )
    op.add_column(
        "applications",
        sa.Column("requirements", sa.Text(), nullable=True),
    )
    op.add_column(
        "applications",
        sa.Column("salary", sa.String(100), nullable=True),
    )
    op.add_column(
        "applications",
        sa.Column("location", sa.String(200), nullable=True),
    )
    op.add_column(
        "applications",
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.add_column(
        "applications",
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_index(
        "ix_applications_applied_date",
        "applications",
        ["applied_date"],
    )
    op.create_index(
        "ix_applications_company_id",
        "applications",
        ["company_id"],
    )
    op.create_index(
        "ix_applications_job_id",
        "applications",
        ["job_id"],
    )
    op.create_index(
        "ix_applications_status",
        "applications",
        ["status"],
    )
    op.create_index(
        "ix_applications_user_id",
        "applications",
        ["user_id"],
    )

    op.create_foreign_key(
        "fk_applications_job_id_jobs",
        "applications",
        "jobs",
        ["job_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_applications_user_id_users",
        "applications",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_applications_company_id_companies",
        "applications",
        "companies",
        ["company_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # BOOKMARKS
    op.add_column(
        "bookmarks",
        sa.Column("user_id", sa.Integer(), nullable=False),
    )
    op.add_column(
        "bookmarks",
        sa.Column("job_id", sa.Integer(), nullable=False),
    )
    op.add_column(
        "bookmarks",
        sa.Column("type", sa.String(16), nullable=False),
    )
    op.add_column(
        "bookmarks",
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_index("ix_bookmarks_job_id", "bookmarks", ["job_id"])
    op.create_index("ix_bookmarks_user_id", "bookmarks", ["user_id"])
    op.create_unique_constraint(
        "uq_bookmark_user_job",
        "bookmarks",
        ["user_id", "job_id"],
    )
    op.create_foreign_key(
        "fk_bookmarks_user_id_users",
        "bookmarks",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_bookmarks_job_id_jobs",
        "bookmarks",
        "jobs",
        ["job_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # DOCUMENTS
    op.add_column(
        "documents",
        sa.Column("user_id", sa.Integer(), nullable=False),
    )
    op.add_column(
        "documents",
        sa.Column("application_id", sa.Integer(), nullable=False),
    )
    op.add_column(
        "documents",
        sa.Column("name", sa.String(255), nullable=False),
    )
    op.add_column(
        "documents",
        sa.Column("file_url", sa.String(1000), nullable=False),
    )
    op.add_column(
        "documents",
        sa.Column("doc_type", sa.String(50), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_index(
        "ix_documents_application_id",
        "documents",
        ["application_id"],
    )
    op.create_index(
        "ix_documents_user_id",
        "documents",
        ["user_id"],
    )
    op.create_foreign_key(
        "fk_documents_user_id_users",
        "documents",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_documents_application_id_applications",
        "documents",
        "applications",
        ["application_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # INTERVIEWS
    op.add_column(
        "interviews",
        sa.Column("application_id", sa.Integer(), nullable=False),
    )
    op.add_column(
        "interviews",
        sa.Column("round_name", sa.String(100), nullable=False),
    )
    op.add_column(
        "interviews",
        sa.Column("scheduled_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "interviews",
        sa.Column("mode", sa.String(30), nullable=True),
    )
    op.add_column(
        "interviews",
        sa.Column("interviewer", sa.String(255), nullable=True),
    )
    op.add_column(
        "interviews",
        sa.Column("meeting_link", sa.String(1000), nullable=True),
    )
    op.add_column(
        "interviews",
        sa.Column("status", sa.String(32), nullable=False),
    )
    op.add_column(
        "interviews",
        sa.Column("feedback", sa.Text(), nullable=True),
    )
    op.add_column(
        "interviews",
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.add_column(
        "interviews",
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_index(
        "ix_interviews_application_id",
        "interviews",
        ["application_id"],
    )
    op.create_index(
        "ix_interviews_scheduled_at",
        "interviews",
        ["scheduled_at"],
    )
    op.create_index(
        "ix_interviews_status",
        "interviews",
        ["status"],
    )
    op.create_foreign_key(
        "fk_interviews_application_id_applications",
        "interviews",
        "applications",
        ["application_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # NOTES
    op.add_column(
        "notes",
        sa.Column("user_id", sa.Integer(), nullable=False),
    )
    op.add_column(
        "notes",
        sa.Column("application_id", sa.Integer(), nullable=False),
    )
    op.add_column(
        "notes",
        sa.Column("title", sa.String(255), nullable=False),
    )
    op.add_column(
        "notes",
        sa.Column("content", sa.Text(), nullable=False),
    )
    op.add_column(
        "notes",
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.add_column(
        "notes",
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_index("ix_notes_application_id", "notes", ["application_id"])
    op.create_index("ix_notes_user_id", "notes", ["user_id"])
    op.create_foreign_key(
        "fk_notes_application_id_applications",
        "notes",
        "applications",
        ["application_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_notes_user_id_users",
        "notes",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # REMINDERS
    op.add_column(
        "reminders",
        sa.Column("user_id", sa.Integer(), nullable=False),
    )
    op.add_column(
        "reminders",
        sa.Column("application_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "reminders",
        sa.Column("title", sa.String(255), nullable=False),
    )
    op.add_column(
        "reminders",
        sa.Column("reminder_type", sa.String(50), nullable=False),
    )
    op.add_column(
        "reminders",
        sa.Column("reminder_time", sa.DateTime(), nullable=False),
    )
    op.add_column(
        "reminders",
        sa.Column("status", sa.String(20), nullable=False),
    )
    op.add_column(
        "reminders",
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_index(
        "ix_reminders_application_id",
        "reminders",
        ["application_id"],
    )
    op.create_index(
        "ix_reminders_reminder_time",
        "reminders",
        ["reminder_time"],
    )
    op.create_index(
        "ix_reminders_status",
        "reminders",
        ["status"],
    )
    op.create_index(
        "ix_reminders_user_id",
        "reminders",
        ["user_id"],
    )
    op.create_foreign_key(
        "fk_reminders_application_id_applications",
        "reminders",
        "applications",
        ["application_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_reminders_user_id_users",
        "reminders",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    raise RuntimeError(
        "CareerTrack schema migrations are forward-only; "
        "use a reviewed recovery plan."
    )
