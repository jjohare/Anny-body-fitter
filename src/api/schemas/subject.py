"""Subject-related Pydantic schemas."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class GenderEnum(str, Enum):
    """Gender options for subject."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class SubjectCreate(BaseModel):
    """Schema for creating a new subject."""
    name: str = Field(..., min_length=1, max_length=100, description="Subject name")
    age: Optional[int] = Field(None, ge=0, le=120, description="Subject age in years")
    gender: Optional[GenderEnum] = Field(None, description="Subject gender")
    height_cm: Optional[float] = Field(None, ge=30, le=250, description="Height in centimeters")
    weight_kg: Optional[float] = Field(None, ge=2, le=300, description="Weight in kilograms")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Subject_001",
                "age": 25,
                "gender": "male",
                "height_cm": 175.0,
                "weight_kg": 70.0,
                "notes": "Athletic build"
            }
        }


class SubjectUpdate(BaseModel):
    """Schema for updating subject information."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=120)
    gender: Optional[GenderEnum] = None
    height_cm: Optional[float] = Field(None, ge=30, le=250)
    weight_kg: Optional[float] = Field(None, ge=2, le=300)
    notes: Optional[str] = Field(None, max_length=1000)


class SubjectResponse(BaseModel):
    """Schema for subject response."""
    id: str = Field(..., description="Unique subject identifier")
    name: str
    age: Optional[int] = None
    gender: Optional[GenderEnum] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    notes: Optional[str] = None
    photo_count: int = Field(0, description="Number of uploaded photos")
    has_fitted_model: bool = Field(False, description="Whether model has been fitted")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "subj_abc123xyz",
                "name": "Subject_001",
                "age": 25,
                "gender": "male",
                "height_cm": 175.0,
                "weight_kg": 70.0,
                "notes": "Athletic build",
                "photo_count": 4,
                "has_fitted_model": True,
                "created_at": "2025-11-10T10:00:00",
                "updated_at": "2025-11-10T10:30:00"
            }
        }


class SubjectList(BaseModel):
    """Schema for paginated subject list."""
    subjects: List[SubjectResponse]
    total: int = Field(..., description="Total number of subjects")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")

    class Config:
        json_schema_extra = {
            "example": {
                "subjects": [],
                "total": 42,
                "page": 1,
                "page_size": 20
            }
        }
