"""Add player_function_name to players

Revision ID: 0980ae8b64a4
Revises: 84dfed329760
Create Date: 2024-08-01 18:20:51.692937

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = '0980ae8b64a4'
down_revision: Union[str, None] = '84dfed329760'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [col['name'] for col in inspector.get_columns('players')]
    if 'player_function_name' not in columns:
        op.add_column('players', sa.Column('player_function_name', sa.String(), nullable=True))

def downgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [col['name'] for col in inspector.get_columns('players')]
    if 'player_function_name' in columns:
        op.drop_column('players', 'player_function_name')
