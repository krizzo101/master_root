"""User management for authentication."""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import uuid4

import bcrypt
from fastapi import HTTPException, status
from pydantic import BaseModel, Field, EmailStr

from .jwt_handler import User

logger = logging.getLogger(__name__)


class UserCreate(BaseModel):
    """User creation model."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)


class UserUpdate(BaseModel):
    """User update model."""

    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    roles: Optional[List[str]] = None
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None


class UserLogin(BaseModel):
    """User login model."""

    username: str
    password: str


class PasswordChange(BaseModel):
    """Password change model."""

    current_password: str
    new_password: str = Field(..., min_length=8)


class UserManager:
    """User management system."""

    def __init__(self):
        """Initialize user manager."""
        # In-memory user storage (replace with database in production)
        self.users: Dict[str, User] = {}
        self._create_default_users()

    def _create_default_users(self):
        """Create default users for development."""
        # Create admin user
        admin_user = User(
            id=str(uuid4()),
            username="admin",
            email="admin@autoforge.com",
            roles=["admin"],
            permissions=["read", "write", "delete", "admin"],
            is_active=True,
        )
        self.users[admin_user.username] = admin_user

        # Create developer user
        dev_user = User(
            id=str(uuid4()),
            username="developer",
            email="dev@autoforge.com",
            roles=["developer"],
            permissions=["read", "write"],
            is_active=True,
        )
        self.users[dev_user.username] = dev_user

        # Create viewer user
        viewer_user = User(
            id=str(uuid4()),
            username="viewer",
            email="viewer@autoforge.com",
            roles=["viewer"],
            permissions=["read"],
            is_active=True,
        )
        self.users[viewer_user.username] = viewer_user

        logger.info("Created default users: admin, developer, viewer")

    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        # Check if username already exists
        if user_data.username in self.users:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )

        # Check if email already exists
        for user in self.users.values():
            if user.email == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered",
                )

        # Create new user
        user = User(
            id=str(uuid4()),
            username=user_data.username,
            email=user_data.email,
            roles=user_data.roles,
            permissions=user_data.permissions,
            is_active=True,
        )

        # Store password hash (in production, store in database)
        user.password_hash = self._hash_password(user_data.password)

        self.users[user.username] = user
        logger.info(f"Created user: {user.username}")

        return user

    def get_user(self, username: str) -> Optional[User]:
        """Get a user by username."""
        return self.users.get(username)

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        for user in self.users.values():
            if user.id == user_id:
                return user
        return None

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password."""
        user = self.get_user(username)
        if not user:
            return None

        if not user.is_active:
            return None

        # For demo purposes, use simple password check
        # In production, verify against stored hash
        if username == "admin" and password == "admin123":
            return user
        elif username == "developer" and password == "dev123":
            return user
        elif username == "viewer" and password == "view123":
            return user

        return None

    def update_user(self, username: str, user_data: UserUpdate) -> User:
        """Update a user."""
        user = self.get_user(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Update fields
        if user_data.username is not None:
            # Check if new username already exists
            if user_data.username != username and user_data.username in self.users:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists",
                )
            user.username = user_data.username

        if user_data.email is not None:
            # Check if new email already exists
            for existing_user in self.users.values():
                if (
                    existing_user.email == user_data.email
                    and existing_user.username != username
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already exists",
                    )
            user.email = user_data.email

        if user_data.roles is not None:
            user.roles = user_data.roles

        if user_data.permissions is not None:
            user.permissions = user_data.permissions

        if user_data.is_active is not None:
            user.is_active = user_data.is_active

        # Update the user in storage
        if user_data.username is not None and user_data.username != username:
            # Username changed, update storage key
            del self.users[username]
            self.users[user.username] = user

        logger.info(f"Updated user: {user.username}")
        return user

    def delete_user(self, username: str) -> bool:
        """Delete a user."""
        if username not in self.users:
            return False

        del self.users[username]
        logger.info(f"Deleted user: {username}")
        return True

    def list_users(self) -> List[User]:
        """List all users."""
        return list(self.users.values())

    def has_permission(self, user: User, permission: str) -> bool:
        """Check if user has a specific permission."""
        return permission in user.permissions

    def has_role(self, user: User, role: str) -> bool:
        """Check if user has a specific role."""
        return role in user.roles

    def has_any_role(self, user: User, roles: List[str]) -> bool:
        """Check if user has any of the specified roles."""
        return any(role in user.roles for role in roles)

    def has_any_permission(self, user: User, permissions: List[str]) -> bool:
        """Check if user has any of the specified permissions."""
        return any(permission in user.permissions for permission in permissions)


# Global user manager instance
user_manager = UserManager()
