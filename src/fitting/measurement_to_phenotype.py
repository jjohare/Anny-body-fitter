# Anny-body-fitter
# Copyright (C) 2025
# Map vision measurements to Anny phenotype parameters
import torch
import numpy as np
from typing import Dict, Any, Optional, Union


class MeasurementToPhenotype:
    """
    Map extracted vision measurements to Anny phenotype parameter space.

    Uses heuristic rules and statistical mappings to convert image-based
    measurements (body proportions, estimated attributes) into the continuous
    phenotype parameters used by Anny's parametric body model.

    Phenotype Parameters:
        - gender: 0.0 (male) to 1.0 (female)
        - age: 0.0 (newborn) to 1.0 (old)
        - muscle: 0.0 (min) to 1.0 (max)
        - weight: 0.0 (min) to 1.0 (max)
        - height: 0.0 (min) to 1.0 (max)
        - proportions: 0.0 (ideal) to 1.0 (uncommon)
    """

    # Heuristic mapping constants
    MIN_HEIGHT_M = 1.20  # Minimum adult height in meters
    MAX_HEIGHT_M = 2.20  # Maximum adult height in meters

    AGE_RANGES = {
        'newborn': (0, 1),
        'baby': (1, 3),
        'child': (3, 12),
        'young': (12, 40),
        'old': (40, 100)
    }

    def __init__(self, model: Any):
        """
        Initialize measurement to phenotype mapper.

        Args:
            model: Anny model instance with phenotype_labels
        """
        self.model = model
        self.phenotype_labels = model.phenotype_labels
        self.device = model.device

    def map_height(self, height_pixels: float, reference_height_meters: float) -> float:
        """
        Map pixel-based height to Anny height parameter.

        Args:
            height_pixels: Height in pixels from image
            reference_height_meters: Estimated real-world height

        Returns:
            Normalized height parameter (0.0 to 1.0)
        """
        # Clamp to reasonable human height range
        height_clamped = np.clip(
            reference_height_meters,
            self.MIN_HEIGHT_M,
            self.MAX_HEIGHT_M
        )

        # Normalize to 0-1 range
        normalized = (height_clamped - self.MIN_HEIGHT_M) / (
            self.MAX_HEIGHT_M - self.MIN_HEIGHT_M
        )

        return float(normalized)

    def map_gender(self, gender: str, confidence: float = 1.0) -> float:
        """
        Map estimated gender to Anny gender parameter.

        Args:
            gender: 'male' or 'female'
            confidence: Confidence of gender estimation (0.0 to 1.0)

        Returns:
            Gender parameter: 0.0 (male) to 1.0 (female)
        """
        base_value = 0.0 if gender.lower() == 'male' else 1.0

        # With low confidence, move toward neutral (0.5)
        if confidence < 1.0:
            neutral_weight = 1.0 - confidence
            base_value = base_value * confidence + 0.5 * neutral_weight

        return float(base_value)

    def map_age(self, age_years: float) -> float:
        """
        Map estimated age in years to Anny age parameter.

        Args:
            age_years: Estimated age in years

        Returns:
            Age parameter (0.0 to 1.0)
        """
        # Anny age mapping: -1/3 (newborn) to 1.0 (old)
        # We normalize to 0-1 for input
        if age_years < 1:
            return 0.0  # Newborn
        elif age_years < 3:
            return 0.2  # Baby
        elif age_years < 12:
            return 0.4  # Child
        elif age_years < 40:
            # Young adult range - linear interpolation
            return 0.4 + 0.3 * (age_years - 12) / (40 - 12)
        else:
            # Old range - linear interpolation
            return 0.7 + 0.3 * min((age_years - 40) / 60, 1.0)

    def map_proportions(
        self,
        shoulder_ratio: Optional[float] = None,
        hip_ratio: Optional[float] = None,
        leg_ratio: Optional[float] = None,
        torso_ratio: Optional[float] = None
    ) -> float:
        """
        Map body proportions to Anny proportions parameter.

        Args:
            shoulder_ratio: Shoulder width / height
            hip_ratio: Hip width / height
            leg_ratio: Leg length / height
            torso_ratio: Torso length / height

        Returns:
            Proportions parameter: 0.0 (ideal) to 1.0 (uncommon)
        """
        # Ideal proportion values (approximate)
        ideal_shoulder = 0.28
        ideal_hip = 0.20
        ideal_leg = 0.52
        ideal_torso = 0.48

        deviations = []

        if shoulder_ratio is not None:
            deviations.append(abs(shoulder_ratio - ideal_shoulder) / ideal_shoulder)
        if hip_ratio is not None:
            deviations.append(abs(hip_ratio - ideal_hip) / ideal_hip)
        if leg_ratio is not None:
            deviations.append(abs(leg_ratio - ideal_leg) / ideal_leg)
        if torso_ratio is not None:
            deviations.append(abs(torso_ratio - ideal_torso) / ideal_torso)

        if not deviations:
            return 0.5  # Default middle value

        # Average deviation, scaled to 0-1
        avg_deviation = np.mean(deviations)
        proportions = np.clip(avg_deviation * 2.0, 0.0, 1.0)

        return float(proportions)

    def map_body_composition(
        self,
        composition: Dict[str, float]
    ) -> tuple[float, float]:
        """
        Map body composition indicators to muscle and weight parameters.

        Args:
            composition: Dict with 'muscle_indicator' and 'weight_indicator'

        Returns:
            Tuple of (muscle, weight) parameters
        """
        muscle = composition.get('muscle_indicator', 0.5)
        weight = composition.get('weight_indicator', 0.5)

        # Ensure valid range
        muscle = np.clip(muscle, 0.0, 1.0)
        weight = np.clip(weight, 0.0, 1.0)

        return float(muscle), float(weight)

    def map_measurements(
        self,
        measurements: Dict[str, Any],
        default_confidence: float = 0.5
    ) -> Dict[str, float]:
        """
        Map complete measurement set to phenotype parameters.

        Args:
            measurements: Dict containing vision measurements
            default_confidence: Default confidence for missing values

        Returns:
            Dict of phenotype parameters with confidence
        """
        result = {}
        confidence = measurements.get('confidence', default_confidence)

        # Height mapping
        if 'height_pixels' in measurements and 'reference_height_meters' in measurements:
            result['height'] = self.map_height(
                measurements['height_pixels'],
                measurements['reference_height_meters']
            )
        else:
            result['height'] = 0.5  # Default middle height

        # Gender mapping
        if 'estimated_gender' in measurements:
            result['gender'] = self.map_gender(
                measurements['estimated_gender'],
                confidence
            )
        else:
            result['gender'] = 0.5  # Default neutral

        # Age mapping
        if 'estimated_age' in measurements:
            result['age'] = self.map_age(measurements['estimated_age'])
        else:
            result['age'] = 0.5  # Default middle age

        # Proportions mapping
        proportions = self.map_proportions(
            shoulder_ratio=measurements.get('shoulder_width_ratio'),
            hip_ratio=measurements.get('hip_width_ratio'),
            leg_ratio=measurements.get('leg_length_ratio'),
            torso_ratio=measurements.get('torso_length_ratio')
        )
        result['proportions'] = proportions

        # Body composition mapping
        if 'body_composition' in measurements:
            muscle, weight = self.map_body_composition(
                measurements['body_composition']
            )
            result['muscle'] = muscle
            result['weight'] = weight
        else:
            result['muscle'] = 0.5
            result['weight'] = 0.5

        # Add confidence to result
        result['confidence'] = confidence

        return result

    def to_tensor(
        self,
        phenotype_dict: Dict[str, float],
        batch_size: int = 1
    ) -> Dict[str, torch.Tensor]:
        """
        Convert phenotype dict to tensor format for Anny model.

        Args:
            phenotype_dict: Dict of phenotype parameters
            batch_size: Batch size for tensors

        Returns:
            Dict of phenotype tensors
        """
        result = {}

        for label in self.phenotype_labels:
            if label in phenotype_dict:
                value = phenotype_dict[label]
            else:
                value = 0.5  # Default middle value

            result[label] = torch.full(
                (batch_size,),
                float(value),
                dtype=torch.float32,
                device=self.device
            )

        return result
