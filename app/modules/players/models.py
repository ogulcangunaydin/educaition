from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.mixins import SoftDeleteMixin


class Player(Base, SoftDeleteMixin):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    player_name = Column(String, index=True)
    player_function_name = Column(String)
    player_tactic = Column(String)
    short_tactic = Column(String)
    player_code = Column(String)
    room_id = Column(Integer, ForeignKey("rooms.id"), index=True)
    extroversion = Column(Float)
    agreeableness = Column(Float)
    conscientiousness = Column(Float)
    negative_emotionality = Column(Float)
    open_mindedness = Column(Float)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    room = relationship("Room", back_populates="players")

    @property
    def is_ready(self):
        return bool(self.player_tactic and self.player_code)
