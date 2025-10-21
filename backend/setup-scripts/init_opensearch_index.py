#!/usr/bin/env python3
"""
OpenSearch Index Initialization Script for Parish Documents

This script creates the 'parish_docs' index in OpenSearch with the proper
mapping for storing text chunks with embeddings for semantic search.

Environment Variables Required:
- OPENSEARCH_HOST: OpenSearch endpoint (default: localhost)
- OPENSEARCH_PORT: OpenSearch port (default: 9200)
- OPENSEARCH_USERNAME: Username for authentication (default: admin)
- OPENSEARCH_PASSWORD: Password for authentication (default: admin)
- OPENSEARCH_USE_SSL: Whether to use SSL (default: false)
"""

import os
import sys
from datetime import datetime, timezone
from opensearchpy import OpenSearch
from opensearchpy.exceptions import NotFoundError, RequestError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_opensearch_client():
    """Create and return an OpenSearch client with environment configuration."""
    host = os.getenv('OPENSEARCH_HOST', 'localhost')
    port = int(os.getenv('OPENSEARCH_PORT', '9200'))
    username = os.getenv('OPENSEARCH_USERNAME', 'admin')
    password = os.getenv('OPENSEARCH_PASSWORD', 'admin')
    use_ssl = os.getenv('OPENSEARCH_USE_SSL', 'false').lower() == 'true'
    
    # For development with security disabled, we might not need auth
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

def create_parish_docs_index(client, index_name="parish_docs"):
    """Create the parish_docs index with the specified mapping."""
    
    # Check if index already exists
    try:
        if client.indices.exists(index=index_name):
            print(f"Index '{index_name}' already exists.")
            response = input("Do you want to delete and recreate it? (y/N): ")
            if response.lower() == 'y':
                client.indices.delete(index=index_name)
                print(f"Deleted existing index '{index_name}'.")
            else:
                print("Keeping existing index.")
                return True
    except Exception as e:
        print(f"Error checking index existence: {e}")
        return False
    
    # Define the index mapping
    mapping = {
        "settings": {
            "index": {
                "knn": True,
                "number_of_shards": 1,
                "number_of_replicas": 0  # Set to 0 for single-node development
            }
        },
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "file_id": {"type": "keyword"},
                "filename": {"type": "keyword"},
                "source": {"type": "keyword"},
                "text": {"type": "text"},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": 1536,  # OpenAI text-embedding-3-small dimension
                    "method": {
                        "name": "hnsw",
                        "engine": "lucene",
                        "space_type": "cosinesimil"
                    }
                },
                "created_at": {"type": "date"},
                "metadata": {"type": "object", "enabled": True}
            }
        }
    }
    
    try:
        # Create the index
        client.indices.create(index=index_name, body=mapping)
        print(f"✅ Index '{index_name}' created successfully!")
        
        # Verify the index was created
        index_info = client.indices.get(index=index_name)
        print(f"📊 Index settings: {index_info[index_name]['settings']}")
        
        return True
        
    except RequestError as e:
        print(f"❌ Error creating index: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_index(client, index_name="parish_docs"):
    """Test the index by inserting a sample document."""
    try:
        # Sample test document
        test_doc = {
            "id": "test-chunk-001",
            "file_id": "test-homily-001",
            "filename": "test_homily.pdf",
            "source": "homily",
            "text": "This is a test chunk to verify the index is working correctly.",
            "embedding": [0.1] * 1536,  # Dummy embedding vector (non-zero values)
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "page": 1,
                "chunk_index": 0,
                "test": True
            }
        }
        
        # Insert test document
        response = client.index(index=index_name, id=test_doc["id"], body=test_doc)
        print(f"✅ Test document inserted: {response['result']}")
        
        # Retrieve test document
        retrieved = client.get(index=index_name, id=test_doc["id"])
        print(f"✅ Test document retrieved successfully")
        
        # # Delete test document
        # client.delete(index=index_name, id=test_doc["id"])
        # print(f"✅ Test document cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing index: {e}")
        return False

def main():
    """Main function to initialize the OpenSearch index."""
    print("🚀 Initializing OpenSearch Index for Parish Documents")
    print("=" * 60)
    
    try:
        # Create OpenSearch client
        print("📡 Connecting to OpenSearch...")
        client = get_opensearch_client()
        
        # Test connection
        try:
            info = client.info()
            print(f"✅ Connected to OpenSearch cluster: {info['cluster_name']}")
            print(f"📋 Version: {info['version']['number']}")
        except Exception as e:
            print(f"❌ Failed to connect to OpenSearch: {e}")
            print("\n💡 Make sure OpenSearch is running and check your environment variables:")
            print("   - OPENSEARCH_HOST")
            print("   - OPENSEARCH_PORT") 
            print("   - OPENSEARCH_USERNAME")
            print("   - OPENSEARCH_PASSWORD")
            print("   - OPENSEARCH_USE_SSL")
            print("   - OPENSEARCH_SECURITY_DISABLED")
            return False
        
        # Create the index
        print("\n🏗️  Creating parish_docs index...")
        if not create_parish_docs_index(client):
            return False
        
        # Test the index
        print("\n🧪 Testing index functionality...")
        if not test_index(client):
            return False
        
        print("\n🎉 OpenSearch index initialization completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Start uploading parish documents")
        print("   2. Use the embedding service to create embeddings")
        print("   3. Index the chunks with embeddings")
        print("   4. Test semantic search queries")
        
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
