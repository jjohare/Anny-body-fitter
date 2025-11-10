# Anny - Vision Module
# Copyright (C) 2025 NAVER Corp.
# Apache License, Version 2.0

import numpy as np
import torch
from typing import Tuple, Optional, Union
from PIL import Image


class ImagePreprocessor:
    """
    Handles image preprocessing and normalization for body landmark detection.

    Performs operations including:
    - Image resizing and normalization
    - Color space conversion
    - Quality validation
    - Aspect ratio preservation
    """

    def __init__(
        self,
        target_size: Tuple[int, int] = (640, 480),
        normalize: bool = True,
        min_resolution: Tuple[int, int] = (320, 240),
        device: str = 'cpu'
    ):
        """
        Initialize image preprocessor.

        Args:
            target_size: Target image size (width, height)
            normalize: Whether to normalize pixel values to [0, 1]
            min_resolution: Minimum acceptable resolution
            device: Device for tensor operations ('cpu' or 'cuda')
        """
        self.target_size = target_size
        self.normalize = normalize
        self.min_resolution = min_resolution
        self.device = device

    def validate_image(self, image: np.ndarray) -> Tuple[bool, str]:
        """
        Validate image quality and dimensions.

        Args:
            image: Input image as numpy array

        Returns:
            Tuple of (is_valid, error_message)
        """
        if image is None or image.size == 0:
            return False, "Empty or None image"

        if len(image.shape) not in [2, 3]:
            return False, f"Invalid image shape: {image.shape}"

        height, width = image.shape[:2]

        if width < self.min_resolution[0] or height < self.min_resolution[1]:
            return False, f"Image resolution {width}x{height} below minimum {self.min_resolution}"

        if len(image.shape) == 3 and image.shape[2] not in [3, 4]:
            return False, f"Invalid number of channels: {image.shape[2]}"

        return True, ""

    def resize_preserve_aspect(
        self,
        image: np.ndarray,
        target_size: Optional[Tuple[int, int]] = None
    ) -> np.ndarray:
        """
        Resize image while preserving aspect ratio.

        Args:
            image: Input image
            target_size: Target size (width, height), uses self.target_size if None

        Returns:
            Resized image with padding if needed
        """
        if target_size is None:
            target_size = self.target_size

        height, width = image.shape[:2]
        target_width, target_height = target_size

        # Calculate scaling factor
        scale = min(target_width / width, target_height / height)
        new_width = int(width * scale)
        new_height = int(height * scale)

        # Resize using PIL for better quality
        pil_image = Image.fromarray(image)
        pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        resized = np.array(pil_image)

        # Create padded image
        if len(image.shape) == 3:
            padded = np.zeros((target_height, target_width, image.shape[2]), dtype=image.dtype)
        else:
            padded = np.zeros((target_height, target_width), dtype=image.dtype)

        # Center the resized image
        y_offset = (target_height - new_height) // 2
        x_offset = (target_width - new_width) // 2

        if len(image.shape) == 3:
            padded[y_offset:y_offset+new_height, x_offset:x_offset+new_width, :] = resized
        else:
            padded[y_offset:y_offset+new_height, x_offset:x_offset+new_width] = resized

        return padded

    def normalize_image(self, image: np.ndarray) -> np.ndarray:
        """
        Normalize image pixel values to [0, 1] range.

        Args:
            image: Input image

        Returns:
            Normalized image
        """
        if image.dtype == np.uint8:
            return image.astype(np.float32) / 255.0
        elif image.dtype in [np.float32, np.float64]:
            # Already float, ensure in [0, 1]
            return np.clip(image, 0.0, 1.0).astype(np.float32)
        else:
            raise ValueError(f"Unsupported image dtype: {image.dtype}")

    def convert_to_rgb(self, image: np.ndarray) -> np.ndarray:
        """
        Convert image to RGB format.

        Args:
            image: Input image (grayscale, RGB, or RGBA)

        Returns:
            RGB image
        """
        if len(image.shape) == 2:
            # Grayscale to RGB
            return np.stack([image] * 3, axis=-1)
        elif image.shape[2] == 4:
            # RGBA to RGB (discard alpha)
            return image[:, :, :3]
        elif image.shape[2] == 3:
            return image
        else:
            raise ValueError(f"Cannot convert image with {image.shape[2]} channels to RGB")

    def preprocess(
        self,
        image: Union[np.ndarray, torch.Tensor, Image.Image],
        validate: bool = True
    ) -> Tuple[np.ndarray, dict]:
        """
        Preprocess image for landmark detection.

        Args:
            image: Input image (numpy array, torch tensor, or PIL Image)
            validate: Whether to validate image quality

        Returns:
            Tuple of (preprocessed_image, metadata_dict)

        Raises:
            ValueError: If image validation fails
        """
        # Convert to numpy if needed
        if isinstance(image, torch.Tensor):
            image = image.cpu().numpy()
            if image.dtype == torch.float32 or image.dtype == torch.float64:
                image = (image * 255).astype(np.uint8)
        elif isinstance(image, Image.Image):
            image = np.array(image)

        # Store original metadata
        metadata = {
            'original_shape': image.shape,
            'original_dtype': str(image.dtype),
            'preprocessed_shape': None,
            'scale_factor': None,
            'padding': None
        }

        # Validate if requested
        if validate:
            is_valid, error_msg = self.validate_image(image)
            if not is_valid:
                raise ValueError(f"Image validation failed: {error_msg}")

        # Convert to RGB
        image = self.convert_to_rgb(image)

        # Resize with aspect ratio preservation
        original_height, original_width = image.shape[:2]
        image = self.resize_preserve_aspect(image)

        # Calculate metadata
        new_height, new_width = image.shape[:2]
        metadata['preprocessed_shape'] = image.shape
        metadata['scale_factor'] = min(
            new_width / original_width,
            new_height / original_height
        )
        metadata['padding'] = {
            'top': (new_height - int(original_height * metadata['scale_factor'])) // 2,
            'left': (new_width - int(original_width * metadata['scale_factor'])) // 2
        }

        # Normalize if requested
        if self.normalize:
            image = self.normalize_image(image)

        return image, metadata

    def preprocess_batch(
        self,
        images: list,
        validate: bool = True
    ) -> Tuple[list, list]:
        """
        Preprocess batch of images.

        Args:
            images: List of input images
            validate: Whether to validate image quality

        Returns:
            Tuple of (preprocessed_images, metadata_list)
        """
        preprocessed = []
        metadata_list = []

        for img in images:
            try:
                prep_img, metadata = self.preprocess(img, validate=validate)
                preprocessed.append(prep_img)
                metadata_list.append(metadata)
            except ValueError as e:
                # Store error in metadata
                metadata_list.append({'error': str(e)})
                preprocessed.append(None)

        return preprocessed, metadata_list

    def to_tensor(self, image: np.ndarray) -> torch.Tensor:
        """
        Convert preprocessed numpy image to PyTorch tensor.

        Args:
            image: Preprocessed numpy image

        Returns:
            PyTorch tensor in (C, H, W) format
        """
        # Convert HWC to CHW
        if len(image.shape) == 3:
            tensor = torch.from_numpy(image).permute(2, 0, 1)
        else:
            tensor = torch.from_numpy(image).unsqueeze(0)

        return tensor.to(self.device)
