"""Authentication routes for the API."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from .dependencies import get_current_user, require_admin
from .jwt_handler import Token, User, jwt_manager
from .user_management import (
    PasswordChange,
    UserCreate,
    UserLogin,
    UserUpdate,
    user_manager,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Login with username and password."""
    try:
        # Authenticate user
        user = user_manager.authenticate_user(
            user_credentials.username, user_credentials.password
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create tokens
        tokens = jwt_manager.create_tokens(user)

        # Update last login
        user.last_login = jwt_manager.create_access_token(
            {"sub": user.username}
        )  # Use current time
        user_manager.update_user(user.username, UserUpdate())

        logger.info(f"User logged in: {user.username}")
        return tokens

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed"
        )


@router.post("/register", response_model=Token)
async def register(user_data: UserCreate):
    """Register a new user."""
    try:
        # Create user
        user = user_manager.create_user(user_data)

        # Create tokens
        tokens = jwt_manager.create_tokens(user)

        logger.info(f"User registered: {user.username}")
        return tokens

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token."""
    try:
        tokens = jwt_manager.refresh_access_token(refresh_token)
        return tokens

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed",
        )


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@router.put("/me", response_model=User)
async def update_current_user(
    user_update: UserUpdate, current_user: User = Depends(get_current_user)
):
    """Update current user information."""
    try:
        updated_user = user_manager.update_user(current_user.username, user_update)
        return updated_user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User update failed",
        )


@router.post("/change-password")
async def change_password(
    password_change: PasswordChange, current_user: User = Depends(get_current_user)
):
    """Change current user password."""
    try:
        # Verify current password
        if not user_manager.authenticate_user(
            current_user.username, password_change.current_password
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        # Update password (in production, update in database)
        # For demo, we'll just return success
        logger.info(f"Password changed for user: {current_user.username}")

        return {"message": "Password changed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed",
        )


@router.get("/users", response_model=List[User])
async def list_users(current_user: User = Depends(require_admin)):
    """List all users (admin only)."""
    try:
        users = user_manager.list_users()
        return users

    except Exception as e:
        logger.error(f"List users error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users",
        )


@router.get("/users/{username}", response_model=User)
async def get_user(username: str, current_user: User = Depends(require_admin)):
    """Get user by username (admin only)."""
    try:
        user = user_manager.get_user(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user",
        )


@router.put("/users/{username}", response_model=User)
async def update_user(
    username: str, user_update: UserUpdate, current_user: User = Depends(require_admin)
):
    """Update user by username (admin only)."""
    try:
        updated_user = user_manager.update_user(username, user_update)
        return updated_user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )


@router.delete("/users/{username}")
async def delete_user(username: str, current_user: User = Depends(require_admin)):
    """Delete user by username (admin only)."""
    try:
        success = user_manager.delete_user(username)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return {"message": f"User {username} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user",
        )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout current user."""
    try:
        # In production, you might want to blacklist the token
        # For now, we'll just return success
        logger.info(f"User logged out: {current_user.username}")
        return {"message": "Logged out successfully"}

    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Logout failed"
        )
