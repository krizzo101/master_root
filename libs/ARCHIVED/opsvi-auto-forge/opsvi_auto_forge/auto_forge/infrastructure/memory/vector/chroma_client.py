"""ChromaDB client for vector memory and context bundles."""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

# Import ContextBundle locally to avoid circular imports
try:
    from opsvi_auto_forge.core.prompting.models import ContextBundle
except ImportError:
    # Fallback for when ContextBundle is not available
    from typing import TypedDict

    class ContextBundle(TypedDict):
        purpose: str
        tokens: int
        summary: str
        sources: list


logger = logging.getLogger(__name__)


class ChromaClient:
    """ChromaDB client for context bundles and embeddings."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8000,
        collection_name: str = "context_bundles",
        embedding_model: str = "text-embedding-3-small",
        api_key: Optional[str] = None,
    ):
        """Initialize ChromaDB client.

        Args:
            host: ChromaDB server host
            port: ChromaDB server port
            collection_name: Name of the collection for context bundles
            embedding_model: OpenAI embedding model to use
            api_key: OpenAI API key for embeddings
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.embedding_model = embedding_model

        # Initialize ChromaDB client
        try:
            self.client = chromadb.HttpClient(
                host=host,
                port=port,
                settings=(
                    Settings(
                        chroma_client_auth_provider="chromadb.auth.basic.BasicAuthClientProvider",
                        chroma_client_auth_credentials="admin:password123",
                        anonymized_telemetry=False,  # Disable telemetry
                    )
                    if host != "localhost"
                    else Settings(anonymized_telemetry=False)  # Disable telemetry
                ),
            )
            logger.info(f"Connected to ChromaDB at {host}:{port}")
        except Exception as e:
            logger.warning(
                f"Failed to connect to ChromaDB, using persistent client: {e}"
            )
            self.client = chromadb.PersistentClient(
                path="./chroma_db",
                settings=Settings(anonymized_telemetry=False),  # Disable telemetry
            )

        # Initialize embedding function
        if api_key:
            self.embedding_function = OpenAIEmbeddingFunction(
                api_key=api_key, model_name=embedding_model
            )
        else:
            # Use default embedding function
            self.embedding_function = (
                chromadb.utils.embedding_functions.DefaultEmbeddingFunction()
            )

        # Get or create collection with comprehensive error handling
        try:
            # First try to get existing collection
            try:
                self.collection = self.client.get_collection(name=collection_name)
                logger.info(f"Retrieved existing collection: {collection_name}")
            except Exception:
                # Collection doesn't exist, create it
                try:
                    self.collection = self.client.create_collection(
                        name=collection_name,
                        embedding_function=self.embedding_function,
                        metadata={"description": "Context bundles for DPG subsystem"},
                    )
                    logger.info(f"Successfully created collection: {collection_name}")
                except Exception as create_error:
                    error_msg = str(create_error)
                    logger.warning(f"ChromaDB collection creation failed: {error_msg}")

                    # Handle version compatibility issues
                    if "_type" in error_msg or "409" in error_msg:
                        # Try creating with minimal configuration
                        try:
                            self.collection = self.client.create_collection(
                                name=collection_name,
                                metadata={
                                    "description": "Context bundles for DPG subsystem"
                                },
                            )
                            logger.info(
                                f"Created collection with minimal config: {collection_name}"
                            )
                        except Exception as minimal_error:
                            logger.error(
                                f"Failed to create collection with minimal config: {minimal_error}"
                            )
                            # Last resort: try to get collection without embedding function
                            try:
                                self.collection = self.client.get_collection(
                                    name=collection_name
                                )
                                logger.info(
                                    f"Retrieved collection without embedding function: {collection_name}"
                                )
                            except Exception as final_error:
                                logger.error(
                                    f"All ChromaDB collection attempts failed: {final_error}"
                                )
                                raise
                    else:
                        raise
        except Exception as e:
            logger.error(f"ChromaDB collection initialization failed: {e}")
            # Create a fallback collection name to avoid conflicts
            fallback_name = f"{collection_name}_fallback_{int(time.time())}"
            try:
                self.collection = self.client.create_collection(
                    name=fallback_name,
                    metadata={"description": "Fallback context bundles collection"},
                )
                logger.info(f"Created fallback collection: {fallback_name}")
            except Exception as fallback_error:
                logger.error(f"Failed to create fallback collection: {fallback_error}")
                raise

        logger.info(f"Using collection: {collection_name}")

    def store_context_bundle(
        self, bundle: ContextBundle, metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a context bundle in ChromaDB.

        Args:
            bundle: Context bundle to store
            metadata: Additional metadata

        Returns:
            Document ID
        """
        doc_id = str(uuid4())

        # Prepare metadata
        doc_metadata = {
            "purpose": bundle.purpose,
            "tokens": bundle.tokens,
            "sources": ",".join(bundle.sources),
            "kind": "context_bundle",
            **(metadata or {}),
        }

        # Store in collection
        self.collection.add(
            ids=[doc_id], documents=[bundle.summary], metadatas=[doc_metadata]
        )

        logger.info(f"Stored context bundle {doc_id} with {bundle.tokens} tokens")
        return doc_id

    def search_context_bundles(
        self, query: str, top_k: int = 8, filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, ContextBundle, float]]:
        """Search for relevant context bundles.

        Args:
            query: Search query
            top_k: Number of results to return
            filters: Metadata filters

        Returns:
            List of (doc_id, bundle, score) tuples
        """
        # Prepare filters
        search_filters = {"kind": "context_bundle"}
        if filters:
            search_filters.update(filters)

        # Search collection
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=search_filters,
            include=["metadatas", "distances"],
        )

        bundles = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i]
                score = 1.0 - distance  # Convert distance to similarity score

                bundle = ContextBundle(
                    purpose=metadata["purpose"],
                    tokens=metadata["tokens"],
                    summary=results["documents"][0][i],
                    sources=(
                        metadata["sources"].split(",") if metadata["sources"] else []
                    ),
                )

                bundles.append((doc_id, bundle, score))

        logger.info(f"Found {len(bundles)} relevant context bundles for query: {query}")
        return bundles

    def get_context_bundle(self, doc_id: str) -> Optional[ContextBundle]:
        """Retrieve a specific context bundle.

        Args:
            doc_id: Document ID

        Returns:
            Context bundle if found, None otherwise
        """
        try:
            results = self.collection.get(
                ids=[doc_id], include=["metadatas", "documents"]
            )

            if results["ids"]:
                metadata = results["metadatas"][0]
                document = results["documents"][0]

                return ContextBundle(
                    purpose=metadata["purpose"],
                    tokens=metadata["tokens"],
                    summary=document,
                    sources=(
                        metadata["sources"].split(",") if metadata["sources"] else []
                    ),
                )
        except Exception as e:
            logger.error(f"Failed to retrieve context bundle {doc_id}: {e}")

        return None

    def delete_context_bundle(self, doc_id: str) -> bool:
        """Delete a context bundle.

        Args:
            doc_id: Document ID to delete

        Returns:
            True if deleted, False otherwise
        """
        try:
            self.collection.delete(ids=[doc_id])
            logger.info(f"Deleted context bundle {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete context bundle {doc_id}: {e}")
            return False

    def list_context_bundles(
        self, filters: Optional[Dict[str, Any]] = None, limit: int = 100
    ) -> List[Tuple[str, ContextBundle]]:
        """List context bundles with optional filtering.

        Args:
            filters: Metadata filters
            limit: Maximum number of results

        Returns:
            List of (doc_id, bundle) tuples
        """
        # Prepare filters
        search_filters = {"kind": "context_bundle"}
        if filters:
            search_filters.update(filters)

        # Get documents
        results = self.collection.get(
            where=search_filters, limit=limit, include=["metadatas", "documents"]
        )

        bundles = []
        if results["ids"]:
            for i, doc_id in enumerate(results["ids"]):
                metadata = results["metadatas"][i]
                document = results["documents"][i]

                bundle = ContextBundle(
                    purpose=metadata["purpose"],
                    tokens=metadata["tokens"],
                    summary=document,
                    sources=(
                        metadata["sources"].split(",") if metadata["sources"] else []
                    ),
                )

                bundles.append((doc_id, bundle))

        return bundles

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics.

        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": self.collection_name,
                "embedding_model": self.embedding_model,
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"error": str(e)}
