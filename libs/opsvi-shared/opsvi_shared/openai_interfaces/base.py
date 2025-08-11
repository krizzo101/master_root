import logging
import os
from typing import Dict, Optional

import openai


class OpenAIBaseInterface:
    """
    Base class for all OpenAI API interfaces.
    Handles authentication, error handling, and SDK/raw HTTP selection.
    """

    def __init__(
        self, api_key: Optional[str] = None, organization: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.organization = organization or os.getenv("OPENAI_ORG_ID")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key must be provided via argument or OPENAI_API_KEY env var."
            )
        openai.api_key = self.api_key
        if self.organization:
            openai.organization = self.organization
        self.client = openai.OpenAI(
            api_key=self.api_key, organization=self.organization
        )
        logging.getLogger(__name__).debug(
            f"[OpenAIBaseInterface] self.client initialized: {self.client}"
        )

    def _handle_error(self, error: Exception) -> None:
        # Standardized error handling for all interfaces
        raise error

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        if self.organization:
            headers["OpenAI-Organization"] = self.organization
        return headers
