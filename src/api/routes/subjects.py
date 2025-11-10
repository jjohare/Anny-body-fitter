"""Subject management API endpoints."""

from fastapi import APIRouter, HTTPException, status, Depends, Query, Request
from typing import List, Optional
import logging

from src.api.schemas import (
    SubjectCreate,
    SubjectResponse,
    SubjectUpdate,
    SubjectList,
    MetricsCreate,
    MetricsResponse
)
from src.api.services.subject_service import SubjectService
from src.api.services.metrics_service import MetricsService
from src.api.middleware.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


def get_subject_service(request: Request) -> SubjectService:
    """Dependency to get subject service."""
    return SubjectService(request.app.state.db)


def get_metrics_service(request: Request) -> MetricsService:
    """Dependency to get metrics service."""
    return MetricsService(request.app.state.db)


@router.post(
    "",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new subject",
    description="Create a new subject for body fitting"
)
async def create_subject(
    subject: SubjectCreate,
    service: SubjectService = Depends(get_subject_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new subject with the following information:
    - **name**: Subject identifier (required)
    - **age**: Age in years (optional)
    - **gender**: Gender (optional)
    - **height_cm**: Height in centimeters (optional)
    - **weight_kg**: Weight in kilograms (optional)
    - **notes**: Additional notes (optional)
    """
    try:
        logger.info(f"Creating subject: {subject.name}")
        created_subject = await service.create_subject(subject, current_user.get("id"))
        return created_subject
    except Exception as e:
        logger.error(f"Error creating subject: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create subject: {str(e)}"
        )


@router.get(
    "",
    response_model=SubjectList,
    summary="List all subjects",
    description="Get paginated list of all subjects"
)
async def list_subjects(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name"),
    service: SubjectService = Depends(get_subject_service),
    current_user: dict = Depends(get_current_user)
):
    """
    List all subjects with pagination:
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **search**: Optional search term for filtering by name
    """
    try:
        subjects_list = await service.list_subjects(
            page=page,
            page_size=page_size,
            search=search,
            user_id=current_user.get("id")
        )
        return subjects_list
    except Exception as e:
        logger.error(f"Error listing subjects: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list subjects: {str(e)}"
        )


@router.get(
    "/{subject_id}",
    response_model=SubjectResponse,
    summary="Get subject details",
    description="Retrieve detailed information about a specific subject"
)
async def get_subject(
    subject_id: str,
    service: SubjectService = Depends(get_subject_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed information about a subject by ID.
    """
    try:
        subject = await service.get_subject(subject_id, current_user.get("id"))
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subject {subject_id} not found"
            )
        return subject
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subject {subject_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get subject: {str(e)}"
        )


@router.patch(
    "/{subject_id}",
    response_model=SubjectResponse,
    summary="Update subject",
    description="Update subject information"
)
async def update_subject(
    subject_id: str,
    updates: SubjectUpdate,
    service: SubjectService = Depends(get_subject_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Update subject information. Only provided fields will be updated.
    """
    try:
        updated_subject = await service.update_subject(
            subject_id,
            updates,
            current_user.get("id")
        )
        if not updated_subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subject {subject_id} not found"
            )
        return updated_subject
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating subject {subject_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update subject: {str(e)}"
        )


@router.delete(
    "/{subject_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete subject",
    description="Delete a subject and all associated data (with privacy safeguards)"
)
async def delete_subject(
    subject_id: str,
    permanent: bool = Query(False, description="Permanently delete (bypass soft delete)"),
    service: SubjectService = Depends(get_subject_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a subject. By default, performs soft delete for data recovery.
    Set permanent=true for permanent deletion (GDPR compliance).

    This will:
    - Delete all photos
    - Delete fitted models
    - Delete metrics
    - Remove all personal data
    """
    try:
        success = await service.delete_subject(
            subject_id,
            current_user.get("id"),
            permanent=permanent
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subject {subject_id} not found"
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting subject {subject_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete subject: {str(e)}"
        )


@router.post(
    "/{subject_id}/metrics",
    response_model=MetricsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add performance metrics",
    description="Add performance metrics for a fitted model"
)
async def add_metrics(
    subject_id: str,
    metrics: MetricsCreate,
    service: MetricsService = Depends(get_metrics_service),
    subject_service: SubjectService = Depends(get_subject_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Add performance metrics for a subject's fitted model.

    Requires a fitted model to exist for the subject.
    """
    try:
        # Verify subject exists
        subject = await subject_service.get_subject(subject_id, current_user.get("id"))
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subject {subject_id} not found"
            )

        if not subject.has_fitted_model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subject must have a fitted model before adding metrics"
            )

        created_metrics = await service.create_metrics(
            subject_id,
            metrics,
            current_user.get("id")
        )
        return created_metrics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding metrics for subject {subject_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add metrics: {str(e)}"
        )


@router.get(
    "/{subject_id}/metrics",
    response_model=List[MetricsResponse],
    summary="Get subject metrics",
    description="Get all performance metrics for a subject"
)
async def get_subject_metrics(
    subject_id: str,
    service: MetricsService = Depends(get_metrics_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all performance metrics associated with a subject.
    """
    try:
        metrics = await service.get_subject_metrics(subject_id, current_user.get("id"))
        return metrics
    except Exception as e:
        logger.error(f"Error getting metrics for subject {subject_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )
