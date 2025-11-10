"""
Database integration tests.
Tests real SQLite database operations with full CRUD, relationships, and transactions.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from src.database.models import Base, Subject, Measurement, ModelParameter, PerformanceMetric, PhotoRecord, Session as SessionModel


@pytest.fixture
def sync_db_session():
    """
    Create an in-memory SQLite database session for testing.
    Uses synchronous SQLAlchemy for integration tests.
    """
    # Create in-memory database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True for SQL debugging
    )

    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    yield session

    # Cleanup
    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


class TestDatabaseCRUD:
    """Test basic CRUD operations."""

    def test_create_subject(self, sync_db_session: Session):
        """Test creating a subject."""
        subject = Subject(
            name="John Doe",
            date_of_birth=datetime(1990, 1, 1),
            notes="Test subject"
        )

        sync_db_session.add(subject)
        sync_db_session.commit()
        sync_db_session.refresh(subject)

        assert subject.id is not None
        assert subject.name == "John Doe"
        assert subject.is_active is True
        assert subject.created_at is not None

    def test_read_subject(self, sync_db_session: Session):
        """Test reading a subject."""
        # Create subject
        subject = Subject(
            name="Jane Doe",
            date_of_birth=datetime(1995, 5, 15)
        )
        sync_db_session.add(subject)
        sync_db_session.commit()

        # Read subject
        retrieved = sync_db_session.query(Subject).filter(Subject.name == "Jane Doe").first()

        assert retrieved is not None
        assert retrieved.name == "Jane Doe"
        assert retrieved.date_of_birth.year == 1995

    def test_update_subject(self, sync_db_session: Session):
        """Test updating a subject."""
        # Create subject
        subject = Subject(
            name="Update Test",
            date_of_birth=datetime(2000, 1, 1)
        )
        sync_db_session.add(subject)
        sync_db_session.commit()

        # Update subject
        subject.name = "Updated Name"
        subject.notes = "Updated notes"
        sync_db_session.commit()
        sync_db_session.refresh(subject)

        assert subject.name == "Updated Name"
        assert subject.notes == "Updated notes"
        assert subject.updated_at > subject.created_at

    def test_delete_subject(self, sync_db_session: Session):
        """Test soft delete and hard delete."""
        # Create subject
        subject = Subject(
            name="Delete Test",
            date_of_birth=datetime(1985, 3, 20)
        )
        sync_db_session.add(subject)
        sync_db_session.commit()
        subject_id = subject.id

        # Soft delete
        subject.is_active = False
        sync_db_session.commit()

        # Verify soft delete
        inactive = sync_db_session.query(Subject).filter(Subject.id == subject_id).first()
        assert inactive.is_active is False

        # Hard delete
        sync_db_session.delete(subject)
        sync_db_session.commit()

        # Verify hard delete
        deleted = sync_db_session.query(Subject).filter(Subject.id == subject_id).first()
        assert deleted is None


class TestDatabaseRelationships:
    """Test relationships between entities."""

    def test_subject_measurements_relationship(self, sync_db_session: Session):
        """Test one-to-many relationship between Subject and Measurements."""
        # Create subject
        subject = Subject(
            name="Measurement Test",
            date_of_birth=datetime(1992, 7, 10)
        )
        sync_db_session.add(subject)
        sync_db_session.commit()

        # Add measurements
        measurement1 = Measurement(
            subject_id=subject.id,
            height=175.5,
            weight=70.0,
            chest_circumference=95.0,
            waist_circumference=80.0
        )
        measurement2 = Measurement(
            subject_id=subject.id,
            height=176.0,
            weight=71.0,
            chest_circumference=96.0,
            waist_circumference=81.0
        )

        sync_db_session.add_all([measurement1, measurement2])
        sync_db_session.commit()

        # Test relationship
        sync_db_session.refresh(subject)
        assert len(subject.measurements) == 2
        assert subject.measurements[0].height in [175.5, 176.0]

    def test_subject_model_parameters_relationship(self, sync_db_session: Session):
        """Test one-to-many relationship with model parameters."""
        subject = Subject(
            name="Model Test",
            date_of_birth=datetime(1988, 4, 15)
        )
        sync_db_session.add(subject)
        sync_db_session.commit()

        # Add model parameters
        params = ModelParameter(
            subject_id=subject.id,
            height_param=1.75,
            weight_param=70.0,
            chest_param=0.95,
            waist_param=0.80,
            shape_param_1=0.1,
            shape_param_2=-0.2,
            model_version="1.0",
            confidence_score=0.92
        )

        sync_db_session.add(params)
        sync_db_session.commit()

        # Test relationship
        sync_db_session.refresh(subject)
        assert len(subject.model_parameters) == 1
        assert subject.model_parameters[0].confidence_score == 0.92

    def test_cascade_delete(self, sync_db_session: Session):
        """Test cascade deletion of related records."""
        # Create subject with related records
        subject = Subject(
            name="Cascade Test",
            date_of_birth=datetime(1991, 9, 25)
        )
        sync_db_session.add(subject)
        sync_db_session.commit()

        # Add related records
        measurement = Measurement(subject_id=subject.id, height=180.0)
        photo = PhotoRecord(
            subject_id=subject.id,
            filename="test.jpg",
            file_path="/tmp/test.jpg",
            photo_type="front"
        )
        metric = PerformanceMetric(
            subject_id=subject.id,
            fitting_error=0.05,
            processing_time=12.5
        )

        sync_db_session.add_all([measurement, photo, metric])
        sync_db_session.commit()

        # Get IDs
        measurement_id = measurement.id
        photo_id = photo.id
        metric_id = metric.id

        # Delete subject
        sync_db_session.delete(subject)
        sync_db_session.commit()

        # Verify cascade deletion
        assert sync_db_session.query(Measurement).filter(Measurement.id == measurement_id).first() is None
        assert sync_db_session.query(PhotoRecord).filter(PhotoRecord.id == photo_id).first() is None
        assert sync_db_session.query(PerformanceMetric).filter(PerformanceMetric.id == metric_id).first() is None


class TestDatabaseTransactions:
    """Test transaction handling and rollback."""

    def test_transaction_commit(self, sync_db_session: Session):
        """Test successful transaction commit."""
        # Start transaction (implicit)
        subject1 = Subject(name="TX Test 1", date_of_birth=datetime(1990, 1, 1))
        subject2 = Subject(name="TX Test 2", date_of_birth=datetime(1991, 1, 1))

        sync_db_session.add_all([subject1, subject2])
        sync_db_session.commit()

        # Verify both committed
        count = sync_db_session.query(Subject).filter(
            Subject.name.in_(["TX Test 1", "TX Test 2"])
        ).count()
        assert count == 2

    def test_transaction_rollback(self, sync_db_session: Session):
        """Test transaction rollback on error."""
        # Create initial subject
        subject1 = Subject(name="Initial", date_of_birth=datetime(1990, 1, 1))
        sync_db_session.add(subject1)
        sync_db_session.commit()

        initial_count = sync_db_session.query(Subject).count()

        # Try to create invalid data and rollback
        try:
            subject2 = Subject(name="Invalid", date_of_birth=datetime(1995, 1, 1))
            sync_db_session.add(subject2)
            # Simulate error
            raise Exception("Simulated error")
        except Exception:
            sync_db_session.rollback()

        # Verify rollback
        final_count = sync_db_session.query(Subject).count()
        assert final_count == initial_count


class TestDatabaseIndexes:
    """Test that indexes work correctly."""

    def test_subject_name_index(self, sync_db_session: Session):
        """Test querying with indexed field is efficient."""
        # Create multiple subjects
        for i in range(100):
            subject = Subject(
                name=f"Subject {i:03d}",
                date_of_birth=datetime(1990 + i % 30, 1, 1)
            )
            sync_db_session.add(subject)
        sync_db_session.commit()

        # Query using indexed name field
        result = sync_db_session.query(Subject).filter(Subject.name == "Subject 050").first()
        assert result is not None
        assert result.name == "Subject 050"

    def test_active_index(self, sync_db_session: Session):
        """Test querying with is_active index."""
        # Create active and inactive subjects
        for i in range(50):
            subject = Subject(
                name=f"Active {i}",
                date_of_birth=datetime(1990, 1, 1),
                is_active=(i % 2 == 0)
            )
            sync_db_session.add(subject)
        sync_db_session.commit()

        # Query active subjects
        active_count = sync_db_session.query(Subject).filter(Subject.is_active == True).count()
        assert active_count == 25


class TestDatabaseComplexQueries:
    """Test complex queries and joins."""

    def test_join_subject_measurements(self, sync_db_session: Session):
        """Test joining subjects with their measurements."""
        # Create subjects with measurements
        subject1 = Subject(name="Join Test 1", date_of_birth=datetime(1990, 1, 1))
        subject2 = Subject(name="Join Test 2", date_of_birth=datetime(1992, 1, 1))
        sync_db_session.add_all([subject1, subject2])
        sync_db_session.commit()

        measurement1 = Measurement(subject_id=subject1.id, height=175.0)
        measurement2 = Measurement(subject_id=subject1.id, height=176.0)
        measurement3 = Measurement(subject_id=subject2.id, height=180.0)
        sync_db_session.add_all([measurement1, measurement2, measurement3])
        sync_db_session.commit()

        # Query with join
        results = sync_db_session.query(Subject, Measurement).join(
            Measurement, Subject.id == Measurement.subject_id
        ).filter(Subject.name == "Join Test 1").all()

        assert len(results) == 2
        for subject, measurement in results:
            assert subject.name == "Join Test 1"
            assert measurement.height in [175.0, 176.0]

    def test_aggregate_queries(self, sync_db_session: Session):
        """Test aggregate functions."""
        from sqlalchemy import func

        # Create test data
        subject = Subject(name="Aggregate Test", date_of_birth=datetime(1990, 1, 1))
        sync_db_session.add(subject)
        sync_db_session.commit()

        for height in [170.0, 175.0, 180.0, 185.0]:
            measurement = Measurement(subject_id=subject.id, height=height, weight=70.0)
            sync_db_session.add(measurement)
        sync_db_session.commit()

        # Test aggregates
        avg_height = sync_db_session.query(func.avg(Measurement.height)).filter(
            Measurement.subject_id == subject.id
        ).scalar()

        assert avg_height == 177.5


class TestDatabaseEncryption:
    """Test encryption integration (if implemented)."""

    def test_sensitive_field_storage(self, sync_db_session: Session):
        """Test that sensitive fields can be stored (encryption would be at app level)."""
        # Note: Actual encryption would be handled by application layer
        # This tests that fields designed for encryption can store encrypted data

        encrypted_name = "encrypted_john_doe_xyz123"  # Simulated encrypted value

        subject = Subject(
            name=encrypted_name,
            date_of_birth=datetime(1990, 1, 1)
        )
        sync_db_session.add(subject)
        sync_db_session.commit()

        # Retrieve and verify
        retrieved = sync_db_session.query(Subject).filter(Subject.id == subject.id).first()
        assert retrieved.name == encrypted_name


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
