"""add test_rooms table

Revision ID: 2026_02_06_002
Revises: 2026_02_06_001
Create Date: 2026-02-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2026_02_06_002'
down_revision = '2026_02_06_001'
branch_labels = None
depends_on = None


def upgrade():
    # Create test_rooms table
    op.create_table(
        'test_rooms',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('test_type', sa.String(50), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('legacy_room_id', sa.Integer(), nullable=True),
        sa.Column('legacy_table', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create indexes
    op.create_index(op.f('ix_test_rooms_id'), 'test_rooms', ['id'], unique=False)
    op.create_index(op.f('ix_test_rooms_test_type'), 'test_rooms', ['test_type'], unique=False)
    op.create_index(op.f('ix_test_rooms_created_by'), 'test_rooms', ['created_by'], unique=False)
    op.create_index(op.f('ix_test_rooms_legacy_room_id'), 'test_rooms', ['legacy_room_id'], unique=False)
    op.create_index(op.f('ix_test_rooms_is_active'), 'test_rooms', ['is_active'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_test_rooms_is_active'), table_name='test_rooms')
    op.drop_index(op.f('ix_test_rooms_legacy_room_id'), table_name='test_rooms')
    op.drop_index(op.f('ix_test_rooms_created_by'), table_name='test_rooms')
    op.drop_index(op.f('ix_test_rooms_test_type'), table_name='test_rooms')
    op.drop_index(op.f('ix_test_rooms_id'), table_name='test_rooms')
    op.drop_table('test_rooms')
