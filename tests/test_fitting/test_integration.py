# Anny-body-fitter
# Integration tests for full parameter estimation pipeline
import pytest
import torch
from unittest.mock import Mock, patch
from typing import Dict, Any


class TestParameterEstimationIntegration:
    """Integration tests for complete parameter estimation pipeline."""

    @pytest.fixture
    def mock_anny_model(self):
        """Mock Anny model with all required attributes."""
        model = Mock()
        model.phenotype_labels = [
            'gender', 'age', 'muscle', 'weight',
            'height', 'proportions'
        ]
        model.device = torch.device('cpu')
        model.dtype = torch.float32
        model.bone_count = 100

        # Mock forward pass
        def mock_forward(pose_parameters=None, phenotype_kwargs=None, **kwargs):
            batch_size = 1
            if phenotype_kwargs and 'gender' in phenotype_kwargs:
                batch_size = phenotype_kwargs['gender'].shape[0]

            return {
                'vertices': torch.randn(batch_size, 10000, 3),
                'bone_poses': torch.eye(4).unsqueeze(0).unsqueeze(0).repeat(batch_size, model.bone_count, 1, 1)
            }

        model.return_value = mock_forward
        model.side_effect = mock_forward

        return model

    @pytest.fixture
    def sample_vision_measurements(self):
        """Sample vision measurements from image analysis."""
        return {
            'height_pixels': 1800.0,
            'reference_height_meters': 1.75,
            'shoulder_width_ratio': 0.28,
            'hip_width_ratio': 0.22,
            'waist_width_ratio': 0.18,
            'leg_length_ratio': 0.52,
            'torso_length_ratio': 0.48,
            'body_composition': {
                'muscle_indicator': 0.6,
                'weight_indicator': 0.55
            },
            'estimated_age': 25,
            'estimated_gender': 'male',
            'confidence': 0.85
        }

    @pytest.fixture
    def multi_image_measurements(self):
        """Measurements from multiple images for fusion."""
        return [
            {
                'height_pixels': 1800.0,
                'reference_height_meters': 1.75,
                'estimated_age': 25,
                'estimated_gender': 'male',
                'body_composition': {'muscle_indicator': 0.6, 'weight_indicator': 0.55},
                'confidence': 0.85
            },
            {
                'height_pixels': 1820.0,
                'reference_height_meters': 1.76,
                'estimated_age': 27,
                'estimated_gender': 'male',
                'body_composition': {'muscle_indicator': 0.62, 'weight_indicator': 0.57},
                'confidence': 0.78
            },
            {
                'height_pixels': 1790.0,
                'reference_height_meters': 1.74,
                'estimated_age': 26,
                'estimated_gender': 'male',
                'body_composition': {'muscle_indicator': 0.58, 'weight_indicator': 0.53},
                'confidence': 0.90
            }
        ]

    def test_single_image_pipeline(self, mock_anny_model, sample_vision_measurements):
        """Test complete pipeline with single image."""
        from src.fitting.measurement_to_phenotype import MeasurementToPhenotype
        from src.fitting.parameter_optimizer import ParameterOptimizer
        from src.anny.parameters_regressor import ParametersRegressor

        # Step 1: Map measurements to phenotype estimates
        mapper = MeasurementToPhenotype(mock_anny_model)
        phenotype_estimates = mapper.map_measurements(sample_vision_measurements)

        assert 'gender' in phenotype_estimates
        assert 'age' in phenotype_estimates
        assert 'height' in phenotype_estimates
        assert 'confidence' in phenotype_estimates

        # Step 2: Create mock regressor
        mock_regressor = Mock(spec=ParametersRegressor)
        mock_regressor.device = torch.device('cpu')

        target_vertices = torch.randn(1, 10000, 3)

        # Mock regressor return
        mock_regressor.return_value = (
            torch.eye(4).unsqueeze(0).unsqueeze(0),  # pose
            phenotype_estimates,  # phenotypes
            target_vertices  # vertices
        )

        # Step 3: Optimize parameters
        optimizer = ParameterOptimizer(mock_regressor)

        result = optimizer.optimize(
            target_vertices=target_vertices,
            initial_phenotypes=phenotype_estimates
        )

        assert 'pose_parameters' in result
        assert 'phenotype_kwargs' in result
        assert 'vertices' in result

    def test_multi_image_fusion_pipeline(
        self,
        mock_anny_model,
        multi_image_measurements
    ):
        """Test pipeline with multi-image fusion."""
        from src.fitting.measurement_to_phenotype import MeasurementToPhenotype
        from src.fitting.confidence_weighting import ConfidenceWeighting

        # Step 1: Map each image's measurements
        mapper = MeasurementToPhenotype(mock_anny_model)

        mapped_measurements = []
        for measurement in multi_image_measurements:
            phenotypes = mapper.map_measurements(measurement)
            mapped_measurements.append({
                'phenotypes': phenotypes,
                'confidence': measurement['confidence']
            })

        # Step 2: Fuse measurements
        weighter = ConfidenceWeighting()
        fused = weighter.fuse_measurements(mapped_measurements)

        assert 'phenotypes' in fused
        assert 'confidence' in fused

        # Fused confidence should be higher than individual
        individual_confidences = [m['confidence'] for m in multi_image_measurements]
        assert fused['confidence'] >= max(individual_confidences)

        # Check phenotype parameters present
        assert 'gender' in fused['phenotypes']
        assert 'age' in fused['phenotypes']
        assert 'height' in fused['phenotypes']

    def test_confidence_based_optimization(self, mock_anny_model):
        """Test optimization respects confidence levels."""
        from src.fitting.parameter_optimizer import ParameterOptimizer

        mock_regressor = Mock()
        mock_regressor.device = torch.device('cpu')

        target_vertices = torch.randn(1, 10000, 3)

        initial_phenotypes = {
            'gender': 0.2,
            'age': 0.5,
            'height': 0.6,
            'muscle': 0.5,
            'weight': 0.5
        }

        confidences = {
            'gender': 0.3,  # Low - should exclude
            'age': 0.9,     # High - should include
            'height': 0.85  # High - should include
        }

        mock_regressor.return_value = (
            torch.eye(4).unsqueeze(0).unsqueeze(0),
            initial_phenotypes,
            target_vertices
        )

        optimizer = ParameterOptimizer(
            mock_regressor,
            confidence_threshold=0.5
        )

        result = optimizer.optimize(
            target_vertices=target_vertices,
            initial_phenotypes=initial_phenotypes,
            confidences=confidences
        )

        # Verify regressor was called
        assert mock_regressor.called

        # Check excluded_phenotypes argument
        call_kwargs = mock_regressor.call_args[1]
        if 'excluded_phenotypes' in call_kwargs:
            assert 'gender' in call_kwargs['excluded_phenotypes']

    def test_staged_optimization(self, mock_anny_model):
        """Test multi-stage optimization strategy."""
        from src.fitting.parameter_optimizer import ParameterOptimizer

        mock_regressor = Mock()
        mock_regressor.device = torch.device('cpu')

        target_vertices = torch.randn(1, 10000, 3)

        initial_phenotypes = {
            'gender': 0.2,
            'age': 0.5,
            'height': 0.6
        }

        confidences = {
            'gender': 0.3,
            'age': 0.9,
            'height': 0.85
        }

        # Mock regressor returns
        mock_regressor.return_value = (
            torch.eye(4).unsqueeze(0).unsqueeze(0),
            initial_phenotypes,
            target_vertices
        )

        optimizer = ParameterOptimizer(mock_regressor)

        result = optimizer.optimize_staged(
            target_vertices=target_vertices,
            initial_phenotypes=initial_phenotypes,
            confidences=confidences
        )

        # Should call regressor twice (stage 1 and stage 2)
        assert mock_regressor.call_count >= 2

    def test_measurement_to_tensor_conversion(self, mock_anny_model):
        """Test conversion of phenotype dict to tensors."""
        from src.fitting.measurement_to_phenotype import MeasurementToPhenotype

        mapper = MeasurementToPhenotype(mock_anny_model)

        phenotype_dict = {
            'gender': 0.2,
            'age': 0.5,
            'height': 0.6,
            'muscle': 0.5,
            'weight': 0.5,
            'proportions': 0.5
        }

        tensors = mapper.to_tensor(phenotype_dict, batch_size=2)

        # Check all labels present
        for label in mock_anny_model.phenotype_labels:
            assert label in tensors
            assert tensors[label].shape == (2,)
            assert tensors[label].device == mock_anny_model.device

    def test_error_metrics_computation(self):
        """Test fitting error metric computation."""
        from src.fitting.parameter_optimizer import ParameterOptimizer

        mock_regressor = Mock()
        optimizer = ParameterOptimizer(mock_regressor)

        predicted = torch.randn(1, 1000, 3)
        target = predicted + 0.001 * torch.randn(1, 1000, 3)  # Small error

        metrics = optimizer.get_fitting_error(predicted, target)

        assert 'pve_mm' in metrics
        assert 'max_error_mm' in metrics
        assert 'rms_error_mm' in metrics

        # Error should be small (around 1mm)
        assert metrics['pve_mm'] < 10.0

    def test_outlier_rejection_in_fusion(self, multi_image_measurements):
        """Test outlier rejection during multi-image fusion."""
        from src.fitting.measurement_to_phenotype import MeasurementToPhenotype
        from src.fitting.confidence_weighting import ConfidenceWeighting

        # Add outlier measurement
        outlier_measurement = {
            'height_pixels': 2500.0,  # Outlier
            'reference_height_meters': 2.2,  # Very tall
            'estimated_age': 25,
            'estimated_gender': 'male',
            'confidence': 0.7
        }

        all_measurements = multi_image_measurements + [outlier_measurement]

        # Map measurements
        mapper = MeasurementToPhenotype(Mock(
            phenotype_labels=['gender', 'age', 'height'],
            device=torch.device('cpu')
        ))

        mapped = []
        for m in all_measurements:
            phenotypes = mapper.map_measurements(m)
            mapped.append({
                'phenotypes': phenotypes,
                'confidence': m['confidence']
            })

        # Fuse with outlier rejection
        weighter = ConfidenceWeighting()
        fused = weighter.fuse_measurements(mapped)

        # Height should not be heavily influenced by outlier
        # (should be closer to normal range)
        assert 0.3 <= fused['phenotypes']['height'] <= 0.7
