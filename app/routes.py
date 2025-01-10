from fastapi import APIRouter, Depends
from . import db_operations

router = APIRouter(
    dependencies=[Depends(db_operations.get_current_user)]
)

router_without_auth = APIRouter()

# Authentication routes
LOGIN = "/login"
REGISTER = "/register/"

# Language routes
GET_LANGUAGES = "/languages/"

# User routes
GET_USERS = "/users/"
GET_USER = "/users/{user_id}"
AUTHENTICATE_USER = "/users/{user_id}/authenticate"
UPDATE_USER = "/users/{user_id}"
DELETE_USER = "/users/{user_id}"

# Room routes
GET_ROOMS = "/rooms/"
GET_ROOM = "/rooms/{room_id}"
CREATE_ROOM = "/rooms/"
DELETE_ROOM = "/rooms/delete/{room_id}"

# Player routes
CREATE_PLAYER = "/players/"
GET_PLAYERS_BY_ROOM = "/players/room/{room_id}"
UPDATE_PLAYER_TACTIC = "/players/{player_id}/tactic"
UPDATE_PLAYER_PERSONALITY = "/players/{player_id}/personality"
GET_PLAYERS_BY_IDS = "/players/{player_ids}"
DELETE_PLAYER = "/players/delete/{player_id}"

# Game routes
START_GAME = "/rooms/{room_id}/ready"
GET_GAME_RESULTS = "/rooms/{session_id}/results"
GET_SESSIONS_BY_ROOM = "/rooms/{room_id}/sessions"
SHOW_SESSION = "/sessions/{session_id}"

# Dissonance Test Participant routes
CREATE_DISSONANCE_TEST_PARTICIPANT = "/dissonance_test_participants/"
READ_DISSONANCE_TEST_PARTICIPANT = "/dissonance_test_participants/{participant_id}"
GET_DISSONANCE_TEST_PARTICIPANTS = "/dissonance_test_participants/"
UPDATE_DISSONANCE_TEST_PARTICIPANT = "/dissonance_test_participants/{participant_id}"
UPDATE_DISSONANCE_TEST_PARTICIPANT_PERSONALITY = "/dissonance_test_participants/{participant_id}/personality"
DELETE_DISSONANCE_TEST_PARTICIPANT = "/dissonance_test_participants/{participant_id}/delete"
