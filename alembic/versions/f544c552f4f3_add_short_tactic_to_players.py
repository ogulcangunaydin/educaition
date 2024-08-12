"""Add short_tactic to players

Revision ID: f544c552f4f3
Revises: 0980ae8b64a4
Create Date: 2024-08-12 17:50:52.316091

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f544c552f4f3'
down_revision: Union[str, None] = '0980ae8b64a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use op.add_column to add the short_tactic column to the players table
    op.add_column('players', sa.Column('short_tactic', sa.String(), nullable=True))

def downgrade() -> None:
    # Use op.drop_column to remove the short_tactic column from the players table
    op.drop_column('players', 'short_tactic')
