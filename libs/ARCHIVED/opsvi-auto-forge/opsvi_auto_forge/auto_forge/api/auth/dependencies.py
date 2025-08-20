"""Authentication dependencies for FastAPI routes."""

import logging
from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .jwt_handler import User, jwt_manager
from .user_management import user_manager

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """Get the current authenticated user."""
    try:
        token_data = jwt_manager.verify_token(credentials.credentials)
        user = user_manager.get_user_by_id(token_data.user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


def require_permission(permission: str):
    """Dependency factory for requiring a specific permission."""

    def permission_dependency(current_user: User = Depends(get_current_user)) -> User:
        if not user_manager.has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required",
            )
        return current_user

    return permission_dependency


def require_any_permission(permissions: List[str]):
    """Dependency factory for requiring any of the specified permissions."""

    def permission_dependency(current_user: User = Depends(get_current_user)) -> User:
        if not user_manager.has_any_permission(current_user, permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of permissions {permissions} required",
            )
        return current_user

    return permission_dependency


def require_role(role: str):
    """Dependency factory for requiring a specific role."""

    def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        if not user_manager.has_role(current_user, role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"Role '{role}' required"
            )
        return current_user

    return role_dependency


def require_any_role(roles: List[str]):
    """Dependency factory for requiring any of the specified roles."""

    def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        if not user_manager.has_any_role(current_user, roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of roles {roles} required",
            )
        return current_user

    return role_dependency


# Common permission dependencies
require_admin = require_role("admin")
require_developer = require_role("developer")
require_viewer = require_role("viewer")

# Common permission dependencies
require_read = require_permission("read")
require_write = require_permission("write")
require_delete = require_permission("delete")
require_admin_permission = require_permission("admin")

# Combined role dependencies
require_admin_or_developer = require_any_role(["admin", "developer"])
require_admin_or_developer_or_viewer = require_any_role(
    ["admin", "developer", "viewer"]
)

# Combined permission dependencies
require_read_or_write = require_any_permission(["read", "write"])
require_write_or_admin = require_any_permission(["write", "admin"])
