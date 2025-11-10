"""
Tests for frontend components
"""
import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from frontend.components.photo_upload import validate_photos
from frontend.components.subject_form import validate_subject_info
from frontend.components.measurement_display import (
    format_measurements_table,
    calculate_measurement_statistics
)


class TestPhotoUpload:
    """Tests for photo upload component"""

    def test_validate_photos_empty(self):
        """Test validation with no photos"""
        is_valid, message = validate_photos([])
        assert not is_valid
        assert "at least one photo" in message.lower()

    def test_validate_photos_single(self):
        """Test validation with single photo"""
        is_valid, message = validate_photos(['photo1.jpg'])
        assert not is_valid
        assert "at least 2 photos" in message.lower()

    def test_validate_photos_valid(self):
        """Test validation with multiple photos"""
        photos = ['photo1.jpg', 'photo2.jpg', 'photo3.jpg']
        is_valid, message = validate_photos(photos)
        assert is_valid


class TestSubjectForm:
    """Tests for subject form component"""

    def test_validate_subject_info_missing_name(self):
        """Test validation with missing name"""
        is_valid, message = validate_subject_info("", "1990-01-01", "Male", 170, 70)
        assert not is_valid
        assert "name" in message.lower()

    def test_validate_subject_info_missing_dob(self):
        """Test validation with missing DOB"""
        is_valid, message = validate_subject_info("John", "", "Male", 170, 70)
        assert not is_valid
        assert "date of birth" in message.lower()

    def test_validate_subject_info_invalid_date_format(self):
        """Test validation with invalid date format"""
        is_valid, message = validate_subject_info("John", "01/01/1990", "Male", 170, 70)
        assert not is_valid
        assert "format" in message.lower()

    def test_validate_subject_info_invalid_height(self):
        """Test validation with invalid height"""
        is_valid, message = validate_subject_info("John", "1990-01-01", "Male", 10, 70)
        assert not is_valid
        assert "height" in message.lower()

    def test_validate_subject_info_invalid_weight(self):
        """Test validation with invalid weight"""
        is_valid, message = validate_subject_info("John", "1990-01-01", "Male", 170, 5)
        assert not is_valid
        assert "weight" in message.lower()

    def test_validate_subject_info_valid(self):
        """Test validation with valid data"""
        is_valid, message = validate_subject_info("John", "1990-01-01", "Male", 170, 70)
        assert is_valid


class TestMeasurementDisplay:
    """Tests for measurement display component"""

    def test_format_measurements_table_empty(self):
        """Test table formatting with empty measurements"""
        input_measurements = {}
        fitted_measurements = {}
        df = format_measurements_table(input_measurements, fitted_measurements)
        assert len(df) == 0

    def test_format_measurements_table_valid(self):
        """Test table formatting with valid measurements"""
        input_measurements = {"height": 170.0, "chest": 95.0}
        fitted_measurements = {"height": 171.0, "chest": 96.0}
        df = format_measurements_table(input_measurements, fitted_measurements)

        assert len(df) == 2
        assert "Measurement" in df.columns
        assert "Input (cm)" in df.columns
        assert "Fitted Model (cm)" in df.columns
        assert "Difference (cm)" in df.columns

    def test_calculate_measurement_statistics_empty(self):
        """Test statistics calculation with empty measurements"""
        stats = calculate_measurement_statistics({}, {})
        assert stats["average_error"] == 0.0
        assert stats["max_error"] == 0.0
        assert stats["accuracy"] == 0.0

    def test_calculate_measurement_statistics_valid(self):
        """Test statistics calculation with valid measurements"""
        input_measurements = {"height": 170.0, "chest": 95.0}
        fitted_measurements = {"height": 171.0, "chest": 96.0}
        stats = calculate_measurement_statistics(input_measurements, fitted_measurements)

        assert stats["average_error"] > 0
        assert stats["max_error"] >= stats["average_error"]
        assert 0 <= stats["accuracy"] <= 100


class TestStateManager:
    """Tests for state manager"""

    def test_create_session(self):
        """Test session creation"""
        from frontend.utils.state_manager import StateManager

        manager = StateManager()
        session = manager.create_session("test_session")

        assert session.session_id == "test_session"
        assert session.status == "initialized"
        assert session.progress == 0.0

    def test_update_session(self):
        """Test session update"""
        from frontend.utils.state_manager import StateManager

        manager = StateManager()
        session = manager.create_session("test_session")

        updated = manager.update_session(
            status="processing",
            progress=0.5
        )

        assert updated.status == "processing"
        assert updated.progress == 0.5

    def test_get_session(self):
        """Test session retrieval"""
        from frontend.utils.state_manager import StateManager

        manager = StateManager()
        manager.create_session("test_session")

        retrieved = manager.get_session("test_session")
        assert retrieved is not None
        assert retrieved.session_id == "test_session"

    def test_clear_session(self):
        """Test session clearing"""
        from frontend.utils.state_manager import StateManager

        manager = StateManager()
        manager.create_session("test_session")
        manager.clear_session("test_session")

        retrieved = manager.get_session("test_session")
        assert retrieved is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
