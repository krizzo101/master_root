#!/usr/bin/env python3
"""
Workspace SDK - Easy integration for agents

This module provides the WorkspaceSDK class which offers:
- Simple API for agents to use collaborative workspaces
- High-level abstractions for common collaboration patterns
- Integration with existing agent frameworks
- Automatic synchronization and conflict resolution
"""

import asyncio
import json
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

import websockets

from .change_tracker import ChangeTracker
from .collaborative_filesystem import CollaborativeFileSystem
from .sync_engine import SyncEngine
from .workspace_manager import WorkspaceConfig, WorkspaceManager


@dataclass
class CollaborationConfig:
    """Configuration for collaboration features"""

    enable_real_time_sync: bool = True
    enable_version_control: bool = True
    enable_conflict_resolution: bool = True
    sync_server_host: str = "localhost"
    sync_server_port: int = 8765
    auto_commit_interval: int = 300  # seconds
    max_file_size: int = 10 * 1024 * 1024  # 10MB


class WorkspaceSDK:
    """
    High-level SDK for collaborative workspace operations

    Provides simple APIs for agents to collaborate on shared workspaces
    with automatic synchronization, conflict resolution, and version control.
    """

    def __init__(
        self,
        agent_id: str,
        base_path: Path,
        config: Optional[CollaborationConfig] = None,
    ):
        self.agent_id = agent_id
        self.base_path = Path(base_path)
        self.config = config or CollaborationConfig()

        # Initialize core components
        self.workspace_manager = WorkspaceManager(self.base_path)
        self.change_tracker = ChangeTracker(self.base_path / "tracking")

        # Current workspace context
        self.current_workspace_id: Optional[str] = None
        self.current_filesystem: Optional[CollaborativeFileSystem] = None

        # WebSocket connection to sync server
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.sync_task: Optional[asyncio.Task] = None

        # Event callbacks
        self.event_callbacks: Dict[str, List[Callable]] = {}

        # Auto-commit task
        self.auto_commit_task: Optional[asyncio.Task] = None

    async def connect_to_sync_server(self) -> bool:
        """Connect to the synchronization server"""
        try:
            uri = f"ws://{self.config.sync_server_host}:{self.config.sync_server_port}"
            self.websocket = await websockets.connect(uri)

            # Identify ourselves
            await self.websocket.send(
                json.dumps({"type": "identify", "agent_id": self.agent_id})
            )

            # Start sync task
            self.sync_task = asyncio.create_task(self._handle_sync_messages())

            return True

        except Exception as e:
            print(f"Failed to connect to sync server: {e}")
            return False

    async def disconnect_from_sync_server(self):
        """Disconnect from the synchronization server"""
        if self.sync_task:
            self.sync_task.cancel()
            try:
                await self.sync_task
            except asyncio.CancelledError:
                pass

        if self.websocket:
            await self.websocket.close()
            self.websocket = None

    async def _handle_sync_messages(self):
        """Handle messages from sync server"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self._process_sync_message(data)
                except json.JSONDecodeError:
                    print("Received invalid JSON from sync server")
                except Exception as e:
                    print(f"Error processing sync message: {e}")

        except websockets.exceptions.ConnectionClosed:
            print("Sync server connection closed")
        except Exception as e:
            print(f"Sync message handler error: {e}")

    async def _process_sync_message(self, data: Dict[str, Any]):
        """Process a sync message from the server"""
        message_type = data.get("type")

        if message_type == "sync_event":
            event = data.get("event", {})
            event_type = event.get("event_type")

            # Call registered callbacks
            callbacks = self.event_callbacks.get(event_type, [])
            for callback in callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    print(f"Error in event callback: {e}")

        elif message_type == "identified":
            print(f"Connected to sync server as {self.agent_id}")

        elif message_type == "error":
            print(f"Sync server error: {data.get('message')}")

    # Workspace Management
    async def create_workspace(
        self,
        name: str,
        workspace_type: str = "project",
        description: str = "",
        template: Optional[str] = None,
    ) -> str:
        """Create a new collaborative workspace"""
        workspace_id = await self.workspace_manager.create_workspace(
            name=name,
            workspace_type=workspace_type,
            owner_id=self.agent_id,
            description=description,
            template=template,
        )

        return workspace_id

    async def join_workspace(self, workspace_id: str) -> bool:
        """Join an existing workspace"""
        workspace = await self.workspace_manager.get_workspace(workspace_id)
        if not workspace:
            return False

        # Set current workspace
        self.current_workspace_id = workspace_id
        workspace_path = await self.workspace_manager.get_workspace_path(workspace_id)

        if workspace_path:
            self.current_filesystem = CollaborativeFileSystem(
                workspace_path, self.change_tracker
            )

        # Subscribe to workspace events if sync is enabled
        if self.config.enable_real_time_sync and self.websocket:
            await self.websocket.send(
                json.dumps(
                    {"type": "subscribe_workspace", "workspace_id": workspace_id}
                )
            )

        # Start auto-commit task
        if self.config.auto_commit_interval > 0:
            self.auto_commit_task = asyncio.create_task(
                self._auto_commit_task(workspace_id)
            )

        return True

    async def leave_workspace(self):
        """Leave the current workspace"""
        if not self.current_workspace_id:
            return

        # Commit any pending changes
        await self.commit_changes("Auto-commit before leaving workspace")

        # Unsubscribe from workspace events
        if self.config.enable_real_time_sync and self.websocket:
            await self.websocket.send(
                json.dumps(
                    {
                        "type": "unsubscribe_workspace",
                        "workspace_id": self.current_workspace_id,
                    }
                )
            )

        # Stop auto-commit task
        if self.auto_commit_task:
            self.auto_commit_task.cancel()
            try:
                await self.auto_commit_task
            except asyncio.CancelledError:
                pass

        self.current_workspace_id = None
        self.current_filesystem = None

    async def list_my_workspaces(self) -> List[WorkspaceConfig]:
        """List all workspaces accessible to this agent"""
        return await self.workspace_manager.list_workspaces(self.agent_id)

    # File Operations
    @asynccontextmanager
    async def edit_file(self, file_path: str) -> AsyncGenerator[str, None]:
        """Context manager for editing files with automatic locking"""
        if not self.current_filesystem:
            raise ValueError("No workspace joined")

        # Acquire lock
        if not await self.current_filesystem.acquire_lock(
            file_path, self.agent_id, "write", operation="edit"
        ):
            raise ValueError("Could not acquire file lock")

        try:
            # Read current content
            result = await self.current_filesystem.read_file(file_path, self.agent_id)
            current_content = result[0] if result else ""
            current_version = result[1] if result else 0

            # Yield content for editing
            yield current_content

            # Content should be modified by the user of this context manager
            # We'll detect changes and save them

        finally:
            # Release lock
            await self.current_filesystem.release_lock(file_path, self.agent_id)

    async def read_file(self, file_path: str) -> Optional[str]:
        """Read a file from the current workspace"""
        if not self.current_filesystem:
            raise ValueError("No workspace joined")

        result = await self.current_filesystem.read_file(file_path, self.agent_id)
        return result[0] if result else None

    async def write_file(
        self, file_path: str, content: str, changes_summary: str = ""
    ) -> bool:
        """Write content to a file in the current workspace"""
        if not self.current_filesystem:
            raise ValueError("No workspace joined")

        success, error = await self.current_filesystem.write_file(
            file_path, content, self.agent_id, changes_summary=changes_summary
        )

        # Notify sync server of file change
        if success and self.config.enable_real_time_sync and self.websocket:
            await self.websocket.send(
                json.dumps(
                    {
                        "type": "file_changed",
                        "workspace_id": self.current_workspace_id,
                        "file_path": file_path,
                        "change_type": "modified",
                        "metadata": {"changes_summary": changes_summary},
                    }
                )
            )

        if not success:
            print(f"Failed to write file {file_path}: {error}")

        return success

    async def append_to_file(self, file_path: str, content: str) -> bool:
        """Append content to a file in the current workspace"""
        if not self.current_filesystem:
            raise ValueError("No workspace joined")

        success, error = await self.current_filesystem.append_to_file(
            file_path, content, self.agent_id
        )

        # Notify sync server
        if success and self.config.enable_real_time_sync and self.websocket:
            await self.websocket.send(
                json.dumps(
                    {
                        "type": "file_changed",
                        "workspace_id": self.current_workspace_id,
                        "file_path": file_path,
                        "change_type": "appended",
                        "metadata": {"appended_by": self.agent_id},
                    }
                )
            )

        return success

    async def list_files(self, directory_path: str = "") -> List[Dict[str, Any]]:
        """List files in the current workspace"""
        if not self.current_filesystem:
            raise ValueError("No workspace joined")

        return await self.current_filesystem.list_files(directory_path)

    async def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get information about a file"""
        if not self.current_filesystem:
            raise ValueError("No workspace joined")

        return await self.current_filesystem.get_file_info(file_path)

    # Collaboration Features
    async def get_collaborators(self) -> List[Dict[str, Any]]:
        """Get list of current collaborators in the workspace"""
        if not self.current_workspace_id:
            return []

        permissions = await self.workspace_manager.get_collaborators(
            self.current_workspace_id
        )

        # Enhance with real-time connection status if available
        collaborators = []
        for perm in permissions:
            collab_info = {
                "agent_id": perm.user_id,
                "role": perm.role,
                "permissions": list(perm.permissions),
                "joined_at": perm.granted_at.isoformat(),
                "online": False,  # Default to offline
            }
            collaborators.append(collab_info)

        return collaborators

    async def send_message_to_collaborator(
        self, target_agent_id: str, message: str, message_type: str = "text"
    ):
        """Send a message to another collaborator"""
        if not self.current_workspace_id:
            raise ValueError("No workspace joined")

        # Create message file in communication directory
        comm_dir = (
            Path(
                await self.workspace_manager.get_workspace_path(
                    self.current_workspace_id
                )
            )
            / "communication"
        )
        comm_dir.mkdir(exist_ok=True)

        message_data = {
            "from": self.agent_id,
            "to": target_agent_id,
            "type": message_type,
            "content": message,
            "timestamp": datetime.now().isoformat(),
            "workspace_id": self.current_workspace_id,
        }

        message_file = (
            comm_dir
            / f"msg_{int(datetime.now().timestamp())}_{self.agent_id}_to_{target_agent_id}.json"
        )
        message_file.write_text(json.dumps(message_data, indent=2))

        # Notify via sync server
        if self.config.enable_real_time_sync and self.websocket:
            await self.websocket.send(
                json.dumps(
                    {
                        "type": "message_sent",
                        "workspace_id": self.current_workspace_id,
                        "target_agent": target_agent_id,
                        "message": message_data,
                    }
                )
            )

    async def get_messages(self) -> List[Dict[str, Any]]:
        """Get messages addressed to this agent"""
        if not self.current_workspace_id:
            return []

        comm_dir = (
            Path(
                await self.workspace_manager.get_workspace_path(
                    self.current_workspace_id
                )
            )
            / "communication"
        )

        if not comm_dir.exists():
            return []

        messages = []
        for msg_file in comm_dir.glob(f"*_to_{self.agent_id}.json"):
            try:
                message_data = json.loads(msg_file.read_text())
                messages.append(message_data)
            except Exception as e:
                print(f"Failed to read message {msg_file}: {e}")

        # Sort by timestamp
        messages.sort(key=lambda m: m.get("timestamp", ""))
        return messages

    # Version Control
    async def commit_changes(self, message: str) -> str:
        """Commit current changes to version control"""
        if not self.current_workspace_id:
            raise ValueError("No workspace joined")

        commit_id = await self.change_tracker.commit_changes(
            self.agent_id, message, self.current_workspace_id
        )

        return commit_id

    async def get_change_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get change history for the current workspace"""
        if not self.current_workspace_id:
            return []

        commits = await self.change_tracker.get_commit_history(
            workspace_id=self.current_workspace_id, limit=limit
        )

        # Convert to dictionaries for easier use
        history = []
        for commit in commits:
            commit_dict = {
                "commit_id": commit.commit_id,
                "agent_id": commit.agent_id,
                "message": commit.message,
                "timestamp": commit.timestamp.isoformat(),
                "changes_count": len(commit.changes),
                "changes": [
                    {
                        "event_type": change.event_type,
                        "resource_path": change.resource_path,
                        "timestamp": change.timestamp.isoformat(),
                    }
                    for change in commit.changes
                ],
            }
            history.append(commit_dict)

        return history

    async def create_snapshot(self, name: str, description: str = "") -> str:
        """Create a snapshot of the current workspace"""
        if not self.current_workspace_id:
            raise ValueError("No workspace joined")

        workspace_path = await self.workspace_manager.get_workspace_path(
            self.current_workspace_id
        )

        snapshot_id = await self.change_tracker.create_snapshot(
            workspace_path, name, self.agent_id, description
        )

        return snapshot_id

    # Event Handling
    def on_event(self, event_type: str, callback: Callable):
        """Register a callback for collaboration events"""
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        self.event_callbacks[event_type].append(callback)

    def off_event(self, event_type: str, callback: Callable):
        """Unregister an event callback"""
        if event_type in self.event_callbacks:
            try:
                self.event_callbacks[event_type].remove(callback)
            except ValueError:
                pass

    # Utility Methods
    async def get_workspace_stats(self) -> Dict[str, Any]:
        """Get statistics about the current workspace"""
        if not self.current_workspace_id:
            return {}

        workspace = await self.workspace_manager.get_workspace(
            self.current_workspace_id
        )
        files = await self.list_files()
        collaborators = await self.get_collaborators()
        history = await self.get_change_history(limit=100)

        return {
            "workspace_id": self.current_workspace_id,
            "name": workspace.name if workspace else "Unknown",
            "type": workspace.workspace_type if workspace else "Unknown",
            "total_files": len(files),
            "total_collaborators": len(collaborators),
            "total_commits": len(history),
            "created_at": workspace.created_at.isoformat() if workspace else None,
            "last_activity": history[0]["timestamp"] if history else None,
        }

    async def _auto_commit_task(self, workspace_id: str):
        """Background task for automatic commits"""
        try:
            while True:
                await asyncio.sleep(self.config.auto_commit_interval)

                # Check if there are pending changes
                if self.change_tracker.pending_changes:
                    await self.commit_changes(f"Auto-commit by {self.agent_id}")
        except asyncio.CancelledError:
            # Task was cancelled, do final commit
            if self.change_tracker.pending_changes:
                await self.commit_changes(f"Final auto-commit by {self.agent_id}")

    # Context Managers
    @asynccontextmanager
    async def workspace_session(self, workspace_id: str):
        """Context manager for workspace sessions"""
        success = await self.join_workspace(workspace_id)
        if not success:
            raise ValueError(f"Failed to join workspace {workspace_id}")

        try:
            yield self
        finally:
            await self.leave_workspace()

    @asynccontextmanager
    async def sync_session(self):
        """Context manager for sync server connection"""
        connected = await self.connect_to_sync_server()
        if not connected:
            raise ValueError("Failed to connect to sync server")

        try:
            yield self
        finally:
            await self.disconnect_from_sync_server()

    # Cleanup
    async def cleanup(self):
        """Clean up resources"""
        await self.leave_workspace()
        await self.disconnect_from_sync_server()
