"""Authentication middleware for opsvi-core."""

import base64
import hashlib
import hmac
import logging
from abc import abstractmethod
from typing import Any, Callable, Dict, Optional, Set, Awaitable

from opsvi_foundation.middleware import Middleware, Request, Response

logger = logging.getLogger(__name__)


class AuthMiddleware(Middleware):
    """Base authentication middleware."""
    
    def __init__(
        self,
        name: str = "AuthMiddleware",
        realm: str = "Protected",
        exclude_paths: Optional[Set[str]] = None
    ):
        """Initialize auth middleware.
        
        Args:
            name: Name of the middleware
            realm: Authentication realm
            exclude_paths: Paths to exclude from authentication
        """
        super().__init__(name)
        self.realm = realm
        self.exclude_paths = exclude_paths or set()
    
    async def process(
        self,
        request: Request,
        next_handler: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request with authentication."""
        # Skip auth for excluded paths
        if request.path in self.exclude_paths:
            return await next_handler(request)
        
        # Authenticate request
        auth_result = await self.authenticate(request)
        
        if auth_result:
            # Store auth info in metadata
            request.metadata["auth"] = auth_result
            return await next_handler(request)
        else:
            return self._create_unauthorized_response()
    
    @abstractmethod
    async def authenticate(self, request: Request) -> Optional[Dict[str, Any]]:
        """Authenticate the request.
        
        Args:
            request: The request to authenticate
            
        Returns:
            Authentication info if successful, None otherwise
        """
        pass
    
    def _create_unauthorized_response(self) -> Response:
        """Create unauthorized response."""
        return Response(
            status=401,
            headers={
                "WWW-Authenticate": f'Basic realm="{self.realm}"',
                "Content-Type": "application/json"
            },
            body={"error": "Unauthorized"},
            metadata={"error": True}
        )


class BasicAuthMiddleware(AuthMiddleware):
    """Basic authentication middleware."""
    
    def __init__(
        self,
        users: Dict[str, str],
        name: str = "BasicAuthMiddleware",
        realm: str = "Protected",
        exclude_paths: Optional[Set[str]] = None,
        hash_passwords: bool = False
    ):
        """Initialize basic auth middleware.
        
        Args:
            users: Dictionary of username: password
            name: Name of the middleware
            realm: Authentication realm
            exclude_paths: Paths to exclude from authentication
            hash_passwords: Whether passwords are hashed
        """
        super().__init__(name, realm, exclude_paths)
        self.users = users
        self.hash_passwords = hash_passwords
    
    async def authenticate(self, request: Request) -> Optional[Dict[str, Any]]:
        """Authenticate using basic auth."""
        auth_header = request.headers.get("Authorization", "")
        
        if not auth_header.startswith("Basic "):
            return None
        
        try:
            # Decode credentials
            encoded = auth_header[6:]  # Remove "Basic "
            decoded = base64.b64decode(encoded).decode("utf-8")
            username, password = decoded.split(":", 1)
            
            # Check credentials
            if username in self.users:
                stored_password = self.users[username]
                
                if self.hash_passwords:
                    # Compare hashed passwords
                    password_hash = hashlib.sha256(password.encode()).hexdigest()
                    if password_hash == stored_password:
                        return {"username": username, "type": "basic"}
                else:
                    # Compare plain passwords
                    if password == stored_password:
                        return {"username": username, "type": "basic"}
            
            return None
            
        except Exception as e:
            logger.error(f"Error in basic auth: {e}")
            return None


class TokenAuthMiddleware(AuthMiddleware):
    """Token-based authentication middleware."""
    
    def __init__(
        self,
        tokens: Set[str],
        name: str = "TokenAuthMiddleware",
        realm: str = "Protected",
        exclude_paths: Optional[Set[str]] = None,
        header_name: str = "X-API-Token",
        query_param: Optional[str] = None
    ):
        """Initialize token auth middleware.
        
        Args:
            tokens: Set of valid tokens
            name: Name of the middleware
            realm: Authentication realm
            exclude_paths: Paths to exclude from authentication
            header_name: Header name for token
            query_param: Optional query parameter name for token
        """
        super().__init__(name, realm, exclude_paths)
        self.tokens = tokens
        self.header_name = header_name
        self.query_param = query_param
    
    async def authenticate(self, request: Request) -> Optional[Dict[str, Any]]:
        """Authenticate using token."""
        token = None
        
        # Check header
        token = request.headers.get(self.header_name)
        
        # Check query parameter if configured
        if not token and self.query_param:
            # Extract from query string (simplified)
            if "?" in request.path:
                query_string = request.path.split("?", 1)[1]
                for param in query_string.split("&"):
                    if "=" in param:
                        key, value = param.split("=", 1)
                        if key == self.query_param:
                            token = value
                            break
        
        # Validate token
        if token and token in self.tokens:
            return {"token": token[:8] + "...", "type": "token"}
        
        return None


class JWTAuthMiddleware(AuthMiddleware):
    """JWT authentication middleware."""
    
    def __init__(
        self,
        secret: str,
        name: str = "JWTAuthMiddleware",
        realm: str = "Protected",
        exclude_paths: Optional[Set[str]] = None,
        algorithm: str = "HS256",
        header_name: str = "Authorization",
        prefix: str = "Bearer"
    ):
        """Initialize JWT auth middleware.
        
        Args:
            secret: JWT secret key
            name: Name of the middleware
            realm: Authentication realm
            exclude_paths: Paths to exclude from authentication
            algorithm: JWT algorithm
            header_name: Header name for token
            prefix: Token prefix (e.g., "Bearer")
        """
        super().__init__(name, realm, exclude_paths)
        self.secret = secret
        self.algorithm = algorithm
        self.header_name = header_name
        self.prefix = prefix
    
    async def authenticate(self, request: Request) -> Optional[Dict[str, Any]]:
        """Authenticate using JWT."""
        auth_header = request.headers.get(self.header_name, "")
        
        if not auth_header.startswith(f"{self.prefix} "):
            return None
        
        try:
            # Extract token
            token = auth_header[len(self.prefix) + 1:]
            
            # Decode JWT (simplified - in production use PyJWT)
            # This is a stub implementation
            logger.warning("JWT authentication is a stub - install PyJWT for full support")
            
            # For demo purposes, just check if token exists
            if token:
                return {
                    "token": token[:8] + "...",
                    "type": "jwt",
                    "claims": {}  # Would contain decoded claims
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in JWT auth: {e}")
            return None


class APIKeyAuthMiddleware(AuthMiddleware):
    """API key authentication middleware."""
    
    def __init__(
        self,
        api_keys: Dict[str, Dict[str, Any]],
        name: str = "APIKeyAuthMiddleware",
        realm: str = "Protected",
        exclude_paths: Optional[Set[str]] = None,
        header_name: str = "X-API-Key"
    ):
        """Initialize API key auth middleware.
        
        Args:
            api_keys: Dictionary of API key: metadata
            name: Name of the middleware
            realm: Authentication realm
            exclude_paths: Paths to exclude from authentication
            header_name: Header name for API key
        """
        super().__init__(name, realm, exclude_paths)
        self.api_keys = api_keys
        self.header_name = header_name
    
    async def authenticate(self, request: Request) -> Optional[Dict[str, Any]]:
        """Authenticate using API key."""
        api_key = request.headers.get(self.header_name)
        
        if api_key and api_key in self.api_keys:
            metadata = self.api_keys[api_key]
            return {
                "api_key": api_key[:8] + "...",
                "type": "api_key",
                "metadata": metadata
            }
        
        return None


__all__ = [
    "AuthMiddleware",
    "BasicAuthMiddleware",
    "TokenAuthMiddleware",
    "JWTAuthMiddleware",
    "APIKeyAuthMiddleware",
]