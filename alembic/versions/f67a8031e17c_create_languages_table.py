"""Create languages table

Revision ID: f67a8031e17c
Revises: d4e4e0e24812
Create Date: 2024-12-23 10:57:33.051107

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f67a8031e17c'
down_revision: Union[str, None] = 'd4e4e0e24812'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
   op.create_table(
        'languages',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('code', sa.String(), nullable=False, unique=True),
        sa.Column('name', sa.String(), nullable=False)
    )


def downgrade() -> None:
    op.drop_table('languages')
    # ### end Alembic commands ###
