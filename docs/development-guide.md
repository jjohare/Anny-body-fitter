# Anny Body Fitter - Development Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Development Environment](#development-environment)
3. [Project Structure](#project-structure)
4. [Coding Standards](#coding-standards)
5. [Testing](#testing)
6. [Documentation](#documentation)
7. [Git Workflow](#git-workflow)
8. [CI/CD Pipeline](#cicd-pipeline)
9. [Deployment](#deployment)
10. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites
- Python 3.9+ (3.10 recommended)
- pip or Poetry
- Git
- PostgreSQL (optional, SQLite works for development)
- Docker (optional, for containerized development)

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Anny-body-fitter
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   # Install production dependencies
   pip install -r requirements.txt

   # Install development dependencies
   pip install -r requirements-dev.txt

   # Or install from pyproject.toml
   pip install -e ".[dev,test,docs]"
   ```

4. **Set up pre-commit hooks**
   ```bash
   pre-commit install
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. **Initialize database**
   ```bash
   # Run migrations (when available)
   alembic upgrade head

   # Or initialize manually
   python scripts/init_db.py
   ```

---

## Development Environment

### Recommended IDE Setup

#### VS Code
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length=100"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false
}
```

#### PyCharm
- Enable Black formatter: Settings → Tools → Black
- Configure pytest: Settings → Tools → Python Integrated Tools
- Enable mypy: Settings → Tools → External Tools

### Environment Variables

Create `.env` file in project root:

```bash
# Database
DATABASE_URL=sqlite:///./anny_fitter.db
# For PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost/anny_fitter

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
RELOAD=True

# Security
SECRET_KEY=your-secret-key-change-in-production
ENCRYPTION_KEY=your-encryption-key-base64-encoded

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# File Upload
MAX_UPLOAD_SIZE_MB=10
UPLOAD_DIR=/tmp/anny-uploads

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/anny-fitter.log
```

---

## Project Structure

```
Anny-body-fitter/
├── .github/
│   └── workflows/          # CI/CD pipelines
├── docs/                   # Documentation
│   ├── architecture/       # Architecture diagrams
│   ├── security/          # Security documentation
│   └── *.md               # Various documentation files
├── src/
│   ├── anny/              # Core Anny parametric model
│   │   ├── models/        # Body models (full, rigged, phenotype)
│   │   ├── skinning/      # Skinning algorithms
│   │   ├── utils/         # Utility functions
│   │   ├── vision/        # Vision processing modules
│   │   └── examples/      # Example usage
│   ├── api/               # FastAPI REST API
│   │   ├── routes/        # API endpoints
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── middleware/    # Middleware components
│   │   └── services/      # Business logic services
│   ├── database/          # Database layer
│   │   ├── models.py      # SQLAlchemy models
│   │   ├── schemas.py     # Database schemas
│   │   ├── crud.py        # CRUD operations
│   │   └── connection.py  # Database connection
│   ├── fitting/           # Fitting algorithms
│   │   ├── measurement_to_phenotype.py
│   │   ├── parameter_optimizer.py
│   │   └── confidence_weighting.py
│   ├── security/          # Security utilities
│   │   ├── encryption.py  # Data encryption
│   │   ├── validators.py  # Input validation
│   │   ├── file_scanner.py # File security
│   │   └── temp_storage.py # Secure temp storage
│   └── frontend/          # Gradio UI components
│       ├── components/    # UI components
│       └── utils/         # Frontend utilities
├── tests/                 # Test suite
│   ├── test_fitting/      # Fitting tests
│   ├── test_database.py   # Database tests
│   └── conftest.py        # Test fixtures
├── benchmarks/            # Performance benchmarks
├── scripts/               # Utility scripts
├── tutorials/             # Usage tutorials
├── .pre-commit-config.yaml
├── pyproject.toml         # Project configuration
├── requirements.txt       # Python dependencies
└── README.md
```

---

## Coding Standards

### Python Style Guide

We follow **PEP 8** with some modifications:

- **Line Length**: 100 characters (Black default)
- **Docstring Style**: Google-style docstrings
- **Import Organization**: isort with Black profile
- **Type Hints**: Required for all public APIs

### Docstring Example

```python
def calculate_body_metrics(
    height: float,
    weight: float,
    age: int,
    gender: str
) -> Dict[str, float]:
    """
    Calculate body composition metrics from basic measurements.

    Args:
        height: Height in centimeters
        weight: Weight in kilograms
        age: Age in years
        gender: Gender ('male' or 'female')

    Returns:
        Dictionary containing:
            - bmi: Body Mass Index
            - ideal_weight: Ideal weight in kg
            - body_fat_percentage: Estimated body fat %

    Raises:
        ValueError: If inputs are outside valid ranges

    Example:
        >>> metrics = calculate_body_metrics(175, 70, 30, 'male')
        >>> print(metrics['bmi'])
        22.86
    """
    # Implementation
    pass
```

### Type Hints

```python
from typing import List, Dict, Optional, Union, Tuple
from pathlib import Path

# Function signatures
def process_image(
    image_path: Path,
    config: Optional[Dict[str, Any]] = None
) -> Tuple[np.ndarray, Dict[str, float]]:
    pass

# Class attributes
class Subject:
    name: str
    age: int
    measurements: List[float]
    metadata: Optional[Dict[str, Any]] = None
```

### Naming Conventions

- **Variables**: `snake_case`
- **Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`
- **Modules**: `lowercase` or `snake_case`

```python
# Good
class SubjectService:
    MAX_RETRY_ATTEMPTS = 3

    def __init__(self):
        self._connection_pool = None

    def create_subject(self, name: str) -> Subject:
        pass

    def _validate_input(self, data: dict) -> bool:
        pass

# Bad
class subjectService:  # Wrong case
    maxRetryAttempts = 3  # Wrong case

    def CreateSubject(self, name):  # Wrong case, no types
        pass
```

### Error Handling

```python
# Use specific exceptions
class ValidationError(Exception):
    """Raised when input validation fails."""
    pass

class DatabaseError(Exception):
    """Raised when database operation fails."""
    pass

# Handle exceptions appropriately
def save_subject(subject: Subject) -> None:
    try:
        db.session.add(subject)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Database integrity error: {e}")
        raise DatabaseError(f"Failed to save subject: {e}")
    except Exception as e:
        db.session.rollback()
        logger.exception("Unexpected error saving subject")
        raise
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate log levels
logger.debug("Detailed information for debugging")
logger.info("General informational messages")
logger.warning("Warning messages for potential issues")
logger.error("Error messages for failures")
logger.critical("Critical errors requiring immediate attention")

# Include context
logger.info(f"Processing subject {subject_id} with {len(photos)} photos")
logger.error(f"Failed to process image {image_path}: {error}", exc_info=True)
```

---

## Testing

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── test_api/
│   ├── test_subjects.py     # Subject API tests
│   └── test_fitting.py      # Fitting API tests
├── test_database/
│   ├── test_models.py       # Model tests
│   └── test_crud.py         # CRUD tests
├── test_fitting/
│   ├── test_measurement_to_phenotype.py
│   └── test_integration.py
└── test_security/
    ├── test_validation.py
    └── test_encryption.py
```

### Writing Tests

#### Unit Tests

```python
import pytest
from src.fitting.measurement_to_phenotype import MeasurementToPhenotype

class TestMeasurementToPhenotype:
    """Test suite for measurement to phenotype mapping."""

    @pytest.fixture
    def mapper(self, mock_model):
        """Create mapper instance with mock model."""
        return MeasurementToPhenotype(mock_model)

    def test_map_height_valid_range(self, mapper):
        """Test height mapping with valid input."""
        result = mapper.map_height(170.0, 1.70)
        assert 0.0 <= result <= 1.0
        assert isinstance(result, float)

    def test_map_height_boundary_conditions(self, mapper):
        """Test height mapping at boundaries."""
        # Test minimum
        result_min = mapper.map_height(120.0, 1.20)
        assert result_min == 0.0

        # Test maximum
        result_max = mapper.map_height(220.0, 2.20)
        assert result_max == 1.0

    @pytest.mark.parametrize("height,expected", [
        (1.50, 0.3),
        (1.70, 0.5),
        (1.90, 0.7),
    ])
    def test_map_height_parametrized(self, mapper, height, expected):
        """Test height mapping with multiple inputs."""
        result = mapper.map_height(height * 100, height)
        assert abs(result - expected) < 0.1
```

#### Integration Tests

```python
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)

@pytest.fixture
def test_subject(client):
    """Create test subject."""
    response = client.post("/api/v1/subjects", json={
        "name": "Test Subject",
        "age": 30,
        "gender": "male"
    })
    return response.json()

def test_complete_fitting_workflow(client, test_subject):
    """Test complete fitting workflow from photo to model."""
    subject_id = test_subject["id"]

    # Upload photo
    with open("tests/fixtures/test_image.jpg", "rb") as f:
        response = client.post(
            f"/api/v1/subjects/{subject_id}/photos",
            files={"file": f}
        )
    assert response.status_code == 201

    # Run fitting
    response = client.post(f"/api/v1/fit/{subject_id}")
    assert response.status_code == 200

    # Verify results
    result = response.json()
    assert "phenotype_parameters" in result
    assert "confidence_score" in result
    assert result["confidence_score"] > 0.5
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/test_fitting/test_measurement_to_phenotype.py

# Run specific test
pytest tests/test_api/test_subjects.py::test_create_subject

# Run with markers
pytest -m "not slow"  # Skip slow tests
pytest -m integration  # Only integration tests

# Run with verbose output
pytest -v

# Run with debugging
pytest --pdb  # Drop into debugger on failure
```

### Test Coverage Goals

- **Overall Coverage**: Minimum 80%
- **Critical Paths**: 95%+ coverage
- **New Code**: 90%+ coverage required

---

## Documentation

### Code Documentation

All public APIs must have docstrings:

```python
class SubjectService:
    """
    Service for managing subject/patient data.

    Handles CRUD operations, validation, and encryption
    of sensitive subject information.

    Attributes:
        db: Database connection instance
        encryptor: Encryption service for sensitive data
    """

    def __init__(self, db: Database):
        """
        Initialize subject service.

        Args:
            db: Database connection instance
        """
        self.db = db
```

### API Documentation

- FastAPI automatically generates OpenAPI documentation
- Access at `/docs` (Swagger UI) and `/redoc` (ReDoc)
- Add detailed descriptions to endpoints

```python
@router.post(
    "/subjects",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new subject",
    description="""
    Create a new subject for body fitting with the following details:

    - **name**: Required subject identifier
    - **age**: Optional age in years (0-120)
    - **gender**: Optional gender (male/female)
    - **height_cm**: Optional height in centimeters

    Returns the created subject with generated ID and timestamps.
    """,
    responses={
        201: {"description": "Subject created successfully"},
        400: {"description": "Invalid input data"},
        401: {"description": "Authentication required"}
    }
)
async def create_subject(subject: SubjectCreate):
    pass
```

### Architecture Documentation

Update architecture diagrams when making significant changes:

1. System architecture
2. Database schema
3. API flow diagrams
4. Deployment architecture

---

## Git Workflow

### Branch Naming

- `feature/feature-name` - New features
- `bugfix/bug-description` - Bug fixes
- `hotfix/critical-fix` - Production hotfixes
- `refactor/refactor-description` - Code refactoring
- `docs/documentation-update` - Documentation changes

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test additions or changes
- `chore`: Build process or auxiliary tool changes
- `perf`: Performance improvements

**Examples**:
```bash
feat(api): add subject batch creation endpoint

fix(validation): correct age range validation logic

docs: update API documentation for fitting endpoints

refactor(database): split models.py into separate files

test: add integration tests for fitting workflow
```

### Pull Request Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Make Changes and Commit**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

3. **Push to Remote**
   ```bash
   git push origin feature/new-feature
   ```

4. **Create Pull Request**
   - Clear title and description
   - Link related issues
   - Add screenshots if UI changes
   - Request reviews

5. **Address Review Comments**
   - Make requested changes
   - Push updates
   - Re-request review

6. **Merge**
   - Squash commits if many small commits
   - Delete branch after merge

### Code Review Guidelines

**As Author**:
- Self-review before requesting review
- Ensure CI passes
- Keep PRs focused and reasonably sized
- Respond to comments promptly

**As Reviewer**:
- Review within 24 hours
- Be constructive and specific
- Test locally if complex changes
- Approve when satisfied

---

## CI/CD Pipeline

### Continuous Integration

Our CI pipeline runs on every push and pull request:

1. **Linting & Formatting**
   - Black formatting check
   - isort import sorting
   - flake8 linting
   - mypy type checking
   - Ruff checks

2. **Testing**
   - pytest across Python 3.9, 3.10, 3.11
   - Coverage report generation
   - Upload to Codecov

3. **Security Scanning**
   - Bandit security checks
   - Safety dependency scanning

4. **Build**
   - Package build
   - Build artifact upload

### Pre-commit Hooks

Automatically run on `git commit`:

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

### Local Quality Checks

Run before pushing:

```bash
# Format code
black src tests benchmarks
isort src tests benchmarks

# Lint
flake8 src tests benchmarks
ruff check src tests benchmarks

# Type check
mypy src

# Security scan
bandit -r src

# Run tests
pytest --cov=src

# All checks
pre-commit run --all-files && pytest
```

---

## Deployment

### Environment Setup

**Development**:
```bash
export ENVIRONMENT=development
export DEBUG=True
export DATABASE_URL=sqlite:///./dev.db
```

**Staging**:
```bash
export ENVIRONMENT=staging
export DEBUG=False
export DATABASE_URL=postgresql://user:pass@staging-db/anny
```

**Production**:
```bash
export ENVIRONMENT=production
export DEBUG=False
export DATABASE_URL=postgresql://user:pass@prod-db/anny
export SECRET_KEY=<secure-random-key>
```

### Docker Deployment

```bash
# Build image
docker build -t anny-fitter:latest .

# Run container
docker run -d \
  --name anny-fitter \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e SECRET_KEY=... \
  anny-fitter:latest

# With docker-compose
docker-compose up -d
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Troubleshooting

### Common Issues

**Import Errors**:
```bash
# Ensure package is installed in editable mode
pip install -e .
```

**Database Connection Issues**:
```bash
# Check DATABASE_URL
echo $DATABASE_URL

# Test connection
python -c "from src.database.connection import get_db; list(get_db())"
```

**Test Failures**:
```bash
# Run with verbose output
pytest -vv

# Debug specific test
pytest --pdb tests/path/to/test.py::test_function
```

**Pre-commit Hook Failures**:
```bash
# Fix formatting issues
black src tests benchmarks
isort src tests benchmarks

# Skip hooks (not recommended)
git commit --no-verify
```

### Getting Help

1. Check existing documentation in `docs/`
2. Search closed issues on GitHub
3. Ask in team chat
4. Create new issue with:
   - Clear description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details

---

## Additional Resources

- [Anny Model Documentation](https://naver.github.io/anny/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [pytest Documentation](https://docs.pytest.org/)
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)

---

**Last Updated**: 2025-11-10
**Maintained By**: Development Team
