# Anny Body Fitter - Test Data Fixtures
# Copyright (C) 2025 NAVER Corp.
# Apache License, Version 2.0
"""
Comprehensive test data fixtures for Anny Body Fitter testing.

Provides synthetic test data including measurements, phenotype parameters,
and expected fitting results.
"""
import torch
import numpy as np
from typing import Dict, Tuple, List
from pathlib import Path


# Realistic anthropometric measurements (adult humans)
SAMPLE_MEASUREMENTS = {
    'average_male': {
        'height': 1.75,  # meters
        'waist_circumference': 0.85,  # meters
        'chest_circumference': 1.00,  # meters
        'hip_circumference': 0.95,  # meters
        'weight': 75.0,  # kg
        'bmi': 24.5,  # kg/m²
        'volume': 0.075,  # m³
    },
    'average_female': {
        'height': 1.65,
        'waist_circumference': 0.70,
        'chest_circumference': 0.90,
        'hip_circumference': 0.95,
        'weight': 62.0,
        'bmi': 22.8,
        'volume': 0.062,
    },
    'tall_male': {
        'height': 1.90,
        'waist_circumference': 0.90,
        'chest_circumference': 1.10,
        'hip_circumference': 1.00,
        'weight': 90.0,
        'bmi': 24.9,
        'volume': 0.092,
    },
    'petite_female': {
        'height': 1.55,
        'waist_circumference': 0.65,
        'chest_circumference': 0.80,
        'hip_circumference': 0.88,
        'weight': 50.0,
        'bmi': 20.8,
        'volume': 0.051,
    },
    'athletic_male': {
        'height': 1.80,
        'waist_circumference': 0.78,
        'chest_circumference': 1.08,
        'hip_circumference': 0.95,
        'weight': 80.0,
        'bmi': 24.7,
        'volume': 0.082,
    },
}


# Sample phenotype parameters (normalized to [0, 1])
SAMPLE_PHENOTYPES = {
    'average_male': {
        'gender': 1.0,  # Male
        'age': 0.45,  # ~30 years
        'muscle': 0.5,  # Average muscle
        'weight': 0.5,  # Average weight
        'height': 0.55,  # Slightly above average
        'proportions': 0.5,  # Average proportions
        'cupsize': 0.0,  # Male (not applicable)
        'firmness': 0.5,  # Average
        'african': 0.0,
        'asian': 0.0,
        'caucasian': 1.0,
    },
    'average_female': {
        'gender': 0.0,  # Female
        'age': 0.42,  # ~28 years
        'muscle': 0.4,  # Less muscle than average male
        'weight': 0.45,  # Slightly below average
        'height': 0.45,  # Slightly below average
        'proportions': 0.5,
        'cupsize': 0.5,  # B/C cup
        'firmness': 0.6,  # Above average
        'african': 0.0,
        'asian': 0.0,
        'caucasian': 1.0,
    },
    'athletic_male': {
        'gender': 1.0,
        'age': 0.38,  # ~25 years
        'muscle': 0.75,  # High muscle
        'weight': 0.52,
        'height': 0.58,
        'proportions': 0.55,  # Athletic proportions
        'cupsize': 0.0,
        'firmness': 0.7,
        'african': 0.0,
        'asian': 0.0,
        'caucasian': 1.0,
    },
    'diverse_female': {
        'gender': 0.0,
        'age': 0.35,  # ~23 years
        'muscle': 0.45,
        'weight': 0.48,
        'height': 0.50,
        'proportions': 0.52,
        'cupsize': 0.6,  # C/D cup
        'firmness': 0.55,
        'african': 0.3,
        'asian': 0.4,
        'caucasian': 0.3,
    },
}


# Expected fitting results (for regression testing)
EXPECTED_FITTING_RESULTS = {
    'average_male': {
        'convergence_iterations': 3,
        'final_error_threshold': 0.05,  # meters
        'phenotype_accuracy': 0.95,  # 95% match to target
        'pose_stability': True,  # No unstable joints
    },
    'average_female': {
        'convergence_iterations': 3,
        'final_error_threshold': 0.05,
        'phenotype_accuracy': 0.94,
        'pose_stability': True,
    },
}


# Vertex generation helpers
def generate_humanoid_vertices(
    height: float = 1.75,
    width_factor: float = 0.3,
    depth_factor: float = 0.2,
    n_vertices: int = 1000,
    device: torch.device = torch.device('cpu'),
    dtype: torch.dtype = torch.float32
) -> torch.Tensor:
    """
    Generate synthetic humanoid vertex cloud.

    Args:
        height: Total height in meters
        width_factor: Width as fraction of height
        depth_factor: Depth as fraction of height
        n_vertices: Number of vertices to generate
        device: Torch device
        dtype: Torch dtype

    Returns:
        Vertices tensor (n_vertices, 3)
    """
    vertices = []

    # Torso (40% of vertices)
    n_torso = int(n_vertices * 0.4)
    torso_height = height * 0.5
    for _ in range(n_torso):
        x = np.random.uniform(-width_factor * 0.3, width_factor * 0.3)
        y = np.random.uniform(-depth_factor * 0.3, depth_factor * 0.3)
        z = np.random.uniform(height * 0.3, height * 0.3 + torso_height)
        vertices.append([x, y, z])

    # Head (10% of vertices)
    n_head = int(n_vertices * 0.1)
    head_center = height * 0.85
    for _ in range(n_head):
        # Spherical distribution
        theta = np.random.uniform(0, 2 * np.pi)
        phi = np.random.uniform(0, np.pi)
        r = np.random.uniform(0, 0.12)  # Head radius ~12cm
        x = r * np.sin(phi) * np.cos(theta)
        y = r * np.sin(phi) * np.sin(theta)
        z = head_center + r * np.cos(phi)
        vertices.append([x, y, z])

    # Arms (20% of vertices)
    n_arms = int(n_vertices * 0.2)
    for _ in range(n_arms):
        # Random arm position
        side = np.random.choice([-1, 1])
        x = side * np.random.uniform(width_factor * 0.2, width_factor * 0.5)
        y = np.random.uniform(-depth_factor * 0.1, depth_factor * 0.1)
        z = np.random.uniform(height * 0.3, height * 0.75)
        vertices.append([x, y, z])

    # Legs (30% of vertices)
    n_legs = int(n_vertices * 0.3)
    for _ in range(n_legs):
        side = np.random.choice([-1, 1])
        x = side * np.random.uniform(width_factor * 0.05, width_factor * 0.15)
        y = np.random.uniform(-depth_factor * 0.15, depth_factor * 0.15)
        z = np.random.uniform(0, height * 0.5)
        vertices.append([x, y, z])

    vertices_array = np.array(vertices, dtype=np.float32)
    return torch.from_numpy(vertices_array).to(device=device, dtype=dtype)


def generate_pose_parameters(
    bone_count: int = 53,
    pose_type: str = 'identity',
    device: torch.device = torch.device('cpu'),
    dtype: torch.dtype = torch.float32
) -> torch.Tensor:
    """
    Generate pose parameters (4x4 transformation matrices).

    Args:
        bone_count: Number of bones in skeleton
        pose_type: 'identity', 't_pose', 'a_pose', or 'random'
        device: Torch device
        dtype: Torch dtype

    Returns:
        Pose parameters (bone_count, 4, 4)
    """
    if pose_type == 'identity':
        # All bones at identity transformation
        return torch.eye(4, device=device, dtype=dtype).unsqueeze(0).repeat(bone_count, 1, 1)

    elif pose_type == 't_pose':
        # T-pose with arms extended
        poses = torch.eye(4, device=device, dtype=dtype).unsqueeze(0).repeat(bone_count, 1, 1)
        # Rotate shoulder joints (bones 11, 12) to extend arms
        # This is simplified - real implementation would use proper bone hierarchy
        return poses

    elif pose_type == 'a_pose':
        # A-pose (slight arm lowering)
        poses = torch.eye(4, device=device, dtype=dtype).unsqueeze(0).repeat(bone_count, 1, 1)
        return poses

    elif pose_type == 'random':
        # Random but valid poses
        poses = torch.eye(4, device=device, dtype=dtype).unsqueeze(0).repeat(bone_count, 1, 1)
        # Add small random rotations
        for i in range(bone_count):
            # Random rotation angle (small)
            angle = np.random.uniform(-0.1, 0.1)
            axis = np.random.choice([0, 1, 2])
            # Simple rotation matrix
            if axis == 2:  # Z-axis rotation
                poses[i, 0, 0] = np.cos(angle)
                poses[i, 0, 1] = -np.sin(angle)
                poses[i, 1, 0] = np.sin(angle)
                poses[i, 1, 1] = np.cos(angle)
        return poses

    return torch.eye(4, device=device, dtype=dtype).unsqueeze(0).repeat(bone_count, 1, 1)


def create_test_batch(
    batch_size: int = 2,
    vertex_count: int = 1000,
    measurement_profiles: List[str] = None,
    device: torch.device = torch.device('cpu'),
    dtype: torch.dtype = torch.float32
) -> Dict[str, torch.Tensor]:
    """
    Create a batch of test data.

    Args:
        batch_size: Number of samples in batch
        vertex_count: Vertices per sample
        measurement_profiles: List of profile names from SAMPLE_MEASUREMENTS
        device: Torch device
        dtype: Torch dtype

    Returns:
        Dictionary containing:
            - vertices: (batch_size, vertex_count, 3)
            - phenotypes: dict of (batch_size,) tensors
            - measurements: dict of (batch_size,) tensors
    """
    if measurement_profiles is None:
        measurement_profiles = ['average_male', 'average_female'][:batch_size]

    # Generate vertices for each profile
    vertices_list = []
    for profile in measurement_profiles:
        if profile in SAMPLE_MEASUREMENTS:
            height = SAMPLE_MEASUREMENTS[profile]['height']
        else:
            height = 1.70  # Default height

        verts = generate_humanoid_vertices(
            height=height,
            n_vertices=vertex_count,
            device=device,
            dtype=dtype
        )
        vertices_list.append(verts)

    vertices = torch.stack(vertices_list)

    # Extract phenotypes
    phenotypes = {}
    phenotype_keys = list(SAMPLE_PHENOTYPES['average_male'].keys())
    for key in phenotype_keys:
        values = []
        for profile in measurement_profiles:
            phenotype_profile = profile if profile in SAMPLE_PHENOTYPES else 'average_male'
            values.append(SAMPLE_PHENOTYPES[phenotype_profile][key])
        phenotypes[key] = torch.tensor(values, device=device, dtype=dtype)

    # Extract measurements
    measurements = {}
    measurement_keys = list(SAMPLE_MEASUREMENTS['average_male'].keys())
    for key in measurement_keys:
        values = []
        for profile in measurement_profiles:
            measurement_profile = profile if profile in SAMPLE_MEASUREMENTS else 'average_male'
            values.append(SAMPLE_MEASUREMENTS[measurement_profile][key])
        measurements[key] = torch.tensor(values, device=device, dtype=dtype)

    return {
        'vertices': vertices,
        'phenotypes': phenotypes,
        'measurements': measurements,
    }


# Image-related test data
IMAGE_METADATA = {
    'front_view': {
        'resolution': (1920, 1080),
        'format': 'RGB',
        'pose': 'front',
        'distance': 2.0,  # meters from camera
    },
    'side_view': {
        'resolution': (1920, 1080),
        'format': 'RGB',
        'pose': 'side_left',
        'distance': 2.0,
    },
    'three_quarter': {
        'resolution': (1920, 1080),
        'format': 'RGB',
        'pose': 'three_quarter_left',
        'distance': 2.5,
    },
}
