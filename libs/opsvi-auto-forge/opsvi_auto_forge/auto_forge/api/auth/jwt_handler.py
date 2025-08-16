"""JWT authentication handler for the API."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from uuid import uuid4

import jwt
from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from opsvi_auto_forge.config.settings import settings

logger = logging.getLogger(__name__)


class TokenData(BaseModel):
    """Token data model."""

    username: Optional[str] = None
    user_id: Optional[str] = None
    roles: list = Field(default_factory=list)
    permissions: list = Field(default_factory=list)


class Token(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None


class User(BaseModel):
    """User model."""

    id: str
    username: str
    email: str
    roles: list = Field(default_factory=list)
    permissions: list = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None


class JWTManager:
    """JWT token manager."""

    def __init__(self):
        """Initialize JWT manager."""
        self.secret_key = settings.jwt_secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = settings.jwt_access_token_expire_minutes
        self.refresh_token_expire_days = settings.jwt_refresh_token_expire_days

    def create_access_token(
        self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create an access token."""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.access_token_expire_minutes
            )

        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(
        self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a refresh token."""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                days=self.refresh_token_expire_days
            )

        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> TokenData:
        """Verify and decode a token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            user_id: str = payload.get("user_id")
            roles: list = payload.get("roles", [])
            permissions: list = payload.get("permissions", [])

            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return TokenData(
                username=username, user_id=user_id, roles=roles, permissions=permissions
            )

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def create_tokens(self, user: User) -> Token:
        """Create access and refresh tokens for a user."""
        access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
        refresh_token_expires = timedelta(days=self.refresh_token_expire_days)

        access_token = self.create_access_token(
            data={
                "sub": user.username,
                "user_id": user.id,
                "roles": user.roles,
                "permissions": user.permissions,
            },
            expires_delta=access_token_expires,
        )

        refresh_token = self.create_refresh_token(
            data={"sub": user.username, "user_id": user.id},
            expires_delta=refresh_token_expires,
        )

        return Token(
            access_token=access_token,
            expires_in=self.access_token_expire_minutes * 60,
            refresh_token=refresh_token,
        )

    def refresh_access_token(self, refresh_token: str) -> Token:
        """Refresh an access token using a refresh token."""
        try:
            payload = jwt.decode(
                refresh_token, self.secret_key, algorithms=[self.algorithm]
            )
            username: str = payload.get("sub")
            user_id: str = payload.get("user_id")

            if username is None or payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Create new access token
            access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
            access_token = self.create_access_token(
                data={
                    "sub": username,
                    "user_id": user_id,
                    "roles": payload.get("roles", []),
                    "permissions": payload.get("permissions", []),
                },
                expires_delta=access_token_expires,
            )

            return Token(
                access_token=access_token,
                expires_in=self.access_token_expire_minutes * 60,
            )

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )


# Global JWT manager instance
jwt_manager = JWTManager()
