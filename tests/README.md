# Data-Manager Tests

This directory contains comprehensive tests for the Data-Manager application.

## Test Structure

- `conftest.py` - Pytest fixtures and configuration
- `test_operators.py` - Tests for database operations
- `test_utils.py` - Tests for utility functions
- `test_api.py` - Tests for web API endpoints
- `test_integration.py` - Integration tests for complete user workflows
- `test_search.py` - Tests for search engine functionality
- `run_tests.py` - Script to run all tests with coverage reports

## Running the Tests

### Recommended Method: Using the Shell Script

The easiest way to run the tests is using the included shell script, which will set up a clean virtual environment with the correct dependencies:

```bash
# Make sure the script is executable
chmod +x run_tests.sh

# Run the tests
./run_tests.sh
```

This will:
1. Create a temporary virtual environment
2. Install all test dependencies with the correct versions
3. Run the tests with coverage reporting
4. Clean up after completion

### Alternative Methods

#### Install Test Dependencies

If you want to run tests in your existing environment, install the required test dependencies:

```bash
pip install -r tests/requirements_test.txt
```

**Note:** Flask version compatibility is important. If you encounter errors about `_request_ctx_stack`, make sure you're using Flask ≤ 2.2.5:

```bash
pip install flask<=2.2.5
```

#### Run Tests Using the Python Script

```bash
python tests/run_tests.py
```

#### Run Tests Directly with Pytest

```bash
# Run all tests
pytest tests/ -v

# Run specific test files
pytest tests/test_operators.py -v
pytest tests/test_utils.py -v
pytest tests/test_api.py -v
pytest tests/test_integration.py -v
pytest tests/test_search.py -v

# Run tests with coverage
pytest --cov=src tests/
```

## Test Categories

### Unit Tests

- `test_operators.py` - Tests database operations in isolation
- `test_utils.py` - Tests utility functions in isolation
- `test_search.py` - Tests search engine functionality

### Integration Tests

- `test_api.py` - Tests API endpoints with database integration
- `test_integration.py` - Tests complete user workflows

## Test Coverage

The tests aim to cover:

1. Database operations (CRUD operations for users, entries, orders, etc.)
2. Utility functions (file operations, validation, security, etc.)
3. Web API endpoints (authentication, data manipulation, etc.)
4. Complete user workflows (user management, entry management, etc.)
5. Search engine functionality

## Mocking

For tests that require external dependencies (e.g., email services, external APIs), we use mocking to isolate the tests from these dependencies.

## Troubleshooting

### ImportError: cannot import name '_request_ctx_stack' from 'flask'

This error occurs due to incompatibility between newer Flask versions (>=2.3) and pytest-flask. To fix:

1. Downgrade Flask: `pip install flask<=2.2.5`
2. Use the shell script `./run_tests.sh` which handles this automatically 