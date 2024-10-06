"""Add job_recommendation to dissonance_test_participants

Revision ID: 343086bbb6f5
Revises: 9e8bd62ae86e
Create Date: 2024-10-06 20:44:01.403340

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '343086bbb6f5'
down_revision: Union[str, None] = '9e8bd62ae86e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('dissonance_test_participants', sa.Column('job_recommendation', sa.Text, nullable=True))

def downgrade() -> None:
    op.drop_column('dissonance_test_participants', 'job_recommendation')
