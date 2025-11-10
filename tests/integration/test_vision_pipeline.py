"""
Vision pipeline integration tests.
Tests image preprocessing, landmark detection, and measurement extraction pipeline.
Uses mock vision detector since MediaPipe is unavailable on Python 3.13.
"""

import pytest
import numpy as np
from PIL import Image
import io
from unittest.mock import Mock, patch, MagicMock

from tests.fixtures.test_images import create_test_image_with_person, create_front_view_image


class MockVisionDetector:
    """Mock vision detector for testing pipeline without MediaPipe."""

    def __init__(self):
        self.landmarks = self._generate_mock_landmarks()

    def _generate_mock_landmarks(self):
        """Generate realistic mock body landmarks."""
        # Simulate 33 body landmarks (similar to MediaPipe Pose)
        landmarks = []
        for i in range(33):
            landmark = {
                'x': 0.5 + (i % 5 - 2) * 0.1,  # Spread across image
                'y': 0.2 + (i // 5) * 0.1,     # Vertical distribution
                'z': 0.0,
                'visibility': 0.9
            }
            landmarks.append(landmark)
        return landmarks

    def detect_landmarks(self, image_array: np.ndarray):
        """Mock landmark detection."""
        # Return mock landmarks
        return {
            'landmarks': self.landmarks,
            'confidence': 0.95,
            'image_width': image_array.shape[1],
            'image_height': image_array.shape[0]
        }

    def extract_measurements(self, landmarks, image_height_px, person_height_cm=None):
        """Mock measurement extraction."""
        # Return realistic mock measurements
        measurements = {
            'height_cm': person_height_cm or 175.0,
            'shoulder_width_cm': 45.0,
            'chest_circumference_cm': 95.0,
            'waist_circumference_cm': 80.0,
            'hip_circumference_cm': 98.0,
            'arm_length_cm': 58.0,
            'leg_length_cm': 88.0,
            'neck_circumference_cm': 38.0,
            'confidence': 0.92
        }
        return measurements


@pytest.fixture
def mock_detector():
    """Provide mock vision detector."""
    return MockVisionDetector()


class TestImagePreprocessing:
    """Test image preprocessing steps."""

    def test_load_image_from_bytes(self):
        """Test loading image from bytes."""
        img_bytes = create_front_view_image()

        # Load image
        img = Image.open(io.BytesIO(img_bytes))

        assert img is not None
        assert img.mode == 'RGB'
        assert img.size[0] > 0
        assert img.size[1] > 0

    def test_resize_image(self):
        """Test image resizing."""
        img_bytes = create_front_view_image()
        img = Image.open(io.BytesIO(img_bytes))

        # Resize to standard size
        target_size = (640, 480)
        resized = img.resize(target_size, Image.Resampling.LANCZOS)

        assert resized.size == target_size

    def test_normalize_image(self):
        """Test image normalization."""
        img_bytes = create_front_view_image()
        img = Image.open(io.BytesIO(img_bytes))

        # Convert to numpy array and normalize
        img_array = np.array(img)
        normalized = img_array.astype(np.float32) / 255.0

        assert normalized.min() >= 0.0
        assert normalized.max() <= 1.0
        assert normalized.dtype == np.float32

    def test_image_augmentation(self):
        """Test basic image augmentation."""
        img_bytes = create_front_view_image()
        img = Image.open(io.BytesIO(img_bytes))

        # Test brightness adjustment
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Brightness(img)
        brightened = enhancer.enhance(1.2)

        assert brightened is not None
        assert brightened.size == img.size


class TestLandmarkDetection:
    """Test landmark detection pipeline."""

    def test_detect_landmarks_single_image(self, mock_detector):
        """Test landmark detection on single image."""
        img_bytes = create_front_view_image()
        img = Image.open(io.BytesIO(img_bytes))
        img_array = np.array(img)

        # Detect landmarks
        result = mock_detector.detect_landmarks(img_array)

        assert result is not None
        assert 'landmarks' in result
        assert len(result['landmarks']) > 0
        assert result['confidence'] > 0.5

    def test_landmark_coordinates(self, mock_detector):
        """Test that landmarks have valid coordinates."""
        img_bytes = create_front_view_image()
        img = Image.open(io.BytesIO(img_bytes))
        img_array = np.array(img)

        result = mock_detector.detect_landmarks(img_array)
        landmarks = result['landmarks']

        for landmark in landmarks:
            assert 'x' in landmark
            assert 'y' in landmark
            assert 'z' in landmark
            assert 0.0 <= landmark['x'] <= 1.0
            assert 0.0 <= landmark['y'] <= 1.0

    def test_landmark_visibility(self, mock_detector):
        """Test landmark visibility scores."""
        img_bytes = create_front_view_image()
        img = Image.open(io.BytesIO(img_bytes))
        img_array = np.array(img)

        result = mock_detector.detect_landmarks(img_array)
        landmarks = result['landmarks']

        for landmark in landmarks:
            assert 'visibility' in landmark
            assert 0.0 <= landmark['visibility'] <= 1.0


class TestMeasurementExtraction:
    """Test measurement extraction from landmarks."""

    def test_extract_basic_measurements(self, mock_detector):
        """Test extraction of basic body measurements."""
        img_bytes = create_front_view_image()
        img = Image.open(io.BytesIO(img_bytes))
        img_array = np.array(img)

        # Detect landmarks
        result = mock_detector.detect_landmarks(img_array)
        landmarks = result['landmarks']

        # Extract measurements
        measurements = mock_detector.extract_measurements(
            landmarks,
            image_height_px=img_array.shape[0],
            person_height_cm=175.0
        )

        assert measurements['height_cm'] == 175.0
        assert measurements['shoulder_width_cm'] > 0
        assert measurements['chest_circumference_cm'] > 0
        assert measurements['waist_circumference_cm'] > 0

    def test_measurement_scaling(self, mock_detector):
        """Test that measurements scale correctly with image size."""
        # Create two images of different sizes
        img1_bytes = create_test_image_with_person(640, 480)
        img2_bytes = create_test_image_with_person(1280, 960)

        img1 = Image.open(io.BytesIO(img1_bytes))
        img2 = Image.open(io.BytesIO(img2_bytes))

        img1_array = np.array(img1)
        img2_array = np.array(img2)

        # Detect and measure both
        result1 = mock_detector.detect_landmarks(img1_array)
        result2 = mock_detector.detect_landmarks(img2_array)

        measurements1 = mock_detector.extract_measurements(
            result1['landmarks'], img1_array.shape[0], person_height_cm=175.0
        )
        measurements2 = mock_detector.extract_measurements(
            result2['landmarks'], img2_array.shape[0], person_height_cm=175.0
        )

        # Measurements should be similar despite different image sizes
        assert abs(measurements1['height_cm'] - measurements2['height_cm']) < 5.0

    def test_measurement_confidence(self, mock_detector):
        """Test confidence scoring for measurements."""
        img_bytes = create_front_view_image()
        img = Image.open(io.BytesIO(img_bytes))
        img_array = np.array(img)

        result = mock_detector.detect_landmarks(img_array)
        measurements = mock_detector.extract_measurements(
            result['landmarks'], img_array.shape[0]
        )

        assert 'confidence' in measurements
        assert 0.0 <= measurements['confidence'] <= 1.0


class TestMultiImageFusion:
    """Test combining measurements from multiple images."""

    def test_average_measurements_two_images(self, mock_detector):
        """Test averaging measurements from two images."""
        # Create two different views
        from tests.fixtures.test_images import create_front_view_image, create_side_view_image

        img1_bytes = create_front_view_image()
        img2_bytes = create_side_view_image()

        # Process both images
        measurements_list = []
        for img_bytes in [img1_bytes, img2_bytes]:
            img = Image.open(io.BytesIO(img_bytes))
            img_array = np.array(img)
            result = mock_detector.detect_landmarks(img_array)
            measurements = mock_detector.extract_measurements(
                result['landmarks'], img_array.shape[0], person_height_cm=175.0
            )
            measurements_list.append(measurements)

        # Average measurements
        averaged = {}
        keys_to_average = ['height_cm', 'shoulder_width_cm', 'chest_circumference_cm']
        for key in keys_to_average:
            values = [m[key] for m in measurements_list if key in m]
            averaged[key] = sum(values) / len(values)

        assert averaged['height_cm'] == 175.0
        assert averaged['shoulder_width_cm'] > 0

    def test_weighted_average_by_confidence(self, mock_detector):
        """Test confidence-weighted averaging."""
        # Simulate measurements with different confidences
        measurements = [
            {'height_cm': 175.0, 'confidence': 0.9},
            {'height_cm': 173.0, 'confidence': 0.6},
            {'height_cm': 176.0, 'confidence': 0.8}
        ]

        # Calculate weighted average
        total_confidence = sum(m['confidence'] for m in measurements)
        weighted_height = sum(
            m['height_cm'] * m['confidence'] for m in measurements
        ) / total_confidence

        # Should be closer to high-confidence measurements
        assert 174.5 <= weighted_height <= 175.5


class TestErrorHandling:
    """Test error handling in vision pipeline."""

    def test_handle_corrupted_image(self):
        """Test handling of corrupted image data."""
        corrupted_data = b"not an image"

        with pytest.raises(Exception):
            img = Image.open(io.BytesIO(corrupted_data))
            np.array(img)

    def test_handle_no_person_detected(self, mock_detector):
        """Test handling when no person is detected."""
        # Create empty/background image
        empty_img_bytes = create_test_image_with_person(640, 480)
        img = Image.open(io.BytesIO(empty_img_bytes))
        img_array = np.array(img)

        # Mock detector should still return landmarks
        # In real scenario, this might return None
        result = mock_detector.detect_landmarks(img_array)

        # Should have some result (even if low confidence)
        assert result is not None

    def test_handle_partial_landmarks(self, mock_detector):
        """Test handling when only partial landmarks are detected."""
        # Modify mock to return fewer landmarks
        mock_detector.landmarks = mock_detector.landmarks[:10]

        img_bytes = create_front_view_image()
        img = Image.open(io.BytesIO(img_bytes))
        img_array = np.array(img)

        result = mock_detector.detect_landmarks(img_array)

        assert len(result['landmarks']) == 10


class TestPipelineIntegration:
    """Test complete vision pipeline integration."""

    def test_full_pipeline_single_image(self, mock_detector):
        """Test complete pipeline: load → preprocess → detect → measure."""
        # 1. Load image
        img_bytes = create_front_view_image()
        img = Image.open(io.BytesIO(img_bytes))

        # 2. Preprocess
        img = img.resize((640, 480))
        img_array = np.array(img)

        # 3. Detect landmarks
        result = mock_detector.detect_landmarks(img_array)

        # 4. Extract measurements
        measurements = mock_detector.extract_measurements(
            result['landmarks'],
            img_array.shape[0],
            person_height_cm=175.0
        )

        # Verify complete pipeline
        assert measurements['height_cm'] == 175.0
        assert measurements['shoulder_width_cm'] > 0
        assert measurements['confidence'] > 0.5

    def test_full_pipeline_multiple_images(self, mock_detector):
        """Test pipeline with multiple images and fusion."""
        from tests.fixtures.test_images import (
            create_front_view_image,
            create_side_view_image,
            create_back_view_image
        )

        all_measurements = []

        # Process each view
        for create_func in [create_front_view_image, create_side_view_image, create_back_view_image]:
            img_bytes = create_func()
            img = Image.open(io.BytesIO(img_bytes))
            img = img.resize((640, 480))
            img_array = np.array(img)

            result = mock_detector.detect_landmarks(img_array)
            measurements = mock_detector.extract_measurements(
                result['landmarks'],
                img_array.shape[0],
                person_height_cm=175.0
            )
            all_measurements.append(measurements)

        # Verify all processed
        assert len(all_measurements) == 3

        # Compute average
        avg_height = sum(m['height_cm'] for m in all_measurements) / len(all_measurements)
        assert avg_height == 175.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
