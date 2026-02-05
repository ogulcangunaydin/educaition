"""add_reference_data_tables

Revision ID: fff0fd95ec84
Revises: 94fc3e380209
Create Date: 2026-02-05 12:51:56.956051

Creates tables for reference data:
- riasec_job_scores: RIASEC scores for job matching
- score_distributions: Score to ranking distribution for exam types
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'fff0fd95ec84'
down_revision: Union[str, None] = '94fc3e380209'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create riasec_job_scores table
    op.create_table(
        'riasec_job_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_title', sa.String(255), nullable=False),
        sa.Column('realistic', sa.Float(), nullable=False, server_default='0'),
        sa.Column('investigative', sa.Float(), nullable=False, server_default='0'),
        sa.Column('artistic', sa.Float(), nullable=False, server_default='0'),
        sa.Column('social', sa.Float(), nullable=False, server_default='0'),
        sa.Column('enterprising', sa.Float(), nullable=False, server_default='0'),
        sa.Column('conventional', sa.Float(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_riasec_job_scores_id', 'riasec_job_scores', ['id'])
    op.create_index('ix_riasec_job_scores_job_title', 'riasec_job_scores', ['job_title'], unique=True)

    # Create score_distributions table
    op.create_table(
        'score_distributions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('puan_type', sa.String(20), nullable=False),
        sa.Column('min_score', sa.Integer(), nullable=False),
        sa.Column('max_score', sa.Integer(), nullable=False),
        sa.Column('distribution', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_score_distributions_id', 'score_distributions', ['id'])
    op.create_index('ix_score_distributions_puan_type', 'score_distributions', ['puan_type'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_score_distributions_puan_type', 'score_distributions')
    op.drop_index('ix_score_distributions_id', 'score_distributions')
    op.drop_table('score_distributions')
    
    op.drop_index('ix_riasec_job_scores_job_title', 'riasec_job_scores')
    op.drop_index('ix_riasec_job_scores_id', 'riasec_job_scores')
    op.drop_table('riasec_job_scores')
