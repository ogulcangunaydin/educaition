"""Add personality_test_answers and compatibility_analysis to dissonance_test_participants

Revision ID: af5d569c2ae5
Revises: b306af759d00
Create Date: 2024-10-18 23:26:08.755100

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'af5d569c2ae5'
down_revision: Union[str, None] = 'b306af759d00'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('dissonance_test_participants', sa.Column('personality_test_answers', postgresql.JSONB, nullable=True))
    op.add_column('dissonance_test_participants', sa.Column('compatibility_analysis', sa.String, nullable=True))

def downgrade() -> None:
    op.drop_column('dissonance_test_participants', 'personality_test_answers')
    op.drop_column('dissonance_test_participants', 'compatibility_analysis')
