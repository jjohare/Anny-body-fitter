# Anny - Vision Module
# Copyright (C) 2025 NAVER Corp.
# Apache License, Version 2.0

import numpy as np
import torch
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from .landmark_detector import LandmarkResult


@dataclass
class BodyMeasurements:
    """Container for extracted body measurements."""
    height: Optional[float] = None  # Total height in meters
    shoulder_width: Optional[float] = None  # Shoulder span in meters
    waist_circumference: Optional[float] = None  # Waist circumference in meters
    hip_circumference: Optional[float] = None  # Hip circumference in meters
    chest_circumference: Optional[float] = None  # Chest circumference in meters

    # Limb lengths in meters
    left_arm_length: Optional[float] = None
    right_arm_length: Optional[float] = None
    left_leg_length: Optional[float] = None
    right_leg_length: Optional[float] = None

    # Segment lengths
    torso_length: Optional[float] = None
    upper_arm_length_left: Optional[float] = None
    upper_arm_length_right: Optional[float] = None
    forearm_length_left: Optional[float] = None
    forearm_length_right: Optional[float] = None
    thigh_length_left: Optional[float] = None
    thigh_length_right: Optional[float] = None
    shin_length_left: Optional[float] = None
    shin_length_right: Optional[float] = None

    # Confidence scores for each measurement
    confidence_scores: Optional[Dict[str, float]] = None

    # Overall quality score
    overall_confidence: float = 0.0


class MeasurementExtractor:
    """
    Extracts body measurements from detected landmarks.

    Estimates various body measurements including:
    - Height (head to toe)
    - Shoulder width (shoulder span)
    - Waist and hip circumference (estimated from landmarks)
    - Limb lengths (arms and legs)
    - Segment lengths (upper arm, forearm, thigh, shin, torso)

    Uses both 2D image landmarks and 3D world coordinates for robust estimation.
    """

    # Anthropometric ratios for circumference estimation
    # Based on typical human body proportions
    CIRCUMFERENCE_RATIOS = {
        'waist': 2.5,  # waist_width * ratio ≈ circumference
        'hip': 2.8,
        'chest': 2.9
    }

    def __init__(
        self,
        use_world_landmarks: bool = True,
        min_confidence: float = 0.5,
        device: str = 'cpu'
    ):
        """
        Initialize measurement extractor.

        Args:
            use_world_landmarks: If True, uses 3D world coordinates when available
            min_confidence: Minimum landmark confidence for measurement extraction
            device: Device for tensor operations
        """
        self.use_world_landmarks = use_world_landmarks
        self.min_confidence = min_confidence
        self.device = device

    def _euclidean_distance(
        self,
        point1: np.ndarray,
        point2: np.ndarray
    ) -> float:
        """Calculate Euclidean distance between two points."""
        return float(np.linalg.norm(point1 - point2))

    def _get_landmark_coords(
        self,
        result: LandmarkResult,
        index: int,
        use_world: bool = True
    ) -> Optional[np.ndarray]:
        """
        Get landmark coordinates with confidence check.

        Args:
            result: LandmarkResult object
            index: Landmark index
            use_world: If True, uses world coordinates when available

        Returns:
            Landmark coordinates or None if confidence too low
        """
        if result.confidence[index] < self.min_confidence:
            return None

        if use_world and result.world_landmarks is not None:
            return result.world_landmarks[index]
        else:
            return result.landmarks[index]

    def extract_height(self, result: LandmarkResult) -> Tuple[Optional[float], float]:
        """
        Extract height from landmarks.

        Uses multiple methods for robustness:
        1. Head to heel distance (most accurate)
        2. Head to ankle distance (fallback)
        3. Proportional estimation from visible landmarks

        Args:
            result: LandmarkResult object

        Returns:
            Tuple of (height in meters, confidence score)
        """
        use_world = self.use_world_landmarks and result.world_landmarks is not None

        # Get head and foot landmarks
        nose = self._get_landmark_coords(result, 0, use_world)  # Nose
        left_heel = self._get_landmark_coords(result, 29, use_world)
        right_heel = self._get_landmark_coords(result, 30, use_world)
        left_ankle = self._get_landmark_coords(result, 27, use_world)
        right_ankle = self._get_landmark_coords(result, 28, use_world)

        if nose is None:
            return None, 0.0

        heights = []
        confidences = []

        # Method 1: Nose to heel (most accurate)
        if left_heel is not None:
            heights.append(abs(nose[2] - left_heel[2]) if use_world else abs(nose[1] - left_heel[1]))
            confidences.append(result.confidence[[0, 29]].mean())
        if right_heel is not None:
            heights.append(abs(nose[2] - right_heel[2]) if use_world else abs(nose[1] - right_heel[1]))
            confidences.append(result.confidence[[0, 30]].mean())

        # Method 2: Nose to ankle (fallback)
        if left_ankle is not None:
            # Add typical ankle-to-heel offset (≈5% of height)
            ankle_height = abs(nose[2] - left_ankle[2]) if use_world else abs(nose[1] - left_ankle[1])
            heights.append(ankle_height * 1.05)
            confidences.append(result.confidence[[0, 27]].mean() * 0.9)
        if right_ankle is not None:
            ankle_height = abs(nose[2] - right_ankle[2]) if use_world else abs(nose[1] - right_ankle[1])
            heights.append(ankle_height * 1.05)
            confidences.append(result.confidence[[0, 28]].mean() * 0.9)

        if not heights:
            return None, 0.0

        # Weighted average based on confidence
        confidences = np.array(confidences)
        heights = np.array(heights)

        weighted_height = np.average(heights, weights=confidences)
        avg_confidence = float(confidences.mean())

        return float(weighted_height), avg_confidence

    def extract_shoulder_width(self, result: LandmarkResult) -> Tuple[Optional[float], float]:
        """
        Extract shoulder width from landmarks.

        Args:
            result: LandmarkResult object

        Returns:
            Tuple of (shoulder width in meters, confidence score)
        """
        use_world = self.use_world_landmarks and result.world_landmarks is not None

        left_shoulder = self._get_landmark_coords(result, 11, use_world)
        right_shoulder = self._get_landmark_coords(result, 12, use_world)

        if left_shoulder is None or right_shoulder is None:
            return None, 0.0

        width = self._euclidean_distance(left_shoulder, right_shoulder)
        confidence = float(result.confidence[[11, 12]].mean())

        return width, confidence

    def extract_waist_circumference(self, result: LandmarkResult) -> Tuple[Optional[float], float]:
        """
        Estimate waist circumference from hip landmarks.

        Note: This is an approximation based on the distance between hips
        and anthropometric ratios. Actual circumference measurement would
        require body segmentation or multiple views.

        Args:
            result: LandmarkResult object

        Returns:
            Tuple of (waist circumference in meters, confidence score)
        """
        use_world = self.use_world_landmarks and result.world_landmarks is not None

        left_hip = self._get_landmark_coords(result, 23, use_world)
        right_hip = self._get_landmark_coords(result, 24, use_world)

        if left_hip is None or right_hip is None:
            return None, 0.0

        hip_width = self._euclidean_distance(left_hip, right_hip)

        # Estimate circumference using anthropometric ratio
        # Waist is typically narrower than hips (0.85-0.95 ratio)
        waist_width = hip_width * 0.9
        circumference = waist_width * self.CIRCUMFERENCE_RATIOS['waist']

        confidence = float(result.confidence[[23, 24]].mean() * 0.7)  # Lower confidence for estimation

        return circumference, confidence

    def extract_hip_circumference(self, result: LandmarkResult) -> Tuple[Optional[float], float]:
        """
        Estimate hip circumference from hip landmarks.

        Args:
            result: LandmarkResult object

        Returns:
            Tuple of (hip circumference in meters, confidence score)
        """
        use_world = self.use_world_landmarks and result.world_landmarks is not None

        left_hip = self._get_landmark_coords(result, 23, use_world)
        right_hip = self._get_landmark_coords(result, 24, use_world)

        if left_hip is None or right_hip is None:
            return None, 0.0

        hip_width = self._euclidean_distance(left_hip, right_hip)
        circumference = hip_width * self.CIRCUMFERENCE_RATIOS['hip']

        confidence = float(result.confidence[[23, 24]].mean() * 0.7)

        return circumference, confidence

    def extract_chest_circumference(self, result: LandmarkResult) -> Tuple[Optional[float], float]:
        """
        Estimate chest circumference from shoulder landmarks.

        Args:
            result: LandmarkResult object

        Returns:
            Tuple of (chest circumference in meters, confidence score)
        """
        use_world = self.use_world_landmarks and result.world_landmarks is not None

        left_shoulder = self._get_landmark_coords(result, 11, use_world)
        right_shoulder = self._get_landmark_coords(result, 12, use_world)

        if left_shoulder is None or right_shoulder is None:
            return None, 0.0

        shoulder_width = self._euclidean_distance(left_shoulder, right_shoulder)
        circumference = shoulder_width * self.CIRCUMFERENCE_RATIOS['chest']

        confidence = float(result.confidence[[11, 12]].mean() * 0.7)

        return circumference, confidence

    def extract_arm_length(
        self,
        result: LandmarkResult,
        side: str = 'left'
    ) -> Tuple[Optional[float], float]:
        """
        Extract arm length (shoulder to wrist).

        Args:
            result: LandmarkResult object
            side: 'left' or 'right'

        Returns:
            Tuple of (arm length in meters, confidence score)
        """
        use_world = self.use_world_landmarks and result.world_landmarks is not None

        if side == 'left':
            shoulder_idx, elbow_idx, wrist_idx = 11, 13, 15
        else:
            shoulder_idx, elbow_idx, wrist_idx = 12, 14, 16

        shoulder = self._get_landmark_coords(result, shoulder_idx, use_world)
        elbow = self._get_landmark_coords(result, elbow_idx, use_world)
        wrist = self._get_landmark_coords(result, wrist_idx, use_world)

        if shoulder is None or elbow is None or wrist is None:
            return None, 0.0

        upper_arm = self._euclidean_distance(shoulder, elbow)
        forearm = self._euclidean_distance(elbow, wrist)
        total_length = upper_arm + forearm

        confidence = float(result.confidence[[shoulder_idx, elbow_idx, wrist_idx]].mean())

        return total_length, confidence

    def extract_leg_length(
        self,
        result: LandmarkResult,
        side: str = 'left'
    ) -> Tuple[Optional[float], float]:
        """
        Extract leg length (hip to ankle).

        Args:
            result: LandmarkResult object
            side: 'left' or 'right'

        Returns:
            Tuple of (leg length in meters, confidence score)
        """
        use_world = self.use_world_landmarks and result.world_landmarks is not None

        if side == 'left':
            hip_idx, knee_idx, ankle_idx = 23, 25, 27
        else:
            hip_idx, knee_idx, ankle_idx = 24, 26, 28

        hip = self._get_landmark_coords(result, hip_idx, use_world)
        knee = self._get_landmark_coords(result, knee_idx, use_world)
        ankle = self._get_landmark_coords(result, ankle_idx, use_world)

        if hip is None or knee is None or ankle is None:
            return None, 0.0

        thigh = self._euclidean_distance(hip, knee)
        shin = self._euclidean_distance(knee, ankle)
        total_length = thigh + shin

        confidence = float(result.confidence[[hip_idx, knee_idx, ankle_idx]].mean())

        return total_length, confidence

    def extract_torso_length(self, result: LandmarkResult) -> Tuple[Optional[float], float]:
        """
        Extract torso length (average of shoulders to hips).

        Args:
            result: LandmarkResult object

        Returns:
            Tuple of (torso length in meters, confidence score)
        """
        use_world = self.use_world_landmarks and result.world_landmarks is not None

        left_shoulder = self._get_landmark_coords(result, 11, use_world)
        right_shoulder = self._get_landmark_coords(result, 12, use_world)
        left_hip = self._get_landmark_coords(result, 23, use_world)
        right_hip = self._get_landmark_coords(result, 24, use_world)

        lengths = []
        confidences = []

        if left_shoulder is not None and left_hip is not None:
            lengths.append(self._euclidean_distance(left_shoulder, left_hip))
            confidences.append(result.confidence[[11, 23]].mean())

        if right_shoulder is not None and right_hip is not None:
            lengths.append(self._euclidean_distance(right_shoulder, right_hip))
            confidences.append(result.confidence[[12, 24]].mean())

        if not lengths:
            return None, 0.0

        avg_length = float(np.mean(lengths))
        avg_confidence = float(np.mean(confidences))

        return avg_length, avg_confidence

    def extract_all(self, result: LandmarkResult) -> BodyMeasurements:
        """
        Extract all available body measurements.

        Args:
            result: LandmarkResult object

        Returns:
            BodyMeasurements object with all extracted measurements
        """
        measurements = BodyMeasurements()
        confidence_scores = {}

        # Extract each measurement
        height, conf = self.extract_height(result)
        measurements.height = height
        confidence_scores['height'] = conf

        shoulder_width, conf = self.extract_shoulder_width(result)
        measurements.shoulder_width = shoulder_width
        confidence_scores['shoulder_width'] = conf

        waist, conf = self.extract_waist_circumference(result)
        measurements.waist_circumference = waist
        confidence_scores['waist_circumference'] = conf

        hip, conf = self.extract_hip_circumference(result)
        measurements.hip_circumference = hip
        confidence_scores['hip_circumference'] = conf

        chest, conf = self.extract_chest_circumference(result)
        measurements.chest_circumference = chest
        confidence_scores['chest_circumference'] = conf

        # Arm lengths
        left_arm, conf = self.extract_arm_length(result, 'left')
        measurements.left_arm_length = left_arm
        confidence_scores['left_arm_length'] = conf

        right_arm, conf = self.extract_arm_length(result, 'right')
        measurements.right_arm_length = right_arm
        confidence_scores['right_arm_length'] = conf

        # Leg lengths
        left_leg, conf = self.extract_leg_length(result, 'left')
        measurements.left_leg_length = left_leg
        confidence_scores['left_leg_length'] = conf

        right_leg, conf = self.extract_leg_length(result, 'right')
        measurements.right_leg_length = right_leg
        confidence_scores['right_leg_length'] = conf

        # Torso length
        torso, conf = self.extract_torso_length(result)
        measurements.torso_length = torso
        confidence_scores['torso_length'] = conf

        # Calculate overall confidence
        valid_confidences = [c for c in confidence_scores.values() if c > 0]
        measurements.overall_confidence = (
            float(np.mean(valid_confidences)) if valid_confidences else 0.0
        )
        measurements.confidence_scores = confidence_scores

        return measurements

    def to_dict(self, measurements: BodyMeasurements) -> Dict[str, any]:
        """
        Convert measurements to dictionary format.

        Args:
            measurements: BodyMeasurements object

        Returns:
            Dictionary with all measurements and confidence scores
        """
        return {
            'measurements': {
                'height': measurements.height,
                'shoulder_width': measurements.shoulder_width,
                'waist_circumference': measurements.waist_circumference,
                'hip_circumference': measurements.hip_circumference,
                'chest_circumference': measurements.chest_circumference,
                'left_arm_length': measurements.left_arm_length,
                'right_arm_length': measurements.right_arm_length,
                'left_leg_length': measurements.left_leg_length,
                'right_leg_length': measurements.right_leg_length,
                'torso_length': measurements.torso_length
            },
            'confidence_scores': measurements.confidence_scores,
            'overall_confidence': measurements.overall_confidence
        }
