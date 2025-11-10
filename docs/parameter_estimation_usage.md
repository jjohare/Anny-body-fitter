# Parameter Estimation Module - Usage Guide

## Overview

The parameter estimation module maps vision-based measurements to Anny phenotype parameters, enabling automated body model fitting from images.

## Components

### 1. MeasurementToPhenotype

Maps extracted vision measurements to Anny's phenotype parameter space.

```python
from src.fitting.measurement_to_phenotype import MeasurementToPhenotype

# Initialize with Anny model
mapper = MeasurementToPhenotype(anny_model)

# Vision measurements from image analysis
measurements = {
    'height_pixels': 1800.0,
    'reference_height_meters': 1.75,
    'shoulder_width_ratio': 0.28,
    'hip_width_ratio': 0.22,
    'leg_length_ratio': 0.52,
    'torso_length_ratio': 0.48,
    'body_composition': {
        'muscle_indicator': 0.6,
        'weight_indicator': 0.55
    },
    'estimated_age': 25,
    'estimated_gender': 'male',
    'confidence': 0.85
}

# Map to phenotype parameters
phenotypes = mapper.map_measurements(measurements)
# Result: {'gender': 0.2, 'age': 0.5, 'height': 0.6, ...}
```

### 2. ParameterOptimizer

Fine-tunes phenotype parameters using Anny's ParametersRegressor.

```python
from src.fitting.parameter_optimizer import ParameterOptimizer
from src.anny.parameters_regressor import ParametersRegressor

# Initialize regressor
regressor = ParametersRegressor(
    model=anny_model,
    max_n_iters=5,
    verbose=True
)

# Create optimizer
optimizer = ParameterOptimizer(regressor)

# Optimize parameters to fit target mesh
result = optimizer.optimize(
    target_vertices=target_mesh_vertices,
    initial_phenotypes=phenotypes,
    confidences={'gender': 0.85, 'age': 0.9, 'height': 0.8}
)

# Access results
pose = result['pose_parameters']
optimized_phenotypes = result['phenotype_kwargs']
fitted_vertices = result['vertices']
```

### 3. ConfidenceWeighting

Fuses measurements from multiple images using confidence weighting.

```python
from src.fitting.confidence_weighting import ConfidenceWeighting

weighter = ConfidenceWeighting()

# Multiple measurements from different views
multi_measurements = [
    {
        'phenotypes': phenotypes_view1,
        'confidence': 0.85
    },
    {
        'phenotypes': phenotypes_view2,
        'confidence': 0.78
    },
    {
        'phenotypes': phenotypes_view3,
        'confidence': 0.90
    }
]

# Fuse measurements
fused = weighter.fuse_measurements(
    multi_measurements,
    return_uncertainty=True
)

final_phenotypes = fused['phenotypes']
final_confidence = fused['confidence']
uncertainties = fused['uncertainty']
```

## Complete Pipeline

### Single Image Pipeline

```python
from src.fitting import (
    MeasurementToPhenotype,
    ParameterOptimizer
)
from src.anny.parameters_regressor import ParametersRegressor

# 1. Extract measurements from vision module
# (This would come from your vision analysis)
vision_measurements = extract_from_image(image)

# 2. Map to phenotype parameters
mapper = MeasurementToPhenotype(anny_model)
phenotype_estimates = mapper.map_measurements(vision_measurements)

# 3. Optimize parameters
regressor = ParametersRegressor(anny_model)
optimizer = ParameterOptimizer(regressor)

result = optimizer.optimize(
    target_vertices=target_mesh,
    initial_phenotypes=phenotype_estimates
)

# 4. Use fitted model
fitted_model = anny_model(
    pose_parameters=result['pose_parameters'],
    phenotype_kwargs=result['phenotype_kwargs']
)
```

### Multi-Image Pipeline

```python
from src.fitting import (
    MeasurementToPhenotype,
    ParameterOptimizer,
    ConfidenceWeighting
)

# 1. Process multiple images
mapper = MeasurementToPhenotype(anny_model)
all_measurements = []

for image in images:
    vision_meas = extract_from_image(image)
    phenotypes = mapper.map_measurements(vision_meas)
    all_measurements.append({
        'phenotypes': phenotypes,
        'confidence': vision_meas['confidence']
    })

# 2. Fuse measurements
weighter = ConfidenceWeighting()
fused = weighter.fuse_measurements(all_measurements)

# 3. Optimize with fused estimates
regressor = ParametersRegressor(anny_model)
optimizer = ParameterOptimizer(regressor)

result = optimizer.optimize(
    target_vertices=combined_target_mesh,
    initial_phenotypes=fused['phenotypes']
)
```

## Advanced Features

### Staged Optimization

Optimize high-confidence parameters first, then refine all parameters:

```python
result = optimizer.optimize_staged(
    target_vertices=target_mesh,
    initial_phenotypes=phenotypes,
    confidences={
        'gender': 0.9,
        'age': 0.5,  # Low confidence
        'height': 0.85
    }
)
```

### Age Anchor Search

Search over multiple age anchors for better initialization:

```python
result = optimizer.optimize_with_age_search(
    target_vertices=target_mesh,
    initial_phenotypes=phenotypes,
    age_anchors=[0.0, 0.33, 0.67, 1.0]
)
```

### Outlier Rejection

Enable outlier rejection during multi-image fusion:

```python
fused = weighter.fuse_measurements(
    multi_measurements
)

# Outlier rejection is enabled by default
# Measurements with z-score > 2.0 are filtered
```

### Uncertainty Quantification

Get uncertainty estimates for fused measurements:

```python
fused = weighter.fuse_measurements(
    multi_measurements,
    return_uncertainty=True
)

# Per-parameter uncertainties
for param, uncertainty in fused['uncertainty'].items():
    print(f"{param}: {uncertainty:.3f}")
```

## Phenotype Parameter Mapping

### Height
- **Range**: 0.0 (1.20m) to 1.0 (2.20m)
- **Source**: Pixel height + reference scale

### Gender
- **Range**: 0.0 (male) to 1.0 (female)
- **Source**: Vision-based gender estimation

### Age
- **Range**: 0.0 (newborn) to 1.0 (old)
- **Mapping**:
  - 0.0: Newborn (0-1 years)
  - 0.2: Baby (1-3 years)
  - 0.4: Child (3-12 years)
  - 0.5-0.7: Young adult (12-40 years)
  - 0.7-1.0: Old (40+ years)

### Muscle & Weight
- **Range**: 0.0 (min) to 1.0 (max)
- **Source**: Body composition indicators

### Proportions
- **Range**: 0.0 (ideal) to 1.0 (uncommon)
- **Source**: Deviation from ideal body ratios

## Integration with Vision Module

```python
# Example integration
from src.vision import ImageAnalyzer
from src.fitting import MeasurementToPhenotype

# Analyze image
analyzer = ImageAnalyzer()
vision_output = analyzer.process_image(image)

# Map to phenotypes
mapper = MeasurementToPhenotype(anny_model)
phenotypes = mapper.map_measurements(vision_output['measurements'])

# Continue with optimization...
```

## Error Handling

```python
# Handle missing measurements
phenotypes = mapper.map_measurements(
    incomplete_measurements
)
# Missing values default to 0.5 (middle range)

# Handle low confidence
if phenotypes['confidence'] < 0.5:
    # Use wider optimization bounds
    result = optimizer.optimize(
        target_vertices=target_mesh,
        initial_phenotypes=phenotypes,
        max_iterations=10  # More iterations for refinement
    )
```

## Performance Metrics

```python
# Compute fitting error
metrics = optimizer.get_fitting_error(
    predicted_vertices=result['vertices'],
    target_vertices=target_mesh
)

print(f"PVE: {metrics['pve_mm']:.2f} mm")
print(f"Max Error: {metrics['max_error_mm']:.2f} mm")
print(f"RMS Error: {metrics['rms_error_mm']:.2f} mm")
```

## Best Practices

1. **Use Multiple Images**: Fusion improves accuracy and confidence
2. **Check Confidence**: Filter low-confidence parameters from optimization
3. **Staged Optimization**: Start with high-confidence parameters
4. **Monitor Errors**: Track fitting metrics to detect issues
5. **Handle Outliers**: Enable outlier rejection with multiple measurements

## Troubleshooting

### High Fitting Error
- Check confidence scores - exclude low-confidence parameters
- Try age anchor search strategy
- Increase optimization iterations

### Inconsistent Results
- Use multi-image fusion for stability
- Enable outlier rejection
- Verify vision measurement quality

### Missing Phenotypes
- Provide default values via initial_phenotypes
- Use staged optimization to refine incrementally
