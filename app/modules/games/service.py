"""
Game service - Business logic for game operations.
"""

from sqlalchemy.orm import Session

from app import models


class GameService:
    """Service class for game operations."""

    @staticmethod
    def get_session(db: Session, session_id: int):
        """
        Get a session by ID.

        Args:
            db: Database session
            session_id: Session ID

        Returns:
            Session object or None
        """
        return db.query(models.Session).filter(models.Session.id == session_id).first()

    @staticmethod
    def get_games_by_session(db: Session, session_id: int):
        """
        Get all games for a session.

        Args:
            db: Database session
            session_id: Session ID

        Returns:
            List of Game objects
        """
        return db.query(models.Game).filter(models.Game.session_id == session_id).all()

    @staticmethod
    def get_game(db: Session, game_id: int):
        """
        Get a game by ID.

        Args:
            db: Database session
            game_id: Game ID

        Returns:
            Game object or None
        """
        return db.query(models.Game).filter(models.Game.id == game_id).first()

    @staticmethod
    def get_rounds_by_game(db: Session, game_id: int):
        """
        Get all rounds for a game.

        Args:
            db: Database session
            game_id: Game ID

        Returns:
            List of Round objects
        """
        return db.query(models.Round).filter(models.Round.game_id == game_id).all()
