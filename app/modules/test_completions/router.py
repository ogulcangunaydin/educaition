"""
Test Completions Router

Provides endpoints for checking whether a user has completed specific test types.
Used by the frontend TestPageGuard to enforce one-test-per-user rules.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user, get_db
from app.modules.users.models import User

from .service import TestCompletionService

router = APIRouter(
    prefix="/test-completions",
    tags=["test_completions"],
)


@router.get("/check")
def check_test_completion(
    test_type: str = Query(..., description="Test type to check"),
    room_id: int | None = Query(None, description="Optional room ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Check if the authenticated user has completed a specific test type.

    Returns whether the test has been completed, and optionally the
    participant ID and result summary.
    """
    result = TestCompletionService.check_completion(
        db,
        user_id=current_user.id,
        test_type=test_type,
        room_id=room_id,
    )
    return result
