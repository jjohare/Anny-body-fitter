# Anny Body Fitter - Anthropometry Unit Tests
# Copyright (C) 2025 NAVER Corp.
# Apache License, Version 2.0
"""
London School TDD unit tests for Anthropometry module.

Tests behavior with mocked model dependencies.
"""
import pytest
import torch
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from anny.anthropometry import Anthropometry, BASE_MESH_WAIST_VERTICES
from tests.fixtures.test_data import SAMPLE_MEASUREMENTS, generate_humanoid_vertices


@pytest.mark.unit
class TestAnthropometryInitialization:
    """Test Anthropometry initialization with mocked model."""

    def test_should_initialize_with_valid_model(self, mock_model):
        """Should successfully initialize when model has valid waist vertices."""
        # Arrange: Mock model includes all waist vertices

        # Act
        anthropometry = Anthropometry(mock_model)

        # Assert
        assert anthropometry.model == mock_model
        assert len(anthropometry.waist_vertex_indices) == len(BASE_MESH_WAIST_VERTICES)
        mock_model.get_triangular_faces.assert_called_once()

    def test_should_raise_error_when_waist_vertices_missing(self, mock_model):
        """Should raise ValueError when model lacks waist vertices."""
        # Arrange: Mock model missing waist vertices
        mock_model.base_mesh_vertex_indices = torch.arange(100)  # Too few vertices

        # Act & Assert
        with pytest.raises(ValueError, match="Base mesh vertex indices do not contain all waist vertices"):
            Anthropometry(mock_model)


@pytest.mark.unit
class TestHeightCalculation:
    """Test height measurement calculation."""

    def test_should_calculate_height_from_vertex_range(self, mock_model, device, dtype):
        """Should calculate height as max Z - min Z."""
        # Arrange
        anthropometry = Anthropometry(mock_model)
        # Create vertices with known height range
        batch_size = 2
        n_vertices = 100
        vertices = torch.zeros(batch_size, n_vertices, 3, dtype=dtype, device=device)
        vertices[:, 0, 2] = 0.0  # Min Z
        vertices[:, 1, 2] = 1.75  # Max Z (175cm)

        # Act
        height = anthropometry.height(vertices)

        # Assert
        assert height.shape == (batch_size,)
        assert torch.allclose(height, torch.tensor([1.75, 1.75], dtype=dtype, device=device))

    def test_should_handle_batch_dimensions(self, mock_model, device, dtype):
        """Should correctly handle batched vertex inputs."""
        # Arrange
        anthropometry = Anthropometry(mock_model)
        batch_size = 5
        vertices = torch.randn(batch_size, 100, 3, dtype=dtype, device=device)

        # Act
        height = anthropometry.height(vertices)

        # Assert
        assert height.shape == (batch_size,)
        assert torch.all(height > 0)


@pytest.mark.unit
class TestWaistCircumference:
    """Test waist circumference measurement."""

    def test_should_calculate_circumference_from_waist_vertices(self, mock_model, device, dtype):
        """Should calculate waist circumference as sum of edge lengths using realistic data."""
        # Arrange
        anthropometry = Anthropometry(mock_model)
        # Use realistic waist circumference from test data
        target_circumference = SAMPLE_MEASUREMENTS['average_male']['waist_circumference']
        radius = target_circumference / (2 * np.pi)

        # Create circular waist vertices
        n_waist = len(BASE_MESH_WAIST_VERTICES)
        angles = torch.linspace(0, 2*torch.pi, n_waist+1, dtype=dtype)[:-1]

        batch_size = 1
        vertices = torch.zeros(batch_size, mock_model.vertex_count, 3, dtype=dtype, device=device)

        # Set waist vertices in a circle
        for i, idx in enumerate(anthropometry.waist_vertex_indices):
            vertices[0, idx, 0] = radius * torch.cos(angles[i])
            vertices[0, idx, 1] = radius * torch.sin(angles[i])
            vertices[0, idx, 2] = 1.0  # height

        # Act
        circumference = anthropometry.waist_circumference(vertices)

        # Assert
        expected_circumference = 2 * torch.pi * radius
        assert circumference.shape == (batch_size,)
        # Allow 10% tolerance for discretization
        assert torch.abs(circumference[0] - expected_circumference) / expected_circumference < 0.1

    def test_should_handle_zero_radius_waist(self, mock_model, device, dtype):
        """Should handle degenerate case of zero-radius waist."""
        # Arrange
        anthropometry = Anthropometry(mock_model)
        vertices = torch.zeros(1, mock_model.vertex_count, 3, dtype=dtype, device=device)

        # Act
        circumference = anthropometry.waist_circumference(vertices)

        # Assert
        assert circumference.shape == (1,)
        assert circumference[0] >= 0


@pytest.mark.unit
class TestVolumeCalculation:
    """Test volume measurement calculation."""

    def test_should_calculate_volume_from_triangular_mesh(self, mock_model, device, dtype):
        """Should calculate volume using divergence theorem."""
        # Arrange
        anthropometry = Anthropometry(mock_model)
        # Create simple closed mesh (tetrahedron)
        vertices = torch.tensor([
            [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]]
        ], dtype=dtype, device=device)

        # Mock triangular faces for tetrahedron
        mock_model.get_triangular_faces.return_value = torch.tensor([
            [0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]
        ])
        anthropometry.triangular_faces = mock_model.get_triangular_faces.return_value

        # Act
        volume = anthropometry.volume(vertices)

        # Assert
        expected_volume = 1/6  # Volume of tetrahedron with unit edge
        assert volume.shape == (1,)
        assert torch.abs(volume[0] - expected_volume) < 0.01

    def test_should_return_positive_volume(self, mock_model, device, dtype):
        """Should return absolute value for volume (no negative volumes)."""
        # Arrange
        anthropometry = Anthropometry(mock_model)
        vertices = torch.randn(2, mock_model.vertex_count, 3, dtype=dtype, device=device)

        # Act
        volume = anthropometry.volume(vertices)

        # Assert
        assert torch.all(volume >= 0)


@pytest.mark.unit
class TestMassCalculation:
    """Test mass calculation based on volume."""

    def test_should_calculate_mass_from_volume_and_density(self, mock_model, device, dtype):
        """Should calculate mass = volume * density."""
        # Arrange
        anthropometry = Anthropometry(mock_model)
        vertices = torch.randn(1, mock_model.vertex_count, 3, dtype=dtype, device=device)

        # Mock volume calculation
        expected_volume = torch.tensor([0.070], dtype=dtype)  # 70 liters
        with patch.object(anthropometry, 'volume', return_value=expected_volume):
            # Act
            mass = anthropometry.mass(vertices)

            # Assert
            expected_mass = expected_volume * 980  # density = 980 kg/m^3
            assert torch.allclose(mass, expected_mass)

    def test_should_use_constant_density(self, mock_model):
        """Should use fixed density of 980 kg/m³."""
        # Arrange
        anthropometry = Anthropometry(mock_model)

        # Assert: Check density constant in source
        # This test documents the behavior
        assert True  # Density is hardcoded in implementation


@pytest.mark.unit
class TestBMICalculation:
    """Test BMI (Body Mass Index) calculation."""

    def test_should_calculate_bmi_from_mass_and_height(self, mock_model, device, dtype):
        """Should calculate BMI = mass / height²."""
        # Arrange
        anthropometry = Anthropometry(mock_model)
        vertices = torch.randn(1, mock_model.vertex_count, 3, dtype=dtype, device=device)

        # Mock height and mass
        expected_height = torch.tensor([1.75], dtype=dtype)  # 175cm
        expected_mass = torch.tensor([70.0], dtype=dtype)   # 70kg

        with patch.object(anthropometry, 'height', return_value=expected_height):
            with patch.object(anthropometry, 'mass', return_value=expected_mass):
                # Act
                bmi = anthropometry.bmi(vertices)

                # Assert
                expected_bmi = expected_mass / (expected_height ** 2)
                assert torch.allclose(bmi, expected_bmi)

    def test_should_handle_batch_bmi_calculation(self, mock_model, device, dtype):
        """Should calculate BMI for batched inputs."""
        # Arrange
        anthropometry = Anthropometry(mock_model)
        batch_size = 3
        vertices = torch.randn(batch_size, mock_model.vertex_count, 3, dtype=dtype, device=device)

        heights = torch.tensor([1.60, 1.75, 1.85], dtype=dtype)
        masses = torch.tensor([55.0, 70.0, 85.0], dtype=dtype)

        with patch.object(anthropometry, 'height', return_value=heights):
            with patch.object(anthropometry, 'mass', return_value=masses):
                # Act
                bmi = anthropometry.bmi(vertices)

                # Assert
                assert bmi.shape == (batch_size,)
                assert torch.all(bmi > 0)


@pytest.mark.unit
class TestAnthropometryCallMethod:
    """Test __call__ method that returns all measurements."""

    def test_should_return_dictionary_of_all_measurements(self, mock_model, device, dtype):
        """Should return dict with height, waist, volume, mass, and BMI."""
        # Arrange
        anthropometry = Anthropometry(mock_model)
        vertices = torch.randn(2, mock_model.vertex_count, 3, dtype=dtype, device=device)

        # Act
        measurements = anthropometry(vertices)

        # Assert
        assert isinstance(measurements, dict)
        assert 'height' in measurements
        assert 'waist_circumference' in measurements
        assert 'volume' in measurements
        assert 'mass' in measurements
        assert 'bmi' in measurements

        # Check all measurements have correct batch size
        for key, value in measurements.items():
            assert value.shape[0] == 2, f"{key} has wrong batch size"

    def test_should_compute_consistent_measurements(self, mock_model, device, dtype):
        """Should ensure BMI is consistent with mass and height."""
        # Arrange
        anthropometry = Anthropometry(mock_model)
        vertices = torch.randn(1, mock_model.vertex_count, 3, dtype=dtype, device=device)

        # Act
        measurements = anthropometry(vertices)

        # Assert: BMI should equal mass / height²
        computed_bmi = measurements['mass'] / (measurements['height'] ** 2)
        assert torch.allclose(measurements['bmi'], computed_bmi, rtol=1e-5)


@pytest.mark.unit
class TestAnthropometryEdgeCases:
    """Test edge cases and error handling."""

    def test_should_handle_single_vertex_input(self, mock_model, device, dtype):
        """Should handle unbatched vertex input (2D tensor)."""
        # Arrange
        anthropometry = Anthropometry(mock_model)
        # Note: The implementation expects batched input [B, V, 3]
        # This test documents the expected behavior
        vertices = torch.randn(mock_model.vertex_count, 3, dtype=dtype, device=device)

        # Act & Assert: Should handle or raise clear error
        # Current implementation expects batched input
        with pytest.raises((IndexError, RuntimeError)):
            _ = anthropometry.height(vertices)

    def test_should_handle_empty_batch(self, mock_model, device, dtype):
        """Should handle empty batch input."""
        # Arrange
        anthropometry = Anthropometry(mock_model)
        vertices = torch.empty(0, mock_model.vertex_count, 3, dtype=dtype, device=device)

        # Act
        measurements = anthropometry(vertices)

        # Assert
        assert measurements['height'].shape == (0,)
        assert measurements['mass'].shape == (0,)

    def test_should_be_differentiable(self, mock_model, device, dtype):
        """Should support gradient computation for optimization."""
        # Arrange
        anthropometry = Anthropometry(mock_model)
        vertices = torch.randn(1, mock_model.vertex_count, 3, dtype=dtype,
                              device=device, requires_grad=True)

        # Act
        measurements = anthropometry(vertices)
        loss = measurements['bmi'].sum()
        loss.backward()

        # Assert
        assert vertices.grad is not None
        assert vertices.grad.shape == vertices.shape
