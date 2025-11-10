"""Model fitting API endpoints."""

from fastapi import (
    APIRouter,
    HTTPException,
    status,
    Depends,
    UploadFile,
    File,
    Form,
    BackgroundTasks,
    Request
)
from typing import List, Optional
import logging
import json

from src.api.schemas import (
    FittingRequest,
    FittingResponse,
    FittingStatus,
    PhotoResponse,
    PhotoMetadata,
    ModelParameters
)
from src.api.services.fitting_service import FittingService
from src.api.services.photo_service import PhotoService
from src.api.services.subject_service import SubjectService
from src.api.middleware.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


def get_fitting_service(request: Request) -> FittingService:
    """Dependency to get fitting service."""
    return FittingService(request.app.state.db)


def get_photo_service(request: Request) -> PhotoService:
    """Dependency to get photo service."""
    return PhotoService(request.app.state.db)


def get_subject_service(request: Request) -> SubjectService:
    """Dependency to get subject service."""
    return SubjectService(request.app.state.db)


@router.post(
    "/subjects/{subject_id}/photos",
    response_model=List[PhotoResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload photos",
    description="Upload one or more photos for model fitting"
)
async def upload_photos(
    subject_id: str,
    files: List[UploadFile] = File(..., description="Photo files (JPEG, PNG)"),
    metadata: str = Form(..., description="JSON array of photo metadata"),
    photo_service: PhotoService = Depends(get_photo_service),
    subject_service: SubjectService = Depends(get_subject_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload photos for a subject. Multiple photos can be uploaded at once.

    - **files**: Image files (JPEG, PNG format recommended)
    - **metadata**: JSON array of metadata objects, one per file

    Example metadata:
    ```json
    [
        {
            "photo_type": "front",
            "camera_height_cm": 150.0,
            "distance_cm": 300.0,
            "notes": "Good lighting"
        }
    ]
    ```
    """
    try:
        # Verify subject exists
        subject = await subject_service.get_subject(subject_id, current_user.get("id"))
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subject {subject_id} not found"
            )

        # Parse metadata
        try:
            metadata_list = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid metadata JSON format"
            )

        if len(files) != len(metadata_list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Number of files must match number of metadata entries"
            )

        # Validate file types
        allowed_types = {"image/jpeg", "image/png", "image/jpg"}
        for file in files:
            if file.content_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid file type: {file.content_type}. Allowed: JPEG, PNG"
                )

        # Upload photos
        uploaded_photos = await photo_service.upload_photos(
            subject_id=subject_id,
            files=files,
            metadata_list=metadata_list,
            user_id=current_user.get("id")
        )

        logger.info(f"Uploaded {len(uploaded_photos)} photos for subject {subject_id}")
        return uploaded_photos

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading photos for subject {subject_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload photos: {str(e)}"
        )


@router.get(
    "/subjects/{subject_id}/photos",
    response_model=List[PhotoResponse],
    summary="List subject photos",
    description="Get all photos for a subject"
)
async def list_subject_photos(
    subject_id: str,
    photo_service: PhotoService = Depends(get_photo_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all photos associated with a subject.
    """
    try:
        photos = await photo_service.get_subject_photos(subject_id, current_user.get("id"))
        return photos
    except Exception as e:
        logger.error(f"Error listing photos for subject {subject_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list photos: {str(e)}"
        )


@router.post(
    "/subjects/{subject_id}/fit",
    response_model=FittingResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger model fitting",
    description="Start background task to fit 3D model to photos"
)
async def fit_model(
    subject_id: str,
    fitting_request: FittingRequest,
    background_tasks: BackgroundTasks,
    fitting_service: FittingService = Depends(get_fitting_service),
    subject_service: SubjectService = Depends(get_subject_service),
    photo_service: PhotoService = Depends(get_photo_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger 3D model fitting process. This is an async operation.

    The fitting process:
    1. Validates that photos have been uploaded
    2. Starts background optimization task
    3. Returns task ID for status tracking

    Configuration options:
    - **optimization_iterations**: Number of optimization steps (1-1000)
    - **use_shape_prior**: Enable shape regularization
    - **use_pose_prior**: Enable pose regularization
    - **lambda_shape**: Weight for shape regularization
    - **lambda_pose**: Weight for pose regularization
    """
    try:
        # Verify subject exists
        subject = await subject_service.get_subject(subject_id, current_user.get("id"))
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subject {subject_id} not found"
            )

        # Verify photos exist
        photos = await photo_service.get_subject_photos(subject_id, current_user.get("id"))
        if not photos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No photos uploaded for this subject. Upload photos first."
            )

        # Start fitting task
        fitting_response = await fitting_service.start_fitting(
            subject_id=subject_id,
            fitting_request=fitting_request,
            background_tasks=background_tasks,
            user_id=current_user.get("id")
        )

        logger.info(f"Started fitting task {fitting_response.task_id} for subject {subject_id}")
        return fitting_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting fitting for subject {subject_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start fitting: {str(e)}"
        )


@router.get(
    "/subjects/{subject_id}/fit/status",
    response_model=FittingStatus,
    summary="Get fitting status",
    description="Check status of ongoing fitting task"
)
async def get_fitting_status(
    subject_id: str,
    fitting_service: FittingService = Depends(get_fitting_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Check the status of a fitting task.

    Returns:
    - Current status (pending/processing/completed/failed)
    - Progress percentage
    - Estimated time remaining (if available)
    """
    try:
        fitting_status = await fitting_service.get_fitting_status(
            subject_id,
            current_user.get("id")
        )
        if not fitting_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No fitting task found for subject {subject_id}"
            )
        return fitting_status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting fitting status for subject {subject_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get fitting status: {str(e)}"
        )


@router.get(
    "/subjects/{subject_id}/model",
    response_model=ModelParameters,
    summary="Get fitted model",
    description="Retrieve fitted 3D model parameters"
)
async def get_fitted_model(
    subject_id: str,
    fitting_service: FittingService = Depends(get_fitting_service),
    subject_service: SubjectService = Depends(get_subject_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Get the fitted 3D model parameters for a subject.

    Returns:
    - Shape parameters (beta)
    - Pose parameters (theta)
    - Global rotation and translation
    - Mesh information (vertices, faces)

    This endpoint only returns data if fitting has completed successfully.
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
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No fitted model available for subject {subject_id}. Run fitting first."
            )

        model_params = await fitting_service.get_model_parameters(
            subject_id,
            current_user.get("id")
        )

        return model_params

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model for subject {subject_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model: {str(e)}"
        )
