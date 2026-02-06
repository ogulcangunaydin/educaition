from datetime import datetime
from pydantic import BaseModel, Field


class DeviceCompletionCheck(BaseModel):
    """Request schema to check if a device has completed a test"""
    device_id: str = Field(..., min_length=16, max_length=64, description="Device fingerprint hash")
    test_type: str = Field(..., min_length=1, max_length=50, description="Type of test")
    room_id: int | None = Field(None, description="Optional room/session ID")


class DeviceCompletionMark(BaseModel):
    """Request schema to mark a device as having completed a test"""
    device_id: str = Field(..., min_length=16, max_length=64, description="Device fingerprint hash")
    test_type: str = Field(..., min_length=1, max_length=50, description="Type of test")
    room_id: int | None = Field(None, description="Optional room/session ID")


class DeviceCompletionResponse(BaseModel):
    """Response schema for device completion status"""
    has_completed: bool
    completed_at: datetime | None = None


class DeviceCompletionRecord(BaseModel):
    """Full record of a device completion"""
    id: int
    device_id: str
    test_type: str
    room_id: int | None
    completed_at: datetime

    class Config:
        from_attributes = True
