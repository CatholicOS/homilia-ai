#!/usr/bin/env python3
"""
Comprehensive unit tests for document_processing_service.py

Tests all functionality of the DocumentProcessingService class.
"""

import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from typing import Dict, Any, List
from pathlib import Path

from tests.conftest import (
    sample_text, sample_chunks, sample_embeddings, 
    sample_processing_result, sample_document_info,
    sample_search_results, sample_delete_result, temp_file
)


class TestDocumentProcessingService:
    """Test class for DocumentProcessingService."""
    
    def test_init(self):
        """Test service initialization."""
        with patch('services.document_processing_service.TextractService') as mock_textract, \
             patch('services.document_processing_service.EmbeddingService') as mock_embedding, \
             patch('services.document_processing_service.S3Service') as mock_s3, \
             patch('services.document_processing_service.OpenSearchService') as mock_opensearch:
            
            from services.document_processing_service import DocumentProcessingService
            
            service = DocumentProcessingService()
            
            assert service.textract_service is not None
            assert service.embedding_service is not None
            assert service.s3_service is not None
            assert service.opensearch_service is not None
            assert service.text_splitter is not None
    
    def test_process_document_from_file_success(self, temp_file, sample_text, sample_embeddings):
        """Test successful document processing from file."""
        with patch('services.document_processing_service.TextractService') as mock_textract, \
             patch('services.document_processing_service.EmbeddingService') as mock_embedding, \
             patch('services.document_processing_service.S3Service') as mock_s3, \
             patch('services.document_processing_service.OpenSearchService') as mock_opensearch, \
             patch('services.document_processing_service.generate_s3_key') as mock_s3_key:
            
            from services.document_processing_service import DocumentProcessingService
            
            # Configure mocks
            mock_textract.return_value.extract_text_from_file.return_value = {
                'success': True,
                'text': sample_text,
                'extraction_method': 'python-docx',
                'file_type': 'txt',
                'file_size': 1024
            }
            
            # Mock the chunking to return 3 chunks
            mock_chunks = [
                {'text': 'chunk 1', 'start': 0, 'end': 10},
                {'text': 'chunk 2', 'start': 10, 'end': 20},
                {'text': 'chunk 3', 'start': 20, 'end': 30}
            ]
            
            mock_embedding.return_value.get_embedding.return_value = Mock(
                embeddings=[sample_embeddings] * 3
            )
            
            mock_s3.return_value.upload_bytes.return_value = {'success': True}
            mock_opensearch.return_value.index_documents_batch.return_value = {'success': True}
            mock_s3_key.return_value = 'test/s3/key'
            
            service = DocumentProcessingService()
            
            # Mock the _chunk_text method to return our expected chunks
            with patch.object(service, '_chunk_text', return_value=mock_chunks):
                result = service.process_document_from_file(
                    file_path=temp_file,
                    parish_id='parish_001',
                    document_type='homily'
                )
            
            assert result['success'] is True
            assert 'file_id' in result
            assert result['filename'] == Path(temp_file).name  # From temp_file
            assert result['parish_id'] == 'parish_001'
            assert result['document_type'] == 'homily'
            assert result['chunk_count'] == 3
    
    def test_process_document_from_file_extraction_failure(self, temp_file):
        """Test document processing when text extraction fails."""
        with patch('services.document_processing_service.TextractService') as mock_textract:
            from services.document_processing_service import DocumentProcessingService
            
            mock_textract.return_value.extract_text_from_file.return_value = {
                'success': False,
                'error': 'Extraction failed'
            }
            
            service = DocumentProcessingService()
            result = service.process_document_from_file(
                file_path=temp_file,
                parish_id='parish_001'
            )
            
            assert result['success'] is False
            assert 'Extraction failed' in result['error']
    
    def test_process_document_from_bytes_success(self, sample_text, sample_embeddings):
        """Test successful document processing from bytes."""
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
            
            # Mock the chunking to return 3 chunks
            mock_chunks = [
                {'text': 'chunk 1', 'start': 0, 'end': 10},
                {'text': 'chunk 2', 'start': 10, 'end': 20},
                {'text': 'chunk 3', 'start': 20, 'end': 30}
            ]
            
            mock_embedding.return_value.get_embedding.return_value = Mock(
                embeddings=[sample_embeddings] * 3
            )
            
            mock_s3.return_value.upload_bytes.return_value = {'success': True}
            mock_opensearch.return_value.index_documents_batch.return_value = {'success': True}
            mock_s3_key.return_value = 'test/s3/key'
            
            service = DocumentProcessingService()
            
            # Mock the _chunk_text method to return our expected chunks
            with patch.object(service, '_chunk_text', return_value=mock_chunks):
                result = service.process_document_from_bytes(
                    file_bytes=b"test content",
                    filename="test.txt",
                    parish_id='parish_001',
                    document_type='homily',
                    metadata={'author': 'test'}
                )
            
            assert result['success'] is True
            assert 'file_id' in result
            assert result['filename'] == 'test.txt'
            assert result['parish_id'] == 'parish_001'
            assert result['document_type'] == 'homily'
            assert result['chunk_count'] == 3
    
    def test_process_document_from_bytes_extraction_failure(self):
        """Test document processing from bytes when extraction fails."""
        with patch('services.document_processing_service.TextractService') as mock_textract:
            from services.document_processing_service import DocumentProcessingService
            
            mock_textract.return_value.extract_text_from_bytes.return_value = {
                'success': False,
                'error': 'Extraction failed'
            }
            
            service = DocumentProcessingService()
            result = service.process_document_from_bytes(
                file_bytes=b"test content",
                filename="test.txt",
                parish_id='parish_001'
            )
            
            assert result['success'] is False
            assert 'Extraction failed' in result['error']
    
    def test_process_extracted_text_empty_text(self):
        """Test processing extracted text with empty text."""
        with patch('services.document_processing_service.EmbeddingService'), \
             patch('services.document_processing_service.S3Service'), \
             patch('services.document_processing_service.OpenSearchService'):
            
            from services.document_processing_service import DocumentProcessingService
            
            service = DocumentProcessingService()
            result = service._process_extracted_text(
                text="",
                file_id="test_file_id",
                filename="test.txt",
                parish_id="parish_001",
                document_type="homily",
                extraction_metadata={}
            )
            
            assert result['success'] is False
            assert 'No text content extracted' in result['error']
    
    def test_process_extracted_text_no_chunks(self, sample_text):
        """Test processing extracted text that produces no chunks."""
        with patch('services.document_processing_service.EmbeddingService'), \
             patch('services.document_processing_service.S3Service'), \
             patch('services.document_processing_service.OpenSearchService'):
            
            from services.document_processing_service import DocumentProcessingService
            
            service = DocumentProcessingService()
            
            # Mock _chunk_text to return empty list
            with patch.object(service, '_chunk_text', return_value=[]):
                result = service._process_extracted_text(
                    text=sample_text,
                    file_id="test_file_id",
                    filename="test.txt",
                    parish_id="parish_001",
                    document_type="homily",
                    extraction_metadata={}
                )
                
                assert result['success'] is False
                assert 'No valid chunks created' in result['error']
    
    def test_process_extracted_text_embedding_failure(self, sample_text, sample_chunks):
        """Test processing extracted text when embedding generation fails."""
        with patch('services.document_processing_service.EmbeddingService') as mock_embedding, \
             patch('services.document_processing_service.S3Service'), \
             patch('services.document_processing_service.OpenSearchService'):
            
            from services.document_processing_service import DocumentProcessingService
            
            mock_embedding.return_value.get_embedding.return_value = Mock(embeddings=[])
            
            service = DocumentProcessingService()
            
            with patch.object(service, '_chunk_text', return_value=sample_chunks):
                result = service._process_extracted_text(
                    text=sample_text,
                    file_id="test_file_id",
                    filename="test.txt",
                    parish_id="parish_001",
                    document_type="homily",
                    extraction_metadata={}
                )
                
                assert result['success'] is False
                assert 'Failed to generate embeddings' in result['error']
    
    def test_process_extracted_text_s3_failure_continues(self, sample_text, sample_chunks, sample_embeddings):
        """Test processing continues even when S3 storage fails."""
        with patch('services.document_processing_service.EmbeddingService') as mock_embedding, \
             patch('services.document_processing_service.S3Service') as mock_s3, \
             patch('services.document_processing_service.OpenSearchService') as mock_opensearch, \
             patch('services.document_processing_service.generate_s3_key') as mock_s3_key:
            
            from services.document_processing_service import DocumentProcessingService
            
            mock_embedding.return_value.get_embedding.return_value = Mock(
                embeddings=[sample_embeddings] * 3
            )
            mock_s3.return_value.upload_bytes.return_value = {'success': False, 'error': 'S3 failed'}
            mock_opensearch.return_value.index_documents_batch.return_value = {'success': True}
            mock_s3_key.return_value = 'test/s3/key'
            
            service = DocumentProcessingService()
            
            with patch.object(service, '_chunk_text', return_value=sample_chunks):
                result = service._process_extracted_text(
                    text=sample_text,
                    file_id="test_file_id",
                    filename="test.txt",
                    parish_id="parish_001",
                    document_type="homily",
                    extraction_metadata={}
                )
                
                # Should still succeed despite S3 failure
                assert result['success'] is True
                assert result['s3_result']['success'] is False
    
    def test_process_extracted_text_indexing_failure(self, sample_text, sample_chunks, sample_embeddings):
        """Test processing fails when OpenSearch indexing fails."""
        with patch('services.document_processing_service.EmbeddingService') as mock_embedding, \
             patch('services.document_processing_service.S3Service') as mock_s3, \
             patch('services.document_processing_service.OpenSearchService') as mock_opensearch, \
             patch('services.document_processing_service.generate_s3_key') as mock_s3_key:
            
            from services.document_processing_service import DocumentProcessingService
            
            mock_embedding.return_value.get_embedding.return_value = Mock(
                embeddings=[sample_embeddings] * 3
            )
            mock_s3.return_value.upload_bytes.return_value = {'success': True}
            mock_opensearch.return_value.index_documents_batch.return_value = {
                'success': False,
                'error': 'Indexing failed'
            }
            mock_s3_key.return_value = 'test/s3/key'
            
            service = DocumentProcessingService()
            
            with patch.object(service, '_chunk_text', return_value=sample_chunks):
                result = service._process_extracted_text(
                    text=sample_text,
                    file_id="test_file_id",
                    filename="test.txt",
                    parish_id="parish_001",
                    document_type="homily",
                    extraction_metadata={}
                )
                
                assert result['success'] is False
                assert 'Failed to index documents' in result['error']
    
    def test_chunk_text_success(self, sample_text):
        """Test successful text chunking."""
        from services.document_processing_service import DocumentProcessingService
        
        service = DocumentProcessingService()
        chunks = service._chunk_text(sample_text)
        
        assert len(chunks) > 0
        for chunk in chunks:
            assert 'text' in chunk
            assert 'start' in chunk
            assert 'end' in chunk
            assert chunk['text'].strip() != ""
            assert chunk['start'] >= 0
            assert chunk['end'] > chunk['start']
    
    def test_chunk_text_empty(self):
        """Test chunking empty text."""
        from services.document_processing_service import DocumentProcessingService
        
        service = DocumentProcessingService()
        chunks = service._chunk_text("")
        
        assert chunks == []
    
    def test_chunk_text_whitespace_only(self):
        """Test chunking whitespace-only text."""
        from services.document_processing_service import DocumentProcessingService
        
        service = DocumentProcessingService()
        chunks = service._chunk_text("   \n\n   ")
        
        assert chunks == []
    
    def test_generate_file_id(self):
        """Test file ID generation."""
        from services.document_processing_service import DocumentProcessingService
        
        service = DocumentProcessingService()
        file_id1 = service._generate_file_id()
        file_id2 = service._generate_file_id()
        
        assert file_id1.startswith("file_")
        assert file_id2.startswith("file_")
        assert file_id1 != file_id2
        assert len(file_id1) == 21  # "file_" + 16 hex chars
    
    def test_delete_document_success(self):
        """Test successful document deletion."""
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
            assert result['file_id'] == 'file_123'
            assert result['deleted_chunks'] == 2
            assert result['deleted_s3_files'] == 1
            assert result['total_chunks'] == 2
            assert result['total_s3_files'] == 1
    
    def test_delete_document_not_found(self):
        """Test document deletion when document not found."""
        with patch('services.document_processing_service.OpenSearchService') as mock_opensearch:
            from services.document_processing_service import DocumentProcessingService
            
            mock_opensearch.return_value.search_by_file_id.return_value = {
                'success': True,
                'results': []
            }
            
            service = DocumentProcessingService()
            result = service.delete_document('nonexistent_file')
            
            assert result['success'] is True
            assert 'No chunks found' in result['message']
    
    def test_delete_document_search_failure(self):
        """Test document deletion when search fails."""
        with patch('services.document_processing_service.OpenSearchService') as mock_opensearch:
            from services.document_processing_service import DocumentProcessingService
            
            mock_opensearch.return_value.search_by_file_id.return_value = {
                'success': False,
                'error': 'Search failed'
            }
            
            service = DocumentProcessingService()
            result = service.delete_document('file_123')
            
            assert result['success'] is False
            assert 'Failed to find document' in result['error']
    
    def test_get_document_info_success(self):
        """Test successful document info retrieval."""
        with patch('services.document_processing_service.OpenSearchService') as mock_opensearch:
            from services.document_processing_service import DocumentProcessingService
            
            mock_opensearch.return_value.search_by_file_id.return_value = {
                'success': True,
                'results': [
                    {
                        'document': {
                            'filename': 'test.txt',
                            'source': 'parish_001_homily',
                            'metadata': {
                                'parish_id': 'parish_001',
                                'document_type': 'homily',
                                's3_key': 'test/s3/key',
                                'extraction_method': 'python-docx',
                                'file_type': 'txt',
                                'file_size': 1024,
                                'created_at': '2024-01-01T12:00:00Z'
                            }
                        }
                    },
                    {
                        'document': {
                            'filename': 'test.txt',
                            'source': 'parish_001_homily',
                            'metadata': {}
                        }
                    }
                ]
            }
            
            service = DocumentProcessingService()
            result = service.get_document_info('file_123')
            
            assert result['success'] is True
            assert result['file_id'] == 'file_123'
            assert result['filename'] == 'test.txt'
            assert result['source'] == 'parish_001_homily'
            assert result['chunk_count'] == 2
            assert result['parish_id'] == 'parish_001'
            assert result['document_type'] == 'homily'
    
    def test_get_document_info_not_found(self):
        """Test document info retrieval when document not found."""
        with patch('services.document_processing_service.OpenSearchService') as mock_opensearch:
            from services.document_processing_service import DocumentProcessingService
            
            mock_opensearch.return_value.search_by_file_id.return_value = {
                'success': True,
                'results': []
            }
            
            service = DocumentProcessingService()
            result = service.get_document_info('nonexistent_file')
            
            assert result['success'] is False
            assert result['error'] == 'Document not found'
    
    def test_get_document_info_search_failure(self):
        """Test document info retrieval when search fails."""
        with patch('services.document_processing_service.OpenSearchService') as mock_opensearch:
            from services.document_processing_service import DocumentProcessingService
            
            mock_opensearch.return_value.search_by_file_id.return_value = {
                'success': False,
                'error': 'Search failed'
            }
            
            service = DocumentProcessingService()
            result = service.get_document_info('file_123')
            
            assert result['success'] is False
            assert 'Failed to find document' in result['error']
    
    def test_search_documents_success(self):
        """Test successful document search."""
        with patch('services.document_processing_service.EmbeddingService') as mock_embedding, \
             patch('services.document_processing_service.OpenSearchService') as mock_opensearch:
            
            from services.document_processing_service import DocumentProcessingService
            
            mock_embedding.return_value.get_embedding.return_value = Mock(
                embeddings=[sample_embeddings]
            )
            
            mock_opensearch.return_value.knn_search.return_value = {
                'success': True,
                'results': [
                    {
                        'document': {
                            'file_id': 'file_123',
                            'filename': 'test.txt',
                            'source': 'parish_001_homily',
                            'text': 'Sample text',
                            'metadata': {
                                'parish_id': 'parish_001',
                                'document_type': 'homily',
                                'chunk_index': 0
                            }
                        },
                        'score': 0.95
                    }
                ]
            }
            
            service = DocumentProcessingService()
            result = service.search_documents(
                query='test query',
                parish_id='parish_001',
                document_type='homily',
                k=10
            )
            
            assert result['success'] is True
            assert result['query'] == 'test query'
            assert len(result['results']) == 1
            assert result['total_files'] == 1
            assert result['total_chunks'] == 1
            
            # Check that results are grouped by file_id
            file_result = result['results'][0]
            assert file_result['file_id'] == 'file_123'
            assert file_result['filename'] == 'test.txt'
            assert len(file_result['chunks']) == 1
    
    def test_search_documents_embedding_failure(self):
        """Test document search when embedding generation fails."""
        with patch('services.document_processing_service.EmbeddingService') as mock_embedding:
            from services.document_processing_service import DocumentProcessingService
            
            mock_embedding.return_value.get_embedding.return_value = Mock(embeddings=[])
            
            service = DocumentProcessingService()
            result = service.search_documents(query='test query')
            
            assert result['success'] is False
            assert 'Failed to generate query embedding' in result['error']
    
    def test_search_documents_search_failure(self):
        """Test document search when OpenSearch search fails."""
        with patch('services.document_processing_service.EmbeddingService') as mock_embedding, \
             patch('services.document_processing_service.OpenSearchService') as mock_opensearch:
            
            from services.document_processing_service import DocumentProcessingService
            
            mock_embedding.return_value.get_embedding.return_value = Mock(
                embeddings=[sample_embeddings]
            )
            
            mock_opensearch.return_value.knn_search.return_value = {
                'success': False,
                'error': 'Search failed'
            }
            
            service = DocumentProcessingService()
            result = service.search_documents(query='test query')
            
            assert result['success'] is False
            assert 'Search failed' in result['error']
    
    def test_search_documents_with_filters(self):
        """Test document search with parish and document type filters."""
        with patch('services.document_processing_service.EmbeddingService') as mock_embedding, \
             patch('services.document_processing_service.OpenSearchService') as mock_opensearch:
            
            from services.document_processing_service import DocumentProcessingService
            
            mock_embedding.return_value.get_embedding.return_value = Mock(
                embeddings=[sample_embeddings]
            )
            
            mock_opensearch.return_value.knn_search.return_value = {
                'success': True,
                'results': []
            }
            
            service = DocumentProcessingService()
            service.search_documents(
                query='test query',
                parish_id='parish_001',
                document_type='homily'
            )
            
            # Verify that knn_search was called with proper filter
            mock_opensearch.return_value.knn_search.assert_called_once()
            call_args = mock_opensearch.return_value.knn_search.call_args
            
            # Check that filter_query was passed
            assert 'filter_query' in call_args.kwargs
            filter_query = call_args.kwargs['filter_query']
            
            # Should have both parish_id and document_type filters
            assert 'bool' in filter_query
            assert 'must' in filter_query['bool']
            assert len(filter_query['bool']['must']) == 2
    
    def test_search_documents_no_filters(self):
        """Test document search without filters."""
        with patch('services.document_processing_service.EmbeddingService') as mock_embedding, \
             patch('services.document_processing_service.OpenSearchService') as mock_opensearch:
            
            from services.document_processing_service import DocumentProcessingService
            
            mock_embedding.return_value.get_embedding.return_value = Mock(
                embeddings=[sample_embeddings]
            )
            
            mock_opensearch.return_value.knn_search.return_value = {
                'success': True,
                'results': []
            }
            
            service = DocumentProcessingService()
            service.search_documents(query='test query')
            
            # Verify that knn_search was called without filter
            mock_opensearch.return_value.knn_search.assert_called_once()
            call_args = mock_opensearch.return_value.knn_search.call_args
            
            # Check that no filter_query was passed
            assert call_args.kwargs.get('filter_query') is None


class TestDocumentProcessingServiceEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_process_document_exception_handling(self):
        """Test exception handling in document processing."""
        with patch('services.document_processing_service.TextractService') as mock_textract:
            from services.document_processing_service import DocumentProcessingService
            
            mock_textract.return_value.extract_text_from_bytes.side_effect = Exception("Unexpected error")
            
            service = DocumentProcessingService()
            result = service.process_document_from_bytes(
                file_bytes=b"test",
                filename="test.txt",
                parish_id="parish_001"
            )
            
            assert result['success'] is False
            assert 'Unexpected error' in result['error']
    
    def test_chunk_text_exception_handling(self):
        """Test exception handling in text chunking."""
        from services.document_processing_service import DocumentProcessingService
        
        service = DocumentProcessingService()
        
        # Mock the text splitter to raise an exception
        with patch.object(service.text_splitter, 'split_text', side_effect=Exception("Chunking error")):
            chunks = service._chunk_text(sample_text)
            
            assert chunks == []
    
    def test_delete_document_exception_handling(self):
        """Test exception handling in document deletion."""
        with patch('services.document_processing_service.OpenSearchService') as mock_opensearch:
            from services.document_processing_service import DocumentProcessingService
            
            mock_opensearch.return_value.search_by_file_id.side_effect = Exception("Search error")
            
            service = DocumentProcessingService()
            result = service.delete_document('file_123')
            
            assert result['success'] is False
            assert 'Search error' in result['error']
    
    def test_get_document_info_exception_handling(self):
        """Test exception handling in document info retrieval."""
        with patch('services.document_processing_service.OpenSearchService') as mock_opensearch:
            from services.document_processing_service import DocumentProcessingService
            
            mock_opensearch.return_value.search_by_file_id.side_effect = Exception("Search error")
            
            service = DocumentProcessingService()
            result = service.get_document_info('file_123')
            
            assert result['success'] is False
            assert 'Search error' in result['error']
    
    def test_search_documents_exception_handling(self):
        """Test exception handling in document search."""
        with patch('services.document_processing_service.EmbeddingService') as mock_embedding:
            from services.document_processing_service import DocumentProcessingService
            
            mock_embedding.return_value.get_embedding.side_effect = Exception("Embedding error")
            
            service = DocumentProcessingService()
            result = service.search_documents(query='test query')
            
            assert result['success'] is False
            assert 'Embedding error' in result['error']
