from itertools import combinations
from multiprocessing import Pool
import random
from app import models
from sqlalchemy.orm import Session

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

def get_player_choice(player_name, game_history, functions):
    player_function = functions[player_name]
    
    # Call the player's function to get the choice
    player_choice = player_function(game_history)

    return player_choice

def play_game(players, db: Session):
    # Prepare the player functions
    functions = prepare_player_functions(players)

    # Generate all possible pairs of players
    player_pairs = list(combinations(players, 2))
    
    for player1, player2 in player_pairs:
        play_multiple_games(player1, player2, db, functions)

def play_multiple_games(player1, player2, db, functions):
    # Play the game 100 times
    for _ in range(10):
        # Create a new game
        game = models.Game(home_player_id=player1.id, away_player_id=player2.id)
        db.add(game)
        db.commit()

        # Initialize the game histories
        game_history_player1 = []
        game_history_player2 = []

        # For each round in the game
        for round_number in range(1, 51):
            # Get the players' choices
            player1_choice = get_player_choice(player1.player_name, game_history_player1, functions)
            player2_choice = get_player_choice(player2.player_name, game_history_player2, functions)

            # Add the choices to the game histories
            game_history_player1.append([player1_choice, player2_choice])
            game_history_player2.append([player2_choice, player1_choice])

            # Compute the payoffs
            player1_score, player2_score = compute_payoffs(player1_choice, player2_choice)

            # Update the players' scores
            game.home_player_score += player1_score
            game.away_player_score += player2_score

            # Create a new round
            round = models.Round(round_number=round_number, home_choice=player1_choice, away_choice=player2_choice, game_id=game.id)
            db.add(round)
            db.commit()

            # Decide whether the game ends on this round with the probability of p = 0.005
            if random.random() <= 0.005:
                break
       
        db.commit()

def calculate_leaderboard(players, db: Session):
    # Initialize the leaderboard
    leaderboard = {}

    # For each player
    for player in players:
        # Get all games where the player was the home player
        home_games = db.query(models.Game).filter(models.Game.home_player_id == player.id).all()

        # Get all games where the player was the away player
        away_games = db.query(models.Game).filter(models.Game.away_player_id == player.id).all()

        # Calculate the total score for the player
        total_score = sum(game.home_player_score for game in home_games) + sum(game.away_player_score for game in away_games)

        # Add the player and their total score to the leaderboard
        leaderboard[player.player_name] = total_score

    # Sort the leaderboard by score in descending order
    leaderboard = dict(sorted(leaderboard.items(), key=lambda item: item[1], reverse=True))

    return leaderboard