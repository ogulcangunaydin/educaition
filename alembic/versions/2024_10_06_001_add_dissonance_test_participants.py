"""Added dissonance_test_participants table

Revision ID: 98fdce5085a0
Revises: f544c552f4f3
Create Date: 2024-10-06 12:50:12.054343

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '98fdce5085a0'
down_revision: Union[str, None] = 'f544c552f4f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if table exists before creating (handles re-runs)
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_name='dissonance_test_participants'"
    ))
    if result.fetchone() is None:
        op.create_table(
            'dissonance_test_participants',
            sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('email', sa.String(255), nullable=True),
            sa.Column('age', sa.Integer, nullable=True),
            sa.Column('gender', sa.String(50), nullable=True),
            sa.Column('education', sa.String(255), nullable=True),
            sa.Column('income', sa.Integer, nullable=True),
            sa.Column('sentiment', sa.Integer, nullable=True),
            sa.Column('question_variant', sa.Integer, nullable=True),
            sa.Column('first_answer', sa.Integer, nullable=True),
            sa.Column('second_answer', sa.Integer, nullable=True),
            sa.Column('extroversion', sa.Float, nullable=True),
            sa.Column('agreeableness', sa.Float, nullable=True),
            sa.Column('conscientiousness', sa.Float, nullable=True),
            sa.Column('negative_emotionality', sa.Float, nullable=True),
            sa.Column('open_mindedness', sa.Float, nullable=True)
        )


def downgrade() -> None:
    op.drop_table('dissonance_test_participants')
