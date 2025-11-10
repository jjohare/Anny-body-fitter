#!/bin/bash
# Verify Code Quality Setup
# This script checks that all quality tools are properly configured

set -e

echo "========================================="
echo "Anny Body Fitter - Quality Setup Verification"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
        return 0
    else
        echo -e "${RED}✗${NC} $1 missing"
        return 1
    fi
}

check_command() {
    if command -v "$1" &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 installed"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} $1 not installed"
        return 1
    fi
}

echo "Checking Configuration Files:"
echo "-----------------------------"
check_file ".pre-commit-config.yaml"
check_file "pyproject.toml"
check_file "requirements-dev.txt"
check_file ".env.example"
check_file "Makefile"
check_file ".github/workflows/ci.yml"
check_file "CONTRIBUTING.md"
echo ""

echo "Checking Documentation:"
echo "----------------------"
check_file "docs/development-guide.md"
check_file "docs/code-review.md"
check_file "docs/QUALITY_ASSESSMENT_SUMMARY.md"
check_file "docs/FILES_CREATED.md"
echo ""

echo "Checking Installed Tools:"
echo "------------------------"
check_command "black"
check_command "isort"
check_command "flake8"
check_command "mypy"
check_command "ruff"
check_command "bandit"
check_command "pytest"
check_command "pre-commit"
echo ""

echo "Checking Pre-commit Hooks:"
echo "-------------------------"
if [ -d ".git/hooks" ] && [ -f ".git/hooks/pre-commit" ]; then
    echo -e "${GREEN}✓${NC} Pre-commit hooks installed"
else
    echo -e "${YELLOW}⚠${NC} Pre-commit hooks not installed"
    echo "  Run: pre-commit install"
fi
echo ""

echo "Testing Tool Configurations:"
echo "---------------------------"

# Test Black
if black --version &> /dev/null; then
    echo -e "${GREEN}✓${NC} Black configured"
else
    echo -e "${YELLOW}⚠${NC} Black not available"
fi

# Test isort
if isort --version &> /dev/null; then
    echo -e "${GREEN}✓${NC} isort configured"
else
    echo -e "${YELLOW}⚠${NC} isort not available"
fi

# Test pytest
if pytest --version &> /dev/null; then
    echo -e "${GREEN}✓${NC} pytest configured"
else
    echo -e "${YELLOW}⚠${NC} pytest not available"
fi

# Test mypy
if mypy --version &> /dev/null; then
    echo -e "${GREEN}✓${NC} mypy configured"
else
    echo -e "${YELLOW}⚠${NC} mypy not available"
fi

echo ""
echo "========================================="
echo "Verification Complete!"
echo "========================================="
echo ""
echo "Next Steps:"
echo "1. Install missing tools: pip install -r requirements-dev.txt"
echo "2. Install pre-commit hooks: pre-commit install"
echo "3. Run quality checks: make check"
echo "4. Run tests: make test"
echo ""
