"""
Role-based access control (RBAC) system.

Provides comprehensive RBAC functionality including role management,
permission decorators, policy engine, and access control.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from enum import Enum

from opsvi_foundation.patterns import ComponentError


class PermissionError(ComponentError):
    """Raised when permission check fails."""


class RoleError(ComponentError):
    """Raised when role operation fails."""


class PermissionLevel(Enum):
    """Permission levels for access control."""

    NONE = 0
    READ = 1
    WRITE = 2
    ADMIN = 3
    OWNER = 4


class Permission:
    """Represents a permission with resource and action."""

    def __init__(
        self,
        resource: str,
        action: str,
        level: PermissionLevel = PermissionLevel.READ,
    ):
        """
        Initialize permission.

        Args:
            resource: Resource being accessed
            action: Action being performed
            level: Permission level
        """
        self.resource = resource
        self.action = action
        self.level = level

    def __str__(self) -> str:
        return f"{self.resource}:{self.action}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Permission):
            return False
        return (
            self.resource == other.resource
            and self.action == other.action
            and self.level == other.level
        )

    def __hash__(self) -> int:
        return hash((self.resource, self.action, self.level))


class Role:
    """Represents a role with associated permissions."""

    def __init__(self, name: str, description: str = ""):
        """
        Initialize role.

        Args:
            name: Role name
            description: Role description
        """
        self.name = name
        self.description = description
        self.permissions: set[Permission] = set()
        self.inherited_roles: set[str] = set()

    def add_permission(self, permission: Permission) -> None:
        """
        Add permission to role.

        Args:
            permission: Permission to add
        """
        self.permissions.add(permission)

    def remove_permission(self, permission: Permission) -> None:
        """
        Remove permission from role.

        Args:
            permission: Permission to remove
        """
        self.permissions.discard(permission)

    def has_permission(self, permission: Permission) -> bool:
        """
        Check if role has specific permission.

        Args:
            permission: Permission to check

        Returns:
            True if role has permission, False otherwise
        """
        return permission in self.permissions

    def inherit_from(self, role_name: str) -> None:
        """
        Inherit permissions from another role.

        Args:
            role_name: Name of role to inherit from
        """
        self.inherited_roles.add(role_name)


class User:
    """Represents a user with roles and permissions."""

    def __init__(self, user_id: str, username: str):
        """
        Initialize user.

        Args:
            user_id: Unique user identifier
            username: User's username
        """
        self.user_id = user_id
        self.username = username
        self.roles: set[str] = set()
        self.custom_permissions: set[Permission] = set()

    def add_role(self, role_name: str) -> None:
        """
        Add role to user.

        Args:
            role_name: Name of role to add
        """
        self.roles.add(role_name)

    def remove_role(self, role_name: str) -> None:
        """
        Remove role from user.

        Args:
            role_name: Name of role to remove
        """
        self.roles.discard(role_name)

    def add_custom_permission(self, permission: Permission) -> None:
        """
        Add custom permission to user.

        Args:
            permission: Permission to add
        """
        self.custom_permissions.add(permission)

    def remove_custom_permission(self, permission: Permission) -> None:
        """
        Remove custom permission from user.

        Args:
            permission: Permission to remove
        """
        self.custom_permissions.discard(permission)


class PolicyEngine:
    """Policy engine for evaluating access control policies."""

    def __init__(self):
        """Initialize policy engine."""
        self.roles: dict[str, Role] = {}
        self.users: dict[str, User] = {}
        self.policies: dict[str, Callable] = {}

    def add_role(self, role: Role) -> None:
        """
        Add role to policy engine.

        Args:
            role: Role to add
        """
        self.roles[role.name] = role

    def remove_role(self, role_name: str) -> None:
        """
        Remove role from policy engine.

        Args:
            role_name: Name of role to remove
        """
        if role_name in self.roles:
            del self.roles[role_name]
            # Remove role from all users
            for user in self.users.values():
                user.remove_role(role_name)

    def add_user(self, user: User) -> None:
        """
        Add user to policy engine.

        Args:
            user: User to add
        """
        self.users[user.user_id] = user

    def remove_user(self, user_id: str) -> None:
        """
        Remove user from policy engine.

        Args:
            user_id: ID of user to remove
        """
        if user_id in self.users:
            del self.users[user_id]

    def add_policy(self, name: str, policy_func: Callable) -> None:
        """
        Add custom policy function.

        Args:
            name: Policy name
            policy_func: Policy function to execute
        """
        self.policies[name] = policy_func

    def check_permission(
        self,
        user_id: str,
        resource: str,
        action: str,
        level: PermissionLevel = PermissionLevel.READ,
    ) -> bool:
        """
        Check if user has permission for resource and action.

        Args:
            user_id: User ID
            resource: Resource being accessed
            action: Action being performed
            level: Required permission level

        Returns:
            True if user has permission, False otherwise
        """
        if user_id not in self.users:
            return False

        user = self.users[user_id]
        permission = Permission(resource, action, level)

        # Check custom permissions first
        if permission in user.custom_permissions:
            return True

        # Check role-based permissions
        for role_name in user.roles:
            if role_name in self.roles:
                role = self.roles[role_name]
                if role.has_permission(permission):
                    return True

                # Check inherited roles
                for inherited_role_name in role.inherited_roles:
                    if inherited_role_name in self.roles:
                        inherited_role = self.roles[inherited_role_name]
                        if inherited_role.has_permission(permission):
                            return True

        return False

    def get_user_permissions(self, user_id: str) -> set[Permission]:
        """
        Get all permissions for a user.

        Args:
            user_id: User ID

        Returns:
            Set of user permissions
        """
        if user_id not in self.users:
            return set()

        user = self.users[user_id]
        permissions = user.custom_permissions.copy()

        # Add role-based permissions
        for role_name in user.roles:
            if role_name in self.roles:
                role = self.roles[role_name]
                permissions.update(role.permissions)

                # Add inherited role permissions
                for inherited_role_name in role.inherited_roles:
                    if inherited_role_name in self.roles:
                        inherited_role = self.roles[inherited_role_name]
                        permissions.update(inherited_role.permissions)

        return permissions


class RBACManager:
    """High-level RBAC manager for easy access control."""

    def __init__(self):
        """Initialize RBAC manager."""
        self.policy_engine = PolicyEngine()
        self._setup_default_roles()

    def _setup_default_roles(self) -> None:
        """Setup default roles and permissions."""
        # Admin role
        admin_role = Role("admin", "Administrator with full access")
        admin_role.add_permission(Permission("*", "*", PermissionLevel.ADMIN))
        self.policy_engine.add_role(admin_role)

        # User role
        user_role = Role("user", "Standard user")
        user_role.add_permission(Permission("profile", "read", PermissionLevel.READ))
        user_role.add_permission(Permission("profile", "update", PermissionLevel.WRITE))
        self.policy_engine.add_role(user_role)

        # Guest role
        guest_role = Role("guest", "Guest user with limited access")
        guest_role.add_permission(Permission("public", "read", PermissionLevel.READ))
        self.policy_engine.add_role(guest_role)

    def create_user(
        self,
        user_id: str,
        username: str,
        roles: list[str] | None = None,
    ) -> User:
        """
        Create a new user.

        Args:
            user_id: Unique user identifier
            username: User's username
            roles: List of role names to assign

        Returns:
            Created user
        """
        user = User(user_id, username)
        if roles:
            for role_name in roles:
                user.add_role(role_name)

        self.policy_engine.add_user(user)
        return user

    def assign_role(self, user_id: str, role_name: str) -> None:
        """
        Assign role to user.

        Args:
            user_id: User ID
            role_name: Role name to assign
        """
        if user_id in self.policy_engine.users:
            self.policy_engine.users[user_id].add_role(role_name)

    def revoke_role(self, user_id: str, role_name: str) -> None:
        """
        Revoke role from user.

        Args:
            user_id: User ID
            role_name: Role name to revoke
        """
        if user_id in self.policy_engine.users:
            self.policy_engine.users[user_id].remove_role(role_name)

    def has_permission(
        self,
        user_id: str,
        resource: str,
        action: str,
        level: PermissionLevel = PermissionLevel.READ,
    ) -> bool:
        """
        Check if user has permission.

        Args:
            user_id: User ID
            resource: Resource being accessed
            action: Action being performed
            level: Required permission level

        Returns:
            True if user has permission, False otherwise
        """
        return self.policy_engine.check_permission(user_id, resource, action, level)

    def require_permission(
        self,
        resource: str,
        action: str,
        level: PermissionLevel = PermissionLevel.READ,
    ):
        """
        Decorator to require permission for function execution.

        Args:
            resource: Resource being accessed
            action: Action being performed
            level: Required permission level
        """

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Extract user_id from first argument or kwargs
                user_id = None
                if args and hasattr(args[0], "user_id"):
                    user_id = args[0].user_id
                elif "user_id" in kwargs:
                    user_id = kwargs["user_id"]

                if not user_id:
                    raise PermissionError("User ID not found in function arguments")

                if not self.has_permission(user_id, resource, action, level):
                    raise PermissionError(
                        f"User {user_id} lacks permission for {resource}:{action}",
                    )

                return func(*args, **kwargs)

            return wrapper

        return decorator


# Global RBAC manager instance
rbac_manager = RBACManager()


def require_permission(
    resource: str,
    action: str,
    level: PermissionLevel = PermissionLevel.READ,
):
    """
    Convenience decorator for requiring permissions.

    Args:
        resource: Resource being accessed
        action: Action being performed
        level: Required permission level
    """
    return rbac_manager.require_permission(resource, action, level)
