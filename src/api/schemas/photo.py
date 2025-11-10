"""Photo-related Pydantic schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class PhotoTypeEnum(str, Enum):
    """Types of photos for fitting."""
    FRONT = "front"
    SIDE = "side"
    BACK = "back"
    CUSTOM = "custom"


class PhotoMetadata(BaseModel):
    """Metadata for uploaded photo."""
    photo_type: PhotoTypeEnum = Field(..., description="Type of photo view")
    camera_height_cm: Optional[float] = Field(None, description="Camera height from ground")
    distance_cm: Optional[float] = Field(None, description="Distance from subject")
    notes: Optional[str] = Field(None, max_length=500)


class PhotoUpload(BaseModel):
    """Schema for photo upload metadata (file sent separately)."""
    metadata: PhotoMetadata

    class Config:
        json_schema_extra = {
            "example": {
                "metadata": {
                    "photo_type": "front",
                    "camera_height_cm": 150.0,
                    "distance_cm": 300.0,
                    "notes": "Good lighting conditions"
                }
            }
        }


class PhotoResponse(BaseModel):
    """Schema for photo response."""
    id: str = Field(..., description="Unique photo identifier")
    subject_id: str
    filename: str
    photo_type: PhotoTypeEnum
    file_size_bytes: int
    width_px: int
    height_px: int
    camera_height_cm: Optional[float] = None
    distance_cm: Optional[float] = None
    notes: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "photo_xyz789",
                "subject_id": "subj_abc123",
                "filename": "front_view.jpg",
                "photo_type": "front",
                "file_size_bytes": 1048576,
                "width_px": 1920,
                "height_px": 1080,
                "camera_height_cm": 150.0,
                "distance_cm": 300.0,
                "notes": "Good lighting",
                "uploaded_at": "2025-11-10T10:05:00"
            }
        }
