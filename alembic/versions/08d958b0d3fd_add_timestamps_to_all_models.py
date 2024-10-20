"""Add timestamps to all models

Revision ID: 08d958b0d3fd
Revises: 0cf11ab6d554
Create Date: 2024-10-18 21:32:50.667000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func
import logging

# Set up logging
logging.basicConfig()
logger = logging.getLogger('alembic.runtime.migration')
logger.setLevel(logging.INFO)

# revision identifiers, used by Alembic.
revision: str = '08d958b0d3fd'
down_revision: Union[str, None] = '0cf11ab6d554'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    logger.info("Starting upgrade")
    try:
        op.add_column('users', sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=False))
        op.add_column('users', sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=func.now(), nullable=True))
        
        op.add_column('rooms', sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=False))
        op.add_column('rooms', sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=func.now(), nullable=True))
        
        op.add_column('players', sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=False))
        op.add_column('players', sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=func.now(), nullable=True))
        
        op.add_column('games', sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=False))
        op.add_column('games', sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=func.now(), nullable=True))
        
        op.add_column('rounds', sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=False))
        op.add_column('rounds', sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=func.now(), nullable=True))
        
        op.add_column('sessions', sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=False))
        op.add_column('sessions', sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=func.now(), nullable=True))
        
        op.add_column('dissonance_test_participants', sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=False))
        op.add_column('dissonance_test_participants', sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=func.now(), nullable=True))
        
        logger.info("Upgrade completed successfully")
    except Exception as e:
        logger.error(f"Error during upgrade: {e}")
        raise


def downgrade() -> None:
    logger.info("Starting downgrade")
    try:
        op.drop_column('users', 'created_at')
        op.drop_column('users', 'updated_at')
        
        op.drop_column('rooms', 'created_at')
        op.drop_column('rooms', 'updated_at')
        
        op.drop_column('players', 'created_at')
        op.drop_column('players', 'updated_at')
        
        op.drop_column('games', 'created_at')
        op.drop_column('games', 'updated_at')
        
        op.drop_column('rounds', 'created_at')
        op.drop_column('rounds', 'updated_at')
        
        op.drop_column('sessions', 'created_at')
        op.drop_column('sessions', 'updated_at')
        
        op.drop_column('dissonance_test_participants', 'created_at')
        op.drop_column('dissonance_test_participants', 'updated_at')
        
        logger.info("Downgrade completed successfully")
    except Exception as e:
        logger.error(f"Error during downgrade: {e}")
        raise