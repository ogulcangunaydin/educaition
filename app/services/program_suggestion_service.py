import json
import logging
import os

from sqlalchemy.orm import Session

from .riasec_service import find_top_matching_jobs, get_program_suggestions_from_gpt


def load_programs_from_db(db: Session) -> list[dict]:
    """
    Load all programs from the database.
    """
    from app.modules.universities.service import ProgramService

    return ProgramService.get_all_programs_as_dicts(db)


def load_score_distribution(json_path: str = None) -> dict:
    """
    Load score-to-ranking distribution data.
    """
    if json_path is None:
        json_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "score_ranking_distribution.json"
        )

    try:
        with open(json_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading score distribution: {e}")
        return {}


def estimate_ranking_from_score(
    score: float, area: str, distribution_data: dict
) -> int | None:
    """
    Estimate ranking based on score using distribution data.
    """
    if not distribution_data:
        return None

    area_lower = area.lower()
    area_data = distribution_data.get(area_lower)
    if not area_data or "distribution" not in area_data:
        return None

    distribution = area_data["distribution"]
    if not distribution:
        return None

    # Find closest score bucket
    closest_idx = 0
    min_diff = float("inf")

    for i, item in enumerate(distribution):
        diff = abs(item["score"] - score)
        if diff < min_diff:
            min_diff = diff
            closest_idx = i

    return distribution[closest_idx]["avgRanking"]


def parse_score(score_val) -> float | None:
    """Parse score to float. Handles both string (from CSV) and numeric (from DB) values."""
    if score_val is None:
        return None
    if isinstance(score_val, (int, float)):
        return float(score_val) if score_val != 0 else None
    # Handle string values (legacy CSV format)
    if not score_val or score_val == "Dolmadı":
        return None
    try:
        # Score uses comma as decimal separator
        cleaned = str(score_val).replace(",", ".")
        return float(cleaned)
    except ValueError:
        return None


def parse_ranking(ranking_val) -> int | None:
    """Parse ranking to int. Handles both string (from CSV) and numeric (from DB) values."""
    if ranking_val is None:
        return None
    if isinstance(ranking_val, (int, float)):
        return int(ranking_val) if ranking_val != 0 else None
    # Handle string values (legacy CSV format)
    if not ranking_val or ranking_val == "Dolmadı":
        return None
    try:
        # Ranking uses dot as thousands separator
        cleaned = str(ranking_val).replace(".", "")
        return int(cleaned)
    except ValueError:
        return None


def filter_programs_by_ranking_and_area(
    programs: list[dict],
    expected_ranking: int,
    area: str,
    alternative_ranking: int | None = None,
    alternative_area: str | None = None,
    preferred_language: str | None = None,
    desired_universities: list[str] | None = None,
    desired_cities: list[str] | None = None,
    min_programs: int = 30,
) -> list[dict]:
    """
    Filter programs based on student's expected ranking and preferences.
    Uses progressive relaxation to GUARANTEE at least min_programs are found.

    Relaxation levels:
    1. All preferences (area, language, city, ranking ±5% to ±100%)
    2. Relax city preference
    3. Relax language preference
    4. Expand to alternative area
    5. Expand ranking to ±200%
    6. Ultimate fallback: closest programs by ranking only

    Args:
        programs: List of all programs
        expected_ranking: Expected ranking (estimated from score)
        area: Main area (say, ea, söz, dil)
        alternative_ranking: Alternative expected ranking
        alternative_area: Alternative area
        preferred_language: Preferred education language
        desired_universities: List of preferred universities
        desired_cities: List of preferred cities (istanbul, ankara, izmir, other)
        min_programs: Minimum number of programs to return (default 30)
    """

    # Map area codes
    area_map = {"say": "say", "ea": "ea", "söz": "söz", "dil": "dil"}

    main_area_code = area_map.get(area.lower(), area) if area else None
    alt_area_code = (
        area_map.get(alternative_area.lower(), alternative_area)
        if alternative_area
        else None
    )

    def check_city_match(program_city: str, city_prefs: list[str]) -> bool:
        """Check if program city matches any preference."""
        if not city_prefs:
            return True
        city = program_city.upper()
        for pref_city in city_prefs:
            pref_city_lower = pref_city.lower()
            if (
                pref_city_lower == "istanbul"
                and "İSTANBUL" in city
                or pref_city_lower == "ankara"
                and "ANKARA" in city
                or pref_city_lower == "izmir"
                and "İZMİR" in city
            ):
                return True
            elif pref_city_lower == "other":
                if (
                    "İSTANBUL" not in city
                    and "ANKARA" not in city
                    and "İZMİR" not in city
                ):
                    return True
        return False

    def check_language_match(program_detail: str, lang_pref: str) -> bool:
        """Check if program language matches preference."""
        if not lang_pref:
            return True
        detail_lower = program_detail.lower()
        if lang_pref.lower() == "ingilizce":
            return "ingilizce" in detail_lower or "english" in detail_lower
        elif lang_pref.lower() == "türkçe":
            return "ingilizce" not in detail_lower and "english" not in detail_lower
        return True

    def filter_with_options(
        check_city: bool,
        check_language: bool,
        include_alt_area: bool,
        max_expansion: float,
    ) -> list[dict]:
        """
        Filter programs with specified options.
        Returns filtered list sorted by preference and ranking.
        """
        filtered = []

        for program in programs:
            puan_type = program.get("puan_type", "").lower()

            # Check area match
            is_main_area = puan_type == main_area_code if main_area_code else False
            is_alt_area = puan_type == alt_area_code if alt_area_code else False

            if not is_main_area and not (include_alt_area and is_alt_area):
                continue

            # Parse ranking
            tbs = parse_ranking(program.get("tbs_2025", ""))
            taban = parse_score(program.get("taban_2025", ""))

            if tbs is None:
                continue

            # Determine which ranking to check against
            if is_main_area:
                check_ranking = expected_ranking
            else:
                check_ranking = (
                    alternative_ranking if alternative_ranking else expected_ranking
                )

            # Check ranking range
            lower_bound = int(check_ranking / max_expansion)
            upper_bound = int(check_ranking * max_expansion)

            if not (lower_bound <= tbs <= upper_bound):
                continue

            # Check language preference
            if check_language and preferred_language:
                if not check_language_match(
                    program.get("program_detail", ""), preferred_language
                ):
                    continue

            # Check city preference
            if check_city and desired_cities:
                if not check_city_match(program.get("city", ""), desired_cities):
                    continue

            # Calculate university priority
            university_priority = 0
            if desired_universities:
                program_uni = program.get("university", "").upper()
                for i, desired_uni in enumerate(desired_universities):
                    if (
                        desired_uni.upper() in program_uni
                        or program_uni in desired_uni.upper()
                    ):
                        university_priority = len(desired_universities) - i
                        break

            # Add to filtered with metadata
            filtered_program = dict(program)
            filtered_program["is_main_area"] = is_main_area
            filtered_program["university_priority"] = university_priority
            filtered_program["tbs_parsed"] = tbs
            filtered_program["taban_parsed"] = taban
            filtered_program["ranking_distance"] = abs(tbs - check_ranking)
            filtered.append(filtered_program)

        # Sort: main area first, university priority, then by ranking distance
        filtered.sort(
            key=lambda x: (
                not x["is_main_area"],
                -x["university_priority"],
                x["ranking_distance"],
            )
        )

        return filtered

    # Progressive relaxation strategy
    relaxation_levels = [
        # (check_city, check_language, include_alt_area, max_expansion, description)
        (True, True, True, 1.05, "All preferences, ±5%"),
        (True, True, True, 1.10, "All preferences, ±10%"),
        (True, True, True, 1.20, "All preferences, ±20%"),
        (True, True, True, 1.30, "All preferences, ±30%"),
        (True, True, True, 1.50, "All preferences, ±50%"),
        (True, True, True, 1.75, "All preferences, ±75%"),
        (True, True, True, 2.00, "All preferences, ±100%"),
        (False, True, True, 2.00, "No city filter, ±100%"),
        (False, False, True, 2.00, "No city/language filter, ±100%"),
        (False, False, True, 3.00, "No city/language filter, ±200%"),
        (False, False, True, 5.00, "No city/language filter, ±400%"),
        (False, False, True, 10.00, "No city/language filter, ±900%"),
    ]

    for check_city, check_lang, include_alt, max_exp, desc in relaxation_levels:
        filtered = filter_with_options(check_city, check_lang, include_alt, max_exp)
        logging.info(f"Relaxation '{desc}': {len(filtered)} programs")

        if len(filtered) >= min_programs:
            logging.info(f"Found {len(filtered)} programs with relaxation: {desc}")
            return filtered

    # Ultimate fallback: get ALL programs in the area, sorted by ranking distance
    logging.warning("Using ultimate fallback - returning closest programs by ranking")

    all_area_programs = []
    for program in programs:
        puan_type = program.get("puan_type", "").lower()
        is_main_area = puan_type == main_area_code if main_area_code else False
        is_alt_area = puan_type == alt_area_code if alt_area_code else False

        if not is_main_area and not is_alt_area:
            continue

        tbs = parse_ranking(program.get("tbs_2025", ""))
        taban = parse_score(program.get("taban_2025", ""))

        if tbs is None:
            continue

        check_ranking = (
            expected_ranking
            if is_main_area
            else (alternative_ranking or expected_ranking)
        )

        university_priority = 0
        if desired_universities:
            program_uni = program.get("university", "").upper()
            for i, desired_uni in enumerate(desired_universities):
                if (
                    desired_uni.upper() in program_uni
                    or program_uni in desired_uni.upper()
                ):
                    university_priority = len(desired_universities) - i
                    break

        filtered_program = dict(program)
        filtered_program["is_main_area"] = is_main_area
        filtered_program["university_priority"] = university_priority
        filtered_program["tbs_parsed"] = tbs
        filtered_program["taban_parsed"] = taban
        filtered_program["ranking_distance"] = abs(tbs - check_ranking)
        all_area_programs.append(filtered_program)

    # Sort by university priority first, then by ranking distance
    all_area_programs.sort(
        key=lambda x: (-x["university_priority"], x["ranking_distance"])
    )

    logging.info(f"Ultimate fallback: returning {len(all_area_programs)} programs")
    return all_area_programs[: max(min_programs * 2, 60)]  # Return more for safety


def get_suggested_programs(
    riasec_scores: dict[str, float],
    expected_score: float,
    area: str,
    alternative_score: float | None = None,
    alternative_area: str | None = None,
    preferred_language: str | None = None,
    desired_universities: list[str] | None = None,
    desired_cities: list[str] | None = None,
    db: Session = None,
    distribution_json_path: str = None,
) -> dict:
    """
    Main function to get program suggestions for a student.
    Uses ranking-based filtering to ensure at least 30 programs for GPT.

    Args:
        db: Database session (required for loading programs and RIASEC data)
        distribution_json_path: Path to score distribution JSON file

    Returns:
        {
            'riasec_scores': {...},
            'suggested_jobs': [...],
            'suggested_programs': [],
            'gpt_prompt': ...,
            'gpt_response': ...
        }
    """
    # Step 1: Find top 6 matching jobs
    suggested_jobs = find_top_matching_jobs(
        riasec_scores, db=db, top_n=6
    )

    if not suggested_jobs:
        return {
            "riasec_scores": riasec_scores,
            "suggested_jobs": [],
            "suggested_programs": [],
            "gpt_prompt": None,
            "gpt_response": None,
        }

    # Step 2: Load distribution data and convert scores to rankings
    distribution_data = load_score_distribution(distribution_json_path)

    # Estimate rankings from scores
    expected_ranking = estimate_ranking_from_score(
        expected_score, area, distribution_data
    )
    alternative_ranking = None
    if alternative_score and alternative_area:
        alternative_ranking = estimate_ranking_from_score(
            alternative_score, alternative_area, distribution_data
        )

    logging.info(f"Score {expected_score} ({area}) -> Ranking {expected_ranking}")
    if alternative_ranking:
        logging.info(
            f"Alt Score {alternative_score} ({alternative_area}) -> Ranking {alternative_ranking}"
        )

    # Fallback if distribution data not available
    if expected_ranking is None:
        # Use a rough estimate: higher score = lower (better) ranking
        # This is a very rough approximation
        expected_ranking = int(1500000 - (expected_score * 2500))
        expected_ranking = max(1, expected_ranking)

    # Step 3: Filter programs by ranking and preferences
    # Load programs from database if db session provided, otherwise raise error
    if db is None:
        raise ValueError("Database session is required to load programs")
    all_programs = load_programs_from_db(db)
    filtered_programs = filter_programs_by_ranking_and_area(
        programs=all_programs,
        expected_ranking=expected_ranking,
        area=area,
        alternative_ranking=alternative_ranking,
        alternative_area=alternative_area,
        preferred_language=preferred_language,
        desired_universities=desired_universities,
        desired_cities=desired_cities,
        min_programs=100,  # Ensure at least 100 programs for more variety
    )

    if not filtered_programs:
        return {
            "riasec_scores": riasec_scores,
            "suggested_jobs": suggested_jobs,
            "suggested_programs": [],
            "gpt_prompt": None,
            "gpt_response": None,
        }

    # Step 3: Use GPT to match jobs with filtered programs
    suggested_programs, gpt_prompt, gpt_response = get_program_suggestions_from_gpt(
        suggested_jobs, filtered_programs, desired_universities=desired_universities
    )

    # If GPT fails, fall back to simple selection
    if not suggested_programs:
        # Simple fallback: return top programs distributed across jobs
        suggested_programs = []
        for i, program in enumerate(filtered_programs[:36]):  # 6 jobs * 6 programs
            job_index = i // 6
            if job_index < len(suggested_jobs):
                is_halic = "haliç" in program.get("university", "").lower() or "halic" in program.get("university", "").lower()
                suggested_programs.append(
                    {
                        "job": suggested_jobs[job_index]["job"],
                        "job_distance": suggested_jobs[job_index]["distance"],
                        "program": program.get("program", ""),
                        "university": program.get("university", ""),
                        "faculty": program.get("faculty", ""),
                        "city": program.get("city", ""),
                        "taban_score": program.get("taban_2025", ""),
                        "scholarship": program.get("scholarship", ""),
                        "reason": "Puan aralığınıza uygun program",
                        "is_priority": is_halic,
                    }
                )

    # Step 4: Add Haliç University programs by matching program names (no score filter)
    # Get all suggested program names from GPT results
    suggested_program_names = set()
    for sp in suggested_programs:
        prog_name = sp.get("program", "").lower().strip()
        if prog_name:
            suggested_program_names.add(prog_name)
            # Also add partial matches (first 3 significant words)
            words = [w for w in prog_name.split() if len(w) > 2]
            if len(words) >= 2:
                suggested_program_names.add(" ".join(words[:3]))

    # Find matching Haliç programs from ALL programs (not just filtered)
    halic_programs = []
    for program in all_programs:
        uni_name = program.get("university", "").lower()
        if "haliç" in uni_name or "halic" in uni_name:
            prog_name = program.get("program", "").lower().strip()
            # Check if this program name matches any suggested program
            is_match = False
            for suggested_name in suggested_program_names:
                if suggested_name in prog_name or prog_name in suggested_name:
                    is_match = True
                    break
                # Also check word overlap
                suggested_words = set(w for w in suggested_name.split() if len(w) > 3)
                prog_words = set(w for w in prog_name.split() if len(w) > 3)
                if len(suggested_words & prog_words) >= 2:
                    is_match = True
                    break
            
            if is_match:
                # Find the most relevant job for this program
                best_job = suggested_jobs[0] if suggested_jobs else {"job": "Genel", "distance": 0}
                for sp in suggested_programs:
                    if sp.get("program", "").lower() in prog_name or prog_name in sp.get("program", "").lower():
                        best_job = {"job": sp.get("job"), "distance": sp.get("job_distance", 0)}
                        break
                
                # Check if already in suggestions
                already_exists = any(
                    sp.get("program", "").lower() == prog_name 
                    and sp.get("university", "").lower() == uni_name
                    for sp in suggested_programs
                )
                
                if not already_exists:
                    halic_programs.append({
                        "job": best_job["job"],
                        "job_distance": best_job["distance"],
                        "program": program.get("program", ""),
                        "university": program.get("university", ""),
                        "faculty": program.get("faculty", ""),
                        "city": program.get("city", ""),
                        "taban_score": program.get("taban_2025", ""),
                        "scholarship": program.get("scholarship", ""),
                        "reason": "Haliç Üniversitesi'nden önerilen program",
                        "is_priority": True,
                    })

    # Combine: Haliç programs first, then other suggestions
    combined_programs = halic_programs + suggested_programs
    
    # Remove duplicates while preserving order
    seen = set()
    unique_programs = []
    for prog in combined_programs:
        key = (prog.get("program", "").lower(), prog.get("university", "").lower())
        if key not in seen:
            seen.add(key)
            unique_programs.append(prog)

    # Enrich program suggestions with additional data
    enriched_programs = []
    for suggestion in unique_programs[:200]:  # Limit to 200
        # Find matching program in all programs to get additional details
        matching_program = None
        for fp in all_programs:
            if (
                suggestion.get("program", "").lower() in fp.get("program", "").lower()
                and suggestion.get("university", "").lower()
                in fp.get("university", "").lower()
            ):
                matching_program = fp
                break

        enriched = dict(suggestion)
        if matching_program:
            enriched["yop_kodu"] = matching_program.get("yop_kodu", "")
            enriched["faculty"] = matching_program.get("faculty", "")
            enriched["city"] = matching_program.get("city", "")
            enriched["taban_score"] = matching_program.get("taban_2025", "")
            enriched["tavan_score"] = matching_program.get("tavan_2025", "")
            enriched["scholarship"] = matching_program.get("scholarship", "")
            enriched["university_type"] = matching_program.get("university_type", "")

        enriched_programs.append(enriched)

    logging.info(f"Total programs: {len(enriched_programs)} (Haliç: {len(halic_programs)})")

    return {
        "riasec_scores": riasec_scores,
        "suggested_jobs": suggested_jobs,
        "suggested_programs": enriched_programs,
        "gpt_prompt": gpt_prompt,
        "gpt_response": gpt_response,
    }
