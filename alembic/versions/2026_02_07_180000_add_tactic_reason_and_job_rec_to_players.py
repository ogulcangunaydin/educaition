"""add tactic_reason and job_recommendation to players

Revision ID: a1b2c3d4e5f6
Revises: 6b1cf37ae5d9
Create Date: 2026-02-07 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7e8d9c0b1a2'
down_revision: Union[str, None] = '6b1cf37ae5d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # Add tactic_reason column if not exists
    result = conn.execute(sa.text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='players' AND column_name='tactic_reason'"
    ))
    if result.fetchone() is None:
        op.add_column('players', sa.Column('tactic_reason', sa.String, nullable=True))

    # Add job_recommendation column if not exists
    result = conn.execute(sa.text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='players' AND column_name='job_recommendation'"
    ))
    if result.fetchone() is None:
        op.add_column('players', sa.Column('job_recommendation', sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column('players', 'job_recommendation')
    op.drop_column('players', 'tactic_reason')
