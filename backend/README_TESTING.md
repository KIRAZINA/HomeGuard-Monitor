# Backend Testing Guide

This document covers the comprehensive testing suite for the HomeGuard Monitor backend.

## Test Coverage

The test suite covers the following areas:

### 1. **API Endpoint Tests** (`test_*.py`)
- **Authentication** (`test_auth.py`): User registration, login, token validation
- **Device Management** (`test_devices.py`): CRUD operations, validation
- **Metrics** (`test_metrics.py`): Ingestion, querying, time ranges
- **Alerts** (`test_alerts.py`): Rule management, alert operations

### 2. **Service Layer Tests** (`test_services.py`)
- **DeviceService**: Business logic for device operations
- **MetricService**: Data processing and aggregation
- **AlertService**: Rule evaluation and alert management
- **AuthService**: User authentication and authorization

### 3. **Model Tests** (`test_models.py`)
- **Device**: Device model validation and relationships
- **Metric**: Metric storage and defaults
- **AlertRule/Alert**: Alert system models
- **User**: User model and constraints

### 4. **Background Task Tests** (`test_tasks.py`)
- **Alerting**: Celery tasks for rule evaluation
- **Data Processing**: Cleanup and aggregation tasks
- **Notifications**: Service integration testing

### 5. **Integration Tests** (`test_integration.py`)
- **Complete Workflows**: End-to-end monitoring scenarios
- **Multi-device**: Multiple device management
- **Performance**: Large dataset handling
- **Error Handling**: Failure scenarios and edge cases

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Install main dependencies
pip install -r requirements.txt
```

### Test Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run specific test class
pytest tests/test_devices.py::TestDevices

# Run specific test method
pytest tests/test_devices.py::TestDevices::test_create_device_success

# Run with markers
pytest -m unit                    # Unit tests only
pytest -m integration             # Integration tests only
pytest -m "not slow"              # Exclude slow tests
```

### Test Script

Use the provided test script for convenience:

```bash
# Run all tests
./scripts/run_tests.sh

# Run with coverage
./scripts/run_tests.sh coverage

# Run integration tests only
./scripts/run_tests.sh integration

# Run unit tests only
./scripts/run_tests.sh unit

# Run fast tests (exclude slow ones)
./scripts/run_tests.sh fast
```

## Test Configuration

### Environment Variables

Tests use an in-memory SQLite database by default:

```bash
export DATABASE_URL="sqlite+aiosqlite:///:memory:"
```

### Configuration Files

- `pytest.ini`: Pytest configuration
- `conftest.py`: Test fixtures and setup

## Test Fixtures

### Database Fixtures

- `db_session`: Fresh database session for each test
- `test_device`: Pre-configured test device
- `test_metrics`: Sample metrics for testing
- `test_user_token`: Authentication token for API tests

### Authentication Fixtures

- `auth_headers`: Authorization headers with valid token
- `test_user`: Authenticated test user

## Coverage Requirements

The test suite aims for **80% code coverage** minimum:

```bash
# Generate coverage report
pytest --cov=app --cov-report=term-missing --cov-fail-under=80

# View HTML report
open htmlcov/index.html
```

## Test Categories

### Unit Tests
- Individual component testing
- Mocked dependencies
- Fast execution
- Isolated functionality

### Integration Tests
- Multiple component interaction
- Database operations
- API endpoint testing
- Real data flow

### Performance Tests
- Large dataset handling
- Query optimization
- Memory usage
- Response times

## Writing New Tests

### Test Structure

```python
import pytest
from httpx import AsyncClient

class TestNewFeature:
    """Test new feature functionality."""

    async def test_feature_success(self, client: AsyncClient, auth_headers):
        """Test successful feature operation."""
        # Arrange
        test_data = {"key": "value"}
        
        # Act
        response = await client.post("/api/v1/endpoint", json=test_data, headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["key"] == test_data["key"]

    async def test_feature_validation_error(self, client: AsyncClient, auth_headers):
        """Test feature validation."""
        # Test with invalid data
        invalid_data = {"key": ""}  # Empty value
        
        response = await client.post("/api/v1/endpoint", json=invalid_data, headers=auth_headers)
        
        assert response.status_code == 422
```

### Best Practices

1. **Descriptive Test Names**: Use `test_what_should_happen_when_condition`
2. **AAA Pattern**: Arrange, Act, Assert
3. **One Assertion Per Test**: Focus on single behavior
4. **Use Fixtures**: Leverage existing test fixtures
5. **Mock External Services**: Use mocks for external dependencies
6. **Test Edge Cases**: Include boundary and error conditions
7. **Cleanup**: Ensure tests don't affect each other

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r backend/requirements.txt
        pip install -r backend/requirements-test.txt
    
    - name: Run tests
      run: |
        cd backend
        pytest --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
      with:
        file: ./backend/coverage.xml
```

## Debugging Tests

### Running Individual Tests

```bash
# Run with verbose output
pytest -v tests/test_auth.py::TestAuth::test_register_user_success

# Run with debugger
pytest --pdb tests/test_auth.py::TestAuth::test_register_user_success

# Stop on first failure
pytest -x tests/
```

### Test Output

```bash
# Show test output
pytest -s tests/

# Show local variables in tracebacks
pytest --tb=long tests/
```

## Performance Testing

### Load Testing

```python
import asyncio
import httpx

async def load_test():
    async with httpx.AsyncClient() as client:
        tasks = []
        for i in range(100):
            task = client.get("/api/v1/devices/")
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        return responses

# Run in test
async def test_load_performance():
    responses = await load_test()
    assert all(r.status_code == 200 for r in responses)
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Ensure test database URL is correct
   - Check SQLite driver installation

2. **Import Errors**
   - Verify all dependencies installed
   - Check PYTHONPATH includes project root

3. **Async Test Errors**
   - Use `pytest-asyncio` plugin
   - Mark test functions with `async def`

4. **Coverage Issues**
   - Install `pytest-cov` plugin
   - Check source path configuration

### Test Database Issues

```bash
# Reset test database
rm -f test.db

# Check database connection
python -c "
import asyncio
from app.core.database import engine
async def test():
    async with engine.begin() as conn:
        print('Database connection successful')
asyncio.run(test())
"
```

## Mocking External Services

### Email Service Mock

```python
from unittest.mock import patch, AsyncMock

class TestNotifications:
    @patch('app.services.notification_service.aiosmtplib.send')
    async def test_email_notification(self, mock_send):
        # Configure mock
        mock_send.return_value = AsyncMock()
        
        # Run test
        # ... test code ...
        
        # Verify mock was called
        mock_send.assert_called_once()
```

### Celery Task Mock

```python
from unittest.mock import patch

class TestCeleryTasks:
    @patch('app.tasks.alerting.evaluate_alert_rules')
    async def test_alert_evaluation(self, mock_evaluate):
        # Run task
        evaluate_alert_rules()
        
        # Verify task was called
        mock_evaluate.assert_called_once()
```

This comprehensive testing suite ensures the reliability and correctness of the HomeGuard Monitor backend system.
