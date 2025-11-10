#!/usr/bin/env python3
# Anny - Vision Module Quick Start Example
# Copyright (C) 2025 NAVER Corp.
# Apache License, Version 2.0

"""
Quick start example for the Anny vision module.
This demonstrates basic usage of all major components.
"""

import numpy as np
from PIL import Image

# Import vision components
from anny.vision import (
    ImagePreprocessor,
    LandmarkDetector,
    MeasurementExtractor,
    MultiViewFusion
)


def single_image_example():
    """Process a single image and extract measurements."""
    print("=" * 60)
    print("EXAMPLE 1: Single Image Processing")
    print("=" * 60)

    # Load image (replace with your image path)
    # For this example, create a synthetic image
    image = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)

    # Step 1: Preprocess image
    print("\n1. Preprocessing image...")
    preprocessor = ImagePreprocessor(
        target_size=(640, 480),
        normalize=True,
        min_resolution=(320, 240)
    )

    try:
        processed, metadata = preprocessor.preprocess(image, validate=True)
        print(f"   ✓ Image preprocessed: {metadata['preprocessed_shape']}")
    except ValueError as e:
        print(f"   ✗ Preprocessing failed: {e}")
        return

    # Step 2: Detect landmarks
    print("\n2. Detecting body landmarks...")
    detector = LandmarkDetector(
        model_complexity=1,
        min_detection_confidence=0.5,
        static_image_mode=True
    )

    result = detector.detect(processed)

    if result is None:
        print("   ✗ No landmarks detected")
        return

    print(f"   ✓ Detected {len(result.landmarks)} landmarks")
    print(f"   ✓ Overall confidence: {result.overall_confidence:.2%}")

    # Step 3: Extract measurements
    print("\n3. Extracting body measurements...")
    extractor = MeasurementExtractor(
        use_world_landmarks=True,
        min_confidence=0.5
    )

    measurements = extractor.extract_all(result)

    print(f"   ✓ Height: {measurements.height:.2f}m ({measurements.height*100:.0f}cm)")
    print(f"   ✓ Shoulder Width: {measurements.shoulder_width:.3f}m")
    print(f"   ✓ Waist: {measurements.waist_circumference:.3f}m")
    print(f"   ✓ Hip: {measurements.hip_circumference:.3f}m")
    print(f"   ✓ Left Arm: {measurements.left_arm_length:.3f}m")
    print(f"   ✓ Right Arm: {measurements.right_arm_length:.3f}m")
    print(f"   ✓ Left Leg: {measurements.left_leg_length:.3f}m")
    print(f"   ✓ Right Leg: {measurements.right_leg_length:.3f}m")
    print(f"   ✓ Overall Confidence: {measurements.overall_confidence:.2%}")

    # Step 4: Show confidence scores
    print("\n4. Measurement confidence scores:")
    for name, conf in measurements.confidence_scores.items():
        status = "✓" if conf > 0.7 else "⚠" if conf > 0.5 else "✗"
        print(f"   {status} {name}: {conf:.2%}")


def multi_view_example():
    """Process multiple images and fuse measurements."""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 2: Multi-View Fusion")
    print("=" * 60)

    # Create synthetic images (replace with real image paths)
    images = [
        np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
        for _ in range(3)
    ]

    # Initialize components
    print("\n1. Initializing components...")
    preprocessor = ImagePreprocessor()
    detector = LandmarkDetector()
    extractor = MeasurementExtractor()
    fusion = MultiViewFusion(
        fusion_method='adaptive',
        outlier_rejection=True,
        outlier_threshold=2.0
    )
    print("   ✓ Components initialized")

    # Process each image
    print("\n2. Processing multiple views...")
    measurements_list = []

    for i, img in enumerate(images):
        # Preprocess
        processed, _ = preprocessor.preprocess(img)

        # Detect landmarks
        result = detector.detect(processed)

        if result is None:
            print(f"   ✗ View {i+1}: No landmarks detected")
            continue

        # Extract measurements
        measurement = extractor.extract_all(result)
        measurements_list.append(measurement)

        print(f"   ✓ View {i+1}: {result.overall_confidence:.2%} confidence")

    if len(measurements_list) < 2:
        print("\n   ✗ Insufficient valid views for fusion")
        return

    # Fuse measurements
    print("\n3. Fusing measurements from multiple views...")
    fused = fusion.fuse_measurements(measurements_list)

    print(f"   ✓ Fused {fused.num_views} views using '{fused.fusion_method}' method")

    # Display fused results
    print("\n4. Fused measurements:")
    print(f"   Height: {fused.measurements.height:.2f}m")
    print(f"   Shoulder Width: {fused.measurements.shoulder_width:.3f}m")
    print(f"   Overall Confidence: {fused.measurements.overall_confidence:.2%}")

    # Display statistics
    print("\n5. Measurement statistics:")
    stats = fusion.get_measurement_statistics(fused)

    for field in ['height', 'shoulder_width', 'waist_circumference']:
        if field in stats:
            s = stats[field]
            print(f"   {field}:")
            print(f"     Value: {s['value']:.3f}m")
            print(f"     Std Dev: {s['std_dev']:.4f}m")
            print(f"     CV: {s['cv']:.2%}")
            print(f"     Confidence: {s['confidence']:.2%}")


def batch_processing_example():
    """Process batch of images efficiently."""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 3: Batch Processing")
    print("=" * 60)

    # Create batch of images
    num_images = 5
    images = [
        np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        for _ in range(num_images)
    ]

    print(f"\n1. Processing batch of {num_images} images...")

    # Initialize detector
    detector = LandmarkDetector()

    # Batch detection
    results = detector.detect_batch(images, skip_failed=True)

    # Count successful detections
    successful = sum(1 for r in results if r is not None)
    failed = num_images - successful

    print(f"   ✓ Successful: {successful}/{num_images}")
    if failed > 0:
        print(f"   ✗ Failed: {failed}/{num_images}")

    # Extract measurements for successful detections
    print("\n2. Extracting measurements...")
    extractor = MeasurementExtractor()

    for i, result in enumerate(results):
        if result is not None:
            measurements = extractor.extract_all(result)
            print(f"   Image {i+1}: Height = {measurements.height:.2f}m, "
                  f"Confidence = {measurements.overall_confidence:.2%}")


def quality_control_example():
    """Demonstrate quality control and validation."""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 4: Quality Control")
    print("=" * 60)

    # Create test image
    image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

    # Initialize detector
    detector = LandmarkDetector()

    print("\n1. Detecting landmarks with quality checks...")
    result = detector.detect(image)

    if result is None:
        print("   ✗ No landmarks detected - image quality too poor")
        return

    # Check overall confidence
    print(f"   Overall confidence: {result.overall_confidence:.2%}")

    if result.overall_confidence < 0.7:
        print("   ⚠ Warning: Low overall confidence")
    else:
        print("   ✓ Good overall confidence")

    # Filter low confidence landmarks
    print("\n2. Filtering low confidence landmarks...")
    filtered = detector.filter_low_confidence(result, min_confidence=0.6)

    # Count valid landmarks
    valid_count = np.sum(~np.isnan(filtered.landmarks[:, 0]))
    print(f"   ✓ Valid landmarks: {valid_count}/33")

    # Extract measurements with confidence check
    print("\n3. Extracting measurements with quality thresholds...")
    extractor = MeasurementExtractor(min_confidence=0.6)
    measurements = extractor.extract_all(filtered)

    # Check measurement quality
    low_conf = [
        name for name, conf in measurements.confidence_scores.items()
        if conf < 0.6
    ]

    if low_conf:
        print(f"   ⚠ Low confidence measurements: {', '.join(low_conf)}")
    else:
        print("   ✓ All measurements have good confidence")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("ANNY VISION MODULE - QUICK START EXAMPLES")
    print("=" * 60)

    try:
        # Run examples
        single_image_example()
        multi_view_example()
        batch_processing_example()
        quality_control_example()

        print("\n" + "=" * 60)
        print("✓ All examples completed successfully!")
        print("=" * 60)

        # Installation reminder
        print("\nTo use with real images, ensure you have installed:")
        print("  pip install anny[vision]@git+https://github.com/naver/anny.git")

    except ImportError as e:
        print(f"\n✗ Error: {e}")
        print("\nPlease install vision dependencies:")
        print("  pip install mediapipe>=0.10.0 pillow>=10.0.0")

    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
