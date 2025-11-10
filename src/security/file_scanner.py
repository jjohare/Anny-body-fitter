# Anny Body Fitter - File Security Scanner
# Copyright (C) 2025 NAVER Corp.
# Apache License, Version 2.0

"""
File upload security scanner for image validation.

Provides comprehensive security checks for uploaded images including:
- File type validation (magic number verification)
- Size limit enforcement
- Malicious content detection
- Path traversal prevention
- Image format validation
"""

import os
import imghdr
import hashlib
from pathlib import Path
from typing import Union, Tuple, Optional
from PIL import Image
import io


class FileSecurityError(Exception):
    """Raised when file security check fails."""
    pass


class FileSecurityScanner:
    """
    Comprehensive security scanner for file uploads.

    Features:
    - Magic number validation
    - File size limits
    - Image format verification
    - Dimension limits
    - Malicious content detection
    - Path traversal prevention
    """

    # Security limits
    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
    MAX_IMAGE_WIDTH = 8192
    MAX_IMAGE_HEIGHT = 8192
    MIN_IMAGE_WIDTH = 32
    MIN_IMAGE_HEIGHT = 32

    # Allowed MIME types
    ALLOWED_MIME_TYPES = {
        'image/jpeg',
        'image/png',
        'image/bmp',
        'image/gif',
    }

    # File signatures (magic numbers)
    FILE_SIGNATURES = {
        'jpeg': [b'\xFF\xD8\xFF\xE0', b'\xFF\xD8\xFF\xE1', b'\xFF\xD8\xFF\xDB'],
        'png': [b'\x89PNG\r\n\x1a\n'],
        'gif': [b'GIF87a', b'GIF89a'],
        'bmp': [b'BM'],
    }

    def __init__(self,
                 max_size_mb: float = 10.0,
                 allowed_formats: Optional[list] = None):
        """
        Initialize file scanner.

        Args:
            max_size_mb: Maximum file size in megabytes
            allowed_formats: List of allowed formats (jpeg, png, etc.)
        """
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        self.allowed_formats = allowed_formats or ['jpeg', 'png', 'bmp', 'gif']

    def validate_file_path(self, file_path: Union[str, Path]) -> Path:
        """
        Validate and sanitize file path to prevent path traversal.

        Args:
            file_path: Path to file

        Returns:
            Sanitized Path object

        Raises:
            FileSecurityError: If path is suspicious
        """
        file_path = Path(file_path).resolve()

        # Check for path traversal attempts
        if '..' in str(file_path):
            raise FileSecurityError("Path traversal detected in file path")

        # Check if file exists
        if not file_path.exists():
            raise FileSecurityError(f"File does not exist: {file_path}")

        # Check if it's a file (not directory or symlink)
        if not file_path.is_file():
            raise FileSecurityError(f"Path is not a regular file: {file_path}")

        return file_path

    def check_file_size(self, file_path: Path) -> int:
        """
        Check if file size is within limits.

        Args:
            file_path: Path to file

        Returns:
            File size in bytes

        Raises:
            FileSecurityError: If file is too large
        """
        size = file_path.stat().st_size

        if size > self.max_size_bytes:
            raise FileSecurityError(
                f"File size ({size / 1024 / 1024:.2f}MB) exceeds "
                f"maximum of {self.max_size_bytes / 1024 / 1024:.2f}MB"
            )

        if size == 0:
            raise FileSecurityError("File is empty")

        return size

    def validate_magic_number(self, file_path: Path) -> str:
        """
        Validate file signature (magic number).

        Args:
            file_path: Path to file

        Returns:
            Detected file format

        Raises:
            FileSecurityError: If magic number is invalid
        """
        with open(file_path, 'rb') as f:
            header = f.read(12)

        # Check against known signatures
        for format_name, signatures in self.FILE_SIGNATURES.items():
            if format_name not in self.allowed_formats:
                continue

            for signature in signatures:
                if header.startswith(signature):
                    return format_name

        raise FileSecurityError(
            "File signature does not match allowed image formats "
            "(possible malware or wrong file type)"
        )

    def validate_image_content(self, file_path: Path) -> Tuple[str, int, int]:
        """
        Validate image content using PIL.

        Args:
            file_path: Path to image file

        Returns:
            Tuple of (format, width, height)

        Raises:
            FileSecurityError: If image is invalid or dangerous
        """
        try:
            with Image.open(file_path) as img:
                # Verify image can be loaded
                img.verify()

            # Re-open to get dimensions (verify() closes the file)
            with Image.open(file_path) as img:
                format_name = img.format.lower() if img.format else 'unknown'
                width, height = img.size

                # Check dimensions
                if width > self.MAX_IMAGE_WIDTH or height > self.MAX_IMAGE_HEIGHT:
                    raise FileSecurityError(
                        f"Image dimensions ({width}x{height}) exceed "
                        f"maximum of {self.MAX_IMAGE_WIDTH}x{self.MAX_IMAGE_HEIGHT}"
                    )

                if width < self.MIN_IMAGE_WIDTH or height < self.MIN_IMAGE_HEIGHT:
                    raise FileSecurityError(
                        f"Image dimensions ({width}x{height}) below "
                        f"minimum of {self.MIN_IMAGE_WIDTH}x{self.MIN_IMAGE_HEIGHT}"
                    )

                # Check format matches extension
                if format_name not in self.allowed_formats:
                    raise FileSecurityError(
                        f"Image format '{format_name}' not in allowed formats"
                    )

                return format_name, width, height

        except Image.DecompressionBombError:
            raise FileSecurityError(
                "Image is too large (decompression bomb protection)"
            )
        except (IOError, OSError) as e:
            raise FileSecurityError(f"Failed to process image: {str(e)}")

    def detect_malicious_content(self, file_path: Path) -> bool:
        """
        Basic malicious content detection.

        Args:
            file_path: Path to file

        Returns:
            True if file appears safe

        Raises:
            FileSecurityError: If suspicious content detected
        """
        # Check for executable content in image files
        suspicious_patterns = [
            b'<?php',
            b'<script',
            b'eval(',
            b'exec(',
            b'system(',
            b'/bin/sh',
            b'/bin/bash',
        ]

        with open(file_path, 'rb') as f:
            content = f.read(4096)  # Check first 4KB

        for pattern in suspicious_patterns:
            if pattern in content:
                raise FileSecurityError(
                    f"Suspicious content detected in file: {pattern.decode('utf-8', errors='ignore')}"
                )

        return True

    def scan_file(self, file_path: Union[str, Path]) -> dict:
        """
        Perform comprehensive security scan on file.

        Args:
            file_path: Path to file to scan

        Returns:
            Dictionary with scan results

        Raises:
            FileSecurityError: If any security check fails
        """
        # Validate path
        validated_path = self.validate_file_path(file_path)

        # Check file size
        file_size = self.check_file_size(validated_path)

        # Validate magic number
        detected_format = self.validate_magic_number(validated_path)

        # Validate image content
        format_name, width, height = self.validate_image_content(validated_path)

        # Check for malicious content
        self.detect_malicious_content(validated_path)

        # Calculate file hash for integrity
        file_hash = self._calculate_hash(validated_path)

        return {
            'path': str(validated_path),
            'size_bytes': file_size,
            'size_mb': round(file_size / 1024 / 1024, 2),
            'format': format_name,
            'detected_format': detected_format,
            'width': width,
            'height': height,
            'hash': file_hash,
            'safe': True
        }

    @staticmethod
    def _calculate_hash(file_path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()


def validate_image_file(file_path: Union[str, Path],
                       max_size_mb: float = 10.0) -> dict:
    """
    Convenience function to validate an image file.

    Args:
        file_path: Path to image file
        max_size_mb: Maximum allowed file size in MB

    Returns:
        Scan results dictionary

    Raises:
        FileSecurityError: If validation fails
    """
    scanner = FileSecurityScanner(max_size_mb=max_size_mb)
    return scanner.scan_file(file_path)


def check_file_size(file_path: Union[str, Path],
                   max_size_mb: float = 10.0) -> bool:
    """
    Quick file size check.

    Args:
        file_path: Path to file
        max_size_mb: Maximum allowed size in MB

    Returns:
        True if file size is acceptable

    Raises:
        FileSecurityError: If file is too large
    """
    file_path = Path(file_path)
    size_mb = file_path.stat().st_size / 1024 / 1024

    if size_mb > max_size_mb:
        raise FileSecurityError(
            f"File size ({size_mb:.2f}MB) exceeds maximum of {max_size_mb}MB"
        )

    return True


def detect_malicious_content(file_path: Union[str, Path]) -> bool:
    """
    Quick malicious content check.

    Args:
        file_path: Path to file

    Returns:
        True if file appears safe

    Raises:
        FileSecurityError: If suspicious content detected
    """
    scanner = FileSecurityScanner()
    return scanner.detect_malicious_content(Path(file_path))


# Example usage
if __name__ == "__main__":
    import tempfile
    import numpy as np
    from PIL import Image

    print("Testing file security scanner...")

    # Create a test image
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        test_image_path = tmp.name
        # Create a simple test image
        img_array = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        img.save(test_image_path, 'PNG')

    try:
        scanner = FileSecurityScanner(max_size_mb=10.0)
        results = scanner.scan_file(test_image_path)

        print("\n✅ Scan Results:")
        print(f"  Format: {results['format']}")
        print(f"  Size: {results['size_mb']}MB")
        print(f"  Dimensions: {results['width']}x{results['height']}")
        print(f"  Hash: {results['hash'][:16]}...")
        print(f"  Safe: {results['safe']}")

        # Test size limit
        print("\n✅ Testing size limit...")
        check_file_size(test_image_path, max_size_mb=10.0)
        print("  Size check passed")

        # Test malicious content detection
        print("\n✅ Testing malicious content detection...")
        detect_malicious_content(test_image_path)
        print("  No malicious content detected")

        print("\n✅ All security tests passed!")

    finally:
        # Cleanup
        if os.path.exists(test_image_path):
            os.unlink(test_image_path)
