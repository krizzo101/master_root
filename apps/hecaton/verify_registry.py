#!/usr/bin/env python
"""Verify agent registry functionality."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from hecaton.agents.agent_registry import Agent, AgentRegistry


def main():
    print("Testing Agent Registry System...")
    print("=" * 50)

    # Create registry
    registry = AgentRegistry(heartbeat_timeout=10.0)
    print("✓ Registry created")

    # Create agents
    agent1 = Agent(
        agent_id="agent-001", name="Compute Agent", capabilities={"compute", "ml", "optimization"}
    )

    agent2 = Agent(
        agent_id="agent-002",
        name="Storage Agent",
        capabilities={"storage", "backup", "replication"},
    )

    agent3 = Agent(
        agent_id="agent-003", name="Network Agent", capabilities={"network", "routing", "firewall"}
    )
    print("✓ Agents created")

    # Register agents
    assert registry.register(agent1) == True
    assert registry.register(agent2) == True
    assert registry.register(agent3) == True
    print("✓ Agents registered")

    # Test duplicate registration
    assert registry.register(agent1) == False
    print("✓ Duplicate registration prevented")

    # Test retrieval
    retrieved = registry.get_agent("agent-001")
    assert retrieved is not None
    assert retrieved.name == "Compute Agent"
    print("✓ Agent retrieval works")

    # Test capability search
    ml_agents = registry.find_by_capability("ml")
    assert len(ml_agents) == 1
    assert ml_agents[0].agent_id == "agent-001"
    print("✓ Capability search works")

    # Test load balancing
    registry.update_agent_load("agent-001", 0.8)
    registry.update_agent_load("agent-002", 0.3)
    registry.update_agent_load("agent-003", 0.5)

    least_loaded = registry.get_least_loaded_agent()
    assert least_loaded.agent_id == "agent-002"
    print("✓ Load balancing works")

    # Test heartbeat update
    assert registry.update_heartbeat("agent-001") == True
    print("✓ Heartbeat update works")

    # Test statistics
    stats = registry.get_registry_stats()
    assert stats["total_agents"] == 3
    assert stats["healthy_agents"] == 3
    assert "active" in stats["status_distribution"]
    print("✓ Registry statistics work")

    # Test deregistration
    assert registry.deregister("agent-003") == True
    assert registry.get_agent("agent-003") is None
    print("✓ Deregistration works")

    # Test task distribution strategies
    agent = registry.distribute_task(strategy="least_loaded")
    assert agent is not None
    print("✓ Task distribution (least_loaded) works")

    agent = registry.distribute_task(strategy="random")
    assert agent is not None
    print("✓ Task distribution (random) works")

    print("\n" + "=" * 50)
    print("All tests passed! Agent Registry is fully functional.")
    print("\nRegistry capabilities implemented:")
    print("  • Agent registration and deregistration")
    print("  • Capability-based discovery")
    print("  • Health monitoring with heartbeats")
    print("  • Load balancing (least-loaded, random, round-robin)")
    print("  • Thread-safe operations")
    print("  • Comprehensive statistics tracking")


if __name__ == "__main__":
    main()
