"""
Player service - Business logic for player management.
"""

import json

import bleach
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.helpers import create_player_function_name
from app.services.calculate_personality_traits import calculate_personality_traits
from app.services.update_player_tactic_and_test_code import (
    update_player_tactic_and_test_code,
)


class PlayerService:
    """Service class for player operations."""

    @staticmethod
    def get_players_by_room(
        db: Session, room_id: int, skip: int = 0, limit: int = 100
    ):
        """
        Get all players in a room.

        Args:
            db: Database session
            room_id: Room ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Player objects
        """
        return (
            db.query(models.Player)
            .filter(models.Player.room_id == room_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_players_by_ids(db: Session, player_ids: str):
        """
        Get players by comma-separated IDs.

        Args:
            db: Database session
            player_ids: Comma-separated player IDs

        Returns:
            List of Player objects
        """
        ids = player_ids.split(",")
        return db.query(models.Player).filter(models.Player.id.in_(ids)).all()

    @staticmethod
    def get_player(db: Session, player_id: int):
        """
        Get a player by ID.

        Args:
            db: Database session
            player_id: Player ID

        Returns:
            Player object

        Raises:
            HTTPException: If player not found
        """
        player = db.query(models.Player).filter(models.Player.id == player_id).first()
        if player is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found",
            )
        return player

    @staticmethod
    def create_player(db: Session, player_name: str, room_id: int):
        """
        Create a new player in a room.

        Args:
            db: Database session
            player_name: Player name
            room_id: Room ID

        Returns:
            Created Player object

        Raises:
            HTTPException: If player name already exists in room
        """
        clean_name = bleach.clean(player_name, strip=True)

        # Check for existing player in room
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

        # Create player
        player_function_name = create_player_function_name(clean_name)
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
        """
        Update a player's tactic.

        Args:
            db: Database session
            player_id: Player ID
            player_tactic: New tactic description

        Returns:
            Updated Player object

        Raises:
            HTTPException: If player not found or tactic invalid
        """
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
        """
        Update a player's personality traits based on test answers.

        Args:
            db: Database session
            player_id: Player ID
            answers: JSON string of personality test answers

        Returns:
            Updated Player object

        Raises:
            HTTPException: If player not found
        """
        player = db.query(models.Player).filter(models.Player.id == player_id).first()

        if player is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found",
            )

        # Calculate personality scores
        parsed_answers = json.loads(answers)
        personality_scores = calculate_personality_traits(parsed_answers)

        # Update player
        player.extroversion = personality_scores["extroversion"]
        player.agreeableness = personality_scores["agreeableness"]
        player.conscientiousness = personality_scores["conscientiousness"]
        player.negative_emotionality = personality_scores["negative_emotionality"]
        player.open_mindedness = personality_scores["open_mindedness"]

        db.commit()
        return player

    @staticmethod
    def delete_player(db: Session, player_id: int):
        """
        Delete a player.

        Args:
            db: Database session
            player_id: Player ID

        Returns:
            Deleted Player object

        Raises:
            HTTPException: If player not found
        """
        player = db.query(models.Player).get(player_id)
        if player is None:
            raise HTTPException(status_code=404, detail="Player not found")
        db.delete(player)
        db.commit()
        return player
