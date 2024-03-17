import requests
import os
import logging

def update_player_tactic_and_test_code(player_tactic: str, player_name: str):
    # Define the prompt
    prompt = (
        f"Write the code of a Python function named {player_name} for the Prisoner's Dilemma game where the player's tactic is: "
        f"{player_tactic}. The function should take an array of arrays as the input, where each sub-array represents a round of the game and "
        "the first element of the sub-array is the player's move and the second element is the opponent's move. "
        "The function should return the player's next move with either 'defect' or 'cooperate'. Without any explanation or comments just give me the function."
    )

    # Define the headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
    }

    # Define the data
    data = {
        "prompt": prompt,
        "max_tokens": 200
    }

    # Send a request to the API with the headers and data
    response = requests.post(os.getenv('OPENAI_ENDPOINT'), headers=headers, json=data)

    # Get the generated text from the API response
    generated_text = response.json()['choices'][0]['text']
    
    logging.info(f"Generated text: {generated_text}")
      
    # Define the test input
    moves = [["cooperate", "defect"], ["defect", "cooperate"]]
    moves_first_round = []

    # Execute the generated Python function and get a reference to it
    try:
        exec(generated_text)
        player_function = locals()[player_name]
    except Exception as e:
        logging.error(f"Error executing generated code or getting function reference: {e}")
        return False, None

    # Call the generated Python function with the test input
    try:
        output = player_function(moves)
        output_first_round = player_function(moves_first_round)
    except Exception as e:
        logging.error(f"Error calling function: {e}")
        return False, None

    # Check if the output is either "defect" or "cooperate"
    test_result = output in ["defect", "cooperate"] and output_first_round in ["defect", "cooperate"]

    # If the test succeeds, return true and the generated code
    if test_result:
        return True, generated_text

    # If the test fails, return false and None
    else:
        return False, None