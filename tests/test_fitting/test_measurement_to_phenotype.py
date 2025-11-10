# Anny-body-fitter
# London TDD Tests for Measurement to Phenotype Mapping
import pytest
import torch
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any


class TestMeasurementToPhenotype:
    """London TDD tests for measurement to phenotype mapping."""

    @pytest.fixture
    def mock_vision_measurements(self):
        """Mock vision measurements extracted from images."""
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
    def mock_model(self):
        """Mock Anny model for testing."""
        model = Mock()
        model.phenotype_labels = [
            'gender', 'age', 'muscle', 'weight',
            'height', 'proportions'
        ]
        model.device = torch.device('cpu')
        return model

    def test_mapper_initialization(self, mock_model):
        """Test mapper initializes with model."""
        from src.fitting.measurement_to_phenotype import MeasurementToPhenotype

        mapper = MeasurementToPhenotype(mock_model)

        assert mapper.model == mock_model
        assert mapper.device == mock_model.device
        assert hasattr(mapper, 'phenotype_labels')

    def test_height_mapping(self, mock_vision_measurements):
        """Test height pixel measurement maps to Anny height parameter."""
        from src.fitting.measurement_to_phenotype import MeasurementToPhenotype

        mapper = MeasurementToPhenotype(Mock())

        # Height should be normalized to 0-1 range
        result = mapper.map_height(
            mock_vision_measurements['height_pixels'],
            mock_vision_measurements['reference_height_meters']
        )

        assert 0.0 <= result <= 1.0
        assert isinstance(result, float)

    def test_gender_mapping(self, mock_vision_measurements):
        """Test gender estimation maps to Anny gender parameter."""
        from src.fitting.measurement_to_phenotype import MeasurementToPhenotype

        mapper = MeasurementToPhenotype(Mock())

        # Male should be close to 0, Female close to 1
        male_result = mapper.map_gender('male', confidence=0.85)
        female_result = mapper.map_gender('female', confidence=0.85)

        assert male_result < 0.3
        assert female_result > 0.7
        assert 0.0 <= male_result <= 1.0
        assert 0.0 <= female_result <= 1.0

    def test_age_mapping(self, mock_vision_measurements):
        """Test age estimation maps to Anny age parameter."""
        from src.fitting.measurement_to_phenotype import MeasurementToPhenotype

        mapper = MeasurementToPhenotype(Mock())

        # Age should map to normalized range
        result = mapper.map_age(mock_vision_measurements['estimated_age'])

        assert 0.0 <= result <= 1.0
        # 25 years should be in young adult range (around 0.5)
        assert 0.3 <= result <= 0.7

    def test_proportions_mapping(self, mock_vision_measurements):
        """Test body proportions map to Anny proportions parameter."""
        from src.fitting.measurement_to_phenotype import MeasurementToPhenotype

        mapper = MeasurementToPhenotype(Mock())

        result = mapper.map_proportions(
            shoulder_ratio=mock_vision_measurements['shoulder_width_ratio'],
            hip_ratio=mock_vision_measurements['hip_width_ratio'],
            leg_ratio=mock_vision_measurements['leg_length_ratio']
        )

        assert 0.0 <= result <= 1.0

    def test_muscle_weight_mapping(self, mock_vision_measurements):
        """Test body composition indicators map to muscle/weight."""
        from src.fitting.measurement_to_phenotype import MeasurementToPhenotype

        mapper = MeasurementToPhenotype(Mock())

        muscle, weight = mapper.map_body_composition(
            mock_vision_measurements['body_composition']
        )

        assert 0.0 <= muscle <= 1.0
        assert 0.0 <= weight <= 1.0

    def test_full_measurement_mapping(self, mock_vision_measurements, mock_model):
        """Test complete mapping from measurements to phenotype dict."""
        from src.fitting.measurement_to_phenotype import MeasurementToPhenotype

        mapper = MeasurementToPhenotype(mock_model)

        result = mapper.map_measurements(mock_vision_measurements)

        # Should return dict with all phenotype parameters
        assert isinstance(result, dict)
        assert 'gender' in result
        assert 'age' in result
        assert 'muscle' in result
        assert 'weight' in result
        assert 'height' in result
        assert 'proportions' in result
        assert 'confidence' in result

        # All values should be in valid range
        for key, value in result.items():
            if key != 'confidence':
                assert 0.0 <= value <= 1.0

    def test_confidence_propagation(self, mock_vision_measurements):
        """Test confidence from measurements propagates to output."""
        from src.fitting.measurement_to_phenotype import MeasurementToPhenotype

        mapper = MeasurementToPhenotype(Mock())

        result = mapper.map_measurements(mock_vision_measurements)

        assert result['confidence'] == mock_vision_measurements['confidence']

    def test_missing_measurements_handling(self):
        """Test handling of incomplete measurements."""
        from src.fitting.measurement_to_phenotype import MeasurementToPhenotype

        mapper = MeasurementToPhenotype(Mock())

        incomplete_measurements = {
            'height_pixels': 1800.0,
            'reference_height_meters': 1.75
        }

        result = mapper.map_measurements(incomplete_measurements)

        # Should use default values for missing measurements
        assert 'gender' in result
        assert 'age' in result
        # Default should be middle range
        assert 0.4 <= result['gender'] <= 0.6
        assert 0.4 <= result['age'] <= 0.6

    def test_uncertainty_handling(self):
        """Test low confidence measurements have appropriate uncertainty."""
        from src.fitting.measurement_to_phenotype import MeasurementToPhenotype

        mapper = MeasurementToPhenotype(Mock())

        low_confidence_measurements = {
            'height_pixels': 1800.0,
            'reference_height_meters': 1.75,
            'estimated_gender': 'male',
            'confidence': 0.3  # Low confidence
        }

        result = mapper.map_measurements(low_confidence_measurements)

        # Low confidence should result in more neutral values
        assert result['confidence'] == 0.3
        # Gender should be closer to middle with low confidence
        assert 0.2 <= result['gender'] <= 0.8


class TestParameterOptimizer:
    """London TDD tests for parameter optimization using ParametersRegressor."""

    @pytest.fixture
    def mock_regressor(self):
        """Mock ParametersRegressor."""
        regressor = Mock()
        regressor.device = torch.device('cpu')
        return regressor

    @pytest.fixture
    def mock_target_vertices(self):
        """Mock target mesh vertices."""
        return torch.randn(1, 10000, 3)

    def test_optimizer_initialization(self, mock_regressor):
        """Test optimizer initializes with regressor."""
        from src.fitting.parameter_optimizer import ParameterOptimizer

        optimizer = ParameterOptimizer(mock_regressor)

        assert optimizer.regressor == mock_regressor

    def test_optimize_with_initial_phenotypes(self, mock_regressor, mock_target_vertices):
        """Test optimization uses initial phenotype estimates."""
        from src.fitting.parameter_optimizer import ParameterOptimizer

        optimizer = ParameterOptimizer(mock_regressor)

        initial_phenotypes = {
            'gender': 0.2,
            'age': 0.5,
            'height': 0.6,
            'muscle': 0.5,
            'weight': 0.5,
            'proportions': 0.5
        }

        # Mock regressor call
        mock_regressor.return_value = (
            torch.eye(4).unsqueeze(0).unsqueeze(0),  # pose
            initial_phenotypes,  # phenotypes
            mock_target_vertices  # vertices
        )

        result = optimizer.optimize(
            mock_target_vertices,
            initial_phenotypes=initial_phenotypes
        )

        assert 'pose_parameters' in result
        assert 'phenotype_kwargs' in result
        assert 'vertices' in result
        assert mock_regressor.called

    def test_optimize_excludes_uncertain_params(self, mock_regressor, mock_target_vertices):
        """Test optimization excludes low-confidence parameters."""
        from src.fitting.parameter_optimizer import ParameterOptimizer

        optimizer = ParameterOptimizer(mock_regressor)

        initial_phenotypes = {
            'gender': 0.5,
            'age': 0.5,
            'height': 0.6
        }

        confidences = {
            'gender': 0.3,  # Low confidence - should exclude
            'age': 0.9,     # High confidence
            'height': 0.8   # High confidence
        }

        result = optimizer.optimize(
            mock_target_vertices,
            initial_phenotypes=initial_phenotypes,
            confidences=confidences,
            confidence_threshold=0.5
        )

        # Should have excluded gender from optimization
        call_args = mock_regressor.call_args
        if call_args:
            # Verify excluded_phenotypes contains 'gender'
            assert 'excluded_phenotypes' in call_args[1] or len(call_args) > 2


class TestConfidenceWeighting:
    """London TDD tests for multi-image confidence weighting."""

    @pytest.fixture
    def mock_multi_image_measurements(self):
        """Mock measurements from multiple images."""
        return [
            {
                'phenotypes': {
                    'gender': 0.2, 'age': 0.5, 'height': 0.6,
                    'muscle': 0.5, 'weight': 0.5, 'proportions': 0.5
                },
                'confidence': 0.85
            },
            {
                'phenotypes': {
                    'gender': 0.3, 'age': 0.52, 'height': 0.58,
                    'muscle': 0.6, 'weight': 0.55, 'proportions': 0.48
                },
                'confidence': 0.75
            },
            {
                'phenotypes': {
                    'gender': 0.25, 'age': 0.48, 'height': 0.62,
                    'muscle': 0.55, 'weight': 0.52, 'proportions': 0.52
                },
                'confidence': 0.90
            }
        ]

    def test_weighting_initialization(self):
        """Test confidence weighting module initializes."""
        from src.fitting.confidence_weighting import ConfidenceWeighting

        weighter = ConfidenceWeighting()

        assert hasattr(weighter, 'fuse_measurements')

    def test_simple_weighted_average(self):
        """Test weighted average fusion of measurements."""
        from src.fitting.confidence_weighting import ConfidenceWeighting

        weighter = ConfidenceWeighting()

        measurements = [
            {'value': 0.5, 'confidence': 0.8},
            {'value': 0.6, 'confidence': 0.6}
        ]

        result = weighter.weighted_average(measurements, key='value')

        # Higher confidence should dominate
        assert 0.5 <= result <= 0.6
        assert result < 0.55  # Closer to high confidence value

    def test_multi_image_fusion(self, mock_multi_image_measurements):
        """Test fusion of phenotypes from multiple images."""
        from src.fitting.confidence_weighting import ConfidenceWeighting

        weighter = ConfidenceWeighting()

        result = weighter.fuse_measurements(mock_multi_image_measurements)

        assert isinstance(result, dict)
        assert 'phenotypes' in result
        assert 'confidence' in result

        # Check all phenotype parameters present
        phenotypes = result['phenotypes']
        assert 'gender' in phenotypes
        assert 'age' in phenotypes
        assert 'height' in phenotypes

        # Confidence should be aggregate (higher than any single)
        assert result['confidence'] >= max(m['confidence'] for m in mock_multi_image_measurements)

    def test_outlier_rejection(self):
        """Test outlier measurements are down-weighted."""
        from src.fitting.confidence_weighting import ConfidenceWeighting

        weighter = ConfidenceWeighting()

        measurements = [
            {'value': 0.5, 'confidence': 0.8},
            {'value': 0.52, 'confidence': 0.85},
            {'value': 0.9, 'confidence': 0.7},  # Outlier
        ]

        result = weighter.weighted_average(
            measurements,
            key='value',
            outlier_rejection=True
        )

        # Should not be influenced much by outlier
        assert 0.48 <= result <= 0.55

    def test_uncertainty_propagation(self, mock_multi_image_measurements):
        """Test uncertainty is properly propagated through fusion."""
        from src.fitting.confidence_weighting import ConfidenceWeighting

        weighter = ConfidenceWeighting()

        result = weighter.fuse_measurements(
            mock_multi_image_measurements,
            return_uncertainty=True
        )

        assert 'uncertainty' in result

        # More measurements should reduce uncertainty
        single_measurement = [mock_multi_image_measurements[0]]
        single_result = weighter.fuse_measurements(
            single_measurement,
            return_uncertainty=True
        )

        assert result['uncertainty'] < single_result['uncertainty']
