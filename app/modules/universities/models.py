"""
University and Program models for storing YÖK (ÖSYM) data.

Schema Design:
- University: Core university data (name, city, type)
- Program: Program definitions linked to university
- ProgramYearlyStats: Yearly statistics (scores, quotas, placements)

This normalized structure:
1. Eliminates data duplication across years
2. Makes querying efficient with proper indexes
3. Supports easy addition of new years
"""

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class University(Base):
    """
    University entity.
    
    Represents a unique university in Turkey.
    """
    __tablename__ = "universities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    city = Column(String(100), nullable=False, index=True)
    university_type = Column(String(50), nullable=False)  # 'Devlet' or 'Vakıf'
    
    # Relationships
    programs = relationship("Program", back_populates="university", lazy="dynamic")

    def __repr__(self):
        return f"<University {self.name}>"


class Program(Base):
    """
    Program entity.
    
    Represents a unique program at a university.
    The combination of yop_kodu is unique per program offering.
    """
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, index=True)
    yop_kodu = Column(String(20), nullable=False, unique=True, index=True)
    
    # Foreign keys
    university_id = Column(Integer, ForeignKey("universities.id"), nullable=False, index=True)
    
    # Program details
    faculty = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False, index=True)  # Program name
    detail = Column(String(255), nullable=True)  # e.g., "(İngilizce) (4 Yıllık)"
    scholarship = Column(String(100), nullable=True)  # e.g., "Burslu", "%50 İndirimli"
    puan_type = Column(String(10), nullable=False, index=True)  # 'say', 'ea', 'söz', 'dil'
    
    # Relationships
    university = relationship("University", back_populates="programs")
    yearly_stats = relationship("ProgramYearlyStats", back_populates="program", lazy="dynamic")

    # Composite index for common queries
    __table_args__ = (
        Index("ix_programs_university_puan", "university_id", "puan_type"),
    )

    def __repr__(self):
        return f"<Program {self.yop_kodu}: {self.name}>"


class ProgramYearlyStats(Base):
    """
    Yearly statistics for a program.
    
    Contains all score and placement data for a specific year.
    Separating this allows efficient storage of multi-year data.
    """
    __tablename__ = "program_yearly_stats"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    
    # Quota and placement
    kontenjan = Column(Integer, nullable=True)  # Quota
    yerlesen = Column(Integer, nullable=True)  # Number placed
    
    # Scores (stored as strings to preserve original format with decimals)
    taban_puan = Column(String(50), nullable=True)  # Minimum score
    tavan_puan = Column(String(50), nullable=True)  # Maximum score
    tavan_basari_sirasi = Column(String(50), nullable=True)  # Max success ranking
    
    # Ranking
    taban_basari_sirasi = Column(Integer, nullable=True)  # Minimum success ranking (TBS)
    
    # Flags
    has_data = Column(Boolean, default=True)  # Whether this year has valid data
    
    # Relationships
    program = relationship("Program", back_populates="yearly_stats")

    # Ensure one entry per program per year
    __table_args__ = (
        UniqueConstraint("program_id", "year", name="uq_program_year"),
        Index("ix_program_yearly_stats_year_tbs", "year", "taban_basari_sirasi"),
    )

    def __repr__(self):
        return f"<ProgramYearlyStats {self.program_id} - {self.year}>"

    @property
    def tbs_parsed(self) -> int | None:
        """Parse TBS to integer for sorting/filtering."""
        if self.taban_basari_sirasi:
            return self.taban_basari_sirasi
        return None
