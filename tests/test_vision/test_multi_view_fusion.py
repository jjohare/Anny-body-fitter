# Anny - Vision Module Tests
# Copyright (C) 2025 NAVER Corp.
# Apache License, Version 2.0

import pytest
import numpy as np
from anny.vision.multi_view_fusion import MultiViewFusion, FusedMeasurements
from anny.vision.measurement_extractor import BodyMeasurements


class TestMultiViewFusion:
    """Test suite for MultiViewFusion class."""

    @pytest.fixture
    def fusion(self):
        """Create default fusion instance."""
        return MultiViewFusion(
            fusion_method='weighted_average',
            outlier_rejection=True,
            outlier_threshold=2.0,
            min_views=1
        )

    @pytest.fixture
    def sample_measurements(self):
        """Create sample measurements from multiple views."""
        measurements = []

        for i in range(3):
            m = BodyMeasurements()
            m.height = 1.75 + i * 0.02  # Slight variation
            m.shoulder_width = 0.45 + i * 0.01
            m.waist_circumference = 0.85 + i * 0.02
            m.hip_circumference = 0.95 + i * 0.01
            m.chest_circumference = 1.0 + i * 0.015
            m.left_arm_length = 0.70 + i * 0.01
            m.right_arm_length = 0.70 + i * 0.01
            m.left_leg_length = 0.90 + i * 0.015
            m.right_leg_length = 0.90 + i * 0.015
            m.torso_length = 0.60 + i * 0.01

            m.confidence_scores = {
                'height': 0.9,
                'shoulder_width': 0.85,
                'waist_circumference': 0.7,
                'hip_circumference': 0.75,
                'chest_circumference': 0.8,
                'left_arm_length': 0.85,
                'right_arm_length': 0.85,
                'left_leg_length': 0.9,
                'right_leg_length': 0.9,
                'torso_length': 0.8
            }
            m.overall_confidence = 0.85

            measurements.append(m)

        return measurements

    def test_init(self):
        """Test fusion initialization."""
        fusion = MultiViewFusion(
            fusion_method='median',
            outlier_rejection=False,
            min_views=2
        )

        assert fusion.fusion_method == 'median'
        assert fusion.outlier_rejection is False
        assert fusion.min_views == 2

    def test_init_invalid_method(self):
        """Test initialization with invalid fusion method."""
        with pytest.raises(ValueError, match="Invalid fusion method"):
            MultiViewFusion(fusion_method='invalid_method')

    def test_weighted_average(self, fusion):
        """Test weighted average fusion."""
        values = np.array([1.0, 1.1, 0.9])
        confidences = np.array([0.9, 0.7, 0.8])

        fused_value, avg_conf, variance = fusion._weighted_average(values, confidences)

        assert fused_value is not None
        assert 0.9 <= fused_value <= 1.1
        assert avg_conf > 0
        assert variance >= 0

    def test_weighted_average_with_nan(self, fusion):
        """Test weighted average with NaN values."""
        values = np.array([1.0, np.nan, 0.9])
        confidences = np.array([0.9, 0.0, 0.8])

        fused_value, avg_conf, variance = fusion._weighted_average(values, confidences)

        assert fused_value is not None
        assert not np.isnan(fused_value)

    def test_weighted_average_all_invalid(self, fusion):
        """Test weighted average with all invalid values."""
        values = np.array([np.nan, np.nan, np.nan])
        confidences = np.array([0.0, 0.0, 0.0])

        fused_value, avg_conf, variance = fusion._weighted_average(values, confidences)

        assert fused_value is None
        assert avg_conf == 0.0
        assert variance == 0.0

    def test_median_fusion(self, fusion):
        """Test median fusion."""
        values = np.array([1.0, 1.5, 0.9, 1.1])
        confidences = np.array([0.9, 0.8, 0.85, 0.9])

        fused_value, avg_conf, variance = fusion._median_fusion(values, confidences)

        assert fused_value is not None
        assert fused_value == pytest.approx(1.05, abs=0.1)  # Median of [0.9, 1.0, 1.1, 1.5]
        assert avg_conf > 0

    def test_max_confidence_fusion(self, fusion):
        """Test max confidence fusion."""
        values = np.array([1.0, 1.5, 0.9])
        confidences = np.array([0.7, 0.95, 0.8])

        fused_value, max_conf, variance = fusion._max_confidence_fusion(values, confidences)

        assert fused_value == 1.5  # Highest confidence
        assert max_conf == 0.95

    def test_adaptive_fusion_low_variance(self, fusion):
        """Test adaptive fusion with low variance (should use weighted average)."""
        values = np.array([1.0, 1.01, 1.02])  # Low variance
        confidences = np.array([0.9, 0.85, 0.8])

        fused_value, conf, variance = fusion._adaptive_fusion(values, confidences)

        assert fused_value is not None
        # Should be close to weighted average
        expected = np.average(values, weights=confidences / confidences.sum())
        assert abs(fused_value - expected) < 0.01

    def test_adaptive_fusion_high_variance(self, fusion):
        """Test adaptive fusion with high variance (should use median)."""
        values = np.array([1.0, 1.5, 0.8])  # High variance
        confidences = np.array([0.9, 0.85, 0.8])

        fused_value, conf, variance = fusion._adaptive_fusion(values, confidences)

        assert fused_value is not None
        # Should be close to median
        assert abs(fused_value - np.median(values)) < 0.1

    def test_reject_outliers(self, fusion):
        """Test outlier rejection."""
        values = np.array([1.0, 1.1, 1.05, 5.0])  # Last value is outlier
        confidences = np.array([0.9, 0.85, 0.9, 0.9])

        filtered_values, filtered_conf = fusion._reject_outliers(values, confidences)

        assert np.isnan(filtered_values[3])  # Outlier should be NaN
        assert filtered_conf[3] == 0.0
        assert not np.isnan(filtered_values[0])

    def test_reject_outliers_insufficient_data(self, fusion):
        """Test outlier rejection with insufficient data points."""
        values = np.array([1.0, 1.1])
        confidences = np.array([0.9, 0.85])

        filtered_values, filtered_conf = fusion._reject_outliers(values, confidences)

        # Should not reject outliers with < 3 points
        assert np.array_equal(filtered_values, values)
        assert np.array_equal(filtered_conf, confidences)

    def test_fuse_single_measurement(self, fusion):
        """Test fusing a single measurement type."""
        values = [1.75, 1.77, 1.73]
        confidences = [0.9, 0.85, 0.88]

        fused_value, fused_conf, variance = fusion._fuse_single_measurement(values, confidences)

        assert fused_value is not None
        assert 1.7 < fused_value < 1.8
        assert fused_conf > 0
        assert variance >= 0

    def test_fuse_measurements(self, fusion, sample_measurements):
        """Test fusing complete measurements from multiple views."""
        fused = fusion.fuse_measurements(sample_measurements)

        assert isinstance(fused, FusedMeasurements)
        assert fused.measurements.height is not None
        assert fused.measurements.shoulder_width is not None
        assert fused.num_views == 3
        assert len(fused.view_confidences) == 3
        assert fused.fusion_method == 'weighted_average'
        assert 'height' in fused.measurement_variance

    def test_fuse_measurements_insufficient_views(self, fusion):
        """Test fusion with insufficient views."""
        fusion.min_views = 3
        measurements = [BodyMeasurements()]  # Only 1 view

        with pytest.raises(ValueError, match="Insufficient views"):
            fusion.fuse_measurements(measurements)

    def test_fuse_measurements_with_missing_data(self, fusion):
        """Test fusion with some missing measurements."""
        measurements = []

        for i in range(3):
            m = BodyMeasurements()
            m.height = 1.75 if i != 1 else None  # Missing height in second view
            m.shoulder_width = 0.45
            m.confidence_scores = {
                'height': 0.9 if i != 1 else 0.0,
                'shoulder_width': 0.85
            }
            m.overall_confidence = 0.85
            measurements.append(m)

        fused = fusion.fuse_measurements(measurements)

        # Should still produce result using available data
        assert fused.measurements.height is not None
        assert fused.measurements.shoulder_width is not None

    def test_get_measurement_statistics(self, fusion, sample_measurements):
        """Test getting measurement statistics."""
        fused = fusion.fuse_measurements(sample_measurements)
        stats = fusion.get_measurement_statistics(fused)

        assert 'height' in stats
        assert 'shoulder_width' in stats

        assert 'value' in stats['height']
        assert 'confidence' in stats['height']
        assert 'variance' in stats['height']
        assert 'std_dev' in stats['height']
        assert 'cv' in stats['height']  # Coefficient of variation

    def test_different_fusion_methods(self, sample_measurements):
        """Test all fusion methods produce valid results."""
        methods = ['weighted_average', 'median', 'max_confidence', 'adaptive']

        for method in methods:
            fusion = MultiViewFusion(fusion_method=method)
            fused = fusion.fuse_measurements(sample_measurements)

            assert fused.measurements.height is not None
            assert fused.measurements.overall_confidence > 0
            assert fused.fusion_method == method

    def test_outlier_rejection_enabled_vs_disabled(self, sample_measurements):
        """Test difference between outlier rejection enabled/disabled."""
        # Add outlier to measurements
        outlier = BodyMeasurements()
        outlier.height = 3.0  # Unrealistic height
        outlier.shoulder_width = 0.45
        outlier.confidence_scores = {'height': 0.9, 'shoulder_width': 0.9}
        outlier.overall_confidence = 0.9

        measurements_with_outlier = sample_measurements + [outlier]

        # With outlier rejection
        fusion_with_rejection = MultiViewFusion(outlier_rejection=True)
        fused_with = fusion_with_rejection.fuse_measurements(measurements_with_outlier)

        # Without outlier rejection
        fusion_without_rejection = MultiViewFusion(outlier_rejection=False)
        fused_without = fusion_without_rejection.fuse_measurements(measurements_with_outlier)

        # Result with rejection should be more reasonable
        assert fused_with.measurements.height < fused_without.measurements.height

    def test_measurement_variance_calculation(self, fusion, sample_measurements):
        """Test that variance is calculated for each measurement."""
        fused = fusion.fuse_measurements(sample_measurements)

        for field in ['height', 'shoulder_width', 'waist_circumference']:
            assert field in fused.measurement_variance
            assert fused.measurement_variance[field] >= 0

    def test_overall_confidence_calculation(self, fusion, sample_measurements):
        """Test overall confidence is calculated correctly."""
        fused = fusion.fuse_measurements(sample_measurements)

        # Overall confidence should be mean of individual confidences
        individual_confidences = list(fused.measurements.confidence_scores.values())
        expected_confidence = np.mean([c for c in individual_confidences if c > 0])

        assert abs(fused.measurements.overall_confidence - expected_confidence) < 0.01

    def test_single_view_fusion(self, fusion):
        """Test fusion with single view (should work like identity function)."""
        m = BodyMeasurements()
        m.height = 1.75
        m.shoulder_width = 0.45
        m.confidence_scores = {'height': 0.9, 'shoulder_width': 0.85}
        m.overall_confidence = 0.875

        fused = fusion.fuse_measurements([m])

        assert fused.measurements.height == 1.75
        assert fused.measurements.shoulder_width == 0.45
        assert fused.num_views == 1
