#!/usr/bin/env python3
"""
Subdivision State Manager - Hierarchical State and Context Management

Manages state coordination across subdivision workflows:
- Hierarchical state tracking across subdivision levels
- Context preservation and inheritance
- State synchronization between subdivision agents
- Performance optimization for complex subdivision hierarchies
- Cross-agent context sharing and coordination

Ensures state consistency and optimal context flow in subdivision scenarios.
"""

from datetime import datetime, timedelta
from typing import Any, Optional

from src.applications.oamat_sd.src.config.config_manager import ConfigManager
from src.applications.oamat_sd.src.models.workflow_models import SmartDecompositionState
from src.applications.oamat_sd.src.sd_logging import LoggerFactory
from src.applications.oamat_sd.src.sd_logging.log_config import default_config


class SubdivisionStateContext:
    """Context container for subdivision state management"""

    def __init__(
        self,
        subdivision_level: int = 0,
        parent_context: Optional["SubdivisionStateContext"] = None,
        subdivision_id: str = None,
        metadata: dict = None,
    ):
        self.subdivision_level = subdivision_level
        self.parent_context = parent_context
        self.subdivision_id = (
            subdivision_id or f"subdivision_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        self.metadata = metadata or {}
        self.child_contexts: dict[str, SubdivisionStateContext] = {}
        self.state_snapshots: list[dict] = []
        self.created_at = datetime.now()
        self.last_updated = datetime.now()

    def add_child_context(
        self, child_id: str, child_context: "SubdivisionStateContext"
    ):
        """Add a child subdivision context"""
        self.child_contexts[child_id] = child_context
        self.last_updated = datetime.now()

    def create_state_snapshot(self, state: dict, snapshot_type: str = "checkpoint"):
        """Create a snapshot of the current state"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "type": snapshot_type,
            "state": state.copy(),
            "subdivision_id": self.subdivision_id,
            "level": self.subdivision_level,
        }
        self.state_snapshots.append(snapshot)
        self.last_updated = datetime.now()

    def get_inheritance_chain(self) -> list["SubdivisionStateContext"]:
        """Get the full inheritance chain from root to this context"""
        chain = []
        current = self
        while current:
            chain.insert(0, current)
            current = current.parent_context
        return chain


class SubdivisionStateManager:
    """
    Manages state coordination and context across subdivision workflows

    Capabilities:
    - Hierarchical state tracking
    - Context inheritance and preservation
    - State synchronization between agents
    - Performance optimization
    - Cross-agent coordination
    """

    def __init__(self, logger_factory: LoggerFactory = None):
        """Initialize the Subdivision State Manager"""
        self.logger_factory = logger_factory or LoggerFactory(default_config)
        self.logger = self.logger_factory.get_debug_logger()

        # Configuration from centralized config manager
        self.config_manager = ConfigManager()

        # State context tracking
        self.active_contexts: dict[str, SubdivisionStateContext] = {}
        self.state_history: list[dict] = []

        # Performance metrics
        self.performance_metrics = {
            "context_creation_time": [],
            "state_synchronization_time": [],
            "context_inheritance_time": [],
            "total_contexts_managed": 0,
        }

        self.logger.info("✅ Subdivision State Manager initialized")

    async def create_subdivision_context(
        self,
        state: SmartDecompositionState,
        subdivision_metadata: dict,
        parent_context_id: str | None = None,
        debug: bool = False,
    ) -> SubdivisionStateContext:
        """
        Create a new subdivision context for state management

        Args:
            state: Current execution state
            subdivision_metadata: Metadata about the subdivision
            parent_context_id: ID of parent context if this is a nested subdivision
            debug: Enable detailed logging

        Returns:
            SubdivisionStateContext for this subdivision
        """
        if debug:
            self.logger.info("🏗️ STATE MANAGER: Creating subdivision context...")

        context_creation_start = datetime.now()

        try:
            # Determine subdivision level
            subdivision_level = 0
            parent_context = None

            if parent_context_id and parent_context_id in self.active_contexts:
                parent_context = self.active_contexts[parent_context_id]
                subdivision_level = parent_context.subdivision_level + 1

            # Create subdivision context
            context_id = f"sub_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

            subdivision_context = SubdivisionStateContext(
                subdivision_level=subdivision_level,
                parent_context=parent_context,
                subdivision_id=context_id,
                metadata={
                    "subdivision_metadata": subdivision_metadata,
                    "original_request": state.get("user_request", ""),
                    "project_path": str(state.get("project_path", "")),
                    "context_creation_time": datetime.now().isoformat(),
                    "estimated_agents": subdivision_metadata.get(
                        "estimated_sub_agents", 0
                    ),
                    "complexity_score": subdivision_metadata.get("complexity_score", 0),
                },
            )

            # Register context
            self.active_contexts[context_id] = subdivision_context

            # Add to parent if exists
            if parent_context:
                parent_context.add_child_context(context_id, subdivision_context)

            # Create initial state snapshot
            subdivision_context.create_state_snapshot(
                state.copy() if hasattr(state, "copy") else dict(state),
                "initialization",
            )

            # Update performance metrics
            creation_time = (
                datetime.now() - context_creation_start
            ).total_seconds() * 1000
            self.performance_metrics["context_creation_time"].append(creation_time)
            self.performance_metrics["total_contexts_managed"] += 1

            if debug:
                self.logger.info(
                    f"🏗️ Context created: {context_id} (Level {subdivision_level})"
                )
                self.logger.info(f"⏱️ Creation time: {creation_time:.2f}ms")

            return subdivision_context

        except Exception as e:
            self.logger.error(f"❌ Subdivision context creation failed: {e}")
            raise RuntimeError(f"Failed to create subdivision context: {e}")

    async def synchronize_subdivision_state(
        self, context_id: str, agent_outputs: dict[str, dict], debug: bool = False
    ) -> dict[str, Any]:
        """
        Synchronize state across subdivision agents

        Args:
            context_id: ID of the subdivision context
            agent_outputs: Outputs from subdivision agents
            debug: Enable detailed logging

        Returns:
            Synchronized state data
        """
        if debug:
            self.logger.info(
                f"🔄 SYNCHRONIZATION: Synchronizing state for context {context_id}..."
            )

        sync_start_time = datetime.now()

        try:
            if context_id not in self.active_contexts:
                raise ValueError(f"Context {context_id} not found")

            context = self.active_contexts[context_id]

            # Create state synchronization data
            synchronized_state = {
                "context_id": context_id,
                "subdivision_level": context.subdivision_level,
                "agent_outputs": agent_outputs,
                "synchronization_timestamp": datetime.now().isoformat(),
                "agent_count": len(agent_outputs),
                "successful_agents": sum(
                    1
                    for output in agent_outputs.values()
                    if not output.get("error", False)
                ),
                "failed_agents": sum(
                    1 for output in agent_outputs.values() if output.get("error", False)
                ),
            }

            # Add context inheritance information
            inheritance_chain = context.get_inheritance_chain()
            synchronized_state["inheritance_path"] = [
                {
                    "context_id": ctx.subdivision_id,
                    "level": ctx.subdivision_level,
                    "created_at": ctx.created_at.isoformat(),
                }
                for ctx in inheritance_chain
            ]

            # Create synchronization snapshot
            context.create_state_snapshot(
                {
                    "synchronized_state": synchronized_state,
                    "agent_outputs": agent_outputs,
                },
                "synchronization",
            )

            # Update performance metrics
            sync_time = (datetime.now() - sync_start_time).total_seconds() * 1000
            self.performance_metrics["state_synchronization_time"].append(sync_time)

            if debug:
                success_rate = (
                    synchronized_state["successful_agents"] / len(agent_outputs)
                    if agent_outputs
                    else 0
                )
                self.logger.info(
                    f"🔄 Synchronization complete: {success_rate:.1%} success rate"
                )
                self.logger.info(f"⏱️ Sync time: {sync_time:.2f}ms")

            return synchronized_state

        except Exception as e:
            self.logger.error(f"❌ State synchronization failed: {e}")
            raise RuntimeError(f"Failed to synchronize subdivision state: {e}")

    async def inherit_context_from_parent(
        self,
        context_id: str,
        inheritance_strategy: str = "selective",
        debug: bool = False,
    ) -> dict[str, Any]:
        """
        Inherit context from parent subdivision levels

        Args:
            context_id: ID of the current subdivision context
            inheritance_strategy: Strategy for context inheritance
            debug: Enable detailed logging

        Returns:
            Inherited context data
        """
        if debug:
            self.logger.info(f"🧬 INHERITANCE: Inheriting context for {context_id}...")

        inheritance_start_time = datetime.now()

        try:
            if context_id not in self.active_contexts:
                raise ValueError(f"Context {context_id} not found")

            context = self.active_contexts[context_id]
            inheritance_chain = context.get_inheritance_chain()

            inherited_context = {
                "context_id": context_id,
                "inheritance_strategy": inheritance_strategy,
                "inheritance_chain_length": len(inheritance_chain),
                "inherited_data": {},
                "inheritance_timestamp": datetime.now().isoformat(),
            }

            # Apply inheritance strategy
            if inheritance_strategy == "selective":
                inherited_context["inherited_data"] = await self._selective_inheritance(
                    inheritance_chain, debug
                )
            elif inheritance_strategy == "full":
                inherited_context["inherited_data"] = await self._full_inheritance(
                    inheritance_chain, debug
                )
            elif inheritance_strategy == "minimal":
                inherited_context["inherited_data"] = await self._minimal_inheritance(
                    inheritance_chain, debug
                )
            else:
                raise ValueError(
                    f"Unknown inheritance strategy: {inheritance_strategy}"
                )

            # Update performance metrics
            inheritance_time = (
                datetime.now() - inheritance_start_time
            ).total_seconds() * 1000
            self.performance_metrics["context_inheritance_time"].append(
                inheritance_time
            )

            if debug:
                inherited_keys = len(inherited_context["inherited_data"])
                self.logger.info(
                    f"🧬 Inheritance complete: {inherited_keys} context elements inherited"
                )
                self.logger.info(f"⏱️ Inheritance time: {inheritance_time:.2f}ms")

            return inherited_context

        except Exception as e:
            self.logger.error(f"❌ Context inheritance failed: {e}")
            raise RuntimeError(f"Failed to inherit context: {e}")

    async def _selective_inheritance(
        self, inheritance_chain: list[SubdivisionStateContext], debug: bool = False
    ) -> dict[str, Any]:
        """Selectively inherit context from parent levels"""

        inherited_data = {}

        for context in inheritance_chain[:-1]:  # Exclude current context
            # Inherit key metadata
            if "subdivision_metadata" in context.metadata:
                subdivision_meta = context.metadata["subdivision_metadata"]

                # Inherit specific fields that are relevant to child contexts
                inherited_data.update(
                    {
                        f"parent_complexity_score_{context.subdivision_level}": subdivision_meta.get(
                            "complexity_score", 0
                        ),
                        f"parent_reasoning_{context.subdivision_level}": subdivision_meta.get(
                            "subdivision_reasoning", ""
                        ),
                        f"parent_estimated_agents_{context.subdivision_level}": subdivision_meta.get(
                            "estimated_sub_agents", 0
                        ),
                    }
                )

            # Inherit project context
            if "original_request" in context.metadata:
                inherited_data["root_request"] = context.metadata["original_request"]

            if "project_path" in context.metadata:
                inherited_data["project_path"] = context.metadata["project_path"]

        return inherited_data

    async def _full_inheritance(
        self, inheritance_chain: list[SubdivisionStateContext], debug: bool = False
    ) -> dict[str, Any]:
        """Fully inherit all context from parent levels"""

        inherited_data = {}

        for i, context in enumerate(inheritance_chain[:-1]):
            context_prefix = f"level_{context.subdivision_level}"

            # Inherit all metadata
            for key, value in context.metadata.items():
                inherited_data[f"{context_prefix}_{key}"] = value

            # Inherit state snapshots summary
            if context.state_snapshots:
                inherited_data[f"{context_prefix}_snapshots_count"] = len(
                    context.state_snapshots
                )
                inherited_data[
                    f"{context_prefix}_last_snapshot"
                ] = context.state_snapshots[-1]["timestamp"]

        return inherited_data

    async def _minimal_inheritance(
        self, inheritance_chain: list[SubdivisionStateContext], debug: bool = False
    ) -> dict[str, Any]:
        """Minimally inherit only essential context"""

        inherited_data = {}

        # Only inherit from root context
        if len(inheritance_chain) > 1:
            root_context = inheritance_chain[0]

            inherited_data.update(
                {
                    "root_request": root_context.metadata.get("original_request", ""),
                    "project_path": root_context.metadata.get("project_path", ""),
                    "subdivision_depth": len(inheritance_chain) - 1,
                }
            )

        return inherited_data

    def get_context_hierarchy(self, context_id: str) -> dict[str, Any]:
        """Get the full context hierarchy for a subdivision context"""

        if context_id not in self.active_contexts:
            return {"error": f"Context {context_id} not found"}

        context = self.active_contexts[context_id]
        inheritance_chain = context.get_inheritance_chain()

        hierarchy = {
            "context_id": context_id,
            "current_level": context.subdivision_level,
            "total_levels": len(inheritance_chain),
            "hierarchy_chain": [],
            "child_contexts": list(context.child_contexts.keys()),
            "total_snapshots": len(context.state_snapshots),
        }

        for ctx in inheritance_chain:
            hierarchy["hierarchy_chain"].append(
                {
                    "context_id": ctx.subdivision_id,
                    "level": ctx.subdivision_level,
                    "created_at": ctx.created_at.isoformat(),
                    "last_updated": ctx.last_updated.isoformat(),
                    "child_count": len(ctx.child_contexts),
                    "snapshot_count": len(ctx.state_snapshots),
                }
            )

        return hierarchy

    def cleanup_completed_contexts(self, retention_hours: int = 24) -> dict[str, Any]:
        """Clean up completed subdivision contexts older than retention period"""

        cleanup_start_time = datetime.now()
        cutoff_time = cleanup_start_time - timedelta(hours=retention_hours)

        contexts_to_remove = []
        contexts_preserved = 0

        for context_id, context in self.active_contexts.items():
            # Only clean up contexts with no active children and older than cutoff
            if context.last_updated < cutoff_time and len(context.child_contexts) == 0:
                contexts_to_remove.append(context_id)
            else:
                contexts_preserved += 1

        # Remove old contexts
        for context_id in contexts_to_remove:
            del self.active_contexts[context_id]

        cleanup_time = (datetime.now() - cleanup_start_time).total_seconds() * 1000

        cleanup_result = {
            "contexts_removed": len(contexts_to_remove),
            "contexts_preserved": contexts_preserved,
            "cleanup_time_ms": cleanup_time,
            "retention_hours": retention_hours,
            "cleanup_timestamp": datetime.now().isoformat(),
        }

        self.logger.info(
            f"🧹 Context cleanup: {len(contexts_to_remove)} removed, {contexts_preserved} preserved"
        )

        return cleanup_result

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics for subdivision state management"""

        def safe_avg(values: list) -> float:
            return sum(values) / len(values) if values else 0.0

        return {
            "total_contexts_managed": self.performance_metrics[
                "total_contexts_managed"
            ],
            "active_contexts": len(self.active_contexts),
            "avg_context_creation_time_ms": safe_avg(
                self.performance_metrics["context_creation_time"]
            ),
            "avg_synchronization_time_ms": safe_avg(
                self.performance_metrics["state_synchronization_time"]
            ),
            "avg_inheritance_time_ms": safe_avg(
                self.performance_metrics["context_inheritance_time"]
            ),
            "total_state_history_entries": len(self.state_history),
            "performance_collected_at": datetime.now().isoformat(),
        }
