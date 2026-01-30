# controllers.py

import json
from sqlalchemy.orm import Session
from . import models, schemas, security, db_operations
from fastapi import HTTPException, Depends, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from datetime import timedelta
from app.services.update_player_tactic_and_test_code import update_player_tactic_and_test_code
from app.services.prisoners_dilemma import play_game
from app.services.calculate_personality_traits import calculate_personality_traits
from app.services.job_recommendation_service import get_job_recommendation
from app.services.compatibility_analysis_service import get_compatibility_analysis
from app.services.riasec_service import calculate_riasec_scores
from app.services.program_suggestion_service import get_suggested_programs
import os
import bleach
from .helpers import create_player_function_name


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

    return {"access_token": access_token, "current_user_id": user.id, "token_type": "bearer"}

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
    success, player_code, short_tactic = update_player_tactic_and_test_code(cleaned_player_tactic,
                                                                            player.player_function_name)

    # If the service returns true, update the player
    if success:
        player.player_tactic = cleaned_player_tactic
        player.player_code = player_code
        player.short_tactic = short_tactic
        db.commit()
        return player

    # If the service returns false, return an error
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The given tactic is not ok",
        )

def delete_player(player_id: int, db: Session):
    player = db.query(models.Player).get(player_id)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    db.delete(player)
    db.commit()
    return player

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
    background_tasks.add_task(play_game, new_session.id)
    
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
    parsed_answers = json.loads(answers)
    personality_scores = calculate_personality_traits(parsed_answers)
    
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

def create_dissonance_test_participant(db: Session, participant: schemas.DissonanceTestParticipantCreate):
    db_participant = models.DissonanceTestParticipant(**participant.dict())
    db.add(db_participant)
    db.commit()
    db.refresh(db_participant)
    return db_participant

def read_dissonance_test_participant(participant_id: int, db: Session):
    db_participant = db.query(models.DissonanceTestParticipant).filter(models.DissonanceTestParticipant.id == participant_id).first()
    if db_participant is None:
        raise HTTPException(status_code=404, detail="Participant not found")
    return db_participant

def get_dissonance_test_participants(request: Request, db: Session):
    user_id = request.session["current_user"]["id"]
    return db.query(models.DissonanceTestParticipant).filter(models.DissonanceTestParticipant.user_id == user_id).all()

def update_dissonance_test_participant(participant_id: int, participant: schemas.DissonanceTestParticipantUpdateSecond, db: Session):
    db_participant = db.query(models.DissonanceTestParticipant).filter(models.DissonanceTestParticipant.id == participant_id).first()
    if db_participant is None:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    update_data = participant.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_participant, key, value)
    
    db.commit()
    db.refresh(db_participant)
    return db_participant

def delete_dissonance_test_participant(participant_id: int, db: Session):
    db_participant = db.query(models.DissonanceTestParticipant).filter(models.DissonanceTestParticipant.id == participant_id).first()
    if db_participant is None:
        raise HTTPException(status_code=404, detail="Participant not found")
    db.delete(db_participant)
    db.commit()
    return db_participant

def update_dissonance_test_participant_personality_traits(participant_id: int, answers: str, db: Session):
    # Retrieve the player from the database
    db_participant = db.query(models.DissonanceTestParticipant).filter(models.DissonanceTestParticipant.id == participant_id).first()
    
    if db_participant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found",
        )
    
    parsed_answers = json.loads(answers)
    answers_dict = {f"q{i+1}": int(answer) for i, answer in enumerate(parsed_answers)}

    # Calculate personality scores using the previously defined function
    personality_scores = calculate_personality_traits(parsed_answers)
    
    job_recommendation = get_job_recommendation(personality_scores, db_participant.gender, db_participant.age, db_participant.education)
    compatibility_analysis = get_compatibility_analysis(personality_scores, db_participant.star_sign, db_participant.rising_sign)

    # Update the db_participant with the calculated personality traits
    db_participant.extroversion = personality_scores["extroversion"]
    db_participant.agreeableness = personality_scores["agreeableness"]
    db_participant.conscientiousness = personality_scores["conscientiousness"]
    db_participant.negative_emotionality = personality_scores["negative_emotionality"]
    db_participant.open_mindedness = personality_scores["open_mindedness"]
    db_participant.job_recommendation = job_recommendation
    db_participant.compatibility_analysis = compatibility_analysis
    db_participant.personality_test_answers = answers_dict
    
    db.commit()
    db.refresh(db_participant)
    return db_participant


# High School Room Controllers
def create_high_school_room(high_school_name: str, high_school_code: str, request: Request, db: Session):
    user_id = request.session["current_user"]["id"]
    clean_name = bleach.clean(high_school_name, strip=True)
    clean_code = bleach.clean(high_school_code, strip=True) if high_school_code else None
    
    room = models.HighSchoolRoom(
        user_id=user_id,
        high_school_name=clean_name,
        high_school_code=clean_code
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


def get_high_school_rooms(request: Request, skip: int, limit: int, db: Session):
    user_id = request.session["current_user"]["id"]
    return db.query(models.HighSchoolRoom).filter(
        models.HighSchoolRoom.user_id == user_id
    ).offset(skip).limit(limit).all()


def get_high_school_room(room_id: int, db: Session):
    room = db.query(models.HighSchoolRoom).filter(
        models.HighSchoolRoom.id == room_id
    ).first()
    if room is None:
        raise HTTPException(status_code=404, detail="High school room not found")
    return room


def delete_high_school_room(room_id: int, db: Session):
    room = db.query(models.HighSchoolRoom).filter(
        models.HighSchoolRoom.id == room_id
    ).first()
    if room is None:
        raise HTTPException(status_code=404, detail="High school room not found")
    db.delete(room)
    db.commit()
    return room


def get_high_school_room_students(room_id: int, db: Session):
    # Get all students
    all_students = db.query(models.ProgramSuggestionStudent).filter(
        models.ProgramSuggestionStudent.high_school_room_id == room_id
    ).all()
    
    # Filter out orphaned 'started' records that have a sibling with same created_at
    # This handles the duplicate issue caused by React StrictMode
    from datetime import timedelta
    
    # Group by created_at timestamp (within 2 second window)
    completed_times = set()
    for student in all_students:
        if student.status != 'started' and student.created_at:
            # Add a time window around completed records
            completed_times.add(student.created_at)
    
    filtered_students = []
    for student in all_students:
        # Keep all non-started records
        if student.status != 'started':
            filtered_students.append(student)
        else:
            # For 'started' records, check if there's a completed sibling within 5 seconds
            is_orphan_duplicate = False
            if student.created_at:
                for completed_time in completed_times:
                    time_diff = abs((student.created_at - completed_time).total_seconds())
                    if time_diff <= 5:  # Within 5 seconds
                        is_orphan_duplicate = True
                        break
            
            if not is_orphan_duplicate:
                filtered_students.append(student)
    
    return filtered_students


# Program Suggestion Student Controllers
def create_program_suggestion_student(high_school_room_id: int, db: Session):
    # Verify room exists
    room = db.query(models.HighSchoolRoom).filter(
        models.HighSchoolRoom.id == high_school_room_id
    ).first()
    if room is None:
        raise HTTPException(status_code=404, detail="High school room not found")
    
    # Check for duplicate records created within last 5 seconds with status 'started'
    # This handles race conditions from React StrictMode or double-clicks
    from datetime import datetime, timedelta, timezone
    five_seconds_ago = datetime.now(timezone.utc) - timedelta(seconds=5)
    
    recent_started = db.query(models.ProgramSuggestionStudent).filter(
        models.ProgramSuggestionStudent.high_school_room_id == high_school_room_id,
        models.ProgramSuggestionStudent.status == 'started',
        models.ProgramSuggestionStudent.created_at >= five_seconds_ago
    ).order_by(models.ProgramSuggestionStudent.created_at.desc()).all()
    
    # If there's a recent 'started' record, return it instead of creating new
    if recent_started:
        return recent_started[0]
    
    student = models.ProgramSuggestionStudent(
        high_school_room_id=high_school_room_id,
        status='started'
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def get_program_suggestion_student(student_id: int, db: Session):
    student = db.query(models.ProgramSuggestionStudent).filter(
        models.ProgramSuggestionStudent.id == student_id
    ).first()
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


def update_student_step1(student_id: int, data: schemas.ProgramSuggestionStudentUpdateStep1, db: Session):
    student = db.query(models.ProgramSuggestionStudent).filter(
        models.ProgramSuggestionStudent.id == student_id
    ).first()
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student.name = data.name
    student.birth_year = data.birth_year
    student.gender = data.gender
    student.status = 'step1_completed'
    
    db.commit()
    db.refresh(student)
    return student


def update_student_step2(student_id: int, data: schemas.ProgramSuggestionStudentUpdateStep2, db: Session):
    student = db.query(models.ProgramSuggestionStudent).filter(
        models.ProgramSuggestionStudent.id == student_id
    ).first()
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student.class_year = data.class_year
    student.will_take_exam = data.will_take_exam
    student.average_grade = data.average_grade
    student.area = data.area
    student.wants_foreign_language = data.wants_foreign_language
    student.status = 'step2_completed'
    
    db.commit()
    db.refresh(student)
    return student


def update_student_step3(student_id: int, data: schemas.ProgramSuggestionStudentUpdateStep3, db: Session):
    student = db.query(models.ProgramSuggestionStudent).filter(
        models.ProgramSuggestionStudent.id == student_id
    ).first()
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student.expected_score_min = data.expected_score_min
    student.expected_score_max = data.expected_score_max
    student.expected_score_distribution = data.expected_score_distribution
    student.alternative_area = data.alternative_area
    student.alternative_score_min = data.alternative_score_min
    student.alternative_score_max = data.alternative_score_max
    student.alternative_score_distribution = data.alternative_score_distribution
    student.status = 'step3_completed'
    
    db.commit()
    db.refresh(student)
    return student


def update_student_step4(student_id: int, data: schemas.ProgramSuggestionStudentUpdateStep4, db: Session):
    student = db.query(models.ProgramSuggestionStudent).filter(
        models.ProgramSuggestionStudent.id == student_id
    ).first()
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student.preferred_language = data.preferred_language
    student.desired_universities = data.desired_universities
    student.desired_cities = data.desired_cities
    student.status = 'step4_completed'
    
    db.commit()
    db.refresh(student)
    return student


def update_student_riasec(student_id: int, data: schemas.ProgramSuggestionStudentUpdateRiasec, db: Session):
    student = db.query(models.ProgramSuggestionStudent).filter(
        models.ProgramSuggestionStudent.id == student_id
    ).first()
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Calculate RIASEC scores
    riasec_scores = calculate_riasec_scores(data.riasec_answers)
    
    # Calculate expected score (middle point based on distribution)
    expected_score = calculate_expected_score(
        student.expected_score_min,
        student.expected_score_max,
        student.expected_score_distribution
    )
    
    alternative_score = None
    if student.alternative_area:
        alternative_score = calculate_expected_score(
            student.alternative_score_min,
            student.alternative_score_max,
            student.alternative_score_distribution
        )
    
    # Get program suggestions
    result = get_suggested_programs(
        riasec_scores=riasec_scores,
        expected_score=expected_score,
        area=student.area,
        alternative_score=alternative_score,
        alternative_area=student.alternative_area,
        preferred_language=student.preferred_language,
        desired_universities=student.desired_universities,
        desired_cities=student.desired_cities
    )
    
    # Update student record
    student.riasec_answers = data.riasec_answers
    student.riasec_scores = result['riasec_scores']
    student.suggested_jobs = result['suggested_jobs']
    student.suggested_programs = result['suggested_programs']
    student.gpt_prompt = result.get('gpt_prompt')
    student.gpt_response = result.get('gpt_response')
    student.status = 'completed'
    
    db.commit()
    db.refresh(student)
    return student


def calculate_expected_score(min_score: float, max_score: float, distribution: str) -> float:
    """Calculate expected score based on distribution preference."""
    if not min_score or not max_score:
        return 0
    
    range_val = max_score - min_score
    
    if distribution == 'low':
        return min_score + (range_val * 0.25)
    elif distribution == 'high':
        return min_score + (range_val * 0.75)
    else:  # medium or default
        return min_score + (range_val * 0.5)


def get_student_result(student_id: int, db: Session):
    student = db.query(models.ProgramSuggestionStudent).filter(
        models.ProgramSuggestionStudent.id == student_id
    ).first()
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    return {
        'id': student.id,
        'name': student.name,
        'expected_score_min': student.expected_score_min,
        'expected_score_max': student.expected_score_max,
        'alternative_area': student.alternative_area,
        'alternative_score_min': student.alternative_score_min,
        'alternative_score_max': student.alternative_score_max,
        'riasec_scores': student.riasec_scores,
        'suggested_jobs': student.suggested_jobs,
        'suggested_programs': student.suggested_programs,
        'area': student.area
    }


def get_student_debug(student_id: int, db: Session):
    student = db.query(models.ProgramSuggestionStudent).filter(
        models.ProgramSuggestionStudent.id == student_id
    ).first()
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    
    return {
        'id': student.id,
        'name': student.name,
        'riasec_scores': student.riasec_scores,
        'suggested_jobs': student.suggested_jobs,
        'gpt_prompt': student.gpt_prompt,
        'gpt_response': student.gpt_response
    }