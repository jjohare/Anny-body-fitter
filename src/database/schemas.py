"""
Pydantic schemas for data validation and serialization.
Provides request/response models for API endpoints.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict, field_validator


# Subject Schemas
class SubjectBase(BaseModel):
    """Base schema for Subject with common fields"""
    name: str = Field(..., min_length=1, max_length=255, description="Subject name (encrypted)")
    date_of_birth: datetime = Field(..., description="Date of birth (encrypted)")
    notes: Optional[str] = Field(None, description="Additional notes")


class SubjectCreate(SubjectBase):
    """Schema for creating a new subject"""
    pass


class SubjectUpdate(BaseModel):
    """Schema for updating a subject"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    date_of_birth: Optional[datetime] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class SubjectResponse(SubjectBase):
    """Schema for subject responses"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Measurement Schemas
class MeasurementBase(BaseModel):
    """Base schema for Measurement"""
    height: Optional[float] = Field(None, ge=0, description="Height in cm")
    weight: Optional[float] = Field(None, ge=0, description="Weight in kg")
    chest_circumference: Optional[float] = Field(None, ge=0, description="Chest circumference in cm")
    waist_circumference: Optional[float] = Field(None, ge=0, description="Waist circumference in cm")
    hip_circumference: Optional[float] = Field(None, ge=0, description="Hip circumference in cm")
    inseam: Optional[float] = Field(None, ge=0, description="Inseam in cm")
    shoulder_width: Optional[float] = Field(None, ge=0, description="Shoulder width in cm")
    arm_length: Optional[float] = Field(None, ge=0, description="Arm length in cm")
    leg_length: Optional[float] = Field(None, ge=0, description="Leg length in cm")
    neck_circumference: Optional[float] = Field(None, ge=0, description="Neck circumference in cm")
    custom_measurements: Optional[str] = Field(None, description="Custom measurements as JSON")
    measured_by: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class MeasurementCreate(MeasurementBase):
    """Schema for creating a new measurement"""
    subject_id: int = Field(..., gt=0)
    measurement_date: Optional[datetime] = None


class MeasurementResponse(MeasurementBase):
    """Schema for measurement responses"""
    id: int
    subject_id: int
    measurement_date: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ModelParameter Schemas
class ModelParameterBase(BaseModel):
    """Base schema for ModelParameter"""
    height_param: Optional[float] = None
    weight_param: Optional[float] = None
    chest_param: Optional[float] = None
    waist_param: Optional[float] = None
    hip_param: Optional[float] = None
    shape_param_1: Optional[float] = None
    shape_param_2: Optional[float] = None
    shape_param_3: Optional[float] = None
    shape_param_4: Optional[float] = None
    shape_param_5: Optional[float] = None
    additional_params: Optional[str] = Field(None, description="Additional parameters as JSON")
    model_version: Optional[str] = Field(None, max_length=50)
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    notes: Optional[str] = None


class ModelParameterCreate(ModelParameterBase):
    """Schema for creating model parameters"""
    subject_id: int = Field(..., gt=0)
    parameter_date: Optional[datetime] = None


class ModelParameterResponse(ModelParameterBase):
    """Schema for model parameter responses"""
    id: int
    subject_id: int
    parameter_date: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# PerformanceMetric Schemas
class PerformanceMetricBase(BaseModel):
    """Base schema for PerformanceMetric"""
    fitting_error: Optional[float] = Field(None, ge=0)
    landmark_accuracy: Optional[float] = Field(None, ge=0, le=1)
    mesh_quality: Optional[float] = Field(None, ge=0, le=1)
    processing_time: Optional[float] = Field(None, ge=0, description="Processing time in seconds")
    convergence_iterations: Optional[int] = Field(None, ge=0)
    height_error: Optional[float] = None
    volume_error: Optional[float] = None
    surface_area_error: Optional[float] = None
    custom_metrics: Optional[str] = Field(None, description="Custom metrics as JSON")
    metric_type: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class PerformanceMetricCreate(PerformanceMetricBase):
    """Schema for creating performance metrics"""
    subject_id: int = Field(..., gt=0)
    metric_date: Optional[datetime] = None


class PerformanceMetricResponse(PerformanceMetricBase):
    """Schema for performance metric responses"""
    id: int
    subject_id: int
    metric_date: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# PhotoRecord Schemas
class PhotoRecordBase(BaseModel):
    """Base schema for PhotoRecord"""
    filename: str = Field(..., min_length=1, max_length=255)
    file_path: str = Field(..., min_length=1, max_length=512)
    file_size: Optional[int] = Field(None, ge=0)
    mime_type: Optional[str] = Field(None, max_length=100)
    photo_type: Optional[str] = Field(None, max_length=50)
    resolution: Optional[str] = Field(None, max_length=50)
    file_hash: Optional[str] = Field(None, max_length=64)
    capture_date: Optional[datetime] = None
    notes: Optional[str] = None


class PhotoRecordCreate(PhotoRecordBase):
    """Schema for creating photo records"""
    subject_id: int = Field(..., gt=0)


class PhotoRecordResponse(PhotoRecordBase):
    """Schema for photo record responses"""
    id: int
    subject_id: int
    is_processed: bool
    processing_status: Optional[str]
    upload_date: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Session Schemas
class SessionBase(BaseModel):
    """Base schema for Session"""
    session_name: Optional[str] = Field(None, max_length=255)
    session_type: Optional[str] = Field(None, max_length=50)
    session_status: str = Field(default="in_progress", max_length=50)
    duration: Optional[int] = Field(None, ge=0, description="Duration in minutes")
    measurement_ids: Optional[str] = Field(None, description="Comma-separated measurement IDs")
    model_parameter_ids: Optional[str] = Field(None, description="Comma-separated model parameter IDs")
    photo_record_ids: Optional[str] = Field(None, description="Comma-separated photo record IDs")
    performance_metric_ids: Optional[str] = Field(None, description="Comma-separated performance metric IDs")
    outcome_summary: Optional[str] = None
    next_steps: Optional[str] = None
    notes: Optional[str] = None


class SessionCreate(SessionBase):
    """Schema for creating sessions"""
    subject_id: int = Field(..., gt=0)
    session_date: Optional[datetime] = None


class SessionUpdate(BaseModel):
    """Schema for updating sessions"""
    session_name: Optional[str] = Field(None, max_length=255)
    session_type: Optional[str] = Field(None, max_length=50)
    session_status: Optional[str] = Field(None, max_length=50)
    duration: Optional[int] = Field(None, ge=0)
    measurement_ids: Optional[str] = None
    model_parameter_ids: Optional[str] = None
    photo_record_ids: Optional[str] = None
    performance_metric_ids: Optional[str] = None
    outcome_summary: Optional[str] = None
    next_steps: Optional[str] = None
    notes: Optional[str] = None


class SessionResponse(SessionBase):
    """Schema for session responses"""
    id: int
    subject_id: int
    session_date: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
