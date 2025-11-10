# Contributing to Anny Body Fitter

Thank you for your interest in contributing to Anny Body Fitter! This document provides guidelines and instructions for contributing.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Community](#community)

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please:
- Be respectful and constructive in all interactions
- Welcome newcomers and help them get started
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites
- Python 3.9 or higher
- Git
- Basic understanding of PyTorch and parametric body models

### Setting Up Development Environment

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR-USERNAME/Anny-body-fitter.git
   cd Anny-body-fitter
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   make install-all
   # or
   pip install -r requirements.txt -r requirements-dev.txt
   pip install -e ".[dev,test]"
   ```

4. **Install pre-commit hooks**
   ```bash
   make pre-commit-install
   ```

5. **Run tests to verify setup**
   ```bash
   make test
   ```

## Development Process

### Workflow

1. **Create an issue** describing the bug or feature
2. **Create a feature branch** from `main`
3. **Implement changes** following code standards
4. **Write tests** for new functionality
5. **Update documentation** as needed
6. **Submit pull request** for review

### Branch Naming

- `feature/descriptive-name` - New features
- `bugfix/issue-description` - Bug fixes
- `hotfix/critical-fix` - Production hotfixes
- `docs/documentation-update` - Documentation
- `refactor/improvement-description` - Code refactoring

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements

**Examples:**
```bash
feat(api): add batch subject creation endpoint

fix(validation): correct age range validation logic

docs: update API documentation for fitting endpoints

test(integration): add tests for complete fitting workflow
```

## Code Standards

### Python Style Guide

- Follow **PEP 8** with line length of 100 characters
- Use **Black** for code formatting
- Use **isort** for import sorting
- Use **Google-style docstrings**

### Type Hints

All public APIs must include type hints:

```python
from typing import Dict, List, Optional

def process_measurements(
    measurements: Dict[str, float],
    confidence: Optional[float] = None
) -> List[float]:
    """Process body measurements."""
    pass
```

### Documentation

- Add docstrings to all public functions and classes
- Include usage examples where helpful
- Update README.md for user-facing changes
- Update CHANGELOG.md for all changes

### Code Quality Tools

Before submitting, run:

```bash
# Format code
make format

# Run linters
make lint

# Type checking
make type-check

# Security scanning
make security

# All checks
make check
```

## Testing Requirements

### Writing Tests

- Place tests in `tests/` directory
- Mirror source structure: `src/module/file.py` → `tests/test_module/test_file.py`
- Use descriptive test names: `test_map_height_with_valid_input`
- Test edge cases and error conditions

### Test Example

```python
import pytest
from src.fitting.measurement_to_phenotype import MeasurementToPhenotype

class TestMeasurementToPhenotype:
    @pytest.fixture
    def mapper(self, mock_model):
        return MeasurementToPhenotype(mock_model)

    def test_map_height_valid_range(self, mapper):
        """Test height mapping with valid input."""
        result = mapper.map_height(170.0, 1.70)
        assert 0.0 <= result <= 1.0

    @pytest.mark.parametrize("height,expected", [
        (1.20, 0.0),
        (2.20, 1.0),
    ])
    def test_map_height_boundaries(self, mapper, height, expected):
        """Test height mapping at boundaries."""
        result = mapper.map_height(height * 100, height)
        assert result == expected
```

### Running Tests

```bash
# All tests
make test

# With coverage
make test-cov

# Fast (parallel)
make test-fast

# Specific test
pytest tests/test_fitting/test_measurement_to_phenotype.py::test_map_height
```

### Coverage Requirements

- Minimum 80% overall coverage
- 95%+ for critical paths
- 90%+ for new code

## Pull Request Process

### Before Submitting

1. ✅ All tests pass locally
2. ✅ Code is formatted (Black, isort)
3. ✅ Linters pass (flake8, ruff)
4. ✅ Type checking passes (mypy)
5. ✅ Security scans pass (bandit)
6. ✅ Documentation updated
7. ✅ CHANGELOG.md updated

### PR Description Template

```markdown
## Description
Brief description of the changes

## Related Issue
Fixes #123

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing performed

## Screenshots (if applicable)

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review performed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] No new warnings
```

### Review Process

1. Automated checks run (CI/CD)
2. Code review by maintainer(s)
3. Address feedback
4. Approval and merge

### After Merge

- Delete feature branch
- Update local main branch
- Close related issues

## Community

### Getting Help

- 📖 Read the [Development Guide](docs/development-guide.md)
- 💬 Ask questions in GitHub Discussions
- 🐛 Report bugs via GitHub Issues
- 💡 Suggest features via GitHub Issues

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Pull Requests**: Code contributions

### Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- GitHub contributors page
- Release notes

Thank you for contributing to Anny Body Fitter! 🎉
