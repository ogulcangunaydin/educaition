"""add gpt debug fields to program suggestion students

Revision ID: e5f2c8a91d34
Revises: d8f3a1c52b90
Create Date: 2026-01-30 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f2c8a91d34'
down_revision: Union[str, None] = 'd8f3a1c52b90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('program_suggestion_students', sa.Column('gpt_prompt', sa.Text(), nullable=True))
    op.add_column('program_suggestion_students', sa.Column('gpt_response', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('program_suggestion_students', 'gpt_response')
    op.drop_column('program_suggestion_students', 'gpt_prompt')
