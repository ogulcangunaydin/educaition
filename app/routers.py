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


def _create_auth_response(token_data: dict) -> JSONResponse:
    response = JSONResponse(
        content={
            "access_token": token_data["access_token"],
            "current_user_id": token_data["current_user_id"],
            "token_type": "bearer",
            "expires_in": token_data["expires_in"],
            "role": token_data.get("role"),
            "university": token_data.get("university"),
        }
    )

    response.set_cookie(
        key="refresh_token",
        value=token_data["refresh_token"],
        httponly=True,
        secure=not settings.is_development,
        samesite="strict",
        max_age=TokenConfig.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api",
    )

    return response


@router_without_auth.post("/authenticate")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    token_data = controllers.login_for_access_token(form_data, db)
    return _create_auth_response(token_data)


@router_without_auth.post("/refresh")
def refresh_token(
    refresh_token: str | None = Cookie(None),
    body_refresh_token: schemas.TokenRefreshRequest | None = Body(None),
):
    token = refresh_token or (body_refresh_token.refresh_token if body_refresh_token else None)

    if not token:
        return JSONResponse(
            status_code=401,
            content={"detail": "Refresh token required"},
        )

    new_tokens = controllers.refresh_access_token(token)
    return _create_auth_response(new_tokens)


@router.post("/logout")
def logout(
    authorization: str = Header(..., description="Bearer token"),
    refresh_token: str | None = Cookie(None),
    body_refresh_token: str | None = Body(None, embed=True),
):
    access_token = authorization.replace("Bearer ", "")
    token_to_revoke = refresh_token or body_refresh_token
    result = controllers.logout_user(access_token, token_to_revoke)

    response = JSONResponse(content=result)
    response.delete_cookie(
        key="refresh_token",
        path="/api",
        httponly=True,
        secure=not settings.is_development,
        samesite="strict",
    )

    return response


@router_without_auth.get(
    "/password-requirements", response_model=schemas.PasswordRequirements
)
def get_password_requirements():
    return schemas.PasswordRequirements()


@router.get("/users/", response_model=list[schemas.User])
def get_users(
    current_user: AdminUser,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return controllers.read_users(skip, limit, db)


@router.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, current_user: AdminUser, db: Session = Depends(get_db)):
    return controllers.read_user(user_id, db)


@router.post("/users/", response_model=schemas.User)
def create_user(
    current_user: AdminUser,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("student"),
    university: str = Form("halic"),
    db: Session = Depends(get_db),
):
    user = schemas.UserCreate(
        username=username,
        email=email,
        password=password,
        role=role,
        university=university,
    )
    return controllers.create_user(user, db)


@router.put("/users/{user_id}", response_model=schemas.User)
def update_user(
    user_id: int,
    current_user: AdminUser,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(None),
    role: str = Form(None),
    university: str = Form(None),
    db: Session = Depends(get_db),
):
    user = schemas.UserUpdate(
        username=username,
        email=email,
        password=password if password else None,
        role=role,
        university=university,
    )
    return controllers.update_user(user_id, user, db)


@router.delete("/users/{user_id}", response_model=schemas.User)
def delete_user(user_id: int, current_user: AdminUser, db: Session = Depends(get_db)):
    return controllers.delete_user(user_id, db)


@router.post("/rooms/", response_model=schemas.Room)
def create_room(
    request: Request,
    current_user: TeacherOrAdmin,
    name: str = Form(...),
    db: Session = Depends(get_db),
):
    return controllers.create_room(name, request, db)


@router.get("/rooms/", response_model=list[schemas.Room])
def get_rooms(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return controllers.get_rooms(request, skip, limit, db)


@router.get("/rooms/{room_id}", response_model=schemas.Room)
def read_room(room_id: int, db: Session = Depends(get_db)):
    return controllers.read_room(room_id, db)


@router.post("/rooms/delete/{room_id}", response_model=schemas.Room)
def delete_room(
    room_id: int, current_user: TeacherOrAdmin, db: Session = Depends(get_db)
):
    return controllers.delete_room(room_id, db)


@router_without_auth.post("/players/")
def create_player(
    player_name: str = Form(...),
    room_id: int = Form(...),
    db: Session = Depends(get_db),
):
    created_player = controllers.create_player(player_name, room_id, db)

    token = create_participant_token(
        participant_id=created_player.id,
        participant_type=ParticipantType.PLAYER,
        room_id=room_id,
    )

    response = JSONResponse(
        content={
            "player": schemas.Player.model_validate(created_player).model_dump(
                mode="json"
            ),
            "session_token": token,
            "expires_in": get_token_expiry_seconds(ParticipantType.PLAYER),
        }
    )

    response.set_cookie(
        key="participant_token",
        value=token,
        httponly=True,
        secure=not settings.is_development,
        samesite="strict",
        max_age=get_token_expiry_seconds(ParticipantType.PLAYER),
    )

    return response


@router_without_auth.get("/players/room/{room_id}", response_model=list[schemas.Player])
def get_players_by_room(
    room_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return controllers.get_players_by_room(room_id, skip, limit, db)


@router_without_auth.post("/players/{player_id}/tactic", response_model=schemas.Player)
def update_player_tactic(
    player_id: int,
    participant: CurrentPlayer,
    player_tactic: str = Form(...),
    db: Session = Depends(get_db),
):
    verify_participant_ownership(participant.participant_id, player_id)
    return controllers.update_player_tactic(player_id, player_tactic, db)


@router_without_auth.post(
    "/players/{player_id}/personality", response_model=schemas.Player
)
def update_player_personality_traits(
    player_id: int,
    participant: CurrentPlayer,
    answers: str = Form(...),
    db: Session = Depends(get_db),
):
    verify_participant_ownership(participant.participant_id, player_id)
    return controllers.update_player_personality_traits(player_id, answers, db)


@router.get("/players/{player_ids}", response_model=list[schemas.Player])
def get_players_by_ids(player_ids: str, db: Session = Depends(get_db)):
    return controllers.get_players_by_ids(player_ids, db)


@router.post("/players/delete/{player_id}", response_model=schemas.Player)
def delete_player(
    player_id: int, current_user: TeacherOrAdmin, db: Session = Depends(get_db)
):
    return controllers.delete_player(player_id, db)


@router.post("/rooms/{room_id}/ready", response_model=schemas.SessionCreate)
def start_game(
    room_id: int,
    background_tasks: BackgroundTasks,
    current_user: TeacherOrAdmin,
    db: Session = Depends(get_db),
    name: str = Form(...),
):
    return controllers.start_game(room_id, name, db, background_tasks)


@router.get("/rooms/{session_id}/results", response_model=schemas.Room)
def get_game_results(session_id: int, db: Session = Depends(get_db)):
    return controllers.get_game_results(session_id, db)


@router.get("/rooms/{room_id}/sessions", response_model=list[schemas.SessionCreate])
def get_sessions_by_room(room_id: int, db: Session = Depends(get_db)):
    return controllers.get_sessions_by_room(room_id, db)


@router.get("/sessions/{session_id}", response_model=schemas.SessionCreate)
def show_session(session_id: int, db: Session = Depends(get_db)):
    return controllers.get_session(session_id, db)


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
