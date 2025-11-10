# Anny - Vision Module Tests
# Copyright (C) 2025 NAVER Corp.
# Apache License, Version 2.0

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch
from anny.vision.landmark_detector import LandmarkDetector, LandmarkResult


# Mock MediaPipe availability
@pytest.fixture
def mock_mediapipe():
    """Mock MediaPipe module."""
    with patch('anny.vision.landmark_detector.MEDIAPIPE_AVAILABLE', True):
        mock_mp = MagicMock()

        # Mock pose solution
        mock_pose_class = MagicMock()
        mock_mp.solutions.pose = MagicMock()
        mock_mp.solutions.pose.Pose = mock_pose_class

        with patch('anny.vision.landmark_detector.mp', mock_mp):
            yield mock_mp, mock_pose_class


class TestLandmarkDetector:
    """Test suite for LandmarkDetector class."""

    def test_init_without_mediapipe(self):
        """Test initialization fails without MediaPipe."""
        with patch('anny.vision.landmark_detector.MEDIAPIPE_AVAILABLE', False):
            with pytest.raises(ImportError, match="MediaPipe is not installed"):
                LandmarkDetector()

    def test_init_with_mediapipe(self, mock_mediapipe):
        """Test successful initialization with MediaPipe."""
        _, mock_pose_class = mock_mediapipe

        detector = LandmarkDetector(
            model_complexity=2,
            min_detection_confidence=0.7,
            static_image_mode=True
        )

        assert detector.model_complexity == 2
        assert detector.min_detection_confidence == 0.7
        assert detector.static_image_mode is True

        # Verify Pose was initialized with correct parameters
        mock_pose_class.assert_called_once()
        call_kwargs = mock_pose_class.call_args[1]
        assert call_kwargs['model_complexity'] == 2
        assert call_kwargs['min_detection_confidence'] == 0.7

    def test_landmark_names(self):
        """Test landmark names are defined correctly."""
        assert len(LandmarkDetector.LANDMARK_NAMES) == 33
        assert 'nose' in LandmarkDetector.LANDMARK_NAMES
        assert 'left_shoulder' in LandmarkDetector.LANDMARK_NAMES
        assert 'right_hip' in LandmarkDetector.LANDMARK_NAMES

    def test_detect_success(self, mock_mediapipe):
        """Test successful landmark detection."""
        mock_mp, mock_pose_class = mock_mediapipe

        # Create mock landmarks
        mock_landmarks = []
        for i in range(33):
            landmark = MagicMock()
            landmark.x = i * 0.01
            landmark.y = i * 0.02
            landmark.z = i * 0.001
            landmark.visibility = 0.9
            mock_landmarks.append(landmark)

        # Mock pose results
        mock_results = MagicMock()
        mock_results.pose_landmarks.landmark = mock_landmarks
        mock_results.pose_world_landmarks.landmark = mock_landmarks

        mock_pose_instance = MagicMock()
        mock_pose_instance.process.return_value = mock_results
        mock_pose_class.return_value = mock_pose_instance

        detector = LandmarkDetector()
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        result = detector.detect(image)

        assert result is not None
        assert isinstance(result, LandmarkResult)
        assert result.landmarks.shape == (33, 3)
        assert result.confidence.shape == (33,)
        assert result.visibility.shape == (33,)
        assert result.overall_confidence > 0
        assert result.image_shape == (480, 640)

    def test_detect_no_landmarks(self, mock_mediapipe):
        """Test detection with no landmarks found."""
        _, mock_pose_class = mock_mediapipe

        # Mock empty results
        mock_results = MagicMock()
        mock_results.pose_landmarks = None

        mock_pose_instance = MagicMock()
        mock_pose_instance.process.return_value = mock_results
        mock_pose_class.return_value = mock_pose_instance

        detector = LandmarkDetector()
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        result = detector.detect(image)

        assert result is None

    def test_detect_float_image(self, mock_mediapipe):
        """Test detection with float32 image."""
        _, mock_pose_class = mock_mediapipe

        mock_landmarks = [MagicMock(x=0.5, y=0.5, z=0.0, visibility=0.9) for _ in range(33)]
        mock_results = MagicMock()
        mock_results.pose_landmarks.landmark = mock_landmarks
        mock_results.pose_world_landmarks = None

        mock_pose_instance = MagicMock()
        mock_pose_instance.process.return_value = mock_results
        mock_pose_class.return_value = mock_pose_instance

        detector = LandmarkDetector()
        image = np.random.rand(480, 640, 3).astype(np.float32)
        result = detector.detect(image)

        assert result is not None
        # Verify conversion to uint8 happened
        mock_pose_instance.process.assert_called_once()

    def test_detect_without_world_landmarks(self, mock_mediapipe):
        """Test detection without world landmarks."""
        _, mock_pose_class = mock_mediapipe

        mock_landmarks = [MagicMock(x=0.5, y=0.5, z=0.0, visibility=0.9) for _ in range(33)]
        mock_results = MagicMock()
        mock_results.pose_landmarks.landmark = mock_landmarks
        mock_results.pose_world_landmarks = None

        mock_pose_instance = MagicMock()
        mock_pose_instance.process.return_value = mock_results
        mock_pose_class.return_value = mock_pose_instance

        detector = LandmarkDetector()
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        result = detector.detect(image, return_world_landmarks=True)

        assert result is not None
        assert result.world_landmarks is None

    def test_detect_batch(self, mock_mediapipe):
        """Test batch detection."""
        _, mock_pose_class = mock_mediapipe

        mock_landmarks = [MagicMock(x=0.5, y=0.5, z=0.0, visibility=0.9) for _ in range(33)]
        mock_results = MagicMock()
        mock_results.pose_landmarks.landmark = mock_landmarks
        mock_results.pose_world_landmarks = None

        mock_pose_instance = MagicMock()
        mock_pose_instance.process.return_value = mock_results
        mock_pose_class.return_value = mock_pose_instance

        detector = LandmarkDetector()
        images = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(3)]
        results = detector.detect_batch(images)

        assert len(results) == 3
        assert all(r is not None for r in results)

    def test_detect_batch_with_failures(self, mock_mediapipe):
        """Test batch detection with some failures."""
        _, mock_pose_class = mock_mediapipe

        def side_effect(*args, **kwargs):
            # Fail on second call
            if mock_pose_instance.process.call_count == 2:
                raise RuntimeError("Detection failed")

            mock_results = MagicMock()
            mock_results.pose_landmarks.landmark = [
                MagicMock(x=0.5, y=0.5, z=0.0, visibility=0.9) for _ in range(33)
            ]
            mock_results.pose_world_landmarks = None
            return mock_results

        mock_pose_instance = MagicMock()
        mock_pose_instance.process.side_effect = side_effect
        mock_pose_class.return_value = mock_pose_instance

        detector = LandmarkDetector()
        images = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(3)]
        results = detector.detect_batch(images, skip_failed=True)

        assert len(results) == 3
        assert results[0] is not None
        assert results[1] is None  # Failed
        assert results[2] is not None

    def test_get_landmark_by_name(self, mock_mediapipe):
        """Test getting landmark by name."""
        _, mock_pose_class = mock_mediapipe

        mock_landmarks = [MagicMock(x=i*0.01, y=i*0.02, z=0.0, visibility=0.9) for i in range(33)]
        mock_results = MagicMock()
        mock_results.pose_landmarks.landmark = mock_landmarks
        mock_results.pose_world_landmarks = None

        mock_pose_instance = MagicMock()
        mock_pose_instance.process.return_value = mock_results
        mock_pose_class.return_value = mock_pose_instance

        detector = LandmarkDetector()
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        result = detector.detect(image)

        coords, conf, vis = detector.get_landmark_by_name(result, 'nose')
        assert coords is not None
        assert conf == 0.9
        assert vis == 0.9

    def test_get_landmark_by_invalid_name(self, mock_mediapipe):
        """Test getting landmark with invalid name."""
        _, mock_pose_class = mock_mediapipe

        detector = LandmarkDetector()
        result = LandmarkResult(
            landmarks=np.zeros((33, 3)),
            confidence=np.ones(33),
            visibility=np.ones(33),
            overall_confidence=0.9,
            image_shape=(480, 640)
        )

        with pytest.raises(ValueError, match="Invalid landmark name"):
            detector.get_landmark_by_name(result, 'invalid_name')

    def test_filter_low_confidence(self):
        """Test filtering low confidence landmarks."""
        result = LandmarkResult(
            landmarks=np.ones((33, 3)),
            confidence=np.array([0.9, 0.3, 0.8, 0.2] + [0.9] * 29),
            visibility=np.ones(33),
            overall_confidence=0.7,
            image_shape=(480, 640)
        )

        filtered = LandmarkDetector().filter_low_confidence(result, min_confidence=0.5)

        assert np.isnan(filtered.landmarks[1]).all()  # Low confidence
        assert np.isnan(filtered.landmarks[3]).all()  # Low confidence
        assert not np.isnan(filtered.landmarks[0]).any()  # High confidence
        assert not np.isnan(filtered.landmarks[2]).any()  # High confidence

    def test_to_pixel_coordinates(self):
        """Test conversion to pixel coordinates."""
        result = LandmarkResult(
            landmarks=np.array([[0.5, 0.5, 0.1], [0.25, 0.75, 0.2]]),
            confidence=np.ones(2),
            visibility=np.ones(2),
            overall_confidence=0.9,
            image_shape=(480, 640)
        )

        detector = LandmarkDetector()
        pixel_coords = detector.to_pixel_coordinates(result, denormalize=True)

        assert pixel_coords[0, 0] == 320  # 0.5 * 640
        assert pixel_coords[0, 1] == 240  # 0.5 * 480
        assert pixel_coords[1, 0] == 160  # 0.25 * 640
        assert pixel_coords[1, 1] == 360  # 0.75 * 480

    def test_to_pixel_coordinates_no_denormalize(self):
        """Test pixel coordinates without denormalization."""
        landmarks = np.array([[0.5, 0.5, 0.1]])
        result = LandmarkResult(
            landmarks=landmarks,
            confidence=np.ones(1),
            visibility=np.ones(1),
            overall_confidence=0.9,
            image_shape=(480, 640)
        )

        detector = LandmarkDetector()
        coords = detector.to_pixel_coordinates(result, denormalize=False)

        assert np.array_equal(coords, landmarks)

    def test_overall_confidence_calculation(self, mock_mediapipe):
        """Test overall confidence is calculated correctly."""
        _, mock_pose_class = mock_mediapipe

        # Mix of high and low visibility landmarks
        mock_landmarks = []
        for i in range(33):
            landmark = MagicMock()
            landmark.x = 0.5
            landmark.y = 0.5
            landmark.z = 0.0
            landmark.visibility = 0.9 if i % 2 == 0 else 0.3
            mock_landmarks.append(landmark)

        mock_results = MagicMock()
        mock_results.pose_landmarks.landmark = mock_landmarks
        mock_results.pose_world_landmarks = None

        mock_pose_instance = MagicMock()
        mock_pose_instance.process.return_value = mock_results
        mock_pose_class.return_value = mock_pose_instance

        detector = LandmarkDetector()
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        result = detector.detect(image)

        # Overall confidence should be mean of visible landmarks (visibility > 0.5)
        assert result.overall_confidence == pytest.approx(0.9, abs=0.01)
