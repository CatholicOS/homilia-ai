#!/usr/bin/env python3
"""
Test utilities and helper functions for document processing tests.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List
import json


class MockUploadFile:
    """Mock UploadFile for testing."""
    
    def __init__(self, filename: str, content: bytes, content_type: str = "text/plain"):
        self.filename = filename
        self.content = content
        self.content_type = content_type
        self._read = False
    
    async def read(self):
        """Simulate async read."""
        if self._read:
            raise ValueError("File already read")
        self._read = True
        return self.content
    
    @property
    def size(self):
        """Get file size."""
        return len(self.content)


class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_sample_text(length: int = 100) -> str:
        """Create sample text of specified length."""
        return "This is a sample document. " * (length // 28 + 1)
    
    @staticmethod
    def create_sample_bytes(size: int = 1024) -> bytes:
        """Create sample bytes of specified size."""
        return b"x" * size
    
    @staticmethod
    def create_sample_chunks(count: int = 3) -> List[Dict[str, Any]]:
        """Create sample chunks."""
        chunks = []
        for i in range(count):
            chunks.append({
                'text': f'This is chunk {i} of the document.',
                'start': i * 50,
                'end': (i + 1) * 50
            })
        return chunks
    
    @staticmethod
    def create_sample_embeddings(dimensions: int = 100, count: int = 3) -> List[List[float]]:
        """Create sample embeddings."""
        embeddings = []
        for i in range(count):
            embedding = [float(j + i) / 100.0 for j in range(dimensions)]
            embeddings.append(embedding)
        return embeddings
    
    @staticmethod
    def create_sample_processing_result(file_id: str = "file_123") -> Dict[str, Any]:
        """Create sample processing result."""
        return {
            'success': True,
            'file_id': file_id,
            'filename': 'test_document.txt',
            'parish_id': 'parish_001',
            'document_type': 'homily',
            'chunk_count': 3,
            's3_key': f'parish_001/homily/{file_id}.txt',
            'processing_timestamp': '2024-01-01T12:00:00Z'
        }
    
    @staticmethod
    def create_sample_document_info(file_id: str = "file_123") -> Dict[str, Any]:
        """Create sample document info."""
        return {
            'success': True,
            'file_id': file_id,
            'filename': 'test_document.txt',
            'source': 'parish_001_homily',
            'chunk_count': 3,
            'parish_id': 'parish_001',
            'document_type': 'homily',
            's3_key': f'parish_001/homily/{file_id}.txt',
            'extraction_method': 'python-docx',
            'file_type': 'txt',
            'file_size': 1024,
            'created_at': '2024-01-01T12:00:00Z'
        }
    
    @staticmethod
    def create_sample_search_results(file_count: int = 1) -> Dict[str, Any]:
        """Create sample search results."""
        results = []
        for i in range(file_count):
            results.append({
                'file_id': f'file_{i:03d}',
                'filename': f'test_document_{i}.txt',
                'source': f'parish_001_homily',
                'metadata': {
                    'parish_id': 'parish_001',
                    'document_type': 'homily',
                    'chunk_index': 0
                },
                'chunks': [
                    {
                        'text': f'This is sample text from document {i}.',
                        'score': 0.95 - (i * 0.1),
                        'chunk_index': 0
                    }
                ],
                'max_score': 0.95 - (i * 0.1)
            })
        
        return {
            'success': True,
            'query': 'test query',
            'results': results,
            'total_files': file_count,
            'total_chunks': file_count
        }
    
    @staticmethod
    def create_sample_delete_result(file_id: str = "file_123") -> Dict[str, Any]:
        """Create sample delete result."""
        return {
            'success': True,
            'file_id': file_id,
            'deleted_chunks': 3,
            'deleted_s3_files': 1,
            'total_chunks': 3,
            'total_s3_files': 1
        }


class MockServiceFactory:
    """Factory for creating mock services."""
    
    @staticmethod
    def create_mock_textract_service():
        """Create mock TextractService."""
        mock_service = Mock()
        mock_service.extract_text_from_file.return_value = {
            'success': True,
            'text': TestDataFactory.create_sample_text(),
            'extraction_method': 'python-docx',
            'file_type': 'txt',
            'file_size': 1024
        }
        mock_service.extract_text_from_bytes.return_value = {
            'success': True,
            'text': TestDataFactory.create_sample_text(),
            'extraction_method': 'python-docx',
            'file_type': 'txt',
            'file_size': 1024
        }
        mock_service.get_supported_formats.return_value = ['.pdf', '.docx', '.doc', '.txt', '.rtf']
        return mock_service
    
    @staticmethod
    def create_mock_embedding_service():
        """Create mock EmbeddingService."""
        mock_service = Mock()
        mock_result = Mock()
        mock_result.embeddings = TestDataFactory.create_sample_embeddings()
        mock_service.get_embedding.return_value = mock_result
        return mock_service
    
    @staticmethod
    def create_mock_s3_service():
        """Create mock S3Service."""
        mock_service = Mock()
        mock_service.upload_bytes.return_value = {'success': True, 's3_key': 'test/key'}
        mock_service.delete_file.return_value = {'success': True}
        mock_service.get_bucket_info.return_value = {'success': True}
        return mock_service
    
    @staticmethod
    def create_mock_opensearch_service():
        """Create mock OpenSearchService."""
        mock_service = Mock()
        mock_service.index_documents_batch.return_value = {'success': True, 'indexed_count': 3}
        mock_service.knn_search.return_value = {
            'success': True,
            'results': []
        }
        mock_service.search_by_file_id.return_value = {
            'success': True,
            'results': []
        }
        mock_service.delete_document.return_value = {'success': True}
        mock_service.test_connection.return_value = True
        mock_service.refresh_index.return_value = None
        return mock_service


class FileTestHelper:
    """Helper for file-related tests."""
    
    @staticmethod
    def create_temp_file(content: str = "Test content", suffix: str = ".txt") -> str:
        """Create a temporary file with content."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=suffix) as f:
            f.write(content)
            return f.name
    
    @staticmethod
    def cleanup_temp_file(file_path: str):
        """Clean up temporary file."""
        try:
            os.unlink(file_path)
        except OSError:
            pass
    
    @staticmethod
    def get_supported_file_types() -> List[str]:
        """Get list of supported file types."""
        return ['.pdf', '.docx', '.doc', '.txt', '.rtf']
    
    @staticmethod
    def get_unsupported_file_types() -> List[str]:
        """Get list of unsupported file types."""
        return ['.xyz', '.exe', '.bin', '.zip', '.rar']


class ValidationHelper:
    """Helper for validation tests."""
    
    @staticmethod
    def validate_file_type(filename: str) -> bool:
        """Validate file type."""
        supported_extensions = ['.pdf', '.docx', '.doc', '.txt', '.rtf']
        file_ext = os.path.splitext(filename)[1].lower()
        return file_ext in supported_extensions
    
    @staticmethod
    def validate_file_size(file_size: int, max_size_mb: int = 50) -> bool:
        """Validate file size."""
        max_size_bytes = max_size_mb * 1024 * 1024
        return file_size <= max_size_bytes
    
    @staticmethod
    def validate_metadata_json(metadata_str: str) -> bool:
        """Validate metadata JSON string."""
        try:
            json.loads(metadata_str)
            return True
        except json.JSONDecodeError:
            return False


class AssertionHelper:
    """Helper for common assertions."""
    
    @staticmethod
    def assert_success_response(response_data: Dict[str, Any]):
        """Assert that response indicates success."""
        assert response_data.get('success') is True
        assert 'error' not in response_data or response_data['error'] is None
    
    @staticmethod
    def assert_error_response(response_data: Dict[str, Any], expected_error: str = None):
        """Assert that response indicates error."""
        assert response_data.get('success') is False
        assert 'error' in response_data
        if expected_error:
            assert expected_error in response_data['error']
    
    @staticmethod
    def assert_document_response_structure(response_data: Dict[str, Any]):
        """Assert that response has proper document structure."""
        required_fields = ['success', 'file_id', 'filename', 'parish_id', 'document_type']
        for field in required_fields:
            assert field in response_data
    
    @staticmethod
    def assert_search_response_structure(response_data: Dict[str, Any]):
        """Assert that response has proper search structure."""
        required_fields = ['success', 'query', 'results', 'total_files', 'total_chunks']
        for field in required_fields:
            assert field in response_data
    
    @staticmethod
    def assert_chunk_structure(chunk: Dict[str, Any]):
        """Assert that chunk has proper structure."""
        required_fields = ['text', 'start', 'end']
        for field in required_fields:
            assert field in chunk
        assert chunk['start'] >= 0
        assert chunk['end'] > chunk['start']
        assert chunk['text'].strip() != ""


class MockDataGenerator:
    """Generate mock data for testing."""
    
    @staticmethod
    def generate_large_file_content(size_mb: int) -> bytes:
        """Generate large file content for size testing."""
        return b"x" * (size_mb * 1024 * 1024)
    
    @staticmethod
    def generate_malformed_json() -> str:
        """Generate malformed JSON string."""
        return '{"invalid": json, "missing": quotes}'
    
    @staticmethod
    def generate_valid_json() -> str:
        """Generate valid JSON string."""
        return json.dumps({"author": "test", "version": "1.0"})
    
    @staticmethod
    def generate_file_id() -> str:
        """Generate a mock file ID."""
        return f"file_{hash(str(hash('test'))):016x}"
    
    @staticmethod
    def generate_parish_id() -> str:
        """Generate a mock parish ID."""
        return f"parish_{hash(str(hash('test'))):03d}"


# Pytest fixtures for common test data
@pytest.fixture
def test_data_factory():
    """Provide TestDataFactory instance."""
    return TestDataFactory


@pytest.fixture
def mock_service_factory():
    """Provide MockServiceFactory instance."""
    return MockServiceFactory


@pytest.fixture
def file_test_helper():
    """Provide FileTestHelper instance."""
    return FileTestHelper


@pytest.fixture
def validation_helper():
    """Provide ValidationHelper instance."""
    return ValidationHelper


@pytest.fixture
def assertion_helper():
    """Provide AssertionHelper instance."""
    return AssertionHelper


@pytest.fixture
def mock_data_generator():
    """Provide MockDataGenerator instance."""
    return MockDataGenerator


@pytest.fixture
def temp_file_with_content():
    """Create temporary file with content and cleanup."""
    file_path = FileTestHelper.create_temp_file("Test content for testing")
    yield file_path
    FileTestHelper.cleanup_temp_file(file_path)


@pytest.fixture
def large_file_content():
    """Generate large file content for testing."""
    return MockDataGenerator.generate_large_file_content(51)  # 51MB


@pytest.fixture
def valid_metadata_json():
    """Generate valid metadata JSON."""
    return MockDataGenerator.generate_valid_json()


@pytest.fixture
def invalid_metadata_json():
    """Generate invalid metadata JSON."""
    return MockDataGenerator.generate_malformed_json()
