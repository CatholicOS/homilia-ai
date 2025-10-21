#!/usr/bin/env python3
"""
Document Upload API Routes

FastAPI routes for document upload and processing.
This module provides endpoints for uploading documents and processing them
through the complete pipeline: text extraction, chunking, embedding, and indexing.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import sys
import os
import logging

# Add the services directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services'))

from document_processing_service import DocumentProcessingService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/documents", tags=["documents"])

# Initialize service
document_service = DocumentProcessingService()

# Pydantic models for request/response
class DocumentUploadResponse(BaseModel):
    success: bool
    file_id: Optional[str] = None
    filename: Optional[str] = None
    parish_id: Optional[str] = None
    document_type: Optional[str] = None
    chunk_count: Optional[int] = None
    s3_key: Optional[str] = None
    error: Optional[str] = None
    processing_timestamp: Optional[str] = None

class DocumentInfoResponse(BaseModel):
    success: bool
    file_id: Optional[str] = None
    filename: Optional[str] = None
    source: Optional[str] = None
    chunk_count: Optional[int] = None
    parish_id: Optional[str] = None
    document_type: Optional[str] = None
    s3_key: Optional[str] = None
    extraction_method: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    created_at: Optional[str] = None
    error: Optional[str] = None

class DocumentSearchResponse(BaseModel):
    success: bool
    query: Optional[str] = None
    results: Optional[List[Dict[str, Any]]] = None
    total_files: Optional[int] = None
    total_chunks: Optional[int] = None
    error: Optional[str] = None

class DocumentDeleteResponse(BaseModel):
    success: bool
    file_id: Optional[str] = None
    deleted_chunks: Optional[int] = None
    deleted_s3_files: Optional[int] = None
    total_chunks: Optional[int] = None
    total_s3_files: Optional[int] = None
    error: Optional[str] = None

class DocumentByDateResponse(BaseModel):
    success: bool
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    results: Optional[List[Dict[str, Any]]] = None
    total_documents: Optional[int] = None
    total_chunks: Optional[int] = None
    error: Optional[str] = None


# Utility functions
def validate_file_type(filename: str) -> bool:
    """Validate if file type is supported."""
    supported_extensions = ['.pdf', '.docx', '.doc', '.txt', '.rtf']
    file_ext = os.path.splitext(filename)[1].lower()
    return file_ext in supported_extensions

def validate_file_size(file_size: int, max_size_mb: int = 50) -> bool:
    """Validate file size."""
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload"),
    parish_id: str = Form(..., description="Parish identifier"),
    document_type: str = Form(default="document", description="Type of document"),
    use_textract: bool = Form(default=False, description="Use AWS Textract for PDF processing"),
    metadata: Optional[str] = Form(default=None, description="Additional metadata as JSON string")
):
    """
    Upload and process a document through the complete pipeline.
    
    This endpoint handles:
    1. File validation
    2. Text extraction
    3. Text chunking
    4. Embedding generation
    5. S3 storage
    6. OpenSearch indexing
    
    Args:
        file: Document file to upload
        parish_id: Parish identifier
        document_type: Type of document (homily, bulletin, etc.)
        use_textract: Whether to use AWS Textract for PDF files
        metadata: Additional metadata as JSON string
        
    Returns:
        DocumentUploadResponse with processing results
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        if not validate_file_type(file.filename):
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Supported types: .pdf, .docx, .doc, .txt, .rtf"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Validate file size
        if not validate_file_size(len(file_content)):
            raise HTTPException(
                status_code=400, 
                detail="File too large. Maximum size is 50MB"
            )
        
        # Parse additional metadata if provided
        additional_metadata = None
        if metadata:
            try:
                import json
                additional_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid metadata JSON format")
        
        # Process document
        logger.info(f"Processing document: {file.filename} for parish: {parish_id}")
        
        result = document_service.process_document_from_bytes(
            file_bytes=file_content,
            filename=file.filename,
            parish_id=parish_id,
            document_type=document_type,
            metadata=additional_metadata
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result['error'])
        
        logger.info(f"Successfully processed document: {result['file_id']}")
        
        return DocumentUploadResponse(
            success=True,
            file_id=result['file_id'],
            filename=result['filename'],
            parish_id=result['parish_id'],
            document_type=result['document_type'],
            chunk_count=result['chunk_count'],
            s3_key=result['s3_key'],
            processing_timestamp=result['processing_timestamp']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/upload/batch", response_model=List[DocumentUploadResponse])
async def upload_documents_batch(
    files: List[UploadFile] = File(..., description="List of document files to upload"),
    parish_id: str = Form(..., description="Parish identifier"),
    document_type: str = Form(default="document", description="Type of document"),
    use_textract: bool = Form(default=False, description="Use AWS Textract for PDF processing"),
    metadata: Optional[str] = Form(default=None, description="Additional metadata as JSON string")
):
    """
    Upload and process multiple documents in batch.
    
    Args:
        files: List of document files to upload
        parish_id: Parish identifier
        document_type: Type of document
        use_textract: Whether to use AWS Textract for PDF files
        metadata: Additional metadata as JSON string
        
    Returns:
        List of DocumentUploadResponse with processing results
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        if len(files) > 10:  # Limit batch size
            raise HTTPException(status_code=400, detail="Too many files. Maximum 10 files per batch")
        
        # Parse additional metadata if provided
        additional_metadata = None
        if metadata:
            try:
                import json
                additional_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid metadata JSON format")
        
        results = []
        
        for file in files:
            try:
                # Validate file
                if not file.filename:
                    results.append(DocumentUploadResponse(
                        success=False,
                        error="No filename provided"
                    ))
                    continue
                
                if not validate_file_type(file.filename):
                    results.append(DocumentUploadResponse(
                        success=False,
                        error=f"Unsupported file type: {file.filename}"
                    ))
                    continue
                
                # Read file content
                file_content = await file.read()
                
                # Validate file size
                if not validate_file_size(len(file_content)):
                    results.append(DocumentUploadResponse(
                        success=False,
                        error=f"File too large: {file.filename}"
                    ))
                    continue
                
                # Process document
                result = document_service.process_document_from_bytes(
                    file_bytes=file_content,
                    filename=file.filename,
                    parish_id=parish_id,
                    document_type=document_type,
                    metadata=additional_metadata
                )
                
                if result['success']:
                    results.append(DocumentUploadResponse(
                        success=True,
                        file_id=result['file_id'],
                        filename=result['filename'],
                        parish_id=result['parish_id'],
                        document_type=result['document_type'],
                        chunk_count=result['chunk_count'],
                        s3_key=result['s3_key'],
                        processing_timestamp=result['processing_timestamp']
                    ))
                else:
                    results.append(DocumentUploadResponse(
                        success=False,
                        error=result['error']
                    ))
                    
            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {str(e)}")
                results.append(DocumentUploadResponse(
                    success=False,
                    error=f"Error processing file: {str(e)}"
                ))
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/info/{file_id}", response_model=DocumentInfoResponse)
async def get_document_info(file_id: str):
    """
    Get information about a processed document.
    
    Args:
        file_id: File identifier
        
    Returns:
        DocumentInfoResponse with document information
    """
    try:
        result = document_service.get_document_info(file_id)
        
        if not result['success']:
            if result['error'] == 'Document not found':
                raise HTTPException(status_code=404, detail="Document not found")
            raise HTTPException(status_code=500, detail=result['error'])
        
        return DocumentInfoResponse(
            success=True,
            file_id=result['file_id'],
            filename=result['filename'],
            source=result['source'],
            chunk_count=result['chunk_count'],
            parish_id=result['parish_id'],
            document_type=result['document_type'],
            s3_key=result['s3_key'],
            extraction_method=result['extraction_method'],
            file_type=result['file_type'],
            file_size=result['file_size'],
            created_at=result['created_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/search", response_model=DocumentSearchResponse)
async def search_documents(
    query: str = Form(..., description="Search query"),
    parish_id: Optional[str] = Form(default=None, description="Parish filter"),
    document_type: Optional[str] = Form(default=None, description="Document type filter"),
    k: int = Form(default=10, description="Number of results to return")
):
    """
    Search documents using semantic search.
    
    Args:
        query: Search query
        parish_id: Optional parish filter
        document_type: Optional document type filter
        k: Number of results to return
        
    Returns:
        DocumentSearchResponse with search results
    """
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        result = document_service.search_documents(
            query=query,
            parish_id=parish_id,
            document_type=document_type,
            k=k
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return DocumentSearchResponse(
            success=True,
            query=result['query'],
            results=result['results'],
            total_files=result['total_files'],
            total_chunks=result['total_chunks']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/{file_id}", response_model=DocumentDeleteResponse)
async def delete_document(file_id: str):
    """
    Delete a document and all its chunks from the system.
    
    Args:
        file_id: File identifier to delete
        
    Returns:
        DocumentDeleteResponse with deletion results
    """
    try:
        result = document_service.delete_document(file_id)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return DocumentDeleteResponse(
            success=True,
            file_id=result['file_id'],
            deleted_chunks=result['deleted_chunks'],
            deleted_s3_files=result['deleted_s3_files'],
            total_chunks=result['total_chunks'],
            total_s3_files=result['total_s3_files']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/by-date", response_model=DocumentByDateResponse)
async def get_documents_by_date(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(default=None, description="End date in YYYY-MM-DD format"),
    parish_id: Optional[str] = Query(default=None, description="Parish filter"),
    document_type: Optional[str] = Query(default=None, description="Document type filter"),
    limit: int = Query(default=100, description="Maximum number of results to return")
):
    """
    Get documents created within a date range.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (optional, defaults to start_date)
        parish_id: Optional parish filter
        document_type: Optional document type filter
        limit: Maximum number of results to return
        
    Returns:
        DocumentByDateResponse with documents created in the date range
    """
    try:
        # Validate date format
        try:
            from datetime import datetime
            datetime.strptime(start_date, "%Y-%m-%d")
            if end_date:
                datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        result = document_service.get_documents_by_date(
            start_date=start_date,
            end_date=end_date,
            parish_id=parish_id,
            document_type=document_type,
            limit=limit
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return DocumentByDateResponse(
            success=True,
            start_date=result['start_date'],
            end_date=result['end_date'],
            results=result['results'],
            total_documents=result['total_documents'],
            total_chunks=result['total_chunks']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting documents by date: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/health")
async def get_health():
    """Get service health status."""
    try:
        # Test connections to all services
        health_status = {
            "status": "healthy",
            "services": {
                "textract": "available",
                "embedding": "available", 
                "s3": "available",
                "opensearch": "available"
            }
        }
        
        # Test OpenSearch connection
        try:
            opensearch_health = document_service.opensearch_service.test_connection()
            if not opensearch_health:
                health_status["services"]["opensearch"] = "unavailable"
                health_status["status"] = "degraded"
        except Exception:
            health_status["services"]["opensearch"] = "unavailable"
            health_status["status"] = "degraded"
        
        # Test S3 connection
        try:
            bucket_info = document_service.s3_service.get_bucket_info()
            if not bucket_info['success']:
                health_status["services"]["s3"] = "unavailable"
                health_status["status"] = "degraded"
        except Exception:
            health_status["services"]["s3"] = "unavailable"
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error checking health: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/supported-formats")
async def get_supported_formats():
    """Get list of supported file formats."""
    return {
        "supported_formats": document_service.textract_service.get_supported_formats(),
        "max_file_size_mb": 50,
        "max_batch_size": 10
    }
