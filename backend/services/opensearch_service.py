#!/usr/bin/env python3
"""
OpenSearch Service for Parish Documents

This service provides comprehensive functionality for interacting with the
parish_docs index in OpenSearch, including document management, search operations,
and index statistics.

Features:
- Document indexing and updating
- Document deletion
- KNN-based semantic search
- Field-based search
- Index statistics and health monitoring
- Batch operations
"""

import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Union
from opensearchpy import OpenSearch
from opensearchpy.exceptions import NotFoundError, RequestError, ConflictError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenSearchService:
    """
    Service class for interacting with OpenSearch parish_docs index.
    
    This service handles all CRUD operations, search functionality, and
    index management for parish documents with embeddings.
    """
    
    def __init__(self, index_name: str = "parish_docs"):
        """
        Initialize the OpenSearch service.
        
        Args:
            index_name: Name of the OpenSearch index to work with
        """
        self.index_name = index_name
        self.client = self._create_client()
        
    def _create_client(self) -> OpenSearch:
        """Create and return an OpenSearch client with environment configuration."""
        host = os.getenv('OPENSEARCH_HOST', 'localhost')
        port = int(os.getenv('OPENSEARCH_PORT', '9200'))
        username = os.getenv('OPENSEARCH_USERNAME', 'admin')
        password = os.getenv('OPENSEARCH_PASSWORD', 'admin')
        use_ssl = os.getenv('OPENSEARCH_USE_SSL', 'false').lower() == 'true'
        
        # For development with security disabled
        if os.getenv('OPENSEARCH_SECURITY_DISABLED', 'false').lower() == 'true':
            client = OpenSearch(
                hosts=[{"host": host, "port": port}],
                use_ssl=use_ssl,
                verify_certs=False,
                ssl_assert_hostname=False,
                ssl_show_warn=False
            )
        else:
            client = OpenSearch(
                hosts=[{"host": host, "port": port}],
                http_auth=(username, password),
                use_ssl=use_ssl,
                verify_certs=False,
                ssl_assert_hostname=False,
                ssl_show_warn=False
            )
        
        return client
    
    def test_connection(self) -> bool:
        """
        Test the connection to OpenSearch.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            info = self.client.info()
            logger.info(f"Connected to OpenSearch cluster: {info['cluster_name']}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to OpenSearch: {e}")
            return False
    
    def index_exists(self) -> bool:
        """
        Check if the index exists.
        
        Returns:
            bool: True if index exists, False otherwise
        """
        try:
            return self.client.indices.exists(index=self.index_name)
        except Exception as e:
            logger.error(f"Error checking index existence: {e}")
            return False
    
    # Document Management Methods
    
    def index_document(self, document: Dict[str, Any], doc_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Index a single document.
        
        Args:
            document: Document to index
            doc_id: Optional document ID. If not provided, will be auto-generated
            
        Returns:
            Dict containing the indexing result
        """
        try:
            # Ensure required fields are present
            if 'created_at' not in document:
                document['created_at'] = datetime.now(timezone.utc).isoformat()
            
            # Index the document
            response = self.client.index(
                index=self.index_name,
                id=doc_id,
                body=document
            )
            
            logger.info(f"Document indexed successfully: {response['result']}")
            return {
                'success': True,
                'result': response['result'],
                'id': response['_id'],
                'version': response['_version']
            }
            
        except RequestError as e:
            logger.error(f"Error indexing document: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error indexing document: {e}")
            return {'success': False, 'error': str(e)}
    
    def index_documents_batch(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Index multiple documents in a batch operation.
        
        Args:
            documents: List of documents to index
            
        Returns:
            Dict containing batch operation results
        """
        try:
            body = []
            for doc in documents:
                # Add index action
                body.append({
                    "index": {
                        "_index": self.index_name,
                        "_id": doc.get('id')  # Use id field if present
                    }
                })
                
                # Ensure created_at is present
                if 'created_at' not in doc:
                    doc['created_at'] = datetime.now(timezone.utc).isoformat()
                
                # Add document
                body.append(doc)
            
            response = self.client.bulk(body=body)
            
            # Check for errors in the response
            errors = [item for item in response['items'] if 'error' in item['index']]
            
            if errors:
                logger.warning(f"Some documents failed to index: {len(errors)} errors")
                return {
                    'success': False,
                    'total': len(documents),
                    'successful': len(documents) - len(errors),
                    'failed': len(errors),
                    'errors': errors
                }
            
            logger.info(f"Batch indexed {len(documents)} documents successfully")
            return {
                'success': True,
                'total': len(documents),
                'successful': len(documents),
                'failed': 0
            }
            
        except Exception as e:
            logger.error(f"Error in batch indexing: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_document(self, doc_id: str) -> Dict[str, Any]:
        """
        Retrieve a document by ID.
        
        Args:
            doc_id: Document ID to retrieve
            
        Returns:
            Dict containing the document or error information
        """
        try:
            response = self.client.get(index=self.index_name, id=doc_id)
            return {
                'success': True,
                'document': response['_source'],
                'id': response['_id'],
                'version': response['_version']
            }
        except NotFoundError:
            logger.warning(f"Document {doc_id} not found")
            return {'success': False, 'error': 'Document not found'}
        except Exception as e:
            logger.error(f"Error retrieving document {doc_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_document(self, doc_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a document by ID.
        
        Args:
            doc_id: Document ID to update
            updates: Fields to update
            
        Returns:
            Dict containing the update result
        """
        try:
            response = self.client.update(
                index=self.index_name,
                id=doc_id,
                body={'doc': updates}
            )
            
            logger.info(f"Document {doc_id} updated successfully")
            return {
                'success': True,
                'result': response['result'],
                'id': response['_id'],
                'version': response['_version']
            }
            
        except NotFoundError:
            logger.warning(f"Document {doc_id} not found for update")
            return {'success': False, 'error': 'Document not found'}
        except ConflictError as e:
            logger.error(f"Conflict updating document {doc_id}: {e}")
            return {'success': False, 'error': 'Document conflict'}
        except Exception as e:
            logger.error(f"Error updating document {doc_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_document(self, doc_id: str) -> Dict[str, Any]:
        """
        Delete a document by ID.
        
        Args:
            doc_id: Document ID to delete
            
        Returns:
            Dict containing the deletion result
        """
        try:
            response = self.client.delete(index=self.index_name, id=doc_id)
            
            logger.info(f"Document {doc_id} deleted successfully")
            return {
                'success': True,
                'result': response['result'],
                'id': response['_id'],
                'version': response['_version']
            }
            
        except NotFoundError:
            logger.warning(f"Document {doc_id} not found for deletion")
            return {'success': False, 'error': 'Document not found'}
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_documents_by_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delete documents matching a query.
        
        Args:
            query: Query to match documents for deletion
            
        Returns:
            Dict containing the deletion result
        """
        try:
            response = self.client.delete_by_query(
                index=self.index_name,
                body={'query': query}
            )
            
            deleted_count = response['deleted']
            logger.info(f"Deleted {deleted_count} documents by query")
            return {
                'success': True,
                'deleted': deleted_count,
                'took': response['took']
            }
            
        except Exception as e:
            logger.error(f"Error deleting documents by query: {e}")
            return {'success': False, 'error': str(e)}
    
    # Search Methods
    
    def knn_search(self, 
                   embedding: List[float], 
                   k: int = 10, 
                   filter_query: Optional[Dict[str, Any]] = None,
                   fields_to_return: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Perform KNN-based semantic search using embeddings.
        
        Args:
            embedding: Vector embedding to search for
            k: Number of results to return
            filter_query: Optional filter to apply to results
            fields_to_return: Optional list of fields to return
            
        Returns:
            Dict containing search results
        """
        try:
            # Build the KNN query with proper structure
            if filter_query:
                # When using filters, we need to use a bool query with knn
                knn_query = {
                    "bool": {
                        "must": [
                            {
                                "knn": {
                                    "embedding": {
                                        "vector": embedding,
                                        "k": k
                                    }
                                }
                            }
                        ],
                        "filter": filter_query
                    }
                }
            else:
                # Simple KNN query without filters
                knn_query = {
                    "knn": {
                        "embedding": {
                            "vector": embedding,
                            "k": k
                        }
                    }
                }
            
            # Build the search body
            search_body = {
                "query": knn_query,
                "size": k
            }
            
            # Add field selection if specified
            if fields_to_return:
                search_body["_source"] = fields_to_return
            
            response = self.client.search(
                index=self.index_name,
                body=search_body
            )
            
            hits = response['hits']['hits']
            results = []
            
            for hit in hits:
                result = {
                    'id': hit['_id'],
                    'score': hit['_score'],
                    'document': hit['_source']
                }
                results.append(result)
            
            logger.info(f"KNN search returned {len(results)} results")
            return {
                'success': True,
                'results': results,
                'total': response['hits']['total']['value'],
                'took': response['took']
            }
            
        except Exception as e:
            logger.error(f"Error in KNN search: {e}")
            return {'success': False, 'error': str(e)}
    
    def field_search(self, 
                     query: Dict[str, Any], 
                     size: int = 10,
                     fields_to_return: Optional[List[str]] = None,
                     sort: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Perform field-based search using various query types.
        
        Args:
            query: Search query (match, term, range, etc.)
            size: Number of results to return
            fields_to_return: Optional list of fields to return
            sort: Optional sorting criteria
            
        Returns:
            Dict containing search results
        """
        try:
            search_body = {
                "query": query,
                "size": size
            }
            
            # Add field selection if specified
            if fields_to_return:
                search_body["_source"] = fields_to_return
            
            # Add sorting if specified
            if sort:
                search_body["sort"] = sort
            
            response = self.client.search(
                index=self.index_name,
                body=search_body
            )
            
            hits = response['hits']['hits']
            results = []
            
            for hit in hits:
                result = {
                    'id': hit['_id'],
                    'score': hit['_score'],
                    'document': hit['_source']
                }
                results.append(result)
            
            logger.info(f"Field search returned {len(results)} results")
            return {
                'success': True,
                'results': results,
                'total': response['hits']['total']['value'],
                'took': response['took']
            }
            
        except Exception as e:
            logger.error(f"Error in field search: {e}")
            return {'success': False, 'error': str(e)}
    
    def text_search(self, 
                   text: str, 
                   field: str = "text", 
                   size: int = 10,
                   fields_to_return: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Perform text search on a specific field.
        
        Args:
            text: Text to search for
            field: Field to search in (default: "text")
            size: Number of results to return
            fields_to_return: Optional list of fields to return
            
        Returns:
            Dict containing search results
        """
        query = {
            "match": {
                field: text
            }
        }
        
        return self.field_search(query, size, fields_to_return)
    
    def search_by_file_id(self, file_id: str, fields_to_return: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Search for all documents belonging to a specific file.
        
        Args:
            file_id: File ID to search for
            fields_to_return: Optional list of fields to return
            
        Returns:
            Dict containing search results
        """
        query = {
            "term": {
                "file_id": file_id
            }
        }
        
        return self.field_search(query, size=1000, fields_to_return=fields_to_return)
    
    def search_by_source(self, source: str, fields_to_return: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Search for all documents from a specific source.
        
        Args:
            source: Source to search for
            fields_to_return: Optional list of fields to return
            
        Returns:
            Dict containing search results
        """
        query = {
            "term": {
                "source": source
            }
        }
        
        return self.field_search(query, size=1000, fields_to_return=fields_to_return)
    
    # Index Statistics and Health Methods
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the index.
        
        Returns:
            Dict containing index statistics
        """
        try:
            # Get index stats
            stats_response = self.client.indices.stats(index=self.index_name)
            index_stats = stats_response['indices'][self.index_name]
            
            # Get index health
            health_response = self.client.cluster.health(index=self.index_name)
            
            # Get index settings
            settings_response = self.client.indices.get(index=self.index_name)
            index_settings = settings_response[self.index_name]['settings']
            
            stats = {
                'success': True,
                'index_name': self.index_name,
                'health': {
                    'status': health_response['status'],
                    'number_of_shards': health_response['number_of_shards'],
                    'number_of_replicas': health_response['number_of_replicas'],
                    'active_shards': health_response['active_shards'],
                    'unassigned_shards': health_response['unassigned_shards']
                },
                'documents': {
                    'total': index_stats['total']['docs']['count'],
                    'deleted': index_stats['total']['docs']['deleted']
                },
                'storage': {
                    'size_in_bytes': index_stats['total']['store']['size_in_bytes'],
                    'size': self._format_bytes(index_stats['total']['store']['size_in_bytes'])
                },
                'indexing': {
                    'index_total': index_stats['total']['indexing']['index_total'],
                    'index_time_in_millis': index_stats['total']['indexing']['index_time_in_millis'],
                    'index_current': index_stats['total']['indexing']['index_current']
                },
                'search': {
                    'query_total': index_stats['total']['search']['query_total'],
                    'query_time_in_millis': index_stats['total']['search']['query_time_in_millis'],
                    'query_current': index_stats['total']['search']['query_current']
                },
                'settings': {
                    'number_of_shards': index_settings['index']['number_of_shards'],
                    'number_of_replicas': index_settings['index']['number_of_replicas'],
                    'knn_enabled': index_settings['index'].get('knn', {}).get('algo_ef_search', None) is not None
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_document_count(self) -> Dict[str, Any]:
        """
        Get the total number of documents in the index.
        
        Returns:
            Dict containing document count
        """
        try:
            response = self.client.count(index=self.index_name)
            return {
                'success': True,
                'count': response['count']
            }
        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_index_health(self) -> Dict[str, Any]:
        """
        Get the health status of the index.
        
        Returns:
            Dict containing health information
        """
        try:
            response = self.client.cluster.health(index=self.index_name)
            return {
                'success': True,
                'status': response['status'],
                'number_of_shards': response['number_of_shards'],
                'number_of_replicas': response['number_of_replicas'],
                'active_shards': response['active_shards'],
                'unassigned_shards': response['unassigned_shards'],
                'active_primary_shards': response['active_primary_shards']
            }
        except Exception as e:
            logger.error(f"Error getting index health: {e}")
            return {'success': False, 'error': str(e)}
    
    def refresh_index(self) -> Dict[str, Any]:
        """
        Refresh the index to make recent changes visible.
        
        Returns:
            Dict containing refresh result
        """
        try:
            response = self.client.indices.refresh(index=self.index_name)
            return {
                'success': True,
                'shards': response['_shards']
            }
        except Exception as e:
            logger.error(f"Error refreshing index: {e}")
            return {'success': False, 'error': str(e)}
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes into human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"


# Example usage and testing functions
def test_opensearch_service():
    """Test function to demonstrate OpenSearch service usage."""
    
    # Initialize service
    service = OpenSearchService()
    
    # Test connection
    if not service.test_connection():
        print("❌ Failed to connect to OpenSearch")
        return False
    
    print("✅ Connected to OpenSearch")
    
    # Check if index exists
    if not service.index_exists():
        print(f"❌ Index '{service.index_name}' does not exist")
        return False
    
    print(f"✅ Index '{service.index_name}' exists")
    
    # Get index stats
    stats = service.get_index_stats()
    if stats['success']:
        print(f"Index stats: {stats['documents']['total']} documents")
        print(f"Storage: {stats['storage']['size']}")
        print(f"Health: {stats['health']['status']}")
    
    # Test document operations
    test_doc = {
        "id": "test-service-001",
        "file_id": "test-file-001",
        "filename": "test_service.pdf",
        "source": "test",
        "text": "This is a test document for the OpenSearch service.",
        "embedding": [0.1] * 1536,
        "metadata": {"test": True}
    }
    
    # Index test document
    result = service.index_document(test_doc, "test-service-001")
    if result['success']:
        print("✅ Test document indexed")
    else:
        print(f"❌ Failed to index test document: {result['error']}")
        return False
    
    # Retrieve test document
    doc = service.get_document("test-service-001")
    if doc['success']:
        print("✅ Test document retrieved")
    else:
        print(f"❌ Failed to retrieve test document: {doc['error']}")
    
    # Test KNN search
    knn_result = service.knn_search([0.1] * 1536, k=5)
    if knn_result['success']:
        print(f"✅ KNN search returned {len(knn_result['results'])} results")
    else:
        print(f"❌ KNN search failed: {knn_result['error']}")
    
    # Test text search
    text_result = service.text_search("test document", size=5)
    if text_result['success']:
        print(f"✅ Text search returned {len(text_result['results'])} results")
    else:
        print(f"❌ Text search failed: {text_result['error']}")
    
    # Clean up test document
    delete_result = service.delete_document("test-service-001")
    if delete_result['success']:
        print("✅ Test document cleaned up")
    else:
        print(f"❌ Failed to clean up test document: {delete_result['error']}")
    
    print("OpenSearch service test completed successfully!")
    return True


if __name__ == "__main__":
    test_opensearch_service()
