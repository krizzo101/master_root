#!/usr/bin/env python3
"""
Example usage of the Collaborative Workspace System

This file demonstrates how agents can use the collaborative workspace system
to work together on shared projects with real-time synchronization.
"""

import asyncio
from pathlib import Path

from .change_tracker import ChangeTracker
from .sync_engine import SyncEngine
from .workspace_sdk import CollaborationConfig, WorkspaceSDK


async def example_basic_collaboration():
    """Basic example of two agents collaborating on a project"""

    # Initialize workspace directories
    base_path = Path("/tmp/collaboration_demo")
    base_path.mkdir(exist_ok=True)

    # Create SDK instances for two agents
    agent1_sdk = WorkspaceSDK(
        agent_id="research_agent_1",
        base_path=base_path / "agent1",
        config=CollaborationConfig(
            enable_real_time_sync=True,
            auto_commit_interval=60,  # Auto-commit every minute
        ),
    )

    agent2_sdk = WorkspaceSDK(
        agent_id="analysis_agent_2",
        base_path=base_path / "agent2",
        config=CollaborationConfig(enable_real_time_sync=True, auto_commit_interval=60),
    )

    try:
        # Agent 1 creates a research workspace
        workspace_id = await agent1_sdk.create_workspace(
            name="AI Research Project",
            workspace_type="research",
            description="Collaborative research on AI capabilities",
        )

        print(f"Agent 1 created workspace: {workspace_id}")

        # Agent 1 joins the workspace
        await agent1_sdk.join_workspace(workspace_id)
        print("Agent 1 joined workspace")

        # Agent 1 creates initial research files
        await agent1_sdk.write_file(
            "shared_files/research_plan.md",
            """# AI Research Project

## Objectives
- Investigate collaborative AI capabilities
- Test real-time synchronization
- Document findings

## Tasks
- [ ] Literature review
- [ ] Experimental design
- [ ] Data collection
- [ ] Analysis
            """,
            "Initial research plan",
        )

        await agent1_sdk.write_file(
            "data/experiment_1_data.json",
            '{"experiment": "collaboration_test", "start_time": "2025-01-01T00:00:00Z"}',
            "Initial experiment data",
        )

        # Commit changes
        commit_id = await agent1_sdk.commit_changes("Initial workspace setup")
        print(f"Agent 1 committed changes: {commit_id}")

        # Share workspace with Agent 2
        await agent1_sdk.workspace_manager.share_workspace(
            workspace_id, "research_agent_1", "analysis_agent_2", "editor"
        )
        print("Workspace shared with Agent 2")

        # Agent 2 joins the workspace
        await agent2_sdk.join_workspace(workspace_id)
        print("Agent 2 joined workspace")

        # Agent 2 reads the research plan
        research_plan = await agent2_sdk.read_file("shared_files/research_plan.md")
        print("Agent 2 read research plan:")
        print(research_plan[:200] + "...")

        # Agent 2 adds analysis notes
        await agent2_sdk.write_file(
            "analysis/initial_analysis.md",
            """# Initial Analysis Notes

## Observations
- Collaborative workspace system is functioning
- Real-time file sharing works properly
- Version control is tracking changes

## Next Steps
- Implement data analysis pipeline
- Set up automated testing
- Document collaboration patterns
            """,
            "Agent 2 analysis notes",
        )

        # Agent 2 updates the research plan
        updated_plan = research_plan.replace(
            "- [ ] Literature review", "- [x] Literature review (Agent 2 reviewing)"
        )

        await agent2_sdk.write_file(
            "shared_files/research_plan.md", updated_plan, "Updated task status"
        )

        # Commit Agent 2's changes
        commit_id_2 = await agent2_sdk.commit_changes("Added analysis and updated plan")
        print(f"Agent 2 committed changes: {commit_id_2}")

        # Both agents check collaboration stats
        agent1_stats = await agent1_sdk.get_workspace_stats()
        agent2_stats = await agent2_sdk.get_workspace_stats()

        print(f"\nAgent 1 workspace stats: {agent1_stats}")
        print(f"Agent 2 workspace stats: {agent2_stats}")

        # Check collaborators
        collaborators = await agent1_sdk.get_collaborators()
        print(f"\nActive collaborators: {len(collaborators)}")
        for collab in collaborators:
            print(f"  - {collab['agent_id']} ({collab['role']})")

        # Get change history
        history = await agent1_sdk.get_change_history(limit=10)
        print(f"\nChange history ({len(history)} commits):")
        for commit in history:
            print(
                f"  - {commit['commit_id'][:8]}: {commit['message']} by {commit['agent_id']}"
            )

        # Create a snapshot
        snapshot_id = await agent1_sdk.create_snapshot(
            "milestone_1", "Completed initial setup and basic collaboration"
        )
        print(f"\nCreated snapshot: {snapshot_id}")

        # Send a message between agents
        await agent1_sdk.send_message_to_collaborator(
            "analysis_agent_2",
            "Great work on the analysis! Ready to proceed to next phase.",
            "text",
        )

        # Agent 2 reads messages
        messages = await agent2_sdk.get_messages()
        print(f"\nAgent 2 received {len(messages)} messages:")
        for msg in messages:
            print(f"  - From {msg['from']}: {msg['content']}")

    finally:
        # Clean up
        await agent1_sdk.leave_workspace()
        await agent2_sdk.leave_workspace()
        await agent1_sdk.cleanup()
        await agent2_sdk.cleanup()

        print("\nCollaboration demo completed!")


async def example_real_time_sync():
    """Example demonstrating real-time synchronization with WebSocket server"""

    # Start the sync server
    change_tracker = ChangeTracker(Path("/tmp/sync_demo/tracking"))
    sync_engine = SyncEngine(host="localhost", port=8765, change_tracker=change_tracker)

    # Start server in background
    await sync_engine.start_server()

    try:
        base_path = Path("/tmp/sync_demo")
        base_path.mkdir(exist_ok=True)

        # Create two agents with sync enabled
        agent1_sdk = WorkspaceSDK(
            agent_id="writer_agent", base_path=base_path / "agent1"
        )

        agent2_sdk = WorkspaceSDK(
            agent_id="reviewer_agent", base_path=base_path / "agent2"
        )

        # Connect both agents to sync server
        await agent1_sdk.connect_to_sync_server()
        await agent2_sdk.connect_to_sync_server()

        # Set up event handlers for real-time notifications
        def on_file_changed(event):
            print(
                f"🔄 Real-time update: {event['data']['file_path']} was {event['data']['change_type']} by {event['agent_id']}"
            )

        agent1_sdk.on_event("file_changed", on_file_changed)
        agent2_sdk.on_event("file_changed", on_file_changed)

        # Create and join workspace
        workspace_id = await agent1_sdk.create_workspace(
            name="Real-time Collaboration Demo", workspace_type="project"
        )

        await agent1_sdk.join_workspace(workspace_id)
        await agent2_sdk.join_workspace(workspace_id)

        # Share workspace
        await agent1_sdk.workspace_manager.share_workspace(
            workspace_id, "writer_agent", "reviewer_agent", "editor"
        )

        print("🚀 Real-time sync demo starting...")

        # Agent 1 writes a document
        await agent1_sdk.write_file(
            "shared_files/collaborative_document.md",
            """# Collaborative Document

This document is being edited in real-time by multiple agents.

## Section 1: Introduction
Writer agent is creating this document...
            """,
            "Initial document creation",
        )

        # Give time for sync
        await asyncio.sleep(1)

        # Agent 2 reads and adds content
        content = await agent2_sdk.read_file("shared_files/collaborative_document.md")
        updated_content = (
            content
            + """

## Section 2: Review Notes
Reviewer agent has read the document and adds:
- The introduction is clear and well-structured
- Ready for additional content
- Collaboration is working smoothly!
        """
        )

        await agent2_sdk.write_file(
            "shared_files/collaborative_document.md",
            updated_content,
            "Added review section",
        )

        # Give time for sync
        await asyncio.sleep(1)

        # Agent 1 appends more content
        await agent1_sdk.append_to_file(
            "shared_files/collaborative_document.md",
            """
## Section 3: Final Thoughts
Writer agent concluding:
- Real-time collaboration is successful
- Multiple agents can work simultaneously
- Changes are synchronized instantly
        """,
        )

        # Final sync wait
        await asyncio.sleep(2)

        # Both agents commit their changes
        await agent1_sdk.commit_changes("Writer agent final commit")
        await agent2_sdk.commit_changes("Reviewer agent final commit")

        # Show connected agents
        connected_agents = await sync_engine.get_connected_agents(workspace_id)
        print(f"\n📊 Connected agents: {len(connected_agents)}")
        for agent in connected_agents:
            print(f"  - {agent['agent_id']} (connected at {agent['connected_at']})")

        # Show workspace activity
        activity = await sync_engine.get_workspace_activity(workspace_id)
        print(f"\n📈 Workspace activity: {activity}")

    finally:
        # Cleanup
        await agent1_sdk.cleanup()
        await agent2_sdk.cleanup()
        await sync_engine.stop_server()

        print("\n✅ Real-time sync demo completed!")


async def example_conflict_resolution():
    """Example demonstrating conflict detection and resolution"""

    base_path = Path("/tmp/conflict_demo")
    base_path.mkdir(exist_ok=True)

    # Create two agents
    agent1_sdk = WorkspaceSDK("agent_1", base_path / "agent1")
    agent2_sdk = WorkspaceSDK("agent_2", base_path / "agent2")

    try:
        # Create and share workspace
        workspace_id = await agent1_sdk.create_workspace(
            "Conflict Resolution Demo", "project"
        )

        await agent1_sdk.join_workspace(workspace_id)
        await agent2_sdk.join_workspace(workspace_id)

        await agent1_sdk.workspace_manager.share_workspace(
            workspace_id, "agent_1", "agent_2", "editor"
        )

        # Both agents start with the same file
        initial_content = """# Shared Configuration

database_host = localhost
database_port = 5432
database_name = myapp
        """

        await agent1_sdk.write_file("config.py", initial_content, "Initial config")

        # Agent 1 reads current version
        content_1, version_1 = await agent1_sdk.current_filesystem.read_file(
            "config.py", "agent_1"
        )
        print(f"Agent 1 has version {version_1}")

        # Agent 2 reads current version
        content_2, version_2 = await agent2_sdk.current_filesystem.read_file(
            "config.py", "agent_2"
        )
        print(f"Agent 2 has version {version_2}")

        # Both agents modify the file simultaneously (conflict scenario)
        agent1_changes = content_1.replace(
            "database_host = localhost", "database_host = prod-server"
        )
        agent2_changes = content_2.replace(
            "database_host = localhost", "database_host = test-server"
        )

        # Agent 1 writes first
        success_1, error_1 = await agent1_sdk.current_filesystem.write_file(
            "config.py", agent1_changes, "agent_1", version_1, "Changed to prod server"
        )
        print(f"Agent 1 write: {'success' if success_1 else f'failed - {error_1}'}")

        # Agent 2 writes second (should detect conflict)
        success_2, error_2 = await agent2_sdk.current_filesystem.write_file(
            "config.py", agent2_changes, "agent_2", version_2, "Changed to test server"
        )
        print(f"Agent 2 write: {'success' if success_2 else f'failed - {error_2}'}")

        # Check for conflicts
        file_info = await agent1_sdk.get_file_info("config.py")
        if file_info and file_info.get("has_conflicts"):
            print("🔥 Conflict detected!")

            # Get file history to understand the conflict
            history = await agent1_sdk.current_filesystem.get_file_history("config.py")
            print(f"File has {len(history)} versions:")
            for version in history[-3:]:  # Last 3 versions
                print(
                    f"  - v{version.version}: {version.changes_summary} by {version.modified_by}"
                )

            # Resolve conflict by merging changes
            resolved_content = """# Shared Configuration

# Conflict resolved: using environment-specific config
import os

if os.getenv('ENVIRONMENT') == 'production':
    database_host = 'prod-server'
elif os.getenv('ENVIRONMENT') == 'test':
    database_host = 'test-server'
else:
    database_host = 'localhost'

database_port = 5432
database_name = myapp
            """

            # Resolve the conflict
            resolved = await agent1_sdk.current_filesystem.resolve_conflict(
                "config.py", "agent_1", "merge", resolved_content
            )

            if resolved:
                print("✅ Conflict resolved using merge strategy")
            else:
                print("❌ Failed to resolve conflict")

        # Commit final state
        await agent1_sdk.commit_changes("Resolved database config conflict")

    finally:
        await agent1_sdk.cleanup()
        await agent2_sdk.cleanup()

        print("🎯 Conflict resolution demo completed!")


if __name__ == "__main__":
    print("🌟 Collaborative Workspace System Demo")
    print("======================================\n")

    # Run examples
    asyncio.run(example_basic_collaboration())
    print("\n" + "=" * 50 + "\n")

    asyncio.run(example_real_time_sync())
    print("\n" + "=" * 50 + "\n")

    asyncio.run(example_conflict_resolution())
