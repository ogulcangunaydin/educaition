"""
Seeder for reference data tables (RIASEC job scores, score distributions).
This data is static and should be seeded once per environment.
"""
import csv
import json
import logging
import os

from sqlalchemy.orm import Session

from app.models import RiasecJobScore, ScoreDistribution

logger = logging.getLogger(__name__)


class ReferenceDataSeeder:
    """Seeder for RIASEC job scores and score distribution data."""

    def __init__(self, db: Session):
        self.db = db
        self.data_dir = os.path.join(os.path.dirname(__file__), "..", "data")

    def run(self):
        """Run all reference data seeders."""
        self.seed_riasec_job_scores()
        self.seed_score_distributions()

    def seed_riasec_job_scores(self):
        """Seed RIASEC job scores from CSV file."""
        csv_path = os.path.join(self.data_dir, "riasec_score_to_job.csv")

        # Check if already seeded
        existing_count = self.db.query(RiasecJobScore).count()
        if existing_count > 0:
            logger.info(
                f"RIASEC job scores already seeded ({existing_count} records), skipping"
            )
            return

        if not os.path.exists(csv_path):
            logger.warning(f"RIASEC CSV file not found: {csv_path}")
            return

        # Parse CSV and group by job title
        jobs: dict[str, dict[str, float]] = {}

        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                title = row["Title"]
                element = row["Element Name"]
                value = float(row["Data Value"])

                if title not in jobs:
                    jobs[title] = {
                        "realistic": 0,
                        "investigative": 0,
                        "artistic": 0,
                        "social": 0,
                        "enterprising": 0,
                        "conventional": 0,
                    }

                # Map element name to column
                element_map = {
                    "Realistic": "realistic",
                    "Investigative": "investigative",
                    "Artistic": "artistic",
                    "Social": "social",
                    "Enterprising": "enterprising",
                    "Conventional": "conventional",
                }
                column = element_map.get(element)
                if column:
                    jobs[title][column] = value

        # Insert into database
        records = []
        for job_title, scores in jobs.items():
            records.append(
                RiasecJobScore(
                    job_title=job_title,
                    realistic=scores["realistic"],
                    investigative=scores["investigative"],
                    artistic=scores["artistic"],
                    social=scores["social"],
                    enterprising=scores["enterprising"],
                    conventional=scores["conventional"],
                )
            )

        self.db.bulk_save_objects(records)
        self.db.commit()

        logger.info(f"Seeded {len(records)} RIASEC job scores")

    def seed_score_distributions(self):
        """Seed score distribution data from JSON file."""
        json_path = os.path.join(self.data_dir, "score_ranking_distribution.json")

        # Check if already seeded
        existing_count = self.db.query(ScoreDistribution).count()
        if existing_count > 0:
            logger.info(
                f"Score distributions already seeded ({existing_count} records), skipping"
            )
            return

        if not os.path.exists(json_path):
            logger.warning(f"Score distribution JSON file not found: {json_path}")
            return

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        records = []
        for puan_type, type_data in data.items():
            records.append(
                ScoreDistribution(
                    puan_type=puan_type,
                    min_score=type_data["minScore"],
                    max_score=type_data["maxScore"],
                    distribution=type_data["distribution"],
                )
            )

        self.db.bulk_save_objects(records)
        self.db.commit()

        logger.info(f"Seeded {len(records)} score distributions")
