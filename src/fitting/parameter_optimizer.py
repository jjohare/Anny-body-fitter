# Anny-body-fitter
# Copyright (C) 2025
# Parameter optimization using Anny's ParametersRegressor
import torch
from typing import Dict, Any, Optional, List, Tuple
from src.anny.parameters_regressor import ParametersRegressor


class ParameterOptimizer:
    """
    Optimize Anny phenotype parameters using ParametersRegressor.

    This wrapper provides a convenient interface to Anny's iterative
    fitting algorithm, with support for:
    - Initial phenotype estimates from vision measurements
    - Confidence-based parameter exclusion
    - Multi-stage optimization strategies
    """

    def __init__(
        self,
        regressor: ParametersRegressor,
        confidence_threshold: float = 0.5
    ):
        """
        Initialize parameter optimizer.

        Args:
            regressor: ParametersRegressor instance
            confidence_threshold: Minimum confidence to include parameter in optimization
        """
        self.regressor = regressor
        self.confidence_threshold = confidence_threshold

    def optimize(
        self,
        target_vertices: torch.Tensor,
        initial_phenotypes: Optional[Dict[str, float]] = None,
        confidences: Optional[Dict[str, float]] = None,
        optimize_phenotypes: bool = True,
        max_iterations: int = 5
    ) -> Dict[str, Any]:
        """
        Optimize phenotype parameters to fit target vertices.

        Args:
            target_vertices: Target mesh vertices [B, V, 3]
            initial_phenotypes: Initial phenotype parameter estimates
            confidences: Confidence for each phenotype parameter
            optimize_phenotypes: Whether to optimize phenotypes
            max_iterations: Maximum optimization iterations

        Returns:
            Dict containing:
                - pose_parameters: Optimized pose
                - phenotype_kwargs: Optimized phenotypes
                - vertices: Fitted vertices
        """
        # Determine which phenotypes to exclude based on confidence
        excluded_phenotypes = []
        if confidences is not None:
            excluded_phenotypes = [
                param for param, conf in confidences.items()
                if conf < self.confidence_threshold
            ]

        # Run optimization
        pose_parameters, phenotype_kwargs, vertices = self.regressor(
            vertices_target=target_vertices,
            initial_phenotype_kwargs=initial_phenotypes,
            optimize_phenotypes=optimize_phenotypes,
            excluded_phenotypes=excluded_phenotypes,
            max_n_iters=max_iterations
        )

        return {
            'pose_parameters': pose_parameters,
            'phenotype_kwargs': phenotype_kwargs,
            'vertices': vertices
        }

    def optimize_with_age_search(
        self,
        target_vertices: torch.Tensor,
        initial_phenotypes: Optional[Dict[str, float]] = None,
        age_anchors: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Optimize with age anchor search strategy.

        This strategy searches over multiple age anchors to find the best
        initial age estimate before fine-tuning other parameters.

        Args:
            target_vertices: Target mesh vertices [B, V, 3]
            initial_phenotypes: Initial phenotype estimates
            age_anchors: Age values to search (default: [0.0, 0.33, 0.67, 1.0])

        Returns:
            Dict containing optimized parameters
        """
        if age_anchors is None:
            age_anchors = [0.0, 0.33, 0.67, 1.0]

        pose_parameters, phenotype_kwargs, vertices = self.regressor.fit_with_age_anchor_search(
            vertices_target=target_vertices,
            age_anchors=age_anchors,
            initial_phenotype_kwargs=initial_phenotypes
        )

        return {
            'pose_parameters': pose_parameters,
            'phenotype_kwargs': phenotype_kwargs,
            'vertices': vertices
        }

    def optimize_staged(
        self,
        target_vertices: torch.Tensor,
        initial_phenotypes: Optional[Dict[str, float]] = None,
        confidences: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Multi-stage optimization strategy.

        Stage 1: Optimize only high-confidence parameters
        Stage 2: Refine with all parameters

        Args:
            target_vertices: Target mesh vertices [B, V, 3]
            initial_phenotypes: Initial phenotype estimates
            confidences: Confidence for each parameter

        Returns:
            Dict containing final optimized parameters
        """
        # Stage 1: High confidence parameters only
        stage1_result = self.optimize(
            target_vertices=target_vertices,
            initial_phenotypes=initial_phenotypes,
            confidences=confidences,
            optimize_phenotypes=True,
            max_iterations=3
        )

        # Stage 2: Refine all parameters
        stage2_result = self.optimize(
            target_vertices=target_vertices,
            initial_phenotypes=stage1_result['phenotype_kwargs'],
            confidences=None,  # Include all parameters
            optimize_phenotypes=True,
            max_iterations=5
        )

        return stage2_result

    def get_fitting_error(
        self,
        predicted_vertices: torch.Tensor,
        target_vertices: torch.Tensor
    ) -> Dict[str, float]:
        """
        Compute fitting error metrics.

        Args:
            predicted_vertices: Fitted vertices [B, V, 3]
            target_vertices: Target vertices [B, V, 3]

        Returns:
            Dict of error metrics
        """
        # Per-vertex error (PVE) in mm
        pve = 1000.0 * torch.norm(
            predicted_vertices - target_vertices,
            dim=-1
        ).mean()

        # Maximum error
        max_error = 1000.0 * torch.norm(
            predicted_vertices - target_vertices,
            dim=-1
        ).max()

        # RMS error
        rms_error = 1000.0 * torch.sqrt(
            ((predicted_vertices - target_vertices) ** 2).mean()
        )

        return {
            'pve_mm': pve.item(),
            'max_error_mm': max_error.item(),
            'rms_error_mm': rms_error.item()
        }
