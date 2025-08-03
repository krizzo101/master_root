import io
from typing import Any, Dict, List

import openai

from shared.openai_interfaces.base import OpenAIBaseInterface


class OpenAIFilesInterface(OpenAIBaseInterface):
    """
    Interface for OpenAI Files API.
    Reference: https://platform.openai.com/docs/api-reference/files
    """

    def list_files(self) -> List[Dict[str, Any]]:
        """
        List all files.
        GET /v1/files
        """
        try:
            response = self.client.files.list()
            return response["data"]
        except Exception as e:
            self._handle_error(e)

    def upload_file(self, file_bytes: bytes, purpose: str, **kwargs) -> Dict[str, Any]:
        """
        Upload a file for a specific purpose.
        POST /v1/files
        """
        try:
            file_obj = io.BytesIO(file_bytes)
            response = self.client.files.create(
                file=file_obj, purpose=purpose, **kwargs
            )
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def delete_file(self, file_id: str) -> Dict[str, Any]:
        """
        Delete a file by ID.
        DELETE /v1/files/{file_id}
        """
        try:
            response = self.client.files.delete(file_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def retrieve_file(self, file_id: str) -> Dict[str, Any]:
        """
        Retrieve file metadata by ID.
        GET /v1/files/{file_id}
        """
        try:
            response = self.client.files.retrieve(file_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def retrieve_file_content(self, file_id: str) -> bytes:
        """
        Retrieve the content of a file by ID.
        GET /v1/files/{file_id}/content
        """
        try:
            response = self.client.files.download(file_id)
            return response
        except Exception as e:
            self._handle_error(e)

    async def alist_files(self) -> List[Dict[str, Any]]:
        """
        Async: List all files.
        GET /v1/files
        """
        try:
            response = await openai.File.alist()
            return response["data"]
        except Exception as e:
            self._handle_error(e)

    async def aupload_file(
        self, file_bytes: bytes, purpose: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Async: Upload a file for a specific purpose.
        POST /v1/files
        """
        try:
            file_obj = io.BytesIO(file_bytes)
            response = await openai.File.acreate(
                file=file_obj, purpose=purpose, **kwargs
            )
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def adelete_file(self, file_id: str) -> Dict[str, Any]:
        """
        Async: Delete a file by ID.
        DELETE /v1/files/{file_id}
        """
        try:
            response = await openai.File.adelete(file_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def aretrieve_file(self, file_id: str) -> Dict[str, Any]:
        """
        Async: Retrieve file metadata by ID.
        GET /v1/files/{file_id}
        """
        try:
            response = await openai.File.aretrieve(file_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def aretrieve_file_content(self, file_id: str) -> bytes:
        """
        Async: Retrieve the content of a file by ID.
        GET /v1/files/{file_id}/content
        """
        try:
            response = await openai.File.adownload(file_id)
            return response
        except Exception as e:
            self._handle_error(e)
