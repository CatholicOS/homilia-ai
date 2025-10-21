#!/usr/bin/env python3
"""
Comprehensive unit tests for document_routes.py

Tests all endpoints and functionality of the document upload API routes.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import UploadFile
from io import BytesIO

from tests.conftest import app, client, mock_document_service, sample_file_content, sample_processing_result


class TestDocumentRoutes:
    """Test class for document routes."""
    
    def test_upload_document_success(self, client, sample_file_content, sample_processing_result):
        """Test successful document upload."""
        with patch('routes.document_routes.document_service') as mock_service:
            mock_service.process_document_from_bytes.return_value = sample_processing_result
            
            files = {"file": ("test.txt", BytesIO(sample_file_content), "text/plain")}
            data = {
                "parish_id": "parish_001",
                "document_type": "homily",
                "use_textract": "false",
                "metadata": json.dumps({"author": "test"})
            }
            
            response = client.post("/api/documents/upload", files=files, data=data)
            
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
            assert result["file_id"] == "file_1234567890abcdef"
            assert result["filename"] == "test_document.txt"
            assert result["parish_id"] == "parish_001"
            assert result["chunk_count"] == 3
            
            mock_service.process_document_from_bytes.assert_called_once()
    
    def test_upload_document_no_filename(self, client):
        """Test upload with no filename."""
        files = {"file": ("", BytesIO(b"content"), "text/plain")}
        data = {"parish_id": "parish_001"}
        
        response = client.post("/api/documents/upload", files=files, data=data)
        
        assert response.status_code == 422  # FastAPI validation error
        # The error message might be different due to FastAPI validation
    
    def test_upload_document_unsupported_file_type(self, client, sample_file_content):
        """Test upload with unsupported file type."""
        files = {"file": ("test.xyz", BytesIO(sample_file_content), "application/xyz")}
        data = {"parish_id": "parish_001"}
        
        response = client.post("/api/documents/upload", files=files, data=data)
        
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]
    
    def test_upload_document_file_too_large(self, client):
        """Test upload with file too large."""
        # Create a large file content (> 50MB)
        large_content = b"x" * (51 * 1024 * 1024)  # 51MB
        
        files = {"file": ("test.txt", BytesIO(large_content), "text/plain")}
        data = {"parish_id": "parish_001"}
        
        response = client.post("/api/documents/upload", files=files, data=data)
        
        assert response.status_code == 400
        assert "File too large" in response.json()["detail"]
    
    def test_upload_document_invalid_metadata_json(self, client, sample_file_content):
        """Test upload with invalid metadata JSON."""
        files = {"file": ("test.txt", BytesIO(sample_file_content), "text/plain")}
        data = {
            "parish_id": "parish_001",
            "metadata": "invalid json"
        }
        
        response = client.post("/api/documents/upload", files=files, data=data)
        
        assert response.status_code == 400
        assert "Invalid metadata JSON format" in response.json()["detail"]
    
    def test_upload_document_processing_failure(self, client, sample_file_content):
        """Test upload when document processing fails."""
        with patch('routes.document_routes.document_service') as mock_service:
            mock_service.process_document_from_bytes.return_value = {
                'success': False,
                'error': 'Processing failed'
            }
            
            files = {"file": ("test.txt", BytesIO(sample_file_content), "text/plain")}
            data = {"parish_id": "parish_001"}
            
            response = client.post("/api/documents/upload", files=files, data=data)
            
            assert response.status_code == 500
            assert "Processing failed" in response.json()["detail"]
    
    def test_upload_document_unexpected_error(self, client, sample_file_content):
        """Test upload with unexpected error."""
        with patch('routes.document_routes.document_service') as mock_service:
            mock_service.process_document_from_bytes.side_effect = Exception("Unexpected error")
            
            files = {"file": ("test.txt", BytesIO(sample_file_content), "text/plain")}
            data = {"parish_id": "parish_001"}
            
            response = client.post("/api/documents/upload", files=files, data=data)
            
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]
    
    def test_upload_documents_batch_success(self, client, sample_file_content, sample_processing_result):
        """Test successful batch document upload."""
        with patch('routes.document_routes.document_service') as mock_service:
            mock_service.process_document_from_bytes.return_value = sample_processing_result
            
            files = [
                ("files", ("file1.txt", BytesIO(sample_file_content), "text/plain")),
                ("files", ("file2.txt", BytesIO(sample_file_content), "text/plain"))
            ]
            data = {
                "parish_id": "parish_001",
                "document_type": "homily"
            }
            
            response = client.post("/api/documents/upload/batch", files=files, data=data)
            
            assert response.status_code == 200
            results = response.json()
            assert len(results) == 2
            assert all(result["success"] for result in results)
            assert mock_service.process_document_from_bytes.call_count == 2
    
    def test_upload_documents_batch_no_files(self, client):
        """Test batch upload with no files."""
        data = {"parish_id": "parish_001"}
        
        response = client.post("/api/documents/upload/batch", files=[], data=data)
        
        assert response.status_code == 422  # FastAPI validation error for empty files list
    
    def test_upload_documents_batch_too_many_files(self, client, sample_file_content):
        """Test batch upload with too many files."""
        files = []
        for i in range(11):  # More than 10 files
            files.append(("files", (f"file{i}.txt", BytesIO(sample_file_content), "text/plain")))
        
        data = {"parish_id": "parish_001"}
        
        response = client.post("/api/documents/upload/batch", files=files, data=data)
        
        assert response.status_code == 400
        assert "Too many files" in response.json()["detail"]
    
    def test_upload_documents_batch_mixed_results(self, client, sample_file_content, sample_processing_result):
        """Test batch upload with mixed success/failure results."""
        with patch('routes.document_routes.document_service') as mock_service:
            # First call succeeds, second fails
            mock_service.process_document_from_bytes.side_effect = [
                sample_processing_result,
                {'success': False, 'error': 'Processing failed'}
            ]
            
            files = [
                ("files", ("file1.txt", BytesIO(sample_file_content), "text/plain")),
                ("files", ("file2.txt", BytesIO(sample_file_content), "text/plain"))
            ]
            data = {"parish_id": "parish_001"}
            
            response = client.post("/api/documents/upload/batch", files=files, data=data)
            
            assert response.status_code == 200
            results = response.json()
            assert len(results) == 2
            assert results[0]["success"] is True
            assert results[1]["success"] is False
            assert "Processing failed" in results[1]["error"]
    
    def test_get_document_info_success(self, client, sample_document_info):
        """Test successful document info retrieval."""
        with patch('routes.document_routes.document_service') as mock_service:
            mock_service.get_document_info.return_value = sample_document_info
            
            response = client.get("/api/documents/info/file_1234567890abcdef")
            
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
            assert result["file_id"] == "file_1234567890abcdef"
            assert result["filename"] == "test_document.txt"
            assert result["chunk_count"] == 3
    
    def test_get_document_info_not_found(self, client):
        """Test document info retrieval when document not found."""
        with patch('routes.document_routes.document_service') as mock_service:
            mock_service.get_document_info.return_value = {
                'success': False,
                'error': 'Document not found'
            }
            
            response = client.get("/api/documents/info/nonexistent_file")
            
            assert response.status_code == 404
            assert "Document not found" in response.json()["detail"]
    
    def test_get_document_info_service_error(self, client):
        """Test document info retrieval with service error."""
        with patch('routes.document_routes.document_service') as mock_service:
            mock_service.get_document_info.return_value = {
                'success': False,
                'error': 'Service error'
            }
            
            response = client.get("/api/documents/info/file_1234567890abcdef")
            
            assert response.status_code == 500
            assert "Service error" in response.json()["detail"]
    
    def test_search_documents_success(self, client, sample_search_results):
        """Test successful document search."""
        with patch('routes.document_routes.document_service') as mock_service:
            mock_service.search_documents.return_value = sample_search_results
            
            data = {
                "query": "test query",
                "parish_id": "parish_001",
                "document_type": "homily",
                "k": "10"
            }
            
            response = client.post("/api/documents/search", data=data)
            
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
            assert result["query"] == "test query"
            assert len(result["results"]) == 1
            assert result["total_files"] == 1
    
    def test_search_documents_empty_query(self, client):
        """Test search with empty query."""
        data = {"query": "   "}  # Empty/whitespace query
        
        response = client.post("/api/documents/search", data=data)
        
        assert response.status_code == 400
        assert "Query cannot be empty" in response.json()["detail"]
    
    def test_search_documents_service_error(self, client):
        """Test search with service error."""
        with patch('routes.document_routes.document_service') as mock_service:
            mock_service.search_documents.return_value = {
                'success': False,
                'error': 'Search failed'
            }
            
            data = {"query": "test query"}
            
            response = client.post("/api/documents/search", data=data)
            
            assert response.status_code == 500
            assert "Search failed" in response.json()["detail"]
    
    def test_delete_document_success(self, client, sample_delete_result):
        """Test successful document deletion."""
        with patch('routes.document_routes.document_service') as mock_service:
            mock_service.delete_document.return_value = sample_delete_result
            
            response = client.delete("/api/documents/file_1234567890abcdef")
            
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
            assert result["file_id"] == "file_1234567890abcdef"
            assert result["deleted_chunks"] == 3
            assert result["deleted_s3_files"] == 1
    
    def test_delete_document_service_error(self, client):
        """Test document deletion with service error."""
        with patch('routes.document_routes.document_service') as mock_service:
            mock_service.delete_document.return_value = {
                'success': False,
                'error': 'Deletion failed'
            }
            
            response = client.delete("/api/documents/file_1234567890abcdef")
            
            assert response.status_code == 500
            assert "Deletion failed" in response.json()["detail"]
    
    def test_get_health_all_services_healthy(self, client):
        """Test health check when all services are healthy."""
        with patch('routes.document_routes.document_service') as mock_service:
            mock_service.opensearch_service.test_connection.return_value = True
            mock_service.s3_service.get_bucket_info.return_value = {'success': True}
            
            response = client.get("/api/documents/health")
            
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "healthy"
            assert all(status == "available" for status in result["services"].values())
    
    def test_get_health_opensearch_unavailable(self, client):
        """Test health check when OpenSearch is unavailable."""
        with patch('routes.document_routes.document_service') as mock_service:
            mock_service.opensearch_service.test_connection.return_value = False
            mock_service.s3_service.get_bucket_info.return_value = {'success': True}
            
            response = client.get("/api/documents/health")
            
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "degraded"
            assert result["services"]["opensearch"] == "unavailable"
    
    def test_get_health_s3_unavailable(self, client):
        """Test health check when S3 is unavailable."""
        with patch('routes.document_routes.document_service') as mock_service:
            mock_service.opensearch_service.test_connection.return_value = True
            mock_service.s3_service.get_bucket_info.return_value = {'success': False}
            
            response = client.get("/api/documents/health")
            
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "degraded"
            assert result["services"]["s3"] == "unavailable"
    
    def test_get_health_service_exception(self, client):
        """Test health check when service throws exception."""
        with patch('routes.document_routes.document_service') as mock_service:
            mock_service.opensearch_service.test_connection.side_effect = Exception("Connection failed")
            mock_service.s3_service.get_bucket_info.side_effect = Exception("S3 failed")
            
            response = client.get("/api/documents/health")
            
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "degraded"
            assert result["services"]["opensearch"] == "unavailable"
            assert result["services"]["s3"] == "unavailable"
    
    def test_get_supported_formats(self, client):
        """Test getting supported file formats."""
        with patch('routes.document_routes.document_service') as mock_service:
            mock_service.textract_service.get_supported_formats.return_value = [
                '.pdf', '.docx', '.doc', '.txt', '.rtf'
            ]
            
            response = client.get("/api/documents/supported-formats")
            
            assert response.status_code == 200
            result = response.json()
            assert "supported_formats" in result
            assert "max_file_size_mb" in result
            assert "max_batch_size" in result
            assert result["max_file_size_mb"] == 50
            assert result["max_batch_size"] == 10


class TestDocumentRoutesValidation:
    """Test validation functions in document routes."""
    
    def test_validate_file_type_supported(self):
        """Test file type validation with supported types."""
        from routes.document_routes import validate_file_type
        
        assert validate_file_type("test.pdf") is True
        assert validate_file_type("test.docx") is True
        assert validate_file_type("test.doc") is True
        assert validate_file_type("test.txt") is True
        assert validate_file_type("test.rtf") is True
    
    def test_validate_file_type_unsupported(self):
        """Test file type validation with unsupported types."""
        from routes.document_routes import validate_file_type
        
        assert validate_file_type("test.xyz") is False
        assert validate_file_type("test") is False
        assert validate_file_type("test.PDF") is True  # Case insensitive
    
    def test_validate_file_size_valid(self):
        """Test file size validation with valid sizes."""
        from routes.document_routes import validate_file_size
        
        assert validate_file_size(1024) is True  # 1KB
        assert validate_file_size(50 * 1024 * 1024) is True  # Exactly 50MB
        assert validate_file_size(1024, max_size_mb=1) is True  # Custom max size
    
    def test_validate_file_size_invalid(self):
        """Test file size validation with invalid sizes."""
        from routes.document_routes import validate_file_size
        
        assert validate_file_size(51 * 1024 * 1024) is False  # Over 50MB
        assert validate_file_size(1024 * 1024, max_size_mb=0.5) is False  # Over custom max size (1MB > 0.5MB)
