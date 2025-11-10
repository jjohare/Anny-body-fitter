"""Model fitting service."""

import uuid
import json
import logging
from typing import Optional
from datetime import datetime
from fastapi import BackgroundTasks

from src.api.schemas import (
    FittingRequest,
    FittingResponse,
    FittingStatus,
    FittingStatusEnum,
    ModelParameters,
    FittingMetrics
)
from src.api.services.database import DatabaseService

logger = logging.getLogger(__name__)


class FittingService:
    """Service for managing model fitting operations."""

    def __init__(self, db: DatabaseService):
        """Initialize fitting service."""
        self.db = db

    async def start_fitting(
        self,
        subject_id: str,
        fitting_request: FittingRequest,
        background_tasks: BackgroundTasks,
        user_id: str
    ) -> FittingResponse:
        """Start model fitting process."""
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        fitting_id = f"fit_{uuid.uuid4().hex[:12]}"

        # Create fitting task record
        query = """
            INSERT INTO fitting_tasks (
                id, subject_id, status, task_id,
                optimization_iterations, use_shape_prior, use_pose_prior,
                lambda_shape, lambda_pose, started_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        params = (
            fitting_id,
            subject_id,
            FittingStatusEnum.PENDING.value,
            task_id,
            fitting_request.optimization_iterations,
            fitting_request.use_shape_prior,
            fitting_request.use_pose_prior,
            fitting_request.lambda_shape,
            fitting_request.lambda_pose
        )

        await self.db.execute(query, params)

        # Queue background task
        background_tasks.add_task(
            self._run_fitting_task,
            fitting_id,
            subject_id,
            fitting_request
        )

        return FittingResponse(
            subject_id=subject_id,
            status=FittingStatusEnum.PENDING,
            task_id=task_id,
            started_at=datetime.utcnow()
        )

    async def _run_fitting_task(
        self,
        fitting_id: str,
        subject_id: str,
        fitting_request: FittingRequest
    ):
        """
        Run the actual fitting process in background.

        This is a placeholder implementation - integrate with actual Anny model.
        """
        try:
            # Update status to processing
            await self._update_fitting_status(fitting_id, FittingStatusEnum.PROCESSING)

            logger.info(f"Starting fitting task {fitting_id} for subject {subject_id}")

            # TODO: Integrate with actual Anny model fitting
            # This is where you would:
            # 1. Load photos from storage
            # 2. Initialize Anny model
            # 3. Run optimization with provided parameters
            # 4. Extract fitted parameters

            # Simulated fitting process
            import asyncio
            await asyncio.sleep(5)  # Simulate processing time

            # Generate mock parameters (replace with actual fitted parameters)
            model_params = ModelParameters(
                shape_params=[0.0] * 10,
                pose_params=[0.0] * 72,
                global_rotation=[0.0, 0.0, 0.0],
                global_translation=[0.0, 0.0, 0.0],
                num_vertices=13776,
                num_faces=27386
            )

            metrics = FittingMetrics(
                final_loss=0.0123,
                iterations_completed=fitting_request.optimization_iterations,
                convergence_achieved=True,
                processing_time_seconds=5.0,
                photo_reprojection_error=2.3
            )

            # Save model parameters
            await self._save_model_parameters(subject_id, model_params, metrics)

            # Update fitting status to completed
            await self._update_fitting_status(
                fitting_id,
                FittingStatusEnum.COMPLETED,
                completed_at=datetime.utcnow()
            )

            # Update subject has_fitted_model flag
            await self.db.execute(
                "UPDATE subjects SET has_fitted_model = 1 WHERE id = ?",
                (subject_id,)
            )

            logger.info(f"Fitting task {fitting_id} completed successfully")

        except Exception as e:
            logger.error(f"Fitting task {fitting_id} failed: {e}", exc_info=True)
            await self._update_fitting_status(
                fitting_id,
                FittingStatusEnum.FAILED,
                error_message=str(e)
            )

    async def _update_fitting_status(
        self,
        fitting_id: str,
        status: FittingStatusEnum,
        error_message: Optional[str] = None,
        completed_at: Optional[datetime] = None
    ):
        """Update fitting task status."""
        updates = ["status = ?"]
        params = [status.value]

        if error_message:
            updates.append("error_message = ?")
            params.append(error_message)

        if completed_at:
            updates.append("completed_at = ?")
            params.append(completed_at.isoformat())

        query = f"""
            UPDATE fitting_tasks
            SET {', '.join(updates)}
            WHERE id = ?
        """
        params.append(fitting_id)

        await self.db.execute(query, tuple(params))

    async def _save_model_parameters(
        self,
        subject_id: str,
        params: ModelParameters,
        metrics: FittingMetrics
    ):
        """Save fitted model parameters."""
        param_id = f"param_{uuid.uuid4().hex[:12]}"

        query = """
            INSERT OR REPLACE INTO model_parameters (
                id, subject_id, shape_params, pose_params,
                global_rotation, global_translation,
                num_vertices, num_faces,
                final_loss, iterations_completed,
                convergence_achieved, processing_time_seconds,
                photo_reprojection_error
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        query_params = (
            param_id,
            subject_id,
            json.dumps(params.shape_params),
            json.dumps(params.pose_params),
            json.dumps(params.global_rotation),
            json.dumps(params.global_translation),
            params.num_vertices,
            params.num_faces,
            metrics.final_loss,
            metrics.iterations_completed,
            metrics.convergence_achieved,
            metrics.processing_time_seconds,
            metrics.photo_reprojection_error
        )

        await self.db.execute(query, query_params)

    async def get_fitting_status(
        self,
        subject_id: str,
        user_id: str
    ) -> Optional[FittingStatus]:
        """Get current fitting status."""
        query = """
            SELECT * FROM fitting_tasks
            WHERE subject_id = ?
            ORDER BY started_at DESC
            LIMIT 1
        """
        row = await self.db.fetch_one(query, (subject_id,))

        if not row:
            return None

        # Calculate progress
        progress = 0.0
        if row["status"] == FittingStatusEnum.COMPLETED.value:
            progress = 100.0
        elif row["status"] == FittingStatusEnum.PROCESSING.value:
            progress = 50.0  # Placeholder
        elif row["status"] == FittingStatusEnum.PENDING.value:
            progress = 0.0

        return FittingStatus(
            status=FittingStatusEnum(row["status"]),
            progress=progress,
            message=row["error_message"] if row["error_message"] else None
        )

    async def get_model_parameters(
        self,
        subject_id: str,
        user_id: str
    ) -> Optional[ModelParameters]:
        """Get fitted model parameters."""
        query = """
            SELECT * FROM model_parameters
            WHERE subject_id = ?
        """
        row = await self.db.fetch_one(query, (subject_id,))

        if not row:
            return None

        return ModelParameters(
            shape_params=json.loads(row["shape_params"]),
            pose_params=json.loads(row["pose_params"]),
            global_rotation=json.loads(row["global_rotation"]),
            global_translation=json.loads(row["global_translation"]),
            num_vertices=row["num_vertices"],
            num_faces=row["num_faces"]
        )
