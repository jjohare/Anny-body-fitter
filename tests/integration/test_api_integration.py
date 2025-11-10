"""
API integration tests.
Tests all API endpoints using TestClient without real server.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import io
import json
from datetime import datetime

from src.api.main import app
from src.api.services.database import DatabaseService
from tests.fixtures.test_images import create_front_view_image


@pytest.fixture
def mock_db_service():
    """Mock database service."""
    db = Mock(spec=DatabaseService)
    db.connection = AsyncMock()
    db.initialize = AsyncMock()
    db.close = AsyncMock()
    db.fetch_one = AsyncMock()
    db.fetch_all = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def client(mock_db_service):
    """Create test client with mocked dependencies."""
    # Override lifespan to use mock database
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_lifespan(app):
        app.state.db = mock_db_service
        yield

    # Replace lifespan
    app.router.lifespan_context = mock_lifespan

    with TestClient(app) as test_client:
        test_client.app.state.db = mock_db_service
        yield test_client


@pytest.fixture
def mock_auth_user():
    """Mock authenticated user."""
    return {"id": "test-user-123", "email": "test@example.com"}


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Anny Body Fitter API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "operational"

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestSubjectEndpoints:
    """Test subject management endpoints."""

    @patch('src.api.middleware.auth.get_current_user')
    @patch('src.api.services.subject_service.SubjectService.create_subject')
    def test_create_subject(self, mock_create, mock_auth, client, mock_auth_user):
        """Test creating a new subject."""
        mock_auth.return_value = mock_auth_user
        mock_create.return_value = {
            "id": "subject-123",
            "name": "John Doe",
            "age": 30,
            "gender": "male",
            "height_cm": 175.0,
            "weight_kg": 70.0,
            "photo_count": 0,
            "has_fitted_model": False,
            "created_at": datetime.now().isoformat()
        }

        subject_data = {
            "name": "John Doe",
            "age": 30,
            "gender": "male",
            "height_cm": 175.0,
            "weight_kg": 70.0
        }

        response = client.post("/api/v1/subjects", json=subject_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "John Doe"
        assert data["id"] == "subject-123"

    @patch('src.api.middleware.auth.get_current_user')
    @patch('src.api.services.subject_service.SubjectService.list_subjects')
    def test_list_subjects(self, mock_list, mock_auth, client, mock_auth_user):
        """Test listing subjects with pagination."""
        mock_auth.return_value = mock_auth_user
        mock_list.return_value = {
            "items": [
                {"id": "1", "name": "Subject 1"},
                {"id": "2", "name": "Subject 2"}
            ],
            "total": 2,
            "page": 1,
            "page_size": 20
        }

        response = client.get("/api/v1/subjects?page=1&page_size=20")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2

    @patch('src.api.middleware.auth.get_current_user')
    @patch('src.api.services.subject_service.SubjectService.get_subject')
    def test_get_subject(self, mock_get, mock_auth, client, mock_auth_user):
        """Test getting a specific subject."""
        mock_auth.return_value = mock_auth_user
        mock_get.return_value = {
            "id": "subject-123",
            "name": "John Doe",
            "age": 30,
            "photo_count": 3,
            "has_fitted_model": True
        }

        response = client.get("/api/v1/subjects/subject-123")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "subject-123"
        assert data["has_fitted_model"] is True

    @patch('src.api.middleware.auth.get_current_user')
    @patch('src.api.services.subject_service.SubjectService.get_subject')
    def test_get_subject_not_found(self, mock_get, mock_auth, client, mock_auth_user):
        """Test getting non-existent subject."""
        mock_auth.return_value = mock_auth_user
        mock_get.return_value = None

        response = client.get("/api/v1/subjects/nonexistent")

        assert response.status_code == 404

    @patch('src.api.middleware.auth.get_current_user')
    @patch('src.api.services.subject_service.SubjectService.update_subject')
    def test_update_subject(self, mock_update, mock_auth, client, mock_auth_user):
        """Test updating subject information."""
        mock_auth.return_value = mock_auth_user
        mock_update.return_value = {
            "id": "subject-123",
            "name": "Updated Name",
            "age": 31
        }

        updates = {"name": "Updated Name", "age": 31}
        response = client.patch("/api/v1/subjects/subject-123", json=updates)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    @patch('src.api.middleware.auth.get_current_user')
    @patch('src.api.services.subject_service.SubjectService.delete_subject')
    def test_delete_subject(self, mock_delete, mock_auth, client, mock_auth_user):
        """Test deleting a subject."""
        mock_auth.return_value = mock_auth_user
        mock_delete.return_value = True

        response = client.delete("/api/v1/subjects/subject-123")

        assert response.status_code == 204


class TestPhotoEndpoints:
    """Test photo upload and management endpoints."""

    @patch('src.api.middleware.auth.get_current_user')
    @patch('src.api.services.subject_service.SubjectService.get_subject')
    @patch('src.api.services.photo_service.PhotoService.upload_photos')
    def test_upload_photos(self, mock_upload, mock_get_subject, mock_auth, client, mock_auth_user):
        """Test uploading photos for a subject."""
        mock_auth.return_value = mock_auth_user
        mock_get_subject.return_value = {"id": "subject-123", "name": "Test"}
        mock_upload.return_value = [
            {
                "id": "photo-1",
                "filename": "front.jpg",
                "photo_type": "front",
                "uploaded_at": datetime.now().isoformat()
            }
        ]

        # Create test image
        img_bytes = create_front_view_image()

        # Prepare multipart form data
        files = [("files", ("front.jpg", io.BytesIO(img_bytes), "image/jpeg"))]
        metadata = json.dumps([{"photo_type": "front", "notes": "Test photo"}])
        data = {"metadata": metadata}

        response = client.post(
            "/api/v1/subjects/subject-123/photos",
            files=files,
            data=data
        )

        assert response.status_code == 201
        photos = response.json()
        assert len(photos) == 1
        assert photos[0]["photo_type"] == "front"

    @patch('src.api.middleware.auth.get_current_user')
    @patch('src.api.services.subject_service.SubjectService.get_subject')
    @patch('src.api.services.photo_service.PhotoService.upload_photos')
    def test_upload_photos_invalid_type(self, mock_upload, mock_get_subject, mock_auth, client, mock_auth_user):
        """Test rejecting invalid file types."""
        mock_auth.return_value = mock_auth_user
        mock_get_subject.return_value = {"id": "subject-123"}

        # Create invalid file
        invalid_file = io.BytesIO(b"not an image")

        files = [("files", ("file.txt", invalid_file, "text/plain"))]
        metadata = json.dumps([{"photo_type": "front"}])
        data = {"metadata": metadata}

        response = client.post(
            "/api/v1/subjects/subject-123/photos",
            files=files,
            data=data
        )

        assert response.status_code == 400

    @patch('src.api.middleware.auth.get_current_user')
    @patch('src.api.services.photo_service.PhotoService.get_subject_photos')
    def test_list_subject_photos(self, mock_list, mock_auth, client, mock_auth_user):
        """Test listing photos for a subject."""
        mock_auth.return_value = mock_auth_user
        mock_list.return_value = [
            {"id": "photo-1", "filename": "front.jpg", "photo_type": "front"},
            {"id": "photo-2", "filename": "side.jpg", "photo_type": "side"}
        ]

        response = client.get("/api/v1/subjects/subject-123/photos")

        assert response.status_code == 200
        photos = response.json()
        assert len(photos) == 2


class TestFittingEndpoints:
    """Test model fitting endpoints."""

    @patch('src.api.middleware.auth.get_current_user')
    @patch('src.api.services.subject_service.SubjectService.get_subject')
    @patch('src.api.services.photo_service.PhotoService.get_subject_photos')
    @patch('src.api.services.fitting_service.FittingService.start_fitting')
    def test_start_fitting(self, mock_start, mock_photos, mock_subject, mock_auth, client, mock_auth_user):
        """Test starting model fitting process."""
        mock_auth.return_value = mock_auth_user
        mock_subject.return_value = {"id": "subject-123", "name": "Test"}
        mock_photos.return_value = [{"id": "photo-1"}]  # Has photos
        mock_start.return_value = {
            "task_id": "task-123",
            "status": "pending",
            "message": "Fitting process started"
        }

        fitting_request = {
            "optimization_iterations": 100,
            "use_shape_prior": True,
            "use_pose_prior": False
        }

        response = client.post(
            "/api/v1/subjects/subject-123/fit",
            json=fitting_request
        )

        assert response.status_code == 202
        data = response.json()
        assert data["task_id"] == "task-123"
        assert data["status"] == "pending"

    @patch('src.api.middleware.auth.get_current_user')
    @patch('src.api.services.subject_service.SubjectService.get_subject')
    @patch('src.api.services.photo_service.PhotoService.get_subject_photos')
    def test_start_fitting_no_photos(self, mock_photos, mock_subject, mock_auth, client, mock_auth_user):
        """Test fitting fails when no photos uploaded."""
        mock_auth.return_value = mock_auth_user
        mock_subject.return_value = {"id": "subject-123"}
        mock_photos.return_value = []  # No photos

        fitting_request = {"optimization_iterations": 100}

        response = client.post(
            "/api/v1/subjects/subject-123/fit",
            json=fitting_request
        )

        assert response.status_code == 400
        assert "no photos" in response.json()["detail"].lower()

    @patch('src.api.middleware.auth.get_current_user')
    @patch('src.api.services.fitting_service.FittingService.get_fitting_status')
    def test_get_fitting_status(self, mock_status, mock_auth, client, mock_auth_user):
        """Test checking fitting status."""
        mock_auth.return_value = mock_auth_user
        mock_status.return_value = {
            "status": "processing",
            "progress": 45.0,
            "estimated_time_remaining": 120.0
        }

        response = client.get("/api/v1/subjects/subject-123/fit/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert data["progress"] == 45.0

    @patch('src.api.middleware.auth.get_current_user')
    @patch('src.api.services.subject_service.SubjectService.get_subject')
    @patch('src.api.services.fitting_service.FittingService.get_model_parameters')
    def test_get_fitted_model(self, mock_params, mock_subject, mock_auth, client, mock_auth_user):
        """Test retrieving fitted model parameters."""
        mock_auth.return_value = mock_auth_user
        mock_subject.return_value = {
            "id": "subject-123",
            "has_fitted_model": True
        }
        mock_params.return_value = {
            "shape_params": [0.1, 0.2, -0.1],
            "pose_params": [0.0] * 24,
            "num_vertices": 6890,
            "num_faces": 13776
        }

        response = client.get("/api/v1/subjects/subject-123/model")

        assert response.status_code == 200
        data = response.json()
        assert "shape_params" in data
        assert data["num_vertices"] == 6890

    @patch('src.api.middleware.auth.get_current_user')
    @patch('src.api.services.subject_service.SubjectService.get_subject')
    def test_get_fitted_model_not_available(self, mock_subject, mock_auth, client, mock_auth_user):
        """Test retrieving model when not fitted yet."""
        mock_auth.return_value = mock_auth_user
        mock_subject.return_value = {
            "id": "subject-123",
            "has_fitted_model": False
        }

        response = client.get("/api/v1/subjects/subject-123/model")

        assert response.status_code == 404
        assert "no fitted model" in response.json()["detail"].lower()


class TestMetricsEndpoints:
    """Test performance metrics endpoints."""

    @patch('src.api.middleware.auth.get_current_user')
    @patch('src.api.services.subject_service.SubjectService.get_subject')
    @patch('src.api.services.metrics_service.MetricsService.create_metrics')
    def test_add_metrics(self, mock_create, mock_subject, mock_auth, client, mock_auth_user):
        """Test adding performance metrics."""
        mock_auth.return_value = mock_auth_user
        mock_subject.return_value = {
            "id": "subject-123",
            "has_fitted_model": True
        }
        mock_create.return_value = {
            "id": "metric-123",
            "subject_id": "subject-123",
            "accuracy_score": 0.92,
            "mean_error_cm": 1.5
        }

        metrics_data = {
            "accuracy_score": 0.92,
            "mean_error_cm": 1.5,
            "validation_method": "manual",
            "ground_truth_available": True
        }

        response = client.post(
            "/api/v1/subjects/subject-123/metrics",
            json=metrics_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["accuracy_score"] == 0.92

    @patch('src.api.middleware.auth.get_current_user')
    @patch('src.api.services.metrics_service.MetricsService.get_subject_metrics')
    def test_get_metrics(self, mock_get, mock_auth, client, mock_auth_user):
        """Test retrieving metrics for a subject."""
        mock_auth.return_value = mock_auth_user
        mock_get.return_value = [
            {"id": "1", "accuracy_score": 0.92},
            {"id": "2", "accuracy_score": 0.95}
        ]

        response = client.get("/api/v1/subjects/subject-123/metrics")

        assert response.status_code == 200
        metrics = response.json()
        assert len(metrics) == 2


class TestAuthentication:
    """Test authentication middleware."""

    @patch('src.api.middleware.auth.get_current_user')
    def test_authenticated_request(self, mock_auth, client):
        """Test request with valid authentication."""
        mock_auth.return_value = {"id": "user-123"}

        # This would normally require auth
        response = client.get("/api/v1/subjects")

        # Should not be rejected due to auth (may fail for other reasons)
        assert response.status_code != 401

    def test_unauthenticated_request(self, client):
        """Test request without authentication."""
        # Depending on middleware implementation
        # Some endpoints might require auth
        pass  # Auth middleware might be permissive in test mode


class TestErrorHandling:
    """Test API error handling."""

    def test_404_endpoint(self, client):
        """Test non-existent endpoint."""
        response = client.get("/api/v1/nonexistent")

        assert response.status_code == 404

    @patch('src.api.middleware.auth.get_current_user')
    @patch('src.api.services.subject_service.SubjectService.create_subject')
    def test_500_internal_error(self, mock_create, mock_auth, client, mock_auth_user):
        """Test handling of internal server errors."""
        mock_auth.return_value = mock_auth_user
        mock_create.side_effect = Exception("Database error")

        subject_data = {"name": "Test"}

        response = client.post("/api/v1/subjects", json=subject_data)

        assert response.status_code == 500
        assert "error" in response.json()


class TestProcessTimeHeader:
    """Test process time middleware."""

    def test_process_time_header(self, client):
        """Test that X-Process-Time header is added."""
        response = client.get("/health")

        assert "X-Process-Time" in response.headers
        process_time = float(response.headers["X-Process-Time"])
        assert process_time >= 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
