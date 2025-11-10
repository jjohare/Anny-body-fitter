"""Pydantic schemas for API request/response validation."""

from .subject import (
    SubjectCreate,
    SubjectResponse,
    SubjectUpdate,
    SubjectList
)
from .fitting import (
    FittingRequest,
    FittingResponse,
    ModelParameters,
    FittingStatus
)
from .photo import (
    PhotoUpload,
    PhotoResponse,
    PhotoMetadata
)
from .metrics import (
    MetricsCreate,
    MetricsResponse,
    PerformanceMetrics
)

__all__ = [
    "SubjectCreate",
    "SubjectResponse",
    "SubjectUpdate",
    "SubjectList",
    "FittingRequest",
    "FittingResponse",
    "ModelParameters",
    "FittingStatus",
    "PhotoUpload",
    "PhotoResponse",
    "PhotoMetadata",
    "MetricsCreate",
    "MetricsResponse",
    "PerformanceMetrics",
]
