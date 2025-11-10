# Frontend API Reference

## Main Application

### `create_demo(server_name, server_port, share)`

Create the main Gradio demo application.

**Parameters:**
- `server_name` (str, optional): Server hostname (None for localhost)
- `server_port` (int, optional): Server port (None for default)
- `share` (bool): Whether to create a public share link

**Returns:**
- `gr.Blocks`: Configured Gradio Blocks application

**Example:**
```python
from frontend.app import create_demo

demo = create_demo(
    server_name="0.0.0.0",
    server_port=7860,
    share=True
)
demo.launch()
```

---

## Components API

### Photo Upload

#### `create_photo_upload_component()`

Create photo upload component with preview gallery.

**Returns:**
- `Tuple[gr.File, gr.Gallery]`: Upload component and gallery

**Example:**
```python
from frontend.components.photo_upload import create_photo_upload_component

upload, gallery = create_photo_upload_component()
```

#### `validate_photos(photos)`

Validate uploaded photos.

**Parameters:**
- `photos` (List): List of uploaded photo files

**Returns:**
- `Tuple[bool, str]`: (is_valid, error_message)

**Example:**
```python
from frontend.components.photo_upload import validate_photos

is_valid, message = validate_photos(uploaded_files)
if not is_valid:
    print(f"Validation error: {message}")
```

---

### Subject Form

#### `create_subject_form_component()`

Create subject information form.

**Returns:**
- `Tuple`: (name, dob, gender, height, weight, chest, waist, hips)

**Example:**
```python
from frontend.components.subject_form import create_subject_form_component

name, dob, gender, height, weight, chest, waist, hips = create_subject_form_component()
```

#### `validate_subject_info(name, dob, gender, height, weight)`

Validate subject information.

**Parameters:**
- `name` (str): Subject's name
- `dob` (str): Date of birth (YYYY-MM-DD)
- `gender` (str): Gender
- `height` (float): Height in cm
- `weight` (float): Weight in kg

**Returns:**
- `Tuple[bool, str]`: (is_valid, error_message)

**Example:**
```python
from frontend.components.subject_form import validate_subject_info

is_valid, message = validate_subject_info(
    name="John Doe",
    dob="1990-01-01",
    gender="Male",
    height=170.0,
    weight=70.0
)
```

---

### Model Viewer

#### `create_model_viewer_component()`

Create 3D model viewer with controls.

**Returns:**
- `Tuple[gr.Model3D, Dict]`: Model viewer and controls dictionary

**Example:**
```python
from frontend.components.model_viewer import create_model_viewer_component

viewer, controls = create_model_viewer_component()
```

#### `export_model_to_glb(vertices, faces, output_path, show_skeleton, show_measurements)`

Export model to GLB format for viewing.

**Parameters:**
- `vertices` (torch.Tensor): Model vertices (N, 3)
- `faces` (torch.Tensor): Model faces (M, 3)
- `output_path` (str, optional): Output file path
- `show_skeleton` (bool): Include skeleton visualization
- `show_measurements` (bool): Include measurement points

**Returns:**
- `str`: Path to exported GLB file

**Example:**
```python
from frontend.components.model_viewer import export_model_to_glb
import torch

vertices = torch.randn(6890, 3)
faces = torch.randint(0, 6890, (13776, 3))

glb_path = export_model_to_glb(
    vertices=vertices,
    faces=faces,
    show_skeleton=True,
    show_measurements=True
)
```

---

### Progress Tracker

#### `create_progress_tracker_component()`

Create progress tracking component.

**Returns:**
- `gr.Progress`: Progress component

**Example:**
```python
from frontend.components.progress_tracker import create_progress_tracker_component

progress = create_progress_tracker_component()
```

#### `update_step_status(step_name, status, message)`

Generate status markdown for a processing step.

**Parameters:**
- `step_name` (str): Name of the processing step
- `status` (str): Status (pending, processing, success, error)
- `message` (str, optional): Optional status message

**Returns:**
- `str`: Formatted markdown string

**Example:**
```python
from frontend.components.progress_tracker import update_step_status

status_md = update_step_status(
    step_name="optimization",
    status="success",
    message="Completed in 2.3 seconds"
)
```

---

### Measurement Display

#### `create_measurement_display_component()`

Create measurement comparison table.

**Returns:**
- `gr.Dataframe`: Dataframe component for measurements

**Example:**
```python
from frontend.components.measurement_display import create_measurement_display_component

measurements_table = create_measurement_display_component()
```

#### `format_measurements_table(input_measurements, fitted_measurements)`

Format measurements into comparison table.

**Parameters:**
- `input_measurements` (Dict[str, float]): Input measurements from user
- `fitted_measurements` (Dict[str, float]): Measurements from fitted model

**Returns:**
- `pd.DataFrame`: Formatted DataFrame

**Example:**
```python
from frontend.components.measurement_display import format_measurements_table

input_meas = {"height": 170.0, "chest": 95.0}
fitted_meas = {"height": 171.0, "chest": 96.0}

df = format_measurements_table(input_meas, fitted_meas)
```

#### `calculate_measurement_statistics(input_measurements, fitted_measurements)`

Calculate summary statistics for measurement accuracy.

**Parameters:**
- `input_measurements` (Dict[str, float]): Input measurements
- `fitted_measurements` (Dict[str, float]): Fitted measurements

**Returns:**
- `Dict[str, float]`: Statistics dictionary with keys:
  - `average_error`: Average absolute error
  - `max_error`: Maximum absolute error
  - `accuracy`: Overall accuracy percentage

**Example:**
```python
from frontend.components.measurement_display import calculate_measurement_statistics

stats = calculate_measurement_statistics(input_meas, fitted_meas)
print(f"Accuracy: {stats['accuracy']:.1f}%")
```

---

## State Management

### `StateManager`

Manages application state across Gradio interactions.

#### Methods

##### `create_session(session_id)`

Create a new session.

**Parameters:**
- `session_id` (str, optional): Session ID (generated if not provided)

**Returns:**
- `SessionState`: New SessionState object

**Example:**
```python
from frontend.utils.state_manager import StateManager

manager = StateManager()
session = manager.create_session("session_123")
```

##### `get_session(session_id)`

Get a session by ID.

**Parameters:**
- `session_id` (str, optional): Session ID (uses current if not provided)

**Returns:**
- `SessionState`: SessionState object or None

**Example:**
```python
session = manager.get_session("session_123")
if session:
    print(f"Session status: {session.status}")
```

##### `update_session(session_id, **kwargs)`

Update session state.

**Parameters:**
- `session_id` (str, optional): Session ID
- `**kwargs`: Fields to update

**Returns:**
- `SessionState`: Updated SessionState or None

**Example:**
```python
manager.update_session(
    session_id="session_123",
    status="processing",
    progress=0.5,
    current_step="optimization"
)
```

##### `save_session(session_id, filepath)`

Save session to file.

**Parameters:**
- `session_id` (str, optional): Session ID
- `filepath` (str, optional): Output file path

**Example:**
```python
manager.save_session("session_123", "session_data.json")
```

##### `load_session(filepath)`

Load session from file.

**Parameters:**
- `filepath` (str): Path to session file

**Returns:**
- `SessionState`: Loaded session or None

**Example:**
```python
session = manager.load_session("session_data.json")
```

---

### `SessionState`

Dataclass representing session state.

**Attributes:**
- `session_id` (str): Unique session identifier
- `created_at` (datetime): Session creation time
- `photos` (List[str]): Uploaded photo paths
- `subject_name` (str): Subject name
- `subject_dob` (str): Date of birth
- `subject_gender` (str): Gender
- `height` (float): Height in cm
- `weight` (float): Weight in kg
- `measurements` (Dict[str, float]): Body measurements
- `status` (str): Processing status
- `current_step` (str): Current processing step
- `progress` (float): Progress (0.0 to 1.0)
- `fitted_model_path` (str): Path to fitted model
- `fitted_measurements` (Dict[str, float]): Fitted measurements
- `optimization_history` (List[Dict]): Optimization history
- `processing_options` (Dict): Processing options
- `errors` (List[str]): Error messages

**Example:**
```python
from frontend.utils.state_manager import SessionState
from datetime import datetime

session = SessionState(
    session_id="session_123",
    created_at=datetime.now(),
    subject_name="John Doe",
    height=170.0,
    weight=70.0
)
```

---

## Event Handlers

### Fitting Pipeline

Custom event handler for model fitting:

```python
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
) -> Tuple:
    """
    Handle the fit model button click

    Returns:
        Tuple of (model_viewer, measurement_display, status_message,
                  export_model_button, export_params_button,
                  export_report_button, progress)
    """
    # Implementation here
    pass
```

### Clear All

Event handler for clearing interface:

```python
def handle_clear_all() -> Tuple:
    """
    Clear all inputs and reset the interface

    Returns:
        Tuple of reset values for all components
    """
    # Implementation here
    pass
```

---

## Custom CSS Classes

Available CSS classes for styling:

- `.status-success`: Green text for success
- `.status-processing`: Yellow text for processing
- `.status-error`: Red text for errors
- `.measurement-table`: Table styling
- `#upload-area`: Upload area styling
- `#progress-container`: Progress container
- `#control-column`: Left control column
- `#viewer-column`: Right viewer column

**Example:**
```python
custom_css = """
.status-success { color: #28a745; font-weight: bold; }
#upload-area { border: 2px dashed #007bff; }
"""

demo = gr.Blocks(css=custom_css)
```
