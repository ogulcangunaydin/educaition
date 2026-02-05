"""Add new fields to dissonance_test_participants

Revision ID: b306af759d00
Revises: 88c13136e9a8
Create Date: 2024-10-18 23:04:53.571683

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b306af759d00'
down_revision: Union[str, None] = '88c13136e9a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    
    def column_exists(col_name):
        result = conn.execute(sa.text(
            f"SELECT column_name FROM information_schema.columns "
            f"WHERE table_name='dissonance_test_participants' AND column_name='{col_name}'"
        ))
        return result.fetchone() is not None
    
    if not column_exists('workload'):
        op.add_column('dissonance_test_participants', sa.Column('workload', sa.Integer, nullable=True))
    if not column_exists('career_start'):
        op.add_column('dissonance_test_participants', sa.Column('career_start', sa.Integer, nullable=True))
    if not column_exists('flexibility'):
        op.add_column('dissonance_test_participants', sa.Column('flexibility', sa.Integer, nullable=True))
    if not column_exists('star_sign'):
        op.add_column('dissonance_test_participants', sa.Column('star_sign', sa.String(50), nullable=True))
    if not column_exists('rising_sign'):
        op.add_column('dissonance_test_participants', sa.Column('rising_sign', sa.String(50), nullable=True))

def downgrade() -> None:
    op.drop_column('dissonance_test_participants', 'workload')
    op.drop_column('dissonance_test_participants', 'career_start')
    op.drop_column('dissonance_test_participants', 'flexibility')
    op.drop_column('dissonance_test_participants', 'star_sign')
    op.drop_column('dissonance_test_participants', 'rising_sign')
