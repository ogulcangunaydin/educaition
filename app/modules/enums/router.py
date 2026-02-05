"""
API router for enum values.

Provides endpoints for frontend to fetch controlled values
instead of hardcoding them.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.enums import get_all_enums

router = APIRouter(prefix="/enums", tags=["enums"])


@router.get("")
@router.get("/")
async def get_enums():
    """
    Get all enum values for frontend dropdowns.

    Returns a dictionary with all controlled values organized by category.
    This endpoint is public and doesn't require authentication.
    """
    return JSONResponse(content=get_all_enums())


@router.get("/{enum_name}")
async def get_enum_by_name(enum_name: str):
    """
    Get a specific enum by name.

    Args:
        enum_name: The name of the enum to retrieve (e.g., 'genders', 'classYears')

    Returns:
        List of {value, label} options for the specified enum
    """
    all_enums = get_all_enums()

    if enum_name not in all_enums:
        return JSONResponse(
            status_code=404,
            content={"detail": f"Enum '{enum_name}' not found. Available: {list(all_enums.keys())}"},
        )

    return JSONResponse(content=all_enums[enum_name])
