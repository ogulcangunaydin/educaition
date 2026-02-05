"""add_soft_delete_to_dissonance_test_participants

Revision ID: 32ffb097c0a4
Revises: cdc92d16b9a6
Create Date: 2026-02-05 20:25:25.171805

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '32ffb097c0a4'
down_revision: Union[str, None] = 'cdc92d16b9a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'dissonance_test_participants',
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index(
        'ix_dissonance_test_participants_deleted_at',
        'dissonance_test_participants',
        ['deleted_at']
    )


def downgrade() -> None:
    op.drop_index('ix_dissonance_test_participants_deleted_at', table_name='dissonance_test_participants')
    op.drop_column('dissonance_test_participants', 'deleted_at')
