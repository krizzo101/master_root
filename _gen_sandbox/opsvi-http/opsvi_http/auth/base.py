"""Auth base for opsvi-http."""
from opsvi_http.core.base import OpsviHttpManager

class AuthManager(OpsviHttpManager):
    async def authenticate(self, token: str) -> bool:
        return False
