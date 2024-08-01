# controllers.py

from sqlalchemy.orm import Session
from . import models, schemas, security, db_operations
from fastapi import HTTPException, Depends, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from datetime import timedelta
from app.services.update_player_tactic_and_test_code import update_player_tactic_and_test_code
from app.services.prisoners_dilemma import play_game
from app.services.calculate_personality_traits import calculate_personality_traits
import os
import bleach
import re
from keyword import iskeyword


def read_users(skip: int = 0, limit: int = 100, db: Session = None):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

def read_user(user_id: int, db: Session = None):
    db_user = db.query(models.User).get(user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

def create_user(user: schemas.UserCreate, db: Session = None):
    clean_name = bleach.clean(user.username, strip=True)
    clean_email = bleach.clean(user.email, strip=True)

    db_user = models.User(username=clean_name, email=clean_email, hashed_password=security.get_password_hash(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(user_id: int, user: schemas.UserCreate, db: Session = None):
    db_user = db.query(models.User).get(user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    cleaned_username = bleach.clean(user.username, strip=True)
    db_user.username = cleaned_username
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

def get_players_by_room(room_id: int, skip: int, limit: int, db: Session):
    return db.query(models.Player).filter(models.Player.room_id == room_id).offset(skip).limit(limit).all()

def get_players_by_ids(player_ids: str, db: Session):
    player_ids = player_ids.split(",")
    return db.query(models.Player).filter(models.Player.id.in_(player_ids)).all()

def create_player_function_name(clean_name):
    # Normalize the name
    normalized_name = clean_name.lower()
    # Replace spaces and invalid characters with underscores
    function_name = re.sub(r'\W|^(?=\d)', '_', normalized_name)
    # Ensure it starts with a valid character
    if not function_name[0].isalpha():
        function_name = "_" + function_name
    # Check for reserved keywords
    if iskeyword(function_name):
        function_name += "_"
    return function_name

def create_player(player_name, room_id, db: Session):
    clean_name = bleach.clean(player_name, strip=True)

    existing_player = db.query(models.Player).filter(models.Player.player_name == clean_name, models.Player.room_id == room_id).first()
    if existing_player:
        raise HTTPException(status_code=400, detail="Player name already exists in the room.")
    
    player_function_name = create_player_function_name(clean_name)
    # If the check passes, proceed to create a new player
    new_player = models.Player(player_name=clean_name, player_function_name=player_function_name, room_id=room_id)
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
    
    cleaned_player_tactic = bleach.clean(player_tactic, strip=True)
    success, player_code = update_player_tactic_and_test_code(cleaned_player_tactic, player.player_function_name)

    # If the service returns true, update the player
    if success:
        player.player_tactic = cleaned_player_tactic
        player.player_code = player_code
        db.commit()
        return player

    # If the service returns false, return an error
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The given tactic is not ok",
        )

def start_game(room_id: int, name: str, db: Session, background_tasks: BackgroundTasks):
    # Existing validation checks
    players = db.query(models.Player).filter(models.Player.room_id == room_id).all()
    if len(players) < 2:
        raise HTTPException(status_code=400, detail="At least two players are required to start a game")
    for player in players:
        if not player.is_ready:
            raise HTTPException(status_code=400, detail="All players are not ready")
    
    # Put players' ids into a comma separated string
    player_ids = ",".join([str(player.id) for player in players])

    # Create a new session
    new_session = models.Session(room_id=room_id, name=name, player_ids= player_ids, status='started')
    db.add(new_session)
    db.commit()
    
    # Initiate the game in the background
    background_tasks.add_task(play_game, new_session.id, db)
    
    # Return the session details
    return new_session

def get_game_results(session_id: int, db: Session):
    # Find the last session created for this room
    session = db.query(models.Session).filter(models.Session.id == session_id).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Please start a game first")
    
    # Check if the last session status is 'finished'
    if session.status == "finished":
        # If finished, return the results stored in the session
        return JSONResponse(content={"results": session.results})
    else:
        # If not finished, return the session object with its status
        return {"session_id": session.id, "status": session.status, "player_ids": session.player_ids}

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

def get_sessions_by_room(room_id: int, db: Session):
    return db.query(models.Session).filter(models.Session.room_id == room_id).all()

def get_session(session_id: int, db: Session):
    return db.query(models.Session).filter(models.Session.id == session_id).first()
