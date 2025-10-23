# Homilia AI Backend API Documentation

## Overview

The Homilia AI backend provides a comprehensive API for document processing, AI-powered Q&A, and search capabilities for Catholic parishes. The API is built with FastAPI and includes three main service modules:

- **Agent Routes** (`/agent`) - AI chat and Q&A functionality
- **Document Routes** (`/documents`) - Document upload, processing, and management
- **OpenSearch Routes** (`/opensearch`) - Search and indexing operations

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not implement authentication. All endpoints are publicly accessible.

## Common Response Formats

### Success Response
```json
{
  "success": true,
  "data": {...}
}
```

### Error Response
```json
{
  "error": "Error message",
  "status_code": 400
}
```

---

## Agent Routes (`/agent`)

The agent routes provide AI-powered chat functionality with document context awareness.

### GET `/agent/info`

Get information about the AI agent including available tools and capabilities.

**Response:**
```json
{
  "name": "string",
  "description": "string", 
  "tools": ["tool1", "tool2"],
  "model": "gpt-4o"
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/agent/info"
```

### POST `/agent/chat`

Chat with the AI agent with optional document context.

**Request Body:**
```json
{
  "message": "string"
}
```

**Response:**
```json
{
  "response": "string",
  "conversation_id": "string",
  "document_context": {},
  "sources": {}
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the main theme of the homily?",
    "document_id": "doc_123"
  }'
```

### POST `/agent/chat/simple`

Simplified chat endpoint that takes parameters directly.

**Parameters:**
- `message` (string, required): The user's message
- `document_id` (string, optional): Document ID for context

**Response:**
```json
{
  "message": "string",
  "response": "string", 
  "document_id": "string",
  "status": "success"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/agent/chat/simple?message=Hello&document_id=doc_123"
```

### GET `/agent/health`

Health check endpoint for the agent service.

**Response:**
```json
{
  "status": "healthy",
  "agent_name": "string",
  "tools_count": 0,
  "model": "gpt-4o"
}
```

---

## Document Routes (`/documents`)

The document routes handle file uploads, processing, and management through the complete pipeline.

### POST `/documents/upload`

Upload and process a single document through the complete pipeline.

**Form Data:**
- `file` (file, required): Document file to upload
- `parish_id` (string, required): Parish identifier
- `document_type` (string, optional): Type of document (default: "document")
- `use_textract` (boolean, optional): Use AWS Textract for PDF processing (default: false)
- `metadata` (string, optional): Additional metadata as JSON string

**Supported File Types:**
- PDF (.pdf)
- Microsoft Word (.docx, .doc)
- Text files (.txt)
- Rich Text Format (.rtf)

**File Size Limit:** 50MB

**Response:**
```json
{
  "success": true,
  "file_id": "string",
  "filename": "string",
  "parish_id": "string",
  "document_type": "string",
  "chunk_count": 0,
  "s3_key": "string",
  "processing_timestamp": "string"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@homily.pdf" \
  -F "parish_id=parish_001" \
  -F "document_type=homily"
```

### POST `/documents/upload/batch`

Upload and process multiple documents in batch.

**Form Data:**
- `files` (array of files, required): List of document files to upload
- `parish_id` (string, required): Parish identifier
- `document_type` (string, optional): Type of document
- `use_textract` (boolean, optional): Use AWS Textract for PDF processing
- `metadata` (string, optional): Additional metadata as JSON string

**Batch Size Limit:** Maximum 10 files per batch

**Response:**
```json
[
  {
    "success": true,
    "file_id": "string",
    "filename": "string",
    "parish_id": "string",
    "document_type": "string",
    "chunk_count": 0,
    "s3_key": "string",
    "processing_timestamp": "string"
  }
]
```

### GET `/documents/info/{file_id}`

Get information about a processed document.

**Path Parameters:**
- `file_id` (string): File identifier

**Response:**
```json
{
  "success": true,
  "file_id": "string",
  "filename": "string",
  "source": "string",
  "chunk_count": 0,
  "parish_id": "string",
  "document_type": "string",
  "s3_key": "string",
  "extraction_method": "string",
  "file_type": "string",
  "file_size": 0,
  "created_at": "string"
}
```

### POST `/documents/search`

Search documents using semantic search.

**Form Data:**
- `query` (string, required): Search query
- `parish_id` (string, optional): Parish filter
- `document_type` (string, optional): Document type filter
- `k` (integer, optional): Number of results to return (default: 10)

**Response:**
```json
{
  "success": true,
  "query": "string",
  "results": [
    {
      "file_id": "string",
      "filename": "string",
      "text": "string",
      "score": 0.95,
      "metadata": {}
    }
  ],
  "total_files": 0,
  "total_chunks": 0
}
```

### DELETE `/documents/{file_id}`

Delete a document and all its chunks from the system.

**Path Parameters:**
- `file_id` (string): File identifier to delete

**Response:**
```json
{
  "success": true,
  "file_id": "string",
  "deleted_chunks": 0,
  "deleted_s3_files": 0,
  "total_chunks": 0,
  "total_s3_files": 0
}
```

### GET `/documents/by-date`

Get documents created within a date range.

**Query Parameters:**
- `start_date` (string, required): Start date in YYYY-MM-DD format
- `end_date` (string, optional): End date in YYYY-MM-DD format
- `parish_id` (string, optional): Parish filter
- `document_type` (string, optional): Document type filter
- `limit` (integer, optional): Maximum number of results (default: 100)

**Response:**
```json
{
  "success": true,
  "start_date": "string",
  "end_date": "string",
  "results": [
    {
      "file_id": "string",
      "filename": "string",
      "created_at": "string",
      "parish_id": "string",
      "document_type": "string"
    }
  ],
  "total_documents": 0,
  "total_chunks": 0
}
```

### GET `/documents/content/{file_id}`

Get document content from S3 by file ID.

**Path Parameters:**
- `file_id` (string): File identifier (may be encrypted S3 key)

**Response:**
```json
{
  "success": true,
  "content": "string",
  "content_type": "string",
  "filename": "string",
  "file_type": "string",
  "encoding": "base64 (optional)"
}
```

### GET `/documents/supported-formats`

Get list of supported file formats.

**Response:**
```json
{
  "supported_formats": [".pdf", ".docx", ".doc", ".txt", ".rtf"],
  "max_file_size_mb": 50,
  "max_batch_size": 10
}
```

### GET `/documents/health`

Get service health status.

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "textract": "available",
    "embedding": "available",
    "s3": "available",
    "opensearch": "available"
  }
}
```

---

## OpenSearch Routes (`/opensearch`)

The OpenSearch routes provide direct access to search and indexing operations.

### GET `/opensearch/health`

Get OpenSearch service health status.

**Response:**
```json
{
  "status": "healthy",
  "opensearch": {
    "status": "green",
    "documents": 0,
    "index_size": "0b"
  }
}
```

### GET `/opensearch/stats`

Get comprehensive index statistics.

**Response:**
```json
{
  "success": true,
  "stats": {
    "documents": 0,
    "index_size": "0b",
    "segments": 0
  }
}
```

### GET `/opensearch/count`

Get total document count.

**Response:**
```json
{
  "success": true,
  "count": 0
}
```

### POST `/opensearch/documents`

Index a single document.

**Request Body:**
```json
{
  "id": "string (optional)",
  "file_id": "string",
  "filename": "string",
  "source": "string",
  "text": "string",
  "embedding": [0.1, 0.2, 0.3],
  "metadata": {}
}
```

### POST `/opensearch/documents/batch`

Index multiple documents in batch.

**Request Body:**
```json
[
  {
    "file_id": "string",
    "filename": "string",
    "source": "string",
    "text": "string",
    "embedding": [0.1, 0.2, 0.3],
    "metadata": {}
  }
]
```

### GET `/opensearch/documents/{doc_id}`

Get a document by ID.

**Path Parameters:**
- `doc_id` (string): Document identifier

### PUT `/opensearch/documents/{doc_id}`

Update a document by ID.

**Path Parameters:**
- `doc_id` (string): Document identifier

**Request Body:**
```json
{
  "updates": {
    "field": "new_value"
  }
}
```

### DELETE `/opensearch/documents/{doc_id}`

Delete a document by ID.

**Path Parameters:**
- `doc_id` (string): Document identifier

### POST `/opensearch/search/knn`

Perform KNN-based semantic search.

**Request Body:**
```json
{
  "embedding": [0.1, 0.2, 0.3],
  "k": 10,
  "filter_query": {},
  "fields_to_return": ["text", "filename"]
}
```

### POST `/opensearch/search/text`

Perform text search on a specific field.

**Request Body:**
```json
{
  "text": "search query",
  "field": "text",
  "size": 10,
  "fields_to_return": ["text", "filename"]
}
```

### POST `/opensearch/search/field`

Perform field-based search using various query types.

**Request Body:**
```json
{
  "query": {
    "match": {
      "field": "value"
    }
  },
  "size": 10,
  "fields_to_return": ["text", "filename"]
}
```

### GET `/opensearch/search/file/{file_id}`

Search for all documents belonging to a specific file.

**Path Parameters:**
- `file_id` (string): File identifier

**Query Parameters:**
- `fields_to_return` (array, optional): Fields to return in results

### GET `/opensearch/search/source/{source}`

Search for all documents from a specific source.

**Path Parameters:**
- `source` (string): Source identifier

**Query Parameters:**
- `fields_to_return` (array, optional): Fields to return in results

### POST `/opensearch/refresh`

Refresh the index to make recent changes visible.

**Response:**
```json
{
  "success": true,
  "message": "Index refreshed successfully"
}
```

---

## Main Application Routes

### GET `/`

Root endpoint with API information.

**Response:**
```json
{
  "message": "Welcome to Homilia AI",
  "description": "AI-powered Q&A platform for Catholic parishes",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health",
  "agent_health": "/agent/health"
}
```

### GET `/health`

Basic health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "homilia-ai",
  "version": "1.0.0"
}
```

---

## Error Handling

The API uses standard HTTP status codes:

- `200` - Success
- `400` - Bad Request (invalid input)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error
- `503` - Service Unavailable (service dependencies down)

All error responses include:
```json
{
  "error": "Error message",
  "status_code": 400
}
```

## Rate Limiting

Currently, no rate limiting is implemented. Consider implementing rate limiting for production use.

## CORS

CORS is configured to allow all origins (`*`). For production, configure specific allowed origins.

## Interactive Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Examples

### Complete Document Processing Workflow

1. **Upload a document:**
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@sunday_homily.pdf" \
  -F "parish_id=st_marys" \
  -F "document_type=homily"
```

2. **Search for content:**
```bash
curl -X POST "http://localhost:8000/documents/search" \
  -F "query=What is the main message?" \
  -F "parish_id=st_marys"
```

3. **Chat with AI about the document:**
```bash
curl -X POST "http://localhost:8000/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Summarize the main points of this homily",
    "document_id": "doc_123"
  }'
```

### Health Monitoring

Check all service health:
```bash
# Main application
curl -X GET "http://localhost:8000/health"

# Agent service
curl -X GET "http://localhost:8000/agent/health"

# Document service
curl -X GET "http://localhost:8000/documents/health"

# OpenSearch service
curl -X GET "http://localhost:8000/opensearch/health"
```

## Development

To run the development server:

```bash
cd backend
python main.py
```

The server will start on `http://localhost:8000` by default.

## Production Considerations

1. **Authentication**: Implement proper authentication and authorization
2. **Rate Limiting**: Add rate limiting to prevent abuse
3. **CORS**: Configure specific allowed origins
4. **Logging**: Implement structured logging
5. **Monitoring**: Add application monitoring and metrics
6. **Security**: Implement input validation and sanitization
7. **Backup**: Implement data backup strategies
8. **Scaling**: Consider horizontal scaling for high traffic
