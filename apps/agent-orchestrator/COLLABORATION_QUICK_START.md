# Real-Time Multi-Agent Collaboration - Quick Start Guide

## Overview

This system transforms the existing agent orchestrator into a real-time collaboration platform where Claude agents can communicate, share workspaces, and coordinate dynamically during execution.

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                Collaboration Platform                        │
├─────────────────────────────────────────────────────────────┤
│  Message Bus    │  Coordination  │  Shared Workspaces      │
│  (Real-time)    │  Engine        │  (File Sharing)         │
└─────────────────────────────────────────────────────────────┘
           │              │                │
    ┌──────┼──────┐   ┌───┼───┐       ┌────┼────┐
    Agent A       Agent B      Agent C
    Research      Design       Implementation
```

## Key Components

1. **CollaborationMessageBus** - Real-time messaging with WebSocket + Redis
2. **DynamicCoordinationEngine** - Event-driven task handoffs and coordination
3. **SharedWorkspaceManager** - Collaborative file editing and versioning
4. **CollaborationOrchestrator** - Main orchestrator with full compatibility

## Quick Start

### 1. Basic Usage (Backwards Compatible)

```python
from pathlib import Path
from src.collaboration import CollaborationOrchestrator

# Works exactly like existing orchestrator
orchestrator = CollaborationOrchestrator(
    output_dir=Path("./output"),
    max_parallel=5,
    enable_collaboration=False  # Traditional mode
)

# Use regular AgentTask objects
tasks = [AgentTask(...)]
results = await orchestrator.execute_batch(tasks)
```

### 2. Enable Collaboration Features

```python
# Enable collaboration with default settings
orchestrator = CollaborationOrchestrator(
    output_dir=Path("./output"),
    max_parallel=5,
    enable_collaboration=True,  # Enable collaboration
    # redis_url="redis://localhost:6379/0",  # Optional Redis
    websocket_port=8767,  # WebSocket port for real-time messaging
)

# Create collaborative tasks
tasks = [
    orchestrator.create_collaborative_task(
        task_id="research",
        task_type="research-specialist",
        prompt="Research microservices patterns",
        required_capabilities=["research", "architecture"],
        collaboration_type=CollaborationType.PARALLEL_WORK,
        shared_workspace=True,  # Enable shared workspace
        allow_handoffs=True,    # Allow dynamic task handoffs
    )
]

results = await orchestrator.execute_batch(tasks)
```

### 3. Advanced Collaboration

```python
# Multi-phase collaborative workflow
tasks = [
    # Phase 1: Parallel research
    orchestrator.create_collaborative_task(
        task_id="requirements_analysis",
        task_type="business-analyst",
        prompt="Analyze system requirements",
        collaboration_type=CollaborationType.EXPERT_CONSULTATION,
        shared_workspace=True,
    ),

    # Phase 2: Collaborative design with peer review
    orchestrator.create_collaborative_task(
        task_id="system_design",
        task_type="system-architect",
        prompt="Design system architecture",
        dependencies=["requirements_analysis"],
        collaboration_type=CollaborationType.PEER_REVIEW,
        allow_peer_review=True,
        shared_workspace=True,
    ),

    # Phase 3: Parallel implementation with handoffs
    orchestrator.create_collaborative_task(
        task_id="implementation",
        task_type="full-stack-developer",
        prompt="Implement the system",
        dependencies=["system_design"],
        collaboration_type=CollaborationType.SEQUENTIAL_HANDOFF,
        allow_handoffs=True,  # Can hand off to specialists
        shared_workspace=True,
        max_collaborators=3,
    ),
]

results = await orchestrator.execute_batch(tasks)
```

## Collaboration Features

### Real-Time Messaging
- **Direct Messages**: Agent-to-agent communication
- **Broadcasts**: One-to-many announcements
- **Coordination Events**: Task handoffs, resource requests
- **WebSocket + Redis**: High-performance real-time delivery

### Dynamic Task Handoffs
- Agents can request handoffs when encountering complexity
- Automatic capability matching to find suitable agents
- Real-time handoff negotiation and status tracking

### Shared Workspaces
- Collaborative file editing with conflict resolution
- Real-time change notifications
- Version control and file locking
- Cross-agent artifact sharing

### Event-Driven Coordination
- Progress updates broadcast to collaborators
- Resource sharing and knowledge exchange
- Collaborative workflow management
- Real-time monitoring and analytics

## Demo and Examples

### Run the Demo
```bash
cd /home/opsvi/master_root/apps/agent-orchestrator
python collaboration_demo.py
```

Choose from:
1. **Basic Demo**: Software development workflow with collaborative tasks
2. **Advanced Demo**: Dynamic handoffs, peer review, and brainstorming
3. **Both Demos**: Complete feature demonstration

### Example Collaboration Patterns

#### 1. Parallel Work Distribution
```python
# Multiple agents work on different aspects simultaneously
collaboration_type=CollaborationType.PARALLEL_WORK
shared_workspace=True
max_collaborators=4
```

#### 2. Expert Consultation
```python
# Bring in specialists when needed
collaboration_type=CollaborationType.EXPERT_CONSULTATION
required_capabilities=["security", "cryptography"]
allow_handoffs=True
```

#### 3. Peer Review Process
```python
# Mandatory peer review for quality assurance
collaboration_type=CollaborationType.PEER_REVIEW
allow_peer_review=True
enable_handoffs=False  # Must complete with review
```

#### 4. Sequential Handoffs
```python
# Pass tasks between agents as complexity evolves
collaboration_type=CollaborationType.SEQUENTIAL_HANDOFF
allow_handoffs=True
preferred_agents=["specialist-agent-id"]
```

## Integration with Existing Systems

### Backwards Compatibility
- All existing orchestrator code works unchanged
- Collaboration is opt-in via `enable_collaboration=True`
- Existing `AgentTask` objects supported alongside `CollaborativeTask`
- No breaking changes to current workflows

### Migration Path
1. **Phase 1**: Add collaboration to new workflows
2. **Phase 2**: Gradually enable collaboration on existing tasks
3. **Phase 3**: Migrate to collaborative-first approach
4. **Phase 4**: Deprecate non-collaborative mode

### Monitoring Integration
- Collaboration metrics added to existing monitoring
- Real-time collaboration dashboard
- WebSocket streaming for live updates
- Enhanced quality reports with collaboration data

## Performance and Scaling

### Performance Targets
- **Message Latency**: <50ms for direct messages
- **Workspace Sync**: <1s for file changes across agents
- **Agent Discovery**: <100ms for capability queries
- **Concurrent Agents**: 50+ with minimal performance impact

### Scaling Options
- **Phase 1** (2-5 agents): WebSocket + File fallback
- **Phase 2** (5-15 agents): Redis Pub/Sub + WebSocket
- **Phase 3** (15-50+ agents): Redis Cluster + Message Queue

## Configuration

### Environment Variables
```bash
# Optional Redis backend for scaling
REDIS_URL=redis://localhost:6379/0

# WebSocket port for real-time messaging
COLLABORATION_WEBSOCKET_PORT=8767

# Enable debug logging
COLLABORATION_DEBUG=true
```

### Dependencies
```bash
# Optional for enhanced performance
pip install redis websockets

# Core collaboration works without external dependencies
# Falls back to file-based messaging
```

## Architecture Benefits

### For Developers
- **Seamless Integration**: No changes to existing code required
- **Progressive Enhancement**: Add collaboration incrementally
- **Rich Monitoring**: Real-time insights into agent collaboration
- **Flexible Patterns**: Multiple collaboration modes supported

### For Agents
- **Real-time Communication**: Direct agent-to-agent messaging
- **Dynamic Coordination**: Intelligent task routing and handoffs
- **Shared Context**: Collaborative workspaces and knowledge sharing
- **Adaptive Workflows**: React to changing requirements in real-time

### for Operations
- **High Reliability**: Multiple fallback mechanisms
- **Scalable Architecture**: Handles 2-50+ concurrent agents
- **Comprehensive Monitoring**: Full visibility into collaboration
- **Zero-Downtime Upgrades**: Backwards compatible deployment

## Troubleshooting

### Common Issues

1. **WebSocket Connection Fails**
   ```python
   # Fallback to file-based messaging automatically
   # Check firewall settings for port 8767
   ```

2. **Redis Connection Issues**
   ```python
   # System falls back to WebSocket + file messaging
   # Verify Redis URL and connectivity
   ```

3. **Workspace Sync Conflicts**
   ```python
   # Automatic conflict resolution with merge strategies
   # Manual resolution for complex conflicts
   ```

## Next Steps

1. **Try the Demo**: Run `python collaboration_demo.py`
2. **Review Architecture**: Read `MULTI_AGENT_COLLABORATION_ARCHITECTURE.md`
3. **Implement Gradually**: Start with `enable_collaboration=True`
4. **Monitor Performance**: Use collaboration statistics and reports
5. **Scale Up**: Add Redis backend for higher concurrency

## Support and Documentation

- **Architecture Document**: `MULTI_AGENT_COLLABORATION_ARCHITECTURE.md`
- **Demo Code**: `collaboration_demo.py`
- **Source Code**: `src/collaboration/`
- **Integration Examples**: Multiple patterns in demo

This collaboration system transforms isolated agent execution into a true multi-agent platform where Claude agents work together seamlessly, making complex tasks more manageable and results more comprehensive.
