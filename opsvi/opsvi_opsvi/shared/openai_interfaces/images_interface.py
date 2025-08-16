from typing import Any, Dict

import openai

from shared.openai_interfaces.base import OpenAIBaseInterface


class OpenAIImagesInterface(OpenAIBaseInterface):
    """
    Interface for OpenAI Images API (DALL·E).
    Reference: https://platform.openai.com/docs/api-reference/images

    This interface provides both synchronous and asynchronous methods for all images endpoints.
    All methods are standards-compliant and mapped to the official OpenAI Python SDK.
    """

    def create_image(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate an image from a prompt.
        POST /v1/images/generations
        """
        try:
            response = openai.Image.create(prompt=prompt, **kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def edit_image(
        self, image: bytes, mask: bytes, prompt: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Edit an image based on a prompt and a mask.
        POST /v1/images/edits
        """
        try:
            response = openai.Image.edit(
                image=image, mask=mask, prompt=prompt, **kwargs
            )
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def create_image_variation(self, image: bytes, **kwargs) -> Dict[str, Any]:
        """
        Create a variation of a given image.
        POST /v1/images/variations
        """
        try:
            response = openai.Image.create_variation(image=image, **kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def acreate_image(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Async: Generate an image from a prompt.
        POST /v1/images/generations
        """
        try:
            response = await openai.Image.acreate(prompt=prompt, **kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def aedit_image(
        self, image: bytes, mask: bytes, prompt: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Async: Edit an image based on a prompt and a mask.
        POST /v1/images/edits
        """
        try:
            response = await openai.Image.aedit(
                image=image, mask=mask, prompt=prompt, **kwargs
            )
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def acreate_image_variation(self, image: bytes, **kwargs) -> Dict[str, Any]:
        """
        Async: Create a variation of a given image.
        POST /v1/images/variations
        """
        try:
            response = await openai.Image.acreate_variation(image=image, **kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)
