# routers.py

from fastapi import APIRouter, Depends, Form, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette.requests import Request
from typing import List
from . import schemas_operations, controllers
from fastapi.responses import JSONResponse
from .schemas import *

from .routes import *


router = APIRouter(
    dependencies=[Depends(db_operations.get_current_user)]
)

router_without_auth = APIRouter()

@router_without_auth.post(LOGIN, response_model=User)
def login_for_access_token(login_request: LoginRequest):
    return controllers.login_for_access_token(login_request)

@router_without_auth.post(REGISTER, response_model=User)
def create_user(user: UserCreate):
    return controllers.create_user(user)

@router.get(GET_USERS, response_model=List[User])
def get_users(db: Session = Depends(db_operations.get_db)):
    return controllers.read_users(db)

@router.get(GET_USER, response_model=User)
def read_user(user_id: int):
    return controllers.read_user(user_id)

@router.get(AUTHENTICATE_USER, response_model=User)
def authenticate_user(user_id: int):
    return controllers.authenticate(user_id)

@router.put(UPDATE_USER, response_model=User)
def update_user(user_id: int, update_user: UserUpdate):
    user = User
    return controllers.update_user(user_id, user)

@router.delete(DELETE_USER, response_model=User)
def delete_user(user_id: int):
    return controllers.delete_user(user_id)

@router.get(GET_ROOMS, response_model=List[Room])
def get_rooms(request: Request):
    return controllers.get_rooms(request)

@router.get(GET_ROOM, response_model=Room)
def read_room(room_id: int):
    return controllers.read_room(room_id)

@router.post(CREATE_ROOM, response_model=Room)
def create_room(request: Request, name: str = Form(...)):
    return controllers.create_room(name, request)

@router.post(DELETE_ROOM, response_model=Room)
def delete_room(room_id: int):
    return controllers.delete_room(room_id)

@router_without_auth.post(CREATE_PLAYER, response_model=Player)
def create_player(player_name: str = Form(...), room_id: int = Form(...)):
    return controllers.create_player(player_name, room_id)

@router_without_auth.get(GET_PLAYERS_BY_ROOM, response_model=List[Player])
def get_players_by_room(room_id: int):
    return controllers.get_players_by_room(room_id)

@router_without_auth.post(UPDATE_PLAYER_TACTIC, response_model=Player)
def update_player_tactic(player_id: int, player_tactic: str = Form(...)):
    return controllers.update_player_tactic(player_id, player_tactic)

@router_without_auth.post(UPDATE_PLAYER_PERSONALITY, response_model=Player)
def update_player_personality_traits(player_id: int, answers: str = Form(...)):
    return controllers.update_player_personality_traits(player_id, answers)

@router.get(GET_PLAYERS_BY_IDS, response_model=List[Player])
def get_players_by_ids(player_ids: str):
    return controllers.get_players_by_ids(player_ids)

@router.post(DELETE_PLAYER, response_model=Player)
def delete_player(player_id: int):
    return controllers.delete_player(player_id)

@router.post(START_GAME, response_model=SessionCreate)
def start_game(room_id: int, background_tasks: BackgroundTasks,  db: Session = Depends(db_operations.get_db), name: str = Form(...)):
    return controllers.start_game(room_id, name, background_tasks)

@router.get(GET_GAME_RESULTS, response_model=Room)
def get_game_results(session_id: int):
    return controllers.get_game_results(session_id)

@router.get(GET_SESSIONS_BY_ROOM, response_model=List[SessionCreate])
def get_sessions_by_room(room_id: int):
    return controllers.get_sessions_by_room(room_id)

@router.get(SHOW_SESSION, response_model=SessionCreate)
def show_session(session_id: int):
    return controllers.get_session(session_id)

@router_without_auth.post(CREATE_DISSONANCE_TEST_PARTICIPANT, response_model=DissonanceTestParticipant)
def create_dissonance_test_participant(participant: DissonanceTestParticipantCreate):
    return controllers.create_dissonance_test_participant(participant=participant)

@router_without_auth.get(READ_DISSONANCE_TEST_PARTICIPANT, response_model=DissonanceTestParticipantResult)
def read_dissonance_test_participant(participant_id: int):
    return controllers.read_dissonance_test_participant(participant_id)

@router.get(GET_DISSONANCE_TEST_PARTICIPANTS, response_model=List[DissonanceTestParticipant])
def get_dissonance_test_participants(request: Request):
    return controllers.get_dissonance_test_participants(request)

@router_without_auth.post(UPDATE_DISSONANCE_TEST_PARTICIPANT, response_model=DissonanceTestParticipant)
def update_dissonance_test_participant(participant_id: int, participant: DissonanceTestParticipantUpdateSecond):
    return controllers.update_dissonance_test_participant(participant_id, participant)

@router_without_auth.post(UPDATE_DISSONANCE_TEST_PARTICIPANT_PERSONALITY, response_model=DissonanceTestParticipant)
def update_dissonance_test_participant_personality_traits(participant_id: int, answers: str = Form(...)):
    return controllers.update_dissonance_test_participant_personality_traits(participant_id, answers)

@router.post(DELETE_DISSONANCE_TEST_PARTICIPANT, response_model=DissonanceTestParticipant)
def delete_dissonance_test_participant(participant_id: int):
    return controllers.delete_dissonance_test_participant(participant_id)

@router_without_auth.get(GET_LANGUAGES, response_model=List[Language])
def get_languages():
    return controllers.get_languages()