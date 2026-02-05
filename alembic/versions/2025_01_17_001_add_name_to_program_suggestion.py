"""add name to program suggestion students

Revision ID: d8f3a1c52b90
Revises: c3f8a2b91e47
Create Date: 2025-01-17 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8f3a1c52b90'
down_revision: Union[str, None] = 'c3f8a2b91e47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='program_suggestion_students' AND column_name='name'"
    ))
    if result.fetchone() is None:
        op.add_column('program_suggestion_students', sa.Column('name', sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column('program_suggestion_students', 'name')
