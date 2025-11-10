# Anny Body Fitter - Input Validation Module
# Copyright (C) 2025 NAVER Corp.
# Apache License, Version 2.0

"""
Input validation and sanitization for security.

Prevents injection attacks, validates data types and ranges,
and sanitizes user inputs to prevent security vulnerabilities.
"""

import re
import html
from typing import Union, Optional, Any
from datetime import datetime, date
from pathlib import Path


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


class InputValidator:
    """
    Comprehensive input validation for Anny Body Fitter.

    Validates:
    - Age and date of birth
    - Physical measurements
    - File uploads
    - Text inputs
    - Numeric ranges
    """

    # Validation constants
    MIN_AGE = 0
    MAX_AGE = 120
    MIN_HEIGHT_CM = 30.0  # Newborn minimum
    MAX_HEIGHT_CM = 300.0  # Extremely tall
    MIN_WEIGHT_KG = 1.0   # Newborn minimum
    MAX_WEIGHT_KG = 500.0  # Extremely heavy

    ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
    MAX_FILE_SIZE_MB = 10

    @staticmethod
    def validate_age(age: Union[int, float, str]) -> int:
        """
        Validate age value.

        Args:
            age: Age in years

        Returns:
            Validated age as integer

        Raises:
            ValidationError: If age is invalid
        """
        try:
            age_int = int(float(age))
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid age format: {age}")

        if not (InputValidator.MIN_AGE <= age_int <= InputValidator.MAX_AGE):
            raise ValidationError(
                f"Age must be between {InputValidator.MIN_AGE} "
                f"and {InputValidator.MAX_AGE} years"
            )

        return age_int

    @staticmethod
    def validate_date_of_birth(dob: Union[str, date, datetime]) -> date:
        """
        Validate date of birth.

        Args:
            dob: Date of birth (ISO format string or date object)

        Returns:
            Validated date object

        Raises:
            ValidationError: If date is invalid
        """
        if isinstance(dob, datetime):
            dob = dob.date()
        elif isinstance(dob, str):
            try:
                dob = datetime.fromisoformat(dob).date()
            except ValueError:
                raise ValidationError(f"Invalid date format: {dob}. Use YYYY-MM-DD")
        elif not isinstance(dob, date):
            raise ValidationError(f"Invalid date type: {type(dob)}")

        # Check if date is in the future
        if dob > date.today():
            raise ValidationError("Date of birth cannot be in the future")

        # Check if age is reasonable
        age_years = (date.today() - dob).days / 365.25
        if age_years > InputValidator.MAX_AGE:
            raise ValidationError(f"Age exceeds maximum of {InputValidator.MAX_AGE} years")

        return dob

    @staticmethod
    def validate_height(height: Union[float, int, str], unit: str = 'cm') -> float:
        """
        Validate height measurement.

        Args:
            height: Height value
            unit: Unit of measurement ('cm' or 'm')

        Returns:
            Height in centimeters

        Raises:
            ValidationError: If height is invalid
        """
        try:
            height_val = float(height)
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid height format: {height}")

        # Convert to cm if needed
        if unit == 'm':
            height_val *= 100
        elif unit != 'cm':
            raise ValidationError(f"Invalid height unit: {unit}. Use 'cm' or 'm'")

        if not (InputValidator.MIN_HEIGHT_CM <= height_val <= InputValidator.MAX_HEIGHT_CM):
            raise ValidationError(
                f"Height must be between {InputValidator.MIN_HEIGHT_CM}cm "
                f"and {InputValidator.MAX_HEIGHT_CM}cm"
            )

        return round(height_val, 2)

    @staticmethod
    def validate_weight(weight: Union[float, int, str], unit: str = 'kg') -> float:
        """
        Validate weight measurement.

        Args:
            weight: Weight value
            unit: Unit of measurement ('kg' or 'lb')

        Returns:
            Weight in kilograms

        Raises:
            ValidationError: If weight is invalid
        """
        try:
            weight_val = float(weight)
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid weight format: {weight}")

        # Convert to kg if needed
        if unit == 'lb':
            weight_val *= 0.453592
        elif unit != 'kg':
            raise ValidationError(f"Invalid weight unit: {unit}. Use 'kg' or 'lb'")

        if not (InputValidator.MIN_WEIGHT_KG <= weight_val <= InputValidator.MAX_WEIGHT_KG):
            raise ValidationError(
                f"Weight must be between {InputValidator.MIN_WEIGHT_KG}kg "
                f"and {InputValidator.MAX_WEIGHT_KG}kg"
            )

        return round(weight_val, 2)

    @staticmethod
    def validate_measurement(value: Union[float, int, str],
                           min_val: float = 0.0,
                           max_val: float = 1000.0,
                           name: str = "measurement") -> float:
        """
        Validate generic measurement value.

        Args:
            value: Measurement value
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            name: Name of measurement for error messages

        Returns:
            Validated measurement

        Raises:
            ValidationError: If measurement is invalid
        """
        try:
            val = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid {name} format: {value}")

        if not (min_val <= val <= max_val):
            raise ValidationError(
                f"{name} must be between {min_val} and {max_val}"
            )

        return round(val, 2)

    @staticmethod
    def validate_phenotype_parameter(value: Union[float, str],
                                     allow_extrapolation: bool = False) -> float:
        """
        Validate phenotype parameter (0.0 to 1.0 range).

        Args:
            value: Phenotype parameter value
            allow_extrapolation: Allow values outside [0, 1] range

        Returns:
            Validated parameter value

        Raises:
            ValidationError: If parameter is invalid
        """
        try:
            val = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid phenotype parameter: {value}")

        if allow_extrapolation:
            min_val, max_val = -0.3, 1.3
        else:
            min_val, max_val = 0.0, 1.0

        if not (min_val <= val <= max_val):
            raise ValidationError(
                f"Phenotype parameter must be between {min_val} and {max_val}"
            )

        return val


def sanitize_input(text: str,
                   max_length: int = 1000,
                   allow_html: bool = False) -> str:
    """
    Sanitize text input to prevent injection attacks.

    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        allow_html: Whether to allow HTML (escaped)

    Returns:
        Sanitized text

    Raises:
        ValidationError: If input is invalid
    """
    if not isinstance(text, str):
        raise ValidationError(f"Input must be string, got {type(text)}")

    # Check length
    if len(text) > max_length:
        raise ValidationError(f"Input exceeds maximum length of {max_length}")

    # Remove null bytes
    text = text.replace('\x00', '')

    # HTML escape if not allowing HTML
    if not allow_html:
        text = html.escape(text)

    # Remove control characters except newlines and tabs
    text = ''.join(char for char in text
                   if char.isprintable() or char in '\n\t')

    return text.strip()


def validate_file_upload(file_path: Union[str, Path],
                        check_content: bool = True) -> bool:
    """
    Validate file upload for security.

    Args:
        file_path: Path to uploaded file
        check_content: Whether to check file content (magic numbers)

    Returns:
        True if file is valid

    Raises:
        ValidationError: If file is invalid or dangerous
    """
    file_path = Path(file_path)

    # Check if file exists
    if not file_path.exists():
        raise ValidationError(f"File does not exist: {file_path}")

    # Check file extension
    if file_path.suffix.lower() not in InputValidator.ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            f"Invalid file extension: {file_path.suffix}. "
            f"Allowed: {InputValidator.ALLOWED_IMAGE_EXTENSIONS}"
        )

    # Check file size
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    if file_size_mb > InputValidator.MAX_FILE_SIZE_MB:
        raise ValidationError(
            f"File size ({file_size_mb:.2f}MB) exceeds maximum "
            f"of {InputValidator.MAX_FILE_SIZE_MB}MB"
        )

    # Check magic numbers (file signatures) if requested
    if check_content:
        with open(file_path, 'rb') as f:
            header = f.read(12)

        # Common image file signatures
        valid_signatures = [
            b'\xFF\xD8\xFF',  # JPEG
            b'\x89PNG\r\n\x1a\n',  # PNG
            b'GIF87a',  # GIF87a
            b'GIF89a',  # GIF89a
            b'BM',  # BMP
        ]

        if not any(header.startswith(sig) for sig in valid_signatures):
            raise ValidationError(
                "File content does not match extension (possible malware)"
            )

    return True


def validate_measurements(measurements: dict) -> dict:
    """
    Validate a dictionary of body measurements.

    Args:
        measurements: Dictionary of measurements

    Returns:
        Validated measurements dictionary

    Raises:
        ValidationError: If any measurement is invalid
    """
    validated = {}
    validator = InputValidator()

    # Required fields
    if 'height' in measurements:
        validated['height'] = validator.validate_height(measurements['height'])

    if 'weight' in measurements:
        validated['weight'] = validator.validate_weight(measurements['weight'])

    if 'age' in measurements:
        validated['age'] = validator.validate_age(measurements['age'])

    if 'dob' in measurements:
        validated['dob'] = validator.validate_date_of_birth(measurements['dob'])

    # Optional measurements
    measurement_fields = {
        'chest_circumference': (50.0, 200.0),
        'waist_circumference': (40.0, 200.0),
        'hip_circumference': (50.0, 200.0),
        'inseam': (30.0, 120.0),
        'shoulder_width': (20.0, 80.0),
    }

    for field, (min_val, max_val) in measurement_fields.items():
        if field in measurements:
            validated[field] = validator.validate_measurement(
                measurements[field],
                min_val=min_val,
                max_val=max_val,
                name=field
            )

    return validated


# Example usage
if __name__ == "__main__":
    validator = InputValidator()

    print("Testing input validation...")

    # Test age validation
    try:
        age = validator.validate_age(25)
        print(f"✅ Valid age: {age}")
    except ValidationError as e:
        print(f"❌ {e}")

    # Test invalid age
    try:
        validator.validate_age(150)
    except ValidationError as e:
        print(f"✅ Caught invalid age: {e}")

    # Test height validation
    height = validator.validate_height(175.5, unit='cm')
    print(f"✅ Valid height: {height}cm")

    # Test measurements
    test_measurements = {
        'height': 175.5,
        'weight': 70.2,
        'age': 30,
        'chest_circumference': 95.0
    }

    validated = validate_measurements(test_measurements)
    print(f"✅ Validated measurements: {validated}")

    # Test sanitization
    dirty_input = '<script>alert("xss")</script>Hello'
    clean_input = sanitize_input(dirty_input)
    print(f"✅ Sanitized: {clean_input}")

    print("\n✅ All validation tests passed!")
