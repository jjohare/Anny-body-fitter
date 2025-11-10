"""Tests for model fitting endpoints."""

import pytest
from fastapi import status
import json


class TestFittingEndpoints:
    """Test suite for fitting endpoints."""

    def test_upload_photos(self, client, sample_subject_data, sample_photo_metadata, temp_photo):
        """Test uploading photos for a subject."""
        # Create subject first
        create_response = client.post("/api/v1/subjects", json=sample_subject_data)
        subject_id = create_response.json()["id"]

        # Upload photo
        files = {"files": ("test.jpg", temp_photo, "image/jpeg")}
        data = {"metadata": json.dumps(sample_photo_metadata)}

        response = client.post(
            f"/api/v1/subjects/{subject_id}/photos",
            files=files,
            data=data
        )

        assert response.status_code == status.HTTP_201_CREATED
        photos = response.json()

        assert len(photos) == 1
        assert photos[0]["subject_id"] == subject_id
        assert photos[0]["photo_type"] == "front"
        assert photos[0]["width_px"] == 100
        assert photos[0]["height_px"] == 100

    def test_upload_photos_invalid_file_type(self, client, sample_subject_data):
        """Test uploading invalid file type."""
        # Create subject
        create_response = client.post("/api/v1/subjects", json=sample_subject_data)
        subject_id = create_response.json()["id"]

        # Try to upload invalid file
        files = {"files": ("test.txt", b"not an image", "text/plain")}
        data = {"metadata": json.dumps([{"photo_type": "front"}])}

        response = client.post(
            f"/api/v1/subjects/{subject_id}/photos",
            files=files,
            data=data
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_upload_photos_metadata_mismatch(self, client, sample_subject_data, temp_photo):
        """Test uploading with mismatched metadata count."""
        # Create subject
        create_response = client.post("/api/v1/subjects", json=sample_subject_data)
        subject_id = create_response.json()["id"]

        # Upload with wrong metadata count
        files = {"files": ("test.jpg", temp_photo, "image/jpeg")}
        data = {"metadata": json.dumps([])}  # Empty metadata

        response = client.post(
            f"/api/v1/subjects/{subject_id}/photos",
            files=files,
            data=data
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_subject_photos(self, client, sample_subject_data, sample_photo_metadata, temp_photo):
        """Test listing photos for a subject."""
        # Create subject and upload photo
        create_response = client.post("/api/v1/subjects", json=sample_subject_data)
        subject_id = create_response.json()["id"]

        files = {"files": ("test.jpg", temp_photo, "image/jpeg")}
        data = {"metadata": json.dumps(sample_photo_metadata)}
        client.post(f"/api/v1/subjects/{subject_id}/photos", files=files, data=data)

        # List photos
        response = client.get(f"/api/v1/subjects/{subject_id}/photos")

        assert response.status_code == status.HTTP_200_OK
        photos = response.json()
        assert len(photos) == 1
        assert photos[0]["subject_id"] == subject_id

    def test_fit_model_without_photos(self, client, sample_subject_data, sample_fitting_request):
        """Test triggering fit without uploading photos first."""
        # Create subject without photos
        create_response = client.post("/api/v1/subjects", json=sample_subject_data)
        subject_id = create_response.json()["id"]

        # Try to fit model
        response = client.post(
            f"/api/v1/subjects/{subject_id}/fit",
            json=sample_fitting_request
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "photo" in response.json()["detail"].lower()

    def test_fit_model_with_photos(
        self,
        client,
        sample_subject_data,
        sample_photo_metadata,
        temp_photo,
        sample_fitting_request
    ):
        """Test triggering model fitting with photos."""
        # Create subject and upload photo
        create_response = client.post("/api/v1/subjects", json=sample_subject_data)
        subject_id = create_response.json()["id"]

        files = {"files": ("test.jpg", temp_photo, "image/jpeg")}
        data = {"metadata": json.dumps(sample_photo_metadata)}
        client.post(f"/api/v1/subjects/{subject_id}/photos", files=files, data=data)

        # Trigger fitting
        response = client.post(
            f"/api/v1/subjects/{subject_id}/fit",
            json=sample_fitting_request
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        fitting_data = response.json()

        assert fitting_data["subject_id"] == subject_id
        assert fitting_data["status"] in ["pending", "processing"]
        assert "task_id" in fitting_data

    def test_get_fitting_status(
        self,
        client,
        sample_subject_data,
        sample_photo_metadata,
        temp_photo,
        sample_fitting_request
    ):
        """Test checking fitting status."""
        # Create subject, upload photo, start fitting
        create_response = client.post("/api/v1/subjects", json=sample_subject_data)
        subject_id = create_response.json()["id"]

        files = {"files": ("test.jpg", temp_photo, "image/jpeg")}
        data = {"metadata": json.dumps(sample_photo_metadata)}
        client.post(f"/api/v1/subjects/{subject_id}/photos", files=files, data=data)

        client.post(f"/api/v1/subjects/{subject_id}/fit", json=sample_fitting_request)

        # Check status
        response = client.get(f"/api/v1/subjects/{subject_id}/fit/status")

        assert response.status_code == status.HTTP_200_OK
        status_data = response.json()

        assert "status" in status_data
        assert "progress" in status_data
        assert 0 <= status_data["progress"] <= 100

    def test_get_fitting_status_no_task(self, client, sample_subject_data):
        """Test getting status when no fitting has been started."""
        # Create subject without fitting
        create_response = client.post("/api/v1/subjects", json=sample_subject_data)
        subject_id = create_response.json()["id"]

        # Try to get status
        response = client.get(f"/api/v1/subjects/{subject_id}/fit/status")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_fitted_model_not_available(self, client, sample_subject_data):
        """Test getting model when fitting hasn't completed."""
        # Create subject without fitting
        create_response = client.post("/api/v1/subjects", json=sample_subject_data)
        subject_id = create_response.json()["id"]

        # Try to get model
        response = client.get(f"/api/v1/subjects/{subject_id}/model")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "fitted model" in response.json()["detail"].lower()
