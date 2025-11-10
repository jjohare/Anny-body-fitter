"""
Progress tracker component
Shows real-time progress during model fitting
"""
import gradio as gr
from typing import List, Dict, Optional


def create_progress_tracker_component() -> gr.Progress:
    """
    Create progress tracking component

    Returns:
        Progress component
    """

    progress = gr.Progress(track_tqdm=True)

    return progress


def create_detailed_progress_display() -> gr.Column:
    """
    Create detailed progress display with step-by-step status

    Returns:
        Column component with progress steps
    """

    with gr.Column(elem_id="progress-container") as progress_col:
        gr.Markdown("### Processing Pipeline")

        # Processing steps
        steps = [
            ("1️⃣", "Photo preprocessing", "photo_prep_status"),
            ("2️⃣", "Pose detection", "pose_status"),
            ("3️⃣", "Silhouette extraction", "silhouette_status"),
            ("4️⃣", "Initial alignment", "alignment_status"),
            ("5️⃣", "Shape optimization", "optimization_status"),
            ("6️⃣", "Final refinement", "refinement_status"),
        ]

        status_components = {}

        for emoji, label, key in steps:
            with gr.Row():
                gr.Markdown(f"{emoji} **{label}**")
                status_components[key] = gr.Markdown("⏳ Pending", elem_classes="status-pending")

        # Overall progress bar
        progress_bar = gr.Progress()

    return progress_col, status_components, progress_bar


def update_step_status(
    step_name: str,
    status: str,
    message: Optional[str] = None
) -> str:
    """
    Generate status markdown for a processing step

    Args:
        step_name: Name of the processing step
        status: Status (pending, processing, success, error)
        message: Optional status message

    Returns:
        Formatted markdown string
    """
    status_icons = {
        "pending": "⏳",
        "processing": "🔄",
        "success": "✅",
        "error": "❌",
        "warning": "⚠️"
    }

    status_classes = {
        "pending": "status-pending",
        "processing": "status-processing",
        "success": "status-success",
        "error": "status-error",
        "warning": "status-warning"
    }

    icon = status_icons.get(status, "❓")
    css_class = status_classes.get(status, "")

    if message:
        return f'<span class="{css_class}">{icon} {status.title()}: {message}</span>'
    else:
        return f'<span class="{css_class}">{icon} {status.title()}</span>'
