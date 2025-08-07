"""
OAuth 2.0 and OpenID Connect integration utilities.

Provides OAuth flows, token validation, PKCE, and OIDC integration
for secure authentication and authorization.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
from typing import Any
from urllib.parse import urlencode

from opsvi_foundation.patterns import ComponentError


class OAuthError(ComponentError):
    """Base exception for OAuth-related errors."""


class TokenValidationError(OAuthError):
    """Raised when token validation fails."""


class PKCEError(OAuthError):
    """Raised when PKCE (Proof Key for Code Exchange) fails."""


class OAuthConfig:
    """Configuration for OAuth 2.0 client."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        authorization_endpoint: str,
        token_endpoint: str,
        scope: str | None = None,
        response_type: str = "code",
        grant_type: str = "authorization_code",
    ):
        """
        Initialize OAuth configuration.

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: Redirect URI for authorization
            authorization_endpoint: Authorization server endpoint
            token_endpoint: Token server endpoint
            scope: Requested scopes
            response_type: Response type (code, token)
            grant_type: Grant type for token exchange
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.authorization_endpoint = authorization_endpoint
        self.token_endpoint = token_endpoint
        self.scope = scope
        self.response_type = response_type
        self.grant_type = grant_type


class PKCE:
    """PKCE (Proof Key for Code Exchange) implementation."""

    @staticmethod
    def generate_code_verifier() -> str:
        """
        Generate a random code verifier for PKCE.

        Returns:
            Random code verifier string
        """
        token = secrets.token_urlsafe(32)
        return token[:128]  # Ensure it's not longer than 128 characters

    @staticmethod
    def generate_code_challenge(code_verifier: str) -> str:
        """
        Generate code challenge from code verifier.

        Args:
            code_verifier: The code verifier

        Returns:
            Base64 URL-encoded code challenge
        """
        sha256_hash = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(sha256_hash).decode("utf-8").rstrip("=")

    @staticmethod
    def verify_code_challenge(code_verifier: str, code_challenge: str) -> bool:
        """
        Verify code challenge against code verifier.

        Args:
            code_verifier: The code verifier
            code_challenge: The code challenge to verify

        Returns:
            True if verification succeeds, False otherwise
        """
        expected_challenge = PKCE.generate_code_challenge(code_verifier)
        return expected_challenge == code_challenge


class OAuthClient:
    """OAuth 2.0 client implementation."""

    def __init__(self, config: OAuthConfig):
        """
        Initialize OAuth client.

        Args:
            config: OAuth configuration
        """
        self.config = config
        self.state = None
        self.code_verifier = None
        self.code_challenge = None

    def generate_authorization_url(
        self,
        state: str | None = None,
        use_pkce: bool = True,
        additional_params: dict[str, str] | None = None,
    ) -> str:
        """
        Generate authorization URL for OAuth flow.

        Args:
            state: State parameter for CSRF protection
            use_pkce: Whether to use PKCE
            additional_params: Additional parameters to include

        Returns:
            Authorization URL
        """
        params = {
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "response_type": self.config.response_type,
            "scope": self.config.scope or "openid profile email",
        }

        # Add state for CSRF protection
        if state:
            self.state = state
            params["state"] = state
        else:
            self.state = secrets.token_urlsafe(32)
            params["state"] = self.state

        # Add PKCE if requested
        if use_pkce:
            self.code_verifier = PKCE.generate_code_verifier()
            self.code_challenge = PKCE.generate_code_challenge(self.code_verifier)
            params["code_challenge"] = self.code_challenge
            params["code_challenge_method"] = "S256"

        # Add additional parameters
        if additional_params:
            params.update(additional_params)

        # Build URL
        query_string = urlencode(params)
        return f"{self.config.authorization_endpoint}?{query_string}"

    def exchange_code_for_token(
        self,
        authorization_code: str,
        state: str | None = None,
    ) -> dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            authorization_code: Authorization code from callback
            state: State parameter for verification

        Returns:
            Token response dictionary

        Raises:
            OAuthError: If token exchange fails
        """
        # Verify state if provided
        if state and state != self.state:
            raise OAuthError("State parameter mismatch")

        # Prepare token request
        data = {
            "grant_type": self.config.grant_type,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "redirect_uri": self.config.redirect_uri,
            "code": authorization_code,
        }

        # Add PKCE code verifier if used
        if self.code_verifier:
            data["code_verifier"] = self.code_verifier

        # In a real implementation, this would make an HTTP POST request
        # to the token endpoint with the data
        # For now, return a placeholder response
        return {
            "access_token": "placeholder_access_token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "placeholder_refresh_token",
            "scope": self.config.scope,
        }

    def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            New token response dictionary
        """
        data = {
            "grant_type": "refresh_token",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "refresh_token": refresh_token,
        }

        # In a real implementation, this would make an HTTP POST request
        # to the token endpoint with the data
        # For now, return a placeholder response
        return {
            "access_token": "new_placeholder_access_token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "new_placeholder_refresh_token",
            "scope": self.config.scope,
        }


class TokenValidator:
    """Token validation utilities."""

    @staticmethod
    def validate_access_token(token: str) -> bool:
        """
        Validate access token format and structure.

        Args:
            token: Access token to validate

        Returns:
            True if token appears valid, False otherwise
        """
        if not token or not isinstance(token, str):
            return False

        # Basic JWT format validation (three parts separated by dots)
        parts = token.split(".")
        if len(parts) != 3:
            return False

        # Check that parts are base64-encoded
        try:
            for part in parts:
                base64.urlsafe_b64decode(part + "=" * (4 - len(part) % 4))
        except Exception:
            return False

        return True

    @staticmethod
    def extract_token_claims(token: str) -> dict[str, Any]:
        """
        Extract claims from JWT token.

        Args:
            token: JWT token

        Returns:
            Token claims dictionary

        Raises:
            TokenValidationError: If token is invalid
        """
        if not TokenValidator.validate_access_token(token):
            raise TokenValidationError("Invalid token format")

        try:
            # Extract payload (second part)
            parts = token.split(".")
            payload = parts[1]

            # Add padding if needed
            payload += "=" * (4 - len(payload) % 4)

            # Decode and parse JSON
            import json

            decoded = base64.urlsafe_b64decode(payload)
            claims = json.loads(decoded.decode("utf-8"))

            return claims
        except Exception as e:
            raise TokenValidationError(f"Failed to extract token claims: {e!s}")

    @staticmethod
    def is_token_expired(token: str) -> bool:
        """
        Check if token is expired.

        Args:
            token: JWT token

        Returns:
            True if expired, False otherwise
        """
        try:
            claims = TokenValidator.extract_token_claims(token)
            exp = claims.get("exp")

            if not exp:
                return True  # No expiration claim, consider expired

            import time

            current_time = int(time.time())
            return current_time >= exp

        except TokenValidationError:
            return True  # Invalid token, consider expired


class OIDCClient(OAuthClient):
    """OpenID Connect client implementation."""

    def __init__(self, config: OAuthConfig, issuer: str):
        """
        Initialize OIDC client.

        Args:
            config: OAuth configuration
            issuer: OIDC issuer URL
        """
        super().__init__(config)
        self.issuer = issuer
        self.userinfo_endpoint = None
        self.jwks_endpoint = None

    def discover_endpoints(self) -> dict[str, str]:
        """
        Discover OIDC endpoints from issuer.

        Returns:
            Dictionary of discovered endpoints
        """
        # In a real implementation, this would fetch the .well-known/openid_configuration
        # endpoint from the issuer to discover available endpoints
        # For now, return placeholder endpoints
        return {
            "authorization_endpoint": f"{self.issuer}/oauth/authorize",
            "token_endpoint": f"{self.issuer}/oauth/token",
            "userinfo_endpoint": f"{self.issuer}/oauth/userinfo",
            "jwks_endpoint": f"{self.issuer}/oauth/jwks",
            "end_session_endpoint": f"{self.issuer}/oauth/logout",
        }

    def get_user_info(self, access_token: str) -> dict[str, Any]:
        """
        Get user information using access token.

        Args:
            access_token: Valid access token

        Returns:
            User information dictionary
        """
        # In a real implementation, this would make an HTTP GET request
        # to the userinfo endpoint with the access token
        # For now, return placeholder user info
        return {
            "sub": "user123",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "email_verified": True,
            "picture": "https://example.com/avatar.jpg",
        }
