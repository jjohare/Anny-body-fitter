"""
3D Model viewer component
Displays fitted body model with rotation and zoom controls
"""
import gradio as gr
from typing import Tuple, Optional, Dict
import tempfile
import trimesh
import torch
import roma


def create_model_viewer_component() -> Tuple[gr.Model3D, Dict]:
    """
    Create 3D model viewer with controls

    Returns:
        Tuple of (model3d_component, controls_dict)
    """

    with gr.Column():
        gr.Markdown("### 3D Model Visualization")

        # 3D Model viewer
        model3d = gr.Model3D(
            label="Fitted Body Model",
            height=600,
            clear_color=[0.9, 0.9, 0.95, 1.0],
            camera_position=[0, 0, 2]
        )

        # Viewer controls
        with gr.Accordion("Display Options", open=True):
            show_wireframe = gr.Checkbox(
                label="Show wireframe",
                value=False
            )

            show_measurements = gr.Checkbox(
                label="Show measurement points",
                value=True
            )

            show_skeleton = gr.Checkbox(
                label="Show skeleton",
                value=False
            )

            lighting_quality = gr.Radio(
                choices=["Low", "Medium", "High"],
                value="Medium",
                label="Lighting Quality"
            )

        # View presets
        with gr.Row():
            front_view_btn = gr.Button("Front View", size="sm")
            side_view_btn = gr.Button("Side View", size="sm")
            back_view_btn = gr.Button("Back View", size="sm")
            top_view_btn = gr.Button("Top View", size="sm")

    controls = {
        "show_wireframe": show_wireframe,
        "show_measurements": show_measurements,
        "show_skeleton": show_skeleton,
        "lighting_quality": lighting_quality,
        "view_buttons": [front_view_btn, side_view_btn, back_view_btn, top_view_btn]
    }

    return model3d, controls


def export_model_to_glb(
    vertices: torch.Tensor,
    faces: torch.Tensor,
    output_path: Optional[str] = None,
    show_skeleton: bool = False,
    show_measurements: bool = False
) -> str:
    """
    Export model to GLB format for viewing

    Args:
        vertices: Model vertices (N, 3)
        faces: Model faces (M, 3)
        output_path: Output file path (creates temp file if None)
        show_skeleton: Whether to include skeleton visualization
        show_measurements: Whether to include measurement points

    Returns:
        Path to exported GLB file
    """
    if output_path is None:
        temp_file = tempfile.NamedTemporaryFile(suffix=".glb", delete=False)
        output_path = temp_file.name

    # Create scene
    scene = trimesh.Scene()

    # Add coordinate axis
    axis = trimesh.creation.axis(
        origin_size=0.01,
        axis_radius=0.005,
        axis_length=1.0
    )
    scene.add_geometry(axis)

    # Create mesh
    mesh = trimesh.Trimesh(
        vertices=vertices.cpu().numpy() if torch.is_tensor(vertices) else vertices,
        faces=faces.cpu().numpy() if torch.is_tensor(faces) else faces
    )

    # Add material
    material = trimesh.visual.material.PBRMaterial(
        baseColorFactor=[0.8, 0.6, 0.5, 1.0],
        metallicFactor=0.2,
        roughnessFactor=0.8,
        doubleSided=True,
        alphaMode='OPAQUE'
    )
    mesh.visual = trimesh.visual.TextureVisuals(material=material)
    scene.add_geometry(mesh, node_name="body")

    # Apply Z-up to Y-up transformation for Gradio viewer
    view_transform = roma.Rigid(
        roma.euler_to_rotmat('x', [-90.], degrees=True),
        torch.zeros(3)
    ).to_homogeneous().numpy()
    scene.apply_transform(view_transform)

    # Export
    scene.export(output_path)

    return output_path


def create_comparison_viewer(
    original_model_path: str,
    fitted_model_path: str
) -> gr.Row:
    """
    Create side-by-side comparison viewer

    Args:
        original_model_path: Path to original/template model
        fitted_model_path: Path to fitted model

    Returns:
        Gradio Row component with two viewers
    """
    with gr.Row():
        with gr.Column():
            gr.Markdown("### Template Model")
            original_viewer = gr.Model3D(
                value=original_model_path,
                height=400
            )

        with gr.Column():
            gr.Markdown("### Fitted Model")
            fitted_viewer = gr.Model3D(
                value=fitted_model_path,
                height=400
            )

    return gr.Row()
