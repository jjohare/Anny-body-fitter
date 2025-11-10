# Anny Body Fitter - Mock Vision Module
# Copyright (C) 2025 NAVER Corp.
# Apache License, Version 2.0
"""
Mock implementations for computer vision landmark detection.

Used for testing vision-dependent code without requiring actual CV models.
Provides realistic 68-point face landmarks (dlib format) and 33-point body
keypoints (MediaPipe Holistic format).
"""
import numpy as np
from typing import Dict, Tuple, Optional, List
from enum import Enum


class PoseVariant(Enum):
    """Available pose variants for testing."""
    FRONT = "front"
    SIDE_LEFT = "side_left"
    SIDE_RIGHT = "side_right"
    BACK = "back"
    THREE_QUARTER_LEFT = "three_quarter_left"
    THREE_QUARTER_RIGHT = "three_quarter_right"
    ARMS_RAISED = "arms_raised"
    T_POSE = "t_pose"


class MockLandmarkDetector:
    """
    Mock landmark detector for testing.

    Generates realistic 68-point face landmarks (dlib format) and 33-point
    body keypoints (MediaPipe Holistic format) with proper confidence scores
    and depth estimation.
    """

    def __init__(self, confidence: float = 0.95, pose_variant: PoseVariant = PoseVariant.FRONT):
        """
        Initialize mock detector.

        Args:
            confidence: Mock confidence score to return (0.0-1.0)
            pose_variant: Default pose variant to generate
        """
        self.confidence = np.clip(confidence, 0.0, 1.0)
        self.detection_count = 0
        self.pose_variant = pose_variant

    def detect(self, image: np.ndarray, pose_variant: Optional[PoseVariant] = None) -> Dict[str, np.ndarray]:
        """
        Mock landmark detection with realistic output format.

        Args:
            image: Input image (H, W, C)
            pose_variant: Override default pose variant

        Returns:
            Dictionary with keys:
                - 'face': (68, 2) face landmarks in dlib format
                - 'body': (33, 2) body keypoints in MediaPipe Holistic format
                - 'face_confidence': (68,) confidence per face landmark
                - 'body_confidence': (33,) confidence per body keypoint
                - 'overall_confidence': float overall detection confidence
        """
        self.detection_count += 1

        height, width = image.shape[:2]
        variant = pose_variant or self.pose_variant

        # Generate consistent but deterministic landmarks
        np.random.seed(42 + self.detection_count)

        # 68-point face model (standard dlib/MediaPipe)
        face_landmarks = self._generate_face_landmarks(width, height)

        # 33-point body keypoints (MediaPipe Holistic format)
        body_landmarks = self._generate_body_landmarks(width, height, variant)

        # Generate realistic per-landmark confidence scores
        face_confidence = self._generate_confidence_scores(68, base=self.confidence)
        body_confidence = self._generate_confidence_scores(33, base=self.confidence)

        return {
            'face': face_landmarks,
            'body': body_landmarks,
            'face_confidence': face_confidence,
            'body_confidence': body_confidence,
            'overall_confidence': self.confidence
        }

    def _generate_face_landmarks(self, width: int, height: int) -> np.ndarray:
        """
        Generate realistic 68-point face landmarks in dlib format.

        Format:
            - Points 0-16: Jaw line (left to right)
            - Points 17-21: Left eyebrow
            - Points 22-26: Right eyebrow
            - Points 27-35: Nose bridge and tip
            - Points 36-41: Left eye
            - Points 42-47: Right eye
            - Points 48-59: Outer mouth
            - Points 60-67: Inner mouth

        Args:
            width: Image width
            height: Image height

        Returns:
            (68, 2) array of (x, y) landmark coordinates
        """
        # Center face in upper portion of image with realistic proportions
        center_x, center_y = width // 2, height // 3
        face_width = width // 5  # More realistic face width
        face_height = height // 4  # Realistic face height

        landmarks = np.zeros((68, 2))

        # Jaw line (0-16) - realistic oval shape
        for i in range(17):
            # Normalized position along jaw
            t = (i - 8) / 8.0  # -1 to 1
            # Elliptical jaw shape
            x_offset = face_width * 0.85 * t
            y_offset = face_height * 0.95 * np.sqrt(1 - (t * 0.7) ** 2)
            landmarks[i] = [center_x + x_offset, center_y + y_offset]

        # Left eyebrow (17-21) - curved arch
        for i in range(17, 22):
            t = (i - 17) / 4.0
            landmarks[i] = [
                center_x - face_width * 0.5 + t * face_width * 0.35,
                center_y - face_height * 0.45 - 0.03 * face_height * np.sin(t * np.pi)
            ]

        # Right eyebrow (22-26) - curved arch
        for i in range(22, 27):
            t = (i - 22) / 4.0
            landmarks[i] = [
                center_x + face_width * 0.15 + t * face_width * 0.35,
                center_y - face_height * 0.45 - 0.03 * face_height * np.sin(t * np.pi)
            ]

        # Nose bridge (27-30)
        for i in range(27, 31):
            t = (i - 27) / 3.0
            landmarks[i] = [center_x, center_y - face_height * 0.25 + t * face_height * 0.35]

        # Nose tip and wings (31-35)
        landmarks[31] = [center_x - face_width * 0.12, center_y + face_height * 0.15]
        landmarks[32] = [center_x - face_width * 0.06, center_y + face_height * 0.2]
        landmarks[33] = [center_x, center_y + face_height * 0.22]  # Nose tip
        landmarks[34] = [center_x + face_width * 0.06, center_y + face_height * 0.2]
        landmarks[35] = [center_x + face_width * 0.12, center_y + face_height * 0.15]

        # Left eye (36-41) - elliptical shape
        eye_center_l = [center_x - face_width * 0.3, center_y - face_height * 0.15]
        eye_angles = np.array([0, np.pi/3, 2*np.pi/3, np.pi, 4*np.pi/3, 5*np.pi/3])
        for i, angle in enumerate(eye_angles):
            landmarks[36 + i] = [
                eye_center_l[0] + face_width * 0.12 * np.cos(angle),
                eye_center_l[1] + face_height * 0.08 * np.sin(angle)
            ]

        # Right eye (42-47) - elliptical shape
        eye_center_r = [center_x + face_width * 0.3, center_y - face_height * 0.15]
        for i, angle in enumerate(eye_angles):
            landmarks[42 + i] = [
                eye_center_r[0] + face_width * 0.12 * np.cos(angle),
                eye_center_r[1] + face_height * 0.08 * np.sin(angle)
            ]

        # Outer mouth (48-59) - realistic lip shape
        mouth_center = [center_x, center_y + face_height * 0.55]
        outer_mouth_points = 12
        for i in range(outer_mouth_points):
            angle = (i / outer_mouth_points) * 2 * np.pi
            # Horizontal ellipse for mouth
            x_radius = face_width * 0.25
            y_radius = face_height * 0.12
            landmarks[48 + i] = [
                mouth_center[0] + x_radius * np.cos(angle),
                mouth_center[1] + y_radius * np.sin(angle)
            ]

        # Inner mouth (60-67) - smaller ellipse
        inner_mouth_points = 8
        for i in range(inner_mouth_points):
            angle = (i / inner_mouth_points) * 2 * np.pi
            x_radius = face_width * 0.18
            y_radius = face_height * 0.08
            landmarks[60 + i] = [
                mouth_center[0] + x_radius * np.cos(angle),
                mouth_center[1] + y_radius * np.sin(angle)
            ]

        return landmarks

    def _generate_body_landmarks(self, width: int, height: int,
                                 pose_variant: PoseVariant = PoseVariant.FRONT) -> np.ndarray:
        """
        Generate realistic 33-point body keypoints in MediaPipe Holistic format.

        MediaPipe Holistic 33 keypoints:
            0-10: Face (nose, eyes, ears, mouth)
            11-16: Torso (shoulders, elbows, wrists)
            23-28: Legs (hips, knees, ankles)
            17-22: Hands (optional, set to wrist position)
            29-32: Feet (optional, set to ankle position)

        Args:
            width: Image width
            height: Image height
            pose_variant: Pose variation to generate

        Returns:
            (33, 2) array of (x, y) landmark coordinates
        """
        center_x = width // 2
        landmarks = np.zeros((33, 2))

        # Apply pose-specific transformations
        if pose_variant == PoseVariant.FRONT:
            return self._generate_front_pose(center_x, width, height)
        elif pose_variant == PoseVariant.SIDE_LEFT:
            return self._generate_side_pose(center_x, width, height, left=True)
        elif pose_variant == PoseVariant.SIDE_RIGHT:
            return self._generate_side_pose(center_x, width, height, left=False)
        elif pose_variant == PoseVariant.T_POSE:
            return self._generate_t_pose(center_x, width, height)
        elif pose_variant == PoseVariant.ARMS_RAISED:
            return self._generate_arms_raised_pose(center_x, width, height)
        else:
            # Default to front pose
            return self._generate_front_pose(center_x, width, height)

    def _generate_front_pose(self, center_x: float, width: int, height: int) -> np.ndarray:
        """Generate front-facing pose with arms at sides."""
        landmarks = np.zeros((33, 2))

        # Face keypoints (0-10)
        landmarks[0] = [center_x, height * 0.08]  # nose
        landmarks[1] = [center_x - width * 0.02, height * 0.07]  # left eye inner
        landmarks[2] = [center_x - width * 0.04, height * 0.07]  # left eye
        landmarks[3] = [center_x - width * 0.06, height * 0.07]  # left eye outer
        landmarks[4] = [center_x + width * 0.02, height * 0.07]  # right eye inner
        landmarks[5] = [center_x + width * 0.04, height * 0.07]  # right eye
        landmarks[6] = [center_x + width * 0.06, height * 0.07]  # right eye outer
        landmarks[7] = [center_x - width * 0.08, height * 0.08]  # left ear
        landmarks[8] = [center_x + width * 0.08, height * 0.08]  # right ear
        landmarks[9] = [center_x - width * 0.03, height * 0.10]  # mouth left
        landmarks[10] = [center_x + width * 0.03, height * 0.10]  # mouth right

        # Upper body (11-16)
        landmarks[11] = [center_x - width * 0.12, height * 0.20]  # left shoulder
        landmarks[12] = [center_x + width * 0.12, height * 0.20]  # right shoulder
        landmarks[13] = [center_x - width * 0.14, height * 0.38]  # left elbow
        landmarks[14] = [center_x + width * 0.14, height * 0.38]  # right elbow
        landmarks[15] = [center_x - width * 0.16, height * 0.56]  # left wrist
        landmarks[16] = [center_x + width * 0.16, height * 0.56]  # right wrist

        # Hands (17-22) - simplified to wrist positions
        landmarks[17:19] = landmarks[15]  # left hand
        landmarks[19:21] = landmarks[16]  # right hand
        landmarks[21] = landmarks[15]
        landmarks[22] = landmarks[16]

        # Lower body (23-28)
        landmarks[23] = [center_x - width * 0.08, height * 0.60]  # left hip
        landmarks[24] = [center_x + width * 0.08, height * 0.60]  # right hip
        landmarks[25] = [center_x - width * 0.09, height * 0.80]  # left knee
        landmarks[26] = [center_x + width * 0.09, height * 0.80]  # right knee
        landmarks[27] = [center_x - width * 0.08, height * 0.95]  # left ankle
        landmarks[28] = [center_x + width * 0.08, height * 0.95]  # right ankle

        # Feet (29-32) - simplified to ankle positions
        landmarks[29:31] = landmarks[27]  # left foot
        landmarks[31:33] = landmarks[28]  # right foot

        return landmarks

    def _generate_side_pose(self, center_x: float, width: int, height: int, left: bool = True) -> np.ndarray:
        """Generate side-view pose."""
        landmarks = self._generate_front_pose(center_x, width, height)

        # Adjust for side view - compress depth dimension
        side_factor = -0.05 if left else 0.05

        # Shift one side of body behind the other
        for i in [11, 13, 15, 23, 25, 27]:  # Left side
            landmarks[i, 0] += width * side_factor

        return landmarks

    def _generate_t_pose(self, center_x: float, width: int, height: int) -> np.ndarray:
        """Generate T-pose with arms extended."""
        landmarks = self._generate_front_pose(center_x, width, height)

        # Extend arms horizontally
        landmarks[13] = [center_x - width * 0.25, height * 0.20]  # left elbow
        landmarks[14] = [center_x + width * 0.25, height * 0.20]  # right elbow
        landmarks[15] = [center_x - width * 0.38, height * 0.20]  # left wrist
        landmarks[16] = [center_x + width * 0.38, height * 0.20]  # right wrist

        # Update hand positions
        landmarks[17:19] = landmarks[15]
        landmarks[19:21] = landmarks[16]
        landmarks[21] = landmarks[15]
        landmarks[22] = landmarks[16]

        return landmarks

    def _generate_arms_raised_pose(self, center_x: float, width: int, height: int) -> np.ndarray:
        """Generate pose with arms raised overhead."""
        landmarks = self._generate_front_pose(center_x, width, height)

        # Raise arms overhead
        landmarks[13] = [center_x - width * 0.10, height * 0.10]  # left elbow
        landmarks[14] = [center_x + width * 0.10, height * 0.10]  # right elbow
        landmarks[15] = [center_x - width * 0.08, height * 0.03]  # left wrist
        landmarks[16] = [center_x + width * 0.08, height * 0.03]  # right wrist

        # Update hand positions
        landmarks[17:19] = landmarks[15]
        landmarks[19:21] = landmarks[16]
        landmarks[21] = landmarks[15]
        landmarks[22] = landmarks[16]

        return landmarks

    def _generate_confidence_scores(self, n_points: int, base: float = 0.95) -> np.ndarray:
        """
        Generate realistic per-landmark confidence scores.

        Args:
            n_points: Number of landmarks
            base: Base confidence level

        Returns:
            (n_points,) array of confidence scores in [0, 1]
        """
        # Add realistic variation to confidence scores
        variation = np.random.uniform(-0.1, 0.05, n_points)
        confidences = np.clip(base + variation, 0.0, 1.0)
        return confidences

    def reset_counter(self):
        """Reset detection counter."""
        self.detection_count = 0


class MockDepthEstimator:
    """
    Mock depth estimation for 2D to 3D reconstruction.

    Provides realistic depth estimates based on anatomical constraints
    and perspective projection principles.
    """

    def __init__(self, baseline_depth: float = 2.0):
        """
        Initialize depth estimator.

        Args:
            baseline_depth: Average distance from camera in meters
        """
        self.baseline_depth = baseline_depth

    def estimate_depth(self, image: np.ndarray, landmarks: np.ndarray,
                      pose_variant: PoseVariant = PoseVariant.FRONT) -> np.ndarray:
        """
        Estimate realistic depth for landmarks.

        Args:
            image: Input image (H, W, C)
            landmarks: 2D landmark positions (N, 2)
            pose_variant: Pose type for depth estimation

        Returns:
            Depth values for each landmark (N,) in meters
        """
        n_landmarks = len(landmarks)
        depths = np.zeros(n_landmarks)

        height, width = image.shape[:2]

        for i, (x, y) in enumerate(landmarks):
            # Normalize coordinates
            norm_x = (x - width / 2) / (width / 2)
            norm_y = (y - height / 2) / (height / 2)

            # Base depth from perspective (things higher in frame are closer)
            perspective_depth = self.baseline_depth - norm_y * 0.3

            # Add horizontal offset for side poses
            if pose_variant in [PoseVariant.SIDE_LEFT, PoseVariant.SIDE_RIGHT]:
                # Add depth variation based on x position
                lateral_depth = abs(norm_x) * 0.2
                depths[i] = perspective_depth + lateral_depth
            else:
                # Front/back pose - minimal depth variation
                depths[i] = perspective_depth + abs(norm_x) * 0.05

            # Add slight random variation
            depths[i] += np.random.normal(0, 0.02)

            # Clamp to reasonable range (0.5m to 5m)
            depths[i] = np.clip(depths[i], 0.5, 5.0)

        return depths

    def estimate_depth_map(self, image: np.ndarray) -> np.ndarray:
        """
        Generate a full depth map for the image.

        Args:
            image: Input image (H, W, C)

        Returns:
            Depth map (H, W) with depth values in meters
        """
        height, width = image.shape[:2]

        # Create gradient-based depth map
        y_coords = np.linspace(0, 1, height)
        depth_gradient = self.baseline_depth - y_coords.reshape(-1, 1) * 0.5

        # Add slight horizontal variation
        x_variation = np.linspace(-0.05, 0.05, width)
        depth_map = depth_gradient + x_variation

        # Add noise for realism
        noise = np.random.normal(0, 0.01, (height, width))
        depth_map = depth_map + noise

        return np.clip(depth_map, 0.5, 5.0)


def landmarks_to_vertices_mock(
    landmarks: Dict[str, np.ndarray],
    image_shape: Tuple[int, int]
) -> np.ndarray:
    """
    Mock conversion from 2D landmarks to 3D vertices.

    Args:
        landmarks: Dictionary with face and body landmarks
        image_shape: (height, width) of source image

    Returns:
        Mock vertex array (V, 3)
    """
    # This is a placeholder - real implementation would use
    # sophisticated 2D->3D reconstruction

    # Combine all landmarks
    all_landmarks = np.vstack([
        landmarks['face'],
        landmarks['body']
    ])

    # Normalize to [-1, 1] range
    height, width = image_shape
    normalized = all_landmarks.copy()
    normalized[:, 0] = (normalized[:, 0] / width) * 2 - 1
    normalized[:, 1] = (normalized[:, 1] / height) * 2 - 1

    # Add mock depth dimension
    depth = np.random.rand(len(normalized)) * 0.5 + 0.5

    vertices_3d = np.column_stack([
        normalized[:, 0] * 0.3,  # x: shoulder width scale
        depth,  # y: depth
        normalized[:, 1] * 1.0  # z: height scale
    ])

    return vertices_3d
