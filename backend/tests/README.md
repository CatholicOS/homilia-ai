# Document Processing Tests

This directory contains comprehensive unit tests for the document processing system, including tests for both the API routes and the core processing service.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest configuration and fixtures
├── test_document_routes.py     # Tests for document API routes
├── test_document_processing_service.py  # Tests for document processing service
├── test_utilities.py           # Test utilities and helper functions
├── test_integration.py         # Integration tests
└── run_tests.py               # Test runner script
```

## Test Coverage

### Document Routes Tests (`test_document_routes.py`)
- **Upload Endpoint Tests**
  - Successful document upload
  - File validation (type, size)
  - Metadata handling
  - Error handling
  - Processing failure scenarios

- **Batch Upload Tests**
  - Multiple file processing
  - Mixed success/failure results
  - Batch size limits
  - Error handling

- **Document Info Tests**
  - Successful info retrieval
  - Document not found scenarios
  - Service error handling

- **Search Tests**
  - Successful search operations
  - Query validation
  - Filter handling
  - Error scenarios

- **Delete Tests**
  - Successful document deletion
  - Service error handling

- **Health Check Tests**
  - All services healthy
  - Service degradation
  - Exception handling

- **Utility Function Tests**
  - File type validation
  - File size validation

### Document Processing Service Tests (`test_document_processing_service.py`)
- **Service Initialization**
  - Proper service setup
  - Dependency injection

- **Document Processing**
  - File-based processing
  - Bytes-based processing
  - Text extraction handling
  - Chunking functionality
  - Embedding generation
  - S3 storage
  - OpenSearch indexing

- **Text Processing**
  - Text chunking with overlap
  - Empty text handling
  - Whitespace handling
  - Chunk structure validation

- **Document Management**
  - Document deletion workflow
  - Document info retrieval
  - Search functionality
  - Filter handling

- **Error Handling**
  - Service failures
  - Exception propagation
  - Graceful degradation

### Integration Tests (`test_integration.py`)
- **Complete Workflow Tests**
  - End-to-end document processing
  - API integration
  - Service coordination

- **Error Propagation Tests**
  - Error handling across layers
  - Service degradation handling

- **Concurrent Operations**
  - Multiple document processing
  - Batch operations
  - Resource management

### Test Utilities (`test_utilities.py`)
- **Test Data Factories**
  - Sample data generation
  - Mock service creation
  - File handling utilities

- **Validation Helpers**
  - File validation
  - JSON validation
  - Response validation

- **Assertion Helpers**
  - Common assertions
  - Structure validation
  - Error checking

## Running Tests

### Prerequisites
Install test dependencies:
```bash
pip install -r requirements.txt
```

### Running All Tests
```bash
# From the backend directory
python -m pytest tests/

# Or use the test runner script
python tests/run_tests.py
```

### Running Specific Test Categories
```bash
# Run only route tests
python tests/run_tests.py --routes-only

# Run only service tests
python tests/run_tests.py --service-only

# Run with coverage
python tests/run_tests.py --coverage

# Run with verbose output
python tests/run_tests.py --verbose
```

### Running Individual Test Files
```bash
# Run specific test file
python -m pytest tests/test_document_routes.py

# Run specific test class
python -m pytest tests/test_document_routes.py::TestDocumentRoutes

# Run specific test method
python -m pytest tests/test_document_routes.py::TestDocumentRoutes::test_upload_document_success
```

### Running with Patterns
```bash
# Run tests matching a pattern
python -m pytest -k "upload"

# Run tests excluding certain patterns
python -m pytest -k "not slow"
```

## Test Configuration

### Pytest Configuration (`pytest.ini`)
- Minimum pytest version: 6.0
- Test discovery patterns
- Markers for test categorization
- Warning filters
- Output formatting

### Fixtures (`conftest.py`)
- FastAPI app and client setup
- Mock service configurations
- Sample data fixtures
- Temporary file handling
- Test data generators

## Mocking Strategy

The tests use comprehensive mocking to isolate components:

- **External Services**: AWS Textract, S3, OpenSearch
- **Dependencies**: Embedding service, file operations
- **Network Calls**: HTTP requests, API calls
- **File Operations**: Temporary files, file I/O

## Test Data Management

- **Sample Data**: Realistic test data for various scenarios
- **Mock Services**: Pre-configured mock services with realistic responses
- **Temporary Files**: Automatic cleanup of test files
- **Data Factories**: Reusable data generation functions

## Coverage Goals

- **Unit Tests**: 90%+ coverage for core business logic
- **Integration Tests**: Cover all major workflows
- **Error Scenarios**: Test all error conditions
- **Edge Cases**: Handle boundary conditions

## Best Practices

1. **Isolation**: Each test is independent and can run in any order
2. **Mocking**: External dependencies are mocked to ensure test reliability
3. **Data Cleanup**: Temporary files and resources are properly cleaned up
4. **Assertions**: Clear, specific assertions with helpful error messages
5. **Documentation**: Tests serve as documentation for expected behavior
6. **Maintainability**: Tests are easy to understand and modify

## Continuous Integration

These tests are designed to run in CI/CD pipelines:
- No external dependencies required
- Fast execution time
- Reliable and deterministic
- Clear pass/fail criteria

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure backend directory is in Python path
2. **Mock Failures**: Check mock configurations and call counts
3. **File Permissions**: Ensure write access for temporary files
4. **Dependencies**: Install all required packages from requirements.txt

### Debug Mode
Run tests with verbose output for debugging:
```bash
python -m pytest -v -s tests/
```

### Coverage Reports
Generate HTML coverage reports:
```bash
python -m pytest --cov=services --cov=routes --cov-report=html tests/
```
