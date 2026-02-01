# routers.py


from fastapi import APIRouter, BackgroundTasks, Depends, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette.requests import Request

from . import controllers, db_operations, schemas

router = APIRouter(dependencies=[Depends(db_operations.get_current_user)])

router_without_auth = APIRouter()


@router_without_auth.post("/authenticate", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(db_operations.get_db),
):
    return controllers.login_for_access_token(form_data, db)


@router_without_auth.get(
    "/password-requirements", response_model=schemas.PasswordRequirements
)
def get_password_requirements():
    return schemas.PasswordRequirements()


@router.get("/users/", response_model=list[schemas.User])
def get_users(
    skip: int = 0, limit: int = 100, db: Session = Depends(db_operations.get_db)
):
    return controllers.read_users(skip, limit, db)


@router.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(db_operations.get_db)):
    return controllers.read_user(user_id, db)


@router.post("/users/", response_model=schemas.User)
def create_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(db_operations.get_db),
):
    user = schemas.UserCreate(username=username, email=email, password=password)
    return controllers.create_user(user, db)


@router.put("/users/{user_id}", response_model=schemas.User)
def update_user(
    user_id: int,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(db_operations.get_db),
):
    user = schemas.UserCreate(username=username, email=email, password=password)
    return controllers.update_user(user_id, user, db)


@router.delete("/users/{user_id}", response_model=schemas.User)
def delete_user(user_id: int, db: Session = Depends(db_operations.get_db)):
    return controllers.delete_user(user_id, db)


@router.post("/rooms/", response_model=schemas.Room)
def create_room(
    request: Request, name: str = Form(...), db: Session = Depends(db_operations.get_db)
):
    return controllers.create_room(name, request, db)


@router.get("/rooms/", response_model=list[schemas.Room])
def get_rooms(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(db_operations.get_db),
):
    return controllers.get_rooms(request, skip, limit, db)


@router.get("/rooms/{room_id}", response_model=schemas.Room)
def read_room(room_id: int, db: Session = Depends(db_operations.get_db)):
    return controllers.read_room(room_id, db)


@router.post("/rooms/delete/{room_id}", response_model=schemas.Room)
def delete_room(room_id: int, db: Session = Depends(db_operations.get_db)):
    return controllers.delete_room(room_id, db)


@router_without_auth.post("/players/", response_model=schemas.Player)
def create_player(
    player_name: str = Form(...),
    room_id: int = Form(...),
    db: Session = Depends(db_operations.get_db),
):
    return controllers.create_player(player_name, room_id, db)


@router_without_auth.get("/players/room/{room_id}", response_model=list[schemas.Player])
def get_players_by_room(
    room_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(db_operations.get_db),
):
    return controllers.get_players_by_room(room_id, skip, limit, db)


@router_without_auth.post("/players/{player_id}/tactic", response_model=schemas.Player)
def update_player_tactic(
    player_id: int,
    player_tactic: str = Form(...),
    db: Session = Depends(db_operations.get_db),
):
    return controllers.update_player_tactic(player_id, player_tactic, db)


@router_without_auth.post(
    "/players/{player_id}/personality", response_model=schemas.Player
)
def update_player_personality_traits(
    player_id: int,
    answers: str = Form(...),
    db: Session = Depends(db_operations.get_db),
):
    return controllers.update_player_personality_traits(player_id, answers, db)


@router.get("/players/{player_ids}", response_model=list[schemas.Player])
def get_players_by_ids(player_ids: str, db: Session = Depends(db_operations.get_db)):
    return controllers.get_players_by_ids(player_ids, db)


@router.post("/players/delete/{player_id}", response_model=schemas.Player)
def delete_player(player_id: int, db: Session = Depends(db_operations.get_db)):
    return controllers.delete_player(player_id, db)


@router.post("/rooms/{room_id}/ready", response_model=schemas.SessionCreate)
def start_game(
    room_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(db_operations.get_db),
    name: str = Form(...),
):
    return controllers.start_game(room_id, name, db, background_tasks)


@router.get("/rooms/{session_id}/results", response_model=schemas.Room)
def get_game_results(session_id: int, db: Session = Depends(db_operations.get_db)):
    return controllers.get_game_results(session_id, db)


@router.get("/rooms/{room_id}/sessions", response_model=list[schemas.SessionCreate])
def get_sessions_by_room(room_id: int, db: Session = Depends(db_operations.get_db)):
    return controllers.get_sessions_by_room(room_id, db)


@router.get("/sessions/{session_id}", response_model=schemas.SessionCreate)
def show_session(session_id: int, db: Session = Depends(db_operations.get_db)):
    return controllers.get_session(session_id, db)


@router.get("/auth/", response_model=schemas.User)
def authenticate_user(request: Request, db: Session = Depends(db_operations.get_db)):
    return controllers.authenticate(request, db)


@router_without_auth.post(
    "/dissonance_test_participants/", response_model=schemas.DissonanceTestParticipant
)
def create_dissonance_test_participant(
    participant: schemas.DissonanceTestParticipantCreate,
    db: Session = Depends(db_operations.get_db),
):
    return controllers.create_dissonance_test_participant(
        db=db, participant=participant
    )


@router_without_auth.get(
    "/dissonance_test_participants/{participant_id}",
    response_model=schemas.DissonanceTestParticipantResult,
)
def read_dissonance_test_participant(
    participant_id: int, db: Session = Depends(db_operations.get_db)
):
    return controllers.read_dissonance_test_participant(participant_id, db)


@router.get(
    "/dissonance_test_participants/",
    response_model=list[schemas.DissonanceTestParticipant],
)
def get_dissonance_test_participants(
    request: Request, db: Session = Depends(db_operations.get_db)
):
    return controllers.get_dissonance_test_participants(request, db)


@router_without_auth.post(
    "/dissonance_test_participants/{participant_id}",
    response_model=schemas.DissonanceTestParticipant,
)
def update_dissonance_test_participant(
    participant_id: int,
    participant: schemas.DissonanceTestParticipantUpdateSecond,
    db: Session = Depends(db_operations.get_db),
):
    return controllers.update_dissonance_test_participant(
        participant_id, participant, db
    )


@router_without_auth.post(
    "/dissonance_test_participants/{participant_id}/personality",
    response_model=schemas.DissonanceTestParticipant,
)
def update_dissonance_test_participant_personality_traits(
    participant_id: int,
    answers: str = Form(...),
    db: Session = Depends(db_operations.get_db),
):
    return controllers.update_dissonance_test_participant_personality_traits(
        participant_id, answers, db
    )


@router.post(
    "/dissonance_test_participants/{participant_id}/delete",
    response_model=schemas.DissonanceTestParticipant,
)
def delete_dissonance_test_participant(
    participant_id: int, db: Session = Depends(db_operations.get_db)
):
    return controllers.delete_dissonance_test_participant(participant_id, db)


# High School Room Routes
@router.post("/high-school-rooms/", response_model=schemas.HighSchoolRoom)
def create_high_school_room(
    request: Request,
    high_school_name: str = Form(...),
    high_school_code: str = Form(None),
    db: Session = Depends(db_operations.get_db),
):
    return controllers.create_high_school_room(
        high_school_name, high_school_code, request, db
    )


@router.get("/high-school-rooms/", response_model=list[schemas.HighSchoolRoom])
def get_high_school_rooms(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(db_operations.get_db),
):
    return controllers.get_high_school_rooms(request, skip, limit, db)


@router.get("/high-school-rooms/{room_id}", response_model=schemas.HighSchoolRoom)
def get_high_school_room(room_id: int, db: Session = Depends(db_operations.get_db)):
    return controllers.get_high_school_room(room_id, db)


@router.delete("/high-school-rooms/{room_id}", response_model=schemas.HighSchoolRoom)
def delete_high_school_room(room_id: int, db: Session = Depends(db_operations.get_db)):
    return controllers.delete_high_school_room(room_id, db)


@router.get(
    "/high-school-rooms/{room_id}/students",
    response_model=list[schemas.ProgramSuggestionStudent],
)
def get_high_school_room_students(
    room_id: int, db: Session = Depends(db_operations.get_db)
):
    return controllers.get_high_school_room_students(room_id, db)


# Program Suggestion Student Routes (without auth - anonymous students)
@router_without_auth.post(
    "/program-suggestion/students/", response_model=schemas.ProgramSuggestionStudent
)
def create_program_suggestion_student(
    student: schemas.ProgramSuggestionStudentCreate,
    db: Session = Depends(db_operations.get_db),
):
    return controllers.create_program_suggestion_student(
        student.high_school_room_id, db
    )


@router_without_auth.get(
    "/program-suggestion/students/{student_id}",
    response_model=schemas.ProgramSuggestionStudent,
)
def get_program_suggestion_student(
    student_id: int, db: Session = Depends(db_operations.get_db)
):
    return controllers.get_program_suggestion_student(student_id, db)


@router_without_auth.post(
    "/program-suggestion/students/{student_id}/step1",
    response_model=schemas.ProgramSuggestionStudent,
)
def update_student_step1(
    student_id: int,
    data: schemas.ProgramSuggestionStudentUpdateStep1,
    db: Session = Depends(db_operations.get_db),
):
    return controllers.update_student_step1(student_id, data, db)


@router_without_auth.post(
    "/program-suggestion/students/{student_id}/step2",
    response_model=schemas.ProgramSuggestionStudent,
)
def update_student_step2(
    student_id: int,
    data: schemas.ProgramSuggestionStudentUpdateStep2,
    db: Session = Depends(db_operations.get_db),
):
    return controllers.update_student_step2(student_id, data, db)


@router_without_auth.post(
    "/program-suggestion/students/{student_id}/step3",
    response_model=schemas.ProgramSuggestionStudent,
)
def update_student_step3(
    student_id: int,
    data: schemas.ProgramSuggestionStudentUpdateStep3,
    db: Session = Depends(db_operations.get_db),
):
    return controllers.update_student_step3(student_id, data, db)


@router_without_auth.post(
    "/program-suggestion/students/{student_id}/step4",
    response_model=schemas.ProgramSuggestionStudent,
)
def update_student_step4(
    student_id: int,
    data: schemas.ProgramSuggestionStudentUpdateStep4,
    db: Session = Depends(db_operations.get_db),
):
    return controllers.update_student_step4(student_id, data, db)


@router_without_auth.post(
    "/program-suggestion/students/{student_id}/riasec",
    response_model=schemas.ProgramSuggestionStudent,
)
def update_student_riasec(
    student_id: int,
    data: schemas.ProgramSuggestionStudentUpdateRiasec,
    db: Session = Depends(db_operations.get_db),
):
    return controllers.update_student_riasec(student_id, data, db)


@router_without_auth.get(
    "/program-suggestion/students/{student_id}/result",
    response_model=schemas.ProgramSuggestionStudentResult,
)
def get_student_result(student_id: int, db: Session = Depends(db_operations.get_db)):
    return controllers.get_student_result(student_id, db)


@router.get(
    "/program-suggestion/students/{student_id}/debug",
    response_model=schemas.ProgramSuggestionStudentDebug,
)
def get_student_debug(student_id: int, db: Session = Depends(db_operations.get_db)):
    return controllers.get_student_debug(student_id, db)
