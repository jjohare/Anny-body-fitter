# Anny Body Fitter - Encryption Tests
# Copyright (C) 2025 NAVER Corp.
# Apache License, Version 2.0

"""
Security tests for encryption module.
"""

import pytest
import os
import base64
from src.security.encryption import (
    FieldEncryption,
    encrypt_pii_field,
    decrypt_pii_field,
    generate_encryption_key,
    derive_key_from_password
)


class TestFieldEncryption:
    """Test suite for field-level encryption."""

    def test_encrypt_decrypt_basic(self):
        """Test basic encryption and decryption."""
        encryptor = FieldEncryption()
        plaintext = "1990-01-15"

        encrypted = encryptor.encrypt(plaintext)
        assert encrypted != plaintext
        assert isinstance(encrypted, str)

        decrypted = encryptor.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_empty_string(self):
        """Test encryption of empty string."""
        encryptor = FieldEncryption()
        encrypted = encryptor.encrypt("")
        assert encrypted == ""

        decrypted = encryptor.decrypt("")
        assert decrypted == ""

    def test_different_encryptions_are_unique(self):
        """Test that same plaintext produces different ciphertexts (due to nonce)."""
        encryptor = FieldEncryption()
        plaintext = "test data"

        encrypted1 = encryptor.encrypt(plaintext)
        encrypted2 = encryptor.encrypt(plaintext)

        # Should be different due to random nonce
        assert encrypted1 != encrypted2

        # But both should decrypt to same plaintext
        assert encryptor.decrypt(encrypted1) == plaintext
        assert encryptor.decrypt(encrypted2) == plaintext

    def test_wrong_key_fails(self):
        """Test that decryption with wrong key fails."""
        encryptor1 = FieldEncryption()
        encryptor2 = FieldEncryption()  # Different key

        plaintext = "secret data"
        encrypted = encryptor1.encrypt(plaintext)

        # Should fail with wrong key
        with pytest.raises(ValueError):
            encryptor2.decrypt(encrypted)

    def test_tampered_data_fails(self):
        """Test that tampered ciphertext fails to decrypt."""
        encryptor = FieldEncryption()
        plaintext = "important data"
        encrypted = encryptor.encrypt(plaintext)

        # Tamper with encrypted data
        encrypted_bytes = base64.b64decode(encrypted)
        tampered = encrypted_bytes[:-1] + b'\x00'  # Modify last byte
        tampered_b64 = base64.b64encode(tampered).decode('utf-8')

        # Should fail authentication
        with pytest.raises(ValueError):
            encryptor.decrypt(tampered_b64)

    def test_encrypt_dict(self):
        """Test encryption of dictionary fields."""
        encryptor = FieldEncryption()
        data = {
            'name': 'John Doe',
            'dob': '1990-01-15',
            'height': '175.5',
            'weight': '70.2'
        }

        fields_to_encrypt = ['dob', 'height', 'weight']
        encrypted = encryptor.encrypt_dict(data, fields_to_encrypt)

        # Encrypted fields should be different
        assert encrypted['dob'] != data['dob']
        assert encrypted['height'] != data['height']
        assert encrypted['weight'] != data['weight']

        # Non-encrypted fields should be same
        assert encrypted['name'] == data['name']

        # Decrypt should restore original
        decrypted = encryptor.decrypt_dict(encrypted, fields_to_encrypt)
        assert decrypted == data

    def test_associated_data(self):
        """Test authenticated encryption with associated data."""
        encryptor = FieldEncryption()
        plaintext = "sensitive data"
        associated = b"user_id:12345"

        # Encrypt with associated data
        encrypted = encryptor.encrypt(plaintext, associated_data=associated)

        # Decrypt with correct associated data
        decrypted = encryptor.decrypt(encrypted, associated_data=associated)
        assert decrypted == plaintext

        # Decrypt with wrong associated data should fail
        with pytest.raises(ValueError):
            encryptor.decrypt(encrypted, associated_data=b"user_id:99999")

    def test_generate_key(self):
        """Test key generation."""
        key = generate_encryption_key()
        assert isinstance(key, str)
        assert len(base64.b64decode(key)) == 32  # 256 bits

        # Keys should be unique
        key2 = generate_encryption_key()
        assert key != key2

    def test_key_from_environment(self):
        """Test loading key from environment."""
        test_key = generate_encryption_key()
        os.environ['ANNY_ENCRYPTION_KEY'] = test_key

        encryptor = FieldEncryption()
        plaintext = "test"
        encrypted = encryptor.encrypt(plaintext)

        # Should be able to decrypt with same key
        decrypted = encryptor.decrypt(encrypted)
        assert decrypted == plaintext

        # Cleanup
        del os.environ['ANNY_ENCRYPTION_KEY']

    def test_derive_key_from_password(self):
        """Test key derivation from password."""
        password = "my_secure_password_123"
        key1, salt1 = derive_key_from_password(password)

        assert len(key1) == 32  # 256 bits
        assert len(salt1) == 32

        # Same password with same salt should produce same key
        key2, _ = derive_key_from_password(password, salt=salt1)
        assert key1 == key2

        # Same password with different salt should produce different key
        key3, salt3 = derive_key_from_password(password)
        assert key3 != key1
        assert salt3 != salt1

    def test_convenience_functions(self):
        """Test convenience encryption/decryption functions."""
        value = "test data"
        encrypted = encrypt_pii_field(value)
        assert encrypted != value

        decrypted = decrypt_pii_field(encrypted)
        assert decrypted == value


class TestEncryptionSecurity:
    """Security-focused tests for encryption."""

    def test_encryption_strength(self):
        """Test that encryption is strong enough."""
        encryptor = FieldEncryption()
        plaintext = "A" * 1000  # Repeated character

        encrypted = encryptor.encrypt(plaintext)
        encrypted_bytes = base64.b64decode(encrypted)

        # Encrypted data should not have obvious patterns
        # (this is a basic check, not comprehensive)
        assert b'AAA' not in encrypted_bytes

    def test_no_plaintext_leakage(self):
        """Test that plaintext doesn't leak into ciphertext."""
        encryptor = FieldEncryption()
        plaintext = "sensitive_password_123"

        encrypted = encryptor.encrypt(plaintext)

        # Plaintext should not appear in encrypted form
        assert plaintext not in encrypted
        assert plaintext.encode() not in base64.b64decode(encrypted)

    def test_timing_attack_resistance(self):
        """Test that decryption time is consistent (basic check)."""
        import time

        encryptor = FieldEncryption()
        plaintext = "test"
        encrypted = encryptor.encrypt(plaintext)

        # Measure decryption time for correct ciphertext
        times = []
        for _ in range(100):
            start = time.perf_counter()
            encryptor.decrypt(encrypted)
            times.append(time.perf_counter() - start)

        avg_time = sum(times) / len(times)

        # Timing should be relatively consistent
        # (this is a basic check, real timing attack testing is more complex)
        assert all(abs(t - avg_time) < avg_time * 0.5 for t in times)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
