# Anny Body Fitter - Sample Image Generation
# Copyright (C) 2025 NAVER Corp.
# Apache License, Version 2.0
"""
Generate synthetic test images using PIL for testing computer vision pipelines.

Creates simple body shapes and saves them to the fixtures/images directory.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from typing import Tuple, Optional


def draw_humanoid_figure(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    pose: str = 'front',
    color: Tuple[int, int, int] = (200, 150, 100)
) -> None:
    """
    Draw a simple humanoid figure.

    Args:
        draw: PIL ImageDraw object
        width: Image width
        height: Image height
        pose: Pose type ('front', 'side', 't_pose')
        color: RGB color for body
    """
    center_x = width // 2
    head_y = height // 6
    shoulder_y = height // 4
    hip_y = int(height * 0.55)
    knee_y = int(height * 0.78)
    foot_y = int(height * 0.95)

    # Head (circle)
    head_radius = width // 12
    draw.ellipse(
        [center_x - head_radius, head_y - head_radius,
         center_x + head_radius, head_y + head_radius],
        fill=color, outline=(150, 100, 50), width=3
    )

    # Torso (rectangle)
    torso_width = width // 5
    draw.rectangle(
        [center_x - torso_width // 2, shoulder_y,
         center_x + torso_width // 2, hip_y],
        fill=color, outline=(150, 100, 50), width=3
    )

    if pose == 'front':
        # Arms (down at sides)
        arm_width = width // 20
        # Left arm
        draw.rectangle(
            [center_x - torso_width // 2 - arm_width, shoulder_y,
             center_x - torso_width // 2, int(height * 0.6)],
            fill=color, outline=(150, 100, 50), width=2
        )
        # Right arm
        draw.rectangle(
            [center_x + torso_width // 2, shoulder_y,
             center_x + torso_width // 2 + arm_width, int(height * 0.6)],
            fill=color, outline=(150, 100, 50), width=2
        )

    elif pose == 't_pose':
        # Arms (extended horizontally)
        arm_length = int(width * 0.35)
        arm_height = (shoulder_y + hip_y) // 2
        arm_thickness = width // 25

        # Left arm
        draw.rectangle(
            [center_x - torso_width // 2 - arm_length, arm_height - arm_thickness,
             center_x - torso_width // 2, arm_height + arm_thickness],
            fill=color, outline=(150, 100, 50), width=2
        )
        # Right arm
        draw.rectangle(
            [center_x + torso_width // 2, arm_height - arm_thickness,
             center_x + torso_width // 2 + arm_length, arm_height + arm_thickness],
            fill=color, outline=(150, 100, 50), width=2
        )

    elif pose == 'side':
        # Single arm visible (side view)
        arm_width = width // 20
        draw.rectangle(
            [center_x + torso_width // 4, shoulder_y,
             center_x + torso_width // 4 + arm_width, int(height * 0.6)],
            fill=color, outline=(150, 100, 50), width=2
        )

    # Legs
    leg_width = width // 12
    leg_spacing = width // 20

    # Left leg
    draw.rectangle(
        [center_x - leg_spacing - leg_width, hip_y,
         center_x - leg_spacing, foot_y],
        fill=color, outline=(150, 100, 50), width=2
    )
    # Right leg
    draw.rectangle(
        [center_x + leg_spacing, hip_y,
         center_x + leg_spacing + leg_width, foot_y],
        fill=color, outline=(150, 100, 50), width=2
    )

    # Facial features (simple)
    eye_y = head_y - head_radius // 4
    eye_offset = head_radius // 3
    eye_size = head_radius // 6

    # Left eye
    draw.ellipse(
        [center_x - eye_offset - eye_size, eye_y - eye_size,
         center_x - eye_offset + eye_size, eye_y + eye_size],
        fill=(50, 50, 50)
    )
    # Right eye
    draw.ellipse(
        [center_x + eye_offset - eye_size, eye_y - eye_size,
         center_x + eye_offset + eye_size, eye_y + eye_size],
        fill=(50, 50, 50)
    )

    # Mouth
    mouth_y = head_y + head_radius // 3
    draw.arc(
        [center_x - head_radius // 2, mouth_y - head_radius // 4,
         center_x + head_radius // 2, mouth_y + head_radius // 4],
        0, 180, fill=(100, 50, 50), width=2
    )


def create_test_image(
    width: int = 640,
    height: int = 480,
    pose: str = 'front',
    background_color: Tuple[int, int, int] = (240, 240, 245),
    body_color: Tuple[int, int, int] = (200, 150, 100)
) -> Image.Image:
    """
    Create a synthetic test image with a simple humanoid figure.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        pose: Pose type
        background_color: RGB background color
        body_color: RGB body color

    Returns:
        PIL Image
    """
    # Create image
    img = Image.new('RGB', (width, height), background_color)
    draw = ImageDraw.Draw(img)

    # Draw humanoid figure
    draw_humanoid_figure(draw, width, height, pose, body_color)

    # Add grid for depth reference
    grid_color = (220, 220, 225)
    for i in range(0, width, 50):
        draw.line([(i, 0), (i, height)], fill=grid_color, width=1)
    for i in range(0, height, 50):
        draw.line([(0, i), (width, i)], fill=grid_color, width=1)

    return img


def generate_all_test_images(output_dir: Path) -> None:
    """
    Generate all test images and save to directory.

    Args:
        output_dir: Directory to save images
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    image_configs = [
        {
            'filename': 'front_view.png',
            'width': 1920,
            'height': 1080,
            'pose': 'front',
            'background': (240, 245, 250),
            'body': (210, 160, 110),
        },
        {
            'filename': 'side_view.png',
            'width': 1920,
            'height': 1080,
            'pose': 'side',
            'background': (245, 240, 235),
            'body': (200, 150, 100),
        },
        {
            'filename': 't_pose.png',
            'width': 1920,
            'height': 1080,
            'pose': 't_pose',
            'background': (235, 245, 240),
            'body': (205, 155, 105),
        },
        {
            'filename': 'front_low_res.png',
            'width': 640,
            'height': 480,
            'pose': 'front',
            'background': (240, 240, 245),
            'body': (200, 150, 100),
        },
        {
            'filename': 'full_body.png',
            'width': 1280,
            'height': 1920,  # Taller for full body
            'pose': 'front',
            'background': (250, 250, 255),
            'body': (195, 145, 95),
        },
    ]

    for config in image_configs:
        img = create_test_image(
            width=config['width'],
            height=config['height'],
            pose=config['pose'],
            background_color=config['background'],
            body_color=config['body']
        )

        output_path = output_dir / config['filename']
        img.save(output_path, 'PNG')
        print(f"Generated: {output_path}")


def create_sample_depth_map(
    width: int = 640,
    height: int = 480,
    baseline_depth: float = 2.0
) -> np.ndarray:
    """
    Create a synthetic depth map matching a humanoid figure.

    Args:
        width: Width in pixels
        height: Height in pixels
        baseline_depth: Average depth in meters

    Returns:
        Depth map (H, W) in meters
    """
    # Create gradient depth map
    y_coords = np.linspace(0, 1, height)
    depth_gradient = baseline_depth - y_coords.reshape(-1, 1) * 0.5

    # Add horizontal variation
    x_variation = np.abs(np.linspace(-0.05, 0.05, width))
    depth_map = depth_gradient + x_variation

    # Add body shape (closer than background)
    center_x = width // 2
    for y in range(height):
        for x in range(width):
            # Simple humanoid mask
            if abs(x - center_x) < width // 6 and y > height // 6:
                depth_map[y, x] *= 0.9  # Bring body closer

    return depth_map


if __name__ == '__main__':
    # Generate images when run directly
    script_dir = Path(__file__).parent
    images_dir = script_dir / 'images'
    generate_all_test_images(images_dir)
    print(f"\nAll test images generated in: {images_dir}")
