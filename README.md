# EducAItion

This project simulates a game where players can adopt different strategies. The strategies are:

1. **Mirror**: Start by cooperating, then mirror the opponent's previous move.
2. **Coop**: Start by cooperating and continue to do so as long as the opponent does the same. If the opponent defects, retaliate by defecting in the next round and continue to mimic their moves thereafter.
3. **Echoing**: Start with cooperation and then observe the opponent's behavior. If they consistently cooperate, maintain cooperation. However, if they defect, switch to defecting in the next round and mirror their moves from then on.
4. **Shadow**: Start by cooperating. If the opponent defects or cooperates 2 times in a row, change the tactic to be the same as the opponent.
5. **Adaptive**: Start with defecting, then always do the opposite of what the opponent does.
6. **Cooperative**: Always cooperate.
7. **Defective**: Always defect.

## Game Results

The results of the game simulations are as follows:

### Without Cooperative and Defective Strategies

| Strategy | Score |
| -------- | ----- |
| Shadow   | 9169  |
| Coop     | 7511  |
| Mirror   | 7440  |
| Echoing  | 7440  |
| Adaptive | 4689  |

### Without Defective Strategy

| Strategy    | Score |
| ----------- | ----- |
| Shadow      | 16010 |
| Coop        | 13916 |
| Echoing     | 13894 |
| Mirror      | 13569 |
| Adaptive    | 10084 |
| Cooperative | 4935  |

### With All Strategies

| Strategy    | Score |
| ----------- | ----- |
| Shadow      | 23892 |
| Echoing     | 20591 |
| Coop        | 20277 |
| Mirror      | 19959 |
| Adaptive    | 15475 |
| Cooperative | 9753  |
| Defective   | 6448  |

### With All Strategies Repeated

| Strategy    | Score |
| ----------- | ----- |
| Shadow      | 31932 |
| Echoing     | 27433 |
| Coop        | 27174 |
| Mirror      | 26691 |
| Adaptive    | 20923 |
| Cooperative | 15030 |
| Defective   | 12652 |

## Setup and Installation

To set up and run the project, follow these steps:

1. Create a virtual environment:
```
python3.10 -m venv env
```
2. Activate the virtual environment:
- On macOS/Linux:
  ```
  source env/bin/activate
  ```
- On Windows:
  ```
  .\env\Scripts\activate
  ```
3. Install the required dependencies (ensure you have a `requirements.txt` file):
```
pip install -r requirements.txt
```
4. Start the application with `uvicorn`:
```
uvicorn app.main:app --reload
```
