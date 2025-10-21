import os
import logging
from typing import List, Union, Optional
import numpy as np
from openai import OpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingRequest(BaseModel):
    """Request model for embedding generation"""
    text: Union[str, List[str]] = Field(..., description="Text or list of texts to embed")
    model: str = Field(default="text-embedding-3-small", description="OpenAI embedding model to use")
    dimensions: Optional[int] = Field(default=None, description="Number of dimensions for the embedding")


class EmbeddingResponse(BaseModel):
    """Response model for embedding generation"""
    embeddings: List[List[float]] = Field(..., description="List of embedding vectors")
    model: str = Field(..., description="Model used for embedding generation")
    dimensions: int = Field(..., description="Number of dimensions in the embeddings")
    usage: dict = Field(..., description="Token usage information")


class EmbeddingService:
    """
    Service for generating text embeddings using OpenAI's embedding models.
    
    This service provides functionality to convert text into high-dimensional
    vector representations that can be used for semantic search, similarity
    comparison, and other NLP tasks.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the embedding service.
        
        Args:
            api_key: OpenAI API key. If not provided, will try to get from environment.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.default_model = "text-embedding-3-small"
        
        logger.info(f"EmbeddingService initialized with model: {self.default_model}")
    
    def get_embedding(
        self, 
        text: Union[str, List[str]], 
        model: str = "text-embedding-3-small",
        dimensions: Optional[int] = None
    ) -> EmbeddingResponse:
        """
        Generate embeddings for the given text(s).
        
        Args:
            text: Single text string or list of text strings to embed
            model: OpenAI embedding model to use (default: text-embedding-3-small)
            dimensions: Number of dimensions for the embedding (optional)
            
        Returns:
            EmbeddingResponse containing the embeddings and metadata
            
        Raises:
            ValueError: If text is empty or invalid
            Exception: If API call fails
        """
        try:
            # Validate input
            if not text:
                raise ValueError("Text cannot be empty")
            
            # Convert single string to list for consistent processing
            if isinstance(text, str):
                texts = [text]
            else:
                texts = text
            
            # Validate each text
            for i, t in enumerate(texts):
                if not isinstance(t, str) or not t.strip():
                    raise ValueError(f"Text at index {i} is empty or not a string")
            
            logger.info(f"Generating embeddings for {len(texts)} text(s) using model: {model}")
            
            # Prepare API call parameters
            api_params = {
                "model": model,
                "input": texts
            }
            
            # Add dimensions if specified (only for text-embedding-3-small and text-embedding-3-large)
            if dimensions is not None:
                if model in ["text-embedding-3-small", "text-embedding-3-large"]:
                    api_params["dimensions"] = dimensions
                else:
                    logger.warning(f"Dimensions parameter not supported for model {model}, ignoring")
            
            # Make API call
            response = self.client.embeddings.create(**api_params)
            
            # Extract embeddings
            embeddings = [data.embedding for data in response.data]
            
            # Get dimensions from the first embedding
            actual_dimensions = len(embeddings[0]) if embeddings else 0
            
            # Prepare usage information
            usage_info = {
                "prompt_tokens": response.usage.prompt_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            logger.info(f"Successfully generated {len(embeddings)} embeddings with {actual_dimensions} dimensions")
            
            return EmbeddingResponse(
                embeddings=embeddings,
                model=model,
                dimensions=actual_dimensions,
                usage=usage_info
            )
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise



# Convenience function for quick embedding generation
def get_embedding(text: Union[str, List[str]], api_key: Optional[str] = None) -> List[List[float]]:
    """
    Convenience function to quickly get embeddings for text.
    
    Args:
        text: Text or list of texts to embed
        api_key: OpenAI API key (optional)
        
    Returns:
        List of embedding vectors
    """
    service = EmbeddingService(api_key=api_key)
    response = service.get_embedding(text)
    return response.embeddings


# Example usage
if __name__ == "__main__":
    # Example usage of the embedding service
    try:
        # Initialize service
        embedding_service = EmbeddingService()
        
        # Example texts
        texts = [
            "The quick brown fox jumps over the lazy dog",
            "Artificial intelligence is transforming the world",
            "Machine learning algorithms can process vast amounts of data"
        ]
        
        # Generate embeddings
        response = embedding_service.get_embedding(texts)
        
        print(f"Generated {len(response.embeddings)} embeddings")
        print(f"Model: {response.model}")
        print(f"Dimensions: {response.dimensions}")
        print(f"Usage: {response.usage}")
        
    except Exception as e:
        print(f"Error: {e}")
