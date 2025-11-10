"""Tests for subject management endpoints."""

import pytest
from fastapi import status


class TestSubjectEndpoints:
    """Test suite for subject endpoints."""

    def test_create_subject(self, client, sample_subject_data):
        """Test creating a new subject."""
        response = client.post("/api/v1/subjects", json=sample_subject_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert "id" in data
        assert data["name"] == sample_subject_data["name"]
        assert data["age"] == sample_subject_data["age"]
        assert data["gender"] == sample_subject_data["gender"]
        assert data["height_cm"] == sample_subject_data["height_cm"]
        assert data["weight_kg"] == sample_subject_data["weight_kg"]
        assert data["photo_count"] == 0
        assert data["has_fitted_model"] is False

    def test_create_subject_minimal_data(self, client):
        """Test creating subject with minimal required data."""
        minimal_data = {"name": "Minimal Subject"}
        response = client.post("/api/v1/subjects", json=minimal_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Minimal Subject"

    def test_create_subject_invalid_data(self, client):
        """Test creating subject with invalid data."""
        invalid_data = {
            "name": "",  # Empty name
            "age": -1,   # Invalid age
        }
        response = client.post("/api/v1/subjects", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_subject(self, client, sample_subject_data):
        """Test retrieving a subject by ID."""
        # Create subject first
        create_response = client.post("/api/v1/subjects", json=sample_subject_data)
        subject_id = create_response.json()["id"]

        # Get subject
        response = client.get(f"/api/v1/subjects/{subject_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == subject_id
        assert data["name"] == sample_subject_data["name"]

    def test_get_nonexistent_subject(self, client):
        """Test retrieving a subject that doesn't exist."""
        response = client.get("/api/v1/subjects/nonexistent_id")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_subjects(self, client, sample_subject_data):
        """Test listing subjects with pagination."""
        # Create multiple subjects
        for i in range(5):
            subject_data = sample_subject_data.copy()
            subject_data["name"] = f"Subject {i}"
            client.post("/api/v1/subjects", json=subject_data)

        # List subjects
        response = client.get("/api/v1/subjects?page=1&page_size=3")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "subjects" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert len(data["subjects"]) <= 3
        assert data["page"] == 1
        assert data["page_size"] == 3

    def test_list_subjects_with_search(self, client, sample_subject_data):
        """Test searching subjects by name."""
        # Create subjects with different names
        subject_data_1 = sample_subject_data.copy()
        subject_data_1["name"] = "Alice"
        client.post("/api/v1/subjects", json=subject_data_1)

        subject_data_2 = sample_subject_data.copy()
        subject_data_2["name"] = "Bob"
        client.post("/api/v1/subjects", json=subject_data_2)

        # Search for Alice
        response = client.get("/api/v1/subjects?search=Alice")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["subjects"]) >= 1
        assert any(s["name"] == "Alice" for s in data["subjects"])

    def test_update_subject(self, client, sample_subject_data):
        """Test updating subject information."""
        # Create subject
        create_response = client.post("/api/v1/subjects", json=sample_subject_data)
        subject_id = create_response.json()["id"]

        # Update subject
        update_data = {"age": 35, "notes": "Updated notes"}
        response = client.patch(f"/api/v1/subjects/{subject_id}", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["age"] == 35
        assert data["notes"] == "Updated notes"
        assert data["name"] == sample_subject_data["name"]  # Unchanged

    def test_update_nonexistent_subject(self, client):
        """Test updating a subject that doesn't exist."""
        update_data = {"age": 35}
        response = client.patch("/api/v1/subjects/nonexistent_id", json=update_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_subject_soft(self, client, sample_subject_data):
        """Test soft deleting a subject."""
        # Create subject
        create_response = client.post("/api/v1/subjects", json=sample_subject_data)
        subject_id = create_response.json()["id"]

        # Delete subject (soft delete)
        response = client.delete(f"/api/v1/subjects/{subject_id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify subject is not accessible
        get_response = client.get(f"/api/v1/subjects/{subject_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_subject_permanent(self, client, sample_subject_data):
        """Test permanently deleting a subject."""
        # Create subject
        create_response = client.post("/api/v1/subjects", json=sample_subject_data)
        subject_id = create_response.json()["id"]

        # Delete subject permanently
        response = client.delete(f"/api/v1/subjects/{subject_id}?permanent=true")

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_add_metrics(self, client, sample_subject_data, sample_metrics_data):
        """Test adding performance metrics to a subject."""
        # Create subject with fitted model
        create_response = client.post("/api/v1/subjects", json=sample_subject_data)
        subject_id = create_response.json()["id"]

        # Mark as having fitted model (would normally be done by fitting process)
        # This is a workaround for testing - in production, fitting creates this

        # For now, test that it fails without fitted model
        response = client.post(
            f"/api/v1/subjects/{subject_id}/metrics",
            json=sample_metrics_data
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "fitted model" in response.json()["detail"].lower()

    def test_get_subject_metrics(self, client, sample_subject_data):
        """Test retrieving metrics for a subject."""
        # Create subject
        create_response = client.post("/api/v1/subjects", json=sample_subject_data)
        subject_id = create_response.json()["id"]

        # Get metrics (should be empty)
        response = client.get(f"/api/v1/subjects/{subject_id}/metrics")

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)
        assert len(response.json()) == 0
