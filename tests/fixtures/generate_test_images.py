#!/usr/bin/env python3
"""
Generate synthetic test images for body fitting tests.

This script creates simple humanoid silhouettes in different poses:
- Front view
- Side view
- Back view
- 3/4 view
- Cropped upper body view

All images are 640x480 pixels, RGB format.
"""

from PIL import Image, ImageDraw
import os


def create_front_view(width=640, height=480):
    """Create a front-facing humanoid silhouette."""
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # Head (circle)
    draw.ellipse([270, 50, 370, 150], fill='tan', outline='black', width=2)

    # Neck
    draw.rectangle([310, 150, 330, 170], fill='tan', outline='black', width=1)

    # Torso (trapezoid-like shape using polygon)
    draw.polygon([
        (250, 170),  # Left shoulder
        (390, 170),  # Right shoulder
        (380, 300),  # Right hip
        (260, 300)   # Left hip
    ], fill='blue', outline='black')

    # Arms
    draw.rectangle([180, 170, 250, 200], fill='tan', outline='black', width=1)  # Left upper arm
    draw.rectangle([180, 200, 220, 350], fill='tan', outline='black', width=1)  # Left forearm
    draw.rectangle([390, 170, 460, 200], fill='tan', outline='black', width=1)  # Right upper arm
    draw.rectangle([420, 200, 460, 350], fill='tan', outline='black', width=1)  # Right forearm

    # Legs
    draw.rectangle([260, 300, 315, 400], fill='gray', outline='black', width=1)  # Left thigh
    draw.rectangle([265, 400, 310, 460], fill='gray', outline='black', width=1)  # Left shin
    draw.rectangle([325, 300, 380, 400], fill='gray', outline='black', width=1)  # Right thigh
    draw.rectangle([330, 400, 375, 460], fill='gray', outline='black', width=1)  # Right shin

    return img


def create_side_view(width=640, height=480):
    """Create a side profile silhouette."""
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # Head (circle, positioned to the right)
    draw.ellipse([350, 50, 430, 130], fill='tan', outline='black', width=2)

    # Neck
    draw.rectangle([360, 130, 380, 150], fill='tan', outline='black', width=1)

    # Torso (curved profile)
    draw.polygon([
        (340, 150),  # Back of neck
        (320, 200),  # Upper back
        (310, 300),  # Lower back
        (350, 300),  # Front hip
        (380, 250),  # Front chest
        (370, 150)   # Front shoulder
    ], fill='blue', outline='black')

    # Arm (single arm visible in profile)
    draw.rectangle([310, 150, 340, 200], fill='tan', outline='black', width=1)  # Upper arm
    draw.rectangle([300, 200, 330, 320], fill='tan', outline='black', width=1)  # Forearm

    # Legs (one in front, one behind)
    draw.rectangle([320, 300, 360, 400], fill='gray', outline='black', width=1)  # Thigh
    draw.rectangle([325, 400, 355, 460], fill='gray', outline='black', width=1)  # Shin

    return img


def create_back_view(width=640, height=480):
    """Create a rear-facing humanoid silhouette."""
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # Head (circle, back of head)
    draw.ellipse([270, 50, 370, 150], fill='tan', outline='black', width=2)

    # Neck
    draw.rectangle([310, 150, 330, 170], fill='tan', outline='black', width=1)

    # Torso (back view, slightly different shape)
    draw.polygon([
        (250, 170),  # Left shoulder
        (390, 170),  # Right shoulder
        (375, 300),  # Right hip
        (265, 300)   # Left hip
    ], fill='darkblue', outline='black')

    # Arms (back view)
    draw.rectangle([180, 170, 250, 200], fill='tan', outline='black', width=1)  # Left upper arm
    draw.rectangle([185, 200, 225, 340], fill='tan', outline='black', width=1)  # Left forearm
    draw.rectangle([390, 170, 460, 200], fill='tan', outline='black', width=1)  # Right upper arm
    draw.rectangle([415, 200, 455, 340], fill='tan', outline='black', width=1)  # Right forearm

    # Legs (back view)
    draw.rectangle([265, 300, 315, 400], fill='darkgray', outline='black', width=1)  # Left thigh
    draw.rectangle([268, 400, 312, 460], fill='darkgray', outline='black', width=1)  # Left shin
    draw.rectangle([325, 300, 375, 400], fill='darkgray', outline='black', width=1)  # Right thigh
    draw.rectangle([328, 400, 372, 460], fill='darkgray', outline='black', width=1)  # Right shin

    return img


def create_three_quarter_view(width=640, height=480):
    """Create a 3/4 angled pose silhouette."""
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # Head (slightly rotated ellipse)
    draw.ellipse([290, 50, 380, 140], fill='tan', outline='black', width=2)

    # Neck
    draw.rectangle([325, 140, 345, 160], fill='tan', outline='black', width=1)

    # Torso (3/4 view - asymmetric)
    draw.polygon([
        (270, 160),  # Left shoulder (more visible)
        (390, 165),  # Right shoulder (less visible)
        (375, 290),  # Right hip
        (280, 295)   # Left hip
    ], fill='mediumblue', outline='black')

    # Arms (left more visible)
    draw.rectangle([200, 160, 270, 190], fill='tan', outline='black', width=1)  # Left upper arm
    draw.rectangle([200, 190, 240, 330], fill='tan', outline='black', width=1)  # Left forearm
    draw.rectangle([390, 165, 440, 190], fill='tan', outline='black', width=1)  # Right upper arm (partial)
    draw.rectangle([410, 190, 440, 310], fill='tan', outline='black', width=1)  # Right forearm (partial)

    # Legs (left more prominent)
    draw.rectangle([280, 295, 325, 395], fill='slategray', outline='black', width=1)  # Left thigh
    draw.rectangle([283, 395, 322, 455], fill='slategray', outline='black', width=1)  # Left shin
    draw.rectangle([335, 295, 375, 395], fill='slategray', outline='black', width=1)  # Right thigh
    draw.rectangle([338, 395, 372, 455], fill='slategray', outline='black', width=1)  # Right shin

    return img


def create_cropped_view(width=640, height=480):
    """Create an upper body only (cropped) view."""
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # Head (larger, centered)
    draw.ellipse([250, 30, 390, 170], fill='tan', outline='black', width=2)

    # Neck
    draw.rectangle([305, 170, 335, 200], fill='tan', outline='black', width=1)

    # Torso (upper portion only, larger)
    draw.polygon([
        (220, 200),  # Left shoulder
        (420, 200),  # Right shoulder
        (410, 400),  # Right mid-torso
        (230, 400)   # Left mid-torso
    ], fill='blue', outline='black')

    # Arms (upper body only)
    draw.rectangle([140, 200, 220, 250], fill='tan', outline='black', width=1)  # Left upper arm
    draw.rectangle([140, 250, 190, 430], fill='tan', outline='black', width=1)  # Left forearm
    draw.rectangle([420, 200, 500, 250], fill='tan', outline='black', width=1)  # Right upper arm
    draw.rectangle([450, 250, 500, 430], fill='tan', outline='black', width=1)  # Right forearm

    # Add text indicator
    draw.text((10, 10), "CROPPED - UPPER BODY ONLY", fill='red')

    return img


def main():
    """Generate all test images and save them."""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, 'images')

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    print("Generating synthetic test images...")

    # Generate and save all views
    images = {
        'front_view.png': create_front_view(),
        'side_view.png': create_side_view(),
        'back_view.png': create_back_view(),
        'three_quarter_view.png': create_three_quarter_view(),
        'cropped_view.png': create_cropped_view()
    }

    for filename, image in images.items():
        filepath = os.path.join(output_dir, filename)
        image.save(filepath)
        print(f"✓ Created: {filename} ({image.size[0]}x{image.size[1]} pixels)")

    print(f"\nAll test images saved to: {output_dir}")
    print("Total images created: 5")


if __name__ == '__main__':
    main()
