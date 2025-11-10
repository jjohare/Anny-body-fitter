"""Subject management service."""

import uuid
import logging
from typing import List, Optional
from datetime import datetime

from src.api.schemas import SubjectCreate, SubjectResponse, SubjectUpdate, SubjectList
from src.api.services.database import DatabaseService

logger = logging.getLogger(__name__)


class SubjectService:
    """Service for managing subjects."""

    def __init__(self, db: DatabaseService):
        """Initialize subject service."""
        self.db = db

    async def create_subject(self, subject: SubjectCreate, user_id: str) -> SubjectResponse:
        """Create a new subject."""
        subject_id = f"subj_{uuid.uuid4().hex[:12]}"

        query = """
            INSERT INTO subjects (id, user_id, name, age, gender, height_cm, weight_kg, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            subject_id,
            user_id,
            subject.name,
            subject.age,
            subject.gender.value if subject.gender else None,
            subject.height_cm,
            subject.weight_kg,
            subject.notes
        )

        await self.db.execute(query, params)

        # Fetch and return created subject
        return await self.get_subject(subject_id, user_id)

    async def get_subject(self, subject_id: str, user_id: str) -> Optional[SubjectResponse]:
        """Get subject by ID."""
        query = """
            SELECT * FROM subjects
            WHERE id = ? AND user_id = ? AND deleted_at IS NULL
        """
        row = await self.db.fetch_one(query, (subject_id, user_id))

        if not row:
            return None

        return self._row_to_subject(row)

    async def list_subjects(
        self,
        page: int,
        page_size: int,
        search: Optional[str],
        user_id: str
    ) -> SubjectList:
        """List subjects with pagination."""
        offset = (page - 1) * page_size

        # Build query
        where_clause = "WHERE user_id = ? AND deleted_at IS NULL"
        params = [user_id]

        if search:
            where_clause += " AND name LIKE ?"
            params.append(f"%{search}%")

        # Get total count
        count_query = f"SELECT COUNT(*) as count FROM subjects {where_clause}"
        count_row = await self.db.fetch_one(count_query, tuple(params))
        total = count_row["count"]

        # Get paginated results
        query = f"""
            SELECT * FROM subjects
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([page_size, offset])
        rows = await self.db.fetch_all(query, tuple(params))

        subjects = [self._row_to_subject(row) for row in rows]

        return SubjectList(
            subjects=subjects,
            total=total,
            page=page,
            page_size=page_size
        )

    async def update_subject(
        self,
        subject_id: str,
        updates: SubjectUpdate,
        user_id: str
    ) -> Optional[SubjectResponse]:
        """Update subject information."""
        # Build update query dynamically
        update_fields = []
        params = []

        if updates.name is not None:
            update_fields.append("name = ?")
            params.append(updates.name)
        if updates.age is not None:
            update_fields.append("age = ?")
            params.append(updates.age)
        if updates.gender is not None:
            update_fields.append("gender = ?")
            params.append(updates.gender.value)
        if updates.height_cm is not None:
            update_fields.append("height_cm = ?")
            params.append(updates.height_cm)
        if updates.weight_kg is not None:
            update_fields.append("weight_kg = ?")
            params.append(updates.weight_kg)
        if updates.notes is not None:
            update_fields.append("notes = ?")
            params.append(updates.notes)

        if not update_fields:
            # No updates provided
            return await self.get_subject(subject_id, user_id)

        update_fields.append("updated_at = CURRENT_TIMESTAMP")

        query = f"""
            UPDATE subjects
            SET {', '.join(update_fields)}
            WHERE id = ? AND user_id = ? AND deleted_at IS NULL
        """
        params.extend([subject_id, user_id])

        await self.db.execute(query, tuple(params))

        return await self.get_subject(subject_id, user_id)

    async def delete_subject(
        self,
        subject_id: str,
        user_id: str,
        permanent: bool = False
    ) -> bool:
        """Delete subject (soft delete by default, hard delete if permanent=True)."""
        if permanent:
            # Hard delete - remove all associated data
            queries = [
                "DELETE FROM metrics WHERE subject_id = ?",
                "DELETE FROM model_parameters WHERE subject_id = ?",
                "DELETE FROM fitting_tasks WHERE subject_id = ?",
                "DELETE FROM photos WHERE subject_id = ?",
                "DELETE FROM subjects WHERE id = ? AND user_id = ?"
            ]
            for query in queries:
                if "subjects" in query:
                    await self.db.execute(query, (subject_id, user_id))
                else:
                    await self.db.execute(query, (subject_id,))
        else:
            # Soft delete
            query = """
                UPDATE subjects
                SET deleted_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ? AND deleted_at IS NULL
            """
            await self.db.execute(query, (subject_id, user_id))

        return True

    def _row_to_subject(self, row) -> SubjectResponse:
        """Convert database row to SubjectResponse."""
        return SubjectResponse(
            id=row["id"],
            name=row["name"],
            age=row["age"],
            gender=row["gender"],
            height_cm=row["height_cm"],
            weight_kg=row["weight_kg"],
            notes=row["notes"],
            photo_count=row["photo_count"],
            has_fitted_model=bool(row["has_fitted_model"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"])
        )
