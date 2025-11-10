"""Test fixtures for generating synthetic test images."""

import numpy as np
from PIL import Image
import io


def create_test_image(width: int = 640, height: int = 480, color: tuple = (128, 128, 128)) -> bytes:
    """
    Create a simple test image.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        color: RGB color tuple

    Returns:
        Image bytes in JPEG format
    """
    # Create a solid color image
    img = Image.new('RGB', (width, height), color=color)

    # Add some simple patterns to make it more realistic
    pixels = img.load()
    for i in range(width):
        for j in range(height):
            # Add gradient
            r, g, b = color
            r = min(255, r + i // 10)
            g = min(255, g + j // 10)
            pixels[i, j] = (r, g, b)

    # Convert to bytes
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='JPEG', quality=95)
    img_buffer.seek(0)
    return img_buffer.getvalue()


def create_test_image_with_person(width: int = 640, height: int = 480) -> bytes:
    """
    Create a test image with a simple person-like shape.

    Args:
        width: Image width
        height: Image height

    Returns:
        Image bytes
    """
    # Create background
    img = Image.new('RGB', (width, height), color=(200, 200, 200))
    pixels = img.load()

    # Draw simple person shape (head, torso, arms, legs)
    center_x = width // 2

    # Head (circle)
    head_y = height // 4
    head_radius = 40
    for i in range(width):
        for j in range(height):
            dist = np.sqrt((i - center_x)**2 + (j - head_y)**2)
            if dist < head_radius:
                pixels[i, j] = (255, 220, 200)  # Skin tone

    # Torso (rectangle)
    torso_top = head_y + head_radius
    torso_bottom = int(height * 0.6)
    torso_width = 80
    for i in range(center_x - torso_width//2, center_x + torso_width//2):
        for j in range(torso_top, torso_bottom):
            if 0 <= i < width and 0 <= j < height:
                pixels[i, j] = (100, 100, 255)  # Blue shirt

    # Arms
    arm_width = 20
    for i in range(center_x - torso_width//2 - arm_width, center_x - torso_width//2):
        for j in range(torso_top, torso_bottom):
            if 0 <= i < width and 0 <= j < height:
                pixels[i, j] = (100, 100, 255)
    for i in range(center_x + torso_width//2, center_x + torso_width//2 + arm_width):
        for j in range(torso_top, torso_bottom):
            if 0 <= i < width and 0 <= j < height:
                pixels[i, j] = (100, 100, 255)

    # Legs
    leg_width = 30
    leg_gap = 10
    for i in range(center_x - leg_width - leg_gap//2, center_x - leg_gap//2):
        for j in range(torso_bottom, height - 20):
            if 0 <= i < width and 0 <= j < height:
                pixels[i, j] = (50, 50, 100)  # Dark pants
    for i in range(center_x + leg_gap//2, center_x + leg_width + leg_gap//2):
        for j in range(torso_bottom, height - 20):
            if 0 <= i < width and 0 <= j < height:
                pixels[i, j] = (50, 50, 100)

    # Convert to bytes
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='JPEG', quality=95)
    img_buffer.seek(0)
    return img_buffer.getvalue()


def create_front_view_image() -> bytes:
    """Create a front view test image."""
    return create_test_image_with_person(640, 480)


def create_side_view_image() -> bytes:
    """Create a side view test image."""
    img_bytes = create_test_image_with_person(640, 480)
    # In a real scenario, this would be a different pose
    return img_bytes


def create_back_view_image() -> bytes:
    """Create a back view test image."""
    img_bytes = create_test_image_with_person(640, 480)
    # In a real scenario, this would be a different pose
    return img_bytes
