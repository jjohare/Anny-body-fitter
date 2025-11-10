# Anny Body Fitter - Test Configuration
# Copyright (C) 2025 NAVER Corp.
# Apache License, Version 2.0
"""
Pytest configuration and shared fixtures for London School TDD testing.

Provides mock implementations of external dependencies and test data fixtures.
"""
import pytest
import torch
import numpy as np
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import tempfile
import os


@pytest.fixture(scope="session")
def test_data_dir():
    """Provide path to test data directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def temp_dir():
    """Provide temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def device():
    """Provide device for testing (CPU by default)."""
    return torch.device("cpu")


@pytest.fixture
def dtype():
    """Provide default dtype for testing."""
    return torch.float32


@pytest.fixture
def batch_size():
    """Default batch size for testing."""
    return 2


@pytest.fixture
def mock_model(device, dtype):
    """
    Mock Anny model with essential attributes for testing.

    London TDD: Mock the model to test behavior without implementation.
    """
    model = Mock()
    model.device = device
    model.dtype = dtype
    model.bone_count = 53
    model.vertex_count = 19158

    # Mock phenotype labels
    model.phenotype_labels = [
        'gender', 'age', 'muscle', 'weight', 'height',
        'proportions', 'cupsize', 'firmness',
        'african', 'asian', 'caucasian'
    ]

    # Mock local change labels
    model.local_change_labels = ['nose_width', 'eye_size', 'mouth_width']

    # Mock bone labels
    model.bone_labels = [f'bone_{i}' for i in range(model.bone_count)]

    # Mock vertex attributes
    model.base_mesh_vertex_indices = torch.arange(model.vertex_count)
    model.template_vertices = torch.randn(model.vertex_count, 3, dtype=dtype, device=device)

    # Mock faces
    model.faces = torch.randint(0, model.vertex_count, (6000, 4), dtype=torch.int64)

    # Mock skinning weights
    model.vertex_bone_weights = torch.rand(model.vertex_count, 4, dtype=dtype, device=device)
    model.vertex_bone_weights /= model.vertex_bone_weights.sum(dim=-1, keepdim=True)
    model.vertex_bone_indices = torch.randint(0, model.bone_count, (model.vertex_count, 4))

    # Mock forward method with realistic vertex generation
    def mock_forward(pose_parameters=None, phenotype_kwargs=None,
                     local_changes_kwargs=None, pose_parameterization='root_relative_world'):
        batch_size = pose_parameters.shape[0] if pose_parameters is not None else 1

        # Generate realistic vertices based on phenotype parameters
        if phenotype_kwargs is not None:
            height_param = phenotype_kwargs.get('height', torch.tensor([0.5] * batch_size))
            weight_param = phenotype_kwargs.get('weight', torch.tensor([0.5] * batch_size))

            # Base height: 1.5m to 2.0m
            heights = 1.5 + height_param * 0.5
            # Width factor based on weight
            widths = 0.25 + weight_param * 0.15

            vertices = []
            for b in range(batch_size):
                # Generate humanoid-shaped vertices
                h = heights[b].item() if torch.is_tensor(heights) else heights
                w = widths[b].item() if torch.is_tensor(widths) else widths

                # Create realistic vertex distribution
                verts = torch.randn(model.vertex_count, 3, dtype=dtype, device=device)
                verts[:, 0] *= w  # width (x)
                verts[:, 1] *= w * 0.7  # depth (y)
                verts[:, 2] = verts[:, 2] * (h * 0.4) + (h * 0.5)  # height (z)

                vertices.append(verts)

            vertices_tensor = torch.stack(vertices)
        else:
            # Default random vertices with human proportions
            vertices_tensor = torch.randn(batch_size, model.vertex_count, 3, dtype=dtype, device=device)
            vertices_tensor[..., 0] *= 0.3  # width
            vertices_tensor[..., 1] *= 0.2  # depth
            vertices_tensor[..., 2] = vertices_tensor[..., 2] * 0.7 + 0.85  # height

        return {
            'vertices': vertices_tensor,
            'bone_poses': torch.eye(4, dtype=dtype, device=device)[None, None].repeat(batch_size, model.bone_count, 1, 1)
        }

    model.side_effect = mock_forward
    model.return_value = mock_forward()

    # Mock triangular faces method
    def get_triangular_faces():
        # Convert quad faces to triangular
        return torch.cat([model.faces[:, [0, 1, 2]], model.faces[:, [0, 2, 3]]], dim=0)

    model.get_triangular_faces = Mock(side_effect=get_triangular_faces)

    # Mock pose parameterization
    model.get_pose_parameterization = Mock(return_value=torch.eye(4)[None, None].repeat(2, model.bone_count, 1, 1))
    model.default_pose_parameterization = 'root_relative_world'

    return model


@pytest.fixture
def sample_vertices(device, dtype):
    """Generate sample vertex data for testing."""
    # Create a simple humanoid shape (approximate)
    n_vertices = 1000
    vertices = torch.randn(2, n_vertices, 3, dtype=dtype, device=device)

    # Scale to realistic human proportions (height ~1.7m)
    vertices[..., 0] *= 0.3  # width
    vertices[..., 1] *= 0.2  # depth
    vertices[..., 2] = vertices[..., 2] * 0.8 + 0.85  # height centered at 0.85m

    return vertices


@pytest.fixture
def sample_phenotype_params(batch_size, device, dtype):
    """Generate sample phenotype parameters."""
    return {
        'gender': torch.full((batch_size,), 0.5, dtype=dtype, device=device),
        'age': torch.full((batch_size,), 0.5, dtype=dtype, device=device),
        'muscle': torch.full((batch_size,), 0.5, dtype=dtype, device=device),
        'weight': torch.full((batch_size,), 0.5, dtype=dtype, device=device),
        'height': torch.full((batch_size,), 0.5, dtype=dtype, device=device),
        'proportions': torch.full((batch_size,), 0.5, dtype=dtype, device=device),
        'cupsize': torch.full((batch_size,), 0.5, dtype=dtype, device=device),
        'firmness': torch.full((batch_size,), 0.5, dtype=dtype, device=device),
        'african': torch.full((batch_size,), 0.0, dtype=dtype, device=device),
        'asian': torch.full((batch_size,), 0.0, dtype=dtype, device=device),
        'caucasian': torch.full((batch_size,), 1.0, dtype=dtype, device=device),
    }


@pytest.fixture
def sample_pose_parameters(batch_size, device, dtype):
    """Generate sample pose parameters (identity pose)."""
    bone_count = 53
    # Identity transformations (4x4 homogeneous matrices)
    return torch.eye(4, dtype=dtype, device=device)[None, None].repeat(batch_size, bone_count, 1, 1)


@pytest.fixture
def mock_cv_detector():
    """
    Mock computer vision landmark detector with realistic output.

    London TDD: Mock external CV dependencies.
    Uses enhanced MockLandmarkDetector from mocks.mock_vision.
    """
    from tests.mocks.mock_vision import MockLandmarkDetector

    # Return the enhanced detector
    return MockLandmarkDetector(confidence=0.95)


@pytest.fixture
def sample_image():
    """Generate sample test image."""
    # 640x480 RGB image
    return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)


@pytest.fixture
def mock_database_connection():
    """
    Mock database connection for testing.

    London TDD: Test database interactions without real DB.
    """
    connection = Mock()

    # Mock storage
    storage = {}

    def mock_insert(table, data):
        key = f"{table}_{len(storage)}"
        storage[key] = data
        return key

    def mock_query(table, query):
        return [v for k, v in storage.items() if k.startswith(table)]

    def mock_update(table, id, data):
        storage[f"{table}_{id}"] = data

    def mock_delete(table, id):
        key = f"{table}_{id}"
        if key in storage:
            del storage[key]

    connection.insert = Mock(side_effect=mock_insert)
    connection.query = Mock(side_effect=mock_query)
    connection.update = Mock(side_effect=mock_update)
    connection.delete = Mock(side_effect=mock_delete)
    connection.commit = Mock()
    connection.rollback = Mock()

    return connection


@pytest.fixture
def anthropometry_test_data(device, dtype):
    """Generate test data for anthropometry calculations."""
    # Create vertices for a simple geometric shape with known measurements
    height = 1.75  # meters
    waist_radius = 0.15  # meters

    # Simple cylinder approximation for testing
    n_height_points = 10
    n_waist_points = 20

    vertices = []
    for h in np.linspace(0, height, n_height_points):
        for angle in np.linspace(0, 2*np.pi, n_waist_points, endpoint=False):
            x = waist_radius * np.cos(angle)
            y = waist_radius * np.sin(angle)
            z = h
            vertices.append([x, y, z])

    vertices_tensor = torch.tensor(vertices, dtype=dtype, device=device)
    return vertices_tensor.unsqueeze(0)  # Add batch dimension


@pytest.fixture(autouse=True)
def reset_mocks(mock_model, mock_cv_detector, mock_database_connection):
    """Reset all mocks before each test."""
    yield
    mock_model.reset_mock()
    # MockLandmarkDetector has reset_counter, not reset_mock
    if hasattr(mock_cv_detector, 'reset_counter'):
        mock_cv_detector.reset_counter()
    elif hasattr(mock_cv_detector, 'reset_mock'):
        mock_cv_detector.reset_mock()
    mock_database_connection.reset_mock()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests with mocked dependencies"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer to run"
    )
    config.addinivalue_line(
        "markers", "performance: Performance benchmark tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add unit marker to tests in unit/ directory
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        # Add integration marker to tests in integration/ directory
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
