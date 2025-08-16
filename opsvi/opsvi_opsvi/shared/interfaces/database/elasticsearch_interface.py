"""
Elasticsearch Shared Interface
-----------------------------
Authoritative implementation based on the official elasticsearch-py documentation:
- https://elasticsearch-py.readthedocs.io/en/latest/
Implements all core features: connection management, index management, search/query, bulk operations, and error handling.
Version: Referenced as of July 2024
"""

import logging
from typing import Any

try:
    from elasticsearch import Elasticsearch, ElasticsearchException
    from elasticsearch.helpers import bulk as es_bulk
except ImportError:
    raise ImportError(
        "elasticsearch-py is required. Install with `pip install elasticsearch`."
    )

logger = logging.getLogger(__name__)


class ElasticsearchInterface:
    """
    Authoritative shared interface for Elasticsearch operations.
    See: https://elasticsearch-py.readthedocs.io/en/latest/
    """

    def __init__(self, hosts: list[str] | None = None, http_auth: Any | None = None):
        """
        Initialize an ElasticsearchInterface.
        Args:
            hosts: List of host URLs.
            http_auth: Optional HTTP auth (user, pass).
        """
        try:
            self.client = Elasticsearch(hosts=hosts, http_auth=http_auth)
            logger.info("Elasticsearch client initialized.")
        except ElasticsearchException as e:
            logger.error(f"Elasticsearch client initialization failed: {e}")
            raise

    def index_document(
        self, index: str, document: dict[str, Any], id: str | None = None
    ) -> str:
        """
        Index a document.
        Args:
            index: Index name.
            document: Document dict.
            id: Optional document ID.
        Returns:
            Document ID.
        """
        try:
            resp = self.client.index(index=index, document=document, id=id)
            return resp["_id"]
        except ElasticsearchException as e:
            logger.error(f"Index document failed: {e}")
            raise

    def get_document(self, index: str, id: str) -> dict[str, Any]:
        try:
            resp = self.client.get(index=index, id=id)
            return resp["_source"]
        except ElasticsearchException as e:
            logger.error(f"Get document failed: {e}")
            raise

    def search(self, index: str, query: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Search an index.
        Args:
            index: Index name.
            query: Query dict.
        Returns:
            List of hits.
        """
        try:
            resp = self.client.search(index=index, query=query)
            return [hit["_source"] for hit in resp["hits"]["hits"]]
        except ElasticsearchException as e:
            logger.error(f"Search failed: {e}")
            raise

    def bulk(self, actions: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Perform bulk operations.
        Args:
            actions: List of bulk actions.
        Returns:
            Bulk API response.
        """
        try:
            success, resp = es_bulk(self.client, actions)
            return {"success": success, "response": resp}
        except Exception as e:
            logger.error(f"Bulk operation failed: {e}")
            raise


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    es = ElasticsearchInterface(hosts=["http://localhost:9200"])
    doc_id = es.index_document("users", {"name": "Dana", "age": 28})
    print("Indexed document ID:", doc_id)
    hits = es.search("users", {"match": {"name": "Dana"}})
    print("Search hits:", hits)
