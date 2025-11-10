# Anny Body Fitter - Test Suite

Comprehensive test suite using **London School TDD** methodology with mock-based testing.

## Test Organization

```
tests/
├── conftest.py              # Shared fixtures and pytest configuration
├── pytest.ini               # Pytest settings
├── unit/                    # Unit tests with mocked dependencies
│   ├── test_anthropometry.py
│   ├── test_parameters_regressor.py
│   └── test_model_integration.py
├── integration/             # Integration tests
│   └── test_end_to_end_fitting.py
├── mocks/                   # Mock implementations
│   └── mock_vision.py
└── fixtures/                # Test data and fixtures
    └── README.md

```

## Running Tests

### Run all tests
```bash
pytest
```

### Run unit tests only
```bash
pytest -m unit
```

### Run integration tests
```bash
pytest -m integration
```

### Run with coverage
```bash
pytest --cov=src/anny --cov-report=html
```

### Run specific test file
```bash
pytest tests/unit/test_anthropometry.py
```

### Run tests matching pattern
```bash
pytest -k "test_should_calculate"
```

## Test Categories

### Unit Tests (`-m unit`)
- Fast execution (< 100ms per test)
- Mock all external dependencies
- Test individual components in isolation
- High coverage of edge cases

### Integration Tests (`-m integration`)
- Test component interactions
- May use real model files
- Slower execution (1-5s per test)
- Verify end-to-end workflows

### Performance Tests (`-m performance`)
- Benchmark execution time
- Memory usage profiling
- Scalability testing

## Writing Tests

### London School TDD Principles

1. **Test Behavior, Not Implementation**
   ```python
   def test_should_calculate_height_from_vertex_range(self):
       """Test describes WHAT, not HOW"""
       # Arrange
       vertices = create_test_vertices()

       # Act
       height = anthropometry.height(vertices)

       # Assert
       assert height == expected_height
   ```

2. **Mock External Dependencies**
   ```python
   @patch('anny.models.full_model.load_data')
   def test_should_load_from_cache(self, mock_load_data):
       mock_load_data.return_value = {...}
       # Test behavior without real file I/O
   ```

3. **Clear Test Names**
   ```python
   # Good
   def test_should_raise_error_when_waist_vertices_missing(self):

   # Bad
   def test_init_error(self):
   ```

4. **One Assertion Per Test** (when practical)
   Each test should verify one specific behavior.

### Test Structure (Arrange-Act-Assert)

```python
def test_should_do_something(self, fixtures):
    # Arrange: Set up test data and mocks
    input_data = create_test_input()
    expected_output = calculate_expected()

    # Act: Execute the code under test
    result = function_under_test(input_data)

    # Assert: Verify behavior
    assert result == expected_output
```

## Fixtures

### Available Fixtures (see `conftest.py`)

- `mock_model` - Mocked Anny model with essential attributes
- `sample_vertices` - Sample vertex data for testing
- `sample_phenotype_params` - Sample phenotype parameters
- `sample_pose_parameters` - Sample pose parameters (identity)
- `mock_cv_detector` - Mocked computer vision landmark detector
- `mock_database_connection` - Mocked database for persistence tests
- `anthropometry_test_data` - Test data for anthropometry calculations
- `device`, `dtype`, `batch_size` - Common test parameters

### Using Fixtures

```python
def test_with_fixtures(mock_model, sample_vertices):
    anthropometry = Anthropometry(mock_model)
    height = anthropometry.height(sample_vertices)
    assert height.shape[0] == sample_vertices.shape[0]
```

## Test Coverage Goals

- **Statements**: > 80%
- **Branches**: > 75%
- **Functions**: > 80%
- **Lines**: > 80%

## Continuous Integration

Tests run automatically on:
- Push to main branch
- Pull requests
- Nightly builds

### CI Requirements
- All unit tests must pass
- Integration tests must pass (when model files available)
- Coverage must not decrease

## Debugging Failed Tests

### Verbose output
```bash
pytest -vv
```

### Show print statements
```bash
pytest -s
```

### Debug mode
```bash
pytest --pdb  # Drop to debugger on failure
```

### Last failed tests only
```bash
pytest --lf
```

## Performance Guidelines

- Unit tests: < 100ms each
- Integration tests: < 5s each
- Full test suite: < 60s total (without slow tests)

## Common Issues

### Import Errors
Ensure `src/` is in Python path:
```bash
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"
```

### Mock Not Resetting
Use `autouse` fixture or manual reset:
```python
@pytest.fixture(autouse=True)
def reset_mocks():
    yield
    mock_object.reset_mock()
```

### Torch Device Mismatch
Always use provided `device` fixture:
```python
def test_with_device(device):
    tensor = torch.randn(10, 3, device=device)
```

## Contributing

When adding new tests:

1. Follow naming convention: `test_should_<expected_behavior>`
2. Add appropriate markers (@pytest.mark.unit, etc.)
3. Update this README if adding new categories
4. Ensure tests are deterministic (no random seeds without fixing)
5. Mock external dependencies (files, networks, heavy computations)

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [London School TDD](http://www.growing-object-oriented-software.com/)
- [unittest.mock Guide](https://docs.python.org/3/library/unittest.mock.html)
