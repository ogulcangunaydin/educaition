"""add_program_interaction_logs_table

Revision ID: 80c52e849043
Revises: 8d24ced8b0c3
Create Date: 2026-02-11 20:56:30.856088

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '80c52e849043'
down_revision: Union[str, None] = '8d24ced8b0c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'program_interaction_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('program_name', sa.String(length=255), nullable=False),
        sa.Column('university', sa.String(length=255), nullable=False),
        sa.Column('scholarship', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['program_suggestion_students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_program_interaction_logs_id'), 'program_interaction_logs', ['id'], unique=False)
    op.create_index(op.f('ix_program_interaction_logs_student_id'), 'program_interaction_logs', ['student_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_program_interaction_logs_student_id'), table_name='program_interaction_logs')
    op.drop_index(op.f('ix_program_interaction_logs_id'), table_name='program_interaction_logs')
    op.drop_table('program_interaction_logs')
