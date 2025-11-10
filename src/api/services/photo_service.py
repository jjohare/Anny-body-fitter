"""Photo management service."""

import uuid
import logging
from typing import List
from pathlib import Path
from datetime import datetime
from fastapi import UploadFile
from PIL import Image
import io

from src.api.schemas import PhotoResponse
from src.api.services.database import DatabaseService

logger = logging.getLogger(__name__)


class PhotoService:
    """Service for managing photo uploads."""

    def __init__(self, db: DatabaseService, storage_path: str = "data/photos"):
        """Initialize photo service."""
        self.db = db
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def upload_photos(
        self,
        subject_id: str,
        files: List[UploadFile],
        metadata_list: List[dict],
        user_id: str
    ) -> List[PhotoResponse]:
        """Upload multiple photos for a subject."""
        uploaded_photos = []

        for file, metadata in zip(files, metadata_list):
            photo_id = f"photo_{uuid.uuid4().hex[:12]}"

            # Read file content
            content = await file.read()

            # Get image dimensions
            image = Image.open(io.BytesIO(content))
            width, height = image.size

            # Save file to storage
            file_extension = file.filename.split(".")[-1]
            storage_filename = f"{photo_id}.{file_extension}"
            storage_filepath = self.storage_path / subject_id / storage_filename
            storage_filepath.parent.mkdir(parents=True, exist_ok=True)

            with open(storage_filepath, "wb") as f:
                f.write(content)

            # Save metadata to database
            query = """
                INSERT INTO photos (
                    id, subject_id, filename, photo_type,
                    file_size_bytes, width_px, height_px,
                    camera_height_cm, distance_cm, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                photo_id,
                subject_id,
                storage_filename,
                metadata.get("photo_type", "custom"),
                len(content),
                width,
                height,
                metadata.get("camera_height_cm"),
                metadata.get("distance_cm"),
                metadata.get("notes")
            )

            await self.db.execute(query, params)

            # Update subject photo count
            await self.db.execute(
                "UPDATE subjects SET photo_count = photo_count + 1 WHERE id = ?",
                (subject_id,)
            )

            # Fetch and add to results
            photo = await self.get_photo(photo_id)
            uploaded_photos.append(photo)

            logger.info(f"Uploaded photo {photo_id} for subject {subject_id}")

        return uploaded_photos

    async def get_photo(self, photo_id: str) -> PhotoResponse:
        """Get photo by ID."""
        query = "SELECT * FROM photos WHERE id = ?"
        row = await self.db.fetch_one(query, (photo_id,))

        return self._row_to_photo(row)

    async def get_subject_photos(
        self,
        subject_id: str,
        user_id: str
    ) -> List[PhotoResponse]:
        """Get all photos for a subject."""
        query = """
            SELECT p.* FROM photos p
            JOIN subjects s ON p.subject_id = s.id
            WHERE p.subject_id = ? AND s.user_id = ?
            ORDER BY p.uploaded_at DESC
        """
        rows = await self.db.fetch_all(query, (subject_id, user_id))

        return [self._row_to_photo(row) for row in rows]

    def _row_to_photo(self, row) -> PhotoResponse:
        """Convert database row to PhotoResponse."""
        return PhotoResponse(
            id=row["id"],
            subject_id=row["subject_id"],
            filename=row["filename"],
            photo_type=row["photo_type"],
            file_size_bytes=row["file_size_bytes"],
            width_px=row["width_px"],
            height_px=row["height_px"],
            camera_height_cm=row["camera_height_cm"],
            distance_cm=row["distance_cm"],
            notes=row["notes"],
            uploaded_at=datetime.fromisoformat(row["uploaded_at"])
        )
