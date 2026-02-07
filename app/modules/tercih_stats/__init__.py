"""
Tercih statistics module.
"""

from app.modules.tercih_stats.models import (
    ProgramPrice,
    TercihIstatistikleri,
    TercihPreference,
    TercihStats,
)
from app.modules.tercih_stats.router import router as tercih_stats_router
from app.modules.tercih_stats.schemas import (
    ProgramPriceListResponse,
    ProgramPriceResponse,
    TercihDetailedStatsResponse,
    TercihPreferenceListResponse,
    TercihPreferenceResponse,
    TercihStatsListResponse,
    TercihStatsResponse,
)
from app.modules.tercih_stats.service import TercihStatsService

__all__ = [
    # Models
    "ProgramPrice",
    "TercihIstatistikleri",
    "TercihPreference",
    "TercihStats",
    # Router
    "tercih_stats_router",
    # Service
    "TercihStatsService",
    # Schemas
    "ProgramPriceListResponse",
    "ProgramPriceResponse",
    "TercihDetailedStatsResponse",
    "TercihPreferenceListResponse",
    "TercihPreferenceResponse",
    "TercihStatsListResponse",
    "TercihStatsResponse",
]
