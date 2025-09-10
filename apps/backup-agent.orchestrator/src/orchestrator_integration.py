"""
Orchestrator Integration Helper

Provides easy integration with the Enhanced Chat Monitor's orchestrator registry
for automatic run registration and agent tracking.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional


class OrchestratorIntegration:
    """
    Helper class for orchestrators to automatically register with chat monitor.

    Usage in GenericOrchestrator:
    ```python
    from orchestrator_integration import OrchestratorIntegration

    # In __init__
    self.chat_monitor_integration = OrchestratorIntegration(
        title="Research Analysis Swarm",
        orchestrator_session=self.session_id,
        focus_areas=["research", "analysis"]
    )

    # When spawning agents
    self.chat_monitor_integration.add_agent(
        agent_session_id=new_agent_session,
        role="research_specialist",
        location=worktree_path
    )

    # When complete
    self.chat_monitor_integration.complete_run("Task completed successfully")
    ```
    """

    def __init__(
        self,
        title: str,
        orchestrator_session: str,
        orchestrator_location: Optional[str] = None,
        worktrees: Optional[List[str]] = None,
        focus_areas: Optional[List[str]] = None,
        **metadata,
    ):
        """
        Initialize orchestrator integration.

        Args:
            title: Human-readable title for this run
            orchestrator_session: Session ID of the orchestrator
            orchestrator_location: Working directory (auto-detected if None)
            worktrees: List of worktree names being used
            focus_areas: List of focus areas for this run
            **metadata: Additional metadata for the run
        """
        self.title = title
        self.orchestrator_session = orchestrator_session
        self.orchestrator_location = orchestrator_location or str(Path.cwd())
        self.worktrees = worktrees or []
        self.focus_areas = focus_areas or []
        self.metadata = metadata
        self.run_id: Optional[str] = None
        self.registry = None

        # Try to register the run
        if self._register_run():
            # Auto-launch chat monitor window
            self._auto_launch_monitor()

    def _register_run(self) -> bool:
        """Register this orchestrator run."""
        try:
            # Import here to avoid hard dependency
            from orchestrator_registry import OrchestratorRegistry

            self.registry = OrchestratorRegistry()

            self.run_id = self.registry.register_run(
                title=self.title,
                orchestrator_session=self.orchestrator_session,
                orchestrator_location=self.orchestrator_location,
                worktrees=self.worktrees,
                focus_areas=self.focus_areas,
                **self.metadata,
            )

            print(f"🎯 Chat Monitor: Registered run '{self.title}' (ID: {self.run_id})")
            return True

        except ImportError:
            # Chat monitor not available - that's ok
            print(
                "💡 Chat Monitor integration not available (orchestrator_registry not found)"
            )
            return False
        except Exception as e:
            print(f"⚠️  Chat Monitor registration failed: {e}")
            return False

    def add_agent(
        self,
        agent_session_id: str,
        role: str = "agent",
        location: Optional[str] = None,
        **agent_metadata,
    ) -> bool:
        """
        Add an agent to this orchestrator run.

        Args:
            agent_session_id: Session ID of the spawned agent
            role: Role of the agent (e.g., "research_specialist")
            location: Working directory of the agent
            **agent_metadata: Additional agent metadata

        Returns:
            True if agent was added successfully
        """
        if not self.registry or not self.run_id:
            return False

        try:
            success = self.registry.add_agent(
                run_id=self.run_id,
                agent_session_id=agent_session_id,
                role=role,
                location=location or str(Path.cwd()),
                **agent_metadata,
            )

            if success:
                print(f"🤖 Chat Monitor: Added agent {role} ({agent_session_id[:8]})")

            return success

        except Exception as e:
            print(f"⚠️  Chat Monitor agent registration failed: {e}")
            return False

    def complete_run(self, completion_reason: str = "completed") -> bool:
        """
        Mark this orchestrator run as completed.

        Args:
            completion_reason: Reason for completion

        Returns:
            True if run was completed successfully
        """
        if not self.registry or not self.run_id:
            return False

        try:
            success = self.registry.complete_run(self.run_id, completion_reason)

            if success:
                print(
                    f"✅ Chat Monitor: Completed run '{self.title}' - {completion_reason}"
                )

            return success

        except Exception as e:
            print(f"⚠️  Chat Monitor completion failed: {e}")
            return False

    def update_metadata(self, **new_metadata) -> bool:
        """
        Update metadata for this run.

        Args:
            **new_metadata: New metadata to add/update

        Returns:
            True if metadata was updated successfully
        """
        if not self.registry or not self.run_id:
            return False

        try:
            run_details = self.registry.get_run_details(self.run_id)
            if run_details:
                run_details.metadata.update(new_metadata)
                self.registry._save_run(run_details)
                return True

        except Exception as e:
            print(f"⚠️  Chat Monitor metadata update failed: {e}")

        return False

    def get_run_details(self) -> Optional[Dict[str, Any]]:
        """
        Get current run details.

        Returns:
            Run details dictionary or None if not available
        """
        if not self.registry or not self.run_id:
            return None

        try:
            run_details = self.registry.get_run_details(self.run_id)
            if run_details:
                return {
                    "run_id": run_details.run_id,
                    "title": run_details.title,
                    "status": run_details.status,
                    "agent_count": len(run_details.agent_sessions),
                    "log_directories": run_details.log_directories,
                    "worktrees": run_details.metadata.get("worktrees", []),
                    "focus_areas": run_details.metadata.get("focus_areas", []),
                }

        except Exception as e:
            print(f"⚠️  Chat Monitor get details failed: {e}")

        return None

    @classmethod
    def create_for_current_session(
        cls,
        title: str,
        worktrees: Optional[List[str]] = None,
        focus_areas: Optional[List[str]] = None,
        **metadata,
    ) -> "OrchestratorIntegration":
        """
        Create integration instance for current session.

        Automatically detects session ID from environment or generates one.

        Args:
            title: Human-readable title for this run
            worktrees: List of worktree names being used
            focus_areas: List of focus areas for this run
            **metadata: Additional metadata for the run

        Returns:
            OrchestratorIntegration instance
        """
        # Try to get session ID from environment
        session_id = os.getenv("CLAUDE_SESSION_ID")

        if not session_id:
            # Generate a session ID
            import uuid

            session_id = str(uuid.uuid4())
            print(f"💡 Generated session ID: {session_id}")

        return cls(
            title=title,
            orchestrator_session=session_id,
            worktrees=worktrees,
            focus_areas=focus_areas,
            **metadata,
        )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - auto-complete run."""
        if exc_type:
            self.complete_run(f"Failed with {exc_type.__name__}: {exc_val}")
        else:
            self.complete_run("Completed successfully")


def monitor_orchestrator_run(
    title: str,
    orchestrator_session: str,
    worktrees: Optional[List[str]] = None,
    focus_areas: Optional[List[str]] = None,
    **metadata,
):
    """
    Decorator for automatic orchestrator run monitoring.

    Usage:
    ```python
    @monitor_orchestrator_run(
        title="Research Analysis Pipeline",
        orchestrator_session=self.session_id,
        worktrees=["research", "analysis"],
        focus_areas=["research", "documentation"]
    )
    async def run_analysis_pipeline(self):
        # Orchestrator code here
        pass
    ```
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            integration = OrchestratorIntegration(
                title=title,
                orchestrator_session=orchestrator_session,
                worktrees=worktrees,
                focus_areas=focus_areas,
                **metadata,
            )

            try:
                # Add integration to first argument (usually self)
                if args and hasattr(args[0], "__dict__"):
                    args[0].chat_monitor_integration = integration

                result = await func(*args, **kwargs)
                integration.complete_run("Decorated function completed successfully")
                return result

            except Exception as e:
                integration.complete_run(f"Decorated function failed: {e}")
                raise

        return wrapper

    return decorator


# Example usage for GenericOrchestrator integration
def integrate_generic_orchestrator():
    """
    Example of how to integrate with GenericOrchestrator.

    Add this to your GenericOrchestrator class:
    """
    example_code = """
    # In GenericOrchestrator.__init__
    from orchestrator_integration import OrchestratorIntegration

    self.chat_monitor_integration = OrchestratorIntegration(
        title=f"Generic Orchestration: {self.output_dir.name}",
        orchestrator_session=self.session_id,  # You'll need to track this
        worktrees=self._detect_worktrees(),
        focus_areas=self._extract_focus_areas_from_tasks(tasks),
        task_count=len(tasks),
        max_parallel=self.max_parallel
    )

    # In your agent spawning code
    def spawn_agent(self, task):
        # ... existing spawn logic ...

        # Register with chat monitor
        if hasattr(self, 'chat_monitor_integration'):
            self.chat_monitor_integration.add_agent(
                agent_session_id=agent_session_id,
                role=task.task_type,
                location=self._get_task_location(task)
            )

    # In completion/cleanup
    def complete(self):
        if hasattr(self, 'chat_monitor_integration'):
            self.chat_monitor_integration.complete_run(
                f"Completed {self.completed_tasks}/{self.total_tasks} tasks"
            )
    """

    print("Example integration code:")
    print(example_code)
