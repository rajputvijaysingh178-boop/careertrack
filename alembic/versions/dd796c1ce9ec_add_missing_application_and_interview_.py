"""add missing application and interview history tables

Revision ID: dd796c1ce9ec
Revises: 20261012_0001
Create Date: 2026-10-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "dd796c1ce9ec"
down_revision: Union[str, None] = "20261012_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "application_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("event_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["application_id"], ["applications.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_application_events_application_id",
        "application_events",
        ["application_id"],
    )
    op.create_index(
        "ix_application_events_event_at", "application_events", ["event_at"]
    )

    op.create_table(
        "application_status_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("old_status", sa.String(length=32), nullable=True),
        sa.Column("new_status", sa.String(length=32), nullable=False),
        sa.Column("changed_at", sa.DateTime(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("changed_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["application_id"], ["applications.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["changed_by"], ["users.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_application_status_history_application_id",
        "application_status_history",
        ["application_id"],
    )
    op.create_index(
        "ix_application_status_history_changed_at",
        "application_status_history",
        ["changed_at"],
    )

    op.create_table(
        "hr_calls",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("hr_name", sa.String(length=200), nullable=True),
        sa.Column("company_name", sa.String(length=200), nullable=True),
        sa.Column("call_at", sa.DateTime(), nullable=False),
        sa.Column("phone", sa.String(length=100), nullable=True),
        sa.Column("discussion", sa.Text(), nullable=True),
        sa.Column("next_round", sa.String(length=200), nullable=True),
        sa.Column("interview_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["application_id"], ["applications.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_hr_calls_application_id", "hr_calls", ["application_id"]
    )
    op.create_index("ix_hr_calls_call_at", "hr_calls", ["call_at"])

    op.create_table(
        "interview_status_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("interview_id", sa.Integer(), nullable=False),
        sa.Column("old_status", sa.String(length=32), nullable=True),
        sa.Column("new_status", sa.String(length=32), nullable=False),
        sa.Column("round_name", sa.String(length=100), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(), nullable=True),
        sa.Column("mode", sa.String(length=30), nullable=True),
        sa.Column("interviewer", sa.String(length=255), nullable=True),
        sa.Column("meeting_link", sa.String(length=1000), nullable=True),
        sa.Column("changed_at", sa.DateTime(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["interview_id"], ["interviews.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_interview_status_history_changed_at",
        "interview_status_history",
        ["changed_at"],
    )
    op.create_index(
        "ix_interview_status_history_interview_id",
        "interview_status_history",
        ["interview_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_interview_status_history_interview_id",
        table_name="interview_status_history",
    )
    op.drop_index(
        "ix_interview_status_history_changed_at",
        table_name="interview_status_history",
    )
    op.drop_table("interview_status_history")

    op.drop_index("ix_hr_calls_call_at", table_name="hr_calls")
    op.drop_index("ix_hr_calls_application_id", table_name="hr_calls")
    op.drop_table("hr_calls")

    op.drop_index(
        "ix_application_status_history_changed_at",
        table_name="application_status_history",
    )
    op.drop_index(
        "ix_application_status_history_application_id",
        table_name="application_status_history",
    )
    op.drop_table("application_status_history")

    op.drop_index("ix_application_events_event_at", table_name="application_events")
    op.drop_index(
        "ix_application_events_application_id",
        table_name="application_events",
    )
    op.drop_table("application_events")