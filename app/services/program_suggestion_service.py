"""
Program Suggestion Service — v2

New architecture:
1. Get top 30 (or 60 if dual-area) RIASEC-matched jobs
2. GPT refines to 6 jobs per area considering student's score level (encouraging tone)
3. GPT suggests 6 program names per job (36 total per area)
4. For each program name, find real university programs:
   a. Haliç first — pick the right scholarship level for the student's score
   b. Then 10+ other programs matched by name similarity and score range
5. Return structured result: jobs → program_names → real_programs (grouped)
"""

import json
import logging
import os
import unicodedata
from difflib import SequenceMatcher

from sqlalchemy.orm import Session

from .riasec_service import find_top_matching_jobs, send_request_to_gpt


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


logger = logging.getLogger(__name__)

AREA_MAP = {"say": "say", "ea": "ea", "söz": "söz", "dil": "dil"}
MAX_SCORE_TURKEY = 500  # Approximate max YKS score


def _normalize_turkish(text: str) -> str:
    """Normalize Turkish text for safe comparison.
    Turkish İ (U+0130) lowercases to 'i' + combining dot above (U+0307)
    which breaks simple string matching. NFC normalization + stripping
    the combining dot fixes this.
    """
    lowered = text.lower()
    # NFC normalize, then strip combining dot above (U+0307)
    normalized = unicodedata.normalize("NFC", lowered)
    return normalized.replace("\u0307", "")


def _is_halic(university_name: str) -> bool:
    """Check if a university is Haliç."""
    uni = _normalize_turkish(university_name)
    return "haliç" in uni or "halic" in uni


def _name_similarity(a: str, b: str) -> float:
    """Simple name similarity using SequenceMatcher. Returns 0-1."""
    a_clean = _normalize_turkish(a).strip()
    b_clean = _normalize_turkish(b).strip()
    if a_clean == b_clean:
        return 1.0
    if a_clean in b_clean or b_clean in a_clean:
        return 0.9
    return SequenceMatcher(None, a_clean, b_clean).ratio()


# ---------------------------------------------------------------------------
# Step 1: Refine jobs with GPT
# ---------------------------------------------------------------------------

def _refine_jobs_with_gpt(
    candidate_jobs: list[dict],
    area: str,
    expected_score: float,
    is_alternative: bool = False,
) -> list[dict]:
    """
    Ask GPT to pick the 6 best jobs from candidates, considering the student's
    area and expected score. Encourages aspirational but realistic suggestions.
    """
    area_labels = {
        "say": "Sayısal (Matematik-Fen)",
        "ea": "Eşit Ağırlık (Matematik-Edebiyat)",
        "söz": "Sözel (Edebiyat-Sosyal)",
        "dil": "Yabancı Dil",
    }
    area_label = area_labels.get(area.lower(), area)

    score_pct = min(expected_score / MAX_SCORE_TURKEY * 100, 100)
    if score_pct >= 70:
        score_level = "yüksek"
    elif score_pct >= 40:
        score_level = "orta"
    else:
        score_level = "başlangıç"

    job_list = "\n".join(
        f"{i+1}. {j['job']} (uyum: %{int(j.get('match_score', 0)*100)})"
        for i, j in enumerate(candidate_jobs)
    )

    prompt = f"""Sen Türkiye'deki bir üniversite kariyer danışmanısın. Bir öğrenci için en uygun 6 mesleği seçmen gerekiyor.

ÖĞRENCİ PROFİLİ:
- Alan: {area_label}
- Beklenen puan seviyesi: {score_level} ({expected_score:.0f}/{MAX_SCORE_TURKEY})
- Bu {'alternatif alanı' if is_alternative else 'ana alanı'}

RIASEC TESTİNE GÖRE EN YAKIN MESLEKLER:
{job_list}

GÖREV:
Bu listeden öğrenciye en uygun 6 mesleği seç. Seçimde şunlara dikkat et:
- Öğrencinin alanına ({area_label}) uygun meslekler öncelikli olsun
- Puan seviyesine göre gerçekçi ama teşvik edici meslekler seç
- Öğrenciyi cesaretlendir — potansiyelini göster, küçümseme
- Çeşitlilik sağla — farklı sektörlerden meslekler olsun
- Her meslek için öğrenciye neden uygun olduğunu kısaca açıkla

Yanıtını SADECE aşağıdaki JSON formatında ver:
{{
  "jobs": [
    {{"job": "Meslek Adı (İngilizce, listeden aynen kopyala)", "reason": "Türkçe kısa açıklama (1-2 cümle)"}},
    ... (toplam 6 meslek)
  ]
}}"""

    response = send_request_to_gpt(prompt)
    if not response:
        return candidate_jobs[:6]

    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start == -1 or end <= start:
            return candidate_jobs[:6]

        result = json.loads(response[start:end])
        selected_job_names = {j["job"].lower().strip() for j in result.get("jobs", [])}
        reasons = {j["job"].lower().strip(): j.get("reason", "") for j in result.get("jobs", [])}

        refined = []
        for cj in candidate_jobs:
            if cj["job"].lower().strip() in selected_job_names:
                cj_copy = dict(cj)
                cj_copy["reason"] = reasons.get(cj["job"].lower().strip(), "")
                refined.append(cj_copy)
                if len(refined) == 6:
                    break

        if len(refined) < 6:
            for cj in candidate_jobs:
                if cj not in refined:
                    refined.append(cj)
                    if len(refined) == 6:
                        break

        return refined
    except Exception as e:
        logging.error(f"Error parsing GPT job refinement: {e}")
        return candidate_jobs[:6]


# ---------------------------------------------------------------------------
# Step 2: Get program names from GPT — one job at a time for quality
# ---------------------------------------------------------------------------

def _get_program_names_for_single_job(
    job: dict,
    available_program_names: list[str],
    area: str,
) -> list[dict]:
    """
    Ask GPT to suggest relevant program names for ONE job from the available list.
    GPT decides how many (3-8) based on relevance — no forced count.
    Returns: [{program_name, reason}, ...]
    """
    area_labels = {
        "say": "Sayısal",
        "ea": "Eşit Ağırlık",
        "söz": "Sözel",
        "dil": "Yabancı Dil",
    }
    area_label = area_labels.get(area.lower(), area)

    programs_text = "\n".join(f"- {p}" for p in available_program_names[:500])
    job_name = job["job"]
    job_reason = job.get("reason", "")

    prompt = f"""Sen bir üniversite kariyer danışmanısın. Bir öğrenciye "{job_name}" mesleği için uygun üniversite programları öneriyorsun.

ÖĞRENCİ ALANI: {area_label}

MESLEK: {job_name}
{f'Meslek Açıklaması: {job_reason}' if job_reason else ''}

KRİTİK KURALLAR:
1. SADECE bu meslekle DOĞRUDAN veya GÜÇLÜ BİR ŞEKİLDE ilgili programları seç
2. İlgisiz veya çok uzak bağlantılı programları KESİNLİKLE ekleme
3. Sayı konusunda esnek ol: 3 ile 8 arası program öner, ama sadece GERÇEKTEN ilgili olanları
4. Az ama kaliteli > çok ama alakasız
5. Program adlarını listeden BİREBİR kopyala (yazım farkı olmasın)
6. Her program için neden bu meslekle ilgili olduğunu açıkla

MEVCUT PROGRAM ADLARI:
{programs_text}

Yanıtını SADECE aşağıdaki JSON formatında ver:
{{
  "programs": [
    {{"program": "Program Adı (listeden birebir kopyala)", "reason": "Bu meslek için neden uygun (Türkçe, 1 cümle)"}},
    ...
  ]
}}"""

    response = send_request_to_gpt(prompt)
    if not response:
        return []

    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start == -1 or end <= start:
            return []

        result = json.loads(response[start:end])
        programs = []
        for p in result.get("programs", [])[:8]:
            name = p.get("program", "").strip()
            reason = p.get("reason", "").strip()
            if name:
                programs.append({"program_name": name, "reason": reason})

        logging.info(f"GPT suggested {len(programs)} programs for job '{job_name}'")
        return programs
    except Exception as e:
        logging.error(f"Error parsing GPT program names for {job_name}: {e}")
        return []


# ---------------------------------------------------------------------------
# Step 3: Match program names to real programs
# ---------------------------------------------------------------------------

def _find_best_halic_program(
    program_name: str,
    halic_programs_by_name: dict[str, list[dict]],
    expected_score: float,
) -> dict | None:
    """
    Find the best Haliç program matching the given program name.
    Always returns the best scholarship variant to promote Haliç,
    even if the student's score is below the minimum threshold.
    Scholarship priority: Burslu > %50 İndirimli > %25 İndirimli > Ücretli
    """
    best_match = None
    best_sim = 0.0

    for halic_name, variants in halic_programs_by_name.items():
        sim = _name_similarity(program_name, halic_name)
        if sim > best_sim and sim >= 0.45:
            best_sim = sim
            best_match = variants

    if not best_match:
        return None

    # Scholarship priority: lower number = better scholarship
    SCHOLARSHIP_PRIORITY = {
        "burslu": 0,
        "%50 indirimli": 1,
        "%25 indirimli": 2,
        "ucretli": 3, "ücretli": 3,
    }

    best_variant = None
    best_priority = 99
    best_diff = float("inf")

    for variant in best_match:
        scholarship = (variant.get("scholarship", "") or "").strip()
        priority = SCHOLARSHIP_PRIORITY.get(_normalize_turkish(scholarship), 5)
        taban = parse_score(variant.get("taban_2025"))
        diff = abs(expected_score - taban) if taban else 999999

        # Pick best scholarship first; among same tier, prefer closest score
        if (priority < best_priority) or (priority == best_priority and diff < best_diff):
            best_priority = priority
            best_diff = diff
            best_variant = variant

    return best_variant


def _find_real_programs(
    program_name: str,
    all_programs: list[dict],
    area_code: str,
    expected_ranking: int,
    min_count: int = 10,
    max_expansion: float = 100.0,
) -> list[dict]:
    """
    Find real university programs matching a program name, filtered by area
    and score range. Uses progressive expansion to get at least min_count.
    Excludes Haliç (handled separately).
    """
    scored = []
    for p in all_programs:
        if _is_halic(p.get("university", "")):
            continue
        puan_type = p.get("puan_type", "").lower()
        if puan_type != area_code:
            continue

        sim = _name_similarity(program_name, p.get("program", ""))
        if sim < 0.50:
            continue

        tbs = parse_ranking(p.get("tbs_2025"))
        scored.append({
            "program_data": p,
            "similarity": sim,
            "tbs": tbs,
            "ranking_distance": abs(tbs - expected_ranking) if tbs else 999999,
        })

    if not scored:
        return []

    scored.sort(key=lambda x: (-x["similarity"], x["ranking_distance"]))

    expansions = [2.0, 5.0, 10.0, 50.0, max_expansion]
    for exp in expansions:
        lower = int(expected_ranking / exp)
        upper = int(expected_ranking * exp)

        in_range = [
            s for s in scored
            if s["tbs"] is None or (lower <= s["tbs"] <= upper)
        ]

        if len(in_range) >= min_count:
            return [s["program_data"] for s in in_range[:min_count + 5]]

    return [s["program_data"] for s in scored[:min_count]]


def _build_program_dict(program: dict, job_name: str = "", reason: str = "") -> dict:
    """Build a standardized program output dictionary."""
    return {
        "job": job_name,
        "program": program.get("program", ""),
        "university": program.get("university", ""),
        "faculty": program.get("faculty", ""),
        "city": program.get("city", ""),
        "yop_kodu": program.get("yop_kodu", ""),
        "taban_score": program.get("taban_2025", ""),
        "tavan_score": program.get("tavan_2025", ""),
        "scholarship": program.get("scholarship", ""),
        "university_type": program.get("university_type", ""),
        "reason": reason,
        "is_priority": _is_halic(program.get("university", "")),
    }


# ---------------------------------------------------------------------------
# Step 4: Process one area (main or alternative)
# ---------------------------------------------------------------------------

def _process_area(
    riasec_scores: dict[str, float],
    expected_score: float,
    area: str,
    expected_ranking: int,
    all_programs: list[dict],
    available_program_names: list[str],
    halic_programs_by_name: dict[str, list[dict]],
    candidate_jobs: list[dict],
    is_alternative: bool = False,
    exclude_job_names: set[str] | None = None,
) -> dict:
    """
    Process suggestions for one area. Returns:
    {
        "jobs": [...],
        "program_groups": [
            {
                "job": "...",
                "program_name": "...",
                "reason": "...",
                "halic_program": {...} or None,
                "programs": [...]
            }, ...
        ]
    }
    """
    area_code = AREA_MAP.get(area.lower(), area)

    # Filter out already-used jobs for dual-area
    if exclude_job_names:
        filtered_candidates = [
            j for j in candidate_jobs
            if j["job"].lower().strip() not in exclude_job_names
        ]
        if len(filtered_candidates) < 12:
            filtered_candidates = candidate_jobs
    else:
        filtered_candidates = candidate_jobs

    refined_jobs = _refine_jobs_with_gpt(
        filtered_candidates, area, expected_score, is_alternative
    )

    # Tag each job with its area
    for j in refined_jobs:
        j["area"] = area.lower()

    logging.info(f"Area {area}: refined {len(refined_jobs)} jobs")

    # Filter program names to this area
    area_program_names = []
    for p in all_programs:
        if p.get("puan_type", "").lower() == area_code:
            name = p.get("program", "").strip()
            if name and name not in area_program_names:
                area_program_names.append(name)

    # Get program names per job — one GPT call per job for quality
    job_program_map: dict[str, list[dict]] = {}
    for job in refined_jobs:
        job_name = job["job"]
        programs = _get_program_names_for_single_job(job, area_program_names, area)
        if programs:
            job_program_map[job_name] = programs
        else:
            # Fallback: grab some area program names
            start_idx = len(job_program_map) * 4
            job_program_map[job_name] = [
                {"program_name": n, "reason": "Alanınıza uygun program"}
                for n in area_program_names[start_idx:start_idx + 4]
            ]

    # For each program name, find real programs
    program_groups = []
    seen_program_names = set()

    for job in refined_jobs:
        job_name = job["job"]
        program_entries = job_program_map.get(job_name, [])

        for entry in program_entries:  # No [:6] limit — GPT decides relevance
            pname = entry["program_name"]
            reason = entry["reason"]

            pname_key = pname.lower().strip()
            if pname_key in seen_program_names:
                continue
            seen_program_names.add(pname_key)

            # Find Haliç match
            halic_match = _find_best_halic_program(
                pname, halic_programs_by_name, expected_score,
            )
            halic_program = None
            if halic_match:
                halic_program = _build_program_dict(halic_match, job_name, "Haliç Üniversitesi programı")

            # Find other real programs
            real_programs_raw = _find_real_programs(
                pname, all_programs, area_code, expected_ranking,
                min_count=10, max_expansion=100.0,
            )
            real_programs = [
                _build_program_dict(rp, job_name, reason)
                for rp in real_programs_raw
            ]

            program_groups.append({
                "job": job_name,
                "program_name": pname,
                "reason": reason,
                "halic_program": halic_program,
                "programs": real_programs,
            })

    logging.info(
        f"Area {area}: {len(refined_jobs)} jobs, "
        f"{len(program_groups)} program groups, "
        f"{sum(1 for g in program_groups if g['halic_program'])} with Haliç"
    )

    return {
        "jobs": refined_jobs,
        "program_groups": program_groups,
    }


def _flatten_program_groups(program_groups: list[dict]) -> list[dict]:
    """Flatten grouped programs into a flat list for backward compatibility."""
    flat = []
    seen = set()

    for group in program_groups:
        hp = group.get("halic_program")
        if hp:
            key = (hp["program"].lower(), hp["university"].lower())
            if key not in seen:
                seen.add(key)
                flat.append(hp)

        for p in group.get("programs", []):
            key = (p["program"].lower(), p["university"].lower())
            if key not in seen:
                seen.add(key)
                flat.append(p)

    return flat


# ---------------------------------------------------------------------------
# REMOVED: filter_programs_by_ranking_and_area (replaced by _process_area)
# ---------------------------------------------------------------------------


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
        # Sort: Haliç first, then main area, then university priority, then ranking distance
        filtered.sort(
            key=lambda x: (
                not ("haliç" in x.get("university", "").lower() or "halic" in x.get("university", "").lower()),
                not x["is_main_area"],
                -x["university_priority"],
                x["ranking_distance"],
            )
        )

        return filtered

    # Progressive relaxation strategy - START with very relaxed filters to get 200+ programs
    relaxation_levels = [
        # (check_city, check_language, include_alt_area, max_expansion, description)
        (False, False, True, 5.00, "No filters, ±400%"),  # Start very relaxed
        (False, False, True, 10.00, "No filters, ±900%"),
        (False, False, True, 20.00, "No filters, ±1900%"),
        (False, False, True, 50.00, "No filters, ±4900%"),
        (False, False, True, 100.00, "No filters, all rankings"),
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

    v2 flow:
    1. Get top 30/60 RIASEC-matched jobs
    2. GPT refines to 6 per area (no overlap if dual-area)
    3. GPT suggests 6 program names per job
    4. Match to real programs (Haliç first, then others by name + score)

    Returns:
    {
        "riasec_scores": {...},
        "suggested_jobs": [...],           # main area jobs
        "suggested_programs": [...],       # flat list (backward compat)
        "program_groups": [...],           # NEW: grouped structure
        "alternative_jobs": [...],         # if dual-area
        "alternative_program_groups": [],  # if dual-area
        "gpt_prompt": None,
        "gpt_response": None,
    }
    """
    if db is None:
        raise ValueError("Database session is required")

    # Load all programs once
    all_programs = load_programs_from_db(db)

    # Load score distribution
    distribution_data = load_score_distribution(distribution_json_path)

    # Estimate rankings
    expected_ranking = estimate_ranking_from_score(expected_score, area, distribution_data)
    if expected_ranking is None:
        expected_ranking = int(1500000 - (expected_score * 2500))
        expected_ranking = max(1, expected_ranking)

    alternative_ranking = None
    if alternative_score and alternative_area:
        alternative_ranking = estimate_ranking_from_score(
            alternative_score, alternative_area, distribution_data
        )
        if alternative_ranking is None:
            alternative_ranking = int(1500000 - (alternative_score * 2500))
            alternative_ranking = max(1, alternative_ranking)

    logging.info(f"Score {expected_score} ({area}) -> Ranking {expected_ranking}")
    if alternative_ranking:
        logging.info(f"Alt Score {alternative_score} ({alternative_area}) -> Ranking {alternative_ranking}")

    # Determine how many candidate jobs to pull
    has_alt = bool(alternative_area and alternative_score)
    top_n_jobs = 60 if has_alt else 30

    # Get RIASEC-matched candidate jobs
    candidate_jobs = find_top_matching_jobs(riasec_scores, db=db, top_n=top_n_jobs)

    if not candidate_jobs:
        return {
            "riasec_scores": riasec_scores,
            "suggested_jobs": [],
            "suggested_programs": [],
            "program_groups": [],
            "alternative_jobs": [],
            "alternative_program_groups": [],
            "gpt_prompt": None,
            "gpt_response": None,
        }

    # Build unique program names list and Haliç lookup
    all_program_names = sorted(set(
        p.get("program", "").strip()
        for p in all_programs
        if p.get("program", "").strip()
    ))

    halic_programs_by_name: dict[str, list[dict]] = {}
    for p in all_programs:
        if _is_halic(p.get("university", "")):
            name = p.get("program", "").strip()
            if name:
                halic_programs_by_name.setdefault(name, []).append(p)

    # Process main area
    main_result = _process_area(
        riasec_scores=riasec_scores,
        expected_score=expected_score,
        area=area,
        expected_ranking=expected_ranking,
        all_programs=all_programs,
        available_program_names=all_program_names,
        halic_programs_by_name=halic_programs_by_name,
        candidate_jobs=candidate_jobs,
        is_alternative=False,
    )

    # Process alternative area if exists
    alt_result = {"jobs": [], "program_groups": []}
    if has_alt:
        main_job_names = {j["job"].lower().strip() for j in main_result["jobs"]}
        alt_result = _process_area(
            riasec_scores=riasec_scores,
            expected_score=alternative_score,
            area=alternative_area,
            expected_ranking=alternative_ranking,
            all_programs=all_programs,
            available_program_names=all_program_names,
            halic_programs_by_name=halic_programs_by_name,
            candidate_jobs=candidate_jobs,
            is_alternative=True,
            exclude_job_names=main_job_names,
        )

    # Build flat suggested_programs for backward compatibility
    flat_programs = _flatten_program_groups(
        main_result["program_groups"] + alt_result["program_groups"]
    )

    # Merge all jobs into a single list (each tagged with area)
    all_jobs = main_result["jobs"] + alt_result["jobs"]

    return {
        "riasec_scores": riasec_scores,
        "suggested_jobs": all_jobs,
        "suggested_programs": flat_programs,
        "program_groups": main_result["program_groups"],
        "alternative_jobs": alt_result["jobs"],
        "alternative_program_groups": alt_result["program_groups"],
        "gpt_prompt": None,
        "gpt_response": None,
    }
