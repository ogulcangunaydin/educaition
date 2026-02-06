"""
Migration: Migrate existing rooms to test_rooms

This migration copies existing data from:
- rooms (prisoners_dilemma) -> test_rooms
- high_school_rooms (program_suggestion) -> test_rooms

Revision ID: 2026_02_06_004
Revises: 2026_02_06_003
Create Date: 2026-02-06

Note: This is a data migration, not a schema migration.
The old tables are preserved for backward compatibility.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2026_02_06_004'
down_revision = '2026_02_06_003'
branch_labels = None
depends_on = None


def upgrade():
    """
    Copy existing rooms to test_rooms table with proper test_type mapping.
    """
    connection = op.get_bind()
    
    # Migrate rooms (Prisoners' Dilemma) to test_rooms
    connection.execute(sa.text("""
        INSERT INTO test_rooms (
            name, test_type, created_by, is_active, settings,
            legacy_room_id, legacy_table, created_at, updated_at
        )
        SELECT 
            name,
            'prisoners_dilemma' as test_type,
            user_id as created_by,
            TRUE as is_active,
            '{}' as settings,
            id as legacy_room_id,
            'rooms' as legacy_table,
            created_at,
            updated_at
        FROM rooms
        WHERE deleted_at IS NULL
        AND NOT EXISTS (
            SELECT 1 FROM test_rooms 
            WHERE legacy_room_id = rooms.id AND legacy_table = 'rooms'
        )
    """))
    
    # Migrate high_school_rooms (Program Suggestion) to test_rooms
    connection.execute(sa.text("""
        INSERT INTO test_rooms (
            name, test_type, created_by, is_active, settings,
            legacy_room_id, legacy_table, created_at, updated_at
        )
        SELECT 
            high_school_name as name,
            'program_suggestion' as test_type,
            user_id as created_by,
            TRUE as is_active,
            jsonb_build_object('high_school_code', high_school_code) as settings,
            id as legacy_room_id,
            'high_school_rooms' as legacy_table,
            created_at,
            updated_at
        FROM high_school_rooms
        WHERE deleted_at IS NULL
        AND NOT EXISTS (
            SELECT 1 FROM test_rooms 
            WHERE legacy_room_id = high_school_rooms.id AND legacy_table = 'high_school_rooms'
        )
    """))


def downgrade():
    """
    Remove migrated rooms from test_rooms.
    Only removes rooms that have legacy_room_id set (i.e., were migrated).
    """
    connection = op.get_bind()
    
    # Remove migrated rooms
    connection.execute(sa.text("""
        DELETE FROM test_rooms 
        WHERE legacy_room_id IS NOT NULL 
        AND legacy_table IN ('rooms', 'high_school_rooms')
    """))
