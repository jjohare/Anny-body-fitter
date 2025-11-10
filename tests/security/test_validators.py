# Anny Body Fitter - Validation Tests
# Copyright (C) 2025 NAVER Corp.
# Apache License, Version 2.0

"""
Security tests for input validation module.
"""

import pytest
from datetime import date, datetime
from pathlib import Path
import tempfile
from PIL import Image
import numpy as np

from src.security.validators import (
    InputValidator,
    ValidationError,
    sanitize_input,
    validate_file_upload,
    validate_measurements
)


class TestAgeValidation:
    """Test age validation."""

    def test_valid_age(self):
        """Test valid age values."""
        validator = InputValidator()
        assert validator.validate_age(25) == 25
        assert validator.validate_age(0) == 0
        assert validator.validate_age(120) == 120
        assert validator.validate_age("30") == 30
        assert validator.validate_age(50.5) == 50

    def test_invalid_age(self):
        """Test invalid age values."""
        validator = InputValidator()

        with pytest.raises(ValidationError):
            validator.validate_age(-1)

        with pytest.raises(ValidationError):
            validator.validate_age(121)

        with pytest.raises(ValidationError):
            validator.validate_age("invalid")

        with pytest.raises(ValidationError):
            validator.validate_age(None)


class TestDateOfBirthValidation:
    """Test date of birth validation."""

    def test_valid_dob(self):
        """Test valid date of birth."""
        validator = InputValidator()

        # String format
        dob = validator.validate_date_of_birth("1990-01-15")
        assert isinstance(dob, date)
        assert dob.year == 1990

        # Date object
        dob_obj = date(1990, 1, 15)
        assert validator.validate_date_of_birth(dob_obj) == dob_obj

        # Datetime object
        dt = datetime(1990, 1, 15, 12, 30)
        assert validator.validate_date_of_birth(dt) == dob_obj

    def test_future_date_rejected(self):
        """Test that future dates are rejected."""
        validator = InputValidator()

        future_date = "2030-01-01"
        with pytest.raises(ValidationError, match="cannot be in the future"):
            validator.validate_date_of_birth(future_date)

    def test_too_old_rejected(self):
        """Test that unreasonably old dates are rejected."""
        validator = InputValidator()

        old_date = "1800-01-01"
        with pytest.raises(ValidationError, match="exceeds maximum"):
            validator.validate_date_of_birth(old_date)

    def test_invalid_format(self):
        """Test invalid date formats."""
        validator = InputValidator()

        with pytest.raises(ValidationError, match="Invalid date format"):
            validator.validate_date_of_birth("01/15/1990")

        with pytest.raises(ValidationError):
            validator.validate_date_of_birth("invalid")


class TestMeasurementValidation:
    """Test physical measurement validation."""

    def test_valid_height(self):
        """Test valid height values."""
        validator = InputValidator()

        assert validator.validate_height(175.5, unit='cm') == 175.5
        assert validator.validate_height(1.755, unit='m') == 175.5
        assert validator.validate_height("180", unit='cm') == 180.0

    def test_invalid_height(self):
        """Test invalid height values."""
        validator = InputValidator()

        with pytest.raises(ValidationError):
            validator.validate_height(20, unit='cm')  # Too short

        with pytest.raises(ValidationError):
            validator.validate_height(400, unit='cm')  # Too tall

        with pytest.raises(ValidationError):
            validator.validate_height(175, unit='invalid')  # Invalid unit

    def test_valid_weight(self):
        """Test valid weight values."""
        validator = InputValidator()

        assert validator.validate_weight(70.5, unit='kg') == 70.5
        assert validator.validate_weight(155.0, unit='lb') == pytest.approx(70.31, rel=0.01)
        assert validator.validate_weight("80", unit='kg') == 80.0

    def test_invalid_weight(self):
        """Test invalid weight values."""
        validator = InputValidator()

        with pytest.raises(ValidationError):
            validator.validate_weight(0.5, unit='kg')  # Too light

        with pytest.raises(ValidationError):
            validator.validate_weight(600, unit='kg')  # Too heavy

    def test_generic_measurement(self):
        """Test generic measurement validation."""
        validator = InputValidator()

        val = validator.validate_measurement(95.5, min_val=50, max_val=150, name="chest")
        assert val == 95.5

        with pytest.raises(ValidationError, match="chest"):
            validator.validate_measurement(200, min_val=50, max_val=150, name="chest")


class TestPhenotypeValidation:
    """Test phenotype parameter validation."""

    def test_valid_phenotype(self):
        """Test valid phenotype parameters."""
        validator = InputValidator()

        assert validator.validate_phenotype_parameter(0.5) == 0.5
        assert validator.validate_phenotype_parameter(0.0) == 0.0
        assert validator.validate_phenotype_parameter(1.0) == 1.0
        assert validator.validate_phenotype_parameter("0.75") == 0.75

    def test_invalid_phenotype(self):
        """Test invalid phenotype parameters."""
        validator = InputValidator()

        with pytest.raises(ValidationError):
            validator.validate_phenotype_parameter(-0.5)

        with pytest.raises(ValidationError):
            validator.validate_phenotype_parameter(1.5)

    def test_phenotype_extrapolation(self):
        """Test phenotype with extrapolation allowed."""
        validator = InputValidator()

        # With extrapolation
        assert validator.validate_phenotype_parameter(-0.2, allow_extrapolation=True) == -0.2
        assert validator.validate_phenotype_parameter(1.2, allow_extrapolation=True) == 1.2

        # Out of extrapolation bounds
        with pytest.raises(ValidationError):
            validator.validate_phenotype_parameter(-0.5, allow_extrapolation=True)

        with pytest.raises(ValidationError):
            validator.validate_phenotype_parameter(1.5, allow_extrapolation=True)


class TestInputSanitization:
    """Test input sanitization."""

    def test_basic_sanitization(self):
        """Test basic text sanitization."""
        clean = sanitize_input("Hello World")
        assert clean == "Hello World"

    def test_html_escaping(self):
        """Test HTML escaping."""
        dirty = '<script>alert("xss")</script>'
        clean = sanitize_input(dirty)
        assert '<script>' not in clean
        assert '&lt;script&gt;' in clean

    def test_length_limit(self):
        """Test length limitation."""
        long_text = "A" * 2000
        with pytest.raises(ValidationError, match="exceeds maximum length"):
            sanitize_input(long_text, max_length=1000)

    def test_null_byte_removal(self):
        """Test null byte removal."""
        text_with_null = "Hello\x00World"
        clean = sanitize_input(text_with_null)
        assert '\x00' not in clean
        assert clean == "HelloWorld"

    def test_control_character_removal(self):
        """Test control character removal."""
        text = "Hello\x01\x02World\n\tTest"
        clean = sanitize_input(text)
        assert '\x01' not in clean
        assert '\x02' not in clean
        assert '\n' in clean  # Newlines preserved
        assert '\t' in clean  # Tabs preserved

    def test_allow_html(self):
        """Test allowing HTML (but escaped)."""
        html = '<b>Bold</b> text'
        clean = sanitize_input(html, allow_html=True)
        # HTML should be escaped even when allowed
        assert '<' not in clean or '&lt;' in clean


class TestFileUploadValidation:
    """Test file upload validation."""

    def setup_method(self):
        """Create test files."""
        # Create valid image
        self.valid_image = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        img = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))
        img.save(self.valid_image.name, 'PNG')
        self.valid_image.close()

        # Create invalid file (text file with .png extension)
        self.invalid_image = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        self.invalid_image.write(b"This is not an image")
        self.invalid_image.close()

    def teardown_method(self):
        """Clean up test files."""
        Path(self.valid_image.name).unlink(missing_ok=True)
        Path(self.invalid_image.name).unlink(missing_ok=True)

    def test_valid_file(self):
        """Test validation of valid image file."""
        assert validate_file_upload(self.valid_image.name) is True

    def test_invalid_extension(self):
        """Test rejection of invalid extension."""
        invalid = tempfile.NamedTemporaryFile(suffix='.exe', delete=False)
        try:
            with pytest.raises(ValidationError, match="Invalid file extension"):
                validate_file_upload(invalid.name)
        finally:
            Path(invalid.name).unlink()

    def test_magic_number_mismatch(self):
        """Test rejection when magic number doesn't match extension."""
        with pytest.raises(ValidationError, match="does not match extension"):
            validate_file_upload(self.invalid_image.name, check_content=True)

    def test_file_size_limit(self):
        """Test file size limit enforcement."""
        # Create large file
        large_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        large_file.write(b'\x00' * (11 * 1024 * 1024))  # 11 MB
        large_file.close()

        try:
            with pytest.raises(ValidationError, match="exceeds maximum"):
                validate_file_upload(large_file.name)
        finally:
            Path(large_file.name).unlink()

    def test_nonexistent_file(self):
        """Test rejection of nonexistent file."""
        with pytest.raises(ValidationError, match="does not exist"):
            validate_file_upload("/nonexistent/file.png")


class TestMeasurementsValidation:
    """Test measurements dictionary validation."""

    def test_valid_measurements(self):
        """Test validation of valid measurements."""
        measurements = {
            'height': 175.5,
            'weight': 70.2,
            'age': 30,
            'chest_circumference': 95.0
        }

        validated = validate_measurements(measurements)
        assert validated['height'] == 175.5
        assert validated['weight'] == 70.2
        assert validated['age'] == 30
        assert validated['chest_circumference'] == 95.0

    def test_invalid_measurements(self):
        """Test rejection of invalid measurements."""
        measurements = {
            'height': 500,  # Too tall
            'weight': 70.2
        }

        with pytest.raises(ValidationError):
            validate_measurements(measurements)

    def test_partial_measurements(self):
        """Test validation with only some fields."""
        measurements = {'height': 175.5}
        validated = validate_measurements(measurements)
        assert 'height' in validated
        assert 'weight' not in validated

    def test_dob_in_measurements(self):
        """Test date of birth validation in measurements."""
        measurements = {
            'dob': '1990-01-15',
            'height': 175.5
        }

        validated = validate_measurements(measurements)
        assert isinstance(validated['dob'], date)


class TestSecurityValidation:
    """Security-focused validation tests."""

    def test_sql_injection_prevention(self):
        """Test that SQL injection attempts are sanitized."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM passwords--"
        ]

        for malicious in malicious_inputs:
            clean = sanitize_input(malicious)
            # Should be escaped
            assert "'" not in clean or "&#x27;" in clean

    def test_xss_prevention(self):
        """Test XSS attack prevention."""
        xss_attempts = [
            '<script>alert("xss")</script>',
            '<img src=x onerror=alert(1)>',
            '<iframe src="javascript:alert(1)">',
            'javascript:alert(document.cookie)'
        ]

        for xss in xss_attempts:
            clean = sanitize_input(xss)
            assert '<script>' not in clean
            assert '<img' not in clean
            assert '<iframe' not in clean

    def test_path_traversal_prevention(self):
        """Test path traversal prevention in filenames."""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "/etc/shadow",
            "C:\\Windows\\System32"
        ]

        for path in malicious_paths:
            with pytest.raises((ValidationError, FileNotFoundError)):
                validate_file_upload(path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
