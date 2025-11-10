# Anny Body Fitter - Temporary Storage Module
# Copyright (C) 2025 NAVER Corp.
# Apache License, Version 2.0

"""
Temporary file storage with automatic cleanup and secure deletion.

Manages temporary photo storage with:
- Automatic expiration and cleanup
- Secure file deletion (overwrite before delete)
- Session-based file isolation
- Background cleanup tasks
"""

import os
import time
import secrets
import hashlib
import threading
from pathlib import Path
from typing import Union, Optional, BinaryIO
from datetime import datetime, timedelta
import shutil
import tempfile


class TemporaryPhotoStorage:
    """
    Secure temporary storage for user photos.

    Features:
    - Automatic file expiration
    - Secure deletion with overwrite
    - Session-based isolation
    - Background cleanup
    - No permanent storage

    Example:
        >>> storage = TemporaryPhotoStorage(ttl_minutes=30)
        >>> file_id = storage.store_photo(photo_data, session_id="user123")
        >>> photo_path = storage.get_photo_path(file_id)
        >>> # ... process photo ...
        >>> storage.delete_photo(file_id)
    """

    def __init__(self,
                 base_dir: Optional[Path] = None,
                 ttl_minutes: int = 30,
                 cleanup_interval_seconds: int = 300):
        """
        Initialize temporary storage.

        Args:
            base_dir: Base directory for temporary files (uses system temp if None)
            ttl_minutes: Time-to-live for files in minutes
            cleanup_interval_seconds: How often to run cleanup (default 5 min)
        """
        if base_dir is None:
            base_dir = Path(tempfile.gettempdir()) / 'anny_temp_photos'

        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True, mode=0o700)  # Owner-only access

        self.ttl_seconds = ttl_minutes * 60
        self.cleanup_interval = cleanup_interval_seconds

        # File registry: {file_id: (path, created_time, session_id)}
        self._files = {}
        self._lock = threading.Lock()

        # Start background cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._background_cleanup,
            daemon=True
        )
        self._cleanup_thread.start()

    def store_photo(self,
                    photo_data: Union[bytes, BinaryIO],
                    session_id: str,
                    extension: str = '.jpg') -> str:
        """
        Store photo temporarily.

        Args:
            photo_data: Photo data (bytes or file-like object)
            session_id: User session ID for isolation
            extension: File extension

        Returns:
            Unique file ID for retrieval

        Raises:
            ValueError: If data is invalid
        """
        if not session_id:
            raise ValueError("Session ID is required")

        # Generate unique file ID
        file_id = self._generate_file_id()

        # Create session directory
        session_dir = self.base_dir / self._sanitize_session_id(session_id)
        session_dir.mkdir(exist_ok=True, mode=0o700)

        # Create file path
        file_path = session_dir / f"{file_id}{extension}"

        # Write data
        if isinstance(photo_data, bytes):
            file_path.write_bytes(photo_data)
        else:
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(photo_data, f)

        # Set restrictive permissions
        file_path.chmod(0o600)  # Owner read/write only

        # Register file
        with self._lock:
            self._files[file_id] = {
                'path': file_path,
                'created': time.time(),
                'session_id': session_id,
                'size': file_path.stat().st_size
            }

        return file_id

    def get_photo_path(self, file_id: str) -> Optional[Path]:
        """
        Get path to stored photo.

        Args:
            file_id: File ID from store_photo()

        Returns:
            Path to file or None if not found/expired
        """
        with self._lock:
            if file_id not in self._files:
                return None

            file_info = self._files[file_id]

            # Check if expired
            if time.time() - file_info['created'] > self.ttl_seconds:
                self._delete_file(file_id)
                return None

            return file_info['path']

    def delete_photo(self, file_id: str) -> bool:
        """
        Securely delete a photo.

        Args:
            file_id: File ID to delete

        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            return self._delete_file(file_id)

    def delete_session_photos(self, session_id: str) -> int:
        """
        Delete all photos for a session.

        Args:
            session_id: Session ID

        Returns:
            Number of files deleted
        """
        deleted_count = 0
        with self._lock:
            file_ids = [
                fid for fid, info in self._files.items()
                if info['session_id'] == session_id
            ]
            for file_id in file_ids:
                if self._delete_file(file_id):
                    deleted_count += 1

        return deleted_count

    def _delete_file(self, file_id: str) -> bool:
        """
        Internal method to delete file (must be called with lock held).

        Args:
            file_id: File ID

        Returns:
            True if deleted
        """
        if file_id not in self._files:
            return False

        file_info = self._files[file_id]
        file_path = file_info['path']

        # Secure delete
        secure_delete_file(file_path)

        # Remove from registry
        del self._files[file_id]

        return True

    def _background_cleanup(self):
        """Background thread to clean up expired files."""
        while True:
            time.sleep(self.cleanup_interval)
            self.cleanup_expired_files()

    def cleanup_expired_files(self) -> int:
        """
        Clean up expired files.

        Returns:
            Number of files cleaned up
        """
        current_time = time.time()
        expired_ids = []

        with self._lock:
            for file_id, info in self._files.items():
                if current_time - info['created'] > self.ttl_seconds:
                    expired_ids.append(file_id)

            # Delete expired files
            for file_id in expired_ids:
                self._delete_file(file_id)

        return len(expired_ids)

    def get_stats(self) -> dict:
        """
        Get storage statistics.

        Returns:
            Dictionary with storage stats
        """
        with self._lock:
            total_files = len(self._files)
            total_size = sum(info['size'] for info in self._files.values())

            sessions = set(info['session_id'] for info in self._files.values())

            return {
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'active_sessions': len(sessions),
                'storage_path': str(self.base_dir)
            }

    @staticmethod
    def _generate_file_id() -> str:
        """Generate unique file ID."""
        random_bytes = secrets.token_bytes(16)
        timestamp = str(time.time()).encode()
        return hashlib.sha256(random_bytes + timestamp).hexdigest()[:32]

    @staticmethod
    def _sanitize_session_id(session_id: str) -> str:
        """Sanitize session ID for use as directory name."""
        # Hash session ID to prevent directory traversal
        return hashlib.sha256(session_id.encode()).hexdigest()[:16]


def secure_delete_file(file_path: Union[str, Path],
                      passes: int = 3) -> bool:
    """
    Securely delete a file by overwriting before deletion.

    Args:
        file_path: Path to file to delete
        passes: Number of overwrite passes

    Returns:
        True if deleted successfully

    Note:
        This provides basic secure deletion. For highly sensitive data,
        consider using specialized tools or encrypted filesystems.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        return False

    try:
        # Get file size
        file_size = file_path.stat().st_size

        # Overwrite with random data
        with open(file_path, 'r+b') as f:
            for _ in range(passes):
                f.seek(0)
                f.write(os.urandom(file_size))
                f.flush()
                os.fsync(f.fileno())

        # Delete file
        file_path.unlink()
        return True

    except Exception as e:
        # If secure deletion fails, still try regular deletion
        try:
            file_path.unlink()
        except:
            pass
        return False


def cleanup_expired_files(base_dir: Union[str, Path],
                         max_age_seconds: int = 3600) -> int:
    """
    Clean up files older than specified age.

    Args:
        base_dir: Directory to clean
        max_age_seconds: Maximum age in seconds

    Returns:
        Number of files deleted
    """
    base_dir = Path(base_dir)
    if not base_dir.exists():
        return 0

    current_time = time.time()
    deleted_count = 0

    for file_path in base_dir.rglob('*'):
        if not file_path.is_file():
            continue

        try:
            file_age = current_time - file_path.stat().st_mtime
            if file_age > max_age_seconds:
                secure_delete_file(file_path)
                deleted_count += 1
        except Exception:
            continue

    return deleted_count


# Example usage
if __name__ == "__main__":
    import tempfile
    import time

    print("Testing temporary photo storage...")

    # Create storage with 1 minute TTL
    storage = TemporaryPhotoStorage(ttl_minutes=1)

    # Create test photo
    test_photo = b"fake photo data " * 100

    print("\n✅ Storing test photo...")
    file_id = storage.store_photo(
        test_photo,
        session_id="test_session_123",
        extension=".jpg"
    )
    print(f"  File ID: {file_id}")

    # Retrieve photo
    print("\n✅ Retrieving photo...")
    photo_path = storage.get_photo_path(file_id)
    print(f"  Path: {photo_path}")
    assert photo_path.exists(), "Photo should exist"

    # Check stats
    stats = storage.get_stats()
    print(f"\n✅ Storage stats:")
    print(f"  Files: {stats['total_files']}")
    print(f"  Size: {stats['total_size_mb']}MB")
    print(f"  Sessions: {stats['active_sessions']}")

    # Delete photo
    print("\n✅ Deleting photo...")
    deleted = storage.delete_photo(file_id)
    assert deleted, "Photo should be deleted"
    assert not photo_path.exists(), "Photo should not exist after deletion"

    # Test secure deletion
    print("\n✅ Testing secure file deletion...")
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"sensitive data to be securely deleted")
        tmp_path = Path(tmp.name)

    assert tmp_path.exists(), "Temp file should exist"
    secure_delete_file(tmp_path)
    assert not tmp_path.exists(), "Temp file should be securely deleted"

    print("\n✅ All temporary storage tests passed!")
