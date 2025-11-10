"""
Subject information form component
Collects metadata about the subject for body fitting
"""
import gradio as gr
from typing import Tuple, Optional
from datetime import datetime


def create_subject_form_component() -> Tuple[gr.Textbox, gr.Textbox, gr.Radio, gr.Number, gr.Number, gr.Number, gr.Number, gr.Number]:
    """
    Create subject information form

    Returns:
        Tuple of form components (name, dob, gender, height, weight, chest, waist, hips)
    """

    with gr.Column():
        # Basic information
        name = gr.Textbox(
            label="Name",
            placeholder="Subject's name",
            info="For identification purposes only"
        )

        dob = gr.Textbox(
            label="Date of Birth",
            placeholder="YYYY-MM-DD",
            info="Used to estimate age-appropriate body proportions"
        )

        gender = gr.Radio(
            choices=["Male", "Female", "Other"],
            label="Gender",
            value="Male",
            info="Used for body model selection"
        )

        gr.Markdown("### Body Measurements (cm/kg)")
        gr.Markdown("*Measurements help improve fitting accuracy*")

        # Primary measurements
        with gr.Row():
            height = gr.Number(
                label="Height (cm)",
                value=170.0,
                minimum=50.0,
                maximum=250.0,
                info="Required"
            )

            weight = gr.Number(
                label="Weight (kg)",
                value=70.0,
                minimum=10.0,
                maximum=300.0,
                info="Required"
            )

        # Optional detailed measurements
        with gr.Accordion("Detailed Measurements (Optional)", open=False):
            gr.Markdown("""
            Providing these measurements will significantly improve fitting accuracy:
            - **Chest**: Circumference at fullest part
            - **Waist**: Circumference at narrowest part
            - **Hips**: Circumference at widest part
            """)

            chest = gr.Number(
                label="Chest/Bust (cm)",
                minimum=50.0,
                maximum=200.0,
                value=None
            )

            waist = gr.Number(
                label="Waist (cm)",
                minimum=40.0,
                maximum=200.0,
                value=None
            )

            hips = gr.Number(
                label="Hips (cm)",
                minimum=50.0,
                maximum=200.0,
                value=None
            )

    return name, dob, gender, height, weight, chest, waist, hips


def validate_subject_info(
    name: str,
    dob: str,
    gender: str,
    height: float,
    weight: float
) -> Tuple[bool, str]:
    """
    Validate subject information

    Args:
        name: Subject's name
        dob: Date of birth (YYYY-MM-DD)
        gender: Gender
        height: Height in cm
        weight: Weight in kg

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name or name.strip() == "":
        return False, "Please enter a name"

    if not dob or dob.strip() == "":
        return False, "Please enter date of birth"

    # Validate date format
    try:
        date_obj = datetime.strptime(dob, "%Y-%m-%d")
        age = (datetime.now() - date_obj).days / 365.25

        if age < 0 or age > 120:
            return False, "Invalid date of birth"
    except ValueError:
        return False, "Date of birth must be in YYYY-MM-DD format"

    if not gender or gender not in ["Male", "Female", "Other"]:
        return False, "Please select a gender"

    if height is None or height < 50 or height > 250:
        return False, "Height must be between 50 and 250 cm"

    if weight is None or weight < 10 or weight > 300:
        return False, "Weight must be between 10 and 300 kg"

    return True, "Subject information validated successfully"
