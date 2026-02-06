"""Add personality_test_participants table

Revision ID: 2026_02_06_003
Revises: 2026_02_06_002
Create Date: 2026-02-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = "2026_02_06_003"
down_revision: Union[str, None] = "2026_02_06_002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "personality_test_participants",
        # Primary key
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        
        # Room and owner references
        sa.Column("test_room_id", sa.Integer(), sa.ForeignKey("test_rooms.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        
        # Demographics
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("gender", sa.String(50), nullable=True),
        sa.Column("education", sa.String(255), nullable=True),
        sa.Column("income", sa.Integer(), nullable=True),
        
        # Astrological
        sa.Column("star_sign", sa.String(50), nullable=True),
        sa.Column("rising_sign", sa.String(50), nullable=True),
        
        # Career preferences
        sa.Column("workload", sa.Integer(), nullable=True),
        sa.Column("career_start", sa.Integer(), nullable=True),
        sa.Column("flexibility", sa.Integer(), nullable=True),
        
        # Personality test raw answers
        sa.Column("personality_test_answers", JSONB(), nullable=True),
        
        # Personality trait scores (Big Five / OCEAN)
        sa.Column("extroversion", sa.Float(), nullable=True),
        sa.Column("agreeableness", sa.Float(), nullable=True),
        sa.Column("conscientiousness", sa.Float(), nullable=True),
        sa.Column("negative_emotionality", sa.Float(), nullable=True),
        sa.Column("open_mindedness", sa.Float(), nullable=True),
        
        # Analysis results
        sa.Column("job_recommendation", sa.String(), nullable=True),
        sa.Column("compatibility_analysis", sa.String(), nullable=True),
        
        # Device tracking
        sa.Column("device_fingerprint", sa.String(255), nullable=True, index=True),
        sa.Column("device_info", JSONB(), nullable=True),
        
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        
        # Soft delete
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for common query patterns
    op.create_index(
        "ix_personality_test_participants_room_completed",
        "personality_test_participants",
        ["test_room_id", "extroversion"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_personality_test_participants_room_completed")
    op.drop_table("personality_test_participants")
