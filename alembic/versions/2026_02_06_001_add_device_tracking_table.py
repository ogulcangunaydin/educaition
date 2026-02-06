"""add device tracking table

Revision ID: 2026_02_06_001
Revises: 32ffb097c0a4
Create Date: 2026-02-06 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2026_02_06_001'
down_revision = '32ffb097c0a4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'device_test_completions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.String(36), nullable=False),
        sa.Column('test_type', sa.String(50), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('device_id', 'test_type', 'room_id', name='uq_device_test_room'),
    )
    op.create_index(op.f('ix_device_test_completions_id'), 'device_test_completions', ['id'], unique=False)
    op.create_index(op.f('ix_device_test_completions_device_id'), 'device_test_completions', ['device_id'], unique=False)
    op.create_index(op.f('ix_device_test_completions_test_type'), 'device_test_completions', ['test_type'], unique=False)
    op.create_index(op.f('ix_device_test_completions_room_id'), 'device_test_completions', ['room_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_device_test_completions_room_id'), table_name='device_test_completions')
    op.drop_index(op.f('ix_device_test_completions_test_type'), table_name='device_test_completions')
    op.drop_index(op.f('ix_device_test_completions_device_id'), table_name='device_test_completions')
    op.drop_index(op.f('ix_device_test_completions_id'), table_name='device_test_completions')
    op.drop_table('device_test_completions')
