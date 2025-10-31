"""
Agent Routes for Homilia AI

This module provides API endpoints for interacting with the AI agent,
including chat functionality and document-based Q&A.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, Tuple
import logging
import asyncio
import re
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from services.agent_service import create_agent
from services.document_processing_service import DocumentProcessingService
from hashing import encrypt_s3_key

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/agent", tags=["agent"])

# Pydantic models for request/response
class ChatRequest(BaseModel):
    """Request model for chat with agent."""
    message: str
    document_id: Optional[str] = None
    conversation_id: Optional[str] = None
    parish_id: Optional[str] = None

class ChatResponse(BaseModel):
    """Response model for chat with agent."""
    response: str
    conversation_id: Optional[str] = None
    document_context: Optional[Dict[str, Any]] = None
    sources: Optional[Dict[str, Tuple[str, int]]] = None

class AgentInfo(BaseModel):
    """Agent information model."""
    name: str
    description: str
    tools: list
    model: str

# Global agent instance (singleton pattern)
_agent_instance = None

def get_agent():
    """Get or create the agent instance."""
    global _agent_instance
    if _agent_instance is None:
        try:
            _agent_instance = create_agent()
            logger.info("Agent instance created successfully")
        except Exception as e:
            logger.error(f"Failed to create agent instance: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize agent: {str(e)}"
            )
    return _agent_instance

@router.get("/info", response_model=AgentInfo)
async def get_agent_info():
    """
    Get information about the agent including available tools and capabilities.
    """
    try:
        agent = get_agent()
        return AgentInfo(
            name=agent.name,
            description=agent.description,
            tools=[tool.name for tool in agent.tools],
            model="gpt-4o"
        )
    except Exception as e:
        logger.error(f"Error getting agent info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent info: {str(e)}"
        )

@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Chat with the AI agent.
    
    This endpoint allows users to send messages to the agent and receive responses.
    The agent can access uploaded documents and provide contextual answers.
    
    Args:
        request: Chat request containing the message and optional document context
        
    Returns:
        ChatResponse: The agent's response with optional context and sources
    """
    try:
        agent = get_agent()
        
        # Prepare the message with contextual hints
        context_parts = []
        if request.parish_id:
            context_parts.append(f"Parish ID: {request.parish_id}")
        if request.document_id:
            context_parts.append(f"Document ID: {request.document_id}")
        if context_parts:
            message = f"Context: {' | '.join(context_parts)}\n\nUser question: {request.message}"
        else:
            message = request.message
        
        logger.info(f"Processing chat request: {request.message[:100]}...")
        
        # Run the agent in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: agent(message)
        )
        
        # Extract response text
        response_text = str(response) if response else "I apologize, but I couldn't process your request."
        
        logger.info(f"Agent response generated successfully")

        pattern = r'\[Document ID: ([^,]+), Filename: ([^\]]+)\]'
        matches = re.findall(pattern, response_text)
        sources = {}
        count = 1
        for document_id, filename in matches:
            if document_id not in sources:
                sources[document_id] = (filename, count)
                count += 1
        if len(sources) > 0:
            logger.info(f"sources: {sources}")
            # Replace pattern with the source number
            def replace_with_source_number(match):
                document_id = match.group(1)
                if document_id in sources:
                    return f"[{sources[document_id][1]}]"
                return match.group(0)  # Return original if not found

            document_processing_service = DocumentProcessingService()
            def getS3Key(document_id):
                doc_info = document_processing_service.get_document_info(document_id)
                if not doc_info['success']:
                    return f"Error: {doc_info['error']}"
                s3_key = doc_info.get('s3_key')
                if s3_key:
                    return encrypt_s3_key(s3_key)
                return "Error: No S3 key found"

            clean_response_text = re.sub(pattern, replace_with_source_number, response_text)
            clean_response_text += "\n\n**Sources**:\n" + "\n".join([f"{count}. [{filename}](/doc/{getS3Key(document_id)})" for document_id, (filename, count) in sources.items()])
        else:
            clean_response_text = response_text
        logger.info(f"clean_response_text: {clean_response_text}")
        
        return ChatResponse(
            response=clean_response_text,
            conversation_id=request.conversation_id,
            sources=sources  # Include the sources dictionary
        )
        
    except Exception as e:
        logger.error(f"Error in chat_with_agent: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat request: {str(e)}"
        )

@router.post("/chat/simple")
async def simple_chat(message: str, document_id: Optional[str] = None, parish_id: Optional[str] = None):
    """
    Simplified chat endpoint for basic interactions.
    
    This is a simpler version of the chat endpoint that takes parameters
    directly instead of using a request body.
    
    Args:
        message: The user's message
        document_id: Optional document ID for context
        
    Returns:
        dict: Simple response with the agent's reply
    """
    try:
        agent = get_agent()
        
        # Prepare the message with context if document_id is provided
        context_parts = []
        if parish_id:
            context_parts.append(f"Parish ID: {parish_id}")
        if document_id:
            context_parts.append(f"Document ID: {document_id}")
        full_message = f"Context: {' | '.join(context_parts)}\n\nUser question: {message}" if context_parts else message
        
        logger.info(f"Processing simple chat request: {message[:100]}...")
        
        # Run the agent in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: agent(full_message)
        )
        
        response_text = str(response) if response else "I apologize, but I couldn't process your request."
        
        return {
            "message": message,
            "response": response_text,
            "document_id": document_id,
            "parish_id": parish_id,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error in simple_chat: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat request: {str(e)}"
        )

@router.get("/health")
async def agent_health_check():
    """
    Health check endpoint for the agent service.
    """
    try:
        agent = get_agent()
        return {
            "status": "healthy",
            "agent_name": agent.name,
            "tools_count": len(agent.tools),
            "model": "gpt-4o"
        }
    except Exception as e:
        logger.error(f"Agent health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Agent service unavailable: {str(e)}"
        )
