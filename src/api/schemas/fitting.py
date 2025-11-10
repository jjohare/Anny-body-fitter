"""Fitting-related Pydantic schemas."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum


class FittingStatusEnum(str, Enum):
    """Status of fitting process."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FittingRequest(BaseModel):
    """Schema for triggering model fitting."""
    optimization_iterations: int = Field(100, ge=1, le=1000, description="Number of optimization iterations")
    use_shape_prior: bool = Field(True, description="Use shape prior regularization")
    use_pose_prior: bool = Field(True, description="Use pose prior regularization")
    lambda_shape: float = Field(0.01, gt=0, description="Shape regularization weight")
    lambda_pose: float = Field(0.01, gt=0, description="Pose regularization weight")

    class Config:
        json_schema_extra = {
            "example": {
                "optimization_iterations": 100,
                "use_shape_prior": True,
                "use_pose_prior": True,
                "lambda_shape": 0.01,
                "lambda_pose": 0.01
            }
        }


class ModelParameters(BaseModel):
    """Schema for 3D model parameters."""
    shape_params: List[float] = Field(..., description="Shape parameters (beta)")
    pose_params: List[float] = Field(..., description="Pose parameters (theta)")
    global_rotation: List[float] = Field(..., description="Global rotation (3 values)")
    global_translation: List[float] = Field(..., description="Global translation (3 values)")
    num_vertices: int = Field(..., description="Number of mesh vertices")
    num_faces: int = Field(..., description="Number of mesh faces")

    class Config:
        json_schema_extra = {
            "example": {
                "shape_params": [0.1, -0.2, 0.3, 0.0, -0.1],
                "pose_params": [0.0] * 72,
                "global_rotation": [0.0, 0.0, 0.0],
                "global_translation": [0.0, 0.0, 0.0],
                "num_vertices": 13776,
                "num_faces": 27386
            }
        }


class FittingMetrics(BaseModel):
    """Metrics from fitting process."""
    final_loss: float = Field(..., description="Final optimization loss")
    iterations_completed: int = Field(..., description="Number of iterations completed")
    convergence_achieved: bool = Field(..., description="Whether optimization converged")
    processing_time_seconds: float = Field(..., description="Total processing time")
    photo_reprojection_error: Optional[float] = Field(None, description="Average reprojection error")


class FittingResponse(BaseModel):
    """Schema for fitting response."""
    subject_id: str
    status: FittingStatusEnum
    task_id: Optional[str] = Field(None, description="Background task identifier")
    parameters: Optional[ModelParameters] = None
    metrics: Optional[FittingMetrics] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "subject_id": "subj_abc123xyz",
                "status": "completed",
                "task_id": "task_xyz789",
                "parameters": {
                    "shape_params": [0.1, -0.2, 0.3],
                    "pose_params": [0.0] * 72,
                    "global_rotation": [0.0, 0.0, 0.0],
                    "global_translation": [0.0, 0.0, 0.0],
                    "num_vertices": 13776,
                    "num_faces": 27386
                },
                "metrics": {
                    "final_loss": 0.0123,
                    "iterations_completed": 100,
                    "convergence_achieved": True,
                    "processing_time_seconds": 45.2,
                    "photo_reprojection_error": 2.3
                },
                "started_at": "2025-11-10T10:15:00",
                "completed_at": "2025-11-10T10:16:00"
            }
        }


class FittingStatus(BaseModel):
    """Schema for fitting status check."""
    status: FittingStatusEnum
    progress: float = Field(..., ge=0, le=100, description="Progress percentage")
    message: Optional[str] = None
    estimated_time_remaining: Optional[float] = Field(None, description="Estimated seconds remaining")
