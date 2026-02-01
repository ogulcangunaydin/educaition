import json
import bleach
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import hashlib
import re
import unicodedata
from keyword import iskeyword
from app import models
from app.services.calculate_personality_traits import calculate_personality_traits
from app.services.update_player_tactic_and_test_code import (
    update_player_tactic_and_test_code,
)

def _create_player_function_name(clean_name: str) -> str:
    ascii_normalized_name = (
        unicodedata.normalize("NFKD", clean_name).encode("ASCII", "ignore").decode()
    )
    normalized_name = ascii_normalized_name.lower()
    function_name = re.sub(r"\W|^(?=\d)", "_", normalized_name)

    if not function_name[0].isalpha():
        function_name = "_" + function_name

    unique_identifier = hashlib.md5(clean_name.encode()).hexdigest()[:8]
    function_name += "_" + unique_identifier

    if iskeyword(function_name):
        function_name += "_"

    return function_name

class PlayerService:
    @staticmethod
    def get_players_by_room(db: Session, room_id: int, skip: int = 0, limit: int = 100):
        return (
            db.query(models.Player)
            .filter(models.Player.room_id == room_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_players_by_ids(db: Session, player_ids: str):
        ids = player_ids.split(",")
        return db.query(models.Player).filter(models.Player.id.in_(ids)).all()

    @staticmethod
    def get_player(db: Session, player_id: int):
        player = db.query(models.Player).filter(models.Player.id == player_id).first()
        if player is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found",
            )
        return player

    @staticmethod
    def create_player(db: Session, player_name: str, room_id: int):
        clean_name = bleach.clean(player_name, strip=True)

        existing_player = (
            db.query(models.Player)
            .filter(
                models.Player.player_name == clean_name,
                models.Player.room_id == room_id,
            )
            .first()
        )
        if existing_player:
            raise HTTPException(
                status_code=400, detail="Player name already exists in the room."
            )

        player_function_name = _create_player_function_name(clean_name)
        new_player = models.Player(
            player_name=clean_name,
            player_function_name=player_function_name,
            room_id=room_id,
        )
        db.add(new_player)
        db.commit()
        db.refresh(new_player)
        return new_player

    @staticmethod
    def update_player_tactic(db: Session, player_id: int, player_tactic: str):
        player = db.query(models.Player).filter(models.Player.id == player_id).first()

        if player is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found",
            )

        cleaned_player_tactic = bleach.clean(player_tactic, strip=True)
        success, player_code, short_tactic = update_player_tactic_and_test_code(
            cleaned_player_tactic, player.player_function_name
        )

        if success:
            player.player_tactic = cleaned_player_tactic
            player.player_code = player_code
            player.short_tactic = short_tactic
            db.commit()
            return player
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The given tactic is not ok",
            )

    @staticmethod
    def update_player_personality_traits(db: Session, player_id: int, answers: str):
        player = db.query(models.Player).filter(models.Player.id == player_id).first()

        if player is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found",
            )

        parsed_answers = json.loads(answers)
        personality_scores = calculate_personality_traits(parsed_answers)

        player.extroversion = personality_scores["extroversion"]
        player.agreeableness = personality_scores["agreeableness"]
        player.conscientiousness = personality_scores["conscientiousness"]
        player.negative_emotionality = personality_scores["negative_emotionality"]
        player.open_mindedness = personality_scores["open_mindedness"]

        db.commit()
        return player

    @staticmethod
    def delete_player(db: Session, player_id: int):
        player = db.query(models.Player).get(player_id)
        if player is None:
            raise HTTPException(status_code=404, detail="Player not found")
        db.delete(player)
        db.commit()
        return player
