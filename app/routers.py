# routers.py


from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.requests import Request

from . import controllers, schemas
from .dependencies import get_current_active_user, get_db

router = APIRouter(dependencies=[Depends(get_current_active_user)])

router_without_auth = APIRouter()


# Auth routes moved to app.modules.auth.router
# The following functions kept for backward compatibility but routes removed
# _create_auth_response, login_for_access_token, refresh_token, logout, get_password_requirements

# User routes moved to app.modules.users.router
# get_users, read_user, create_user, update_user, delete_user

# Room routes moved to app.modules.rooms.router
# create_room, get_rooms, read_room, delete_room, start_game, get_game_results, get_sessions_by_room

# Player routes moved to app.modules.players.router
# create_player, get_players_by_room, update_player_tactic, update_player_personality_traits, get_players_by_ids, delete_player

# Session routes moved to app.modules.games.router
# show_session

# Dissonance test routes moved to app.modules.dissonance_test.router
# create_dissonance_test_participant, read_dissonance_test_participant,
# get_dissonance_test_participants, update_dissonance_test_participant,
# update_dissonance_test_participant_personality_traits, delete_dissonance_test_participant


@router.get("/auth/", response_model=schemas.User)
def authenticate_user(request: Request, db: Session = Depends(get_db)):
    return controllers.authenticate(request, db)


# High School Room Routes moved to app.modules.high_school_rooms.router
# create_high_school_room, get_high_school_rooms, get_high_school_room,
# delete_high_school_room, get_high_school_room_students

# Program Suggestion Routes moved to app.modules.program_suggestion.router
# create_program_suggestion_student, get_program_suggestion_student,
# update_student_step1, update_student_step2, update_student_step3, update_student_step4,
# update_student_riasec, get_student_result, get_student_debug
