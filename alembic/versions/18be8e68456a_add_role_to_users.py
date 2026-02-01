"""add_role_to_users

Revision ID: 18be8e68456a
Revises: a2b3b47aa6fd
Create Date: 2026-02-01 15:30:25.516836

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "18be8e68456a"
down_revision: Union[str, None] = "a2b3b47aa6fd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add role column to users table with default 'student'
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=20), nullable=False, server_default="student"),
    )


def downgrade() -> None:
    op.drop_column("users", "role")
