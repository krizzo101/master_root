"""
OAuth2/JWT Auth Shared Interface
-------------------------------
Authoritative implementation based on the official PyJWT documentation:
- https://pyjwt.readthedocs.io/en/stable/
Implements all core features: JWT token creation, validation, and user extraction. OAuth2 flows are not implemented.
Version: Referenced as of July 2024
"""

import logging
from typing import Any, Dict, Optional

try:
    import jwt
except ImportError:
    raise ImportError("pyjwt is required. Install with `pip install pyjwt`.")

logger = logging.getLogger(__name__)


class AuthInterface:
    """
    Authoritative shared interface for JWT validation and creation (PyJWT).
    OAuth2 flows are not implemented. See: https://pyjwt.readthedocs.io/en/stable/
    """

    def __init__(
        self, secret_key: str, algorithm: str = "HS256", expires_in: int = 3600
    ):
        """
        Initialize the AuthInterface.
        Args:
            secret_key: Secret key for signing tokens.
            algorithm: JWT algorithm (default HS256).
            expires_in: Token expiration in seconds.
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expires_in = expires_in

    def create_token(self, data: Dict[str, Any]) -> str:
        """
        Create a JWT token with the given data.
        See: https://pyjwt.readthedocs.io/en/stable/usage.html
        """
        import datetime

        payload = data.copy()
        payload["exp"] = datetime.datetime.utcnow() + datetime.timedelta(
            seconds=self.expires_in
        )
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate a JWT token and return the payload.
        See: https://pyjwt.readthedocs.io/en/stable/usage.html
        """
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except jwt.ExpiredSignatureError:
            logger.error("Token expired.")
            raise
        except jwt.InvalidTokenError:
            logger.error("Invalid token.")
            raise

    def get_user(self, token: str) -> Optional[str]:
        """
        Extract the user identifier from a JWT token.
        Returns the 'sub' claim if present.
        """
        payload = self.validate_token(token)
        return payload.get("sub")


# Example usage and advanced features are available in the official docs:
# https://pyjwt.readthedocs.io/en/stable/
