from typing import Any, Dict, List

import openai

from shared.openai_interfaces.base import OpenAIBaseInterface


class OpenAIVectorStoresInterface(OpenAIBaseInterface):
    """
    Interface for OpenAI Vector Stores API (Beta).
    Reference: https://platform.openai.com/docs/api-reference/vector-stores
    """

    def create_vector_store(self, **kwargs) -> Dict[str, Any]:
        """
        Create a vector store.
        POST /v1/vector_stores
        """
        try:
            response = self.client.vector_stores.create(**kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def retrieve_vector_store(self, vector_store_id: str) -> Dict[str, Any]:
        """
        Retrieve a vector store by ID.
        GET /v1/vector_stores/{vector_store_id}
        """
        try:
            response = self.client.vector_stores.retrieve(vector_store_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def list_vector_stores(self) -> List[Dict[str, Any]]:
        """
        List all vector stores.
        GET /v1/vector_stores
        """
        try:
            response = self.client.vector_stores.list()
            return response["data"]
        except Exception as e:
            self._handle_error(e)

    def update_vector_store(self, vector_store_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update a vector store.
        POST /v1/vector_stores/{vector_store_id}
        """
        try:
            response = self.client.vector_stores.update(vector_store_id, **kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def delete_vector_store(self, vector_store_id: str) -> Dict[str, Any]:
        """
        Delete a vector store.
        DELETE /v1/vector_stores/{vector_store_id}
        """
        try:
            response = openai.VectorStore.delete(vector_store_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def list_files(self, vector_store_id: str) -> List[Dict[str, Any]]:
        """
        List files in a vector store.
        GET /v1/vector_stores/{vector_store_id}/files
        """
        try:
            response = openai.VectorStore.list_files(vector_store_id)
            return response["data"]
        except Exception as e:
            self._handle_error(e)

    def add_file(self, vector_store_id: str, file_id: str) -> Dict[str, Any]:
        """
        Add a file to a vector store.
        POST /v1/vector_stores/{vector_store_id}/files
        """
        try:
            response = openai.VectorStore.add_file(vector_store_id, file_id=file_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def remove_file(self, vector_store_id: str, file_id: str) -> Dict[str, Any]:
        """
        Remove a file from a vector store.
        DELETE /v1/vector_stores/{vector_store_id}/files/{file_id}
        """
        try:
            response = openai.VectorStore.remove_file(vector_store_id, file_id=file_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def list_file_batches(self, vector_store_id: str) -> List[Dict[str, Any]]:
        """
        List file batches in a vector store.
        GET /v1/vector_stores/{vector_store_id}/file_batches
        """
        try:
            response = openai.VectorStore.list_file_batches(vector_store_id)
            return response["data"]
        except Exception as e:
            self._handle_error(e)

    def retrieve_file_batch(
        self, vector_store_id: str, batch_id: str
    ) -> Dict[str, Any]:
        """
        Retrieve a file batch by ID.
        GET /v1/vector_stores/{vector_store_id}/file_batches/{batch_id}
        """
        try:
            response = openai.VectorStore.retrieve_file_batch(vector_store_id, batch_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def acreate_vector_store(self, **kwargs) -> Dict[str, Any]:
        """
        Async: Create a vector store.
        POST /v1/vector_stores
        """
        try:
            response = await openai.VectorStore.acreate(**kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def aretrieve_vector_store(self, vector_store_id: str) -> Dict[str, Any]:
        """
        Async: Retrieve a vector store by ID.
        GET /v1/vector_stores/{vector_store_id}
        """
        try:
            response = await openai.VectorStore.aretrieve(vector_store_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def alist_vector_stores(self) -> List[Dict[str, Any]]:
        """
        Async: List all vector stores.
        GET /v1/vector_stores
        """
        try:
            response = await openai.VectorStore.alist()
            return response["data"]
        except Exception as e:
            self._handle_error(e)

    async def aupdate_vector_store(
        self, vector_store_id: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Async: Update a vector store.
        POST /v1/vector_stores/{vector_store_id}
        """
        try:
            response = await openai.VectorStore.aupdate(vector_store_id, **kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def adelete_vector_store(self, vector_store_id: str) -> Dict[str, Any]:
        """
        Async: Delete a vector store.
        DELETE /v1/vector_stores/{vector_store_id}
        """
        try:
            response = await openai.VectorStore.adelete(vector_store_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def alist_files(self, vector_store_id: str) -> List[Dict[str, Any]]:
        """
        Async: List files in a vector store.
        GET /v1/vector_stores/{vector_store_id}/files
        """
        try:
            response = await openai.VectorStore.alist_files(vector_store_id)
            return response["data"]
        except Exception as e:
            self._handle_error(e)

    async def aadd_file(self, vector_store_id: str, file_id: str) -> Dict[str, Any]:
        """
        Async: Add a file to a vector store.
        POST /v1/vector_stores/{vector_store_id}/files
        """
        try:
            response = await openai.VectorStore.aadd_file(
                vector_store_id, file_id=file_id
            )
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def aremove_file(self, vector_store_id: str, file_id: str) -> Dict[str, Any]:
        """
        Async: Remove a file from a vector store.
        DELETE /v1/vector_stores/{vector_store_id}/files/{file_id}
        """
        try:
            response = await openai.VectorStore.aremove_file(
                vector_store_id, file_id=file_id
            )
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def alist_file_batches(self, vector_store_id: str) -> List[Dict[str, Any]]:
        """
        Async: List file batches in a vector store.
        GET /v1/vector_stores/{vector_store_id}/file_batches
        """
        try:
            response = await openai.VectorStore.alist_file_batches(vector_store_id)
            return response["data"]
        except Exception as e:
            self._handle_error(e)

    async def aretrieve_file_batch(
        self, vector_store_id: str, batch_id: str
    ) -> Dict[str, Any]:
        """
        Async: Retrieve a file batch by ID.
        GET /v1/vector_stores/{vector_store_id}/file_batches/{batch_id}
        """
        try:
            response = await openai.VectorStore.aretrieve_file_batch(
                vector_store_id, batch_id
            )
            return dict(response)
        except Exception as e:
            self._handle_error(e)
