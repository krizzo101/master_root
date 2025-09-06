#!/usr/bin/env python3
"""
Workspace Manager - Create, manage, and share collaborative workspaces

This module provides the WorkspaceManager class which handles:
- Workspace creation and initialization
- Access control and permissions
- Workspace sharing and collaboration
- Template management and workspace types
"""

import asyncio
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .change_tracker import ChangeTracker


@dataclass
class WorkspaceConfig:
    """Configuration for a collaborative workspace"""

    workspace_id: str
    name: str
    workspace_type: str  # project, research, problem_solving, knowledge
    owner_id: str
    created_at: datetime = field(default_factory=datetime.now)
    description: str = ""
    template: Optional[str] = None
    max_collaborators: int = 50
    auto_sync: bool = True
    version_control: bool = True
    access_control: str = "open"  # open, restricted, private


@dataclass
class WorkspacePermissions:
    """Permissions for workspace access"""

    workspace_id: str
    user_id: str
    role: str  # owner, admin, editor, viewer
    granted_at: datetime = field(default_factory=datetime.now)
    granted_by: str = ""
    permissions: Set[str] = field(default_factory=lambda: {"read"})


class WorkspaceManager:
    """
    Manages collaborative workspaces for agent collaboration

    Provides workspace lifecycle management, access control,
    and coordination between multiple collaborating agents.
    """

    def __init__(self, base_path: Path, change_tracker: Optional[ChangeTracker] = None):
        self.base_path = Path(base_path)
        self.workspaces_path = self.base_path / "workspaces"
        self.templates_path = self.base_path / "templates"
        self.config_path = self.base_path / "workspace_configs"

        # Ensure directories exist
        self.workspaces_path.mkdir(parents=True, exist_ok=True)
        self.templates_path.mkdir(parents=True, exist_ok=True)
        self.config_path.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.change_tracker = change_tracker or ChangeTracker(
            self.base_path / "changes"
        )

        # Workspace registry
        self.active_workspaces: Dict[str, WorkspaceConfig] = {}
        self.workspace_permissions: Dict[str, Dict[str, WorkspacePermissions]] = {}
        self.lock = asyncio.Lock()

        # Load existing workspaces
        self._load_workspaces()

    def _load_workspaces(self):
        """Load existing workspace configurations"""
        for config_file in self.config_path.glob("*.json"):
            try:
                config_data = json.loads(config_file.read_text())
                config = WorkspaceConfig(**config_data)
                self.active_workspaces[config.workspace_id] = config

                # Load permissions
                perm_file = self.config_path / f"{config.workspace_id}_permissions.json"
                if perm_file.exists():
                    perm_data = json.loads(perm_file.read_text())
                    self.workspace_permissions[config.workspace_id] = {
                        user_id: WorkspacePermissions(**perm)
                        for user_id, perm in perm_data.items()
                    }
            except Exception as e:
                print(f"Failed to load workspace config {config_file}: {e}")

    async def create_workspace(
        self,
        name: str,
        workspace_type: str,
        owner_id: str,
        description: str = "",
        template: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a new collaborative workspace

        Args:
            name: Workspace name
            workspace_type: Type (project, research, problem_solving, knowledge)
            owner_id: ID of the workspace owner
            description: Optional description
            template: Optional template to use
            config: Additional configuration options

        Returns:
            str: Workspace ID
        """
        async with self.lock:
            workspace_id = str(uuid.uuid4())

            # Create workspace config
            workspace_config = WorkspaceConfig(
                workspace_id=workspace_id,
                name=name,
                workspace_type=workspace_type,
                owner_id=owner_id,
                description=description,
                template=template,
                **(config or {}),
            )

            # Create workspace directory
            workspace_dir = self.workspaces_path / workspace_id
            workspace_dir.mkdir(parents=True, exist_ok=True)

            # Initialize workspace structure
            await self._initialize_workspace_structure(
                workspace_dir, workspace_type, template
            )

            # Set up permissions
            owner_permissions = WorkspacePermissions(
                workspace_id=workspace_id,
                user_id=owner_id,
                role="owner",
                granted_by="system",
                permissions={"read", "write", "admin", "share", "delete"},
            )

            # Store configuration and permissions
            self.active_workspaces[workspace_id] = workspace_config
            self.workspace_permissions[workspace_id] = {owner_id: owner_permissions}

            # Persist to disk
            await self._save_workspace_config(workspace_config)
            await self._save_workspace_permissions(workspace_id)

            # Track workspace creation
            await self.change_tracker.track_workspace_event(
                workspace_id, "created", {"name": name, "type": workspace_type}
            )

            return workspace_id

    async def _initialize_workspace_structure(
        self, workspace_dir: Path, workspace_type: str, template: Optional[str] = None
    ):
        """Initialize the directory structure for a workspace"""
        # Common structure for all workspaces
        (workspace_dir / "shared_files").mkdir(exist_ok=True)
        (workspace_dir / "notebooks").mkdir(exist_ok=True)
        (workspace_dir / "artifacts").mkdir(exist_ok=True)
        (workspace_dir / "communication").mkdir(exist_ok=True)
        (workspace_dir / "temp").mkdir(exist_ok=True)

        # Type-specific initialization
        if workspace_type == "project":
            (workspace_dir / "code").mkdir(exist_ok=True)
            (workspace_dir / "documentation").mkdir(exist_ok=True)
            (workspace_dir / "tests").mkdir(exist_ok=True)

        elif workspace_type == "research":
            (workspace_dir / "papers").mkdir(exist_ok=True)
            (workspace_dir / "data").mkdir(exist_ok=True)
            (workspace_dir / "analysis").mkdir(exist_ok=True)

        elif workspace_type == "problem_solving":
            (workspace_dir / "problem_definition").mkdir(exist_ok=True)
            (workspace_dir / "solutions").mkdir(exist_ok=True)
            (workspace_dir / "brainstorming").mkdir(exist_ok=True)

        elif workspace_type == "knowledge":
            (workspace_dir / "knowledge_base").mkdir(exist_ok=True)
            (workspace_dir / "concepts").mkdir(exist_ok=True)
            (workspace_dir / "references").mkdir(exist_ok=True)

        # Apply template if specified
        if template:
            await self._apply_template(workspace_dir, template)

        # Create README file
        readme_content = f"""# {workspace_type.title()} Workspace

This is a collaborative workspace for {workspace_type} work.

## Structure
- `shared_files/` - Shared files accessible to all collaborators
- `notebooks/` - Collaborative notebooks and analysis
- `artifacts/` - Generated artifacts and outputs
- `communication/` - Communication logs and messages
- `temp/` - Temporary files and scratch space

Created: {datetime.now().isoformat()}
"""
        (workspace_dir / "README.md").write_text(readme_content)

    async def _apply_template(self, workspace_dir: Path, template: str):
        """Apply a workspace template"""
        template_dir = self.templates_path / template
        if template_dir.exists():
            # Copy template files
            import shutil

            for item in template_dir.iterdir():
                dest = workspace_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)

    async def share_workspace(
        self,
        workspace_id: str,
        user_id: str,
        target_user_id: str,
        role: str = "editor",
        permissions: Optional[Set[str]] = None,
    ) -> bool:
        """
        Share workspace with another user

        Args:
            workspace_id: Workspace to share
            user_id: User sharing the workspace
            target_user_id: User to share with
            role: Role to assign (viewer, editor, admin)
            permissions: Custom permission set

        Returns:
            bool: Success status
        """
        async with self.lock:
            # Check if workspace exists
            if workspace_id not in self.active_workspaces:
                return False

            # Check if user has sharing permissions
            if not await self._can_share_workspace(workspace_id, user_id):
                return False

            # Define default permissions for roles
            role_permissions = {
                "viewer": {"read"},
                "editor": {"read", "write"},
                "admin": {"read", "write", "admin", "share"},
            }

            # Create permissions
            user_permissions = WorkspacePermissions(
                workspace_id=workspace_id,
                user_id=target_user_id,
                role=role,
                granted_by=user_id,
                permissions=permissions or role_permissions.get(role, {"read"}),
            )

            # Add to workspace permissions
            if workspace_id not in self.workspace_permissions:
                self.workspace_permissions[workspace_id] = {}

            self.workspace_permissions[workspace_id][target_user_id] = user_permissions

            # Save permissions
            await self._save_workspace_permissions(workspace_id)

            # Track sharing event
            await self.change_tracker.track_workspace_event(
                workspace_id,
                "shared",
                {"shared_with": target_user_id, "role": role, "shared_by": user_id},
            )

            return True

    async def get_workspace(self, workspace_id: str) -> Optional[WorkspaceConfig]:
        """Get workspace configuration"""
        return self.active_workspaces.get(workspace_id)

    async def get_workspace_path(self, workspace_id: str) -> Optional[Path]:
        """Get the filesystem path for a workspace"""
        if workspace_id in self.active_workspaces:
            return self.workspaces_path / workspace_id
        return None

    async def list_workspaces(self, user_id: str) -> List[WorkspaceConfig]:
        """List all workspaces accessible to a user"""
        accessible_workspaces = []

        for workspace_id, config in self.active_workspaces.items():
            if await self._can_access_workspace(workspace_id, user_id):
                accessible_workspaces.append(config)

        return accessible_workspaces

    async def get_collaborators(self, workspace_id: str) -> List[WorkspacePermissions]:
        """Get all collaborators for a workspace"""
        if workspace_id in self.workspace_permissions:
            return list(self.workspace_permissions[workspace_id].values())
        return []

    async def _can_access_workspace(self, workspace_id: str, user_id: str) -> bool:
        """Check if user can access workspace"""
        workspace = self.active_workspaces.get(workspace_id)
        if not workspace:
            return False

        # Owner always has access
        if workspace.owner_id == user_id:
            return True

        # Check explicit permissions
        perms = self.workspace_permissions.get(workspace_id, {})
        return user_id in perms

    async def _can_share_workspace(self, workspace_id: str, user_id: str) -> bool:
        """Check if user can share workspace"""
        workspace = self.active_workspaces.get(workspace_id)
        if not workspace:
            return False

        # Owner can always share
        if workspace.owner_id == user_id:
            return True

        # Check if user has share permission
        perms = self.workspace_permissions.get(workspace_id, {}).get(user_id)
        return perms and "share" in perms.permissions

    async def _save_workspace_config(self, config: WorkspaceConfig):
        """Save workspace configuration to disk"""
        config_file = self.config_path / f"{config.workspace_id}.json"

        # Convert config to dict, handling datetime serialization
        config_dict = asdict(config)
        config_dict["created_at"] = config.created_at.isoformat()

        config_file.write_text(json.dumps(config_dict, indent=2))

    async def _save_workspace_permissions(self, workspace_id: str):
        """Save workspace permissions to disk"""
        if workspace_id not in self.workspace_permissions:
            return

        perm_file = self.config_path / f"{workspace_id}_permissions.json"

        # Convert permissions to dict
        perms_dict = {}
        for user_id, perm in self.workspace_permissions[workspace_id].items():
            perm_dict = asdict(perm)
            perm_dict["granted_at"] = perm.granted_at.isoformat()
            perm_dict["permissions"] = list(perm.permissions)
            perms_dict[user_id] = perm_dict

        perm_file.write_text(json.dumps(perms_dict, indent=2))

    async def cleanup_workspace(self, workspace_id: str, user_id: str) -> bool:
        """Clean up and delete a workspace"""
        async with self.lock:
            workspace = self.active_workspaces.get(workspace_id)
            if not workspace or workspace.owner_id != user_id:
                return False

            # Remove workspace directory
            import shutil

            workspace_dir = self.workspaces_path / workspace_id
            if workspace_dir.exists():
                shutil.rmtree(workspace_dir)

            # Remove configuration files
            config_file = self.config_path / f"{workspace_id}.json"
            perm_file = self.config_path / f"{workspace_id}_permissions.json"

            config_file.unlink(missing_ok=True)
            perm_file.unlink(missing_ok=True)

            # Remove from memory
            del self.active_workspaces[workspace_id]
            self.workspace_permissions.pop(workspace_id, None)

            # Track deletion
            await self.change_tracker.track_workspace_event(
                workspace_id, "deleted", {"deleted_by": user_id}
            )

            return True
