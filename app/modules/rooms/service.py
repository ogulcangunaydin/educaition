from fastapi import BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app import models
from app.services.prisoners_dilemma import play_game

class RoomService:
    @staticmethod
    def create_room(db: Session, name: str, user_id: int):
        room = models.Room(user_id=user_id, name=name)
        db.add(room)
        db.commit()
        db.refresh(room)
        return room

    @staticmethod
    def get_rooms(db: Session, user_id: int, skip: int = 0, limit: int = 100):
        return (
            db.query(models.Room)
            .filter(models.Room.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_room(db: Session, room_id: int):
        room = db.query(models.Room).get(room_id)
        if room is None:
            raise HTTPException(status_code=404, detail="Room not found")
        return room

    @staticmethod
    def delete_room(db: Session, room_id: int):
        room = db.query(models.Room).get(room_id)
        if room is None:
            raise HTTPException(status_code=404, detail="Room not found")
        
        room.soft_delete()  # Automatically cascades to players and sessions
        db.commit()
        return room

    @staticmethod
    def start_game(
        db: Session,
        room_id: int,
        name: str,
        background_tasks: BackgroundTasks,
    ):
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

        player_ids = ",".join([str(player.id) for player in players])
        new_session = models.Session(
            room_id=room_id, name=name, player_ids=player_ids, status="started"
        )
        db.add(new_session)
        db.commit()

        background_tasks.add_task(play_game, new_session.id)

        return new_session

    @staticmethod
    def get_game_results(db: Session, session_id: int):
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
        return db.query(models.Session).filter(models.Session.room_id == room_id).all()

    @staticmethod
    def get_session(db: Session, session_id: int):
        return db.query(models.Session).filter(models.Session.id == session_id).first()
