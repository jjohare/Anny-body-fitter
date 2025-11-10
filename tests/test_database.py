"""
London TDD tests for database models and CRUD operations.
Uses mocks instead of real database connections.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from sqlalchemy.orm import Session

from src.database.models import (
    Subject, Measurement, ModelParameter,
    PerformanceMetric, PhotoRecord, Session as SessionModel
)
from src.database.schemas import (
    SubjectCreate, SubjectUpdate,
    MeasurementCreate,
    ModelParameterCreate,
    PerformanceMetricCreate,
    PhotoRecordCreate,
    SessionCreate, SessionUpdate
)
from src.database.crud import (
    subject as subject_crud,
    measurement as measurement_crud,
    model_parameter as model_parameter_crud,
    performance_metric as performance_metric_crud,
    photo_record as photo_record_crud,
    session as session_crud
)


class TestSubjectModel:
    """Test Subject model"""

    def test_subject_creation(self):
        """Test creating a Subject instance"""
        subject = Subject(
            id=1,
            name="John Doe",
            date_of_birth=datetime(1990, 1, 1),
            notes="Test subject"
        )

        assert subject.id == 1
        assert subject.name == "John Doe"
        assert subject.date_of_birth == datetime(1990, 1, 1)
        assert subject.notes == "Test subject"

    def test_subject_repr(self):
        """Test Subject string representation"""
        subject = Subject(id=1, name="John Doe")
        assert repr(subject) == "<Subject(id=1, name=John Doe)>"


class TestMeasurementModel:
    """Test Measurement model"""

    def test_measurement_creation(self):
        """Test creating a Measurement instance"""
        measurement = Measurement(
            id=1,
            subject_id=1,
            height=180.0,
            weight=75.0,
            chest_circumference=95.0
        )

        assert measurement.id == 1
        assert measurement.subject_id == 1
        assert measurement.height == 180.0
        assert measurement.weight == 75.0
        assert measurement.chest_circumference == 95.0


class TestModelParameterModel:
    """Test ModelParameter model"""

    def test_model_parameter_creation(self):
        """Test creating a ModelParameter instance"""
        param = ModelParameter(
            id=1,
            subject_id=1,
            height_param=1.0,
            weight_param=0.5,
            model_version="v1.0"
        )

        assert param.id == 1
        assert param.subject_id == 1
        assert param.model_version == "v1.0"


class TestPerformanceMetricModel:
    """Test PerformanceMetric model"""

    def test_performance_metric_creation(self):
        """Test creating a PerformanceMetric instance"""
        metric = PerformanceMetric(
            id=1,
            subject_id=1,
            fitting_error=0.05,
            processing_time=2.5,
            metric_type="initial_fit"
        )

        assert metric.id == 1
        assert metric.fitting_error == 0.05
        assert metric.metric_type == "initial_fit"


class TestPhotoRecordModel:
    """Test PhotoRecord model"""

    def test_photo_record_creation(self):
        """Test creating a PhotoRecord instance"""
        photo = PhotoRecord(
            id=1,
            subject_id=1,
            filename="photo.jpg",
            file_path="/uploads/photo.jpg",
            photo_type="front"
        )

        assert photo.id == 1
        assert photo.filename == "photo.jpg"
        assert photo.photo_type == "front"


class TestSessionModel:
    """Test Session model"""

    def test_session_creation(self):
        """Test creating a Session instance"""
        session = SessionModel(
            id=1,
            subject_id=1,
            session_name="Initial Fitting",
            session_type="initial",
            session_status="in_progress"
        )

        assert session.id == 1
        assert session.session_name == "Initial Fitting"
        assert session.session_status == "in_progress"


class TestCRUDSubject:
    """Test CRUD operations for Subject"""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        return Mock(spec=Session)

    @pytest.fixture
    def sample_subject_create(self):
        """Create a sample SubjectCreate schema"""
        return SubjectCreate(
            name="John Doe",
            date_of_birth=datetime(1990, 1, 1),
            notes="Test subject"
        )

    def test_create_subject(self, mock_db, sample_subject_create):
        """Test creating a subject"""
        # Mock the Subject model
        mock_subject = Mock(spec=Subject)
        mock_subject.id = 1
        mock_subject.name = "John Doe"

        with patch('src.database.crud.Subject') as MockSubject:
            MockSubject.return_value = mock_subject

            result = subject_crud.create(mock_db, sample_subject_create)

            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

    def test_get_subject(self, mock_db):
        """Test getting a subject by ID"""
        mock_subject = Mock(spec=Subject)
        mock_subject.id = 1

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_subject
        mock_db.query.return_value = mock_query

        result = subject_crud.get(mock_db, id=1)

        mock_db.query.assert_called_once_with(Subject)
        assert result == mock_subject

    def test_get_active_subjects(self, mock_db):
        """Test getting active subjects"""
        mock_subjects = [Mock(spec=Subject), Mock(spec=Subject)]

        mock_query = Mock()
        mock_query.filter.return_value.offset.return_value.limit.return_value.all.return_value = mock_subjects
        mock_db.query.return_value = mock_query

        result = subject_crud.get_active(mock_db)

        assert len(result) == 2
        mock_db.query.assert_called_once_with(Subject)

    def test_soft_delete_subject(self, mock_db):
        """Test soft deleting a subject"""
        mock_subject = Mock(spec=Subject)
        mock_subject.id = 1
        mock_subject.is_active = True

        with patch.object(subject_crud, 'get', return_value=mock_subject):
            result = subject_crud.soft_delete(mock_db, id=1)

            assert result.is_active == False
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()


class TestCRUDMeasurement:
    """Test CRUD operations for Measurement"""

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    def test_get_by_subject(self, mock_db):
        """Test getting measurements by subject ID"""
        mock_measurements = [Mock(spec=Measurement), Mock(spec=Measurement)]

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_measurements
        mock_db.query.return_value = mock_query

        result = measurement_crud.get_by_subject(mock_db, subject_id=1)

        assert len(result) == 2
        mock_db.query.assert_called_once_with(Measurement)

    def test_get_latest_measurement(self, mock_db):
        """Test getting the latest measurement"""
        mock_measurement = Mock(spec=Measurement)
        mock_measurement.id = 1

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = mock_measurement
        mock_db.query.return_value = mock_query

        result = measurement_crud.get_latest(mock_db, subject_id=1)

        assert result == mock_measurement


class TestCRUDModelParameter:
    """Test CRUD operations for ModelParameter"""

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    def test_get_by_subject(self, mock_db):
        """Test getting model parameters by subject ID"""
        mock_params = [Mock(spec=ModelParameter)]

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_params
        mock_db.query.return_value = mock_query

        result = model_parameter_crud.get_by_subject(mock_db, subject_id=1)

        assert len(result) == 1

    def test_get_by_version(self, mock_db):
        """Test getting model parameters by version"""
        mock_params = [Mock(spec=ModelParameter)]

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = mock_params
        mock_db.query.return_value = mock_query

        result = model_parameter_crud.get_by_version(mock_db, subject_id=1, model_version="v1.0")

        assert len(result) == 1


class TestCRUDPerformanceMetric:
    """Test CRUD operations for PerformanceMetric"""

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    def test_get_by_type(self, mock_db):
        """Test getting performance metrics by type"""
        mock_metrics = [Mock(spec=PerformanceMetric)]

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = mock_metrics
        mock_db.query.return_value = mock_query

        result = performance_metric_crud.get_by_type(mock_db, subject_id=1, metric_type="initial_fit")

        assert len(result) == 1


class TestCRUDPhotoRecord:
    """Test CRUD operations for PhotoRecord"""

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    def test_get_unprocessed_photos(self, mock_db):
        """Test getting unprocessed photos"""
        mock_photos = [Mock(spec=PhotoRecord)]

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = mock_photos
        mock_db.query.return_value = mock_query

        result = photo_record_crud.get_unprocessed(mock_db)

        assert len(result) == 1

    def test_mark_processed(self, mock_db):
        """Test marking a photo as processed"""
        mock_photo = Mock(spec=PhotoRecord)
        mock_photo.id = 1
        mock_photo.is_processed = False

        with patch.object(photo_record_crud, 'get', return_value=mock_photo):
            result = photo_record_crud.mark_processed(mock_db, id=1)

            assert result.is_processed == True
            assert result.processing_status == "completed"


class TestCRUDSession:
    """Test CRUD operations for Session"""

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    def test_get_by_status(self, mock_db):
        """Test getting sessions by status"""
        mock_sessions = [Mock(spec=SessionModel)]

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_sessions
        mock_db.query.return_value = mock_query

        result = session_crud.get_by_status(mock_db, status="in_progress")

        assert len(result) == 1

    def test_complete_session(self, mock_db):
        """Test completing a session"""
        mock_session = Mock(spec=SessionModel)
        mock_session.id = 1
        mock_session.session_status = "in_progress"

        with patch.object(session_crud, 'get', return_value=mock_session):
            result = session_crud.complete_session(mock_db, id=1)

            assert result.session_status == "completed"
            mock_db.commit.assert_called_once()


class TestSchemaValidation:
    """Test Pydantic schema validation"""

    def test_subject_create_validation(self):
        """Test SubjectCreate schema validation"""
        subject = SubjectCreate(
            name="John Doe",
            date_of_birth=datetime(1990, 1, 1),
            notes="Test"
        )

        assert subject.name == "John Doe"
        assert isinstance(subject.date_of_birth, datetime)

    def test_measurement_create_validation(self):
        """Test MeasurementCreate schema validation"""
        measurement = MeasurementCreate(
            subject_id=1,
            height=180.0,
            weight=75.0
        )

        assert measurement.subject_id == 1
        assert measurement.height == 180.0

    def test_measurement_negative_values(self):
        """Test that negative values are rejected"""
        with pytest.raises(Exception):
            MeasurementCreate(
                subject_id=1,
                height=-180.0  # Should fail validation
            )
