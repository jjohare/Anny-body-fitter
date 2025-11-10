"""
Measurement comparison display component
Shows comparison between input and fitted model measurements
"""
import gradio as gr
from typing import Dict, List, Optional, Tuple
import pandas as pd


def create_measurement_display_component() -> gr.Dataframe:
    """
    Create measurement comparison table

    Returns:
        Dataframe component for measurements
    """

    with gr.Column():
        gr.Markdown("### Measurement Comparison")

        # Create sample dataframe structure
        sample_data = pd.DataFrame({
            "Measurement": ["Height", "Chest", "Waist", "Hips"],
            "Input (cm)": ["-", "-", "-", "-"],
            "Fitted Model (cm)": ["-", "-", "-", "-"],
            "Difference (cm)": ["-", "-", "-", "-"],
            "Accuracy": ["-", "-", "-", "-"]
        })

        measurements_table = gr.Dataframe(
            value=sample_data,
            label="Measurements",
            interactive=False,
            wrap=True
        )

        # Summary statistics
        summary_stats = gr.Markdown("""
        **Fitting Accuracy**: -
        **Average Error**: -
        **Max Error**: -
        """)

    return measurements_table


def format_measurements_table(
    input_measurements: Dict[str, float],
    fitted_measurements: Dict[str, float]
) -> pd.DataFrame:
    """
    Format measurements into comparison table

    Args:
        input_measurements: Input measurements from user
        fitted_measurements: Measurements from fitted model

    Returns:
        Formatted DataFrame
    """
    rows = []

    for key in input_measurements.keys():
        input_val = input_measurements.get(key)
        fitted_val = fitted_measurements.get(key)

        if input_val is not None and fitted_val is not None:
            diff = fitted_val - input_val
            accuracy = 100 * (1 - abs(diff) / input_val) if input_val != 0 else 0

            rows.append({
                "Measurement": key.title(),
                "Input (cm)": f"{input_val:.1f}",
                "Fitted Model (cm)": f"{fitted_val:.1f}",
                "Difference (cm)": f"{diff:+.1f}",
                "Accuracy": f"{accuracy:.1f}%"
            })
        elif input_val is not None:
            rows.append({
                "Measurement": key.title(),
                "Input (cm)": f"{input_val:.1f}",
                "Fitted Model (cm)": "-",
                "Difference (cm)": "-",
                "Accuracy": "-"
            })

    return pd.DataFrame(rows)


def calculate_measurement_statistics(
    input_measurements: Dict[str, float],
    fitted_measurements: Dict[str, float]
) -> Dict[str, float]:
    """
    Calculate summary statistics for measurement accuracy

    Args:
        input_measurements: Input measurements
        fitted_measurements: Fitted measurements

    Returns:
        Dictionary with statistics
    """
    errors = []

    for key in input_measurements.keys():
        input_val = input_measurements.get(key)
        fitted_val = fitted_measurements.get(key)

        if input_val is not None and fitted_val is not None:
            error = abs(fitted_val - input_val)
            errors.append(error)

    if not errors:
        return {
            "average_error": 0.0,
            "max_error": 0.0,
            "accuracy": 0.0
        }

    avg_error = sum(errors) / len(errors)
    max_error = max(errors)
    accuracy = 100 * (1 - avg_error / max(input_measurements.values()))

    return {
        "average_error": avg_error,
        "max_error": max_error,
        "accuracy": accuracy
    }


def create_anthropometric_chart(
    measurements: Dict[str, float],
    age: int,
    gender: str
) -> Optional[gr.Plot]:
    """
    Create anthropometric percentile chart

    Args:
        measurements: Body measurements
        age: Subject age
        gender: Subject gender

    Returns:
        Plot component or None
    """
    # TODO: Implement percentile plotting
    # This would compare measurements against population norms
    pass
