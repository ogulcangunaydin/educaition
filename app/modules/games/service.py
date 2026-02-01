from sqlalchemy.orm import Session

from app import models


class GameService:

    @staticmethod
    def get_session(db: Session, session_id: int):
        return db.query(models.Session).filter(models.Session.id == session_id).first()

    @staticmethod
    def get_games_by_session(db: Session, session_id: int):
        return db.query(models.Game).filter(models.Game.session_id == session_id).all()

    @staticmethod
    def get_game(db: Session, game_id: int):
        return db.query(models.Game).filter(models.Game.id == game_id).first()

    @staticmethod
    def get_rounds_by_game(db: Session, game_id: int):
        return db.query(models.Round).filter(models.Round.game_id == game_id).all()
