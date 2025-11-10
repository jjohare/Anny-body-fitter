"""
CRUD operations for database models.
Provides standardized database access patterns.
"""
from typing import Optional, List, Type, TypeVar, Generic
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .models import (
    Subject, Measurement, ModelParameter,
    PerformanceMetric, PhotoRecord, Session as SessionModel
)
from .schemas import (
    SubjectCreate, SubjectUpdate,
    MeasurementCreate,
    ModelParameterCreate,
    PerformanceMetricCreate,
    PhotoRecordCreate,
    SessionCreate, SessionUpdate
)

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base CRUD class with generic database operations.
    """
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """Get a single record by ID"""
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records with pagination"""
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record"""
        obj_in_data = obj_in.model_dump() if hasattr(obj_in, 'model_dump') else obj_in.dict()
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        db_obj: ModelType,
        obj_in: UpdateSchemaType
    ) -> ModelType:
        """Update an existing record"""
        obj_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, 'model_dump') else obj_in.dict(exclude_unset=True)

        for field, value in obj_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> Optional[ModelType]:
        """Delete a record by ID"""
        obj = db.query(self.model).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj


class CRUDSubject(CRUDBase[Subject, SubjectCreate, SubjectUpdate]):
    """CRUD operations for Subject model"""

    def get_active(self, db: Session, skip: int = 0, limit: int = 100) -> List[Subject]:
        """Get all active subjects"""
        return (
            db.query(Subject)
            .filter(Subject.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_name(self, db: Session, name: str) -> Optional[Subject]:
        """Get subject by name (exact match)"""
        return db.query(Subject).filter(Subject.name == name).first()

    def search_by_name(self, db: Session, name_pattern: str) -> List[Subject]:
        """Search subjects by name pattern"""
        return (
            db.query(Subject)
            .filter(Subject.name.ilike(f"%{name_pattern}%"))
            .filter(Subject.is_active == True)
            .all()
        )

    def soft_delete(self, db: Session, id: int) -> Optional[Subject]:
        """Soft delete a subject by marking as inactive"""
        subject = self.get(db, id)
        if subject:
            subject.is_active = False
            db.commit()
            db.refresh(subject)
        return subject


class CRUDMeasurement(CRUDBase[Measurement, MeasurementCreate, None]):
    """CRUD operations for Measurement model"""

    def get_by_subject(
        self,
        db: Session,
        subject_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Measurement]:
        """Get all measurements for a subject"""
        return (
            db.query(Measurement)
            .filter(Measurement.subject_id == subject_id)
            .order_by(Measurement.measurement_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_latest(self, db: Session, subject_id: int) -> Optional[Measurement]:
        """Get the most recent measurement for a subject"""
        return (
            db.query(Measurement)
            .filter(Measurement.subject_id == subject_id)
            .order_by(Measurement.measurement_date.desc())
            .first()
        )

    def get_by_date_range(
        self,
        db: Session,
        subject_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[Measurement]:
        """Get measurements within a date range"""
        return (
            db.query(Measurement)
            .filter(
                Measurement.subject_id == subject_id,
                Measurement.measurement_date >= start_date,
                Measurement.measurement_date <= end_date
            )
            .order_by(Measurement.measurement_date.desc())
            .all()
        )


class CRUDModelParameter(CRUDBase[ModelParameter, ModelParameterCreate, None]):
    """CRUD operations for ModelParameter model"""

    def get_by_subject(
        self,
        db: Session,
        subject_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelParameter]:
        """Get all model parameters for a subject"""
        return (
            db.query(ModelParameter)
            .filter(ModelParameter.subject_id == subject_id)
            .order_by(ModelParameter.parameter_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_latest(self, db: Session, subject_id: int) -> Optional[ModelParameter]:
        """Get the most recent model parameters for a subject"""
        return (
            db.query(ModelParameter)
            .filter(ModelParameter.subject_id == subject_id)
            .order_by(ModelParameter.parameter_date.desc())
            .first()
        )

    def get_by_version(
        self,
        db: Session,
        subject_id: int,
        model_version: str
    ) -> List[ModelParameter]:
        """Get model parameters by version"""
        return (
            db.query(ModelParameter)
            .filter(
                ModelParameter.subject_id == subject_id,
                ModelParameter.model_version == model_version
            )
            .order_by(ModelParameter.parameter_date.desc())
            .all()
        )


class CRUDPerformanceMetric(CRUDBase[PerformanceMetric, PerformanceMetricCreate, None]):
    """CRUD operations for PerformanceMetric model"""

    def get_by_subject(
        self,
        db: Session,
        subject_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[PerformanceMetric]:
        """Get all performance metrics for a subject"""
        return (
            db.query(PerformanceMetric)
            .filter(PerformanceMetric.subject_id == subject_id)
            .order_by(PerformanceMetric.metric_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_type(
        self,
        db: Session,
        subject_id: int,
        metric_type: str
    ) -> List[PerformanceMetric]:
        """Get performance metrics by type"""
        return (
            db.query(PerformanceMetric)
            .filter(
                PerformanceMetric.subject_id == subject_id,
                PerformanceMetric.metric_type == metric_type
            )
            .order_by(PerformanceMetric.metric_date.desc())
            .all()
        )

    def get_latest(self, db: Session, subject_id: int) -> Optional[PerformanceMetric]:
        """Get the most recent performance metric for a subject"""
        return (
            db.query(PerformanceMetric)
            .filter(PerformanceMetric.subject_id == subject_id)
            .order_by(PerformanceMetric.metric_date.desc())
            .first()
        )


class CRUDPhotoRecord(CRUDBase[PhotoRecord, PhotoRecordCreate, None]):
    """CRUD operations for PhotoRecord model"""

    def get_by_subject(
        self,
        db: Session,
        subject_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[PhotoRecord]:
        """Get all photo records for a subject"""
        return (
            db.query(PhotoRecord)
            .filter(PhotoRecord.subject_id == subject_id)
            .order_by(PhotoRecord.upload_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_type(
        self,
        db: Session,
        subject_id: int,
        photo_type: str
    ) -> List[PhotoRecord]:
        """Get photo records by type"""
        return (
            db.query(PhotoRecord)
            .filter(
                PhotoRecord.subject_id == subject_id,
                PhotoRecord.photo_type == photo_type
            )
            .order_by(PhotoRecord.upload_date.desc())
            .all()
        )

    def get_unprocessed(self, db: Session) -> List[PhotoRecord]:
        """Get all unprocessed photos"""
        return (
            db.query(PhotoRecord)
            .filter(PhotoRecord.is_processed == False)
            .order_by(PhotoRecord.upload_date.asc())
            .all()
        )

    def mark_processed(
        self,
        db: Session,
        id: int,
        status: str = "completed"
    ) -> Optional[PhotoRecord]:
        """Mark a photo as processed"""
        photo = self.get(db, id)
        if photo:
            photo.is_processed = True
            photo.processing_status = status
            db.commit()
            db.refresh(photo)
        return photo


class CRUDSession(CRUDBase[SessionModel, SessionCreate, SessionUpdate]):
    """CRUD operations for Session model"""

    def get_by_subject(
        self,
        db: Session,
        subject_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[SessionModel]:
        """Get all sessions for a subject"""
        return (
            db.query(SessionModel)
            .filter(SessionModel.subject_id == subject_id)
            .order_by(SessionModel.session_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_status(
        self,
        db: Session,
        status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[SessionModel]:
        """Get sessions by status"""
        return (
            db.query(SessionModel)
            .filter(SessionModel.session_status == status)
            .order_by(SessionModel.session_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_latest(self, db: Session, subject_id: int) -> Optional[SessionModel]:
        """Get the most recent session for a subject"""
        return (
            db.query(SessionModel)
            .filter(SessionModel.subject_id == subject_id)
            .order_by(SessionModel.session_date.desc())
            .first()
        )

    def complete_session(self, db: Session, id: int) -> Optional[SessionModel]:
        """Mark a session as completed"""
        session = self.get(db, id)
        if session:
            session.session_status = "completed"
            db.commit()
            db.refresh(session)
        return session


# Instantiate CRUD objects
subject = CRUDSubject(Subject)
measurement = CRUDMeasurement(Measurement)
model_parameter = CRUDModelParameter(ModelParameter)
performance_metric = CRUDPerformanceMetric(PerformanceMetric)
photo_record = CRUDPhotoRecord(PhotoRecord)
session = CRUDSession(SessionModel)
