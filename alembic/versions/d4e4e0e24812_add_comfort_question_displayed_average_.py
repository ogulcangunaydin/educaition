"""Add comfort_question_displayed_average and fare_question_displayed_average to DissonanceTestParticipant

Revision ID: d4e4e0e24812
Revises: af5d569c2ae5
Create Date: 2024-12-10 15:43:59.796062

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd4e4e0e24812'
down_revision: Union[str, None] = 'af5d569c2ae5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('dissonance_test_participants', sa.Column('comfort_question_displayed_average', sa.Float(), nullable=True))
    op.add_column('dissonance_test_participants', sa.Column('fare_question_displayed_average', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('dissonance_test_participants', 'comfort_question_displayed_average')
    op.drop_column('dissonance_test_participants', 'fare_question_displayed_average')
