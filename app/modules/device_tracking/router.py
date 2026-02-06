from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import get_db

from .schemas import (
    DeviceCompletionCheck,
    DeviceCompletionMark,
    DeviceCompletionResponse,
    DeviceCompletionRecord,
)
from .service import DeviceTrackingService


router = APIRouter(
    prefix="/device-tracking",
    tags=["device_tracking"],
)


@router.post("/check", response_model=DeviceCompletionResponse)
def check_device_completion(
    request: DeviceCompletionCheck,
    db: Session = Depends(get_db),
):
    """
    Check if a device has already completed a specific test.
    
    This is a public endpoint - no authentication required.
    Used by anonymous test takers to verify if they've already completed a test.
    """
    completion = DeviceTrackingService.has_completed_test(
        db,
        device_id=request.device_id,
        test_type=request.test_type,
        room_id=request.room_id,
    )
    
    return DeviceCompletionResponse(
        has_completed=completion is not None,
        completed_at=completion.completed_at if completion else None,
    )


@router.post("/mark", response_model=DeviceCompletionRecord)
def mark_device_completion(
    request: DeviceCompletionMark,
    db: Session = Depends(get_db),
):
    """
    Mark a device as having completed a test.
    
    This is a public endpoint - no authentication required.
    Should be called when an anonymous user completes a test.
    """
    completion = DeviceTrackingService.mark_test_completed(
        db,
        device_id=request.device_id,
        test_type=request.test_type,
        room_id=request.room_id,
    )
    
    return DeviceCompletionRecord.model_validate(completion)


@router.get("/device/{device_id}", response_model=list[DeviceCompletionRecord])
def get_device_completions(
    device_id: str,
    db: Session = Depends(get_db),
):
    """
    Get all test completions for a specific device.
    
    This is a public endpoint - useful for debugging and verifying completion status.
    """
    completions = DeviceTrackingService.get_device_completions(db, device_id)
    return [DeviceCompletionRecord.model_validate(c) for c in completions]
