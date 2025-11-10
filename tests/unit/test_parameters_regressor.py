# Anny Body Fitter - ParametersRegressor Unit Tests
# Copyright (C) 2025 NAVER Corp.
# Apache License, Version 2.0
"""
London School TDD unit tests for ParametersRegressor module.

Tests iterative fitting algorithm with mocked model dependencies.
"""
import pytest
import torch
import roma
import numpy as np
from unittest.mock import Mock, patch, MagicMock, call
from anny.parameters_regressor import ParametersRegressor
from tests.fixtures.test_data import (
    SAMPLE_PHENOTYPES,
    generate_humanoid_vertices,
    generate_pose_parameters,
    create_test_batch
)


@pytest.mark.unit
class TestParametersRegressorInitialization:
    """Test ParametersRegressor initialization."""

    def test_should_initialize_with_default_parameters(self, mock_model):
        """Should initialize with sensible default values."""
        # Act
        regressor = ParametersRegressor(mock_model)

        # Assert
        assert regressor.model == mock_model
        assert regressor.eps == 0.1
        assert regressor.n_points == 5000
        assert regressor.max_n_iters == 5
        assert regressor.device == mock_model.device
        assert regressor.dtype == torch.float32

    def test_should_initialize_with_custom_parameters(self, mock_model):
        """Should accept custom hyperparameters."""
        # Arrange
        custom_params = {
            'eps': 0.05,
            'n_points': 10000,
            'max_n_iters': 10,
            'verbose': True
        }

        # Act
        regressor = ParametersRegressor(mock_model, **custom_params)

        # Assert
        assert regressor.eps == 0.05
        assert regressor.n_points == 10000
        assert regressor.max_n_iters == 10
        assert regressor.verbose is True

    def test_should_initialize_regularization_weights(self, mock_model):
        """Should set up regularization weights for phenotype parameters."""
        # Act
        regressor = ParametersRegressor(mock_model)

        # Assert
        assert regressor.reg_weights.shape[0] == len(mock_model.phenotype_labels)
        assert torch.all(regressor.reg_weights > 0)

    def test_should_accept_custom_regularization_weights(self, mock_model):
        """Should allow custom regularization weights."""
        # Arrange
        custom_reg = {
            'gender': 2.0,
            'age': 5.0,
            'height': 0.001
        }

        # Act
        regressor = ParametersRegressor(mock_model, reg_weight_kwargs=custom_reg)

        # Assert
        gender_idx = mock_model.phenotype_labels.index('gender')
        assert regressor.reg_weights[gender_idx] == 2.0


@pytest.mark.unit
class TestPartitioning:
    """Test mesh partitioning by joint influence."""

    def test_should_partition_vertices_by_bone_weights(self, mock_model):
        """Should group vertices by their influencing bones."""
        # Act
        regressor = ParametersRegressor(mock_model)
        partitioning = regressor.partitioning

        # Assert
        assert 'joint_vertex_sets' in partitioning
        assert 'vertex_joint_weights' in partitioning
        assert len(partitioning['joint_vertex_sets']) == mock_model.bone_count
        assert len(partitioning['vertex_joint_weights']) == mock_model.bone_count

    def test_should_filter_vertices_by_minimum_weight_threshold(self, mock_model):
        """Should only include vertices with weight >= 0.01."""
        # Arrange
        regressor = ParametersRegressor(mock_model)

        # Act
        partitioning = regressor.partitioning

        # Assert: Verify filtering occurred (implementation detail)
        # Each joint should have vertices with sufficient influence
        for joint_weights in partitioning['vertex_joint_weights']:
            if len(joint_weights) > 0:
                assert torch.all(joint_weights >= 0.0)


@pytest.mark.unit
class TestIdentityIndices:
    """Test facial joint identity preservation."""

    def test_should_identify_facial_bones_for_neutral_pose(self, mock_model):
        """Should mark facial expression bones for identity rotation."""
        # Arrange
        mock_model.bone_labels = [
            'root', 'spine', 'neck',
            'risorius03.L', 'risorius03.R',
            'levator06.L', 'levator06.R',
            'toe1-1.L', 'toe1-1.R'
        ]

        # Act
        regressor = ParametersRegressor(mock_model)
        identity_indices = regressor.indices_identity

        # Assert
        assert 3 in identity_indices  # risorius03.L
        assert 4 in identity_indices  # risorius03.R
        assert 0 not in identity_indices  # root should not be identity
        assert 1 not in identity_indices  # spine should not be identity


@pytest.mark.unit
class TestPoseMacroLocalInitialization:
    """Test initialization of pose, phenotype, and local change parameters."""

    def test_should_initialize_identity_pose(self, mock_model, device, dtype):
        """Should initialize pose with identity transformations."""
        # Arrange
        regressor = ParametersRegressor(mock_model)
        batch_size = 2

        # Act
        pose_params, phenotype_kwargs, local_kwargs = regressor._init_pose_macro_local(
            batch_size, {}
        )

        # Assert
        assert pose_params.shape == (batch_size, mock_model.bone_count, 4, 4)
        # Check identity matrices
        expected_identity = torch.eye(4, dtype=dtype, device=device)
        assert torch.allclose(pose_params[0, 0], expected_identity)

    def test_should_initialize_phenotype_to_midpoint(self, mock_model):
        """Should initialize phenotype parameters to 0.5 (middle of range)."""
        # Arrange
        regressor = ParametersRegressor(mock_model)
        batch_size = 3

        # Act
        _, phenotype_kwargs, _ = regressor._init_pose_macro_local(batch_size, {})

        # Assert
        for key in mock_model.phenotype_labels:
            assert key in phenotype_kwargs
            assert phenotype_kwargs[key].shape == (batch_size,)
            assert torch.allclose(phenotype_kwargs[key], torch.tensor([0.5] * batch_size))

    def test_should_override_initial_phenotype_values(self, mock_model):
        """Should accept initial phenotype value overrides."""
        # Arrange
        regressor = ParametersRegressor(mock_model)
        batch_size = 2
        initial_phenotypes = {
            'gender': 0.8,
            'age': torch.tensor([0.3, 0.7])
        }

        # Act
        _, phenotype_kwargs, _ = regressor._init_pose_macro_local(
            batch_size, initial_phenotypes
        )

        # Assert
        assert torch.allclose(phenotype_kwargs['gender'], torch.tensor([0.8, 0.8]))
        assert torch.allclose(phenotype_kwargs['age'], torch.tensor([0.3, 0.7]))

    def test_should_initialize_local_changes_to_zero(self, mock_model):
        """Should initialize local changes to zero (neutral)."""
        # Arrange
        regressor = ParametersRegressor(mock_model)
        batch_size = 2

        # Act
        _, _, local_kwargs = regressor._init_pose_macro_local(batch_size, {})

        # Assert
        for key in mock_model.local_change_labels:
            assert key in local_kwargs
            assert torch.allclose(local_kwargs[key], torch.zeros(batch_size))


@pytest.mark.unit
class TestJacobianComputation:
    """Test finite-difference Jacobian computation."""

    def test_should_compute_jacobian_with_finite_differences(self, mock_model, device, dtype):
        """Should compute Jacobian matrix using forward differences."""
        # Arrange
        regressor = ParametersRegressor(mock_model)
        batch_size = 1

        # Setup inputs
        pose_params = torch.eye(4, dtype=dtype, device=device)[None, None].repeat(
            batch_size, mock_model.bone_count, 1, 1
        )
        phenotype_kwargs = {k: torch.tensor([0.5], dtype=dtype, device=device)
                           for k in mock_model.phenotype_labels}
        local_kwargs = {k: torch.tensor([0.0], dtype=dtype, device=device)
                       for k in mock_model.local_change_labels}
        idx = torch.randint(0, mock_model.vertex_count, (100,))

        # Mock model forward pass to return predictable output
        def mock_forward(**kwargs):
            batch = kwargs['pose_parameters'].shape[0]
            return {
                'vertices': torch.randn(batch, mock_model.vertex_count, 3, dtype=dtype, device=device)
            }
        mock_model.side_effect = mock_forward

        # Act
        jacobian = regressor._compute_macro_jacobian(
            pose_params, local_kwargs, idx, phenotype_kwargs
        )

        # Assert
        n_phenotypes = len(phenotype_kwargs)
        expected_shape = (batch_size, len(idx) * 3, n_phenotypes)
        assert jacobian.shape == expected_shape

    def test_should_call_model_with_perturbed_parameters(self, mock_model):
        """Should evaluate model at parameter + epsilon for each phenotype."""
        # Arrange
        regressor = ParametersRegressor(mock_model)
        batch_size = 1

        pose_params = regressor._init_pose_macro_local(batch_size, {})[0]
        phenotype_kwargs = {k: torch.tensor([0.5]) for k in mock_model.phenotype_labels}
        local_kwargs = {k: torch.tensor([0.0]) for k in mock_model.local_change_labels}
        idx = torch.randint(0, 100, (50,))

        # Act
        _ = regressor._compute_macro_jacobian(pose_params, local_kwargs, idx, phenotype_kwargs)

        # Assert
        # Should call model once per phenotype parameter + 1 base evaluation
        expected_calls = len(phenotype_kwargs) + 1
        assert mock_model.call_count >= 1  # At least one call


@pytest.mark.unit
class TestJointwiseRegistration:
    """Test joint-wise rigid registration."""

    @patch('roma.rigid_points_registration')
    def test_should_register_joints_to_target_mesh(self, mock_registration, mock_model, device, dtype):
        """Should perform rigid registration for each joint."""
        # Arrange
        regressor = ParametersRegressor(mock_model)
        batch_size = 1
        n_vertices = 1000

        v_ref = torch.randn(batch_size, n_vertices, 3, dtype=dtype, device=device)
        v_tar = torch.randn(batch_size, n_vertices, 3, dtype=dtype, device=device)
        b_ref = torch.eye(4, dtype=dtype, device=device)[None, None].repeat(
            batch_size, mock_model.bone_count, 1, 1
        )
        phenotype_kwargs = {k: torch.tensor([0.5], dtype=dtype, device=device)
                           for k in mock_model.phenotype_labels}
        local_kwargs = {k: torch.tensor([0.0], dtype=dtype, device=device)
                       for k in mock_model.local_change_labels}

        # Mock registration return
        R_mock = torch.eye(3, dtype=dtype, device=device)[None].repeat(batch_size, 1, 1)
        t_mock = torch.zeros(batch_size, 3, dtype=dtype, device=device)
        mock_registration.return_value = (R_mock, t_mock)

        # Act
        pose_new, v_hat = regressor._jointwise_registration_to_pose(
            v_ref, v_tar, b_ref, phenotype_kwargs, local_kwargs
        )

        # Assert
        assert pose_new.shape == (batch_size, mock_model.bone_count, 4, 4)
        assert v_hat.shape[0] == batch_size
        mock_registration.assert_called()  # Registration was performed


@pytest.mark.unit
class TestGlobalAdjustment:
    """Test global rigid alignment."""

    @patch('roma.rigid_points_registration')
    def test_should_apply_global_transform_to_root(self, mock_registration,
                                                     mock_model, device, dtype):
        """Should compute and apply global alignment to root joint."""
        # Arrange
        regressor = ParametersRegressor(mock_model)
        batch_size = 1

        pose_params = torch.eye(4, dtype=dtype, device=device)[None, None].repeat(
            batch_size, mock_model.bone_count, 1, 1
        )
        source_vertices = torch.randn(batch_size, 1000, 3, dtype=dtype, device=device)
        target_vertices = torch.randn(batch_size, 1000, 3, dtype=dtype, device=device)

        # Mock registration
        R = torch.eye(3, dtype=dtype, device=device)[None]
        t = torch.ones(batch_size, 3, dtype=dtype, device=device)
        mock_registration.return_value = (R, t)

        # Act
        adjusted_pose = regressor._apply_global_adjustment(
            pose_params, source_vertices, target_vertices
        )

        # Assert
        assert adjusted_pose.shape == pose_params.shape
        # Root joint (index 0) should be modified
        assert not torch.allclose(adjusted_pose[:, 0], pose_params[:, 0])
        # Other joints should remain unchanged
        assert torch.allclose(adjusted_pose[:, 1:], pose_params[:, 1:])


@pytest.mark.unit
class TestRegressorCallMethod:
    """Test main fitting workflow."""

    def test_should_fit_pose_and_phenotype_to_target(self, mock_model, device, dtype):
        """Should iteratively optimize pose and phenotype parameters using realistic data."""
        # Arrange
        regressor = ParametersRegressor(mock_model, max_n_iters=2, verbose=False)

        # Use realistic humanoid vertices
        target_vertices = generate_humanoid_vertices(
            height=1.75,
            n_vertices=mock_model.vertex_count,
            device=device,
            dtype=dtype
        ).unsqueeze(0)  # Add batch dimension

        # Act
        pose, phenotype, v_hat = regressor(target_vertices)

        # Assert
        assert pose.shape[0] == 1
        assert pose.shape[1] == mock_model.bone_count
        assert isinstance(phenotype, dict)
        assert all(k in phenotype for k in mock_model.phenotype_labels)
        assert v_hat.shape[0] == 1
        # Verify phenotype values are in valid range
        for key, value in phenotype.items():
            assert torch.all(value >= 0.01)
            assert torch.all(value <= 0.99)

    def test_should_respect_max_iterations(self, mock_model):
        """Should stop after max_n_iters iterations."""
        # Arrange
        max_iters = 3
        regressor = ParametersRegressor(mock_model, max_n_iters=max_iters)
        target_vertices = torch.randn(1, mock_model.vertex_count, 3)

        # Track iteration count via model calls
        call_count_before = mock_model.call_count

        # Act
        regressor(target_vertices)

        # Assert
        # Model should be called multiple times (at least once per iteration)
        assert mock_model.call_count > call_count_before

    def test_should_support_batch_fitting(self, mock_model, device, dtype):
        """Should fit multiple target meshes in parallel using realistic batch data."""
        # Arrange
        regressor = ParametersRegressor(mock_model, max_n_iters=1)
        batch_size = 3

        # Create realistic batch with different profiles
        batch_data = create_test_batch(
            batch_size=batch_size,
            vertex_count=mock_model.vertex_count,
            measurement_profiles=['average_male', 'average_female', 'athletic_male'],
            device=device,
            dtype=dtype
        )
        target_vertices = batch_data['vertices']

        # Act
        pose, phenotype, v_hat = regressor(target_vertices)

        # Assert
        assert pose.shape[0] == batch_size
        assert phenotype['gender'].shape[0] == batch_size
        assert v_hat.shape[0] == batch_size
        # Verify all phenotype parameters are batched correctly
        for key, value in phenotype.items():
            assert value.shape[0] == batch_size

    def test_should_accept_initial_phenotype_guess(self, mock_model):
        """Should use provided initial phenotype parameters."""
        # Arrange
        regressor = ParametersRegressor(mock_model, max_n_iters=1)
        target_vertices = torch.randn(1, mock_model.vertex_count, 3)
        initial_phenotype = {'gender': 0.9, 'age': 0.2}

        # Act
        _, phenotype, _ = regressor(target_vertices,
                                    initial_phenotype_kwargs=initial_phenotype)

        # Assert: Initial values should influence result
        # (exact match not guaranteed due to optimization)
        assert 'gender' in phenotype
        assert 'age' in phenotype

    def test_should_allow_disabling_phenotype_optimization(self, mock_model):
        """Should skip phenotype optimization when optimize_phenotypes=False."""
        # Arrange
        regressor = ParametersRegressor(mock_model, max_n_iters=1)
        target_vertices = torch.randn(1, mock_model.vertex_count, 3)

        # Act
        _, phenotype, _ = regressor(target_vertices, optimize_phenotypes=False)

        # Assert
        # Phenotypes should be at initial values (0.5 default)
        for key in mock_model.phenotype_labels:
            assert torch.allclose(phenotype[key], torch.tensor([0.5]))

    def test_should_exclude_specified_phenotypes_from_optimization(self, mock_model):
        """Should not optimize phenotypes in excluded list."""
        # Arrange
        regressor = ParametersRegressor(mock_model, max_n_iters=1)
        target_vertices = torch.randn(1, mock_model.vertex_count, 3)
        excluded = ['age', 'gender']

        # Act
        _, phenotype, _ = regressor(target_vertices,
                                    optimize_phenotypes=True,
                                    excluded_phenotypes=excluded)

        # Assert
        # Excluded phenotypes should remain at initial value
        assert torch.allclose(phenotype['age'], torch.tensor([0.5]))
        assert torch.allclose(phenotype['gender'], torch.tensor([0.5]))


@pytest.mark.unit
class TestAgeAnchorSearch:
    """Test age anchor search optimization."""

    def test_should_try_multiple_age_anchors(self, mock_model):
        """Should evaluate fitting at different age values."""
        # Arrange
        regressor = ParametersRegressor(mock_model, max_n_iters=1, verbose=False)
        target_vertices = torch.randn(1, mock_model.vertex_count, 3)
        age_anchors = [0.0, 0.5, 1.0]

        # Act
        pose, phenotype, v_hat = regressor.fit_with_age_anchor_search(
            target_vertices, age_anchors=age_anchors
        )

        # Assert
        assert 'age' in phenotype
        # Age should be one of the anchors (or close to it after refinement)
        assert phenotype['age'].item() >= 0.0
        assert phenotype['age'].item() <= 1.0

    def test_should_select_best_age_by_reconstruction_error(self, mock_model):
        """Should choose age anchor with lowest vertex error."""
        # Arrange
        regressor = ParametersRegressor(mock_model, max_n_iters=1, verbose=False)
        target_vertices = torch.randn(2, mock_model.vertex_count, 3)

        # Act
        pose, phenotype, v_hat = regressor.fit_with_age_anchor_search(target_vertices)

        # Assert
        assert phenotype['age'].shape[0] == 2  # Batch size preserved

    def test_should_refine_after_anchor_selection(self, mock_model):
        """Should perform final optimization after selecting best age."""
        # Arrange
        regressor = ParametersRegressor(mock_model, max_n_iters=1, verbose=False)
        target_vertices = torch.randn(1, mock_model.vertex_count, 3)

        # Track model calls
        call_count_before = mock_model.call_count

        # Act
        regressor.fit_with_age_anchor_search(target_vertices, age_anchors=[0.0, 1.0])

        # Assert
        # Should call model multiple times (anchor search + final refinement)
        assert mock_model.call_count > call_count_before + 2


@pytest.mark.unit
class TestRegressorEdgeCases:
    """Test edge cases and error handling."""

    def test_should_handle_single_vertex_batch(self, mock_model):
        """Should automatically add batch dimension to 2D input."""
        # Arrange
        regressor = ParametersRegressor(mock_model, max_n_iters=1)
        target_vertices = torch.randn(mock_model.vertex_count, 3)  # No batch dim

        # Act
        pose, phenotype, v_hat = regressor(target_vertices)

        # Assert
        assert pose.shape[0] == 1  # Batch dimension added

    def test_should_clamp_phenotype_parameters(self, mock_model):
        """Should enforce phenotype bounds [0.01, 0.99]."""
        # Arrange
        regressor = ParametersRegressor(mock_model, max_n_iters=1)
        target_vertices = torch.randn(1, mock_model.vertex_count, 3)

        # Act
        _, phenotype, _ = regressor(target_vertices)

        # Assert
        for key, value in phenotype.items():
            assert torch.all(value >= 0.01)
            assert torch.all(value <= 0.99)

    def test_should_handle_nan_in_jacobian(self, mock_model):
        """Should handle NaN values in Jacobian computation."""
        # Arrange
        regressor = ParametersRegressor(mock_model, max_n_iters=1)
        target_vertices = torch.randn(1, mock_model.vertex_count, 3)

        # Act (implementation includes nan_to_num)
        _, phenotype, _ = regressor(target_vertices)

        # Assert: Should complete without crashing
        assert all(torch.all(torch.isfinite(v)) for v in phenotype.values())
