# Universities module

from app.modules.universities.models import Program, ProgramYearlyStats, University
from app.modules.universities.router import programs_router, router
from app.modules.universities.service import ProgramService, UniversityService

__all__ = [
    "University",
    "Program",
    "ProgramYearlyStats",
    "router",
    "programs_router",
    "UniversityService",
    "ProgramService",
]
