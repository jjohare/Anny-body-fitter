# Frontend Development Guide

## Architecture Overview

The Anny Body Fitter frontend is built using **Gradio** for rapid development and easy integration with the existing Anny model.

### Technology Stack
- **Gradio 4.x**: Web UI framework
- **PyTorch**: Backend model processing
- **Trimesh**: 3D mesh manipulation
- **Pandas**: Data handling for measurements
- **PIL/Pillow**: Image processing

## Project Structure

```
src/frontend/
├── __init__.py              # Package initialization
├── app.py                   # Main Gradio application
├── components/              # UI components
│   ├── __init__.py
│   ├── photo_upload.py      # Photo upload with drag-drop
│   ├── subject_form.py      # Subject metadata form
│   ├── model_viewer.py      # 3D model viewer
│   ├── progress_tracker.py  # Progress indicators
│   └── measurement_display.py  # Measurement comparison
└── utils/                   # Utility modules
    ├── __init__.py
    └── state_manager.py     # Session state management

tests/test_frontend/
├── __init__.py
├── test_components.py       # Component unit tests
└── test_app.py              # Integration tests
```

## Component Architecture

### 1. Photo Upload Component (`photo_upload.py`)

**Features:**
- Multi-file drag-and-drop upload
- Image preview gallery
- File validation (size, format)
- Photo count display

**API:**
```python
from frontend.components.photo_upload import create_photo_upload_component

# Returns: (upload_component, gallery_component)
upload, gallery = create_photo_upload_component()
```

### 2. Subject Form Component (`subject_form.py`)

**Features:**
- Required fields: name, DOB, gender, height, weight
- Optional detailed measurements
- Input validation
- Age calculation from DOB

**API:**
```python
from frontend.components.subject_form import create_subject_form_component

# Returns: tuple of form components
form_components = create_subject_form_component()
# (name, dob, gender, height, weight, chest, waist, hips)
```

### 3. Model Viewer Component (`model_viewer.py`)

**Features:**
- Interactive 3D visualization using Gradio Model3D
- Display controls (wireframe, measurements, skeleton)
- View presets (front, side, back, top)
- GLB export functionality

**API:**
```python
from frontend.components.model_viewer import (
    create_model_viewer_component,
    export_model_to_glb
)

viewer, controls = create_model_viewer_component()
glb_path = export_model_to_glb(vertices, faces)
```

### 4. Progress Tracker (`progress_tracker.py`)

**Features:**
- Real-time progress updates
- Step-by-step status display
- Progress bar with percentage
- Status icons (pending, processing, success, error)

**API:**
```python
from frontend.components.progress_tracker import (
    create_progress_tracker_component,
    update_step_status
)

progress = create_progress_tracker_component()
status_md = update_step_status("optimization", "success", "Completed in 2.3s")
```

### 5. Measurement Display (`measurement_display.py`)

**Features:**
- Comparison table (input vs. fitted)
- Accuracy percentages
- Summary statistics
- Anthropometric charts (planned)

**API:**
```python
from frontend.components.measurement_display import (
    create_measurement_display_component,
    format_measurements_table,
    calculate_measurement_statistics
)

display = create_measurement_display_component()
df = format_measurements_table(input_meas, fitted_meas)
stats = calculate_measurement_statistics(input_meas, fitted_meas)
```

## State Management

The `StateManager` class handles session state across Gradio interactions:

```python
from frontend.utils.state_manager import StateManager, SessionState

manager = StateManager()

# Create session
session = manager.create_session("session_123")

# Update session
manager.update_session(
    status="processing",
    progress=0.5,
    current_step="optimization"
)

# Get session
session = manager.get_session("session_123")

# Save/load session
manager.save_session("session_123", "session_data.json")
manager.load_session("session_data.json")
```

## Running the Frontend

### Development Mode

```bash
# Install dependencies
pip install -e ".[frontend,dev]"

# Run the application
python -m frontend.app

# Or with custom settings
python -m frontend.app \
    --server_name 0.0.0.0 \
    --server_port 7860 \
    --share
```

### Production Deployment

```bash
# Using Gradio's built-in sharing
python -m frontend.app --share

# Or deploy to Hugging Face Spaces
# See: https://huggingface.co/docs/hub/spaces-sdks-gradio
```

## Testing

### Run Tests

```bash
# Run all frontend tests
pytest tests/test_frontend/ -v

# Run with coverage
pytest tests/test_frontend/ --cov=src/frontend --cov-report=html

# Run specific test file
pytest tests/test_frontend/test_components.py -v
```

### Test Structure

```python
# tests/test_frontend/test_components.py
class TestPhotoUpload:
    def test_validate_photos_empty(self):
        """Test validation with no photos"""
        is_valid, message = validate_photos([])
        assert not is_valid

    def test_validate_photos_valid(self):
        """Test validation with multiple photos"""
        photos = ['photo1.jpg', 'photo2.jpg']
        is_valid, message = validate_photos(photos)
        assert is_valid
```

## Customization

### Custom CSS

Add custom styling in `app.py`:

```python
custom_css = """
#upload-area {
    border: 2px dashed #007bff;
    border-radius: 12px;
}
.measurement-table {
    font-family: 'Monaco', monospace;
}
"""

demo = gr.Blocks(css=custom_css)
```

### Custom Theme

```python
import gradio as gr

demo = gr.Blocks(
    theme=gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="green"
    )
)
```

### Adding New Components

1. Create component file in `src/frontend/components/`
2. Implement creation function
3. Add validation/helper functions
4. Wire up in `app.py`
5. Add tests in `tests/test_frontend/`

Example:
```python
# src/frontend/components/custom_widget.py
import gradio as gr

def create_custom_widget():
    with gr.Column():
        widget = gr.Textbox(label="Custom Widget")
        button = gr.Button("Submit")

    return widget, button
```

## Integration with Backend

### Calling Fitting Pipeline

```python
from fitting.pipeline import FittingPipeline

def handle_fit_model(photos, subject_info, options):
    # Initialize pipeline
    pipeline = FittingPipeline(
        model_type="fullbody",
        optimization_iterations=options["iterations"]
    )

    # Process photos
    results = pipeline.fit(
        photos=photos,
        subject_info=subject_info,
        callbacks=[progress_callback]
    )

    return results
```

### Progress Callbacks

```python
def progress_callback(step, progress, message):
    """Called during fitting for progress updates"""
    print(f"[{step}] {progress*100:.1f}% - {message}")

    # Update Gradio components
    gr.update(value=progress)
```

## Performance Optimization

### Image Preprocessing

```python
from PIL import Image

def preprocess_photo(photo_path, max_size=1024):
    """Resize large images before processing"""
    img = Image.open(photo_path)

    if max(img.size) > max_size:
        img.thumbnail((max_size, max_size), Image.LANCZOS)

    return img
```

### Lazy Loading

```python
# Load heavy models only when needed
def lazy_load_model():
    global model
    if model is None:
        model = create_fullbody_model()
    return model
```

### Caching

```python
import functools

@functools.lru_cache(maxsize=128)
def compute_measurements(vertices_hash):
    """Cache measurement computations"""
    return measurements
```

## Troubleshooting

### Common Issues

**Gradio version conflicts:**
```bash
pip install --upgrade gradio>=4.0.0
```

**Import errors:**
```bash
# Ensure src is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/Anny-body-fitter/src"
```

**3D model not rendering:**
- Check GLB export is valid
- Verify camera position settings
- Test with smaller models first

### Debug Mode

```python
# Enable Gradio debug mode
demo.launch(debug=True)
```

## Future Enhancements

### Planned Features
- [ ] Real-time photo capture via webcam
- [ ] Multi-person batch processing
- [ ] Virtual try-on integration
- [ ] Anthropometric percentile charts
- [ ] Video input support
- [ ] Mobile-optimized UI
- [ ] Collaborative editing
- [ ] Cloud storage integration

### React Alternative

For more customized UI, consider React + Three.js:

```bash
# Frontend structure for React version
frontend-react/
├── src/
│   ├── components/
│   │   ├── PhotoUpload.tsx
│   │   ├── SubjectForm.tsx
│   │   └── ModelViewer.tsx
│   ├── hooks/
│   │   └── useModelFitting.ts
│   └── App.tsx
└── package.json
```

## Resources

- [Gradio Documentation](https://www.gradio.app/docs)
- [Gradio Custom Components](https://www.gradio.app/custom-components)
- [Trimesh Documentation](https://trimsh.org/)
- [Three.js (alternative)](https://threejs.org/)
