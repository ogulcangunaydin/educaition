"""Update question_variant to String in dissonance_test_participants

Revision ID: 9e8bd62ae86e
Revises: 98fdce5085a0
Create Date: 2024-10-06 17:19:55.161006

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e8bd62ae86e'
down_revision: Union[str, None] = '98fdce5085a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if column exists before altering
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_name='dissonance_test_participants' AND column_name='question_variant'"
    ))
    row = result.fetchone()
    if row is None:
        # Column doesn't exist, create it as String
        op.add_column('dissonance_test_participants', 
                      sa.Column('question_variant', sa.String(255), nullable=True))
    elif row[1] != 'character varying':
        # Column exists but not String type, alter it
        op.alter_column('dissonance_test_participants', 'question_variant',
                        existing_type=sa.Integer(),
                        type_=sa.String(255),
                        existing_nullable=True)

def downgrade() -> None:
    op.alter_column('dissonance_test_participants', 'question_variant',
                    existing_type=sa.String(255),
                    type_=sa.Integer(),
                    existing_nullable=True)
