# Anny - Vision Module
# Copyright (C) 2025 NAVER Corp.
# Apache License, Version 2.0

import numpy as np
import torch
from typing import Optional, List, Dict, Tuple, Union
from dataclasses import dataclass

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    mp = None


@dataclass
class LandmarkResult:
    """Container for landmark detection results."""
    landmarks: np.ndarray  # Shape: (num_landmarks, 3) - x, y, z coordinates
    confidence: np.ndarray  # Shape: (num_landmarks,) - confidence scores
    visibility: np.ndarray  # Shape: (num_landmarks,) - visibility scores
    overall_confidence: float  # Overall detection confidence
    image_shape: Tuple[int, int]  # Original image shape (height, width)
    world_landmarks: Optional[np.ndarray] = None  # 3D world coordinates if available


class LandmarkDetector:
    """
    Detects body landmarks from images using MediaPipe Pose.

    Provides 33 body keypoints including:
    - Face landmarks (nose, eyes, ears, mouth)
    - Torso landmarks (shoulders, hips)
    - Arm landmarks (elbows, wrists, hands)
    - Leg landmarks (knees, ankles, feet)

    Each landmark includes:
    - 2D image coordinates (normalized to [0, 1])
    - Depth coordinate (relative to hips)
    - Confidence score
    - Visibility score
    """

    # MediaPipe Pose landmark indices
    LANDMARK_NAMES = [
        'nose', 'left_eye_inner', 'left_eye', 'left_eye_outer',
        'right_eye_inner', 'right_eye', 'right_eye_outer',
        'left_ear', 'right_ear', 'mouth_left', 'mouth_right',
        'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
        'left_wrist', 'right_wrist', 'left_pinky', 'right_pinky',
        'left_index', 'right_index', 'left_thumb', 'right_thumb',
        'left_hip', 'right_hip', 'left_knee', 'right_knee',
        'left_ankle', 'right_ankle', 'left_heel', 'right_heel',
        'left_foot_index', 'right_foot_index'
    ]

    def __init__(
        self,
        model_complexity: int = 1,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        static_image_mode: bool = True,
        enable_segmentation: bool = False,
        smooth_landmarks: bool = True,
        device: str = 'cpu'
    ):
        """
        Initialize landmark detector with MediaPipe.

        Args:
            model_complexity: Model complexity (0, 1, or 2). Higher = more accurate but slower
            min_detection_confidence: Minimum confidence for detection to be successful
            min_tracking_confidence: Minimum confidence for landmark tracking
            static_image_mode: If True, treats each image independently
            enable_segmentation: If True, also generates segmentation mask
            smooth_landmarks: If True, applies temporal smoothing (only for video)
            device: Device for processing ('cpu' or 'cuda')

        Raises:
            ImportError: If MediaPipe is not installed
        """
        if not MEDIAPIPE_AVAILABLE:
            raise ImportError(
                "MediaPipe is not installed. Install with: pip install mediapipe"
            )

        self.model_complexity = model_complexity
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.static_image_mode = static_image_mode
        self.enable_segmentation = enable_segmentation
        self.smooth_landmarks = smooth_landmarks
        self.device = device

        # Initialize MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=static_image_mode,
            model_complexity=model_complexity,
            smooth_landmarks=smooth_landmarks,
            enable_segmentation=enable_segmentation,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )

    def detect(
        self,
        image: np.ndarray,
        return_world_landmarks: bool = True
    ) -> Optional[LandmarkResult]:
        """
        Detect body landmarks in a single image.

        Args:
            image: Input image as numpy array (RGB format, uint8 or float32)
            return_world_landmarks: If True, includes 3D world coordinates

        Returns:
            LandmarkResult object if detection successful, None otherwise
        """
        # Ensure image is in correct format
        if image.dtype == np.float32 or image.dtype == np.float64:
            image_uint8 = (image * 255).astype(np.uint8)
        else:
            image_uint8 = image

        # Process image
        results = self.pose.process(image_uint8)

        if not results.pose_landmarks:
            return None

        # Extract landmarks
        height, width = image.shape[:2]
        landmarks = []
        confidences = []
        visibilities = []

        for landmark in results.pose_landmarks.landmark:
            landmarks.append([landmark.x, landmark.y, landmark.z])
            # MediaPipe doesn't provide per-landmark confidence in Pose
            # Use visibility as proxy for confidence
            confidences.append(landmark.visibility)
            visibilities.append(landmark.visibility)

        landmarks = np.array(landmarks, dtype=np.float32)
        confidences = np.array(confidences, dtype=np.float32)
        visibilities = np.array(visibilities, dtype=np.float32)

        # Calculate overall confidence as mean of visible landmarks
        visible_mask = visibilities > 0.5
        overall_confidence = (
            confidences[visible_mask].mean()
            if visible_mask.any()
            else 0.0
        )

        # Extract world landmarks if requested
        world_landmarks = None
        if return_world_landmarks and results.pose_world_landmarks:
            world_landmarks = []
            for landmark in results.pose_world_landmarks.landmark:
                world_landmarks.append([landmark.x, landmark.y, landmark.z])
            world_landmarks = np.array(world_landmarks, dtype=np.float32)

        return LandmarkResult(
            landmarks=landmarks,
            confidence=confidences,
            visibility=visibilities,
            overall_confidence=float(overall_confidence),
            image_shape=(height, width),
            world_landmarks=world_landmarks
        )

    def detect_batch(
        self,
        images: List[np.ndarray],
        return_world_landmarks: bool = True,
        skip_failed: bool = True
    ) -> List[Optional[LandmarkResult]]:
        """
        Detect landmarks in batch of images.

        Args:
            images: List of input images
            return_world_landmarks: If True, includes 3D world coordinates
            skip_failed: If True, returns None for failed detections, otherwise raises error

        Returns:
            List of LandmarkResult objects (None for failed detections if skip_failed=True)
        """
        results = []
        for image in images:
            try:
                result = self.detect(image, return_world_landmarks=return_world_landmarks)
                results.append(result)
            except Exception as e:
                if skip_failed:
                    results.append(None)
                else:
                    raise RuntimeError(f"Landmark detection failed: {str(e)}") from e

        return results

    def get_landmark_by_name(
        self,
        result: LandmarkResult,
        name: str
    ) -> Tuple[np.ndarray, float, float]:
        """
        Get specific landmark by name.

        Args:
            result: LandmarkResult object
            name: Landmark name (e.g., 'nose', 'left_shoulder')

        Returns:
            Tuple of (coordinates, confidence, visibility)

        Raises:
            ValueError: If landmark name is invalid
        """
        if name not in self.LANDMARK_NAMES:
            raise ValueError(
                f"Invalid landmark name: {name}. "
                f"Valid names: {', '.join(self.LANDMARK_NAMES)}"
            )

        idx = self.LANDMARK_NAMES.index(name)
        return (
            result.landmarks[idx],
            result.confidence[idx],
            result.visibility[idx]
        )

    def filter_low_confidence(
        self,
        result: LandmarkResult,
        min_confidence: Optional[float] = None
    ) -> LandmarkResult:
        """
        Filter out low-confidence landmarks.

        Args:
            result: Input LandmarkResult
            min_confidence: Minimum confidence threshold (uses detector default if None)

        Returns:
            Filtered LandmarkResult with low-confidence landmarks set to NaN
        """
        if min_confidence is None:
            min_confidence = self.min_detection_confidence

        filtered_landmarks = result.landmarks.copy()
        mask = result.confidence < min_confidence
        filtered_landmarks[mask] = np.nan

        return LandmarkResult(
            landmarks=filtered_landmarks,
            confidence=result.confidence,
            visibility=result.visibility,
            overall_confidence=result.overall_confidence,
            image_shape=result.image_shape,
            world_landmarks=result.world_landmarks
        )

    def to_pixel_coordinates(
        self,
        result: LandmarkResult,
        denormalize: bool = True
    ) -> np.ndarray:
        """
        Convert normalized landmarks to pixel coordinates.

        Args:
            result: LandmarkResult object
            denormalize: If True, converts from [0,1] to pixel coordinates

        Returns:
            Landmarks in pixel coordinates (num_landmarks, 3)
        """
        if not denormalize:
            return result.landmarks

        height, width = result.image_shape
        pixel_coords = result.landmarks.copy()
        pixel_coords[:, 0] *= width
        pixel_coords[:, 1] *= height
        # Z coordinate is already in world scale (meters)

        return pixel_coords

    def __del__(self):
        """Cleanup MediaPipe resources."""
        if hasattr(self, 'pose'):
            self.pose.close()
