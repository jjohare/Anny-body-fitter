"""
SQLAlchemy ORM models for Anny Body Fitter database.
Implements privacy-conscious schema with audit trails.
"""
from datetime import datetime
from typing import List
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey,
    Text, Boolean, Index, LargeBinary
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Subject(Base):
    """
    Subject/Patient entity with basic demographic information.
    Sensitive fields are designed for encryption at application level.
    """
    __tablename__ = 'subjects'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)  # Should be encrypted
    date_of_birth = Column(DateTime, nullable=False)  # Should be encrypted

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Soft delete support
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Optional metadata
    notes = Column(Text, nullable=True)

    # Relationships
    measurements = relationship("Measurement", back_populates="subject", cascade="all, delete-orphan")
    model_parameters = relationship("ModelParameter", back_populates="subject", cascade="all, delete-orphan")
    performance_metrics = relationship("PerformanceMetric", back_populates="subject", cascade="all, delete-orphan")
    photo_records = relationship("PhotoRecord", back_populates="subject", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="subject", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_subject_active_created', 'is_active', 'created_at'),
    )

    def __repr__(self):
        return f"<Subject(id={self.id}, name={self.name})>"


class Measurement(Base):
    """
    Body measurements for a subject at a specific point in time.
    Stores traditional anthropometric measurements.
    """
    __tablename__ = 'measurements'

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False, index=True)

    # Core measurements (in cm unless noted)
    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)  # kg
    chest_circumference = Column(Float, nullable=True)
    waist_circumference = Column(Float, nullable=True)
    hip_circumference = Column(Float, nullable=True)
    inseam = Column(Float, nullable=True)
    shoulder_width = Column(Float, nullable=True)
    arm_length = Column(Float, nullable=True)
    leg_length = Column(Float, nullable=True)
    neck_circumference = Column(Float, nullable=True)

    # Additional custom measurements (JSON-like storage)
    custom_measurements = Column(Text, nullable=True)  # Store as JSON string

    # Measurement context
    measurement_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    measured_by = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    subject = relationship("Subject", back_populates="measurements")

    __table_args__ = (
        Index('idx_measurement_subject_date', 'subject_id', 'measurement_date'),
    )

    def __repr__(self):
        return f"<Measurement(id={self.id}, subject_id={self.subject_id}, date={self.measurement_date})>"


class ModelParameter(Base):
    """
    Anny phenotype parameters for body shape modeling.
    Stores the specific parameters used to generate the 3D model.
    """
    __tablename__ = 'model_parameters'

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False, index=True)

    # Anny phenotype parameters (adjust based on actual Anny model)
    height_param = Column(Float, nullable=True)
    weight_param = Column(Float, nullable=True)
    chest_param = Column(Float, nullable=True)
    waist_param = Column(Float, nullable=True)
    hip_param = Column(Float, nullable=True)

    # Shape parameters (could be PCA components or other shape descriptors)
    shape_param_1 = Column(Float, nullable=True)
    shape_param_2 = Column(Float, nullable=True)
    shape_param_3 = Column(Float, nullable=True)
    shape_param_4 = Column(Float, nullable=True)
    shape_param_5 = Column(Float, nullable=True)

    # Additional parameters stored as JSON
    additional_params = Column(Text, nullable=True)

    # Model metadata
    model_version = Column(String(50), nullable=True)
    confidence_score = Column(Float, nullable=True)  # 0-1 confidence in parameter fit

    # Context
    parameter_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    notes = Column(Text, nullable=True)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    subject = relationship("Subject", back_populates="model_parameters")

    __table_args__ = (
        Index('idx_model_param_subject_date', 'subject_id', 'parameter_date'),
    )

    def __repr__(self):
        return f"<ModelParameter(id={self.id}, subject_id={self.subject_id}, version={self.model_version})>"


class PerformanceMetric(Base):
    """
    Custom performance metrics related to body fitting and model accuracy.
    Tracks quality metrics for the fitting process.
    """
    __tablename__ = 'performance_metrics'

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False, index=True)

    # Fitting quality metrics
    fitting_error = Column(Float, nullable=True)  # Overall error metric
    landmark_accuracy = Column(Float, nullable=True)  # Accuracy of landmark detection
    mesh_quality = Column(Float, nullable=True)  # Quality of generated mesh

    # Performance metrics
    processing_time = Column(Float, nullable=True)  # seconds
    convergence_iterations = Column(Integer, nullable=True)

    # Specific error metrics
    height_error = Column(Float, nullable=True)
    volume_error = Column(Float, nullable=True)
    surface_area_error = Column(Float, nullable=True)

    # Additional metrics stored as JSON
    custom_metrics = Column(Text, nullable=True)

    # Context
    metric_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metric_type = Column(String(100), nullable=True)  # e.g., 'initial_fit', 'refined_fit'
    notes = Column(Text, nullable=True)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    subject = relationship("Subject", back_populates="performance_metrics")

    __table_args__ = (
        Index('idx_perf_metric_subject_date', 'subject_id', 'metric_date'),
    )

    def __repr__(self):
        return f"<PerformanceMetric(id={self.id}, subject_id={self.subject_id}, type={self.metric_type})>"


class PhotoRecord(Base):
    """
    Metadata for uploaded photos (does NOT store actual image data).
    Images should be stored in object storage (S3, local filesystem, etc.)
    with only references stored in the database.
    """
    __tablename__ = 'photo_records'

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False, index=True)

    # File metadata
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)  # Path to stored image
    file_size = Column(Integer, nullable=True)  # bytes
    mime_type = Column(String(100), nullable=True)

    # Photo metadata
    photo_type = Column(String(50), nullable=True)  # e.g., 'front', 'side', 'back'
    resolution = Column(String(50), nullable=True)  # e.g., '1920x1080'

    # Processing metadata
    is_processed = Column(Boolean, default=False, nullable=False)
    processing_status = Column(String(50), nullable=True)  # e.g., 'pending', 'completed', 'failed'

    # Hash for integrity verification
    file_hash = Column(String(64), nullable=True)  # SHA-256 hash

    # Context
    capture_date = Column(DateTime(timezone=True), nullable=True)
    upload_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    notes = Column(Text, nullable=True)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    subject = relationship("Subject", back_populates="photo_records")

    __table_args__ = (
        Index('idx_photo_subject_upload', 'subject_id', 'upload_date'),
        Index('idx_photo_type_processed', 'photo_type', 'is_processed'),
    )

    def __repr__(self):
        return f"<PhotoRecord(id={self.id}, subject_id={self.subject_id}, filename={self.filename})>"


class Session(Base):
    """
    Fitting sessions to track history and progress over time.
    Links together measurements, parameters, and photos from a single session.
    """
    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False, index=True)

    # Session metadata
    session_name = Column(String(255), nullable=True)
    session_type = Column(String(50), nullable=True)  # e.g., 'initial', 'follow_up', 'final'
    session_status = Column(String(50), default='in_progress', nullable=False)  # 'in_progress', 'completed', 'cancelled'

    # Session date/time
    session_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    duration = Column(Integer, nullable=True)  # minutes

    # Links to related records (stored as comma-separated IDs or JSON)
    measurement_ids = Column(Text, nullable=True)
    model_parameter_ids = Column(Text, nullable=True)
    photo_record_ids = Column(Text, nullable=True)
    performance_metric_ids = Column(Text, nullable=True)

    # Session outcomes
    outcome_summary = Column(Text, nullable=True)
    next_steps = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    subject = relationship("Subject", back_populates="sessions")

    __table_args__ = (
        Index('idx_session_subject_date', 'subject_id', 'session_date'),
        Index('idx_session_status', 'session_status'),
    )

    def __repr__(self):
        return f"<Session(id={self.id}, subject_id={self.subject_id}, name={self.session_name})>"
