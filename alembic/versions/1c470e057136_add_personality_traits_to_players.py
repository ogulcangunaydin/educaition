"""Add personality traits to players

Revision ID: 1c470e057136
Revises: fa11f5e0ce6c
Create Date: 2024-07-22 12:31:06.832356

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1c470e057136'
down_revision: Union[str, None] = 'fa11f5e0ce6c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns for personality traits to the players table
    op.add_column('players', sa.Column('extroversion', sa.Float(), nullable=True))
    op.add_column('players', sa.Column('agreeableness', sa.Float(), nullable=True))
    op.add_column('players', sa.Column('conscientiousness', sa.Float(), nullable=True))
    op.add_column('players', sa.Column('negative_emotionality', sa.Float(), nullable=True))
    op.add_column('players', sa.Column('open_mindedness', sa.Float(), nullable=True))

def downgrade() -> None:
    # Remove columns for personality traits from the players table
    op.drop_column('players', 'extroversion')
    op.drop_column('players', 'agreeableness')
    op.drop_column('players', 'conscientiousness')
    op.drop_column('players', 'negative_emotionality')
    op.drop_column('players', 'open_mindedness')
    # ### end Alembic commands ###
