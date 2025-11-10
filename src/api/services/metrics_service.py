"""Metrics management service."""

import uuid
import json
import logging
from typing import List
from datetime import datetime

from src.api.schemas import MetricsCreate, MetricsResponse
from src.api.services.database import DatabaseService

logger = logging.getLogger(__name__)


class MetricsService:
    """Service for managing performance metrics."""

    def __init__(self, db: DatabaseService):
        """Initialize metrics service."""
        self.db = db

    async def create_metrics(
        self,
        subject_id: str,
        metrics: MetricsCreate,
        user_id: str
    ) -> MetricsResponse:
        """Create performance metrics for a subject."""
        metrics_id = f"metrics_{uuid.uuid4().hex[:12]}"

        query = """
            INSERT INTO metrics (
                id, subject_id,
                accuracy_score, precision_score, recall_score, f1_score,
                mean_error_cm, max_error_cm,
                ground_truth_available, validation_method,
                notes, custom_metrics
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            metrics_id,
            subject_id,
            metrics.metrics.accuracy_score,
            metrics.metrics.precision,
            metrics.metrics.recall,
            metrics.metrics.f1_score,
            metrics.metrics.mean_error_cm,
            metrics.metrics.max_error_cm,
            metrics.ground_truth_available,
            metrics.validation_method,
            metrics.notes,
            json.dumps(metrics.custom_metrics) if metrics.custom_metrics else None
        )

        await self.db.execute(query, params)

        # Fetch and return created metrics
        return await self.get_metrics(metrics_id)

    async def get_metrics(self, metrics_id: str) -> MetricsResponse:
        """Get metrics by ID."""
        query = "SELECT * FROM metrics WHERE id = ?"
        row = await self.db.fetch_one(query, (metrics_id,))

        return self._row_to_metrics(row)

    async def get_subject_metrics(
        self,
        subject_id: str,
        user_id: str
    ) -> List[MetricsResponse]:
        """Get all metrics for a subject."""
        query = """
            SELECT m.* FROM metrics m
            JOIN subjects s ON m.subject_id = s.id
            WHERE m.subject_id = ? AND s.user_id = ?
            ORDER BY m.created_at DESC
        """
        rows = await self.db.fetch_all(query, (subject_id, user_id))

        return [self._row_to_metrics(row) for row in rows]

    def _row_to_metrics(self, row) -> MetricsResponse:
        """Convert database row to MetricsResponse."""
        from src.api.schemas import PerformanceMetrics

        return MetricsResponse(
            id=row["id"],
            subject_id=row["subject_id"],
            metrics=PerformanceMetrics(
                accuracy_score=row["accuracy_score"],
                precision=row["precision_score"],
                recall=row["recall_score"],
                f1_score=row["f1_score"],
                mean_error_cm=row["mean_error_cm"],
                max_error_cm=row["max_error_cm"]
            ),
            ground_truth_available=bool(row["ground_truth_available"]),
            validation_method=row["validation_method"],
            notes=row["notes"],
            custom_metrics=json.loads(row["custom_metrics"]) if row["custom_metrics"] else None,
            created_at=datetime.fromisoformat(row["created_at"])
        )
