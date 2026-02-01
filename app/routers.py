# routers.py


from fastapi import APIRouter, BackgroundTasks, Body, Cookie, Depends, Form, Header
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette.requests import Request

from . import controllers, schemas
from .config import settings
from .dependencies import (
    AdminUser,
    CurrentPlayer,
    CurrentProgramStudent,
    CurrentTestParticipant,
    TeacherOrAdmin,
    get_current_active_user,
    get_db,
    require_admin,
    require_teacher_or_admin,
    verify_participant_ownership,
)
from .services.participant_token_service import (
    ParticipantType,
    create_participant_token,
    get_token_expiry_seconds,
)
from .services.token_service import TokenConfig

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


@router.get("/auth/", response_model=schemas.User)
def authenticate_user(request: Request, db: Session = Depends(get_db)):
    return controllers.authenticate(request, db)


@router_without_auth.post("/dissonance_test_participants/")
def create_dissonance_test_participant(
    participant: schemas.DissonanceTestParticipantCreate,
    db: Session = Depends(get_db),
):
    created_participant = controllers.create_dissonance_test_participant(
        db=db, participant=participant
    )

    # Use user_id as a pseudo room_id for dissonance tests
    token = create_participant_token(
        participant_id=created_participant.id,
        participant_type=ParticipantType.DISSONANCE_TEST,
        room_id=created_participant.user_id,
    )

    response = JSONResponse(
        content={
            "participant": schemas.DissonanceTestParticipant.model_validate(
                created_participant
            ).model_dump(mode="json"),
            "session_token": token,
            "expires_in": get_token_expiry_seconds(ParticipantType.DISSONANCE_TEST),
        }
    )

    response.set_cookie(
        key="participant_token",
        value=token,
        httponly=True,
        secure=not settings.is_development,
        samesite="strict",
        max_age=get_token_expiry_seconds(ParticipantType.DISSONANCE_TEST),
    )

    return response


@router_without_auth.get(
    "/dissonance_test_participants/{participant_id}",
    response_model=schemas.DissonanceTestParticipantResult,
)
def read_dissonance_test_participant(
    participant_id: int,
    participant: CurrentTestParticipant,
    db: Session = Depends(get_db),
):
    verify_participant_ownership(participant.participant_id, participant_id)
    return controllers.read_dissonance_test_participant(participant_id, db)


@router.get(
    "/dissonance_test_participants/",
    response_model=list[schemas.DissonanceTestParticipant],
)
def get_dissonance_test_participants(request: Request, db: Session = Depends(get_db)):
    return controllers.get_dissonance_test_participants(request, db)


@router_without_auth.post(
    "/dissonance_test_participants/{participant_id}",
    response_model=schemas.DissonanceTestParticipant,
)
def update_dissonance_test_participant(
    participant_id: int,
    participant_data: schemas.DissonanceTestParticipantUpdateSecond,
    participant: CurrentTestParticipant,
    db: Session = Depends(get_db),
):
    verify_participant_ownership(participant.participant_id, participant_id)
    return controllers.update_dissonance_test_participant(
        participant_id, participant_data, db
    )


@router_without_auth.post(
    "/dissonance_test_participants/{participant_id}/personality",
    response_model=schemas.DissonanceTestParticipant,
)
def update_dissonance_test_participant_personality_traits(
    participant_id: int,
    participant: CurrentTestParticipant,
    answers: str = Form(...),
    db: Session = Depends(get_db),
):
    verify_participant_ownership(participant.participant_id, participant_id)
    return controllers.update_dissonance_test_participant_personality_traits(
        participant_id, answers, db
    )


@router.post(
    "/dissonance_test_participants/{participant_id}/delete",
    response_model=schemas.DissonanceTestParticipant,
)
def delete_dissonance_test_participant(
    participant_id: int, current_user: TeacherOrAdmin, db: Session = Depends(get_db)
):
    return controllers.delete_dissonance_test_participant(participant_id, db)


# High School Room Routes
@router.post("/high-school-rooms/", response_model=schemas.HighSchoolRoom)
def create_high_school_room(
    request: Request,
    current_user: TeacherOrAdmin,
    high_school_name: str = Form(...),
    high_school_code: str = Form(None),
    db: Session = Depends(get_db),
):
    return controllers.create_high_school_room(
        high_school_name, high_school_code, request, db
    )


@router.get("/high-school-rooms/", response_model=list[schemas.HighSchoolRoom])
def get_high_school_rooms(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return controllers.get_high_school_rooms(request, skip, limit, db)


@router.get("/high-school-rooms/{room_id}", response_model=schemas.HighSchoolRoom)
def get_high_school_room(room_id: int, db: Session = Depends(get_db)):
    return controllers.get_high_school_room(room_id, db)


@router.delete("/high-school-rooms/{room_id}", response_model=schemas.HighSchoolRoom)
def delete_high_school_room(
    room_id: int, current_user: TeacherOrAdmin, db: Session = Depends(get_db)
):
    return controllers.delete_high_school_room(room_id, db)


@router.get(
    "/high-school-rooms/{room_id}/students",
    response_model=list[schemas.ProgramSuggestionStudent],
)
def get_high_school_room_students(room_id: int, db: Session = Depends(get_db)):
    return controllers.get_high_school_room_students(room_id, db)


@router_without_auth.post("/program-suggestion/students/")
def create_program_suggestion_student(
    student: schemas.ProgramSuggestionStudentCreate,
    db: Session = Depends(get_db),
):
    created_student = controllers.create_program_suggestion_student(
        student.high_school_room_id, db
    )

    token = create_participant_token(
        participant_id=created_student.id,
        participant_type=ParticipantType.PROGRAM_SUGGESTION,
        room_id=student.high_school_room_id,
    )

    response = JSONResponse(
        content={
            "student": schemas.ProgramSuggestionStudent.model_validate(
                created_student
            ).model_dump(mode="json"),
            "session_token": token,
            "expires_in": get_token_expiry_seconds(ParticipantType.PROGRAM_SUGGESTION),
        }
    )

    response.set_cookie(
        key="participant_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=get_token_expiry_seconds(ParticipantType.PROGRAM_SUGGESTION),
    )

    return response


@router_without_auth.get(
    "/program-suggestion/students/{student_id}",
    response_model=schemas.ProgramSuggestionStudent,
)
def get_program_suggestion_student(
    student_id: int,
    participant: CurrentProgramStudent,
    db: Session = Depends(get_db),
):
    verify_participant_ownership(participant.participant_id, student_id)
    return controllers.get_program_suggestion_student(student_id, db)


@router_without_auth.post(
    "/program-suggestion/students/{student_id}/step1",
    response_model=schemas.ProgramSuggestionStudent,
)
def update_student_step1(
    student_id: int,
    data: schemas.ProgramSuggestionStudentUpdateStep1,
    participant: CurrentProgramStudent,
    db: Session = Depends(get_db),
):
    verify_participant_ownership(participant.participant_id, student_id)
    return controllers.update_student_step1(student_id, data, db)


@router_without_auth.post(
    "/program-suggestion/students/{student_id}/step2",
    response_model=schemas.ProgramSuggestionStudent,
)
def update_student_step2(
    student_id: int,
    data: schemas.ProgramSuggestionStudentUpdateStep2,
    participant: CurrentProgramStudent,
    db: Session = Depends(get_db),
):
    verify_participant_ownership(participant.participant_id, student_id)
    return controllers.update_student_step2(student_id, data, db)


@router_without_auth.post(
    "/program-suggestion/students/{student_id}/step3",
    response_model=schemas.ProgramSuggestionStudent,
)
def update_student_step3(
    student_id: int,
    data: schemas.ProgramSuggestionStudentUpdateStep3,
    participant: CurrentProgramStudent,
    db: Session = Depends(get_db),
):
    verify_participant_ownership(participant.participant_id, student_id)
    return controllers.update_student_step3(student_id, data, db)


@router_without_auth.post(
    "/program-suggestion/students/{student_id}/step4",
    response_model=schemas.ProgramSuggestionStudent,
)
def update_student_step4(
    student_id: int,
    data: schemas.ProgramSuggestionStudentUpdateStep4,
    participant: CurrentProgramStudent,
    db: Session = Depends(get_db),
):
    verify_participant_ownership(participant.participant_id, student_id)
    return controllers.update_student_step4(student_id, data, db)


@router_without_auth.post(
    "/program-suggestion/students/{student_id}/riasec",
    response_model=schemas.ProgramSuggestionStudent,
)
def update_student_riasec(
    student_id: int,
    data: schemas.ProgramSuggestionStudentUpdateRiasec,
    participant: CurrentProgramStudent,
    db: Session = Depends(get_db),
):
    verify_participant_ownership(participant.participant_id, student_id)
    return controllers.update_student_riasec(student_id, data, db)


@router_without_auth.get(
    "/program-suggestion/students/{student_id}/result",
    response_model=schemas.ProgramSuggestionStudentResult,
)
def get_student_result(
    student_id: int,
    participant: CurrentProgramStudent,
    db: Session = Depends(get_db),
):
    verify_participant_ownership(participant.participant_id, student_id)
    return controllers.get_student_result(student_id, db)


@router.get(
    "/program-suggestion/students/{student_id}/debug",
    response_model=schemas.ProgramSuggestionStudentDebug,
)
def get_student_debug(
    student_id: int, current_user: AdminUser, db: Session = Depends(get_db)
):
    return controllers.get_student_debug(student_id, db)
