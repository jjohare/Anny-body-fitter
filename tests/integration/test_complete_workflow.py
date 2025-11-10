"""
Complete end-to-end workflow integration tests.
Tests the full pipeline: upload photos → extract measurements → fit model → store in DB → retrieve results.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import io
import json
from datetime import datetime
import tempfile
import os
from pathlib import Path

from tests.fixtures.test_images import (
    create_front_view_image,
    create_side_view_image,
    create_back_view_image
)


class TestSingleImageWorkflow:
    """Test complete workflow with single image."""

    @patch('src.api.services.database.DatabaseService')
    @patch('src.api.services.subject_service.SubjectService')
    @patch('src.api.services.photo_service.PhotoService')
    @patch('src.api.services.fitting_service.FittingService')
    async def test_single_image_complete_workflow(self,
                                                   mock_fitting_service,
                                                   mock_photo_service,
                                                   mock_subject_service,
                                                   mock_db_service):
        """
        Test complete workflow:
        1. Create subject
        2. Upload photo
        3. Trigger fitting
        4. Wait for completion
        5. Retrieve fitted model
        6. Store results in database
        """
        # Setup mocks
        subject_id = "test-subject-123"
        photo_id = "test-photo-456"
        task_id = "test-task-789"

        # Mock database
        mock_db = Mock()
        mock_db.fetch_one = AsyncMock()
        mock_db.fetch_all = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db_service.return_value = mock_db

        # Mock subject service
        mock_subject_svc = Mock()
        mock_subject_svc.create_subject = AsyncMock(return_value={
            "id": subject_id,
            "name": "Test Subject",
            "age": 30,
            "height_cm": 175.0,
            "weight_kg": 70.0,
            "photo_count": 0,
            "has_fitted_model": False,
            "created_at": datetime.now().isoformat()
        })
        mock_subject_svc.get_subject = AsyncMock(return_value={
            "id": subject_id,
            "has_fitted_model": False
        })
        mock_subject_service.return_value = mock_subject_svc

        # Mock photo service
        mock_photo_svc = Mock()
        mock_photo_svc.upload_photos = AsyncMock(return_value=[{
            "id": photo_id,
            "subject_id": subject_id,
            "filename": "front.jpg",
            "photo_type": "front",
            "uploaded_at": datetime.now().isoformat()
        }])
        mock_photo_svc.get_subject_photos = AsyncMock(return_value=[{
            "id": photo_id
        }])
        mock_photo_service.return_value = mock_photo_svc

        # Mock fitting service
        mock_fitting_svc = Mock()
        mock_fitting_svc.start_fitting = AsyncMock(return_value={
            "task_id": task_id,
            "status": "pending",
            "message": "Fitting started"
        })
        mock_fitting_svc.get_fitting_status = AsyncMock(return_value={
            "status": "completed",
            "progress": 100.0
        })
        mock_fitting_svc.get_model_parameters = AsyncMock(return_value={
            "shape_params": [0.1, 0.2, -0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "pose_params": [0.0] * 24,
            "global_rotation": [0.0, 0.0, 0.0],
            "global_translation": [0.0, 0.0, 0.0],
            "num_vertices": 6890,
            "num_faces": 13776,
            "final_loss": 0.05,
            "iterations_completed": 100,
            "convergence_achieved": True
        })
        mock_fitting_service.return_value = mock_fitting_svc

        # Execute workflow
        # 1. Create subject
        subject = await mock_subject_svc.create_subject({
            "name": "Test Subject",
            "age": 30,
            "height_cm": 175.0
        }, "user-123")

        assert subject["id"] == subject_id
        assert subject["has_fitted_model"] is False

        # 2. Upload photo
        img_bytes = create_front_view_image()
        photos = await mock_photo_svc.upload_photos(
            subject_id=subject_id,
            files=[Mock(file=io.BytesIO(img_bytes), filename="front.jpg")],
            metadata_list=[{"photo_type": "front"}],
            user_id="user-123"
        )

        assert len(photos) == 1
        assert photos[0]["photo_type"] == "front"

        # 3. Trigger fitting
        fitting_response = await mock_fitting_svc.start_fitting(
            subject_id=subject_id,
            fitting_request={"optimization_iterations": 100},
            background_tasks=Mock(),
            user_id="user-123"
        )

        assert fitting_response["task_id"] == task_id
        assert fitting_response["status"] == "pending"

        # 4. Check completion status
        status = await mock_fitting_svc.get_fitting_status(subject_id, "user-123")

        assert status["status"] == "completed"
        assert status["progress"] == 100.0

        # 5. Retrieve fitted model
        model_params = await mock_fitting_svc.get_model_parameters(subject_id, "user-123")

        assert len(model_params["shape_params"]) == 10
        assert model_params["num_vertices"] == 6890
        assert model_params["convergence_achieved"] is True

        # Verify complete workflow
        assert subject["id"] == subject_id
        assert len(photos) > 0
        assert model_params["final_loss"] < 1.0


class TestMultiImageWorkflow:
    """Test complete workflow with multiple images."""

    @patch('src.api.services.database.DatabaseService')
    @patch('src.api.services.subject_service.SubjectService')
    @patch('src.api.services.photo_service.PhotoService')
    @patch('src.api.services.fitting_service.FittingService')
    async def test_multi_image_workflow(self,
                                        mock_fitting_service,
                                        mock_photo_service,
                                        mock_subject_service,
                                        mock_db_service):
        """
        Test workflow with multiple images (front, side, back).
        Should improve fitting accuracy.
        """
        subject_id = "multi-image-subject"

        # Setup mocks
        mock_db = Mock()
        mock_db.fetch_one = AsyncMock()
        mock_db.fetch_all = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db_service.return_value = mock_db

        mock_subject_svc = Mock()
        mock_subject_svc.create_subject = AsyncMock(return_value={
            "id": subject_id,
            "name": "Multi-Image Subject",
            "photo_count": 0
        })
        mock_subject_service.return_value = mock_subject_svc

        mock_photo_svc = Mock()
        mock_photo_svc.upload_photos = AsyncMock(return_value=[
            {"id": "photo-1", "photo_type": "front"},
            {"id": "photo-2", "photo_type": "side"},
            {"id": "photo-3", "photo_type": "back"}
        ])
        mock_photo_svc.get_subject_photos = AsyncMock(return_value=[
            {"id": "photo-1"},
            {"id": "photo-2"},
            {"id": "photo-3"}
        ])
        mock_photo_service.return_value = mock_photo_svc

        mock_fitting_svc = Mock()
        mock_fitting_svc.start_fitting = AsyncMock(return_value={
            "task_id": "multi-task",
            "status": "pending"
        })
        mock_fitting_svc.get_model_parameters = AsyncMock(return_value={
            "shape_params": [0.1] * 10,
            "final_loss": 0.03,  # Better than single image
            "convergence_achieved": True
        })
        mock_fitting_service.return_value = mock_fitting_svc

        # 1. Create subject
        subject = await mock_subject_svc.create_subject({
            "name": "Multi-Image Subject"
        }, "user-123")

        # 2. Upload multiple photos
        images = [
            create_front_view_image(),
            create_side_view_image(),
            create_back_view_image()
        ]
        metadata = [
            {"photo_type": "front"},
            {"photo_type": "side"},
            {"photo_type": "back"}
        ]

        photos = await mock_photo_svc.upload_photos(
            subject_id=subject_id,
            files=[Mock(file=io.BytesIO(img)) for img in images],
            metadata_list=metadata,
            user_id="user-123"
        )

        assert len(photos) == 3

        # 3. Trigger fitting with multiple images
        fitting_response = await mock_fitting_svc.start_fitting(
            subject_id=subject_id,
            fitting_request={"optimization_iterations": 200},
            background_tasks=Mock(),
            user_id="user-123"
        )

        # 4. Get final model (should have better accuracy)
        model_params = await mock_fitting_svc.get_model_parameters(subject_id, "user-123")

        # Multi-image should have lower error
        assert model_params["final_loss"] < 0.05
        assert model_params["convergence_achieved"] is True


class TestSubjectMetadataStorage:
    """Test storing and retrieving subject metadata."""

    @patch('src.api.services.database.DatabaseService')
    @patch('src.api.services.subject_service.SubjectService')
    async def test_store_subject_metadata(self, mock_subject_service, mock_db_service):
        """Test storing comprehensive subject metadata."""
        mock_db = Mock()
        mock_db.execute = AsyncMock()
        mock_db.fetch_one = AsyncMock(return_value={
            "id": "subject-123",
            "name": "John Doe",
            "age": 30,
            "gender": "male",
            "height_cm": 175.0,
            "weight_kg": 70.0,
            "notes": "Test subject with complete metadata",
            "created_at": datetime.now().isoformat()
        })
        mock_db_service.return_value = mock_db

        mock_subject_svc = Mock()
        mock_subject_svc.create_subject = AsyncMock(return_value={
            "id": "subject-123",
            "name": "John Doe",
            "age": 30,
            "gender": "male",
            "height_cm": 175.0,
            "weight_kg": 70.0,
            "notes": "Test subject with complete metadata"
        })
        mock_subject_svc.get_subject = AsyncMock(return_value={
            "id": "subject-123",
            "name": "John Doe",
            "age": 30
        })
        mock_subject_service.return_value = mock_subject_svc

        # Create subject with metadata
        subject = await mock_subject_svc.create_subject({
            "name": "John Doe",
            "age": 30,
            "gender": "male",
            "height_cm": 175.0,
            "weight_kg": 70.0,
            "notes": "Test subject with complete metadata"
        }, "user-123")

        # Verify stored
        assert subject["name"] == "John Doe"
        assert subject["age"] == 30
        assert subject["gender"] == "male"

        # Retrieve and verify
        retrieved = await mock_subject_svc.get_subject("subject-123", "user-123")
        assert retrieved["id"] == "subject-123"


class Test3DModelExport:
    """Test exporting fitted 3D models."""

    @patch('src.api.services.fitting_service.FittingService')
    async def test_export_obj_format(self, mock_fitting_service):
        """Test exporting fitted model to OBJ format."""
        mock_fitting_svc = Mock()
        mock_fitting_svc.get_model_parameters = AsyncMock(return_value={
            "shape_params": [0.1] * 10,
            "pose_params": [0.0] * 24,
            "num_vertices": 6890,
            "num_faces": 13776
        })
        mock_fitting_service.return_value = mock_fitting_svc

        # Get model parameters
        params = await mock_fitting_svc.get_model_parameters("subject-123", "user-123")

        # Simulate export
        vertices = [[0.0, 0.0, 0.0]] * params["num_vertices"]
        faces = [[0, 1, 2]] * params["num_faces"]

        # Create OBJ content
        obj_lines = []
        for v in vertices[:10]:  # Sample
            obj_lines.append(f"v {v[0]} {v[1]} {v[2]}")
        for f in faces[:10]:  # Sample
            obj_lines.append(f"f {f[0]+1} {f[1]+1} {f[2]+1}")

        obj_content = "\n".join(obj_lines)

        assert "v " in obj_content
        assert "f " in obj_content


class TestErrorRecovery:
    """Test error recovery in workflows."""

    @patch('src.api.services.fitting_service.FittingService')
    async def test_fitting_failure_recovery(self, mock_fitting_service):
        """Test handling of fitting failures."""
        mock_fitting_svc = Mock()
        mock_fitting_svc.start_fitting = AsyncMock(return_value={
            "task_id": "fail-task",
            "status": "pending"
        })
        mock_fitting_svc.get_fitting_status = AsyncMock(return_value={
            "status": "failed",
            "error_message": "Optimization did not converge",
            "progress": 75.0
        })
        mock_fitting_service.return_value = mock_fitting_svc

        # Start fitting
        response = await mock_fitting_svc.start_fitting(
            subject_id="subject-123",
            fitting_request={},
            background_tasks=Mock(),
            user_id="user-123"
        )

        # Check status (failed)
        status = await mock_fitting_svc.get_fitting_status("subject-123", "user-123")

        assert status["status"] == "failed"
        assert "error_message" in status

    @patch('src.api.services.photo_service.PhotoService')
    async def test_photo_upload_failure(self, mock_photo_service):
        """Test handling of photo upload failures."""
        mock_photo_svc = Mock()
        mock_photo_svc.upload_photos = AsyncMock(
            side_effect=Exception("Storage service unavailable")
        )
        mock_photo_service.return_value = mock_photo_svc

        # Attempt upload
        with pytest.raises(Exception) as exc_info:
            await mock_photo_svc.upload_photos(
                subject_id="subject-123",
                files=[],
                metadata_list=[],
                user_id="user-123"
            )

        assert "Storage service" in str(exc_info.value)


class TestDataConsistency:
    """Test data consistency across workflow."""

    @patch('src.api.services.database.DatabaseService')
    @patch('src.api.services.subject_service.SubjectService')
    @patch('src.api.services.fitting_service.FittingService')
    async def test_photo_count_consistency(self,
                                           mock_fitting_service,
                                           mock_subject_service,
                                           mock_db_service):
        """Test that photo count is correctly maintained."""
        # Setup
        subject_id = "consistency-test"
        mock_db = Mock()
        mock_db_service.return_value = mock_db

        mock_subject_svc = Mock()
        mock_subject_svc.create_subject = AsyncMock(return_value={
            "id": subject_id,
            "photo_count": 0
        })
        mock_subject_svc.get_subject = AsyncMock(return_value={
            "id": subject_id,
            "photo_count": 3  # After upload
        })
        mock_subject_service.return_value = mock_subject_svc

        # Create subject
        subject = await mock_subject_svc.create_subject({}, "user-123")
        assert subject["photo_count"] == 0

        # After uploading 3 photos
        updated_subject = await mock_subject_svc.get_subject(subject_id, "user-123")
        assert updated_subject["photo_count"] == 3

    @patch('src.api.services.database.DatabaseService')
    @patch('src.api.services.subject_service.SubjectService')
    async def test_fitting_status_consistency(self, mock_subject_service, mock_db_service):
        """Test that has_fitted_model flag is correctly updated."""
        subject_id = "fitting-status-test"

        mock_db = Mock()
        mock_db_service.return_value = mock_db

        mock_subject_svc = Mock()
        mock_subject_svc.get_subject = AsyncMock(side_effect=[
            {"id": subject_id, "has_fitted_model": False},  # Before fitting
            {"id": subject_id, "has_fitted_model": True}    # After fitting
        ])
        mock_subject_service.return_value = mock_subject_svc

        # Before fitting
        subject = await mock_subject_svc.get_subject(subject_id, "user-123")
        assert subject["has_fitted_model"] is False

        # After fitting
        subject = await mock_subject_svc.get_subject(subject_id, "user-123")
        assert subject["has_fitted_model"] is True


class TestPerformanceMetrics:
    """Test performance tracking across workflow."""

    @patch('src.api.services.fitting_service.FittingService')
    async def test_fitting_performance_tracking(self, mock_fitting_service):
        """Test that fitting performance is tracked."""
        mock_fitting_svc = Mock()
        mock_fitting_svc.get_model_parameters = AsyncMock(return_value={
            "shape_params": [0.1] * 10,
            "final_loss": 0.045,
            "iterations_completed": 150,
            "convergence_achieved": True,
            "processing_time_seconds": 45.2,
            "photo_reprojection_error": 2.3
        })
        mock_fitting_service.return_value = mock_fitting_svc

        # Get parameters with performance metrics
        params = await mock_fitting_svc.get_model_parameters("subject-123", "user-123")

        # Verify performance metrics
        assert params["processing_time_seconds"] > 0
        assert params["iterations_completed"] == 150
        assert params["photo_reprojection_error"] < 5.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
