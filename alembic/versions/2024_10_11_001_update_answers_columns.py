"""Update answers columns in dissonance_test_participants

Revision ID: 0cf11ab6d554
Revises: 343086bbb6f5
Create Date: 2024-10-11 14:56:10.279545

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0cf11ab6d554'
down_revision: Union[str, None] = '343086bbb6f5'
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
    
    # Remove old columns if they exist
    if column_exists('first_answer'):
        op.drop_column('dissonance_test_participants', 'first_answer')
    if column_exists('second_answer'):
        op.drop_column('dissonance_test_participants', 'second_answer')
    if column_exists('question_variant'):
        op.drop_column('dissonance_test_participants', 'question_variant')
    
    # Add new columns if they don't exist
    if not column_exists('comfort_question_first_answer'):
        op.add_column('dissonance_test_participants', sa.Column('comfort_question_first_answer', sa.Integer, nullable=True))
    if not column_exists('fare_question_first_answer'):
        op.add_column('dissonance_test_participants', sa.Column('fare_question_first_answer', sa.Integer, nullable=True))
    if not column_exists('comfort_question_second_answer'):
        op.add_column('dissonance_test_participants', sa.Column('comfort_question_second_answer', sa.Integer, nullable=True))
    if not column_exists('fare_question_second_answer'):
        op.add_column('dissonance_test_participants', sa.Column('fare_question_second_answer', sa.Integer, nullable=True))

def downgrade() -> None:
    # Add old columns back
    op.add_column('dissonance_test_participants', sa.Column('first_answer', sa.Integer, nullable=True))
    op.add_column('dissonance_test_participants', sa.Column('second_answer', sa.Integer, nullable=True))
    op.add_column('dissonance_test_participants', sa.Column('question_variant', sa.Text, nullable=True))
    
    # Remove new columns
    op.drop_column('dissonance_test_participants', 'comfort_question_first_answer')
    op.drop_column('dissonance_test_participants', 'fare_question_first_answer')
    op.drop_column('dissonance_test_participants', 'comfort_question_second_answer')
    op.drop_column('dissonance_test_participants', 'fare_question_second_answer')
