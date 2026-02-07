import json
import logging
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
from app.services.tactic_analysis_service import (
    generate_tactic_reasons,
    generate_job_recommendation,
)
from app.modules.players.schemas import PlayerRegister

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
    def register_player(db: Session, data: PlayerRegister, is_privileged: bool = False):
        """
        Standardized player registration used by TestRegistrationCard.
        Resolves test_room_id → legacy_room_id for the players FK.
        Handles duplicate device_fingerprint by returning 409 (skipped for admin/teacher).
        """
        # Resolve test_room_id → legacy_room_id (players FK to rooms.id)
        test_room = (
            db.query(models.TestRoom)
            .filter(models.TestRoom.id == data.test_room_id)
            .first()
        )
        if not test_room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test room not found",
            )

        if test_room.legacy_room_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Test room has no associated game room",
            )

        room_id = test_room.legacy_room_id
        clean_name = bleach.clean(data.full_name, strip=True)

        # Check for duplicate device_fingerprint in same room (skip for privileged users)
        if data.device_fingerprint and not is_privileged:
            existing = (
                db.query(models.Player)
                .filter(
                    models.Player.device_fingerprint == data.device_fingerprint,
                    models.Player.room_id == room_id,
                )
                .first()
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Already registered from this device",
                )

        # Check for duplicate name in room
        existing_name = (
            db.query(models.Player)
            .filter(
                models.Player.player_name == clean_name,
                models.Player.room_id == room_id,
            )
            .first()
        )
        if existing_name:
            raise HTTPException(
                status_code=400, detail="Player name already exists in the room."
            )

        player_function_name = _create_player_function_name(clean_name)
        new_player = models.Player(
            player_name=clean_name,
            player_function_name=player_function_name,
            student_number=data.student_number,
            device_fingerprint=data.device_fingerprint,
            student_user_id=data.student_user_id,
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
    def get_tactic_reasons(db: Session, player_id: int, language: str = "tr") -> list[str]:
        """Generate probable reasons for choosing the player's tactic via GPT."""
        player = db.query(models.Player).filter(models.Player.id == player_id).first()

        if player is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found",
            )

        if not player.player_tactic:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Player has no tactic submitted yet",
            )

        reasons = generate_tactic_reasons(player.player_tactic, language)
        return reasons

    @staticmethod
    def submit_tactic_reason(db: Session, player_id: int, reason: str, language: str = "tr"):
        """Save the selected tactic reason and generate job recommendation via GPT."""
        player = db.query(models.Player).filter(models.Player.id == player_id).first()

        if player is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found",
            )

        if not player.player_tactic:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Player has no tactic submitted yet",
            )

        cleaned_reason = bleach.clean(reason, strip=True)
        player.tactic_reason = cleaned_reason

        try:
            job_rec = generate_job_recommendation(
                player.player_tactic, cleaned_reason, language
            )
            player.job_recommendation = job_rec
        except Exception as e:
            logging.error(f"Failed to generate job recommendation for player {player_id}: {e}")

        db.commit()
        db.refresh(player)
        return player

    @staticmethod
    def delete_player(db: Session, player_id: int):
        player = db.query(models.Player).get(player_id)
        if player is None:
            raise HTTPException(status_code=404, detail="Player not found")
        player.soft_delete()
        db.commit()
        return player
