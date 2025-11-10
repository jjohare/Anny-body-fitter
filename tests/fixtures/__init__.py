"""Test fixtures for integration tests."""

from .test_images import (
    create_test_image,
    create_test_image_with_person,
    create_front_view_image,
    create_side_view_image,
    create_back_view_image
)

__all__ = [
    'create_test_image',
    'create_test_image_with_person',
    'create_front_view_image',
    'create_side_view_image',
    'create_back_view_image'
]
