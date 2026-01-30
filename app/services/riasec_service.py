import csv
import math
import os
import requests
import logging
from typing import Dict, List, Tuple, Optional

# RIASEC Score mapping
SCORE_MAP = {
    'strongly_like': 2,
    'like': 1,
    'unsure': 0,
    'dislike': -1,
    'strongly_dislike': -2
}

# RIASEC question types mapping
RIASEC_TYPES = {
    'R': 'realistic',
    'I': 'investigative',
    'A': 'artistic',
    'S': 'social',
    'E': 'enterprising',
    'C': 'conventional'
}


def calculate_riasec_scores(answers: Dict[str, int]) -> Dict[str, float]:
    """
    Calculate RIASEC scores from student answers.
    Answers format: {question_id: score_value}
    Score values: 2 (strongly_like), 1 (like), 0 (unsure), -1 (dislike), -2 (strongly_dislike)
    
    Returns normalized scores in ONET style (0-7 scale)
    """
    # Initialize raw scores
    raw_scores = {'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0}
    counts = {'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0}
    
    # Question ID to type mapping (based on riasecQuestions.json structure)
    question_type_map = get_question_type_map()
    
    for question_id, score in answers.items():
        q_type = question_type_map.get(str(question_id))
        if q_type:
            raw_scores[q_type] += score
            counts[q_type] += 1
    
    # Normalize scores to ONET 0-7 scale
    # Original range is -20 to 20 (10 questions * -2 to 2)
    # Convert to 0-7 scale
    normalized_scores = {}
    for letter in raw_scores:
        if counts[letter] > 0:
            # Raw score range: -2*count to 2*count
            # Normalize to 0-7 scale
            max_raw = 2 * counts[letter]
            min_raw = -2 * counts[letter]
            # Shift to 0 to 4*count, then scale to 0-7
            shifted = raw_scores[letter] - min_raw
            normalized_scores[letter] = round((shifted / (max_raw - min_raw)) * 7, 2)
        else:
            normalized_scores[letter] = 0
    
    return normalized_scores


def get_question_type_map() -> Dict[str, str]:
    """
    Returns mapping of question IDs to their RIASEC type.
    """
    return {
        # Realistic
        '1': 'R', '14': 'R', '26': 'R', '49': 'R', '61': 'R',
        '62': 'R', '146': 'R', '158': 'R', '169': 'R', '170': 'R',
        # Investigative
        '27': 'I', '39': 'I', '75': 'I', '100': 'I', '111': 'I',
        '112': 'I', '135': 'I', '136': 'I', '147': 'I', '171': 'I',
        # Artistic
        '29': 'A', '30': 'A', '54': 'A', '77': 'A', '90': 'A',
        '113': 'A', '137': 'A', '149': 'A', '161': 'A', '173': 'A',
        # Social
        '7': 'S', '20': 'S', '44': 'S', '67': 'S', '68': 'S',
        '80': 'S', '92': 'S', '104': 'S', '151': 'S', '176': 'S',
        # Enterprising
        '9': 'E', '10': 'E', '22': 'E', '93': 'E', '117': 'E',
        '118': 'E', '129': 'E', '142': 'E', '154': 'E', '166': 'E',
        # Conventional
        '11': 'C', '12': 'C', '36': 'C', '60': 'C', '96': 'C',
        '107': 'C', '120': 'C', '155': 'C', '167': 'C', '179': 'C'
    }


def load_job_riasec_scores(csv_path: str = None) -> Dict[str, Dict[str, float]]:
    """
    Load job RIASEC scores from CSV file.
    Returns: {job_title: {R: score, I: score, ...}}
    """
    if csv_path is None:
        # Default path - use data folder in backend
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 
                                'riasec_score_to_job.csv')
    
    jobs = {}
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                title = row['Title']
                element = row['Element Name']
                value = float(row['Data Value'])
                
                if title not in jobs:
                    jobs[title] = {}
                
                # Map element name to letter
                element_map = {
                    'Realistic': 'R',
                    'Investigative': 'I',
                    'Artistic': 'A',
                    'Social': 'S',
                    'Enterprising': 'E',
                    'Conventional': 'C'
                }
                letter = element_map.get(element)
                if letter:
                    jobs[title][letter] = value
    except Exception as e:
        logging.error(f"Error loading job RIASEC scores: {e}")
        jobs = {}
    
    return jobs


def get_holland_code(scores: Dict[str, float], top_n: int = 3) -> str:
    """
    Get the Holland code (top N dominant RIASEC letters) from scores.
    Returns string like 'SIA' for Social-Investigative-Artistic dominant profile.
    """
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return ''.join([letter for letter, _ in sorted_scores[:top_n]])


def calculate_cosine_similarity(student_scores: Dict[str, float], 
                                 job_scores: Dict[str, float]) -> float:
    """
    Calculate cosine similarity between student and job RIASEC profiles.
    This measures profile SHAPE similarity regardless of magnitude.
    Returns value between -1 and 1 (higher is better match).
    """
    letters = ['R', 'I', 'A', 'S', 'E', 'C']
    
    # Calculate dot product
    dot_product = sum(student_scores.get(l, 0) * job_scores.get(l, 0) for l in letters)
    
    # Calculate magnitudes
    student_magnitude = math.sqrt(sum(student_scores.get(l, 0) ** 2 for l in letters))
    job_magnitude = math.sqrt(sum(job_scores.get(l, 0) ** 2 for l in letters))
    
    # Avoid division by zero
    if student_magnitude == 0 or job_magnitude == 0:
        return 0
    
    return dot_product / (student_magnitude * job_magnitude)


def calculate_holland_code_match(student_scores: Dict[str, float], 
                                  job_scores: Dict[str, float]) -> float:
    """
    Calculate how well the dominant RIASEC types match.
    Compares top 3 letters (Holland code) with weighted scoring.
    Returns value between 0 and 1 (higher is better).
    """
    student_code = get_holland_code(student_scores, 3)
    job_code = get_holland_code(job_scores, 3)
    
    score = 0
    weights = [3, 2, 1]  # Primary type most important, then secondary, then tertiary
    
    for i, student_letter in enumerate(student_code):
        if student_letter in job_code:
            # Bonus if same position
            job_position = job_code.index(student_letter)
            if job_position == i:
                score += weights[i] * 1.5  # Same position bonus
            else:
                score += weights[i] * (1 - 0.2 * abs(job_position - i))  # Partial credit
    
    # Normalize to 0-1 range (max possible score = 3*1.5 + 2*1.5 + 1*1.5 = 9)
    return score / 9


def calculate_profile_differentiation(scores: Dict[str, float]) -> float:
    """
    Calculate how differentiated/peaked a profile is (vs flat).
    A flat profile (all similar scores) has low differentiation.
    A peaked profile (clear dominant types) has high differentiation.
    
    Returns value between 0 and 1.
    """
    values = list(scores.values())
    if not values:
        return 0
    
    mean = sum(values) / len(values)
    # Standard deviation as measure of spread
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std_dev = math.sqrt(variance)
    
    # Normalize: max possible std dev for scores 0-7 is about 3.5
    # (when half are 0 and half are 7)
    normalized_diff = min(std_dev / 2.5, 1.0)
    
    return normalized_diff


def calculate_profile_match_score(student_scores: Dict[str, float], 
                                   job_scores: Dict[str, float]) -> float:
    """
    Combined matching score using multiple metrics:
    - Cosine similarity (profile shape)
    - Holland code match (dominant types)
    - Profile differentiation penalty (flat profiles are less reliable)
    
    Returns a score between 0 and 1 (higher is better).
    """
    cosine_sim = calculate_cosine_similarity(student_scores, job_scores)
    holland_match = calculate_holland_code_match(student_scores, job_scores)
    
    # Convert cosine similarity from [-1,1] to [0,1]
    normalized_cosine = (cosine_sim + 1) / 2
    
    # Calculate how differentiated the student's profile is
    # Flat profiles (all similar scores) should have reduced confidence
    student_diff = calculate_profile_differentiation(student_scores)
    
    # Base score: 40% cosine similarity, 60% Holland code match
    base_score = 0.4 * normalized_cosine + 0.6 * holland_match
    
    # Apply differentiation factor: flat profiles get scaled down
    # At minimum differentiation (0), we scale to 60% of the score
    # At maximum differentiation (1), we keep full score
    diff_factor = 0.6 + (0.4 * student_diff)
    
    combined_score = base_score * diff_factor
    
    return combined_score


def find_top_matching_jobs(student_scores: Dict[str, float], 
                           top_n: int = 3,
                           csv_path: str = None) -> List[Dict]:
    """
    Find top N jobs that best match student's RIASEC profile.
    Uses combined profile matching (cosine similarity + Holland code).
    Returns list of {job: title, distance: score, riasec_scores: {...}}
    """
    jobs = load_job_riasec_scores(csv_path)
    
    student_holland = get_holland_code(student_scores, 3)
    logging.info(f"Student Holland code: {student_holland}")
    
    matches = []
    for job_title, job_scores in jobs.items():
        if len(job_scores) == 6:  # Ensure all 6 scores exist
            match_score = calculate_profile_match_score(student_scores, job_scores)
            job_holland = get_holland_code(job_scores, 3)
            
            # Convert to "distance" format for backward compatibility
            # Lower distance = better match, so invert the score
            distance = 1 - match_score
            
            matches.append({
                'job': job_title,
                'distance': round(distance, 4),
                'match_score': round(match_score, 4),
                'holland_code': job_holland,
                'riasec_scores': job_scores
            })
    
    # Sort by distance (ascending - lower is better, meaning higher match score)
    matches.sort(key=lambda x: x['distance'])
    
    return matches[:top_n]


def send_request_to_gpt(prompt: str) -> str:
    """Send request to GPT for program matching."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
    }
    data = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "max_tokens": 2000
    }
    response = requests.post(os.getenv('OPENAI_ENDPOINT'), headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        logging.error(f"Failed to get response from GPT. Status code: {response.status_code}")
        return None


def get_unique_program_names(programs: List[Dict]) -> List[str]:
    """
    Extract unique program names from the list of programs.
    """
    program_names = set()
    for p in programs:
        program_name = p.get('program', '').strip()
        if program_name:
            # Clean up the program name - remove scholarship/language suffixes for grouping
            program_names.add(program_name)
    return sorted(list(program_names))


def get_program_suggestions_from_gpt(jobs: List[Dict], 
                                     available_programs: List[Dict],
                                     desired_universities: List[str] = None) -> Tuple[List[Dict], str, str]:
    """
    Use GPT to match jobs with program NAMES (not university-specific).
    Then match the suggested program names with actual university programs
    based on student preferences and score.
    
    Returns tuple: (suggestions list, prompt, response)
    """
    # Get unique program names (not university-specific)
    unique_programs = get_unique_program_names(available_programs)
    
    if not unique_programs:
        return [], None, None
    
    programs_text = "\n".join([f"- {p}" for p in unique_programs[:150]])  # Limit to avoid token limits
    
    prompt = f"""Sen bir kariyer danışmanısın. Aşağıdaki meslek önerileri ve mevcut üniversite program adları listesi verilmiştir.

ÖNEMLİ: Sadece program adları verilmiştir, üniversite isimleri yok. Sen sadece mesleğe uygun PROGRAM ADLARINI seçeceksin.

Her meslek için, o mesleğe en uygun 5 program ADINI seç. Bu programlar o mesleğe götürebilecek veya o meslekle alakalı olmalıdır.

MESLEK ÖNERİLERİ:
1. {jobs[0]['job']}
2. {jobs[1]['job']}
3. {jobs[2]['job']}

MEVCUT PROGRAM ADLARI:
{programs_text}

Yanıtını SADECE aşağıdaki JSON formatında ver, başka hiçbir açıklama ekleme:
{{
  "job_1": {{
    "job_name": "{jobs[0]['job']}",
    "programs": [
      {{"program": "Program Adı", "reason": "Bu program neden bu mesleğe uygun - kısa açıklama"}},
      {{"program": "Program Adı", "reason": "..."}},
      {{"program": "Program Adı", "reason": "..."}},
      {{"program": "Program Adı", "reason": "..."}},
      {{"program": "Program Adı", "reason": "..."}}
    ]
  }},
  "job_2": {{
    "job_name": "{jobs[1]['job']}",
    "programs": [...]
  }},
  "job_3": {{
    "job_name": "{jobs[2]['job']}",
    "programs": [...]
  }}
}}
"""

    response = send_request_to_gpt(prompt)
    
    if response:
        try:
            # Extract JSON from response
            import json
            # Find JSON in response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                result = json.loads(json_str)
                
                # Now match GPT's program suggestions with actual university programs
                suggestions = []
                
                for i, job in enumerate(jobs):
                    job_key = f"job_{i+1}"
                    if job_key not in result:
                        continue
                    
                    job_data = result[job_key]
                    gpt_programs = job_data.get('programs', [])
                    
                    for gpt_program in gpt_programs:
                        program_name = gpt_program.get('program', '').lower()
                        reason = gpt_program.get('reason', '')
                        
                        if not program_name:
                            continue
                        
                        # Find matching actual programs (with universities)
                        matching_programs = []
                        for p in available_programs:
                            actual_name = p.get('program', '').lower()
                            # Fuzzy match: check if the GPT program name is contained in or similar to actual
                            if program_name in actual_name or actual_name in program_name:
                                matching_programs.append(p)
                        
                        if not matching_programs:
                            # Try partial match
                            program_words = program_name.split()
                            for p in available_programs:
                                actual_name = p.get('program', '').lower()
                                # Match if at least 2 key words match
                                matches = sum(1 for word in program_words if len(word) > 3 and word in actual_name)
                                if matches >= 2:
                                    matching_programs.append(p)
                        
                        # Sort matching programs: preferred universities first, then by ranking
                        def sort_key(p):
                            uni_priority = 0
                            if desired_universities:
                                program_uni = p.get('university', '').upper()
                                for idx, desired_uni in enumerate(desired_universities):
                                    if desired_uni.upper() in program_uni or program_uni in desired_uni.upper():
                                        uni_priority = len(desired_universities) - idx
                                        break
                            tbs = p.get('tbs_parsed') or parse_ranking(p.get('tbs_2025', '')) or 999999
                            return (-uni_priority, tbs)
                        
                        matching_programs.sort(key=sort_key)
                        
                        # Take top 2 university matches per program
                        for matched in matching_programs[:2]:
                            # Avoid duplicates
                            existing = [s for s in suggestions 
                                       if s['program'] == matched.get('program') 
                                       and s['university'] == matched.get('university')]
                            if not existing:
                                suggestions.append({
                                    'job': job['job'],
                                    'job_distance': job['distance'],
                                    'program': matched.get('program', ''),
                                    'university': matched.get('university', ''),
                                    'faculty': matched.get('faculty', ''),
                                    'city': matched.get('city', ''),
                                    'taban_score': matched.get('taban_2025', ''),
                                    'scholarship': matched.get('scholarship', ''),
                                    'reason': reason
                                })
                
                return suggestions[:15], prompt, response  # Limit to 15 suggestions
        except Exception as e:
            logging.error(f"Error parsing GPT response: {e}")
    
    return [], prompt, response


def parse_ranking(ranking_str: str) -> Optional[int]:
    """Parse Turkish ranking format to int (dot as thousands separator)."""
    if not ranking_str or ranking_str == 'Dolmadı':
        return None
    try:
        # Ranking uses dot as thousands separator
        cleaned = ranking_str.replace('.', '')
        return int(cleaned)
    except ValueError:
        return None
