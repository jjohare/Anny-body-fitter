# Anny - Vision Module Tests
# Copyright (C) 2025 NAVER Corp.
# Apache License, Version 2.0

import pytest
import numpy as np
import torch
from PIL import Image
from anny.vision.image_preprocessing import ImagePreprocessor


class TestImagePreprocessor:
    """Test suite for ImagePreprocessor class."""

    @pytest.fixture
    def preprocessor(self):
        """Create default preprocessor instance."""
        return ImagePreprocessor(
            target_size=(640, 480),
            normalize=True,
            min_resolution=(320, 240)
        )

    @pytest.fixture
    def sample_image(self):
        """Create sample RGB image."""
        return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

    @pytest.fixture
    def sample_grayscale(self):
        """Create sample grayscale image."""
        return np.random.randint(0, 255, (480, 640), dtype=np.uint8)

    def test_init(self):
        """Test preprocessor initialization."""
        preprocessor = ImagePreprocessor(
            target_size=(800, 600),
            normalize=False,
            min_resolution=(100, 100)
        )
        assert preprocessor.target_size == (800, 600)
        assert preprocessor.normalize is False
        assert preprocessor.min_resolution == (100, 100)

    def test_validate_image_valid(self, preprocessor, sample_image):
        """Test image validation with valid image."""
        is_valid, msg = preprocessor.validate_image(sample_image)
        assert is_valid is True
        assert msg == ""

    def test_validate_image_empty(self, preprocessor):
        """Test image validation with empty image."""
        empty_img = np.array([])
        is_valid, msg = preprocessor.validate_image(empty_img)
        assert is_valid is False
        assert "Empty" in msg

    def test_validate_image_low_resolution(self, preprocessor):
        """Test image validation with low resolution."""
        low_res = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        is_valid, msg = preprocessor.validate_image(low_res)
        assert is_valid is False
        assert "resolution" in msg.lower()

    def test_validate_image_invalid_channels(self, preprocessor):
        """Test image validation with invalid channel count."""
        invalid_channels = np.random.randint(0, 255, (480, 640, 5), dtype=np.uint8)
        is_valid, msg = preprocessor.validate_image(invalid_channels)
        assert is_valid is False
        assert "channels" in msg.lower()

    def test_resize_preserve_aspect(self, preprocessor, sample_image):
        """Test aspect ratio preservation during resize."""
        resized = preprocessor.resize_preserve_aspect(sample_image)

        assert resized.shape == (480, 640, 3)  # Target size
        assert resized.dtype == sample_image.dtype

    def test_resize_preserve_aspect_smaller(self, preprocessor):
        """Test resize with smaller input image."""
        small_img = np.random.randint(0, 255, (200, 300, 3), dtype=np.uint8)
        resized = preprocessor.resize_preserve_aspect(small_img)

        assert resized.shape == (480, 640, 3)

    def test_resize_preserve_aspect_larger(self, preprocessor):
        """Test resize with larger input image."""
        large_img = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        resized = preprocessor.resize_preserve_aspect(large_img)

        assert resized.shape == (480, 640, 3)

    def test_normalize_image_uint8(self, preprocessor):
        """Test normalization of uint8 image."""
        img = np.array([0, 127, 255], dtype=np.uint8)
        normalized = preprocessor.normalize_image(img)

        assert normalized.dtype == np.float32
        assert np.allclose(normalized, [0.0, 127/255, 1.0], atol=1e-3)

    def test_normalize_image_float(self, preprocessor):
        """Test normalization of float image."""
        img = np.array([0.0, 0.5, 1.0], dtype=np.float32)
        normalized = preprocessor.normalize_image(img)

        assert normalized.dtype == np.float32
        assert np.allclose(normalized, [0.0, 0.5, 1.0])

    def test_normalize_image_clipping(self, preprocessor):
        """Test normalization clips out-of-range values."""
        img = np.array([-0.5, 0.5, 1.5], dtype=np.float32)
        normalized = preprocessor.normalize_image(img)

        assert np.min(normalized) >= 0.0
        assert np.max(normalized) <= 1.0

    def test_convert_to_rgb_grayscale(self, preprocessor, sample_grayscale):
        """Test conversion from grayscale to RGB."""
        rgb = preprocessor.convert_to_rgb(sample_grayscale)

        assert rgb.shape == (*sample_grayscale.shape, 3)
        assert np.array_equal(rgb[:, :, 0], rgb[:, :, 1])
        assert np.array_equal(rgb[:, :, 1], rgb[:, :, 2])

    def test_convert_to_rgb_rgba(self, preprocessor):
        """Test conversion from RGBA to RGB."""
        rgba = np.random.randint(0, 255, (480, 640, 4), dtype=np.uint8)
        rgb = preprocessor.convert_to_rgb(rgba)

        assert rgb.shape == (480, 640, 3)
        assert np.array_equal(rgb, rgba[:, :, :3])

    def test_convert_to_rgb_already_rgb(self, preprocessor, sample_image):
        """Test conversion when already RGB."""
        rgb = preprocessor.convert_to_rgb(sample_image)

        assert np.array_equal(rgb, sample_image)

    def test_preprocess_numpy(self, preprocessor, sample_image):
        """Test preprocessing numpy array."""
        processed, metadata = preprocessor.preprocess(sample_image)

        assert processed.shape == (480, 640, 3)
        assert processed.dtype == np.float32
        assert 0.0 <= processed.min() <= processed.max() <= 1.0
        assert metadata['original_shape'] == sample_image.shape

    def test_preprocess_torch_tensor(self, preprocessor):
        """Test preprocessing PyTorch tensor."""
        tensor = torch.rand(480, 640, 3)
        processed, metadata = preprocessor.preprocess(tensor)

        assert isinstance(processed, np.ndarray)
        assert processed.shape == (480, 640, 3)

    def test_preprocess_pil_image(self, preprocessor):
        """Test preprocessing PIL Image."""
        pil_img = Image.fromarray(np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8))
        processed, metadata = preprocessor.preprocess(pil_img)

        assert isinstance(processed, np.ndarray)
        assert processed.shape == (480, 640, 3)

    def test_preprocess_with_validation_failure(self, preprocessor):
        """Test preprocessing with validation failure."""
        invalid_img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        with pytest.raises(ValueError, match="validation failed"):
            preprocessor.preprocess(invalid_img, validate=True)

    def test_preprocess_without_validation(self, preprocessor):
        """Test preprocessing without validation."""
        invalid_img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # Should not raise when validation disabled
        processed, metadata = preprocessor.preprocess(invalid_img, validate=False)
        assert processed is not None

    def test_preprocess_metadata(self, preprocessor, sample_image):
        """Test metadata returned by preprocess."""
        processed, metadata = preprocessor.preprocess(sample_image)

        assert 'original_shape' in metadata
        assert 'preprocessed_shape' in metadata
        assert 'scale_factor' in metadata
        assert 'padding' in metadata
        assert metadata['preprocessed_shape'] == processed.shape

    def test_preprocess_batch(self, preprocessor):
        """Test batch preprocessing."""
        images = [
            np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            for _ in range(3)
        ]

        processed, metadata_list = preprocessor.preprocess_batch(images)

        assert len(processed) == 3
        assert len(metadata_list) == 3
        assert all(img.shape == (480, 640, 3) for img in processed)

    def test_preprocess_batch_with_errors(self, preprocessor):
        """Test batch preprocessing with some invalid images."""
        images = [
            np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8),
            np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8),  # Too small
            np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        ]

        processed, metadata_list = preprocessor.preprocess_batch(images, validate=True)

        assert len(processed) == 3
        assert processed[0] is not None
        assert processed[1] is None  # Failed validation
        assert processed[2] is not None
        assert 'error' in metadata_list[1]

    def test_to_tensor(self, preprocessor):
        """Test conversion to PyTorch tensor."""
        img = np.random.rand(480, 640, 3).astype(np.float32)
        tensor = preprocessor.to_tensor(img)

        assert isinstance(tensor, torch.Tensor)
        assert tensor.shape == (3, 480, 640)  # CHW format

    def test_to_tensor_grayscale(self, preprocessor):
        """Test conversion of grayscale to tensor."""
        img = np.random.rand(480, 640).astype(np.float32)
        tensor = preprocessor.to_tensor(img)

        assert isinstance(tensor, torch.Tensor)
        assert tensor.shape == (1, 480, 640)

    def test_normalization_disabled(self):
        """Test preprocessor with normalization disabled."""
        preprocessor = ImagePreprocessor(normalize=False)
        img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

        processed, _ = preprocessor.preprocess(img)

        assert processed.dtype == np.uint8
        assert processed.max() > 1.0  # Not normalized
