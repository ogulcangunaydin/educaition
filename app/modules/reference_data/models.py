from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


class RiasecJobScore(Base):
    """
    RIASEC scores for different job titles.
    Used to match student RIASEC profiles to suitable careers.
    Data sourced from O*NET (Occupational Information Network).
    """

    __tablename__ = "riasec_job_scores"

    id = Column(Integer, primary_key=True, index=True)
    job_title = Column(String(255), unique=True, nullable=False, index=True)
    realistic = Column(Float, nullable=False, default=0)
    investigative = Column(Float, nullable=False, default=0)
    artistic = Column(Float, nullable=False, default=0)
    social = Column(Float, nullable=False, default=0)
    enterprising = Column(Float, nullable=False, default=0)
    conventional = Column(Float, nullable=False, default=0)

    def to_dict(self) -> dict:
        """Return RIASEC scores as dictionary with letter keys."""
        return {
            "R": self.realistic,
            "I": self.investigative,
            "A": self.artistic,
            "S": self.social,
            "E": self.enterprising,
            "C": self.conventional,
        }


class ScoreDistribution(Base):
    """
    Score to ranking distribution data for different exam types.
    Used to estimate ranking based on expected score.
    """

    __tablename__ = "score_distributions"

    id = Column(Integer, primary_key=True, index=True)
    puan_type = Column(String(20), unique=True, nullable=False, index=True)
    min_score = Column(Integer, nullable=False)
    max_score = Column(Integer, nullable=False)
    distribution = Column(JSONB, nullable=False)
