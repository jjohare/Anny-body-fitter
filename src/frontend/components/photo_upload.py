"""
Photo upload component with drag-and-drop support
Handles multiple photo uploads from different angles
"""
import gradio as gr
from typing import Tuple, List, Optional
import os


def create_photo_upload_component() -> Tuple[gr.File, gr.Gallery]:
    """
    Create photo upload component with preview gallery

    Returns:
        Tuple of (upload_component, gallery_component)
    """

    with gr.Column():
        gr.Markdown("""
        ### Upload Photos (Minimum 3 recommended)
        - Front view (required)
        - Side view (recommended)
        - Back view (optional)
        - Additional angles (optional)

        **Tips for best results:**
        - Use well-lit photos
        - Subject should be in fitted clothing or swimwear
        - Stand in neutral pose (arms slightly away from body)
        - Avoid baggy clothing
        """)

        # File upload with multiple file support
        photo_upload = gr.File(
            label="Select or drag photos here",
            file_count="multiple",
            file_types=["image"],
            elem_id="upload-area"
        )

        # Gallery for preview
        photo_gallery = gr.Gallery(
            label="Uploaded Photos",
            show_label=True,
            columns=3,
            rows=2,
            height="auto",
            object_fit="contain"
        )

        # Photo count indicator
        photo_count = gr.Markdown("No photos uploaded yet")

        def update_gallery(files):
            """Update gallery when files are uploaded"""
            if not files:
                return None, "No photos uploaded yet"

            file_paths = [f.name if hasattr(f, 'name') else f for f in files]
            count = len(file_paths)
            status = f"✅ {count} photo{'s' if count != 1 else ''} uploaded"

            return file_paths, status

        photo_upload.change(
            fn=update_gallery,
            inputs=[photo_upload],
            outputs=[photo_gallery, photo_count]
        )

    return photo_upload, photo_gallery


def validate_photos(photos: List) -> Tuple[bool, str]:
    """
    Validate uploaded photos

    Args:
        photos: List of uploaded photo files

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not photos or len(photos) == 0:
        return False, "Please upload at least one photo"

    if len(photos) < 2:
        return False, "Please upload at least 2 photos from different angles for better results"

    # Check file sizes
    max_size = 10 * 1024 * 1024  # 10 MB
    for photo in photos:
        if hasattr(photo, 'size') and photo.size > max_size:
            return False, f"Photo {photo.name} is too large. Maximum size is 10 MB"

    return True, "Photos validated successfully"
