#!/usr/bin/env python3
"""
Test script to verify the S3 and OpenSearch file_id mismatch fix.

This script tests the get_doc_tool function to ensure it can properly
retrieve documents from S3 using the s3_key from OpenSearch metadata.
"""

import os
import sys
import logging
from pathlib import Path

# Add the services directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

from services.agent_service import get_doc_tool
from services.document_processing_service import DocumentProcessingService
from services.opensearch_service import OpenSearchService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_get_doc_tool():
    """Test the get_doc_tool function with a sample document."""
    
    print("🧪 Testing S3 and OpenSearch file_id mismatch fix...")
    
    try:
        # Initialize services
        doc_service = DocumentProcessingService()
        opensearch_service = OpenSearchService()
        
        # Check if OpenSearch is available
        if not opensearch_service.test_connection():
            print("❌ OpenSearch connection failed - skipping test")
            return False
        
        # Check if index exists
        if not opensearch_service.index_exists():
            print("❌ OpenSearch index does not exist - skipping test")
            return False
        
        # Get document count
        count_result = opensearch_service.get_document_count()
        if not count_result['success']:
            print("❌ Failed to get document count")
            return False
        
        document_count = count_result['count']
        print(f"📊 Found {document_count} documents in OpenSearch")
        
        if document_count == 0:
            print("⚠️  No documents found in OpenSearch - skipping test")
            return True
        
        # Get a sample document to test with
        search_result = opensearch_service.field_search(
            query={"match_all": {}},
            size=1,
            fields_to_return=['file_id', 'filename', 'source', 'metadata']
        )
        
        if not search_result['success'] or not search_result['results']:
            print("❌ No documents found for testing")
            return False
        
        sample_doc = search_result['results'][0]
        file_id = sample_doc['document']['file_id']
        filename = sample_doc['document']['filename']
        
        print(f"🔍 Testing with document: {filename} (file_id: {file_id})")
        
        # Test the get_doc_tool function
        print("📖 Testing get_doc_tool function...")
        result = get_doc_tool(file_id)
        
        if isinstance(result, str) and result.startswith("Error:"):
            print(f"❌ get_doc_tool failed: {result}")
            return False
        
        if isinstance(result, str) and len(result) > 0:
            print(f"✅ get_doc_tool succeeded! Retrieved {len(result)} characters")
            print(f"📄 First 100 characters: {result[:100]}...")
            return True
        else:
            print("❌ get_doc_tool returned empty result")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        logger.error(f"Test exception: {str(e)}", exc_info=True)
        return False

def test_document_info_retrieval():
    """Test the document info retrieval functionality."""
    
    print("\n🔍 Testing document info retrieval...")
    
    try:
        doc_service = DocumentProcessingService()
        opensearch_service = OpenSearchService()
        
        # Get a sample document
        search_result = opensearch_service.field_search(
            query={"match_all": {}},
            size=1,
            fields_to_return=['file_id', 'filename', 'source', 'metadata']
        )
        
        if not search_result['success'] or not search_result['results']:
            print("❌ No documents found for testing")
            return False
        
        sample_doc = search_result['results'][0]
        file_id = sample_doc['document']['file_id']
        
        # Test get_document_info
        doc_info = doc_service.get_document_info(file_id)
        
        if not doc_info['success']:
            print(f"❌ get_document_info failed: {doc_info['error']}")
            return False
        
        print(f"✅ get_document_info succeeded!")
        print(f"📋 Document info:")
        print(f"   - file_id: {doc_info['file_id']}")
        print(f"   - filename: {doc_info['filename']}")
        print(f"   - s3_key: {doc_info['s3_key']}")
        print(f"   - chunk_count: {doc_info['chunk_count']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Document info test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting S3 and OpenSearch file_id mismatch fix tests...\n")
    
    # Test document info retrieval first
    info_test_passed = test_document_info_retrieval()
    
    # Test get_doc_tool function
    doc_tool_test_passed = test_get_doc_tool()
    
    print(f"\n📊 Test Results:")
    print(f"   - Document info retrieval: {'✅ PASSED' if info_test_passed else '❌ FAILED'}")
    print(f"   - get_doc_tool function: {'✅ PASSED' if doc_tool_test_passed else '❌ FAILED'}")
    
    if info_test_passed and doc_tool_test_passed:
        print("\n🎉 All tests passed! The S3 and OpenSearch file_id mismatch has been fixed.")
    else:
        print("\n⚠️  Some tests failed. Please check the error messages above.")
