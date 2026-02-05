"""add_missing_foreign_key_indexes

Revision ID: 94fc3e380209
Revises: 92e0df0e3aa7
Create Date: 2026-02-05 10:52:52.045772

This migration adds indexes to all foreign key columns that were missing indexes.
Indexes on FK columns improve:
- JOIN performance
- Foreign key constraint validation
- CASCADE delete operations
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '94fc3e380209'
down_revision: Union[str, None] = '92e0df0e3aa7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # token_blacklist indexes
    op.create_index('ix_token_blacklist_user_id', 'token_blacklist', ['user_id'])
    op.create_index('ix_token_blacklist_expires_at', 'token_blacklist', ['expires_at'])
    
    # rooms indexes
    op.create_index('ix_rooms_user_id', 'rooms', ['user_id'])
    
    # players indexes
    op.create_index('ix_players_room_id', 'players', ['room_id'])
    
    # games indexes
    op.create_index('ix_games_session_id', 'games', ['session_id'])
    op.create_index('ix_games_home_player_id', 'games', ['home_player_id'])
    op.create_index('ix_games_away_player_id', 'games', ['away_player_id'])
    
    # rounds indexes
    op.create_index('ix_rounds_game_id', 'rounds', ['game_id'])
    
    # sessions indexes
    op.create_index('ix_sessions_room_id', 'sessions', ['room_id'])
    
    # dissonance_test_participants indexes
    op.create_index('ix_dissonance_test_participants_user_id', 'dissonance_test_participants', ['user_id'])
    
    # high_school_rooms indexes
    op.create_index('ix_high_school_rooms_user_id', 'high_school_rooms', ['user_id'])
    
    # program_suggestion_students indexes
    op.create_index('ix_program_suggestion_students_high_school_room_id', 'program_suggestion_students', ['high_school_room_id'])


def downgrade() -> None:
    # Drop all indexes in reverse order
    op.drop_index('ix_program_suggestion_students_high_school_room_id', 'program_suggestion_students')
    op.drop_index('ix_high_school_rooms_user_id', 'high_school_rooms')
    op.drop_index('ix_dissonance_test_participants_user_id', 'dissonance_test_participants')
    op.drop_index('ix_sessions_room_id', 'sessions')
    op.drop_index('ix_rounds_game_id', 'rounds')
    op.drop_index('ix_games_away_player_id', 'games')
    op.drop_index('ix_games_home_player_id', 'games')
    op.drop_index('ix_games_session_id', 'games')
    op.drop_index('ix_players_room_id', 'players')
    op.drop_index('ix_rooms_user_id', 'rooms')
    op.drop_index('ix_token_blacklist_expires_at', 'token_blacklist')
    op.drop_index('ix_token_blacklist_user_id', 'token_blacklist')
