"""Added username column to User model

Revision ID: fa11f5e0ce6c
Revises: 
Create Date: 2024-02-04 16:42:30.855253

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fa11f5e0ce6c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    None


def downgrade() -> None:
    None