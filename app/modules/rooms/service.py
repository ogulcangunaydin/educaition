"""
Room service - Business logic for room management.
"""

from fastapi import BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette.requests import Request

from app import models
from app.services.prisoners_dilemma import play_game


class RoomService:
    """Service class for room operations."""

    @staticmethod
    def create_room(db: Session, name: str, request: Request):
        """
        Create a new room.

        Args:
            db: Database session
            name: Room name
            request: Request object (contains user session)

        Returns:
            Created Room object
        """
        user_id = request.session["current_user"]["id"]
        room = models.Room(user_id=user_id, name=name)
        db.add(room)
        db.commit()
        db.refresh(room)
        return room

    @staticmethod
    def get_rooms(db: Session, request: Request, skip: int = 0, limit: int = 100):
        """
        Get all rooms for the current user.

        Args:
            db: Database session
            request: Request object (contains user session)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Room objects
        """
        user_id = request.session["current_user"]["id"]
        return (
            db.query(models.Room)
            .filter(models.Room.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_room(db: Session, room_id: int):
        """
        Get a room by ID.

        Args:
            db: Database session
            room_id: Room ID

        Returns:
            Room object

        Raises:
            HTTPException: If room not found
        """
        room = db.query(models.Room).get(room_id)
        if room is None:
            raise HTTPException(status_code=404, detail="Room not found")
        return room

    @staticmethod
    def delete_room(db: Session, room_id: int):
        """
        Delete a room.

        Args:
            db: Database session
            room_id: Room ID

        Returns:
            Deleted Room object

        Raises:
            HTTPException: If room not found
        """
        room = db.query(models.Room).get(room_id)
        if room is None:
            raise HTTPException(status_code=404, detail="Room not found")
        db.delete(room)
        db.commit()
        return room

    @staticmethod
    def start_game(
        db: Session,
        room_id: int,
        name: str,
        background_tasks: BackgroundTasks,
    ):
        """
        Start a game session for a room.

        Args:
            db: Database session
            room_id: Room ID
            name: Session name
            background_tasks: FastAPI background tasks

        Returns:
            Created Session object

        Raises:
            HTTPException: If not enough players or players not ready
        """
        # Validate players
        players = db.query(models.Player).filter(models.Player.room_id == room_id).all()
        if len(players) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least two players are required to start a game",
            )
        for player in players:
            if not player.is_ready:
                raise HTTPException(
                    status_code=400, detail="All players are not ready"
                )

        # Create session
        player_ids = ",".join([str(player.id) for player in players])
        new_session = models.Session(
            room_id=room_id, name=name, player_ids=player_ids, status="started"
        )
        db.add(new_session)
        db.commit()

        # Start game in background
        background_tasks.add_task(play_game, new_session.id)

        return new_session

    @staticmethod
    def get_game_results(db: Session, session_id: int):
        """
        Get game results for a session.

        Args:
            db: Database session
            session_id: Session ID

        Returns:
            Game results or session status

        Raises:
            HTTPException: If session not found
        """
        session = (
            db.query(models.Session).filter(models.Session.id == session_id).first()
        )

        if not session:
            raise HTTPException(status_code=404, detail="Please start a game first")

        if session.status == "finished":
            return JSONResponse(content={"results": session.results})
        else:
            return {
                "session_id": session.id,
                "status": session.status,
                "player_ids": session.player_ids,
            }

    @staticmethod
    def get_sessions_by_room(db: Session, room_id: int):
        """
        Get all sessions for a room.

        Args:
            db: Database session
            room_id: Room ID

        Returns:
            List of Session objects
        """
        return db.query(models.Session).filter(models.Session.room_id == room_id).all()

    @staticmethod
    def get_session(db: Session, session_id: int):
        """
        Get a session by ID.

        Args:
            db: Database session
            session_id: Session ID

        Returns:
            Session object
        """
        return db.query(models.Session).filter(models.Session.id == session_id).first()
