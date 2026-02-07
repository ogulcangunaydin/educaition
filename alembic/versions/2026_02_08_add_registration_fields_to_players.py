"""Add student_number, device_fingerprint, student_user_id to players

Revision ID: b3c4d5e6f7a8
Revises: f7e8d9c0b1a2
Create Date: 2026-02-08
"""

from alembic import op
import sqlalchemy as sa

revision = "b3c4d5e6f7a8"
down_revision = "f7e8d9c0b1a2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("players", sa.Column("student_number", sa.String(), nullable=True))
    op.add_column("players", sa.Column("device_fingerprint", sa.String(), nullable=True))
    op.add_column(
        "players",
        sa.Column("student_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("players", "student_user_id")
    op.drop_column("players", "device_fingerprint")
    op.drop_column("players", "student_number")
