"""add student_user_id to participant tables

Revision ID: 2026_02_06_006
Revises: a1b2c3d4e5f6
Create Date: 2026-02-06

"""
from alembic import op
import sqlalchemy as sa

revision = '2026_02_06_006'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add student_user_id column to personality_test_participants
    op.add_column(
        'personality_test_participants',
        sa.Column('student_user_id', sa.Integer(), nullable=True),
    )
    op.create_index(
        'ix_personality_test_participants_student_user_id',
        'personality_test_participants',
        ['student_user_id'],
    )
    op.create_foreign_key(
        'fk_personality_test_student_user',
        'personality_test_participants',
        'users',
        ['student_user_id'],
        ['id'],
        ondelete='SET NULL',
    )

    # Add student_user_id column to dissonance_test_participants
    op.add_column(
        'dissonance_test_participants',
        sa.Column('student_user_id', sa.Integer(), nullable=True),
    )
    op.create_index(
        'ix_dissonance_test_participants_student_user_id',
        'dissonance_test_participants',
        ['student_user_id'],
    )
    op.create_foreign_key(
        'fk_dissonance_test_student_user',
        'dissonance_test_participants',
        'users',
        ['student_user_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint(
        'fk_dissonance_test_student_user',
        'dissonance_test_participants',
        type_='foreignkey',
    )
    op.drop_index(
        'ix_dissonance_test_participants_student_user_id',
        'dissonance_test_participants',
    )
    op.drop_column('dissonance_test_participants', 'student_user_id')

    op.drop_constraint(
        'fk_personality_test_student_user',
        'personality_test_participants',
        type_='foreignkey',
    )
    op.drop_index(
        'ix_personality_test_participants_student_user_id',
        'personality_test_participants',
    )
    op.drop_column('personality_test_participants', 'student_user_id')
