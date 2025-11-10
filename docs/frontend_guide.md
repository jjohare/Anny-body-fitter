# Frontend User Guide

## Anny Body Fitter - 3D Body Model from Photos

The Anny Body Fitter frontend provides an intuitive interface for creating personalized 3D body models from photographs.

## Features

### 1. Photo Upload
- **Drag-and-drop** or click to upload multiple photos
- Supports common image formats (JPG, PNG, etc.)
- Real-time preview gallery
- Minimum 2 photos recommended (front and side views)

**Best Practices:**
- Use well-lit photos with neutral background
- Subject should wear fitted clothing or swimwear
- Capture from multiple angles (front, side, back)
- Subject should stand in neutral pose with arms slightly away from body

### 2. Subject Information Form
Required fields:
- **Name**: Subject identification
- **Date of Birth**: For age-appropriate body proportions
- **Gender**: Affects body model selection
- **Height**: In centimeters
- **Weight**: In kilograms

Optional detailed measurements (improves accuracy):
- Chest/Bust circumference
- Waist circumference
- Hip circumference

### 3. Processing Options

**Quality Settings:**
- **Fast**: Quick processing with lower accuracy
- **Balanced**: Good balance of speed and accuracy (default)
- **High Quality**: Best accuracy, slower processing

**Advanced Options:**
- **Optimization Iterations**: Number of fitting iterations (10-200)
- **Silhouette Fitting**: Use body silhouettes for better shape matching
- **Keypoint Detection**: Use pose keypoints for alignment

### 4. 3D Model Visualization

The fitted model is displayed in an interactive 3D viewer with:
- **Rotation**: Click and drag to rotate
- **Zoom**: Scroll to zoom in/out
- **Pan**: Right-click and drag to pan

**Display Options:**
- Show wireframe mesh
- Show measurement points
- Show skeleton
- Adjust lighting quality

**View Presets:**
- Front View
- Side View
- Back View
- Top View

### 5. Measurement Comparison

A detailed table shows:
- Input measurements vs. fitted model measurements
- Differences (cm)
- Accuracy percentages

**Summary Statistics:**
- Overall fitting accuracy
- Average error
- Maximum error

### 6. Export Options

Download results in multiple formats:
- **3D Model (.glb)**: Use in 3D software (Blender, Unity, etc.)
- **Parameters (.json)**: Body shape parameters for reconstruction
- **Report (.pdf)**: Comprehensive fitting report with measurements

## Usage Workflow

1. **Upload Photos**
   - Click "Select or drag photos here"
   - Upload 2+ photos from different angles
   - Verify preview in gallery

2. **Enter Subject Info**
   - Fill in name, date of birth, gender
   - Enter height and weight
   - Optionally add detailed measurements

3. **Configure Processing**
   - Select quality preset
   - Adjust advanced options if needed

4. **Fit Model**
   - Click "Fit Model" button
   - Monitor progress in real-time
   - Wait for processing to complete

5. **Review Results**
   - Inspect 3D model in viewer
   - Check measurement comparison
   - Verify fitting accuracy

6. **Export**
   - Download fitted 3D model
   - Save parameters for later use
   - Generate PDF report

## Troubleshooting

### Common Issues

**Error: "Please upload at least one photo"**
- Solution: Upload at least 2 photos before clicking "Fit Model"

**Error: "Please fill in all required subject information"**
- Solution: Ensure name, DOB, gender, height, and weight are filled in

**Poor Fitting Results**
- Try uploading more photos from different angles
- Ensure photos are well-lit and subject is visible
- Add detailed measurements (chest, waist, hips)
- Increase optimization iterations in advanced options

**Slow Processing**
- Use "Fast" quality preset
- Reduce optimization iterations
- Ensure photos are not extremely high resolution

## Technical Details

### Supported Image Formats
- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- TIFF (.tiff)

### File Size Limits
- Maximum photo size: 10 MB per file
- Recommended: 1-3 MB for optimal performance

### Browser Compatibility
- Chrome (recommended)
- Firefox
- Safari
- Edge

### System Requirements
- Modern web browser
- Stable internet connection
- Recommended: 8GB+ RAM for smooth 3D visualization

## API Access

For programmatic access, see the API documentation:
- REST API endpoint: `/api/fitting/submit`
- WebSocket for real-time progress: `/ws/fitting/{session_id}`

## Privacy & Data

- Photos are processed locally and not stored permanently
- Session data is deleted after 24 hours
- Export your results before closing the browser

## Support

For issues or questions:
- GitHub Issues: https://github.com/naver/anny/issues
- Documentation: https://naver.github.io/anny/
