# Anny-body-fitter
# Copyright (C) 2025
# Multi-image confidence weighting and fusion
import numpy as np
from typing import Dict, Any, List, Optional
from scipy import stats


class ConfidenceWeighting:
    """
    Fuse measurements from multiple images using confidence weighting.

    Implements several fusion strategies:
    - Weighted average based on confidence scores
    - Outlier rejection using statistical methods
    - Uncertainty propagation for final estimates
    """

    def __init__(self, outlier_threshold: float = 2.0):
        """
        Initialize confidence weighting module.

        Args:
            outlier_threshold: Z-score threshold for outlier rejection
        """
        self.outlier_threshold = outlier_threshold

    def weighted_average(
        self,
        measurements: List[Dict[str, float]],
        key: str,
        outlier_rejection: bool = True
    ) -> float:
        """
        Compute weighted average of measurements.

        Args:
            measurements: List of measurement dicts with 'value' and 'confidence'
            key: Key to extract from measurements
            outlier_rejection: Whether to reject outliers

        Returns:
            Weighted average value
        """
        if not measurements:
            return 0.5  # Default value

        values = np.array([m[key] for m in measurements])
        confidences = np.array([m.get('confidence', 1.0) for m in measurements])

        if outlier_rejection and len(values) > 2:
            # Compute z-scores
            z_scores = np.abs(stats.zscore(values))

            # Filter outliers
            mask = z_scores < self.outlier_threshold
            if mask.sum() > 0:  # Ensure we keep some values
                values = values[mask]
                confidences = confidences[mask]

        # Weighted average
        if confidences.sum() > 0:
            weighted_avg = np.average(values, weights=confidences)
        else:
            weighted_avg = np.mean(values)

        return float(weighted_avg)

    def fuse_measurements(
        self,
        multi_measurements: List[Dict[str, Any]],
        return_uncertainty: bool = False
    ) -> Dict[str, Any]:
        """
        Fuse measurements from multiple images.

        Args:
            multi_measurements: List of measurement dicts, each containing:
                - phenotypes: Dict of phenotype parameters
                - confidence: Overall confidence score
            return_uncertainty: Whether to return uncertainty estimates

        Returns:
            Fused measurement dict with aggregated phenotypes and confidence
        """
        if not multi_measurements:
            return {
                'phenotypes': {},
                'confidence': 0.0
            }

        # Extract all phenotype keys
        all_keys = set()
        for m in multi_measurements:
            all_keys.update(m['phenotypes'].keys())

        # Fuse each phenotype parameter
        fused_phenotypes = {}
        uncertainties = {}

        for key in all_keys:
            # Collect measurements for this parameter
            param_measurements = []
            for m in multi_measurements:
                if key in m['phenotypes']:
                    param_measurements.append({
                        'value': m['phenotypes'][key],
                        'confidence': m.get('confidence', 1.0)
                    })

            if param_measurements:
                fused_phenotypes[key] = self.weighted_average(
                    param_measurements,
                    key='value',
                    outlier_rejection=True
                )

                if return_uncertainty:
                    # Estimate uncertainty as weighted std dev
                    values = np.array([m['value'] for m in param_measurements])
                    confidences = np.array([m['confidence'] for m in param_measurements])

                    weighted_std = np.sqrt(
                        np.average(
                            (values - fused_phenotypes[key]) ** 2,
                            weights=confidences
                        )
                    )

                    # Uncertainty decreases with more measurements
                    uncertainties[key] = weighted_std / np.sqrt(len(param_measurements))

        # Aggregate confidence
        # Use harmonic mean weighted by number of measurements
        confidences = [m['confidence'] for m in multi_measurements]

        # Higher confidence with more measurements
        n = len(multi_measurements)
        base_confidence = stats.hmean(confidences) if confidences else 0.0

        # Boost confidence with multiple measurements (diminishing returns)
        confidence_boost = 1.0 + 0.15 * np.log1p(n - 1)
        aggregated_confidence = min(base_confidence * confidence_boost, 1.0)

        result = {
            'phenotypes': fused_phenotypes,
            'confidence': float(aggregated_confidence)
        }

        if return_uncertainty:
            result['uncertainty'] = uncertainties

        return result

    def compute_agreement(
        self,
        multi_measurements: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Compute inter-measurement agreement for each parameter.

        Higher agreement indicates more reliable measurements.

        Args:
            multi_measurements: List of measurement dicts

        Returns:
            Dict of agreement scores (0.0 to 1.0) for each parameter
        """
        if len(multi_measurements) < 2:
            return {}

        agreement_scores = {}

        # Extract all phenotype keys
        all_keys = set()
        for m in multi_measurements:
            all_keys.update(m['phenotypes'].keys())

        for key in all_keys:
            values = []
            for m in multi_measurements:
                if key in m['phenotypes']:
                    values.append(m['phenotypes'][key])

            if len(values) >= 2:
                # Use coefficient of variation (inverse)
                # Lower variation = higher agreement
                std = np.std(values)
                mean = np.mean(values)

                if mean > 0:
                    cv = std / mean
                    # Convert to agreement score (0 to 1)
                    agreement = np.exp(-2 * cv)
                else:
                    agreement = 1.0 - std  # If mean is 0, use 1-std

                agreement_scores[key] = float(np.clip(agreement, 0.0, 1.0))

        return agreement_scores

    def select_best_measurements(
        self,
        multi_measurements: List[Dict[str, Any]],
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Select the top-k most confident measurements.

        Args:
            multi_measurements: List of measurement dicts
            top_k: Number of measurements to select

        Returns:
            List of top-k measurements sorted by confidence
        """
        # Sort by confidence
        sorted_measurements = sorted(
            multi_measurements,
            key=lambda m: m.get('confidence', 0.0),
            reverse=True
        )

        return sorted_measurements[:top_k]
