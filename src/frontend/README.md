# Anny Body Fitter Frontend

A Gradio-based web interface for creating personalized 3D body models from photographs.

## Features

✨ **Photo Upload**
- Drag-and-drop multi-file upload
- Image preview gallery
- Automatic validation

👤 **Subject Information**
- Required fields: name, DOB, gender, height, weight
- Optional detailed measurements for improved accuracy
- Automatic age calculation

🎨 **3D Visualization**
- Interactive model viewer with rotation and zoom
- Display options: wireframe, measurements, skeleton
- View presets: front, side, back, top

📊 **Measurement Comparison**
- Side-by-side comparison of input vs. fitted measurements
- Accuracy percentages
- Summary statistics

⚡ **Real-time Progress**
- Step-by-step processing status
- Progress bar with percentage
- Status indicators

💾 **Export Options**
- 3D Model (.glb) - for use in 3D software
- Parameters (.json) - for reconstruction
- Report (.pdf) - comprehensive fitting report

## Quick Start

### Installation

```bash
# Install with frontend dependencies
pip install -e ".[frontend]"
```

### Run the Application

```bash
# Using Python module
python -m frontend.app

# Or using the run script
./scripts/run_frontend.sh

# With custom settings
python -m frontend.app \
    --server_name 0.0.0.0 \
    --server_port 7860 \
    --share
```

The application will be available at `http://localhost:7860`

## Usage

1. **Upload Photos**: Drag and drop 2+ photos from different angles
2. **Enter Subject Info**: Fill in required fields (name, DOB, gender, height, weight)
3. **Configure Options**: Adjust quality and advanced settings
4. **Fit Model**: Click "Fit Model" and wait for processing
5. **Review Results**: Inspect 3D model and measurement comparison
6. **Export**: Download fitted model and results

## Project Structure

```
src/frontend/
├── app.py                      # Main Gradio application
├── components/
│   ├── photo_upload.py         # Photo upload component
│   ├── subject_form.py         # Subject information form
│   ├── model_viewer.py         # 3D model viewer
│   ├── progress_tracker.py     # Progress indicators
│   └── measurement_display.py  # Measurement comparison
└── utils/
    └── state_manager.py        # Session state management
```

## Development

### Run Tests

```bash
# Run all tests
pytest tests/test_frontend/ -v

# With coverage
pytest tests/test_frontend/ --cov=src/frontend --cov-report=html

# Specific test
pytest tests/test_frontend/test_components.py::TestPhotoUpload -v
```

### Code Quality

```bash
# Format code
black src/frontend/

# Lint
flake8 src/frontend/

# Type checking
mypy src/frontend/
```

## API Integration

The frontend integrates with the backend fitting pipeline:

```python
from fitting.pipeline import FittingPipeline

# Initialize pipeline
pipeline = FittingPipeline(model_type="fullbody")

# Process photos
results = pipeline.fit(
    photos=uploaded_photos,
    subject_info=subject_data,
    callbacks=[progress_callback]
)
```

## Configuration

### Environment Variables

```bash
SERVER_NAME=0.0.0.0      # Server hostname
SERVER_PORT=7860          # Server port
SHARE=false              # Enable public sharing
```

### Custom Styling

Modify CSS in `app.py`:

```python
custom_css = """
#upload-area { border: 2px dashed #007bff; }
.measurement-table { font-family: monospace; }
"""
```

## Documentation

- **User Guide**: `/docs/frontend_guide.md`
- **Development Guide**: `/docs/frontend_development.md`
- **API Reference**: `/docs/frontend_api.md`

## Technologies

- **Gradio 4.x**: Web UI framework
- **PyTorch**: Backend processing
- **Trimesh**: 3D mesh manipulation
- **Pandas**: Data handling
- **Pillow**: Image processing

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge

## Performance

- Supports photos up to 10 MB
- Recommended: 1-3 MB for optimal performance
- Processing time: 1-5 minutes depending on quality settings

## Troubleshooting

**Issue**: Dependencies not found
```bash
pip install -e ".[frontend,dev]"
```

**Issue**: Port already in use
```bash
python -m frontend.app --server_port 7861
```

**Issue**: 3D model not rendering
- Verify GLB export is valid
- Check browser console for errors
- Try with a smaller test model

## Contributing

1. Create feature branch
2. Add tests for new components
3. Update documentation
4. Submit pull request

## License

Copyright (c) 2025 NAVER Corp.
Licensed under Apache License 2.0

## Support

- GitHub Issues: https://github.com/naver/anny/issues
- Documentation: https://naver.github.io/anny/
