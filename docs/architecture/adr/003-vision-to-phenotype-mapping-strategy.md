# ADR 003: Vision-to-Phenotype Mapping Strategy

## Status
**ACCEPTED**

## Context
The core technical challenge is mapping 2D image measurements to Anny's 8 phenotype parameters:
- `gender` [0, 1]
- `age` [-0.33, 1.0]
- `height` [0, 1]
- `weight` [0, 1]
- `muscle` [0, 1]
- `proportions` [0, 1]
- `cupsize` [0, 1] (optional)
- `firmness` [0, 1] (optional)

**Challenges**:
1. **Underconstrained Problem**: 2D photos lack full 3D information
2. **Ambiguity**: Similar photos may map to different phenotypes
3. **Noisy Measurements**: Pose detection and depth estimation have errors
4. **Sparse Data**: No large dataset of photos → ground-truth phenotypes

**Requirements**:
- Produce reasonable initial phenotype estimates from photos
- Enable refinement through existing `ParametersRegressor`
- Handle cases where certain parameters are unobservable (e.g., muscle definition in loose clothing)

## Decision

### Strategy: Hybrid Analytical + Learned Mapping

We will use a **two-stage approach**:
1. **Stage 1: Analytical Mapping** - Rules-based estimation from measurements
2. **Stage 2: Regressor Refinement** - Optimize using `ParametersRegressor` with target mesh from vision

### Stage 1: Analytical Mapping (Initial Estimates)

#### 1.1 Height Parameter
**Direct Mapping** from detected body height:
```python
def map_height(measured_height_m, min_height=1.0, max_height=2.2):
    """
    Map measured height to Anny height parameter [0, 1]
    Anny height range: ~1.0m (infant) to ~2.2m (tall adult)
    """
    height_param = (measured_height_m - min_height) / (max_height - min_height)
    return np.clip(height_param, 0.0, 1.0)
```

**Rationale**: Height is directly observable and unambiguous

#### 1.2 Age Parameter
**Heuristic Mapping** from height + proportions:
```python
def estimate_age(height_m, head_to_body_ratio):
    """
    Estimate age parameter from body proportions
    Age anchors: -0.33 (newborn), 0.0 (baby), 0.33 (child), 0.67 (young), 1.0 (old)
    """
    # Newborns/babies have large heads relative to body
    if head_to_body_ratio > 0.25:
        return -0.33 if height_m < 0.6 else 0.0  # newborn or baby
    # Children have different limb proportions
    elif height_m < 1.3:
        return 0.33  # child
    # Adults: default to young unless other signals
    else:
        return 0.67  # young adult (conservative default)
```

**Fallback**: If DOB provided by user, use exact age
```python
def age_from_dob(date_of_birth):
    age_years = (datetime.now() - date_of_birth).days / 365.25
    # Map to Anny age parameter
    if age_years < 1:
        return -0.33
    elif age_years < 3:
        return 0.0
    elif age_years < 12:
        return 0.33
    elif age_years < 50:
        return 0.67
    else:
        return 1.0
```

**Rationale**: Age is ambiguous from photos alone, use conservative estimates

#### 1.3 Weight Parameter
**Proxy Mapping** from BMI estimate:
```python
def estimate_weight(bmi, gender_hint=0.5):
    """
    Map estimated BMI to weight parameter [0, 1]
    BMI ranges: Underweight <18.5, Normal 18.5-24.9, Overweight 25-29.9, Obese >30
    """
    # Normalize BMI to [0, 1] range
    # min_bmi=15 (very underweight), max_bmi=40 (very obese)
    weight_param = (bmi - 15) / (40 - 15)
    return np.clip(weight_param, 0.0, 1.0)

def estimate_bmi(waist_circ_m, height_m):
    """
    Estimate BMI from waist circumference and height
    Empirical relationship: BMI ≈ k * (waist / height)^2
    """
    k = 22.0  # Calibration constant (determined empirically)
    bmi = k * (waist_circ_m / height_m) ** 2
    return bmi
```

**Rationale**: Weight is hard to measure from photos, use BMI as proxy

#### 1.4 Muscle Parameter
**Conservative Default** with optional user input:
```python
def estimate_muscle(shoulder_width_m, waist_circ_m, user_hint=None):
    """
    Estimate muscle parameter [0, 1]
    Default: 0.5 (average muscle)
    Can be overridden by user input
    """
    if user_hint is not None:
        return user_hint

    # Heuristic: shoulder-to-waist ratio correlates with muscularity
    ratio = shoulder_width_m / waist_circ_m
    if ratio > 1.4:
        return 0.7  # muscular
    elif ratio < 1.2:
        return 0.3  # low muscle
    else:
        return 0.5  # average
```

**Rationale**: Muscle is difficult to observe under clothing, rely on user input or default

#### 1.5 Gender Parameter
**Multiple Approaches**:
```python
def estimate_gender(measurements, face_landmarks=None, user_input=None):
    """
    Estimate gender parameter [0=male, 1=female]
    Priority: user_input > measurements > default
    """
    if user_input is not None:
        return user_input

    # Heuristic from body proportions
    hip_to_waist_ratio = measurements['hip_circ'] / measurements['waist_circ']
    shoulder_to_hip_ratio = measurements['shoulder_width'] / measurements['hip_circ']

    # Females typically have higher hip-to-waist, lower shoulder-to-hip
    if hip_to_waist_ratio > 1.1 and shoulder_to_hip_ratio < 0.9:
        return 0.8  # likely female
    elif hip_to_waist_ratio < 0.95 and shoulder_to_hip_ratio > 1.0:
        return 0.2  # likely male
    else:
        return 0.5  # ambiguous, default to middle
```

**Rationale**: Gender estimation is sensitive; prefer user self-report

#### 1.6 Proportions Parameter
**Default to Ideal**:
```python
def estimate_proportions():
    """
    Default to ideal proportions unless specific deviations detected
    """
    return 0.0  # ideal proportions
```

**Rationale**: "Uncommon proportions" are rare edge cases, default to ideal

#### 1.7 Cupsize & Firmness
**Skip or Default**:
```python
def estimate_cupsize_firmness(gender_param):
    """
    These are excluded phenotypes (EXCLUDED_PHENOTYPES)
    Skip unless explicitly required
    """
    if gender_param < 0.3:
        return None, None  # Not applicable for males
    return 0.5, 0.5  # Average defaults for females
```

**Rationale**: Not critical for body shape, use defaults

### Stage 2: Regressor Refinement

**Approach**: Use analytical estimates as initialization for `ParametersRegressor`

```python
def fit_model_from_photo(photo_path):
    # Stage 1: Vision processing
    measurements = vision_pipeline(photo_path)

    # Stage 2: Analytical mapping
    initial_phenotypes = {
        'height': map_height(measurements['height']),
        'age': estimate_age(measurements['height'], measurements['head_body_ratio']),
        'weight': estimate_weight(estimate_bmi(measurements['waist_circ'], measurements['height'])),
        'muscle': estimate_muscle(measurements['shoulder_width'], measurements['waist_circ']),
        'gender': estimate_gender(measurements),
        'proportions': estimate_proportions(),
    }

    # Stage 3: Construct approximate target mesh from vision
    # (Use depth map + keypoints to create pseudo-3D mesh)
    target_vertices = reconstruct_approximate_mesh(measurements, depth_map)

    # Stage 4: Refine using ParametersRegressor
    regressor = ParametersRegressor(model=anny_model)
    pose, phenotypes, fitted_vertices = regressor(
        vertices_target=target_vertices,
        initial_phenotype_kwargs=initial_phenotypes,
        optimize_phenotypes=True,
        excluded_phenotypes=['cupsize', 'firmness'],  # Exclude non-essential
        max_n_iters=5
    )

    return pose, phenotypes, fitted_vertices
```

**Key Insight**: Analytical mapping provides good initialization, regressor refines to minimize error

### Approximate Mesh Reconstruction from Vision

**Challenge**: `ParametersRegressor` expects target vertices, but we only have 2D photos

**Solution**: Construct pseudo-3D mesh from depth map + keypoints
```python
def reconstruct_approximate_mesh(measurements, depth_map, keypoints_2d):
    """
    Create coarse 3D mesh from vision data
    Not anatomically perfect, but sufficient for regressor optimization
    """
    # 1. Lift 2D keypoints to 3D using depth map
    keypoints_3d = lift_to_3d(keypoints_2d, depth_map, camera_intrinsics)

    # 2. Fit SMPL template to keypoints (coarse alignment)
    smpl_params = fit_smpl_to_keypoints(keypoints_3d)
    smpl_mesh = smpl_model(**smpl_params)

    # 3. Refine mesh with depth map (non-rigid ICP)
    refined_mesh = align_mesh_to_depth(smpl_mesh, depth_map, silhouette_mask)

    return refined_mesh.vertices  # [V, 3] tensor
```

**Rationale**: Regressor is robust to noisy target meshes (designed for scan data)

## Alternatives Considered

### Alternative 1: End-to-End Learned Model
**Approach**: Train CNN to directly predict phenotype parameters from photos
**Rejected Reason**:
- Requires large labeled dataset (photos + ground-truth phenotypes)
- Difficult to interpret/debug predictions
- Black box approach reduces trust

### Alternative 2: Optimization from Scratch
**Approach**: Skip analytical mapping, optimize phenotypes from default values
**Rejected Reason**:
- Slower convergence (more iterations needed)
- Higher risk of local minima (e.g., stuck at wrong age)
- Wastes information from vision pipeline

### Alternative 3: User-Driven Adjustment
**Approach**: Show initial fit, let user manually adjust sliders
**Status**: Planned for Phase 2 (optional refinement UI)

## Consequences

### Positive
1. **Interpretable**: Each parameter has clear semantic meaning
2. **Robust**: Analytical priors prevent unrealistic predictions
3. **Efficient**: Good initialization reduces regressor iterations
4. **Flexible**: Easy to incorporate user-provided hints (age, gender)
5. **Extensible**: Can add learned components later without full rewrite

### Negative
1. **Heuristics**: Some mappings (age, muscle) are rough approximations
2. **Measurement Errors**: Vision pipeline errors propagate to phenotypes
3. **Ambiguity**: Multiple phenotype combinations may fit same photo

### Mitigation Strategies
1. **Uncertainty Quantification**: Provide confidence scores for each parameter
2. **Multi-Hypothesis**: Try multiple age anchors, select best (already implemented)
3. **User Feedback**: Allow manual override of auto-detected parameters (future)

## Validation Plan

### Synthetic Data Testing
1. Generate Anny meshes with known phenotypes
2. Render synthetic photos from multiple views
3. Run vision → mapping → regressor pipeline
4. Compare predicted phenotypes to ground truth

**Success Criteria**:
- Height: ±0.1 parameter error (<10cm actual height)
- Age: Correct age bracket in 80% of cases
- Weight: ±0.15 parameter error
- Gender: 95% accuracy (if self-reported available)

### Real-World Testing
1. Collect 50 photos of volunteers with measured height/weight
2. Run full pipeline
3. Compare predicted vs measured anthropometry

**Success Criteria**:
- Height error: <3cm
- Weight error: <5kg (or 10% of actual weight)

## Future Enhancements (Phase 2)

1. **Learned Correction Model**: Train lightweight MLP to correct analytical estimates
   ```python
   corrected_phenotypes = correction_mlp(initial_phenotypes, vision_features)
   ```

2. **Multi-View Fusion**: Use multiple photos to resolve ambiguity
   ```python
   phenotypes = fuse_multi_view([phenotypes_front, phenotypes_side, phenotypes_back])
   ```

3. **Temporal Consistency**: For video input, enforce smooth parameter changes

4. **User Calibration**: Learn user-specific correction factors from feedback

## References
- Anny Phenotype Parameters: `/src/anny/models/phenotype.py`
- ParametersRegressor: `/src/anny/parameters_regressor.py`
- Anthropometry Module: `/src/anny/anthropometry.py`

## Revision History
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-10 | Architecture Team | Initial decision |
