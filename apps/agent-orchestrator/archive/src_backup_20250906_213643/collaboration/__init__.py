"""
Collaborative Workspace System

A comprehensive framework for enabling real-time collaboration between AI agents.
Provides shared workspaces, synchronized file systems, and collaborative editing capabilities.
"""

from .change_tracker import ChangeTracker
from .collaborative_filesystem import CollaborativeFileSystem
from .sync_engine import SyncEngine
from .workspace_manager import WorkspaceManager
from .workspace_sdk import WorkspaceSDK

__all__ = [
    "WorkspaceManager",
    "CollaborativeFileSystem",
    "ChangeTracker",
    "SyncEngine",
    "WorkspaceSDK",
]

__version__ = "1.0.0"
