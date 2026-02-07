"""
Service layer for tercih statistics.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.modules.tercih_stats.models import (
    ProgramPrice,
    TercihIstatistikleri,
    TercihPreference,
    TercihStats,
)


class TercihStatsService:
    """Service for tercih statistics operations."""

    def __init__(self, db: Session):
        self.db = db

    # Program Prices
    def get_prices_by_yop_kodu(self, yop_kodu: str) -> List[ProgramPrice]:
        """Get all price records for a program."""
        return self.db.query(ProgramPrice).filter(
            ProgramPrice.yop_kodu == yop_kodu
        ).all()

    def get_all_prices(self, skip: int = 0, limit: int = 1000) -> List[ProgramPrice]:
        """Get all program prices with pagination."""
        return self.db.query(ProgramPrice).offset(skip).limit(limit).all()

    def get_prices_count(self) -> int:
        """Get total count of program prices."""
        return self.db.query(ProgramPrice).count()

    # Tercih Stats
    def get_stats_by_yop_kodu(
        self, yop_kodu: str, year: Optional[int] = None
    ) -> List[TercihStats]:
        """Get tercih stats for a program, optionally filtered by year."""
        query = self.db.query(TercihStats).filter(TercihStats.yop_kodu == yop_kodu)
        if year:
            query = query.filter(TercihStats.year == year)
        return query.all()

    def get_stats_by_year(self, year: int) -> List[TercihStats]:
        """Get all tercih stats for a specific year."""
        return self.db.query(TercihStats).filter(TercihStats.year == year).all()

    def get_all_stats(self, skip: int = 0, limit: int = 1000) -> List[TercihStats]:
        """Get all tercih stats with pagination."""
        return self.db.query(TercihStats).offset(skip).limit(limit).all()

    def get_stats_count(self) -> int:
        """Get total count of tercih stats."""
        return self.db.query(TercihStats).count()

    # Tercih Detailed Stats
    def get_detailed_stats_by_yop_kodu(self, yop_kodu: str) -> Optional[TercihIstatistikleri]:
        """Get detailed stats for a program."""
        return self.db.query(TercihIstatistikleri).filter(
            TercihIstatistikleri.yop_kodu == yop_kodu
        ).first()

    def get_all_detailed_stats(
        self, skip: int = 0, limit: int = 1000
    ) -> List[TercihIstatistikleri]:
        """Get all detailed stats with pagination."""
        return self.db.query(TercihIstatistikleri).offset(skip).limit(limit).all()

    def get_detailed_stats_count(self) -> int:
        """Get total count of detailed stats."""
        return self.db.query(TercihIstatistikleri).count()

    # Tercih Preferences
    def get_preferences_by_yop_kodu(
        self,
        yop_kodu: str,
        source_university: Optional[str] = None,
        preference_type: Optional[str] = None,
        year: Optional[int] = None,
    ) -> List[TercihPreference]:
        """Get tercih preferences for a program with optional filters."""
        query = self.db.query(TercihPreference).filter(
            TercihPreference.yop_kodu == yop_kodu
        )
        if source_university:
            query = query.filter(TercihPreference.source_university == source_university)
        if preference_type:
            query = query.filter(TercihPreference.preference_type == preference_type)
        if year:
            query = query.filter(TercihPreference.year == year)
        return query.all()

    def get_preferences_by_source(
        self,
        source_university: str,
        preference_type: Optional[str] = None,
        year: Optional[int] = None,
    ) -> List[TercihPreference]:
        """Get all tercih preferences for a source university."""
        query = self.db.query(TercihPreference).filter(
            TercihPreference.source_university == source_university
        )
        if preference_type:
            query = query.filter(TercihPreference.preference_type == preference_type)
        if year:
            query = query.filter(TercihPreference.year == year)
        return query.all()

    def get_all_preferences(
        self, skip: int = 0, limit: int = 1000
    ) -> List[TercihPreference]:
        """Get all preferences with pagination."""
        return self.db.query(TercihPreference).offset(skip).limit(limit).all()

    def get_preferences_count(self) -> int:
        """Get total count of preferences."""
        return self.db.query(TercihPreference).count()

    def get_source_universities(self) -> List[str]:
        """Get list of all source universities."""
        result = (
            self.db.query(TercihPreference.source_university)
            .distinct()
            .all()
        )
        return [r[0] for r in result]

    def get_available_years(self) -> List[int]:
        """Get list of available years."""
        result = (
            self.db.query(TercihStats.year)
            .distinct()
            .order_by(TercihStats.year)
            .all()
        )
        return [r[0] for r in result]

    # ===================== Batch queries =====================

    def get_stats_by_yop_kodlari(
        self, yop_kodlari: List[str], year: Optional[int] = None
    ) -> List[TercihStats]:
        """Get tercih stats for multiple programs at once."""
        query = self.db.query(TercihStats).filter(
            TercihStats.yop_kodu.in_(yop_kodlari)
        )
        if year:
            query = query.filter(TercihStats.year == year)
        return query.all()

    def get_prices_by_yop_kodlari(
        self, yop_kodlari: List[str]
    ) -> List[ProgramPrice]:
        """Get prices for multiple programs at once."""
        return self.db.query(ProgramPrice).filter(
            ProgramPrice.yop_kodu.in_(yop_kodlari)
        ).all()

    def get_detailed_stats_by_yop_kodlari(
        self, yop_kodlari: List[str]
    ) -> List[TercihIstatistikleri]:
        """Get detailed stats for multiple programs at once."""
        return self.db.query(TercihIstatistikleri).filter(
            TercihIstatistikleri.yop_kodu.in_(yop_kodlari)
        ).all()
