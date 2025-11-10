# Anny - Vision Module Tests
# Copyright (C) 2025 NAVER Corp.
# Apache License, Version 2.0

import pytest
import numpy as np
from anny.vision.landmark_detector import LandmarkResult
from anny.vision.measurement_extractor import MeasurementExtractor, BodyMeasurements


class TestMeasurementExtractor:
    """Test suite for MeasurementExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create default extractor instance."""
        return MeasurementExtractor(
            use_world_landmarks=True,
            min_confidence=0.5
        )

    @pytest.fixture
    def mock_landmark_result(self):
        """Create mock landmark result with synthetic data."""
        # Create realistic body landmark positions (normalized)
        landmarks = np.array([
            [0.50, 0.15, 0.0],   # 0: nose
            [0.48, 0.14, 0.0],   # 1: left_eye_inner
            [0.47, 0.14, 0.0],   # 2: left_eye
            [0.46, 0.14, 0.0],   # 3: left_eye_outer
            [0.52, 0.14, 0.0],   # 4: right_eye_inner
            [0.53, 0.14, 0.0],   # 5: right_eye
            [0.54, 0.14, 0.0],   # 6: right_eye_outer
            [0.44, 0.15, 0.0],   # 7: left_ear
            [0.56, 0.15, 0.0],   # 8: right_ear
            [0.48, 0.17, 0.0],   # 9: mouth_left
            [0.52, 0.17, 0.0],   # 10: mouth_right
            [0.40, 0.25, 0.0],   # 11: left_shoulder
            [0.60, 0.25, 0.0],   # 12: right_shoulder
            [0.38, 0.40, 0.0],   # 13: left_elbow
            [0.62, 0.40, 0.0],   # 14: right_elbow
            [0.36, 0.55, 0.0],   # 15: left_wrist
            [0.64, 0.55, 0.0],   # 16: right_wrist
            [0.35, 0.57, 0.0],   # 17: left_pinky
            [0.65, 0.57, 0.0],   # 18: right_pinky
            [0.36, 0.56, 0.0],   # 19: left_index
            [0.64, 0.56, 0.0],   # 20: right_index
            [0.37, 0.55, 0.0],   # 21: left_thumb
            [0.63, 0.55, 0.0],   # 22: right_thumb
            [0.42, 0.50, 0.0],   # 23: left_hip
            [0.58, 0.50, 0.0],   # 24: right_hip
            [0.41, 0.70, 0.0],   # 25: left_knee
            [0.59, 0.70, 0.0],   # 26: right_knee
            [0.40, 0.90, 0.0],   # 27: left_ankle
            [0.60, 0.90, 0.0],   # 28: right_ankle
            [0.39, 0.95, 0.0],   # 29: left_heel
            [0.61, 0.95, 0.0],   # 30: right_heel
            [0.41, 0.95, 0.0],   # 31: left_foot_index
            [0.59, 0.95, 0.0],   # 32: right_foot_index
        ], dtype=np.float32)

        # Create world landmarks (in meters, ~1.7m tall person)
        world_landmarks = landmarks.copy()
        world_landmarks[:, 2] = np.linspace(1.7, 0.0, 33)  # Height dimension

        confidence = np.ones(33) * 0.9
        visibility = np.ones(33) * 0.9

        return LandmarkResult(
            landmarks=landmarks,
            confidence=confidence,
            visibility=visibility,
            overall_confidence=0.9,
            image_shape=(480, 640),
            world_landmarks=world_landmarks
        )

    def test_init(self):
        """Test extractor initialization."""
        extractor = MeasurementExtractor(
            use_world_landmarks=False,
            min_confidence=0.7
        )
        assert extractor.use_world_landmarks is False
        assert extractor.min_confidence == 0.7

    def test_extract_height(self, extractor, mock_landmark_result):
        """Test height extraction."""
        height, confidence = extractor.extract_height(mock_landmark_result)

        assert height is not None
        assert height > 0
        assert confidence > 0.5
        # Height should be close to 1.7m (from mock data)
        assert 1.5 < height < 2.0

    def test_extract_height_low_confidence(self, extractor):
        """Test height extraction with low confidence landmarks."""
        result = LandmarkResult(
            landmarks=np.random.rand(33, 3),
            confidence=np.ones(33) * 0.3,  # Low confidence
            visibility=np.ones(33),
            overall_confidence=0.3,
            image_shape=(480, 640),
            world_landmarks=np.random.rand(33, 3)
        )

        height, confidence = extractor.extract_height(result)

        # Should return None with low confidence
        assert height is None
        assert confidence == 0.0

    def test_extract_shoulder_width(self, extractor, mock_landmark_result):
        """Test shoulder width extraction."""
        width, confidence = extractor.extract_shoulder_width(mock_landmark_result)

        assert width is not None
        assert width > 0
        assert confidence > 0.5

    def test_extract_waist_circumference(self, extractor, mock_landmark_result):
        """Test waist circumference estimation."""
        circumference, confidence = extractor.extract_waist_circumference(mock_landmark_result)

        assert circumference is not None
        assert circumference > 0
        assert confidence > 0  # Lower confidence due to estimation

    def test_extract_hip_circumference(self, extractor, mock_landmark_result):
        """Test hip circumference estimation."""
        circumference, confidence = extractor.extract_hip_circumference(mock_landmark_result)

        assert circumference is not None
        assert circumference > 0
        assert confidence > 0

    def test_extract_chest_circumference(self, extractor, mock_landmark_result):
        """Test chest circumference estimation."""
        circumference, confidence = extractor.extract_chest_circumference(mock_landmark_result)

        assert circumference is not None
        assert circumference > 0
        assert confidence > 0

    def test_extract_arm_length_left(self, extractor, mock_landmark_result):
        """Test left arm length extraction."""
        length, confidence = extractor.extract_arm_length(mock_landmark_result, 'left')

        assert length is not None
        assert length > 0
        assert confidence > 0.5

    def test_extract_arm_length_right(self, extractor, mock_landmark_result):
        """Test right arm length extraction."""
        length, confidence = extractor.extract_arm_length(mock_landmark_result, 'right')

        assert length is not None
        assert length > 0
        assert confidence > 0.5

    def test_extract_leg_length_left(self, extractor, mock_landmark_result):
        """Test left leg length extraction."""
        length, confidence = extractor.extract_leg_length(mock_landmark_result, 'left')

        assert length is not None
        assert length > 0
        assert confidence > 0.5

    def test_extract_leg_length_right(self, extractor, mock_landmark_result):
        """Test right leg length extraction."""
        length, confidence = extractor.extract_leg_length(mock_landmark_result, 'right')

        assert length is not None
        assert length > 0
        assert confidence > 0.5

    def test_extract_torso_length(self, extractor, mock_landmark_result):
        """Test torso length extraction."""
        length, confidence = extractor.extract_torso_length(mock_landmark_result)

        assert length is not None
        assert length > 0
        assert confidence > 0.5

    def test_extract_all(self, extractor, mock_landmark_result):
        """Test extraction of all measurements."""
        measurements = extractor.extract_all(mock_landmark_result)

        assert isinstance(measurements, BodyMeasurements)
        assert measurements.height is not None
        assert measurements.shoulder_width is not None
        assert measurements.waist_circumference is not None
        assert measurements.hip_circumference is not None
        assert measurements.chest_circumference is not None
        assert measurements.left_arm_length is not None
        assert measurements.right_arm_length is not None
        assert measurements.left_leg_length is not None
        assert measurements.right_leg_length is not None
        assert measurements.torso_length is not None
        assert measurements.overall_confidence > 0

    def test_extract_all_with_missing_landmarks(self, extractor):
        """Test extraction with some missing landmarks."""
        # Set some landmarks to low confidence
        landmarks = np.random.rand(33, 3)
        confidence = np.ones(33) * 0.9
        confidence[15:17] = 0.3  # Low confidence for wrists

        result = LandmarkResult(
            landmarks=landmarks,
            confidence=confidence,
            visibility=np.ones(33),
            overall_confidence=0.7,
            image_shape=(480, 640),
            world_landmarks=landmarks.copy()
        )

        measurements = extractor.extract_all(result)

        # Some measurements should be None due to low confidence
        assert measurements.left_arm_length is None or measurements.right_arm_length is None

    def test_to_dict(self, extractor, mock_landmark_result):
        """Test conversion to dictionary."""
        measurements = extractor.extract_all(mock_landmark_result)
        result_dict = extractor.to_dict(measurements)

        assert 'measurements' in result_dict
        assert 'confidence_scores' in result_dict
        assert 'overall_confidence' in result_dict

        assert 'height' in result_dict['measurements']
        assert 'shoulder_width' in result_dict['measurements']
        assert result_dict['overall_confidence'] > 0

    def test_without_world_landmarks(self):
        """Test extraction without world landmarks."""
        extractor = MeasurementExtractor(use_world_landmarks=False)

        landmarks = np.random.rand(33, 3)
        result = LandmarkResult(
            landmarks=landmarks,
            confidence=np.ones(33) * 0.9,
            visibility=np.ones(33),
            overall_confidence=0.9,
            image_shape=(480, 640),
            world_landmarks=None
        )

        measurements = extractor.extract_all(result)

        # Should still extract measurements from 2D landmarks
        assert measurements.height is not None

    def test_euclidean_distance(self, extractor):
        """Test Euclidean distance calculation."""
        p1 = np.array([0, 0, 0])
        p2 = np.array([3, 4, 0])

        distance = extractor._euclidean_distance(p1, p2)
        assert distance == 5.0  # 3-4-5 triangle

    def test_get_landmark_coords_low_confidence(self, extractor):
        """Test getting landmark with low confidence returns None."""
        result = LandmarkResult(
            landmarks=np.random.rand(33, 3),
            confidence=np.array([0.3] * 33),  # All low confidence
            visibility=np.ones(33),
            overall_confidence=0.3,
            image_shape=(480, 640)
        )

        coords = extractor._get_landmark_coords(result, 0, use_world=False)
        assert coords is None

    def test_confidence_scores_present(self, extractor, mock_landmark_result):
        """Test that confidence scores are recorded for each measurement."""
        measurements = extractor.extract_all(mock_landmark_result)

        assert measurements.confidence_scores is not None
        assert 'height' in measurements.confidence_scores
        assert 'shoulder_width' in measurements.confidence_scores
        assert all(0 <= v <= 1 for v in measurements.confidence_scores.values())

    def test_anthropometric_ratios(self):
        """Test that circumference ratios are reasonable."""
        ratios = MeasurementExtractor.CIRCUMFERENCE_RATIOS

        assert 2.0 < ratios['waist'] < 3.0
        assert 2.5 < ratios['hip'] < 3.5
        assert 2.5 < ratios['chest'] < 3.5
