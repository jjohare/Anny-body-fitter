# Anny Body Fitter - Security Module
# Copyright (C) 2025 NAVER Corp.
# Apache License, Version 2.0

"""
Security module for Anny Body Fitter application.

Provides encryption, validation, and secure file handling for protecting
user privacy and preventing security vulnerabilities.

Modules:
    - encryption: Field-level encryption for PII data
    - validators: Input validation and sanitization
    - file_scanner: Secure file upload handling
    - temp_storage: Temporary file management with auto-deletion
    - auth: Authentication and authorization utilities
"""

from .encryption import (
    FieldEncryption,
    encrypt_pii_field,
    decrypt_pii_field,
    generate_encryption_key,
)

from .validators import (
    InputValidator,
    sanitize_input,
    validate_age,
    validate_measurements,
    validate_file_upload,
)

from .file_scanner import (
    FileSecurityScanner,
    validate_image_file,
    check_file_size,
    detect_malicious_content,
)

from .temp_storage import (
    TemporaryPhotoStorage,
    secure_delete_file,
    cleanup_expired_files,
)

__all__ = [
    # Encryption
    'FieldEncryption',
    'encrypt_pii_field',
    'decrypt_pii_field',
    'generate_encryption_key',

    # Validation
    'InputValidator',
    'sanitize_input',
    'validate_age',
    'validate_measurements',
    'validate_file_upload',

    # File Security
    'FileSecurityScanner',
    'validate_image_file',
    'check_file_size',
    'detect_malicious_content',

    # Temporary Storage
    'TemporaryPhotoStorage',
    'secure_delete_file',
    'cleanup_expired_files',
]

__version__ = '1.0.0'
