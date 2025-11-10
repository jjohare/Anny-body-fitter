"""
Main Gradio application for Anny Body Fitter
Combines photo upload, subject metadata input, and 3D model visualization
"""
import gradio as gr
import torch
import tempfile
from typing import Optional, Dict, List, Tuple
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from frontend.components.photo_upload import create_photo_upload_component
from frontend.components.subject_form import create_subject_form_component
from frontend.components.model_viewer import create_model_viewer_component
from frontend.components.progress_tracker import create_progress_tracker_component
from frontend.components.measurement_display import create_measurement_display_component
from frontend.utils.state_manager import StateManager


def create_demo(
    server_name: Optional[str] = None,
    server_port: Optional[int] = None,
    share: bool = False
) -> gr.Blocks:
    """
    Create the main Gradio demo application

    Args:
        server_name: Server hostname (None for localhost)
        server_port: Server port (None for default)
        share: Whether to create a public share link

    Returns:
        Configured Gradio Blocks application
    """

    # Initialize state manager
    state_manager = StateManager()

    # Custom CSS for better layout
    custom_css = """
    #main-container { max-width: 1400px; margin: auto; }
    #control-column { max-width: 400px; }
    #viewer-column { min-width: 600px; }
    #upload-area { border: 2px dashed #ccc; border-radius: 8px; padding: 20px; }
    #progress-container { margin: 20px 0; }
    .measurement-table { width: 100%; border-collapse: collapse; }
    .measurement-table th, .measurement-table td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
    .status-success { color: #28a745; }
    .status-processing { color: #ffc107; }
    .status-error { color: #dc3545; }
    """

    with gr.Blocks(
        title="Anny Body Fitter - 3D Body Model from Photos",
        css=custom_css,
        theme=gr.themes.Soft()
    ) as demo:

        gr.Markdown("""
        # 🎯 Anny Body Fitter
        ### Create personalized 3D body models from photographs

        Upload photos of a subject from multiple angles and provide basic measurements
        to generate a fitted 3D body model using the Anny parametric model.
        """)

        with gr.Row():
            # Left column: Controls and inputs
            with gr.Column(scale=1, elem_id="control-column"):
                gr.Markdown("## 📸 Step 1: Upload Photos")

                # Photo upload component
                photo_upload, photo_gallery = create_photo_upload_component()

                gr.Markdown("## 👤 Step 2: Subject Information")

                # Subject form component
                subject_form = create_subject_form_component()

                # Processing controls
                gr.Markdown("## ⚙️ Step 3: Processing Options")

                with gr.Accordion("Advanced Options", open=False):
                    processing_quality = gr.Radio(
                        choices=["Fast", "Balanced", "High Quality"],
                        value="Balanced",
                        label="Processing Quality"
                    )

                    optimization_iterations = gr.Slider(
                        minimum=10,
                        maximum=200,
                        value=100,
                        step=10,
                        label="Optimization Iterations"
                    )

                    use_silhouette = gr.Checkbox(
                        label="Use silhouette fitting",
                        value=True
                    )

                    use_keypoints = gr.Checkbox(
                        label="Use keypoint detection",
                        value=True
                    )

                # Action buttons
                with gr.Row():
                    fit_button = gr.Button(
                        "🚀 Fit Model",
                        variant="primary",
                        size="lg"
                    )
                    clear_button = gr.Button(
                        "🔄 Clear All",
                        variant="secondary"
                    )

            # Right column: Results and visualization
            with gr.Column(scale=2, elem_id="viewer-column"):
                gr.Markdown("## 📊 Results")

                # Progress tracker
                progress_component = create_progress_tracker_component()

                # Status message
                status_message = gr.Markdown(
                    "Upload photos and fill in subject information to begin.",
                    elem_id="status-message"
                )

                # 3D Model viewer
                model_viewer, viewer_controls = create_model_viewer_component()

                # Measurement comparison
                measurement_display = create_measurement_display_component()

                # Export options
                with gr.Row():
                    export_model_button = gr.DownloadButton(
                        "💾 Download 3D Model (.glb)",
                        visible=False
                    )
                    export_params_button = gr.DownloadButton(
                        "📄 Download Parameters (.json)",
                        visible=False
                    )
                    export_report_button = gr.DownloadButton(
                        "📊 Download Report (.pdf)",
                        visible=False
                    )

        # Event handlers
        def handle_fit_model(
            photos: List,
            name: str,
            dob: str,
            gender: str,
            height: float,
            weight: float,
            chest: float,
            waist: float,
            hips: float,
            quality: str,
            iterations: int,
            use_silhouette: bool,
            use_keypoints: bool
        ):
            """Handle the fit model button click"""
            try:
                # Validate inputs
                if not photos or len(photos) == 0:
                    return (
                        None,
                        None,
                        gr.update(value="❌ Please upload at least one photo."),
                        gr.update(visible=False),
                        gr.update(visible=False),
                        gr.update(visible=False),
                        0
                    )

                if not name or not dob or not gender:
                    return (
                        None,
                        None,
                        gr.update(value="❌ Please fill in all required subject information."),
                        gr.update(visible=False),
                        gr.update(visible=False),
                        gr.update(visible=False),
                        0
                    )

                # Update status
                status_msg = "🔄 Processing... This may take a few minutes."

                # TODO: Call fitting pipeline
                # For now, return placeholder

                return (
                    None,  # model_viewer
                    None,  # measurement_display
                    gr.update(value=status_msg),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    50  # progress
                )

            except Exception as e:
                return (
                    None,
                    None,
                    gr.update(value=f"❌ Error: {str(e)}"),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    0
                )

        def handle_clear_all():
            """Clear all inputs and reset the interface"""
            return (
                None,  # photos
                None,  # gallery
                "",    # name
                "",    # dob
                "Male",  # gender
                170.0,  # height
                70.0,   # weight
                None,   # chest
                None,   # waist
                None,   # hips
                None,   # model_viewer
                None,   # measurements
                gr.update(value="Upload photos and fill in subject information to begin."),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                0  # progress
            )

        # Wire up event handlers
        fit_button.click(
            fn=handle_fit_model,
            inputs=[
                photo_upload,
                *subject_form,
                processing_quality,
                optimization_iterations,
                use_silhouette,
                use_keypoints
            ],
            outputs=[
                model_viewer,
                measurement_display,
                status_message,
                export_model_button,
                export_params_button,
                export_report_button,
                progress_component
            ]
        )

        clear_button.click(
            fn=handle_clear_all,
            inputs=[],
            outputs=[
                photo_upload,
                photo_gallery,
                *subject_form,
                model_viewer,
                measurement_display,
                status_message,
                export_model_button,
                export_params_button,
                export_report_button,
                progress_component
            ]
        )

    return demo


def main(
    server_name: Optional[str] = None,
    server_port: Optional[int] = 7860,
    share: bool = False
):
    """
    Launch the Gradio demo

    Args:
        server_name: Server hostname
        server_port: Server port
        share: Create public share link
    """
    demo = create_demo(server_name, server_port, share)
    demo.launch(
        server_name=server_name,
        server_port=server_port,
        share=share
    )


if __name__ == "__main__":
    from jsonargparse import CLI
    CLI(main)
