# controllers.py

from sqlalchemy.orm import Session
from . import models, schemas, security, db_operations
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from datetime import timedelta
from app.services.update_player_tactic_and_test_code import update_player_tactic_and_test_code
from app.services.prisoners_dilemma import play_game, calculate_leaderboard_and_scores_matrix
from app.services.calculate_personality_traits import calculate_personality_traits
from typing import List
import os


def read_users(skip: int = 0, limit: int = 100, db: Session = None):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

def read_user(user_id: int, db: Session = None):
    db_user = db.query(models.User).get(user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

def create_user(user: schemas.UserCreate, db: Session = None):
    db_user = models.User(username=user.username, email=user.email, hashed_password=security.get_password_hash(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(user_id: int, user: schemas.UserCreate, db: Session = None):
    db_user = db.query(models.User).get(user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.username = user.username
    db_user.hashed_password = security.get_password_hash(user.password)
    db.commit()
    return db_user

def delete_user(user_id: int, db: Session = None):
    db_user = db.query(models.User).get(user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return db_user

def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = None):
    user = db_operations.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

def create_room(name: str, request: None, db: Session):
    user_id = request.session["current_user"]["id"]
    room = models.Room(user_id=user_id, name=name)
    db.add(room)
    db.commit()
    db.refresh(room)
    return room

def get_rooms(request: None, skip: int, limit: int, db: Session = None):
    user_id = request.session["current_user"]["id"]
    return db.query(models.Room).filter(models.Room.user_id == user_id).offset(skip).limit(limit).all()

def delete_room(room_id: int, db: Session):
    room = db.query(models.Room).get(room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    db.delete(room)
    db.commit()
    return room

def get_players(room_id: int, skip: int, limit: int, db: Session):
    return db.query(models.Player).filter(models.Player.room_id == room_id).offset(skip).limit(limit).all()

def create_player(player: schemas.PlayerCreate, db: Session):
    existing_player = db.query(models.Player).filter(models.Player.player_name == player.player_name, models.Player.room_id == player.room_id).first()
    if existing_player:
        raise HTTPException(status_code=400, detail="Player name already exists in the room.")
    
    # If the check passes, proceed to create a new player
    new_player = models.Player(player_name=player.player_name, room_id=player.room_id)
    db.add(new_player)
    db.commit()
    db.refresh(new_player)
    return new_player

def update_player_tactic(player_id: int, player_tactic: str, db: Session):
    # Call the service to update the player's tactic and test the generated code
    player = db.query(models.Player).filter(models.Player.id == player_id).first()
    
    if player is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found",
        )
    
    success, player_code = update_player_tactic_and_test_code(player_tactic, player.player_name)

    # If the service returns true, update the player
    if success:
        player.player_tactic = player_tactic
        player.player_code = player_code
        db.commit()
        return player

    # If the service returns false, return an error
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The given tactic is not ok",
        )

def start_game(room_id: int, db: Session):
    # Fetch the players in the room
    players = db.query(models.Player).filter(models.Player.room_id == room_id).all()

    # Ensure there are at least two players
    if len(players) < 2:
        raise HTTPException(status_code=400, detail="At least two players are required to start a game")

    # Ensure all players are ready
    for player in players:
        if not player.is_ready:
            raise HTTPException(status_code=400, detail="All players are not ready")

    # Make the players play the game
    play_game(players, db)
    
    # Refresh the session
    for player in players:
        db.refresh(player)

    # Calculate the leaderboard
    leaderboard, matrix = calculate_leaderboard_and_scores_matrix(players, db)
    # Return the leaderboard as a JSON response
    return JSONResponse(content={"leaderboard": leaderboard, "matrix": matrix})

def authenticate(request: None, db: Session):
    user_id = request.session["current_user"]["id"]
    return db.query(models.User).filter(models.User.id == user_id).first()

def update_player_personality_traits(player_id: int, answers: str, db: Session):
    # Retrieve the player from the database
    player = db.query(models.Player).filter(models.Player.id == player_id).first()
    
    if player is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found",
        )
    
    # Calculate personality scores using the previously defined function
    personality_scores = calculate_personality_traits(answers)
    
    # Update the player with the calculated personality traits
    player.extroversion = personality_scores["extroversion"]
    player.agreeableness = personality_scores["agreeableness"]
    player.conscientiousness = personality_scores["conscientiousness"]
    player.negative_emotionality = personality_scores["negative_emotionality"]
    player.open_mindedness = personality_scores["open_mindedness"]
    
    db.commit()
    return player
