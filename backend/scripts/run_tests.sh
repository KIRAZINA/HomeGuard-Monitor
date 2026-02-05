#!/bin/bash

# Test runner script for HomeGuard Monitor backend

set -e

echo "🧪 Running HomeGuard Monitor Backend Tests"
echo "======================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
pip install -r requirements-test.txt

# Run database migrations (for test database)
echo "Setting up test database..."
export DATABASE_URL="sqlite+aiosqlite:///:memory:"

# Run tests
echo "Running tests..."
if [ "$1" = "coverage" ]; then
    echo "Running tests with coverage report..."
    pytest --cov=app --cov-report=html --cov-report=term-missing --cov-fail-under=80
    echo "Coverage report generated in htmlcov/"
elif [ "$1" = "integration" ]; then
    echo "Running integration tests only..."
    pytest -m integration -v
elif [ "$1" = "unit" ]; then
    echo "Running unit tests only..."
    pytest -m "not integration" -v
elif [ "$1" = "fast" ]; then
    echo "Running fast tests (excluding slow ones)..."
    pytest -m "not slow" -v
else
    echo "Running all tests..."
    pytest -v
fi

echo "✅ Tests completed!"

# Deactivate virtual environment
deactivate
