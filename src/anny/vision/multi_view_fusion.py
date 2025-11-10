# Anny - Vision Module
# Copyright (C) 2025 NAVER Corp.
# Apache License, Version 2.0

import numpy as np
from typing import List, Optional, Dict
from dataclasses import dataclass
from .landmark_detector import LandmarkResult
from .measurement_extractor import BodyMeasurements, MeasurementExtractor


@dataclass
class FusedMeasurements:
    """Container for fused measurements from multiple views."""
    measurements: BodyMeasurements
    num_views: int
    view_confidences: List[float]
    fusion_method: str
    measurement_variance: Dict[str, float]  # Variance across views for each measurement


class MultiViewFusion:
    """
    Fuses measurements from multiple camera views/images for improved accuracy.

    Supports multiple fusion strategies:
    - Weighted average by confidence
    - Median filtering (robust to outliers)
    - Maximum confidence selection
    - Kalman filtering (for temporal sequences)

    Handles missing measurements gracefully and provides variance estimates.
    """

    def __init__(
        self,
        fusion_method: str = 'weighted_average',
        outlier_rejection: bool = True,
        outlier_threshold: float = 2.0,  # Standard deviations
        min_views: int = 1,
        device: str = 'cpu'
    ):
        """
        Initialize multi-view fusion.

        Args:
            fusion_method: Method for combining measurements
                - 'weighted_average': Confidence-weighted average
                - 'median': Median of measurements (robust to outliers)
                - 'max_confidence': Select measurement with highest confidence
                - 'adaptive': Adaptive selection based on variance
            outlier_rejection: If True, rejects outlier measurements before fusion
            outlier_threshold: Threshold in standard deviations for outlier rejection
            min_views: Minimum number of views required for fusion
            device: Device for computations
        """
        valid_methods = ['weighted_average', 'median', 'max_confidence', 'adaptive']
        if fusion_method not in valid_methods:
            raise ValueError(
                f"Invalid fusion method: {fusion_method}. "
                f"Valid methods: {', '.join(valid_methods)}"
            )

        self.fusion_method = fusion_method
        self.outlier_rejection = outlier_rejection
        self.outlier_threshold = outlier_threshold
        self.min_views = min_views
        self.device = device
        self.extractor = MeasurementExtractor(device=device)

    def _reject_outliers(
        self,
        values: np.ndarray,
        confidences: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Reject outlier measurements using statistical methods.

        Args:
            values: Array of measurement values
            confidences: Corresponding confidence scores

        Returns:
            Tuple of (filtered_values, filtered_confidences)
        """
        if len(values) < 3:  # Need at least 3 points for outlier detection
            return values, confidences

        # Remove None/NaN values
        valid_mask = ~np.isnan(values)
        if valid_mask.sum() < 3:
            return values, confidences

        valid_values = values[valid_mask]
        valid_confidences = confidences[valid_mask]

        # Calculate statistics
        median = np.median(valid_values)
        mad = np.median(np.abs(valid_values - median))  # Median Absolute Deviation

        # Modified Z-score (more robust than standard deviation)
        if mad > 0:
            modified_z_scores = 0.6745 * (valid_values - median) / mad
            outlier_mask = np.abs(modified_z_scores) <= self.outlier_threshold
        else:
            outlier_mask = np.ones(len(valid_values), dtype=bool)

        # Create output arrays
        filtered_values = values.copy()
        filtered_confidences = confidences.copy()

        # Set outliers to NaN
        valid_indices = np.where(valid_mask)[0]
        outlier_indices = valid_indices[~outlier_mask]
        filtered_values[outlier_indices] = np.nan
        filtered_confidences[outlier_indices] = 0.0

        return filtered_values, filtered_confidences

    def _weighted_average(
        self,
        values: np.ndarray,
        confidences: np.ndarray
    ) -> tuple[Optional[float], float, float]:
        """
        Compute confidence-weighted average.

        Args:
            values: Measurement values
            confidences: Confidence scores

        Returns:
            Tuple of (fused_value, average_confidence, variance)
        """
        # Filter out invalid values
        valid_mask = ~np.isnan(values) & (confidences > 0)

        if valid_mask.sum() == 0:
            return None, 0.0, 0.0

        valid_values = values[valid_mask]
        valid_confidences = confidences[valid_mask]

        # Weighted average
        weights = valid_confidences / valid_confidences.sum()
        fused_value = np.average(valid_values, weights=weights)
        avg_confidence = valid_confidences.mean()

        # Weighted variance
        variance = np.average((valid_values - fused_value) ** 2, weights=weights)

        return float(fused_value), float(avg_confidence), float(variance)

    def _median_fusion(
        self,
        values: np.ndarray,
        confidences: np.ndarray
    ) -> tuple[Optional[float], float, float]:
        """
        Compute median (robust to outliers).

        Args:
            values: Measurement values
            confidences: Confidence scores

        Returns:
            Tuple of (median_value, average_confidence, variance)
        """
        valid_mask = ~np.isnan(values) & (confidences > 0)

        if valid_mask.sum() == 0:
            return None, 0.0, 0.0

        valid_values = values[valid_mask]
        valid_confidences = confidences[valid_mask]

        median_value = np.median(valid_values)
        avg_confidence = valid_confidences.mean()
        variance = np.var(valid_values)

        return float(median_value), float(avg_confidence), float(variance)

    def _max_confidence_fusion(
        self,
        values: np.ndarray,
        confidences: np.ndarray
    ) -> tuple[Optional[float], float, float]:
        """
        Select measurement with maximum confidence.

        Args:
            values: Measurement values
            confidences: Confidence scores

        Returns:
            Tuple of (best_value, max_confidence, variance)
        """
        valid_mask = ~np.isnan(values) & (confidences > 0)

        if valid_mask.sum() == 0:
            return None, 0.0, 0.0

        valid_values = values[valid_mask]
        valid_confidences = confidences[valid_mask]

        max_idx = np.argmax(valid_confidences)
        best_value = valid_values[max_idx]
        max_confidence = valid_confidences[max_idx]
        variance = np.var(valid_values)

        return float(best_value), float(max_confidence), float(variance)

    def _adaptive_fusion(
        self,
        values: np.ndarray,
        confidences: np.ndarray
    ) -> tuple[Optional[float], float, float]:
        """
        Adaptive fusion: uses median if high variance, weighted average otherwise.

        Args:
            values: Measurement values
            confidences: Confidence scores

        Returns:
            Tuple of (fused_value, confidence, variance)
        """
        valid_mask = ~np.isnan(values) & (confidences > 0)

        if valid_mask.sum() == 0:
            return None, 0.0, 0.0

        valid_values = values[valid_mask]

        # Calculate coefficient of variation
        mean_val = np.mean(valid_values)
        std_val = np.std(valid_values)
        cv = std_val / mean_val if mean_val > 0 else 0

        # Use median if high variance (CV > 0.2), weighted average otherwise
        if cv > 0.2:
            return self._median_fusion(values, confidences)
        else:
            return self._weighted_average(values, confidences)

    def _fuse_single_measurement(
        self,
        values: List[Optional[float]],
        confidences: List[float]
    ) -> tuple[Optional[float], float, float]:
        """
        Fuse a single measurement type across multiple views.

        Args:
            values: List of measurement values from different views
            confidences: Corresponding confidence scores

        Returns:
            Tuple of (fused_value, fused_confidence, variance)
        """
        # Convert to numpy arrays
        values_array = np.array([v if v is not None else np.nan for v in values])
        confidences_array = np.array(confidences)

        # Outlier rejection if enabled
        if self.outlier_rejection:
            values_array, confidences_array = self._reject_outliers(
                values_array, confidences_array
            )

        # Apply fusion method
        if self.fusion_method == 'weighted_average':
            return self._weighted_average(values_array, confidences_array)
        elif self.fusion_method == 'median':
            return self._median_fusion(values_array, confidences_array)
        elif self.fusion_method == 'max_confidence':
            return self._max_confidence_fusion(values_array, confidences_array)
        elif self.fusion_method == 'adaptive':
            return self._adaptive_fusion(values_array, confidences_array)
        else:
            raise ValueError(f"Unknown fusion method: {self.fusion_method}")

    def fuse_measurements(
        self,
        measurements_list: List[BodyMeasurements]
    ) -> FusedMeasurements:
        """
        Fuse measurements from multiple views.

        Args:
            measurements_list: List of BodyMeasurements from different views

        Returns:
            FusedMeasurements object

        Raises:
            ValueError: If insufficient views provided
        """
        if len(measurements_list) < self.min_views:
            raise ValueError(
                f"Insufficient views: got {len(measurements_list)}, "
                f"minimum required: {self.min_views}"
            )

        # Extract view confidences
        view_confidences = [m.overall_confidence for m in measurements_list]

        # Initialize fused measurements
        fused = BodyMeasurements()
        fused.confidence_scores = {}
        measurement_variance = {}

        # Measurement fields to fuse
        measurement_fields = [
            'height', 'shoulder_width', 'waist_circumference',
            'hip_circumference', 'chest_circumference',
            'left_arm_length', 'right_arm_length',
            'left_leg_length', 'right_leg_length', 'torso_length'
        ]

        # Fuse each measurement type
        for field in measurement_fields:
            values = [getattr(m, field) for m in measurements_list]
            confidences = [
                m.confidence_scores.get(field, 0.0) if m.confidence_scores else 0.0
                for m in measurements_list
            ]

            fused_value, fused_conf, variance = self._fuse_single_measurement(
                values, confidences
            )

            setattr(fused, field, fused_value)
            fused.confidence_scores[field] = fused_conf
            measurement_variance[field] = variance

        # Calculate overall fused confidence
        valid_confidences = [
            c for c in fused.confidence_scores.values() if c > 0
        ]
        fused.overall_confidence = (
            float(np.mean(valid_confidences)) if valid_confidences else 0.0
        )

        return FusedMeasurements(
            measurements=fused,
            num_views=len(measurements_list),
            view_confidences=view_confidences,
            fusion_method=self.fusion_method,
            measurement_variance=measurement_variance
        )

    def fuse_from_landmarks(
        self,
        landmark_results: List[LandmarkResult]
    ) -> FusedMeasurements:
        """
        Extract and fuse measurements from multiple landmark results.

        Args:
            landmark_results: List of LandmarkResult objects

        Returns:
            FusedMeasurements object
        """
        # Extract measurements from each view
        measurements_list = [
            self.extractor.extract_all(result)
            for result in landmark_results
        ]

        # Fuse measurements
        return self.fuse_measurements(measurements_list)

    def get_measurement_statistics(
        self,
        fused: FusedMeasurements
    ) -> Dict[str, Dict[str, float]]:
        """
        Get statistical summary of fused measurements.

        Args:
            fused: FusedMeasurements object

        Returns:
            Dictionary with statistics for each measurement
        """
        stats = {}

        for field, value in vars(fused.measurements).items():
            if field == 'confidence_scores' or value is None:
                continue

            variance = fused.measurement_variance.get(field, 0.0)
            confidence = fused.measurements.confidence_scores.get(field, 0.0)

            stats[field] = {
                'value': value,
                'confidence': confidence,
                'variance': variance,
                'std_dev': np.sqrt(variance),
                'cv': np.sqrt(variance) / value if value > 0 else 0.0  # Coefficient of variation
            }

        return stats
