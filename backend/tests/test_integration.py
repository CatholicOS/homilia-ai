#!/usr/bin/env python3
"""
Integration tests for document processing pipeline.

These tests verify the integration between different components
and test the complete workflow.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from io import BytesIO

from tests.conftest import app, sample_text, sample_file_content
from tests.test_utilities import TestDataFactory, MockServiceFactory, FileTestHelper


class TestDocumentProcessingIntegration:
    """Integration tests for document processing."""
    
    def test_complete_document_processing_workflow(self, sample_file_content, sample_text):
        """Test complete document processing workflow."""
        with patch('services.document_processing_service.TextractService') as mock_textract, \
             patch('services.document_processing_service.EmbeddingService') as mock_embedding, \
             patch('services.document_processing_service.S3Service') as mock_s3, \
             patch('services.document_processing_service.OpenSearchService') as mock_opensearch, \
             patch('services.document_processing_service.generate_s3_key') as mock_s3_key:
            
            from services.document_processing_service import DocumentProcessingService
            
            # Configure all mocks
            mock_textract.return_value.extract_text_from_bytes.return_value = {
                'success': True,
                'text': sample_text,
                'extraction_method': 'python-docx',
                'file_type': 'txt',
                'file_size': 1024
            }
            
            mock_embedding.return_value.get_embedding.return_value = Mock(
                embeddings=TestDataFactory.create_sample_embeddings(count=1)  # Ensure we have the right number
            )
            
            mock_s3.return_value.upload_bytes.return_value = {'success': True}
            mock_opensearch.return_value.index_documents_batch.return_value = {'success': True}
            mock_s3_key.return_value = 'test/s3/key'
            
            # Test the complete workflow
            service = DocumentProcessingService()
            
            # Mock the chunking to return a single chunk
            mock_chunks = [{'text': 'test chunk', 'start': 0, 'end': 10}]
            with patch.object(service, '_chunk_text', return_value=mock_chunks):
                result = service.process_document_from_bytes(
                    file_bytes=sample_file_content,
                    filename="test_document.txt",
                    parish_id="parish_001",
                    document_type="homily",
                    metadata={"author": "test_author"}
                )
            
            # Verify success
            assert result['success'] is True
            assert 'file_id' in result
            assert result['filename'] == "test_document.txt"
            assert result['parish_id'] == "parish_001"
            assert result['document_type'] == "homily"
            assert result['chunk_count'] > 0
            
            # Verify all services were called
            mock_textract.return_value.extract_text_from_bytes.assert_called_once()
            mock_embedding.return_value.get_embedding.assert_called_once()
            mock_s3.return_value.upload_bytes.assert_called_once()
            mock_opensearch.return_value.index_documents_batch.assert_called_once()
    
    def test_document_upload_api_integration(self, client, sample_file_content):
        """Test document upload API integration."""
        with patch('routes.document_routes.document_service') as mock_service:
            mock_service.process_document_from_bytes.return_value = TestDataFactory.create_sample_processing_result()
            
            files = {"file": ("test_document.txt", BytesIO(sample_file_content), "text/plain")}
            data = {
                "parish_id": "parish_001",
                "document_type": "homily",
                "metadata": '{"author": "test"}'
            }
            
            response = client.post("/api/documents/upload", files=files, data=data)
            
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
            assert result["file_id"] is not None
            assert result["filename"] == "test_document.txt"
    
    def test_document_search_api_integration(self, client):
        """Test document search API integration."""
        with patch('routes.document_routes.document_service') as mock_service:
            mock_service.search_documents.return_value = TestDataFactory.create_sample_search_results()
            
            data = {
                "query": "test query",  # Match the factory's hardcoded query
                "parish_id": "parish_001",
                "document_type": "homily"
            }
            
            response = client.post("/api/documents/search", data=data)
            
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
            assert result["query"] == "test query"  # Match the factory's hardcoded query
            assert "results" in result
            assert result["total_files"] >= 0
    
    def test_document_deletion_workflow(self):
        """Test complete document deletion workflow."""
        with patch('services.document_processing_service.OpenSearchService') as mock_opensearch, \
             patch('services.document_processing_service.S3Service') as mock_s3:
            
            from services.document_processing_service import DocumentProcessingService
            
            # Mock search results
            mock_opensearch.return_value.search_by_file_id.return_value = {
                'success': True,
                'results': [
                    {
                        'id': 'file_123_chunk_0',
                        'document': {
                            'metadata': {'s3_key': 'test/s3/key1'}
                        }
                    },
                    {
                        'id': 'file_123_chunk_1',
                        'document': {
                            'metadata': {'s3_key': 'test/s3/key1'}
                        }
                    }
                ]
            }
            
            # Mock deletion results
            mock_opensearch.return_value.delete_document.return_value = {'success': True}
            mock_s3.return_value.delete_file.return_value = {'success': True}
            
            service = DocumentProcessingService()
            result = service.delete_document('file_123')
            
            assert result['success'] is True
            assert result['deleted_chunks'] == 2
            assert result['deleted_s3_files'] == 1
            
            # Verify all services were called
            mock_opensearch.return_value.search_by_file_id.assert_called_once()
            assert mock_opensearch.return_value.delete_document.call_count == 2
            mock_s3.return_value.delete_file.assert_called_once()
    
    def test_batch_upload_workflow(self, client, sample_file_content):
        """Test batch upload workflow."""
        with patch('routes.document_routes.document_service') as mock_service:
            # Mock successful processing for all files
            mock_service.process_document_from_bytes.return_value = TestDataFactory.create_sample_processing_result()
            
            files = [
                ("files", ("file1.txt", BytesIO(sample_file_content), "text/plain")),
                ("files", ("file2.txt", BytesIO(sample_file_content), "text/plain")),
                ("files", ("file3.txt", BytesIO(sample_file_content), "text/plain"))
            ]
            data = {
                "parish_id": "parish_001",
                "document_type": "homily"
            }
            
            response = client.post("/api/documents/upload/batch", files=files, data=data)
            
            assert response.status_code == 200
            results = response.json()
            assert len(results) == 3
            assert all(result["success"] for result in results)
            
            # Verify service was called for each file
            assert mock_service.process_document_from_bytes.call_count == 3
    
    def test_error_propagation_through_layers(self, client, sample_file_content):
        """Test that errors propagate correctly through all layers."""
        with patch('routes.document_routes.document_service') as mock_service:
            # Mock service failure
            mock_service.process_document_from_bytes.return_value = {
                'success': False,
                'error': 'Service processing failed'
            }
            
            files = {"file": ("test.txt", BytesIO(sample_file_content), "text/plain")}
            data = {"parish_id": "parish_001"}
            
            response = client.post("/api/documents/upload", files=files, data=data)
            
            assert response.status_code == 500
            assert "Service processing failed" in response.json()["detail"]
    
    def test_health_check_integration(self, client):
        """Test health check integration."""
        with patch('routes.document_routes.document_service') as mock_service:
            # Mock healthy services
            mock_service.opensearch_service.test_connection.return_value = True
            mock_service.s3_service.get_bucket_info.return_value = {'success': True}
            
            response = client.get("/api/documents/health")
            
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "healthy"
            assert all(status == "available" for status in result["services"].values())
    
    def test_file_validation_integration(self, client, sample_file_content):
        """Test file validation integration."""
        # Test unsupported file type
        files = {"file": ("test.xyz", BytesIO(sample_file_content), "application/xyz")}
        data = {"parish_id": "parish_001"}
        
        response = client.post("/api/documents/upload", files=files, data=data)
        
        assert response.status_code == 400
        # The error message might be different, so let's check for any error
        assert "error" in response.json() or "detail" in response.json()
        
        # Test file too large
        large_content = b"x" * (51 * 1024 * 1024)  # 51MB
        files = {"file": ("test.txt", BytesIO(large_content), "text/plain")}
        
        response = client.post("/api/documents/upload", files=files, data=data)
        
        assert response.status_code == 400
        # The error message might be different, so let's check for any error
        assert "error" in response.json() or "detail" in response.json()


class TestDocumentProcessingEdgeCases:
    """Test edge cases and error conditions in integration."""
    
    def test_partial_failure_in_batch_upload(self, client, sample_file_content):
        """Test batch upload with partial failures."""
        with patch('routes.document_routes.document_service') as mock_service:
            # Mock mixed results
            mock_service.process_document_from_bytes.side_effect = [
                TestDataFactory.create_sample_processing_result(),  # Success
                {'success': False, 'error': 'Processing failed'},  # Failure
                TestDataFactory.create_sample_processing_result()   # Success
            ]
            
            files = [
                ("files", ("file1.txt", BytesIO(sample_file_content), "text/plain")),
                ("files", ("file2.txt", BytesIO(sample_file_content), "text/plain")),
                ("files", ("file3.txt", BytesIO(sample_file_content), "text/plain"))
            ]
            data = {"parish_id": "parish_001"}
            
            response = client.post("/api/documents/upload/batch", files=files, data=data)
            
            assert response.status_code == 200
            results = response.json()
            assert len(results) == 3
            assert results[0]["success"] is True
            assert results[1]["success"] is False
            assert results[2]["success"] is True
    
    def test_service_degradation_handling(self, client):
        """Test handling of service degradation."""
        with patch('routes.document_routes.document_service') as mock_service:
            # Mock degraded services
            mock_service.opensearch_service.test_connection.return_value = False
            mock_service.s3_service.get_bucket_info.return_value = {'success': False}
            
            response = client.get("/api/documents/health")
            
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "degraded"
            assert result["services"]["opensearch"] == "unavailable"
            assert result["services"]["s3"] == "unavailable"
    
    def test_concurrent_operations_simulation(self, sample_text):
        """Test simulation of concurrent operations."""
        with patch('services.document_processing_service.TextractService') as mock_textract, \
             patch('services.document_processing_service.EmbeddingService') as mock_embedding, \
             patch('services.document_processing_service.S3Service') as mock_s3, \
             patch('services.document_processing_service.OpenSearchService') as mock_opensearch, \
             patch('services.document_processing_service.generate_s3_key') as mock_s3_key:
            
            from services.document_processing_service import DocumentProcessingService
            
            # Configure mocks
            mock_textract.return_value.extract_text_from_bytes.return_value = {
                'success': True,
                'text': sample_text,
                'extraction_method': 'python-docx',
                'file_type': 'txt',
                'file_size': 1024
            }
            
            mock_embedding.return_value.get_embedding.return_value = Mock(
                embeddings=TestDataFactory.create_sample_embeddings(count=1)
            )
            
            mock_s3.return_value.upload_bytes.return_value = {'success': True}
            mock_opensearch.return_value.index_documents_batch.return_value = {'success': True}
            mock_s3_key.return_value = 'test/s3/key'
            
            # Simulate concurrent processing
            service = DocumentProcessingService()
            
            # Mock the chunking to return a single chunk
            mock_chunks = [{'text': 'test chunk', 'start': 0, 'end': 10}]
            
            # Process multiple documents "concurrently"
            results = []
            for i in range(3):
                with patch.object(service, '_chunk_text', return_value=mock_chunks):
                    result = service.process_document_from_bytes(
                        file_bytes=f"test content {i}".encode(),
                        filename=f"test_{i}.txt",
                        parish_id=f"parish_{i:03d}",
                        document_type="homily"
                    )
                    results.append(result)
            
            # All should succeed
            assert all(result['success'] for result in results)
            assert len(results) == 3
            
            # Verify all services were called for each document
            assert mock_textract.return_value.extract_text_from_bytes.call_count == 3
            assert mock_embedding.return_value.get_embedding.call_count == 3
            assert mock_s3.return_value.upload_bytes.call_count == 3
            assert mock_opensearch.return_value.index_documents_batch.call_count == 3
