"""HTTP server base for opsvi-http."""
from typing import Any
import logging
from opsvi_http.core.base import OpsviHttpManager
from opsvi_http.config.settings import OpsviHttpConfig

logger = logging.getLogger(__name__)

class HTTPServer(OpsviHttpManager):
    async def start(self) -> None:
        await self.initialize()
    
    async def stop(self) -> None:
        await self.shutdown()
