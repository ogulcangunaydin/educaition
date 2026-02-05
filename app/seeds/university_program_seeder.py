"""
Seeder for University and Program data from CSV files.

Reads the master CSV files and populates:
- universities table
- programs table  
- program_yearly_stats table

Source:
- programs/2022-2024/programs_master.csv (2022, 2023, 2024 data)
- programs/2025/programs_master.csv (2025 data)
"""

import csv
import logging
import os
from sqlalchemy.orm import Session

from app.modules.universities.models import University, Program, ProgramYearlyStats

logger = logging.getLogger(__name__)


class UniversityProgramSeeder:
    """Seeds university and program data from CSV files."""

    # Path to the backend data files (source of truth for seeding)
    DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
    DATA_DIR_2022_2024 = os.path.join(DATA_DIR, "programs", "2022-2024")
    DATA_DIR_2025 = os.path.join(DATA_DIR, "programs", "2025")

    def __init__(self, db: Session):
        self.db = db
        self.universities_cache: dict[str, University] = {}
        self.programs_cache: dict[str, Program] = {}

    def run(self):
        """Main entry point for seeding."""
        logger.info("Starting University/Program seeding...")

        # Seed 2025 data first (most current)
        self.seed_from_2025_csv()

        # Then add historical data from 2024 (years 2022, 2023, 2024)
        self.seed_from_2024_csv()

        logger.info(
            f"Seeding complete! Universities: {len(self.universities_cache)}, "
            f"Programs: {len(self.programs_cache)}"
        )

    def seed_from_2025_csv(self):
        """Seed from the 2025 data file."""
        csv_path = os.path.join(self.DATA_DIR_2025, "programs_master.csv")

        if not os.path.exists(csv_path):
            logger.warning(f"2025 CSV not found: {csv_path}")
            return

        logger.info(f"Reading 2025 data from: {csv_path}")
        row_count = 0

        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_count += 1
                self._process_row(row, year=2025)

                if row_count % 1000 == 0:
                    logger.info(f"Processed {row_count} rows...")
                    self.db.flush()

        self.db.commit()
        logger.info(f"2025 data: processed {row_count} rows")

    def seed_from_2024_csv(self):
        """Seed historical data from 2022-2024 file (contains 2022, 2023, 2024 data)."""
        csv_path = os.path.join(self.DATA_DIR_2022_2024, "programs_master.csv")

        if not os.path.exists(csv_path):
            logger.warning(f"2024 CSV not found: {csv_path}")
            return

        logger.info(f"Reading 2024 data from: {csv_path}")
        row_count = 0
        stats_added = 0

        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_count += 1

                # Get or create the program (it might already exist from 2025 data)
                program = self._get_or_create_program(row)

                # Add yearly stats for 2022, 2023, 2024
                for year in [2022, 2023, 2024]:
                    if self._add_yearly_stats(program, row, year):
                        stats_added += 1

                if row_count % 1000 == 0:
                    logger.info(f"Processed {row_count} rows (historical)...")
                    self.db.flush()

        self.db.commit()
        logger.info(f"2024 data: processed {row_count} rows, added {stats_added} yearly stats")

    def _get_or_create_university(self, row: dict) -> University:
        """Get existing university or create new one."""
        name = row.get("university", "").strip()

        if name in self.universities_cache:
            return self.universities_cache[name]

        # Check database
        university = self.db.query(University).filter(University.name == name).first()

        if not university:
            university = University(
                name=name,
                city=row.get("city", "").strip(),
                university_type=row.get("university_type", "").strip(),
            )
            self.db.add(university)
            self.db.flush()  # Get the ID

        self.universities_cache[name] = university
        return university

    def _get_or_create_program(self, row: dict) -> Program:
        """Get existing program or create new one."""
        yop_kodu = row.get("yop_kodu", "").strip()

        if yop_kodu in self.programs_cache:
            return self.programs_cache[yop_kodu]

        # Check database
        program = self.db.query(Program).filter(Program.yop_kodu == yop_kodu).first()

        if not program:
            university = self._get_or_create_university(row)
            program = Program(
                yop_kodu=yop_kodu,
                university_id=university.id,
                faculty=row.get("faculty", "").strip(),
                name=row.get("program", "").strip(),
                detail=row.get("program_detail", "").strip() or None,
                scholarship=row.get("scholarship", "").strip() or None,
                puan_type=row.get("puan_type", "").strip().lower(),
            )
            self.db.add(program)
            self.db.flush()  # Get the ID

        self.programs_cache[yop_kodu] = program
        return program

    def _process_row(self, row: dict, year: int):
        """Process a single row and create program + yearly stats."""
        program = self._get_or_create_program(row)
        self._add_yearly_stats(program, row, year)

    def _add_yearly_stats(self, program: Program, row: dict, year: int) -> bool:
        """Add yearly stats for a program. Returns True if stats were added."""
        # Check if stats already exist
        existing = (
            self.db.query(ProgramYearlyStats)
            .filter(
                ProgramYearlyStats.program_id == program.id,
                ProgramYearlyStats.year == year,
            )
            .first()
        )
        if existing:
            return False

        # Get year-specific column names
        suffix = f"_{year}"

        # Check if this year has data in the row
        has_data_key = f"has{suffix}"
        has_data_value = row.get(has_data_key, "").lower()
        
        # For 2025 data, columns are like kontenjan_2025
        kontenjan_key = f"kontenjan{suffix}"
        taban_key = f"taban{suffix}"
        tavan_key = f"tavan{suffix}"
        tavan_bs_key = f"tavan_bs{suffix}"
        tbs_key = f"tbs{suffix}"
        yerlesen_key = f"yerlesen{suffix}"

        # Skip if no data for this year
        kontenjan_val = row.get(kontenjan_key, "")
        if not kontenjan_val and has_data_value != "true":
            return False

        # Parse TBS (taban başarı sırası) - it uses dot as thousands separator
        tbs_str = row.get(tbs_key, "")
        tbs_parsed = self._parse_ranking(tbs_str)

        stats = ProgramYearlyStats(
            program_id=program.id,
            year=year,
            kontenjan=self._parse_int(kontenjan_val),
            yerlesen=self._parse_int(row.get(yerlesen_key, "")),
            taban_puan=row.get(taban_key, "") or None,
            tavan_puan=row.get(tavan_key, "") or None,
            tavan_basari_sirasi=row.get(tavan_bs_key, "") or None,
            taban_basari_sirasi=tbs_parsed,
            has_data=has_data_value == "true" if has_data_value else True,
        )
        self.db.add(stats)
        return True

    def _parse_int(self, value: str) -> int | None:
        """Parse integer, handling empty strings and dots as thousands separators."""
        if not value:
            return None
        try:
            # Remove dots (thousands separator) and parse
            cleaned = str(value).replace(".", "").strip()
            return int(float(cleaned)) if cleaned else None
        except (ValueError, TypeError):
            return None

    def _parse_ranking(self, value: str) -> int | None:
        """Parse ranking value (uses dot as thousands separator)."""
        if not value or value.lower() in ("dolmadı", "---", "-"):
            return None
        try:
            # Remove dots (thousands separator) and parse
            cleaned = str(value).replace(".", "").strip()
            return int(float(cleaned)) if cleaned else None
        except (ValueError, TypeError):
            return None
