# Fitting Module

Parameter estimation module for mapping vision measurements to Anny phenotype parameters.

## Components

- **measurement_to_phenotype.py**: Maps vision measurements to phenotype parameters
- **parameter_optimizer.py**: Optimizes parameters using ParametersRegressor
- **confidence_weighting.py**: Fuses multi-image measurements with confidence weighting

## Quick Start

```python
from src.fitting import MeasurementToPhenotype, ParameterOptimizer

# Map measurements
mapper = MeasurementToPhenotype(anny_model)
phenotypes = mapper.map_measurements(vision_measurements)

# Optimize
optimizer = ParameterOptimizer(regressor)
result = optimizer.optimize(target_vertices, phenotypes)
```

See `/docs/parameter_estimation_usage.md` for complete documentation.
