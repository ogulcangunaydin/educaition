"""
Users module - User management.

This module handles:
- User CRUD operations
- User role and university management
"""

from .router import router as users_router
from .schemas import User, UserCreate, UserRoleEnum, UserUpdate, UniversityKeyEnum
from .service import UserService

__all__ = [
    "users_router",
    "UserService",
    "User",
    "UserCreate",
    "UserUpdate",
    "UserRoleEnum",
    "UniversityKeyEnum",
]
