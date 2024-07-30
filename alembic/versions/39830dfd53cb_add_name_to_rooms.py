"""add name to rooms

Revision ID: 39830dfd53cb
Revises: 1c470e057136
Create Date: 2024-07-29 20:46:11.258925

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39830dfd53cb'
down_revision: Union[str, None] = '1c470e057136'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('rooms', sa.Column('name', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('rooms', 'name')
