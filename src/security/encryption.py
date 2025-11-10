# Anny Body Fitter - Encryption Module
# Copyright (C) 2025 NAVER Corp.
# Apache License, Version 2.0

"""
Encryption utilities for protecting PII (Personally Identifiable Information).

Provides field-level encryption for sensitive data like date of birth,
measurements, and other personal information using AES-256-GCM.
"""

import os
import base64
import hashlib
from typing import Union, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import secrets


class FieldEncryption:
    """
    Field-level encryption for PII data using AES-256-GCM.

    Features:
    - AES-256-GCM authenticated encryption
    - Unique nonce for each encryption operation
    - Key derivation from master key using PBKDF2
    - Base64 encoding for storage compatibility

    Example:
        >>> encryptor = FieldEncryption()
        >>> encrypted = encryptor.encrypt("1990-01-15")
        >>> decrypted = encryptor.decrypt(encrypted)
        >>> assert decrypted == "1990-01-15"
    """

    def __init__(self, master_key: Optional[bytes] = None):
        """
        Initialize encryption with master key.

        Args:
            master_key: 32-byte encryption key. If None, reads from environment
                       variable ANNY_ENCRYPTION_KEY or generates new key.
        """
        if master_key is None:
            # Try to load from environment
            key_b64 = os.environ.get('ANNY_ENCRYPTION_KEY')
            if key_b64:
                master_key = base64.b64decode(key_b64)
            else:
                # Generate new key (WARNING: Should be persisted in production)
                master_key = AESGCM.generate_key(bit_length=256)
                print("⚠️ WARNING: Generated new encryption key. "
                      "Set ANNY_ENCRYPTION_KEY environment variable in production.")

        if len(master_key) != 32:
            raise ValueError("Master key must be 32 bytes for AES-256")

        self.master_key = master_key
        self.aesgcm = AESGCM(master_key)

    def encrypt(self, plaintext: str, associated_data: Optional[bytes] = None) -> str:
        """
        Encrypt a string value using AES-256-GCM.

        Args:
            plaintext: String to encrypt
            associated_data: Additional authenticated data (not encrypted)

        Returns:
            Base64-encoded string containing: nonce + ciphertext + tag
        """
        if not plaintext:
            return ""

        # Generate random nonce (96 bits recommended for GCM)
        nonce = secrets.token_bytes(12)

        # Convert plaintext to bytes
        plaintext_bytes = plaintext.encode('utf-8')

        # Encrypt with authenticated encryption
        ciphertext = self.aesgcm.encrypt(
            nonce,
            plaintext_bytes,
            associated_data
        )

        # Combine nonce + ciphertext for storage
        encrypted_data = nonce + ciphertext

        # Encode as base64 for storage compatibility
        return base64.b64encode(encrypted_data).decode('utf-8')

    def decrypt(self, encrypted_b64: str, associated_data: Optional[bytes] = None) -> str:
        """
        Decrypt a base64-encoded encrypted value.

        Args:
            encrypted_b64: Base64-encoded encrypted data
            associated_data: Same AAD used during encryption

        Returns:
            Decrypted plaintext string

        Raises:
            ValueError: If decryption fails (wrong key, tampered data)
        """
        if not encrypted_b64:
            return ""

        try:
            # Decode from base64
            encrypted_data = base64.b64decode(encrypted_b64)

            # Extract nonce and ciphertext
            nonce = encrypted_data[:12]
            ciphertext = encrypted_data[12:]

            # Decrypt and verify
            plaintext_bytes = self.aesgcm.decrypt(
                nonce,
                ciphertext,
                associated_data
            )

            return plaintext_bytes.decode('utf-8')

        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")

    def encrypt_dict(self, data: dict, fields_to_encrypt: list) -> dict:
        """
        Encrypt specific fields in a dictionary.

        Args:
            data: Dictionary containing data
            fields_to_encrypt: List of field names to encrypt

        Returns:
            Dictionary with specified fields encrypted
        """
        encrypted_data = data.copy()
        for field in fields_to_encrypt:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = self.encrypt(str(encrypted_data[field]))
        return encrypted_data

    def decrypt_dict(self, data: dict, fields_to_decrypt: list) -> dict:
        """
        Decrypt specific fields in a dictionary.

        Args:
            data: Dictionary containing encrypted data
            fields_to_decrypt: List of field names to decrypt

        Returns:
            Dictionary with specified fields decrypted
        """
        decrypted_data = data.copy()
        for field in fields_to_decrypt:
            if field in decrypted_data and decrypted_data[field]:
                decrypted_data[field] = self.decrypt(decrypted_data[field])
        return decrypted_data


def generate_encryption_key() -> str:
    """
    Generate a new AES-256 encryption key.

    Returns:
        Base64-encoded 256-bit key

    Example:
        >>> key = generate_encryption_key()
        >>> os.environ['ANNY_ENCRYPTION_KEY'] = key
    """
    key = AESGCM.generate_key(bit_length=256)
    return base64.b64encode(key).decode('utf-8')


def encrypt_pii_field(value: str, key: Optional[bytes] = None) -> str:
    """
    Convenience function to encrypt a PII field.

    Args:
        value: Plaintext value to encrypt
        key: Optional encryption key (uses environment if not provided)

    Returns:
        Encrypted base64 string
    """
    encryptor = FieldEncryption(master_key=key)
    return encryptor.encrypt(value)


def decrypt_pii_field(encrypted_value: str, key: Optional[bytes] = None) -> str:
    """
    Convenience function to decrypt a PII field.

    Args:
        encrypted_value: Encrypted base64 string
        key: Optional encryption key (uses environment if not provided)

    Returns:
        Decrypted plaintext string
    """
    encryptor = FieldEncryption(master_key=key)
    return encryptor.decrypt(encrypted_value)


def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> tuple:
    """
    Derive encryption key from password using PBKDF2.

    Args:
        password: User password
        salt: Salt bytes (generated if not provided)

    Returns:
        Tuple of (derived_key, salt)

    Note:
        This is useful for user-specific encryption but NOT recommended
        for general PII encryption. Use environment-based keys instead.
    """
    if salt is None:
        salt = secrets.token_bytes(32)

    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )

    key = kdf.derive(password.encode('utf-8'))
    return key, salt


# Example usage and testing
if __name__ == "__main__":
    # Generate and print new key
    print("Generated encryption key:")
    print(f"ANNY_ENCRYPTION_KEY={generate_encryption_key()}")
    print("\nAdd this to your .env file or environment variables")

    # Test encryption
    encryptor = FieldEncryption()

    test_data = {
        'name': 'John Doe',
        'dob': '1990-01-15',
        'height': '175.5',
        'weight': '70.2'
    }

    pii_fields = ['dob', 'height', 'weight']

    print("\nOriginal data:")
    print(test_data)

    encrypted = encryptor.encrypt_dict(test_data, pii_fields)
    print("\nEncrypted data:")
    print(encrypted)

    decrypted = encryptor.decrypt_dict(encrypted, pii_fields)
    print("\nDecrypted data:")
    print(decrypted)

    assert test_data == decrypted, "Encryption/decryption failed!"
    print("\n✅ Encryption test passed!")
