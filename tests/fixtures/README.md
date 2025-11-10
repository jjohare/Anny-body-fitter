# Test Fixtures for Anny Body Fitter

This directory contains test data for the Anny Body Fitter project, including synthetic images, sample data, and expected results.

## Directory Structure

```
tests/fixtures/
├── README.md                    # This file
├── generate_test_images.py      # Script to generate synthetic test images
├── sample_data.json             # Sample subject data with measurements
├── expected_results.json        # Expected outputs for test validation
├── images/                      # Generated test images
│   ├── front_view.png
│   ├── side_view.png
│   ├── back_view.png
│   ├── three_quarter_view.png
│   └── cropped_view.png
└── real_samples/                # Optional real human images (not included)
```

## Test Images

### Synthetic Images

All synthetic images are generated using `generate_test_images.py` and are:
- **Resolution**: 640×480 pixels
- **Format**: PNG, RGB color
- **Style**: Simple geometric silhouettes with clear body landmarks

#### Available Views

1. **front_view.png**
   - Front-facing humanoid silhouette
   - Clear shoulders, hips, knees visible
   - Best for: Testing full frontal landmark detection

2. **side_view.png**
   - Profile silhouette
   - Single side of body visible
   - Best for: Testing depth/profile measurements

3. **back_view.png**
   - Rear-facing silhouette
   - Back view of shoulders, spine, hips
   - Best for: Testing back landmark detection

4. **three_quarter_view.png**
   - 3/4 angled pose
   - Asymmetric view showing more of one side
   - Best for: Testing multi-angle detection

5. **cropped_view.png**
   - Upper body only (head to mid-torso)
   - Larger scale, closer crop
   - Best for: Testing partial body detection

### Regenerating Test Images

To regenerate all synthetic test images:

```bash
# From project root
cd tests/fixtures
python generate_test_images.py
```

This will create/overwrite all 5 test images in the `images/` directory.

### Adding Real Sample Images

If you want to add real human body images for testing:

1. Download CC0/Public Domain images from:
   - [Pixabay](https://pixabay.com/) - Search "person standing" with CC0 filter
   - [Unsplash](https://unsplash.com/) - Free to use photos
   - [Pexels](https://www.pexels.com/) - Free stock photos

2. Place them in `real_samples/` directory

3. Update `sample_data.json` with corresponding metadata

4. **Important**: Ensure proper attribution if required by license

5. Update `.gitignore` if images should not be committed

## Sample Data

### sample_data.json

Contains test subject profiles with:
- Personal info (name, DOB, gender)
- Physical measurements (height, weight)
- Body measurements (circumferences, lengths)
- Notes about each test case

**Test Subjects**:
- `test_subject_1` - Standard male (175cm, 70kg)
- `test_subject_2` - Standard female (165cm, 60kg)
- `test_subject_3` - Tall athletic male (185cm, 85kg)
- `test_subject_4` - Petite female (158cm, 52kg)
- `test_subject_minimal` - Minimal data (testing required fields only)

### Usage in Tests

```python
import json

# Load sample data
with open('tests/fixtures/sample_data.json') as f:
    sample_data = json.load(f)

# Use in tests
subject = sample_data['test_subject_1']
height = subject['height_cm']  # 175.0
measurements = subject['measurements']
```

## Expected Results

### expected_results.json

Defines expected outputs for validation:

1. **Landmark Detection**
   - Expected landmark positions (x, y coordinates)
   - Tolerance ranges (±pixels)
   - Confidence thresholds
   - Per-image expectations

2. **Body Measurements**
   - Pixel measurements from images
   - Tolerance ranges
   - Height, width, depth measurements

3. **Phenotype Fitting**
   - Expected SMPL parameter ranges
   - Per-vertex error (PVE) thresholds
   - Fit quality metrics

4. **Edge Cases**
   - Missing landmark handling
   - Low confidence thresholds
   - Extreme measurement ranges

5. **Regression Thresholds**
   - Minimum success rates
   - Accuracy thresholds
   - Performance benchmarks

### Usage in Tests

```python
import json

# Load expected results
with open('tests/fixtures/expected_results.json') as f:
    expected = json.load(f)

# Validate landmark detection
front_view_landmarks = expected['landmark_detection']['front_view.png']
expected_nose = front_view_landmarks['expected_landmarks']['nose']
tolerance = expected_nose['tolerance']  # ±20 pixels

# Check if detected landmark is within tolerance
assert abs(detected_x - expected_nose['x']) <= tolerance
assert abs(detected_y - expected_nose['y']) <= tolerance
```

## Test Data Guidelines

### Image Requirements

- Images must be valid PNG or JPEG
- Resolution should be at least 640×480
- Subject should be clearly visible
- Good lighting and contrast
- Neutral background preferred

### Measurement Data

- All measurements in metric (cm, kg)
- Circumferences measured at standard body locations
- Heights/lengths measured along body axes
- Include realistic human ranges (see edge_cases in expected_results.json)

### Expected Results Format

- Pixel coordinates: (x, y) from top-left origin
- Tolerances: absolute pixel values
- Confidence: 0.0 to 1.0 range
- Errors: specified in appropriate units (cm, px, %)

## Testing Best Practices

1. **Always validate against expected results**
   - Don't hardcode values in tests
   - Use expected_results.json as single source of truth

2. **Include tolerance checks**
   - Exact matches are fragile
   - Use specified tolerance ranges

3. **Test multiple views**
   - Front, side, back, angled views
   - Cropped and full-body images

4. **Test edge cases**
   - Missing landmarks
   - Low confidence detections
   - Extreme measurements
   - Minimal data subjects

5. **Regenerate synthetic images**
   - After changing test requirements
   - To ensure consistency
   - When adding new test scenarios

## Maintenance

### When to Update Test Data

- **New features**: Add corresponding test cases and expected results
- **Algorithm changes**: Regenerate expected results with new baselines
- **Bug fixes**: Add regression test cases
- **Performance improvements**: Update threshold expectations

### Version Control

- Commit synthetic image generation script: ✅
- Commit sample_data.json: ✅
- Commit expected_results.json: ✅
- Commit generated synthetic images: ✅ (small file sizes)
- Commit real sample images: ⚠️ (check license, consider .gitignore)

## Troubleshooting

### Images not generating

```bash
# Ensure PIL is installed
pip install Pillow

# Check script permissions
chmod +x generate_test_images.py

# Run directly
python tests/fixtures/generate_test_images.py
```

### Invalid image format errors

```python
from PIL import Image

# Verify image
img = Image.open('tests/fixtures/images/front_view.png')
print(f"Format: {img.format}, Size: {img.size}, Mode: {img.mode}")
```

### JSON parsing errors

```bash
# Validate JSON syntax
python -m json.tool tests/fixtures/sample_data.json
python -m json.tool tests/fixtures/expected_results.json
```

## License

Test fixtures are part of the Anny Body Fitter project.

- Synthetic images: Generated, no copyright restrictions
- Real sample images: See individual image attributions in `real_samples/ATTRIBUTIONS.md` (if applicable)

## References

- SMPL model: http://smpl.is.tue.mpg.de/
- MediaPipe landmarks: https://google.github.io/mediapipe/solutions/pose.html
- Test data best practices: https://testing.googleblog.com/
