"""Utility functions for embedding and ChromaDB availability checking."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Global flag to cache embedding availability status
_embedding_availability_cached: Optional[bool] = None


def are_embeddings_available() -> bool:
    """
    Check if ChromaDB and embedding functionality is available.
    
    This function checks for:
    1. ChromaDB import availability
    2. Compatible embedding functions
    3. Version compatibility
    
    Returns:
        bool: True if embeddings are available and functional, False otherwise
    """
    global _embedding_availability_cached
    
    # Return cached result if we've already checked
    if _embedding_availability_cached is not None:
        return _embedding_availability_cached
    
    try:
        # Test ChromaDB import
        import chromadb
        from chromadb.config import Settings
        
        # Test embedding function imports
        try:
            from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
            # Try to create a default embedding function to test functionality
            embedding_func = DefaultEmbeddingFunction()
            
            # Test creating a temporary client to verify ChromaDB works
            temp_client = chromadb.Client(settings=Settings(anonymized_telemetry=False))
            
            # Test creating a collection with embedding function
            test_collection = temp_client.get_or_create_collection(
                name="embedding_test",
                embedding_function=embedding_func
            )
            
            # Clean up test collection
            temp_client.delete_collection("embedding_test")
            
            logger.info("✅ ChromaDB and embedding functions are available and functional")
            _embedding_availability_cached = True
            return True
            
        except Exception as embed_error:
            logger.warning(f"❌ Embedding function initialization failed: {embed_error}")
            _embedding_availability_cached = False
            return False
            
    except ImportError as import_error:
        logger.warning(f"❌ ChromaDB import failed: {import_error}")
        _embedding_availability_cached = False
        return False
    except Exception as general_error:
        logger.warning(f"❌ ChromaDB functionality check failed: {general_error}")
        _embedding_availability_cached = False
        return False


def reset_embedding_availability_cache():
    """Reset the cached embedding availability status for retesting."""
    global _embedding_availability_cached
    _embedding_availability_cached = None


def get_embedding_status_message() -> str:
    """
    Get a user-friendly message about embedding availability status.
    
    Returns:
        str: Status message for UI display
    """
    if are_embeddings_available():
        return "✅ ChromaDB embeddings are available and functional"
    else:
        return "⚠️ ChromaDB embeddings are unavailable due to version conflicts or configuration issues"


def check_and_warn_embedding_unavailable(feature_name: str = "this feature") -> bool:
    """
    Check embedding availability and log warning if unavailable.
    
    Args:
        feature_name: Name of the feature that requires embeddings
        
    Returns:
        bool: True if embeddings are available, False if unavailable (and warning logged)
    """
    if are_embeddings_available():
        return True
    else:
        logger.warning(f"🚫 {feature_name} requires ChromaDB embeddings which are currently unavailable. "
                      f"Skipping embedding-dependent functionality.")
        return False