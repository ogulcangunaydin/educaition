import json

def calculate_personality_traits(answers):
  # Convert answers to integers
  parsed_answers = json.loads(answers)
  answers = [int(answer) for answer in parsed_answers]
  
  # Calculate personality traits
  extroversion = ((answers[0] + answers[5] + answers[20] + answers[40] + answers[45] + answers[55] +
           (6 - answers[10]) + (6 - answers[15]) + (6 - answers[25]) + (6 - answers[30]) +
           (6 - answers[35]) + (6 - answers[50])) * 25 / 12) - 25

  agreeableness = ((answers[1] + answers[6] + answers[26] + answers[31] + answers[51] + answers[56] +
            (6 - answers[11]) + (6 - answers[16]) + (6 - answers[21]) + (6 - answers[36]) +
            (6 - answers[41]) + (6 - answers[46])) * 25 / 12) - 25

  conscientiousness = ((answers[12] + answers[17] + answers[32] + answers[37] + answers[42] + answers[52] +
              (6 - answers[2]) + (6 - answers[7]) + (6 - answers[22]) + (6 - answers[27]) +
              (6 - answers[47]) + (6 - answers[57])) * 25 / 12) - 25

  negative_emotionality = ((answers[13] + answers[18] + answers[33] + answers[38] + answers[53] +
                answers[58] + (6 - answers[3]) + (6 - answers[8]) + (6 - answers[23]) +
                (6 - answers[28]) + (6 - answers[43]) + (6 - answers[48])) * 25 / 13) - 25

  open_mindedness = ((answers[9] + answers[14] + answers[19] + answers[34] + answers[39] + answers[59] +
            (6 - answers[4]) + (6 - answers[24]) + (6 - answers[29]) + (6 - answers[44]) +
            (6 - answers[49]) + (6 - answers[54])) * 25 / 12) - 25

  return {
    "extroversion": extroversion,
    "agreeableness": agreeableness,
    "conscientiousness": conscientiousness,
    "negative_emotionality": negative_emotionality,
    "open_mindedness": open_mindedness
  }