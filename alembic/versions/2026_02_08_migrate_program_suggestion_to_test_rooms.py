"""migrate_program_suggestion_to_test_rooms

Replace high_school_room_id with test_room_id in program_suggestion_students table.
This is part of the unified test room architecture cleanup.

Revision ID: migrate_to_test_rooms
Revises: 
Create Date: 2026-02-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "migrate_to_test_rooms"
down_revision: Union[str, None] = "b3c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add test_room_id column
    op.add_column(
        "program_suggestion_students",
        sa.Column("test_room_id", sa.Integer(), nullable=True),
    )
    
    # Create index for test_room_id
    op.create_index(
        "ix_program_suggestion_students_test_room_id",
        "program_suggestion_students",
        ["test_room_id"],
    )
    
    # Create foreign key to test_rooms table
    op.create_foreign_key(
        "fk_program_suggestion_students_test_room_id",
        "program_suggestion_students",
        "test_rooms",
        ["test_room_id"],
        ["id"],
        ondelete="SET NULL",
    )
    
    # Make high_school_room_id nullable (for transition period)
    op.alter_column(
        "program_suggestion_students",
        "high_school_room_id",
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade() -> None:
    # Remove foreign key
    op.drop_constraint(
        "fk_program_suggestion_students_test_room_id",
        "program_suggestion_students",
        type_="foreignkey",
    )
    
    # Remove index
    op.drop_index(
        "ix_program_suggestion_students_test_room_id",
        table_name="program_suggestion_students",
    )
    
    # Remove test_room_id column
    op.drop_column("program_suggestion_students", "test_room_id")
    
    # Restore high_school_room_id as not nullable
    op.alter_column(
        "program_suggestion_students",
        "high_school_room_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
