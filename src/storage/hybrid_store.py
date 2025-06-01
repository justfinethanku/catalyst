"""Minimal HybridStore with ChromaDB integration."""
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import hashlib
from datetime import datetime
import logging

# Disable tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

logger = logging.getLogger(__name__)


class HybridStore:
    """Simple hybrid storage with ChromaDB and JSON backup."""
    
    def __init__(
        self,
        vector_db_path: str = "./catalyst_vector_db",
        json_backup_path: str = "./clients",
        collection_name: str = "research_data",
        openai_api_key: Optional[str] = None
    ):
        """Initialize storage."""
        from ..core.embedding_utils import are_embeddings_available, check_and_warn_embedding_unavailable
        
        # Check if embeddings are available before attempting ChromaDB initialization
        self.embeddings_available = are_embeddings_available()
        
        if self.embeddings_available:
            try:
                import chromadb
                from chromadb.config import Settings
                from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
                
                # Initialize ChromaDB
                self.client = chromadb.PersistentClient(
                    path=vector_db_path,
                    settings=Settings(anonymized_telemetry=False)
                )
                
                # Configure embedding function
                embedding_function = DefaultEmbeddingFunction()
                logger.info("🔗 Using ChromaDB default embeddings")
                
                # Create or get collection with embedding function
                self.collection = self.client.get_or_create_collection(
                    name=collection_name,
                    metadata={"description": f"Catalyst {collection_name} storage"},
                    embedding_function=embedding_function
                )
                
            except Exception as e:
                logger.error(f"❌ ChromaDB initialization failed despite embeddings check: {e}")
                self.embeddings_available = False
                self.client = None
                self.collection = None
        else:
            check_and_warn_embedding_unavailable("ChromaDB vector storage")
            self.client = None
            self.collection = None
        
        # JSON backup path (always available)
        self.json_path = Path(json_backup_path)
        self.json_path.mkdir(exist_ok=True)
    
    def store(
        self,
        content: str,
        metadata: Dict[str, Any],
        client_name: str
    ) -> str:
        """
        Store research data in vector DB and JSON.
        
        Args:
            content: The research content to store
            metadata: Metadata about the research
            client_name: Name of the client
            
        Returns:
            Document ID
        """
        # Generate ID
        timestamp = datetime.now().isoformat()
        id_string = f"{client_name}_{metadata.get('step', 'unknown')}_{timestamp}"
        doc_id = hashlib.md5(id_string.encode()).hexdigest()
        
        # Add to metadata
        metadata["client"] = client_name
        metadata["timestamp"] = timestamp
        
        # Store in ChromaDB if available
        if self.embeddings_available and self.collection:
            try:
                self.collection.add(
                    documents=[content],
                    metadatas=[metadata],
                    ids=[doc_id]
                )
                logger.debug(f"✅ Stored document {doc_id} in ChromaDB")
            except Exception as e:
                logger.warning(f"⚠️ ChromaDB storage failed for {doc_id}: {e}")
        else:
            logger.debug(f"📝 Storing {doc_id} in JSON only (ChromaDB unavailable)")
        
        # Always backup to JSON
        self._save_to_json(content, metadata, doc_id, client_name)
        
        return doc_id
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_client: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar content.
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter_client: Optional client filter
            
        Returns:
            List of results with content and metadata
        """
        formatted = []
        
        # Use ChromaDB search if available
        if self.embeddings_available and self.collection:
            try:
                # Build filter
                where_clause = None
                if filter_client:
                    where_clause = {"client": filter_client}
                
                # Search
                results = self.collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where_clause
                )
                
                # Format results
                if results["documents"] and results["documents"][0]:
                    for i in range(len(results["documents"][0])):
                        formatted.append({
                            "content": results["documents"][0][i],
                            "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                            "distance": results["distances"][0][i] if results["distances"] else None,
                            "id": results["ids"][0][i] if results["ids"] else None
                        })
                        
                logger.debug(f"🔍 ChromaDB search returned {len(formatted)} results")
                
            except Exception as e:
                logger.warning(f"⚠️ ChromaDB search failed: {e}. Falling back to JSON search.")
                formatted = self._search_json_fallback(query, n_results, filter_client)
        else:
            # Fall back to JSON-based search
            logger.debug("🔍 Using JSON fallback search (ChromaDB unavailable)")
            formatted = self._search_json_fallback(query, n_results, filter_client)
        
        return formatted
    
    def get_all_clients(self) -> List[str]:
        """Get list of all clients in the database."""
        # Get all documents
        all_data = self.collection.get()
        
        clients = set()
        if all_data["metadatas"]:
            for metadata in all_data["metadatas"]:
                if metadata.get("client"):
                    clients.add(metadata["client"])
        
        return sorted(list(clients))
    
    def delete_client(self, client_name: str) -> Dict[str, Any]:
        """Delete all data for a specific client from both ChromaDB and JSON storage."""
        try:
            deleted_count = 0
            
            if self.embeddings_available and hasattr(self, 'collection'):
                # Get all documents for this client from ChromaDB
                all_data = self.collection.get()
                
                if all_data["metadatas"]:
                    # Find document IDs for this client
                    ids_to_delete = []
                    for i, metadata in enumerate(all_data["metadatas"]):
                        if metadata.get("client") == client_name:
                            ids_to_delete.append(all_data["ids"][i])
                    
                    # Delete from ChromaDB
                    if ids_to_delete:
                        self.collection.delete(ids=ids_to_delete)
                        deleted_count += len(ids_to_delete)
                        logger.info(f"🗑️ Deleted {len(ids_to_delete)} documents from ChromaDB for client: {client_name}")
            
            # Delete JSON backup directory
            client_dir = Path(self.json_backup_path) / client_name
            if client_dir.exists():
                import shutil
                shutil.rmtree(client_dir)
                logger.info(f"🗑️ Deleted JSON backup directory for client: {client_name}")
            
            logger.info(f"✅ Successfully deleted all data for client: {client_name}")
            
            return {
                "status": "success",
                "client_name": client_name,
                "deleted_documents": deleted_count,
                "message": f"Successfully deleted all data for {client_name}"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to delete client {client_name}: {e}")
            return {
                "status": "error",
                "client_name": client_name,
                "error": str(e),
                "message": f"Failed to delete client {client_name}: {e}"
            }
    
    def _save_to_json(
        self,
        content: str,
        metadata: Dict[str, Any],
        doc_id: str,
        client_name: str
    ):
        """Save backup to JSON file."""
        # Create client directory
        client_dir = self.json_path / client_name.lower().replace(" ", "_")
        client_dir.mkdir(exist_ok=True)
        
        # Save data
        data = {
            "id": doc_id,
            "content": content,
            "metadata": metadata,
            "stored_at": datetime.now().isoformat()
        }
        
        filename = f"{doc_id}.json"
        with open(client_dir / filename, "w") as f:
            json.dump(data, f, indent=2)
    
    def _search_json_fallback(self, query: str, n_results: int, filter_client: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fallback search using JSON files when ChromaDB is unavailable.
        
        This performs simple text matching rather than semantic search.
        """
        results = []
        query_lower = query.lower()
        
        # Determine which client directories to search
        if filter_client:
            client_dirs = [self.json_path / filter_client] if (self.json_path / filter_client).exists() else []
        else:
            client_dirs = [d for d in self.json_path.iterdir() if d.is_dir()]
        
        # Search through JSON files
        for client_dir in client_dirs:
            for json_file in client_dir.glob("*.json"):
                try:
                    with open(json_file, "r") as f:
                        data = json.load(f)
                    
                    content = data.get("content", "")
                    metadata = data.get("metadata", {})
                    
                    # Simple text matching (case-insensitive)
                    if query_lower in content.lower():
                        results.append({
                            "content": content,
                            "metadata": metadata,
                            "distance": None,  # No semantic distance available
                            "id": data.get("id")
                        })
                        
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"Failed to read JSON file {json_file}: {e}")
                    continue
        
        # Sort by recency (if timestamp available) and limit results
        results.sort(key=lambda x: x["metadata"].get("timestamp", ""), reverse=True)
        return results[:n_results]