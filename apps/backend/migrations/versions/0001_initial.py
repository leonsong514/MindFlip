"""initial schema: storage_probe

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-29

Iteration 01 introduces a single technical table used to verify the
persistence contract (migration, insert, close, reopen, rollback). It
is not a domain entity and will be replaced in a later iteration.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "storage_probe",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("value", sa.String(length=255), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("storage_probe")
