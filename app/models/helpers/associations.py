from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from .database import Base

# Association table for many-to-many relationship between users and rooms
user_room_association = Table(
    'user_room_associations',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('room_id', UUID(as_uuid=True), ForeignKey('rooms.id', ondelete='CASCADE'), primary_key=True)
)
