#!/usr/bin/env python3
"""
Test configuration and fixtures for document processing tests.
"""

import pytest
import os
import sys
import tempfile
import json
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import the modules we're testing
from routes.document_routes import router, DocumentProcessingService
from services.document_processing_service import DocumentProcessingService as DPS


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_document_service():
    """Mock DocumentProcessingService."""
    service = Mock(spec=DocumentProcessingService)
    return service


@pytest.fixture
def sample_file_content():
    """Sample file content for testing."""
    return b"This is a sample document content for testing purposes."


@pytest.fixture
def sample_text():
    """Sample text content for testing."""
    return """
    This is a sample document for testing the document processing service.
    It contains multiple sentences that will be chunked and processed.
    The service will extract text, create chunks, generate embeddings,
    and store everything in S3 and OpenSearch.
    This is another paragraph with more content to test chunking.
    The chunking algorithm should handle overlapping chunks properly.
    """


@pytest.fixture
def sample_chunks():
    """Sample chunked text for testing."""
    return [
        {
            'text': 'This is a sample document for testing the document processing service.',
            'start': 0,
            'end': 80
        },
        {
            'text': 'It contains multiple sentences that will be chunked and processed.',
            'start': 80,
            'end': 150
        },
        {
            'text': 'The service will extract text, create chunks, generate embeddings.',
            'start': 150,
            'end': 220
        }
    ]


@pytest.fixture
def sample_embeddings():
    """Sample embeddings for testing."""
    return [0.1, 0.2, 0.3, 0.4, 0.5] * 20  # 100-dimensional embedding


@pytest.fixture
def sample_processing_result():
    """Sample processing result."""
    return {
        'success': True,
        'file_id': 'file_1234567890abcdef',
        'filename': 'test_document.txt',
        'parish_id': 'parish_001',
        'document_type': 'homily',
        'chunk_count': 3,
        's3_key': 'parish_001/homily/test_document.txt',
        'processing_timestamp': '2024-01-01T12:00:00Z'
    }


@pytest.fixture
def sample_document_info():
    """Sample document info."""
    return {
        'success': True,
        'file_id': 'file_1234567890abcdef',
        'filename': 'test_document.txt',
        'source': 'parish_001_homily',
        'chunk_count': 3,
        'parish_id': 'parish_001',
        'document_type': 'homily',
        's3_key': 'parish_001/homily/test_document.txt',
        'extraction_method': 'python-docx',
        'file_type': 'txt',
        'file_size': 1024,
        'created_at': '2024-01-01T12:00:00Z'
    }


@pytest.fixture
def sample_search_results():
    """Sample search results."""
    return {
        'success': True,
        'query': 'test query',
        'results': [
            {
                'file_id': 'file_1234567890abcdef',
                'filename': 'test_document.txt',
                'source': 'parish_001_homily',
                'metadata': {
                    'parish_id': 'parish_001',
                    'document_type': 'homily',
                    'chunk_index': 0
                },
                'chunks': [
                    {
                        'text': 'This is a sample document for testing.',
                        'score': 0.95,
                        'chunk_index': 0
                    }
                ],
                'max_score': 0.95
            }
        ],
        'total_files': 1,
        'total_chunks': 1
    }


@pytest.fixture
def sample_delete_result():
    """Sample delete result."""
    return {
        'success': True,
        'file_id': 'file_1234567890abcdef',
        'deleted_chunks': 3,
        'deleted_s3_files': 1,
        'total_chunks': 3,
        'total_s3_files': 1
    }


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("This is a test file content.")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except OSError:
        pass


@pytest.fixture
def mock_services():
    """Mock all external services."""
    with patch('services.document_processing_service.TextractService') as mock_textract, \
         patch('services.document_processing_service.EmbeddingService') as mock_embedding, \
         patch('services.document_processing_service.S3Service') as mock_s3, \
         patch('services.document_processing_service.OpenSearchService') as mock_opensearch:
        
        # Configure mock services
        mock_textract.return_value.extract_text_from_bytes.return_value = {
            'success': True,
            'text': 'Sample extracted text',
            'extraction_method': 'python-docx',
            'file_type': 'txt',
            'file_size': 1024
        }
        
        mock_embedding.return_value.get_embedding.return_value = Mock(
            embeddings=[[0.1] * 100] * 3
        )
        
        mock_s3.return_value.upload_bytes.return_value = {
            'success': True,
            's3_key': 'test/key'
        }
        
        mock_opensearch.return_value.index_documents_batch.return_value = {
            'success': True,
            'indexed_count': 3
        }
        
        yield {
            'textract': mock_textract,
            'embedding': mock_embedding,
            's3': mock_s3,
            'opensearch': mock_opensearch
        }
