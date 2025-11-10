# Vision Module Documentation

The Anny vision module provides computer vision capabilities for body landmark detection and measurement extraction from images.

## Features

- **Body Landmark Detection**: Detects 33 body keypoints using MediaPipe Pose
- **Measurement Extraction**: Converts landmarks to physical measurements (height, limb lengths, circumferences)
- **Multi-View Fusion**: Intelligently combines measurements from multiple images
- **Image Preprocessing**: Handles image normalization, resizing, and validation
- **High Confidence Scoring**: Provides confidence metrics for all measurements
- **Robust Error Handling**: Gracefully handles poor quality images

## Installation

Install the vision module dependencies:

```bash
pip install anny[vision]@git+https://github.com/naver/anny.git
```

This installs:
- `mediapipe>=0.10.0` - Body landmark detection
- `pillow>=10.0.0` - Image processing
- `opencv-python>=4.8.0` - Computer vision utilities

## Quick Start

### Basic Usage

```python
import numpy as np
from anny.vision import LandmarkDetector, MeasurementExtractor

# Initialize detector
detector = LandmarkDetector(
    model_complexity=1,  # 0, 1, or 2 (higher = more accurate)
    min_detection_confidence=0.5
)

# Load image (RGB format)
image = load_your_image()  # Shape: (height, width, 3)

# Detect landmarks
result = detector.detect(image)

if result is not None:
    print(f"Detected {len(result.landmarks)} landmarks")
    print(f"Overall confidence: {result.overall_confidence:.2f}")

    # Extract measurements
    extractor = MeasurementExtractor()
    measurements = extractor.extract_all(result)

    print(f"Height: {measurements.height:.2f}m")
    print(f"Shoulder width: {measurements.shoulder_width:.2f}m")
    print(f"Left arm length: {measurements.left_arm_length:.2f}m")
```

### Multi-View Fusion

Combine measurements from multiple images for improved accuracy:

```python
from anny.vision import (
    ImagePreprocessor,
    LandmarkDetector,
    MeasurementExtractor,
    MultiViewFusion
)

# Preprocess images
preprocessor = ImagePreprocessor(target_size=(640, 480))
images = [load_image_1(), load_image_2(), load_image_3()]

processed_images = []
for img in images:
    processed, metadata = preprocessor.preprocess(img)
    processed_images.append(processed)

# Detect landmarks in all images
detector = LandmarkDetector()
landmark_results = detector.detect_batch(processed_images)

# Fuse measurements
fusion = MultiViewFusion(
    fusion_method='weighted_average',
    outlier_rejection=True
)
fused = fusion.fuse_from_landmarks(landmark_results)

print(f"Fused height from {fused.num_views} views: {fused.measurements.height:.2f}m")
print(f"Height variance: {fused.measurement_variance['height']:.4f}")
```

## Module Components

### 1. ImagePreprocessor

Handles image preprocessing and validation.

```python
from anny.vision import ImagePreprocessor

preprocessor = ImagePreprocessor(
    target_size=(640, 480),    # Target image size
    normalize=True,             # Normalize to [0, 1]
    min_resolution=(320, 240)   # Minimum acceptable resolution
)

# Preprocess single image
processed, metadata = preprocessor.preprocess(image)

# Batch processing
processed_batch, metadata_list = preprocessor.preprocess_batch(images)

# Convert to PyTorch tensor
tensor = preprocessor.to_tensor(processed)
```

**Features:**
- Aspect ratio preservation
- Image validation (resolution, channels, format)
- RGB conversion
- Normalization
- PyTorch tensor conversion

### 2. LandmarkDetector

Detects 33 body landmarks using MediaPipe Pose.

```python
from anny.vision import LandmarkDetector

detector = LandmarkDetector(
    model_complexity=1,              # 0 (lite), 1 (full), 2 (heavy)
    min_detection_confidence=0.5,    # Detection threshold
    static_image_mode=True,          # True for images, False for video
    enable_segmentation=False        # Generate segmentation mask
)

# Detect landmarks
result = detector.detect(image, return_world_landmarks=True)

# Get specific landmark
coords, conf, vis = detector.get_landmark_by_name(result, 'left_shoulder')

# Filter low confidence landmarks
filtered = detector.filter_low_confidence(result, min_confidence=0.7)

# Convert to pixel coordinates
pixel_coords = detector.to_pixel_coordinates(result)
```

**Landmarks (33 total):**
- Face: nose, eyes, ears, mouth
- Torso: shoulders, hips
- Arms: elbows, wrists, hands
- Legs: knees, ankles, feet

### 3. MeasurementExtractor

Converts landmarks to physical body measurements.

```python
from anny.vision import MeasurementExtractor

extractor = MeasurementExtractor(
    use_world_landmarks=True,  # Use 3D coordinates when available
    min_confidence=0.5          # Minimum landmark confidence
)

# Extract all measurements
measurements = extractor.extract_all(result)

# Extract specific measurements
height, conf = extractor.extract_height(result)
shoulder_width, conf = extractor.extract_shoulder_width(result)
left_arm, conf = extractor.extract_arm_length(result, 'left')

# Convert to dictionary
measurements_dict = extractor.to_dict(measurements)
```

**Available Measurements:**
- Height (head to heel)
- Shoulder width
- Waist circumference (estimated)
- Hip circumference (estimated)
- Chest circumference (estimated)
- Arm lengths (left/right)
- Leg lengths (left/right)
- Torso length
- Segment lengths (upper arm, forearm, thigh, shin)

### 4. MultiViewFusion

Fuses measurements from multiple views for improved accuracy.

```python
from anny.vision import MultiViewFusion

fusion = MultiViewFusion(
    fusion_method='weighted_average',  # 'weighted_average', 'median', 'max_confidence', 'adaptive'
    outlier_rejection=True,             # Reject statistical outliers
    outlier_threshold=2.0,              # Standard deviations for outlier detection
    min_views=1                         # Minimum views required
)

# Fuse measurements
fused = fusion.fuse_measurements(measurements_list)

# Get statistics
stats = fusion.get_measurement_statistics(fused)

print(f"Height: {stats['height']['value']:.2f}m")
print(f"Std dev: {stats['height']['std_dev']:.4f}m")
print(f"CV: {stats['height']['cv']:.2%}")
```

**Fusion Methods:**
- `weighted_average`: Confidence-weighted mean
- `median`: Robust to outliers
- `max_confidence`: Select best measurement
- `adaptive`: Automatically choose based on variance

## Complete Example

```python
import numpy as np
from PIL import Image
from anny.vision import (
    ImagePreprocessor,
    LandmarkDetector,
    MeasurementExtractor,
    MultiViewFusion
)

def extract_body_measurements(image_paths):
    """
    Extract body measurements from multiple images.

    Args:
        image_paths: List of paths to images

    Returns:
        Dictionary with fused measurements and statistics
    """
    # Initialize components
    preprocessor = ImagePreprocessor(
        target_size=(640, 480),
        normalize=True,
        min_resolution=(320, 240)
    )

    detector = LandmarkDetector(
        model_complexity=1,
        min_detection_confidence=0.5,
        static_image_mode=True
    )

    extractor = MeasurementExtractor(
        use_world_landmarks=True,
        min_confidence=0.5
    )

    fusion = MultiViewFusion(
        fusion_method='adaptive',
        outlier_rejection=True,
        outlier_threshold=2.0
    )

    # Load and preprocess images
    images = [np.array(Image.open(path)) for path in image_paths]
    processed_images = []

    for img in images:
        try:
            processed, metadata = preprocessor.preprocess(img, validate=True)
            processed_images.append(processed)
        except ValueError as e:
            print(f"Skipping invalid image: {e}")
            continue

    if not processed_images:
        raise ValueError("No valid images found")

    # Detect landmarks
    landmark_results = detector.detect_batch(
        processed_images,
        return_world_landmarks=True,
        skip_failed=True
    )

    # Filter out failed detections
    valid_results = [r for r in landmark_results if r is not None]

    if not valid_results:
        raise ValueError("No landmarks detected in any image")

    # Extract measurements
    measurements_list = [
        extractor.extract_all(result)
        for result in valid_results
    ]

    # Fuse measurements
    fused = fusion.fuse_measurements(measurements_list)

    # Get statistics
    stats = fusion.get_measurement_statistics(fused)

    return {
        'measurements': {
            'height': fused.measurements.height,
            'shoulder_width': fused.measurements.shoulder_width,
            'waist_circumference': fused.measurements.waist_circumference,
            'hip_circumference': fused.measurements.hip_circumference,
            'chest_circumference': fused.measurements.chest_circumference,
            'left_arm_length': fused.measurements.left_arm_length,
            'right_arm_length': fused.measurements.right_arm_length,
            'left_leg_length': fused.measurements.left_leg_length,
            'right_leg_length': fused.measurements.right_leg_length,
            'torso_length': fused.measurements.torso_length
        },
        'statistics': stats,
        'metadata': {
            'num_views': fused.num_views,
            'overall_confidence': fused.measurements.overall_confidence,
            'fusion_method': fused.fusion_method
        }
    }

# Usage
image_paths = ['front.jpg', 'side.jpg', 'back.jpg']
results = extract_body_measurements(image_paths)

print(f"Height: {results['measurements']['height']:.2f}m")
print(f"Confidence: {results['metadata']['overall_confidence']:.2%}")
print(f"Views used: {results['metadata']['num_views']}")
```

## Best Practices

### Image Quality

For best results, use images with:
- Good lighting (avoid shadows and glare)
- Full body visible (head to feet)
- Minimal occlusion
- Resolution ≥ 640x480 pixels
- Subject standing upright
- Minimal clothing (or form-fitting)

### Multiple Views

When using multi-view fusion:
- Capture 3-5 images from different angles
- Include front, side, and back views
- Maintain consistent distance from subject
- Use the same lighting conditions
- Avoid movement between captures

### Performance Optimization

For faster processing:
- Use `model_complexity=0` for speed
- Reduce target image size
- Disable segmentation if not needed
- Process images in batches
- Use GPU if available (via PyTorch)

### Error Handling

```python
from anny.vision import LandmarkDetector

detector = LandmarkDetector()

try:
    result = detector.detect(image)
    if result is None:
        print("No landmarks detected - check image quality")
    elif result.overall_confidence < 0.5:
        print("Low confidence detection - consider using different image")
    else:
        # Process measurements
        pass
except Exception as e:
    print(f"Detection failed: {e}")
```

## Troubleshooting

### No Landmarks Detected

- Check image resolution (minimum 320x240)
- Ensure full body is visible
- Improve lighting conditions
- Reduce `min_detection_confidence` threshold

### Low Confidence Measurements

- Use multiple images with multi-view fusion
- Improve image quality
- Ensure subject is centered in frame
- Use `model_complexity=2` for better accuracy

### Memory Issues

- Reduce `target_size` in preprocessor
- Process images sequentially instead of batching
- Use `model_complexity=0` (lite model)

## API Reference

See individual module documentation:
- [ImagePreprocessor](image_preprocessing.md)
- [LandmarkDetector](landmark_detector.md)
- [MeasurementExtractor](measurement_extractor.md)
- [MultiViewFusion](multi_view_fusion.md)

## Citation

If you use this vision module, please cite the Anny body model:

```bibtex
@article{anny2024,
  title={Anny: A Differentiable Human Body Model},
  author={Br{\'e}gier, Romain and others},
  journal={arXiv preprint arXiv:2511.03589},
  year={2024}
}
```

## License

Copyright (C) 2025 NAVER Corp.
Licensed under Apache License 2.0
