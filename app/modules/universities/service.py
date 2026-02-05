"""
Service layer for University and Program data access.
"""

import logging
from typing import Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.modules.universities.models import Program, ProgramYearlyStats, University
from app.modules.universities.schemas import ProgramFlat

logger = logging.getLogger(__name__)


class UniversityService:
    """Service for university-related database operations."""

    @staticmethod
    def get_all_universities(db: Session) -> list[University]:
        """Get all universities ordered by name."""
        return db.query(University).order_by(University.name).all()

    @staticmethod
    def get_university_by_id(db: Session, university_id: int) -> Optional[University]:
        """Get a university by ID."""
        return db.query(University).filter(University.id == university_id).first()

    @staticmethod
    def get_university_by_name(db: Session, name: str) -> Optional[University]:
        """Get a university by name (case-insensitive)."""
        return db.query(University).filter(
            func.lower(University.name) == func.lower(name)
        ).first()

    @staticmethod
    def get_cities(db: Session) -> list[str]:
        """Get all unique cities with universities."""
        result = db.query(University.city).distinct().order_by(University.city).all()
        return [row[0] for row in result]


class ProgramService:
    """Service for program-related database operations."""

    @staticmethod
    def get_programs_flat(
        db: Session,
        university_id: int | None = None,
        university_name: str | None = None,
        puan_type: str | None = None,
        year: int | None = None,
        city: str | None = None,
        program_name: str | None = None,
        min_tbs: int | None = None,
        max_tbs: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ProgramFlat], int]:
        """
        Get programs in flattened format matching frontend expectations.
        Returns (programs, total_count).
        """
        # Base query - use explicit column selection to avoid DISTINCT issues
        query = (
            db.query(Program)
            .join(University)
        )

        # Apply filters
        if university_id:
            query = query.filter(Program.university_id == university_id)

        if university_name:
            query = query.filter(
                func.lower(University.name).contains(func.lower(university_name))
            )

        if puan_type:
            query = query.filter(func.lower(Program.puan_type) == func.lower(puan_type))

        if city:
            query = query.filter(
                func.lower(University.city) == func.lower(city)
            )

        if program_name:
            query = query.filter(
                func.lower(Program.name).contains(func.lower(program_name))
            )

        # If filtering by year or TBS, we need to join yearly stats
        if year or min_tbs is not None or max_tbs is not None:
            query = query.join(ProgramYearlyStats)

            if year:
                query = query.filter(ProgramYearlyStats.year == year)
                query = query.filter(ProgramYearlyStats.has_data == True)

            if min_tbs is not None:
                query = query.filter(ProgramYearlyStats.taban_basari_sirasi >= min_tbs)

            if max_tbs is not None:
                query = query.filter(ProgramYearlyStats.taban_basari_sirasi <= max_tbs)

        # Get total count before pagination (subquery approach for distinct)
        # Use a subquery to get distinct program IDs first
        from sqlalchemy import distinct
        count_query = db.query(func.count(distinct(Program.id)))
        for criterion in query.whereclause.get_children() if query.whereclause is not None else []:
            pass  # Filters already applied
        total = query.with_entities(func.count(distinct(Program.id))).scalar()

        # Get distinct program IDs with pagination, then load full objects
        program_ids_query = (
            query.with_entities(Program.id, University.name.label('uni_name'), Program.name.label('prog_name'))
            .distinct()
            .order_by(University.name, Program.name)
            .offset(offset)
            .limit(limit)
        )
        program_ids = [row[0] for row in program_ids_query.all()]

        # Load full program objects with eager loading
        if program_ids:
            programs = (
                db.query(Program)
                .options(joinedload(Program.university))
                .filter(Program.id.in_(program_ids))
                .all()
            )
            # Re-sort by original order (university name, program name)
            programs_dict = {p.id: p for p in programs}
            programs = [programs_dict[pid] for pid in program_ids if pid in programs_dict]
        else:
            programs = []

        # Convert to flat format
        flat_programs = []
        for program in programs:
            flat = ProgramService._to_flat(db, program)
            flat_programs.append(flat)

        return flat_programs, total

    @staticmethod
    def get_all_programs_flat(db: Session, year: int | None = None) -> list[ProgramFlat]:
        """
        Get all programs in flattened format.
        Optimized for bulk loading (no pagination).
        """
        query = (
            db.query(Program)
            .join(University)
            .options(joinedload(Program.university))
        )

        if year:
            query = (
                query.join(ProgramYearlyStats)
                .filter(ProgramYearlyStats.year == year)
                .filter(ProgramYearlyStats.has_data == True)
            )

        programs = query.order_by(University.name, Program.name).all()

        # Batch load yearly stats for efficiency
        program_ids = [p.id for p in programs]
        yearly_stats = (
            db.query(ProgramYearlyStats)
            .filter(ProgramYearlyStats.program_id.in_(program_ids))
            .all()
        )

        # Group stats by program_id
        stats_by_program: dict[int, list[ProgramYearlyStats]] = {}
        for stat in yearly_stats:
            if stat.program_id not in stats_by_program:
                stats_by_program[stat.program_id] = []
            stats_by_program[stat.program_id].append(stat)

        # Convert to flat format
        flat_programs = []
        for program in programs:
            stats = stats_by_program.get(program.id, [])
            flat = ProgramService._program_to_flat(program, stats)
            flat_programs.append(flat)

        return flat_programs

    @staticmethod
    def _to_flat(db: Session, program: Program) -> ProgramFlat:
        """Convert a program to flat format with yearly stats."""
        # Load yearly stats
        stats = (
            db.query(ProgramYearlyStats)
            .filter(ProgramYearlyStats.program_id == program.id)
            .all()
        )
        return ProgramService._program_to_flat(program, stats)

    @staticmethod
    def _program_to_flat(program: Program, stats: list[ProgramYearlyStats]) -> ProgramFlat:
        """Convert program and stats to flat format."""
        flat_data = {
            "yop_kodu": program.yop_kodu,
            "university": program.university.name,
            "faculty": program.faculty,
            "program": program.name,
            "program_detail": program.detail,
            "city": program.university.city,
            "university_type": program.university.university_type,
            "scholarship": program.scholarship,
            "puan_type": program.puan_type,
        }

        # Add yearly stats
        for stat in stats:
            year = stat.year
            flat_data[f"kontenjan_{year}"] = stat.kontenjan
            flat_data[f"yerlesen_{year}"] = stat.yerlesen
            flat_data[f"has_{year}"] = stat.has_data

            # Parse score strings to floats
            flat_data[f"taban_{year}"] = ProgramService._parse_score(stat.taban_puan)
            flat_data[f"tavan_{year}"] = ProgramService._parse_score(stat.tavan_puan)

            # Parse ranking strings to ints
            flat_data[f"tavan_bs_{year}"] = ProgramService._parse_ranking(
                stat.tavan_basari_sirasi
            )
            flat_data[f"tbs_{year}"] = stat.taban_basari_sirasi  # Already parsed as int

            # Handle "Dolmadı" case: if taban is null but tavan exists, use tavan
            if flat_data[f"taban_{year}"] is None and flat_data[f"tavan_{year}"] is not None:
                flat_data[f"taban_{year}"] = flat_data[f"tavan_{year}"]

            if flat_data[f"tbs_{year}"] is None and flat_data[f"tavan_bs_{year}"] is not None:
                flat_data[f"tbs_{year}"] = flat_data[f"tavan_bs_{year}"]

        return ProgramFlat(**flat_data)

    @staticmethod
    def _parse_score(score_str: str | None) -> float | None:
        """Parse Turkish score format (comma as decimal) to float."""
        if not score_str or score_str in ("", "Dolmadı", "0"):
            return None
        try:
            # Remove quotes and convert comma to dot for decimal
            cleaned = str(score_str).replace('"', "").replace(",", ".")
            return float(cleaned)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_ranking(ranking_str: str | None) -> int | None:
        """Parse Turkish ranking format (dot as thousands separator) to int."""
        if not ranking_str or ranking_str in ("", "Dolmadı", "0", "---", "-"):
            return None
        try:
            # Remove dots (thousands separator)
            cleaned = str(ranking_str).replace(".", "")
            return int(float(cleaned))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def get_program_by_yop_kodu(db: Session, yop_kodu: str) -> Optional[Program]:
        """Get a program by YOP code."""
        return (
            db.query(Program)
            .options(joinedload(Program.university))
            .filter(Program.yop_kodu == yop_kodu)
            .first()
        )

    @staticmethod
    def get_programs_by_university(
        db: Session, university_id: int, year: int | None = None
    ) -> list[ProgramFlat]:
        """Get all programs for a specific university."""
        query = (
            db.query(Program)
            .options(joinedload(Program.university))
            .filter(Program.university_id == university_id)
        )

        if year:
            query = (
                query.join(ProgramYearlyStats)
                .filter(ProgramYearlyStats.year == year)
                .filter(ProgramYearlyStats.has_data == True)
            )

        programs = query.order_by(Program.name).all()

        # Convert to flat format
        flat_programs = []
        for program in programs:
            flat = ProgramService._to_flat(db, program)
            flat_programs.append(flat)

        return flat_programs

    @staticmethod
    def get_all_programs_as_dicts(db: Session) -> list[dict]:
        """
        Get all programs as dictionaries.
        This method is for backward compatibility with code that expects
        the old CSV structure with string values.
        """
        flat_programs = ProgramService.get_all_programs_flat(db)
        return [p.model_dump() for p in flat_programs]
