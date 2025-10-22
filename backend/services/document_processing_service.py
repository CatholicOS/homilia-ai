#!/usr/bin/env python3
"""
Document Processing Service

This service orchestrates the complete document processing pipeline:
1. Text extraction using TextractService
2. Text chunking for optimal embedding and search
3. Embedding generation using EmbeddingService
4. Storage in S3 and indexing in OpenSearch

Features:
- Document text extraction and preprocessing
- Intelligent text chunking with overlap
- Embedding generation for semantic search
- S3 storage with consistent file_id
- OpenSearch indexing with metadata
- Batch processing capabilities
"""

import os
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import re
from pathlib import Path
import sys

# Add the services directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from textract_service import TextractService
from embedding_service import EmbeddingService
from s3_service import S3Service, generate_s3_key
from opensearch_service import OpenSearchService
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentProcessingService:
    """
    Service for processing documents through the complete pipeline.
    
    This service handles the end-to-end processing of documents:
    - Text extraction
    - Chunking
    - Embedding generation
    - Storage and indexing
    """
    
    def __init__(self):
        """Initialize the document processing service."""
        self.textract_service = TextractService()
        self.embedding_service = EmbeddingService()
        self.s3_service = S3Service()
        self.opensearch_service = OpenSearchService()
        
        # Initialize RecursiveCharacterTextSplitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # Characters per chunk
            chunk_overlap=200,  # Overlap between chunks
            length_function=len,
            separators=["\n\n", "\n", " ", ""]  # Split on paragraphs, lines, spaces, then characters
        )
        
        logger.info("DocumentProcessingService initialized")
    
    def process_document_from_file(self, 
                                 file_path: str, 
                                 parish_id: str,
                                 document_type: str = "document",
                                 metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a document from file path through the complete pipeline.
        
        Args:
            file_path: Path to the document file
            parish_id: Parish identifier
            document_type: Type of document (homily, bulletin, etc.)
            metadata: Additional metadata to store
            
        Returns:
            Dict containing processing results
        """
        try:
            # Generate unique file_id
            file_id = self._generate_file_id()
            
            # Extract text from document
            logger.info(f"Extracting text from file: {file_path}")
            extraction_result = self.textract_service.extract_text_from_file(file_path)
            
            if not extraction_result['success']:
                return {
                    'success': False,
                    'error': f"Text extraction failed: {extraction_result['error']}",
                    'file_id': file_id
                }
            
            # Get filename from path
            filename = Path(file_path).name
            
            # Process the extracted text
            return self._process_extracted_text(
                text=extraction_result['text'],
                file_id=file_id,
                filename=filename,
                parish_id=parish_id,
                document_type=document_type,
                extraction_metadata=extraction_result,
                additional_metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error processing document from file: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def process_document_from_bytes(self, 
                                 file_bytes: bytes, 
                                 filename: str,
                                 parish_id: str,
                                 document_type: str = "document",
                                 metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a document from bytes through the complete pipeline.
        
        Args:
            file_bytes: Document content as bytes
            filename: Original filename
            parish_id: Parish identifier
            document_type: Type of document (homily, bulletin, etc.)
            metadata: Additional metadata to store
            
        Returns:
            Dict containing processing results
        """
        try:
            # Generate unique file_id
            file_id = self._generate_file_id()
            
            # Extract text from document
            logger.info(f"Extracting text from bytes: {filename}")
            extraction_result = self.textract_service.extract_text_from_bytes(file_bytes, filename)
            
            if not extraction_result['success']:
                return {
                    'success': False,
                    'error': f"Text extraction failed: {extraction_result['error']}",
                    'file_id': file_id
                }
            
            # Process the extracted text
            return self._process_extracted_text(
                text=extraction_result['text'],
                file_id=file_id,
                filename=filename,
                parish_id=parish_id,
                document_type=document_type,
                extraction_metadata=extraction_result,
                additional_metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error processing document from bytes: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _process_extracted_text(self, 
                              text: str, 
                              file_id: str,
                              filename: str,
                              parish_id: str,
                              document_type: str,
                              extraction_metadata: Dict[str, Any],
                              additional_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process extracted text through chunking, embedding, and storage.
        
        Args:
            text: Extracted text content
            file_id: Unique file identifier
            filename: Original filename
            parish_id: Parish identifier
            document_type: Type of document
            extraction_metadata: Metadata from text extraction
            additional_metadata: Additional metadata
            
        Returns:
            Dict containing processing results
        """
        try:
            # Validate text
            if not text or not text.strip():
                return {
                    'success': False,
                    'error': 'No text content extracted from document',
                    'file_id': file_id
                }
            
            # Chunk the text
            logger.info(f"Chunking text for file_id: {file_id}")
            chunks = self._chunk_text(text)
            
            if not chunks:
                return {
                    'success': False,
                    'error': 'No valid chunks created from text',
                    'file_id': file_id
                }
            
            # Generate embeddings for chunks
            logger.info(f"Generating embeddings for {len(chunks)} chunks")
            embedding_result = self.embedding_service.get_embedding([chunk['text'] for chunk in chunks])
            
            if not embedding_result.embeddings:
                return {
                    'success': False,
                    'error': 'Failed to generate embeddings',
                    'file_id': file_id
                }
            
            # Store document in S3
            logger.info(f"Storing document in S3: {file_id}")
            s3_key = generate_s3_key(parish_id, document_type, filename)
            
            # Prepare metadata for S3
            s3_metadata = {
                'file_id': file_id,
                'parish_id': parish_id,
                'document_type': document_type,
                'filename': filename,
                'chunk_count': str(len(chunks)),
                'extraction_method': extraction_metadata.get('extraction_method', 'unknown'),
                'file_type': extraction_metadata.get('file_type', 'unknown'),
                'file_size': str(extraction_metadata.get('file_size', 0))
            }
            
            # Add additional metadata if provided
            if additional_metadata:
                for key, value in additional_metadata.items():
                    s3_metadata[f'meta_{key}'] = str(value)
            
            # Store original document in S3 (we'll store the extracted text as a backup)
            s3_result = self.s3_service.upload_bytes(
                file_bytes=text.encode('utf-8'),
                s3_key=s3_key,
                content_type='text/plain',
                metadata=s3_metadata
            )
            
            if not s3_result['success']:
                logger.warning(f"Failed to store document in S3: {s3_result['error']}")
                # Continue processing even if S3 storage fails
            
            # Prepare documents for OpenSearch indexing
            documents = []
            for i, chunk in enumerate(chunks):
                doc = {
                    'id': f"{file_id}_chunk_{i}",
                    'file_id': file_id,
                    'filename': filename,
                    'source': f"{parish_id}_{document_type}",
                    'text': chunk['text'],
                    'embedding': embedding_result.embeddings[i],
                    'metadata': {
                        'parish_id': parish_id,
                        'document_type': document_type,
                        'chunk_index': i,
                        'chunk_count': len(chunks),
                        'chunk_start': chunk['start'],
                        'chunk_end': chunk['end'],
                        's3_key': s3_key,
                        'extraction_method': extraction_metadata.get('extraction_method', 'unknown'),
                        'file_type': extraction_metadata.get('file_type', 'unknown'),
                        'file_size': extraction_metadata.get('file_size', 0),
                        'created_at': datetime.now(timezone.utc).isoformat()
                    }
                }
                
                # Add additional metadata
                if additional_metadata:
                    doc['metadata'].update(additional_metadata)
                
                documents.append(doc)
            
            # Index documents in OpenSearch
            logger.info(f"Indexing {len(documents)} chunks in OpenSearch")
            indexing_result = self.opensearch_service.index_documents_batch(documents)
            
            if not indexing_result['success']:
                return {
                    'success': False,
                    'error': f"Failed to index documents: {indexing_result['error']}",
                    'file_id': file_id,
                    's3_result': s3_result
                }
            
            # Refresh index to make documents searchable
            self.opensearch_service.refresh_index()
            
            logger.info(f"Successfully processed document with file_id: {file_id}")
            
            return {
                'success': True,
                'file_id': file_id,
                'filename': filename,
                'parish_id': parish_id,
                'document_type': document_type,
                'chunk_count': len(chunks),
                's3_key': s3_key,
                's3_result': s3_result,
                'indexing_result': indexing_result,
                'extraction_metadata': extraction_metadata,
                'processing_timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing extracted text: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks using RecursiveCharacterTextSplitter.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of chunk dictionaries with text and position info
        """
        try:
            if not text or not text.strip():
                return []
            
            # Use RecursiveCharacterTextSplitter to split text
            text_chunks = self.text_splitter.split_text(text)
            
            # Convert to our expected format with position tracking
            chunks = []
            current_pos = 0
            
            for chunk_text in text_chunks:
                if chunk_text.strip():  # Only add non-empty chunks
                    # Find the position of this chunk in the original text
                    start_pos = text.find(chunk_text.strip(), current_pos)
                    if start_pos == -1:
                        # Fallback: use current position
                        start_pos = current_pos
                    
                    end_pos = start_pos + len(chunk_text.strip())
                    
                    chunks.append({
                        'text': chunk_text.strip(),
                        'start': start_pos,
                        'end': end_pos
                    })
                    
                    # Update current position for next search
                    current_pos = end_pos
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}")
            return []
    
    
    def _generate_file_id(self) -> str:
        """Generate a unique file identifier."""
        return f"file_{uuid.uuid4().hex[:16]}"
    
    def delete_document(self, file_id: str) -> Dict[str, Any]:
        """
        Delete a document and all its chunks from the system.
        
        Args:
            file_id: File identifier to delete
            
        Returns:
            Dict containing deletion results
        """
        try:
            # Find all chunks for this file
            search_result = self.opensearch_service.search_by_file_id(file_id)
            
            if not search_result['success']:
                return {'success': False, 'error': f"Failed to find document: {search_result['error']}"}
            
            chunks = search_result['results']
            if not chunks:
                return {'success': True, 'message': 'No chunks found for this file_id'}
            
            # Get S3 keys to delete
            s3_keys = []
            chunk_ids = []
            
            for chunk in chunks:
                chunk_ids.append(chunk['id'])
                metadata = chunk['document'].get('metadata', {})
                s3_key = metadata.get('s3_key')
                if s3_key and s3_key not in s3_keys:
                    s3_keys.append(s3_key)
            
            # Delete chunks from OpenSearch
            deleted_chunks = 0
            for chunk_id in chunk_ids:
                delete_result = self.opensearch_service.delete_document(chunk_id)
                if delete_result['success']:
                    deleted_chunks += 1
            
            # Delete files from S3
            deleted_s3_files = 0
            for s3_key in s3_keys:
                delete_result = self.s3_service.delete_file(s3_key)
                if delete_result['success']:
                    deleted_s3_files += 1
            
            logger.info(f"Deleted document {file_id}: {deleted_chunks} chunks, {deleted_s3_files} S3 files")
            
            return {
                'success': True,
                'file_id': file_id,
                'deleted_chunks': deleted_chunks,
                'deleted_s3_files': deleted_s3_files,
                'total_chunks': len(chunks),
                'total_s3_files': len(s3_keys)
            }
            
        except Exception as e:
            logger.error(f"Error deleting document {file_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_document_info(self, file_id: str) -> Dict[str, Any]:
        """
        Get information about a processed document.
        
        Args:
            file_id: File identifier
            
        Returns:
            Dict containing document information
        """
        try:
            # Find all chunks for this file
            search_result = self.opensearch_service.search_by_file_id(file_id)
            
            if not search_result['success']:
                return {'success': False, 'error': f"Failed to find document: {search_result['error']}"}
            
            chunks = search_result['results']
            if not chunks:
                return {'success': False, 'error': 'Document not found'}
            
            # Get metadata from first chunk
            first_chunk = chunks[0]['document']
            metadata = first_chunk.get('metadata', {})
            
            return {
                'success': True,
                'file_id': file_id,
                'filename': first_chunk.get('filename'),
                'source': first_chunk.get('source'),
                'chunk_count': len(chunks),
                'parish_id': metadata.get('parish_id'),
                'document_type': metadata.get('document_type'),
                's3_key': metadata.get('s3_key'),
                'extraction_method': metadata.get('extraction_method'),
                'file_type': metadata.get('file_type'),
                'file_size': metadata.get('file_size'),
                'created_at': metadata.get('created_at')
            }
            
        except Exception as e:
            logger.error(f"Error getting document info for {file_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def search_documents(self, query: str, parish_id: Optional[str] = None, 
                        document_type: Optional[str] = None, k: int = 10) -> Dict[str, Any]:
        """
        Search documents using semantic search.
        
        Args:
            query: Search query
            parish_id: Optional parish filter
            document_type: Optional document type filter
            k: Number of results to return
            
        Returns:
            Dict containing search results
        """
        try:
            # Generate embedding for query
            embedding_result = self.embedding_service.get_embedding(query)
            
            if not embedding_result.embeddings:
                return {'success': False, 'error': 'Failed to generate query embedding'}
            
            # Build filter query
            filter_query = None
            if parish_id or document_type:
                filter_conditions = []
                if parish_id:
                    filter_conditions.append({"term": {"metadata.parish_id.keyword": parish_id}})
                if document_type:
                    filter_conditions.append({"term": {"metadata.document_type.keyword": document_type}})
                
                if len(filter_conditions) == 1:
                    filter_query = filter_conditions[0]
                else:
                    filter_query = {"bool": {"must": filter_conditions}}
            
            # Perform KNN search
            search_result = self.opensearch_service.knn_search(
                embedding=embedding_result.embeddings[0],
                k=k,
                filter_query=filter_query,
                fields_to_return=['file_id', 'filename', 'source', 'text', 'metadata']
            )
            
            if not search_result['success']:
                return {'success': False, 'error': f"Search failed: {search_result['error']}"}
            
            # Group results by file_id
            file_results = {}
            for result in search_result['results']:
                file_id = result['document']['file_id']
                if file_id not in file_results:
                    file_results[file_id] = {
                        'file_id': file_id,
                        'filename': result['document']['filename'],
                        'source': result['document']['source'],
                        'metadata': result['document']['metadata'],
                        'chunks': [],
                        'max_score': result['score']
                    }
                
                file_results[file_id]['chunks'].append({
                    'text': result['document']['text'],
                    'score': result['score'],
                    'chunk_index': result['document']['metadata'].get('chunk_index')
                })
            
            # Convert to list and sort by max score
            results = list(file_results.values())
            results.sort(key=lambda x: x['max_score'], reverse=True)
            
            return {
                'success': True,
                'query': query,
                'results': results,
                'total_files': len(results),
                'total_chunks': len(search_result['results'])
            }
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_documents_by_date(self, 
                             start_date: str, 
                             end_date: Optional[str] = None,
                             parish_id: Optional[str] = None,
                             document_type: Optional[str] = None,
                             limit: int = 100) -> Dict[str, Any]:
        """
        Get documents created within a date range.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (optional, defaults to start_date)
            parish_id: Optional parish filter
            document_type: Optional document type filter
            limit: Maximum number of results to return
            
        Returns:
            Dict containing documents created in the date range
        """
        try:
            from datetime import datetime
            
            # Parse start date
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                start_iso = start_dt.strftime("%Y-%m-%dT00:00:00Z")
            except ValueError:
                return {'success': False, 'error': 'Invalid start_date format. Use YYYY-MM-DD'}
            
            # Parse end date or default to start date
            if end_date:
                try:
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                    end_iso = end_dt.strftime("%Y-%m-%dT23:59:59Z")
                except ValueError:
                    return {'success': False, 'error': 'Invalid end_date format. Use YYYY-MM-DD'}
            else:
                end_iso = start_dt.strftime("%Y-%m-%dT23:59:59Z")
            
            # Build date range query
            date_query = {
                "range": {
                    "metadata.created_at": {
                        "gte": start_iso,
                        "lte": end_iso
                    }
                }
            }
            
            # Build filter conditions
            filter_conditions = [date_query]
            
            if parish_id:
                filter_conditions.append({"term": {"metadata.parish_id.keyword": parish_id}})
            
            if document_type:
                filter_conditions.append({"term": {"metadata.document_type.keyword": document_type}})
            
            # Create the main query
            if len(filter_conditions) == 1:
                query = date_query
            else:
                query = {"bool": {"must": filter_conditions}}
            
            # Perform the search
            search_result = self.opensearch_service.field_search(
                query=query,
                size=limit,
                fields_to_return=['file_id', 'filename', 'source', 'metadata'],
                sort=[{"metadata.created_at": {"order": "desc"}}]
            )
            
            if not search_result['success']:
                return {'success': False, 'error': f"Search failed: {search_result['error']}"}
            
            # Group results by file_id to get unique documents
            file_results = {}
            for result in search_result['results']:
                file_id = result['document']['file_id']
                if file_id not in file_results:
                    file_results[file_id] = {
                        'file_id': file_id,
                        'filename': result['document']['filename'],
                        'source': result['document']['source'],
                        'metadata': result['document']['metadata'],
                        'created_at': result['document']['metadata'].get('created_at')
                    }
            
            # Convert to list and sort by creation date (newest first)
            results = list(file_results.values())
            results.sort(key=lambda x: x['created_at'], reverse=True)
            
            return {
                'success': True,
                'start_date': start_date,
                'end_date': end_date or start_date,
                'results': results,
                'total_documents': len(results),
                'total_chunks': len(search_result['results'])
            }
            
        except Exception as e:
            logger.error(f"Error getting documents by date: {str(e)}")
            return {'success': False, 'error': str(e)}


# Example usage and testing functions
def test_document_processing_service():
    """Test function to demonstrate document processing service usage."""
    
    # Initialize service
    service = DocumentProcessingService()
    
    print("✅ DocumentProcessingService initialized")
    
    # Test with sample text
    sample_text = """
    This is a sample document for testing the document processing service.
    It contains multiple sentences that will be chunked and processed.
    The service will extract text, create chunks, generate embeddings,
    and store everything in S3 and OpenSearch.
    This is another paragraph with more content to test chunking.
    The chunking algorithm should handle overlapping chunks properly.
    """
    
    # Test chunking
    chunks = service._chunk_text(sample_text)
    print(f"✅ Created {len(chunks)} chunks from sample text")
    
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i}: {chunk['text'][:50]}...")


if __name__ == "__main__":
    test_document_processing_service()
