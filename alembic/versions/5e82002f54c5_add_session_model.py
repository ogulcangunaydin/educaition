"""Add session model

Revision ID: 5e82002f54c5
Revises: 39830dfd53cb
Create Date: 2024-07-31 12:20:56.487551

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = '5e82002f54c5'
down_revision: Union[str, None] = '39830dfd53cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    # Check if the 'sessions' table exists before creating
    if 'sessions' not in inspector.get_table_names():
        op.create_table('sessions',
            sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
            sa.Column('name', sa.VARCHAR(), nullable=False),
            sa.Column('room_id', sa.INTEGER(), nullable=False),
            sa.Column('player_ids', sa.Text(), nullable=False), 
            sa.Column('status', sa.VARCHAR(), nullable=True, server_default='pending'),
            sa.Column('results', JSONB, nullable=True),
            sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], name='sessions_room_id_fkey'),
            sa.PrimaryKeyConstraint('id', name='sessions_pkey')
        )
    
    # Check if the 'ix_sessions_id' index exists before creating
    if 'ix_sessions_id' not in [index['name'] for index in inspector.get_indexes('sessions')]:
        op.create_index('ix_sessions_id', 'sessions', ['id'], unique=False)

def downgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    # Check if the 'ix_sessions_id' index exists before dropping
    if 'ix_sessions_id' in [index['name'] for index in inspector.get_indexes('sessions')]:
        op.drop_index('ix_sessions_id', table_name='sessions')
    
    # Check if the 'sessions' table exists before dropping
    if 'sessions' in inspector.get_table_names():
        op.drop_table('sessions')