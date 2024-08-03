from itertools import combinations
import random
from app import models
from sqlalchemy.exc import SQLAlchemyError
from math import factorial
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from datetime import datetime
from ..database import SessionLocal

GAMES_PLAYED_WITH_EACH_OTHER = 100
MAXIMUM_NUMBER_OF_ROUNDS = 1000
MAX_WORKERS = 4
global_game_session = None
global_game_session_id = None
global_players = []

def compute_payoffs(player1_choice, player2_choice):
    # Define the payoff matrix
    T, R, P, S = 5, 3, 1, 0  # Temptation, Reward, Punishment, Sucker's payoff

    if player1_choice == "cooperate" and player2_choice == "cooperate":
        return R, R
    elif player1_choice == "cooperate" and player2_choice == "defect":
        return S, T
    elif player1_choice == "defect" and player2_choice == "cooperate":
        return T, S
    else:  # Both defect
        return P, P

def prepare_player_functions(players):
    # Create a new dictionary for the functions
    functions = {}
    
    # For each player
    for player in players:
        # Create the function for the player
        exec(player.player_code, functions)

    return functions

def get_player_choice(player_function_name, game_history, functions):
    player_function = functions[player_function_name]
    
    # Call the player's function to get the choice
    player_choice = player_function(game_history)

    return player_choice

def play_multiple_games_wrapper(args):
    player1, player2, functions, game_session_id = args
    
    wrapperDb = SessionLocal()
    try:
        play_multiple_games(player1, player2, wrapperDb, functions, game_session_id)
    finally:
        wrapperDb.close()

def play_game(game_session_id):
    global global_game_session, global_players    

    start_time = datetime.now()
    checkpoint_start_time = start_time  # Initialize checkpoint start time
    checkpoint_durations = []

    # Prepare the player functions
    mainDb = SessionLocal()
    try:
        global_game_session = mainDb.query(models.Session).filter(models.Session.id == game_session_id).first()
        player_ids = global_game_session.player_ids.split(",")
        global_players = [mainDb.query(models.Player).filter(models.Player.id == player_id).first() for player_id in player_ids]
    except SQLAlchemyError as e:
        logging.info(f"An error occurred: {e}")
    finally:
        mainDb.close()

    functions = prepare_player_functions(global_players)

    # Generate all possible pairs of global_players
    player_pairs = list(combinations(global_players, 2))
    total_players = len(global_players)
    total_games = (factorial(total_players) / (factorial(2) * factorial(total_players - 2))) * GAMES_PLAYED_WITH_EACH_OTHER
    completed_games = 0
    
    tasks = [(player1, player2, functions, game_session_id) for player1, player2 in player_pairs]
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_pair = {executor.submit(play_multiple_games_wrapper, task): task for task in tasks}
        
        for _ in as_completed(future_to_pair):
            completed_games += GAMES_PLAYED_WITH_EACH_OTHER
            completion_percentage = round((completed_games / total_games) * 100)
            now = datetime.now()
            checkpoint_duration = (now - checkpoint_start_time).total_seconds()
            checkpoint_durations.append(checkpoint_duration)
            checkpoint_start_time = now

            percentageDb = SessionLocal()
            try:
                current_session = percentageDb.query(models.Session).filter(models.Session.id == game_session_id).first()
                current_session.status = f"{completion_percentage}"
                percentageDb.commit()
            except SQLAlchemyError as exc:
                logging.info(f"An error occurred: {exc}")
                percentageDb.rollback()
            finally:
                percentageDb.close()
            
            logging.info(f"{completion_percentage}% completed in {checkpoint_duration} seconds")
            
    post_completion_start_time = datetime.now()  # Start time after 100% completion
    
    # After all games are finished, calculate the leaderboard and scores matrix
    leaderboard, scores_matrix = calculate_leaderboard_and_scores_matrix(global_players, game_session_id)

    # Convert the leaderboard to a JSON-compatible format
    # Assuming leaderboard is a list of tuples or a similar structure that needs conversion
    leaderboard_jsonb = {"leaderboard": leaderboard, "matrix": scores_matrix}

    lastDb = SessionLocal()
    try:
        current_session = lastDb.query(models.Session).filter(models.Session.id == game_session_id).first()
        current_session.results = leaderboard_jsonb
        current_session.status = "finished"
        lastDb.query(models.Game).filter(models.Game.session_id == game_session_id).delete()
        lastDb.commit()
    except SQLAlchemyError as e:
        logging.info(f"An error occurred: {e}")
        lastDb.rollback()
    finally:
        lastDb.close()

    remaining_time_to_exit = (datetime.now() - post_completion_start_time).total_seconds()
    
    logging.info(f"Game session {global_game_session.name} with id:{game_session_id} completed in {remaining_time_to_exit} seconds. Checkpoint durations: {checkpoint_durations}")

def play_multiple_games(player1, player2, wrapperDb, functions, game_session_id):
    for _ in range(GAMES_PLAYED_WITH_EACH_OTHER):
        try:
            game = models.Game(home_player_id=player1.id, away_player_id=player2.id,
                               home_player_score=0, away_player_score=0, session_id=game_session_id)
            wrapperDb.add(game)

            game_history_player1 = []
            game_history_player2 = []

            for _ in range(1, MAXIMUM_NUMBER_OF_ROUNDS):
                player1_choice = get_player_choice(player1.player_function_name, game_history_player1, functions)
                player2_choice = get_player_choice(player2.player_function_name, game_history_player2, functions)

                game_history_player1.append([player1_choice, player2_choice])
                game_history_player2.append([player2_choice, player1_choice])

                player1_score, player2_score = compute_payoffs(player1_choice, player2_choice)
                game.home_player_score += player1_score
                game.away_player_score += player2_score

                if random.random() <= 0.005:
                    break
            wrapperDb.commit()
        except SQLAlchemyError as e:
            logging.info(f"An error occurred: {e}")
            wrapperDb.rollback()

def calculate_scores_matrix(players, all_games):
    logging.info("Starting to calculate scores matrix.")
    
    # Create a dictionary to map player IDs to player names for quick lookup
    player_id_to_name = {player.id: player.player_name for player in players}
    logging.info("Mapped player IDs to player names.")
    
    # Initialize the scores matrix with player names
    scores_matrix = {player.player_name: {opponent.player_name: 0 for opponent in players if opponent.id != player.id} for player in players}
    logging.info("Initialized scores matrix with player names.")
    
    # Process each game to update the scores matrix
    for game in all_games:
        home_player_name = player_id_to_name[game.home_player_id]
        away_player_name = player_id_to_name[game.away_player_id]
        
        # Update the scores matrix for the home player
        scores_matrix[home_player_name][away_player_name] += game.home_player_score
        # Update the scores matrix for the away player
        scores_matrix[away_player_name][home_player_name] += game.away_player_score
    
    logging.info("Completed updating scores matrix.")
    return scores_matrix

def calculate_leaderboard_and_scores_matrix(players, game_session_id):
    logging.info("Starting to calculate leaderboard and scores matrix.")
    db = SessionLocal()
    try:
        all_games = db.query(models.Game).filter(models.Game.session_id == game_session_id).all()
        logging.info(f"Retrieved all games for session ID: {game_session_id}")
    except SQLAlchemyError as e:
        logging.error(f"An error occurred while querying the database: {e}")
    finally:
        db.close()
        logging.info("Database session closed.")

    scores_matrix = calculate_scores_matrix(players, all_games)

    leaderboard = {}
    # Process games in Python to calculate total scores
    player_scores = {player.id: 0 for player in players}  # Initialize scores for all players
    for game in all_games:
        player_scores[game.home_player_id] += game.home_player_score
        player_scores[game.away_player_id] += game.away_player_score
    logging.info("Calculated total scores for all players.")
    
    # Map player IDs back to player names and scores
    for player in players:
        leaderboard[player.player_name] = player_scores[player.id]

    # Sort the leaderboard by score in descending order
    leaderboard = dict(sorted(leaderboard.items(), key=lambda item: item[1], reverse=True))
    logging.info("Sorted the leaderboard by score in descending order.")

    return leaderboard, scores_matrix