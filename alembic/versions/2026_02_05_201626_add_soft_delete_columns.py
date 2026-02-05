"""add_soft_delete_columns

Revision ID: cdc92d16b9a6
Revises: db19c00f3c56
Create Date: 2026-02-05 20:16:26.859419

Adds deleted_at column to 6 tables for soft delete functionality:
- users
- rooms
- players
- sessions
- high_school_rooms
- program_suggestion_students
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cdc92d16b9a6'
down_revision: Union[str, None] = 'db19c00f3c56'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tables that will have soft delete
SOFT_DELETE_TABLES = [
    "users",
    "rooms",
    "players",
    "sessions",
    "high_school_rooms",
    "program_suggestion_students",
]


def upgrade() -> None:
    for table_name in SOFT_DELETE_TABLES:
        op.add_column(
            table_name,
            sa.Column(
                "deleted_at",
                sa.DateTime(timezone=True),
                nullable=True,
            ),
        )
        # Create index for efficient filtering of non-deleted records
        op.create_index(
            f"ix_{table_name}_deleted_at",
            table_name,
            ["deleted_at"],
            unique=False,
        )


def downgrade() -> None:
    for table_name in SOFT_DELETE_TABLES:
        op.drop_index(f"ix_{table_name}_deleted_at", table_name=table_name)
        op.drop_column(table_name, "deleted_at")
        op.drop_column(table_name, "deleted_at")
