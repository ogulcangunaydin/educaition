"""
Models for program prices and tercih (preference) statistics.
"""

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class ProgramPrice(Base):
    """Program pricing information by year."""

    __tablename__ = "program_prices"

    id = Column(Integer, primary_key=True, index=True)
    yop_kodu = Column(String(20), ForeignKey("programs.yop_kodu"), index=True)
    is_english = Column(Boolean, default=False)
    scholarship_pct = Column(Float)  # 0, 25, 50, 75, 100
    full_price_2024 = Column(Float, nullable=True)
    full_price_2025 = Column(Float, nullable=True)
    discounted_price_2024 = Column(Float, nullable=True)
    discounted_price_2025 = Column(Float, nullable=True)

    # Relationship
    program = relationship("Program", back_populates="prices")


class TercihStats(Base):
    """Combined tercih statistics per program and year."""

    __tablename__ = "tercih_stats"

    id = Column(Integer, primary_key=True, index=True)
    yop_kodu = Column(String(20), ForeignKey("programs.yop_kodu"), index=True)
    year = Column(Integer, index=True)
    
    # From tercih/2022-2024/combined_stats.csv
    ortalama_tercih_edilme_sirasi = Column(Float, nullable=True)  # Average preference order (A)
    ortalama_yerlesen_tercih_sirasi = Column(Float, nullable=True)  # Average placed preference order (B)
    marka_etkinlik_degeri = Column(Float, nullable=True)  # Brand effectiveness (A/B)

    # Relationship
    program = relationship("Program", back_populates="tercih_stats")


class TercihIstatistikleri(Base):
    """Detailed tercih statistics per program (yearly columns)."""

    __tablename__ = "tercih_istatistikleri"

    id = Column(Integer, primary_key=True, index=True)
    yop_kodu = Column(String(20), ForeignKey("programs.yop_kodu"), index=True, unique=True)
    
    # Per-year statistics
    bir_kontenjana_talip_olan_aday_sayisi_2022 = Column(Float, nullable=True)
    bir_kontenjana_talip_olan_aday_sayisi_2023 = Column(Float, nullable=True)
    bir_kontenjana_talip_olan_aday_sayisi_2024 = Column(Float, nullable=True)
    bir_kontenjana_talip_olan_aday_sayisi_2025 = Column(Float, nullable=True)
    
    ilk_uc_sirada_tercih_eden_sayisi_2022 = Column(Float, nullable=True)
    ilk_uc_sirada_tercih_eden_sayisi_2023 = Column(Float, nullable=True)
    ilk_uc_sirada_tercih_eden_sayisi_2024 = Column(Float, nullable=True)
    ilk_uc_sirada_tercih_eden_sayisi_2025 = Column(Float, nullable=True)
    
    ilk_uc_sirada_tercih_eden_orani_2022 = Column(Float, nullable=True)
    ilk_uc_sirada_tercih_eden_orani_2023 = Column(Float, nullable=True)
    ilk_uc_sirada_tercih_eden_orani_2024 = Column(Float, nullable=True)
    ilk_uc_sirada_tercih_eden_orani_2025 = Column(Float, nullable=True)
    
    ilk_uc_tercih_olarak_yerlesen_sayisi_2022 = Column(Float, nullable=True)
    ilk_uc_tercih_olarak_yerlesen_sayisi_2023 = Column(Float, nullable=True)
    ilk_uc_tercih_olarak_yerlesen_sayisi_2024 = Column(Float, nullable=True)
    ilk_uc_tercih_olarak_yerlesen_sayisi_2025 = Column(Float, nullable=True)
    
    ilk_uc_tercih_olarak_yerlesen_orani_2022 = Column(Float, nullable=True)
    ilk_uc_tercih_olarak_yerlesen_orani_2023 = Column(Float, nullable=True)
    ilk_uc_tercih_olarak_yerlesen_orani_2024 = Column(Float, nullable=True)
    ilk_uc_tercih_olarak_yerlesen_orani_2025 = Column(Float, nullable=True)

    # Relationship
    program = relationship("Program", back_populates="tercih_istatistikleri")


class TercihPreference(Base):
    """
    University-specific tercih preferences.
    Stores where students who chose a specific program also applied.
    """

    __tablename__ = "tercih_preferences"

    id = Column(Integer, primary_key=True, index=True)
    source_university = Column(String(100), index=True)  # e.g., "halic", "fsm"
    yop_kodu = Column(String(20), ForeignKey("programs.yop_kodu"), index=True)
    year = Column(Integer, index=True)
    preference_type = Column(String(20), index=True)  # "city", "university", "program"
    
    # The preferred item (city name, university name, or program name)
    preferred_item = Column(String(255))
    tercih_sayisi = Column(Integer)  # Number of students who made this preference
    
    # Additional info for university preferences
    university_type = Column(String(50), nullable=True)  # "devlet" or "vakif"

    # Relationship
    program = relationship("Program", back_populates="tercih_preferences")
