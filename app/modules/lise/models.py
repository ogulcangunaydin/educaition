"""Database models for high school (lise) placement data."""

from sqlalchemy import Column, Float, Integer, String, Boolean, UniqueConstraint

from app.core.database import Base


class Lise(Base):
    """High school (lise) master data."""
    __tablename__ = "lises"
    __table_args__ = (
        UniqueConstraint("lise_id", "year_group", name="uq_lise_id_year_group"),
    )

    id = Column(Integer, primary_key=True, index=True)
    lise_id = Column(Integer, index=True, nullable=False)
    lise_adi = Column(String, nullable=False)
    sehir = Column(String)
    year_group = Column(String, nullable=False)  # "2022-2024" or "2025"


class LisePlacement(Base):
    """High school placement data per university program."""
    __tablename__ = "lise_placements"

    id = Column(Integer, primary_key=True, index=True)
    university_slug = Column(String, index=True, nullable=False)  # e.g. "istanbul_universitesi"
    yop_kodu = Column(String, index=True, nullable=False)
    year = Column(Integer, index=True, nullable=False)
    lise_id = Column(Integer, index=True, nullable=False)
    yerlesen_sayisi = Column(Integer, nullable=False)
    school_type = Column(Integer)  # Encoded school type


class LisePlacement2025(Base):
    """High school placement data for 2025 (different structure with detailed fields)."""
    __tablename__ = "lise_placements_2025"

    id = Column(Integer, primary_key=True, index=True)
    source_university = Column(String, index=True, nullable=False)  # fsm, halic, ibnhaldun, izu, mayis
    yop_kodu = Column(String, index=True, nullable=False)
    year = Column(Integer, default=2025)
    lise_adi = Column(String, nullable=False)
    sehir = Column(String)
    ilce = Column(String)
    yerlesen_sayisi = Column(Integer, nullable=False)
    is_ozel = Column(Boolean, default=False)
    is_fen = Column(Boolean, default=False)
    is_anadolu = Column(Boolean, default=False)
    is_acik_ogretim = Column(Boolean, default=False)


class ScoreRankingDistribution(Base):
    """Score to ranking distribution data."""
    __tablename__ = "score_ranking_distributions"

    id = Column(Integer, primary_key=True, index=True)
    puan_turu = Column(String, index=True, nullable=False)  # SAY, SOZ, EA, DİL
    puan = Column(Float, nullable=False)
    siralama = Column(Integer, nullable=False)
