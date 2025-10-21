#!/usr/bin/env python3
"""
OpenSearch API Routes

FastAPI routes for interacting with the OpenSearch service.
This demonstrates how to integrate the OpenSearchService with a web API.
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import sys
import os

# Add the services directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services'))

from opensearch_service import OpenSearchService

# Create router
router = APIRouter(prefix="/opensearch", tags=["opensearch"])

# Initialize service
opensearch_service = OpenSearchService()

# Pydantic models for request/response
class DocumentModel(BaseModel):
    id: Optional[str] = None
    file_id: str
    filename: str
    source: str
    text: str
    embedding: List[float]
    metadata: Optional[Dict[str, Any]] = {}

class DocumentUpdateModel(BaseModel):
    updates: Dict[str, Any]

class SearchQueryModel(BaseModel):
    query: Dict[str, Any]
    size: Optional[int] = 10
    fields_to_return: Optional[List[str]] = None

class KNNSearchModel(BaseModel):
    embedding: List[float]
    k: Optional[int] = 10
    filter_query: Optional[Dict[str, Any]] = None
    fields_to_return: Optional[List[str]] = None

class TextSearchModel(BaseModel):
    text: str
    field: Optional[str] = "text"
    size: Optional[int] = 10
    fields_to_return: Optional[List[str]] = None


@router.get("/health")
async def get_health():
    """Get OpenSearch service health status."""
    try:
        if not opensearch_service.test_connection():
            raise HTTPException(status_code=503, detail="OpenSearch connection failed")
        
        health = opensearch_service.get_index_health()
        if not health['success']:
            raise HTTPException(status_code=503, detail=f"Index health check failed: {health['error']}")
        
        return {
            "status": "healthy",
            "opensearch": health
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_index_stats():
    """Get comprehensive index statistics."""
    try:
        stats = opensearch_service.get_index_stats()
        if not stats['success']:
            raise HTTPException(status_code=500, detail=f"Failed to get stats: {stats['error']}")
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/count")
async def get_document_count():
    """Get total document count."""
    try:
        count = opensearch_service.get_document_count()
        if not count['success']:
            raise HTTPException(status_code=500, detail=f"Failed to get count: {count['error']}")
        
        return count
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents")
async def index_document(document: DocumentModel):
    """Index a single document."""
    try:
        doc_dict = document.dict()
        result = opensearch_service.index_document(doc_dict, document.id)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=f"Failed to index document: {result['error']}")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/batch")
async def index_documents_batch(documents: List[DocumentModel]):
    """Index multiple documents in batch."""
    try:
        docs_list = [doc.dict() for doc in documents]
        result = opensearch_service.index_documents_batch(docs_list)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=f"Failed to index documents: {result['error']}")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get a document by ID."""
    try:
        result = opensearch_service.get_document(doc_id)
        
        if not result['success']:
            if result['error'] == 'Document not found':
                raise HTTPException(status_code=404, detail="Document not found")
            raise HTTPException(status_code=500, detail=f"Failed to get document: {result['error']}")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/documents/{doc_id}")
async def update_document(doc_id: str, update_data: DocumentUpdateModel):
    """Update a document by ID."""
    try:
        result = opensearch_service.update_document(doc_id, update_data.updates)
        
        if not result['success']:
            if result['error'] == 'Document not found':
                raise HTTPException(status_code=404, detail="Document not found")
            raise HTTPException(status_code=400, detail=f"Failed to update document: {result['error']}")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document by ID."""
    try:
        result = opensearch_service.delete_document(doc_id)
        
        if not result['success']:
            if result['error'] == 'Document not found':
                raise HTTPException(status_code=404, detail="Document not found")
            raise HTTPException(status_code=400, detail=f"Failed to delete document: {result['error']}")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/knn")
async def knn_search(search_data: KNNSearchModel):
    """Perform KNN-based semantic search."""
    try:
        result = opensearch_service.knn_search(
            embedding=search_data.embedding,
            k=search_data.k,
            filter_query=search_data.filter_query,
            fields_to_return=search_data.fields_to_return
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=f"KNN search failed: {result['error']}")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/text")
async def text_search(search_data: TextSearchModel):
    """Perform text search on a specific field."""
    try:
        result = opensearch_service.text_search(
            text=search_data.text,
            field=search_data.field,
            size=search_data.size,
            fields_to_return=search_data.fields_to_return
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=f"Text search failed: {result['error']}")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/field")
async def field_search(search_data: SearchQueryModel):
    """Perform field-based search using various query types."""
    try:
        result = opensearch_service.field_search(
            query=search_data.query,
            size=search_data.size,
            fields_to_return=search_data.fields_to_return
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=f"Field search failed: {result['error']}")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/file/{file_id}")
async def search_by_file_id(file_id: str, fields_to_return: Optional[List[str]] = Query(None)):
    """Search for all documents belonging to a specific file."""
    try:
        result = opensearch_service.search_by_file_id(file_id, fields_to_return)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=f"File search failed: {result['error']}")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/source/{source}")
async def search_by_source(source: str, fields_to_return: Optional[List[str]] = Query(None)):
    """Search for all documents from a specific source."""
    try:
        result = opensearch_service.search_by_source(source, fields_to_return)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=f"Source search failed: {result['error']}")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
async def refresh_index():
    """Refresh the index to make recent changes visible."""
    try:
        result = opensearch_service.refresh_index()
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=f"Failed to refresh index: {result['error']}")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
