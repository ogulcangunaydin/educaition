"""add high school room and program suggestion student tables

Revision ID: c3f8a2b91e47
Revises: d4e4e0e24812
Create Date: 2026-01-25 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c3f8a2b91e47'
down_revision = 'd4e4e0e24812'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create high_school_rooms table
    op.create_table(
        'high_school_rooms',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('high_school_name', sa.String(), nullable=False),
        sa.Column('high_school_code', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_high_school_rooms_id'), 'high_school_rooms', ['id'], unique=False)

    # Create program_suggestion_students table
    op.create_table(
        'program_suggestion_students',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('high_school_room_id', sa.Integer(), nullable=False),
        sa.Column('birth_year', sa.Integer(), nullable=True),
        sa.Column('gender', sa.String(length=20), nullable=True),
        sa.Column('class_year', sa.String(length=20), nullable=True),
        sa.Column('will_take_exam', sa.Boolean(), default=True),
        sa.Column('average_grade', sa.Float(), nullable=True),
        sa.Column('area', sa.String(length=50), nullable=True),
        sa.Column('wants_foreign_language', sa.Boolean(), default=False),
        sa.Column('expected_score_min', sa.Float(), nullable=True),
        sa.Column('expected_score_max', sa.Float(), nullable=True),
        sa.Column('expected_score_distribution', sa.String(length=20), nullable=True),
        sa.Column('alternative_area', sa.String(length=50), nullable=True),
        sa.Column('alternative_score_min', sa.Float(), nullable=True),
        sa.Column('alternative_score_max', sa.Float(), nullable=True),
        sa.Column('alternative_score_distribution', sa.String(length=20), nullable=True),
        sa.Column('preferred_language', sa.String(length=50), nullable=True),
        sa.Column('desired_universities', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('desired_cities', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('riasec_answers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('riasec_scores', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('suggested_jobs', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('suggested_programs', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), default='started'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['high_school_room_id'], ['high_school_rooms.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_program_suggestion_students_id'), 'program_suggestion_students', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_program_suggestion_students_id'), table_name='program_suggestion_students')
    op.drop_table('program_suggestion_students')
    op.drop_index(op.f('ix_high_school_rooms_id'), table_name='high_school_rooms')
    op.drop_table('high_school_rooms')
