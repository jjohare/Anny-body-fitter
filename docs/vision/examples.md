# Vision Module Examples

This document provides practical examples for using the Anny vision module.

## Example 1: Basic Single Image Processing

```python
import numpy as np
from PIL import Image
from anny.vision import LandmarkDetector, MeasurementExtractor

# Load image
image = np.array(Image.open('person.jpg'))

# Detect landmarks
detector = LandmarkDetector(model_complexity=1)
result = detector.detect(image)

if result:
    print(f"Detected {len(result.landmarks)} landmarks")
    print(f"Confidence: {result.overall_confidence:.2%}")

    # Extract measurements
    extractor = MeasurementExtractor()
    measurements = extractor.extract_all(result)

    print(f"\nBody Measurements:")
    print(f"  Height: {measurements.height:.2f}m ({measurements.height*100:.1f}cm)")
    print(f"  Shoulder Width: {measurements.shoulder_width:.2f}m")
    print(f"  Left Arm: {measurements.left_arm_length:.2f}m")
    print(f"  Right Arm: {measurements.right_arm_length:.2f}m")
    print(f"  Left Leg: {measurements.left_leg_length:.2f}m")
    print(f"  Right Leg: {measurements.right_leg_length:.2f}m")
```

## Example 2: Batch Processing Multiple Images

```python
from pathlib import Path
from anny.vision import ImagePreprocessor, LandmarkDetector

# Get all images in directory
image_dir = Path('images/')
image_paths = list(image_dir.glob('*.jpg'))

# Initialize
preprocessor = ImagePreprocessor()
detector = LandmarkDetector()

# Process all images
results = []
for path in image_paths:
    img = np.array(Image.open(path))

    # Preprocess
    processed, _ = preprocessor.preprocess(img)

    # Detect
    result = detector.detect(processed)

    if result:
        results.append({
            'path': path.name,
            'confidence': result.overall_confidence,
            'landmarks': result.landmarks
        })

# Print summary
print(f"Successfully processed {len(results)}/{len(image_paths)} images")
for r in results:
    print(f"  {r['path']}: {r['confidence']:.2%} confidence")
```

## Example 3: Multi-View Fusion with Validation

```python
from anny.vision import (
    ImagePreprocessor,
    LandmarkDetector,
    MeasurementExtractor,
    MultiViewFusion
)

def process_multi_view(front_path, side_path, back_path):
    """Process three views and fuse measurements."""

    # Initialize
    preprocessor = ImagePreprocessor(target_size=(640, 480))
    detector = LandmarkDetector(min_detection_confidence=0.5)
    extractor = MeasurementExtractor(use_world_landmarks=True)
    fusion = MultiViewFusion(
        fusion_method='adaptive',
        outlier_rejection=True
    )

    # Load images
    images = {
        'front': np.array(Image.open(front_path)),
        'side': np.array(Image.open(side_path)),
        'back': np.array(Image.open(back_path))
    }

    # Process each view
    measurements = []
    view_info = []

    for view_name, img in images.items():
        # Preprocess
        try:
            processed, metadata = preprocessor.preprocess(img, validate=True)
        except ValueError as e:
            print(f"Skipping {view_name}: {e}")
            continue

        # Detect landmarks
        result = detector.detect(processed)

        if result is None:
            print(f"No landmarks in {view_name}")
            continue

        if result.overall_confidence < 0.5:
            print(f"Low confidence in {view_name}: {result.overall_confidence:.2%}")
            continue

        # Extract measurements
        measurement = extractor.extract_all(result)
        measurements.append(measurement)

        view_info.append({
            'name': view_name,
            'confidence': result.overall_confidence,
            'resolution': metadata['original_shape']
        })

    # Validate we have enough views
    if len(measurements) < 2:
        raise ValueError(f"Insufficient valid views: {len(measurements)}/3")

    # Fuse measurements
    fused = fusion.fuse_measurements(measurements)

    # Get statistics
    stats = fusion.get_measurement_statistics(fused)

    return {
        'measurements': fused.measurements,
        'statistics': stats,
        'views': view_info,
        'fusion_method': fused.fusion_method
    }

# Usage
try:
    result = process_multi_view('front.jpg', 'side.jpg', 'back.jpg')

    print(f"\nFused Measurements ({result['fusion_method']}):")
    print(f"  Height: {result['measurements'].height:.2f}m ± {result['statistics']['height']['std_dev']:.3f}m")
    print(f"  Shoulder Width: {result['measurements'].shoulder_width:.3f}m")
    print(f"  Overall Confidence: {result['measurements'].overall_confidence:.2%}")

    print(f"\nViews Used:")
    for view in result['views']:
        print(f"  {view['name']}: {view['confidence']:.2%} confidence")

except ValueError as e:
    print(f"Error: {e}")
```

## Example 4: Real-time Webcam Processing

```python
import cv2
from anny.vision import LandmarkDetector, MeasurementExtractor

def webcam_measurement():
    """Real-time body measurement from webcam."""

    detector = LandmarkDetector(
        model_complexity=0,  # Use lite model for speed
        static_image_mode=False  # Video mode
    )
    extractor = MeasurementExtractor()

    cap = cv2.VideoCapture(0)

    print("Press 'c' to capture, 'q' to quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detect landmarks
        result = detector.detect(rgb_frame)

        if result:
            # Draw landmarks
            for i, landmark in enumerate(result.landmarks):
                x = int(landmark[0] * frame.shape[1])
                y = int(landmark[1] * frame.shape[0])
                cv2.circle(frame, (x, y), 3, (0, 255, 0), -1)

            # Show confidence
            cv2.putText(
                frame,
                f"Confidence: {result.overall_confidence:.2%}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

        cv2.imshow('Body Landmarks', frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('c') and result:
            # Capture and measure
            measurements = extractor.extract_all(result)
            print(f"\nMeasurements captured:")
            print(f"  Height: {measurements.height:.2f}m")
            print(f"  Shoulder Width: {measurements.shoulder_width:.3f}m")

        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Run
webcam_measurement()
```

## Example 5: Integration with Anny Body Model

```python
import torch
from anny import FullModel
from anny.vision import (
    ImagePreprocessor,
    LandmarkDetector,
    MeasurementExtractor
)

def fit_anny_to_image(image_path, output_path='fitted_model.obj'):
    """
    Fit Anny body model to image measurements.

    Args:
        image_path: Path to input image
        output_path: Path to save fitted mesh
    """

    # Extract measurements from image
    image = np.array(Image.open(image_path))

    preprocessor = ImagePreprocessor()
    detector = LandmarkDetector()
    extractor = MeasurementExtractor()

    processed, _ = preprocessor.preprocess(image)
    result = detector.detect(processed)

    if result is None:
        raise ValueError("No landmarks detected")

    measurements = extractor.extract_all(result)

    # Initialize Anny model
    model = FullModel()

    # Target measurements (convert to meters)
    target_height = measurements.height
    target_waist = measurements.waist_circumference

    # Optimize Anny parameters to match measurements
    # (This is a simplified example - full optimization would be more complex)

    from anny import Anthropometry

    anthropometry = Anthropometry(model)

    # Initial random parameters
    params = torch.randn(1, model.shape_space_dim)
    params.requires_grad = True

    optimizer = torch.optim.Adam([params], lr=0.01)

    for iteration in range(100):
        optimizer.zero_grad()

        # Generate mesh
        vertices = model(params)

        # Compute current measurements
        current_height = anthropometry.height(vertices)
        current_waist = anthropometry.waist_circumference(vertices)

        # Loss
        loss = (
            (current_height - target_height) ** 2 +
            (current_waist - target_waist) ** 2
        )

        loss.backward()
        optimizer.step()

        if iteration % 10 == 0:
            print(f"Iter {iteration}: Loss = {loss.item():.4f}")

    # Save fitted model
    final_vertices = model(params).detach()

    # Export to OBJ (simplified)
    print(f"Fitted model saved to {output_path}")
    print(f"  Target height: {target_height:.2f}m")
    print(f"  Final height: {current_height.item():.2f}m")
    print(f"  Target waist: {target_waist:.2f}m")
    print(f"  Final waist: {current_waist.item():.2f}m")

    return final_vertices

# Usage
fitted = fit_anny_to_image('person.jpg')
```

## Example 6: Confidence Filtering and Quality Control

```python
from anny.vision import LandmarkDetector, MeasurementExtractor

def measure_with_quality_check(image, min_overall_conf=0.7, min_landmark_conf=0.6):
    """
    Extract measurements with quality checks.

    Args:
        image: Input image
        min_overall_conf: Minimum overall confidence
        min_landmark_conf: Minimum per-landmark confidence

    Returns:
        Measurements dict or None if quality too low
    """

    detector = LandmarkDetector()
    extractor = MeasurementExtractor(min_confidence=min_landmark_conf)

    # Detect
    result = detector.detect(image)

    if result is None:
        return {'error': 'No landmarks detected'}

    # Check overall confidence
    if result.overall_confidence < min_overall_conf:
        return {
            'error': 'Low confidence',
            'confidence': result.overall_confidence,
            'threshold': min_overall_conf
        }

    # Filter low confidence landmarks
    filtered = detector.filter_low_confidence(result, min_confidence=min_landmark_conf)

    # Extract measurements
    measurements = extractor.extract_all(filtered)

    # Check measurement confidence
    low_conf_measurements = [
        name for name, conf in measurements.confidence_scores.items()
        if conf < min_landmark_conf
    ]

    return {
        'measurements': measurements,
        'overall_confidence': result.overall_confidence,
        'low_confidence_measurements': low_conf_measurements,
        'quality': 'high' if not low_conf_measurements else 'medium'
    }

# Usage
image = np.array(Image.open('person.jpg'))
result = measure_with_quality_check(image)

if 'error' in result:
    print(f"Error: {result['error']}")
else:
    print(f"Quality: {result['quality']}")
    print(f"Height: {result['measurements'].height:.2f}m")
    if result['low_confidence_measurements']:
        print(f"Warning: Low confidence for {result['low_confidence_measurements']}")
```

## Example 7: Custom Measurement Extraction

```python
from anny.vision import LandmarkDetector

def extract_custom_measurements(image):
    """Extract custom body measurements."""

    detector = LandmarkDetector()
    result = detector.detect(image)

    if result is None:
        return None

    # Get specific landmarks
    nose, _, _ = detector.get_landmark_by_name(result, 'nose')
    left_shoulder, _, _ = detector.get_landmark_by_name(result, 'left_shoulder')
    right_shoulder, _, _ = detector.get_landmark_by_name(result, 'right_shoulder')
    left_hip, _, _ = detector.get_landmark_by_name(result, 'left_hip')
    right_hip, _, _ = detector.get_landmark_by_name(result, 'right_hip')

    # Custom calculations
    shoulder_center = (left_shoulder + right_shoulder) / 2
    hip_center = (left_hip + right_hip) / 2

    # Neck to hip length
    torso_length = np.linalg.norm(shoulder_center - hip_center)

    # Head length (approximate)
    head_length = np.linalg.norm(nose - shoulder_center) * 1.5

    # Aspect ratio
    shoulder_width = np.linalg.norm(left_shoulder - right_shoulder)
    hip_width = np.linalg.norm(left_hip - right_hip)
    waist_hip_ratio = shoulder_width / hip_width if hip_width > 0 else 0

    return {
        'torso_length': torso_length,
        'head_length': head_length,
        'shoulder_width': shoulder_width,
        'hip_width': hip_width,
        'waist_hip_ratio': waist_hip_ratio
    }

# Usage
image = np.array(Image.open('person.jpg'))
custom_measurements = extract_custom_measurements(image)

if custom_measurements:
    print("Custom Measurements:")
    for name, value in custom_measurements.items():
        print(f"  {name}: {value:.3f}")
```

## Tips and Best Practices

1. **Always validate input images** before processing
2. **Use multi-view fusion** when accuracy is critical
3. **Check confidence scores** before using measurements
4. **Process images in batches** for efficiency
5. **Handle errors gracefully** with try-except blocks
6. **Cache detectors** - don't reinitialize for every image
7. **Use appropriate model complexity** based on speed/accuracy needs
