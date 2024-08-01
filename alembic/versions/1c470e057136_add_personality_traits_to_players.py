"""Add personality traits to players

Revision ID: 1c470e057136
Revises: fa11f5e0ce6c
Create Date: 2024-07-22 12:31:06.832356

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = '1c470e057136'
down_revision: Union[str, None] = 'fa11f5e0ce6c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [col['name'] for col in inspector.get_columns('players')]
    
    if 'extroversion' not in columns:
        op.add_column('players', sa.Column('extroversion', sa.Float(), nullable=True))
    if 'agreeableness' not in columns:
        op.add_column('players', sa.Column('agreeableness', sa.Float(), nullable=True))
    if 'conscientiousness' not in columns:
        op.add_column('players', sa.Column('conscientiousness', sa.Float(), nullable=True))
    if 'negative_emotionality' not in columns:
        op.add_column('players', sa.Column('negative_emotionality', sa.Float(), nullable=True))
    if 'open_mindedness' not in columns:
        op.add_column('players', sa.Column('open_mindedness', sa.Float(), nullable=True))

def downgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [col['name'] for col in inspector.get_columns('players')]
    
    if 'extroversion' in columns:
        op.drop_column('players', 'extroversion')
    if 'agreeableness' in columns:
        op.drop_column('players', 'agreeableness')  
    if 'conscientiousness' in columns:
        op.drop_column('players', 'conscientiousness')      
    if 'negative_emotionality' in columns:
        op.drop_column('players', 'negative_emotionality')
    if 'open_mindedness' in columns:
        op.drop_column('players', 'open_mindedness')
    # ### end Alembic commands ###
