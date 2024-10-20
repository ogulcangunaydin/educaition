"""Add user relation to dissonance_test_participants

Revision ID: 88c13136e9a8
Revises: 08d958b0d3fd
Create Date: 2024-10-18 21:35:39.604575

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '88c13136e9a8'
down_revision: Union[str, None] = '08d958b0d3fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('dissonance_test_participants', sa.Column('user_id', sa.Integer, nullable=True))
    op.create_foreign_key('fk_dissonance_test_participants_user', 'dissonance_test_participants', 'users', ['user_id'], ['id'])

def downgrade() -> None:
    op.drop_constraint('fk_dissonance_test_participants_user', 'dissonance_test_participants', type_='foreignkey')
    op.drop_column('dissonance_test_participants', 'user_id')
