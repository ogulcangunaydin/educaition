"""widen device_id column to 64 chars for SHA-256 fingerprint

Revision ID: a1b2c3d4e5f6
Revises: 2026_02_06_004_migrate_rooms_to_test_rooms
Create Date: 2026-02-06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '2026_02_06_004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Widen device_id from String(36) to String(64) to accept SHA-256 hex hashes
    op.alter_column(
        'device_test_completions',
        'device_id',
        existing_type=sa.String(36),
        type_=sa.String(64),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        'device_test_completions',
        'device_id',
        existing_type=sa.String(64),
        type_=sa.String(36),
        existing_nullable=False,
    )
