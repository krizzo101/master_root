"""HTTP client base for opsvi-http."""
from typing import Any, Dict, Optional
import logging
from opsvi_http.core.base import OpsviHttpManager
from opsvi_http.config.settings import OpsviHttpConfig
from opsvi_http.exceptions.base import OpsviHttpError

logger = logging.getLogger(__name__)

class HTTPClient(OpsviHttpManager):
    async def request(self, method: str, url: str, **kwargs: Any) -> Any:
        raise NotImplementedError
