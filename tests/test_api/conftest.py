"""Test configuration and fixtures for API tests."""

import pytest
import asyncio
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import os

# Set test environment
os.environ["DISABLE_AUTH"] = "true"
os.environ["DATABASE_PATH"] = ":memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db():
    """Create temporary test database."""
    from src.api.services.database import DatabaseService

    db = DatabaseService(":memory:")
    await db.initialize()

    yield db

    await db.close()


@pytest.fixture
def client():
    """Create test client."""
    from src.api.main import app

    return TestClient(app)


@pytest.fixture
def sample_subject_data():
    """Sample subject data for testing."""
    return {
        "name": "Test Subject",
        "age": 30,
        "gender": "male",
        "height_cm": 180.0,
        "weight_kg": 75.0,
        "notes": "Test subject for API testing"
    }


@pytest.fixture
def sample_photo_metadata():
    """Sample photo metadata for testing."""
    return [{
        "photo_type": "front",
        "camera_height_cm": 150.0,
        "distance_cm": 300.0,
        "notes": "Test photo"
    }]


@pytest.fixture
def sample_fitting_request():
    """Sample fitting request for testing."""
    return {
        "optimization_iterations": 100,
        "use_shape_prior": True,
        "use_pose_prior": True,
        "lambda_shape": 0.01,
        "lambda_pose": 0.01
    }


@pytest.fixture
def sample_metrics_data():
    """Sample metrics data for testing."""
    return {
        "metrics": {
            "accuracy_score": 0.95,
            "precision": 0.92,
            "recall": 0.93,
            "f1_score": 0.925,
            "mean_error_cm": 1.2,
            "max_error_cm": 4.5
        },
        "ground_truth_available": True,
        "validation_method": "3D scanner comparison",
        "notes": "Test validation"
    }


@pytest.fixture
def temp_photo():
    """Create temporary test photo."""
    from PIL import Image
    import io

    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)

    return img_bytes
