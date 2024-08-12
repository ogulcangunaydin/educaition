import requests
import os
import logging
import random

def update_player_tactic_and_test_code(player_tactic: str, player_name: str):
    def process_gpt_response(content):
        # Remove triple backticks and leading/trailing whitespace
        cleaned_content = content.replace("```python", "").replace("```", "").strip()
        return cleaned_content

    def send_request_to_gpt(prompt):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
        }
        data = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.5,
            "max_tokens": 500
        }
        response = requests.post(os.getenv('OPENAI_ENDPOINT'), headers=headers, json=data)
        if response.status_code == 200:
            raw_response = response.json()['choices'][0]['message']['content']
            return process_gpt_response(raw_response)
        else:
            logging.error(f"Failed to get response from GPT. Status code: {response.status_code}, Response: {response.text}")
            return None
    
    def summarize_tactic(tactic: str) -> str:
        """
        Summarize the player's tactic into a one-sentence summary using GPT.
        """
        prompt = f"Summarize the following tactic with few words: '{tactic}'"
        summary = send_request_to_gpt(prompt)
        return summary
    
    prompt = (
        f"Generate a directly executable Python function named '{player_name}' for the Prisoner's Dilemma game. The tactic is: "
        f"'{player_tactic}'. The function should accept an array of arrays as input, where each sub-array represents a game round. "
        "The first element of the sub-array is the player's move, and the second is the opponent's move. "
        "The function should return the player's next move with either 'defect' or 'cooperate'. "
        "Ensure the code is syntactically correct, complete, and does not require any modifications to run."
        "Please provide the function without any comments or additional explanations."
    )

    generated_code = send_request_to_gpt(prompt)

    if not generated_code:
        return False, None

    # Execute the generated Python function and get a reference to it
    try:
        exec(generated_code)
        player_function = locals()[player_name]
    except Exception as initial_error:
        logging.error(f"Initial code: {generated_code}")
        logging.error(f"Initial code execution error: {initial_error}")

        # Prompt to fix the code
        fix_prompt = (
            f"The following Python function generated an error: '{initial_error}'.\n\n"
            f"Original code:\n{generated_code}\n\n"
            "Please fix the code."
        )

        fixed_code = send_request_to_gpt(fix_prompt)

        if not fixed_code:
            return False, "Failed to fix the code."

        try:
            exec(fixed_code)
            player_function = locals()[player_name]
        except Exception as fixed_error:
            logging.error(f"Fixed code execution error: {fixed_error}")
            return False, "Failed to execute fixed code."

    def generate_random_test_cases(test_cases, num_cases=3):
        for _ in range(num_cases):
            num_rounds = random.randint(10, 100)
            rounds = [[random.choice(["cooperate", "defect"]), random.choice(["cooperate", "defect"])] for _ in range(num_rounds)]
            test_cases.append(rounds)
        return test_cases
    
    # Define the test input
    test_cases = [
        [],
        [["cooperate", "defect"]],
        [["cooperate", "cooperate"]],
        [["defect", "defect"]],
        [["cooperate", "defect"], ["defect", "cooperate"]],
        [["defect", "defect"], ["defect", "defect"]],
        [["cooperate", "cooperate"], ["cooperate", "cooperate"]],
        [["defect", "cooperate"], ["cooperate", "defect"], ["defect", "cooperate"]]
    ]
    
    test_cases = generate_random_test_cases(test_cases)
    
    try:
        for moves in test_cases:
            output = player_function(moves)
            # Check if the output is either "defect" or "cooperate"
            if output not in ["defect", "cooperate"]:
                raise ValueError("Output validation failed")
            
        short_tactic = summarize_tactic(player_tactic)

        # Remove backslashes and double quotes
        if short_tactic:
            short_tactic = short_tactic.replace("\\", "").replace("\"", "")
        

        return True, generated_code, short_tactic
    except Exception as e:
        logging.error(f"Error during function execution or output validation: {e}")

        # Prompt to fix the code
        fix_prompt = (
          f"The following Python function generated an error or failed output validation: '{e}'.\n\n"
          f"Original code:\n{generated_code}\n\n"
          "Please fix the code."
        )

        fixed_further_code = send_request_to_gpt(fix_prompt)

        if not fixed_further_code:
          return False, None

        try:
            exec(fixed_further_code)
            fixed_player_function = locals()[player_name]

            for moves in test_cases:
                output = fixed_player_function(moves)
                if output not in ["defect", "cooperate"]:
                    raise ValueError("Output validation failed")
        
            return True, generated_code
        except Exception as fixed_error:
          logging.error(f"Error executing fixed code: {fixed_error}")
          return False, None
