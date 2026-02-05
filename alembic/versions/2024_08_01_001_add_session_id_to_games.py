"""Add session_id to games

Revision ID: 84dfed329760
Revises: 5e82002f54c5
Create Date: 2024-08-01 13:21:53.650077

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = '84dfed329760'
down_revision: Union[str, None] = '5e82002f54c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [col['name'] for col in inspector.get_columns('games')]
    if 'session_id' not in columns:
        op.add_column('games', sa.Column('session_id', sa.Integer(), nullable=True))
    
    # Check if the foreign key exists before creating
    if not foreign_key_exists(conn, 'games', 'games_session_id_fkey'):
        op.create_foreign_key('games_session_id_fkey', 'games', 'sessions', ['session_id'], ['id'])

def downgrade():
    conn = op.get_bind()
    # Check if the foreign key exists before dropping
    if foreign_key_exists(conn, 'games', 'games_session_id_fkey'):
        op.drop_constraint('games_session_id_fkey', 'games', type_='foreignkey')
    
    inspector = Inspector.from_engine(conn)
    columns = [col['name'] for col in inspector.get_columns('games')]
    if 'session_id' in columns:
        op.drop_column('games', 'session_id')

def foreign_key_exists(connection, table_name, fk_name):
    result = connection.execute(text(f"""
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.table_constraints 
            WHERE constraint_type = 'FOREIGN KEY' 
            AND table_name = :table_name 
            AND constraint_name = :fk_name
        );
    """), {'table_name': table_name, 'fk_name': fk_name})
    return result.scalar()