"""Metrics-related Pydantic schemas."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class PerformanceMetrics(BaseModel):
    """Performance metrics for model fitting."""
    accuracy_score: Optional[float] = Field(None, ge=0, le=1, description="Model accuracy (0-1)")
    precision: Optional[float] = Field(None, ge=0, le=1, description="Precision metric")
    recall: Optional[float] = Field(None, ge=0, le=1, description="Recall metric")
    f1_score: Optional[float] = Field(None, ge=0, le=1, description="F1 score")
    mean_error_cm: Optional[float] = Field(None, ge=0, description="Mean error in centimeters")
    max_error_cm: Optional[float] = Field(None, ge=0, description="Maximum error in centimeters")

    class Config:
        json_schema_extra = {
            "example": {
                "accuracy_score": 0.95,
                "precision": 0.92,
                "recall": 0.93,
                "f1_score": 0.925,
                "mean_error_cm": 1.2,
                "max_error_cm": 4.5
            }
        }


class MetricsCreate(BaseModel):
    """Schema for creating performance metrics."""
    metrics: PerformanceMetrics
    ground_truth_available: bool = Field(..., description="Whether ground truth data was available")
    validation_method: str = Field(..., description="Method used for validation")
    notes: Optional[str] = Field(None, max_length=1000)
    custom_metrics: Optional[Dict[str, Any]] = Field(None, description="Additional custom metrics")

    class Config:
        json_schema_extra = {
            "example": {
                "metrics": {
                    "accuracy_score": 0.95,
                    "mean_error_cm": 1.2,
                    "max_error_cm": 4.5
                },
                "ground_truth_available": True,
                "validation_method": "3D scanner comparison",
                "notes": "High quality validation",
                "custom_metrics": {
                    "joint_error": 0.8,
                    "volume_difference": 2.3
                }
            }
        }


class MetricsResponse(BaseModel):
    """Schema for metrics response."""
    id: str = Field(..., description="Unique metrics identifier")
    subject_id: str
    metrics: PerformanceMetrics
    ground_truth_available: bool
    validation_method: str
    notes: Optional[str] = None
    custom_metrics: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "metrics_123abc",
                "subject_id": "subj_abc123",
                "metrics": {
                    "accuracy_score": 0.95,
                    "mean_error_cm": 1.2
                },
                "ground_truth_available": True,
                "validation_method": "3D scanner",
                "notes": "Validation complete",
                "custom_metrics": {"joint_error": 0.8},
                "created_at": "2025-11-10T10:20:00"
            }
        }
