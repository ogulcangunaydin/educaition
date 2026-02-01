from fastapi import HTTPException
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
    def get_game(db: Session, session_id: int, game_id: int):
        game = (
            db.query(models.Game)
            .filter(
                models.Game.id == game_id,
                models.Game.session_id == session_id,
            )
            .first()
        )

        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")

        return game

    @staticmethod
    def get_rounds_by_game(db: Session, session_id: int, game_id: int):
        game = (
            db.query(models.Game)
            .filter(
                models.Game.id == game_id,
                models.Game.session_id == session_id,
            )
            .first()
        )

        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")

        return db.query(models.Round).filter(models.Round.game_id == game_id).all()
