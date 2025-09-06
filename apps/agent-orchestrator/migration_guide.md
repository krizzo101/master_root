# Migration Guide: GenericOrchestrator → CollaborativeOrchestrator

## Quick Start (5 Minutes)

### Zero-Risk Migration (Identical Behavior)
```bash
# 1. Backup current setup (optional but recommended)
cp -r /path/to/orchestrator /path/to/orchestrator_backup

# 2. Update import (only change required)
```

**Before:**
```python
from src.generic_orchestrator import GenericOrchestrator
orchestrator = GenericOrchestrator(output_dir="/tmp/test")
```

**After:**
```python
from src.collaborative_orchestrator import CollaborativeOrchestrator
orchestrator = CollaborativeOrchestrator(output_dir="/tmp/test")
# Identical behavior, zero risk
```

✅ **Result**: Identical behavior, collaboration-ready codebase

## Migration Phases

### Phase 1: Foundation (Week 1) - Zero Risk
**Goal**: Establish collaboration-ready infrastructure with zero behavior changes

#### Step 1.1: Class Replacement
```python
# Change only the class name
from src.collaborative_orchestrator import CollaborativeOrchestrator

# All existing parameters work identically
orchestrator = CollaborativeOrchestrator(
    output_dir="/tmp/output",
    max_parallel=5,
    tokens=["token1", "token2"],
    use_optimizations=True
)

# All existing methods work identically
await orchestrator.run(task_generator, result_processor)
```

**Validation**: All existing tests should pass without modification.

#### Step 1.2: Infrastructure Verification
```python
# Verify collaboration infrastructure is ready (but not active)
orchestrator = CollaborativeOrchestrator(output_dir="/tmp/test")

# Check collaboration components initialized correctly
assert orchestrator.collaboration_enabled == False  # No config provided
assert hasattr(orchestrator, 'agent_registry')  # Ready but inactive
assert hasattr(orchestrator, 'enhanced_message_bus')  # Ready but inactive
```

### Phase 2: Basic Collaboration (Week 2) - Low Risk
**Goal**: Enable basic messaging and agent discovery

#### Step 2.1: Enable Messaging
```python
collaboration_config = {
    'enable_messaging': True,
    'redis_url': 'redis://localhost:6379'  # Optional, defaults to localhost
}

orchestrator = CollaborativeOrchestrator(
    output_dir="/tmp/output",
    collaboration_config=collaboration_config
)
```

**What This Enables**:
- Real-time agent-to-agent messaging
- Agent discovery and registration
- Event-driven coordination
- Enhanced dependency resolution

**Risk Level**: 🟡 Low - Non-collaborative tasks unaffected

#### Step 2.2: Test Basic Collaboration
```python
# Create collaborative task with agent communication
def create_collaborative_tasks():
    return [
        AgentTask(
            task_id="researcher",
            task_type="research",
            prompt="Research topic X and share findings with analyzer",
            context={'collaboration': {'notify': ['analyzer']}}
        ),
        AgentTask(
            task_id="analyzer",
            task_type="analysis",
            prompt="Wait for research findings and analyze",
            dependencies=["researcher"]
        )
    ]

await orchestrator.run(create_collaborative_tasks)
```

### Phase 3: Full Collaboration (Week 3) - Medium Value
**Goal**: Enable shared workspaces and advanced coordination

#### Step 3.1: Enable Shared Workspaces
```python
collaboration_config = {
    'enable_messaging': True,
    'shared_workspace': True,
    'workspace_config': {
        'sync_interval': 1.0,  # Real-time sync every 1 second
        'version_control': True,  # Track all changes
        'auto_backup': True  # Backup every hour
    }
}

orchestrator = CollaborativeOrchestrator(
    output_dir="/tmp/output",
    collaboration_config=collaboration_config
)
```

**What This Enables**:
- Multi-agent editing of same files
- Real-time workspace synchronization
- Version control and change tracking
- Collaborative artifact creation

#### Step 3.2: Advanced Collaborative Workflows
```python
def create_advanced_workflow():
    return [
        AgentTask(
            task_id="architect",
            task_type="architecture",
            prompt="Design system architecture in shared workspace",
            context={
                'workspace': {'shared': True, 'files': ['architecture.md']},
                'collaboration': {'broadcast_discoveries': True}
            }
        ),
        AgentTask(
            task_id="implementer_1",
            task_type="implementation",
            prompt="Implement frontend based on shared architecture",
            context={
                'workspace': {'shared': True, 'files': ['frontend/']},
                'collaboration': {'watch': ['architecture.md'], 'notify': ['tester']}
            }
        ),
        AgentTask(
            task_id="implementer_2",
            task_type="implementation",
            prompt="Implement backend based on shared architecture",
            context={
                'workspace': {'shared': True, 'files': ['backend/']},
                'collaboration': {'watch': ['architecture.md'], 'notify': ['tester']}
            }
        ),
        AgentTask(
            task_id="tester",
            task_type="testing",
            prompt="Test integrated system as components are completed",
            dependencies=["architect"],
            context={
                'workspace': {'shared': True, 'files': ['tests/']},
                'collaboration': {'watch': ['frontend/', 'backend/'], 'coordinate': True}
            }
        )
    ]
```

## Environment Setup

### Prerequisites
```bash
# Required (existing)
pip install asyncio pathlib

# Optional (for collaboration features)
pip install redis websockets aiofiles

# Verify Redis (if using collaboration)
redis-server --version
redis-cli ping  # Should return PONG
```

### Configuration Templates

#### Development Configuration
```python
# config/development.py
COLLABORATION_CONFIG = {
    'enable_messaging': True,
    'shared_workspace': True,
    'redis_url': 'redis://localhost:6379',
    'websocket_port': 8765,
    'log_level': 'DEBUG',
    'workspace_config': {
        'sync_interval': 0.5,  # Fast sync for development
        'auto_backup': False   # Disable backup in development
    }
}
```

#### Production Configuration
```python
# config/production.py
COLLABORATION_CONFIG = {
    'enable_messaging': True,
    'shared_workspace': True,
    'redis_url': 'redis://redis-cluster:6379',
    'websocket_port': 8765,
    'log_level': 'INFO',
    'workspace_config': {
        'sync_interval': 2.0,    # Slower sync for stability
        'auto_backup': True,     # Enable backup
        'backup_interval': 3600  # Backup every hour
    },
    'performance': {
        'max_concurrent_agents': 50,
        'message_buffer_size': 1000,
        'connection_pool_size': 20
    }
}
```

## Migration Checklist

### Pre-Migration (5 minutes)
- [ ] **Backup current setup** (recommended)
  ```bash
  cp -r /current/orchestrator /backup/orchestrator_$(date +%Y%m%d)
  ```
- [ ] **Verify dependencies installed**
  ```bash
  python -c "import asyncio, json, logging, pathlib, uuid; print('Core deps OK')"
  ```
- [ ] **Test current functionality**
  ```bash
  python -m pytest tests/ --tb=short
  ```

### Phase 1 Migration (15 minutes)
- [ ] **Update imports**
  ```python
  from src.collaborative_orchestrator import CollaborativeOrchestrator
  ```
- [ ] **Replace class instantiation**
  ```python
  orchestrator = CollaborativeOrchestrator(...)  # Same parameters
  ```
- [ ] **Run regression tests**
  ```bash
  python -m pytest tests/ --tb=short  # Should pass identically
  ```
- [ ] **Verify identical behavior**
  ```python
  # Run existing workflows - should work exactly the same
  ```

### Phase 2 Migration (1 hour)
- [ ] **Install optional dependencies**
  ```bash
  pip install redis websockets
  ```
- [ ] **Start Redis server**
  ```bash
  redis-server &  # Or use existing Redis instance
  ```
- [ ] **Add collaboration config**
  ```python
  collaboration_config = {'enable_messaging': True}
  orchestrator = CollaborativeOrchestrator(..., collaboration_config=collaboration_config)
  ```
- [ ] **Test basic collaboration**
  ```python
  # Run simple 2-agent collaborative task
  ```

### Phase 3 Migration (2 hours)
- [ ] **Enable shared workspaces**
  ```python
  collaboration_config.update({'shared_workspace': True})
  ```
- [ ] **Design collaborative workflows**
  ```python
  # Create tasks with shared workspace context
  ```
- [ ] **Performance testing**
  ```bash
  # Monitor resource usage, response times
  ```

## Rollback Procedures

### Immediate Rollback (30 seconds)
```python
# Change class back - instant rollback
from src.generic_orchestrator import GenericOrchestrator
orchestrator = GenericOrchestrator(...)  # Identical to original
```

### Configuration Rollback (1 minute)
```python
# Disable collaboration features
orchestrator = CollaborativeOrchestrator(
    ...,
    collaboration_config=None  # Disables all collaboration
)
```

### Service Rollback (2 minutes)
```bash
# Stop collaboration services if needed
redis-cli shutdown  # Stop Redis
# Kill WebSocket processes if running separately
```

## Validation & Testing

### Regression Testing
```bash
# Ensure existing functionality unchanged
python -m pytest tests/test_orchestrator.py -v

# Compare performance benchmarks
python benchmarks/performance_test.py --mode=baseline
python benchmarks/performance_test.py --mode=collaborative-disabled
# Should show <1% difference
```

### Collaboration Testing
```python
# Test basic messaging
async def test_basic_collaboration():
    config = {'enable_messaging': True}
    orchestrator = CollaborativeOrchestrator(output_dir="/tmp/test", collaboration_config=config)

    tasks = [
        AgentTask(task_id="sender", task_type="test", prompt="Send message to receiver"),
        AgentTask(task_id="receiver", task_type="test", prompt="Receive and acknowledge message")
    ]

    results = await orchestrator.execute_batch(tasks)
    assert all(r['status'] == 'completed' for r in results)

# Test shared workspace
async def test_shared_workspace():
    config = {'enable_messaging': True, 'shared_workspace': True}
    orchestrator = CollaborativeOrchestrator(output_dir="/tmp/test", collaboration_config=config)

    tasks = [
        AgentTask(
            task_id="writer",
            task_type="test",
            prompt="Write to shared file",
            context={'workspace': {'shared': True, 'files': ['shared.md']}}
        ),
        AgentTask(
            task_id="reader",
            task_type="test",
            prompt="Read from shared file",
            context={'workspace': {'shared': True, 'files': ['shared.md']}}
        )
    ]

    results = await orchestrator.execute_batch(tasks)
    assert all(r['status'] == 'completed' for r in results)
```

## Performance Optimization

### Memory Management
```python
# Configure memory limits for collaboration
collaboration_config = {
    'enable_messaging': True,
    'memory_limits': {
        'message_buffer_mb': 50,      # Limit message buffer to 50MB
        'workspace_cache_mb': 100,    # Limit workspace cache to 100MB
        'agent_registry_mb': 10       # Limit agent registry to 10MB
    }
}
```

### Connection Pooling
```python
# Optimize for high-throughput scenarios
collaboration_config = {
    'enable_messaging': True,
    'connection_pool': {
        'redis_pool_size': 20,        # Redis connection pool
        'websocket_pool_size': 100,   # WebSocket connection pool
        'reuse_connections': True     # Reuse connections when possible
    }
}
```

## Monitoring & Observability

### Built-in Metrics
```python
# Access collaboration metrics
orchestrator = CollaborativeOrchestrator(...)
await orchestrator.run(tasks)

# Get metrics after execution
metrics = orchestrator.get_collaboration_metrics()
print(f"Messages sent: {metrics['messages_sent']}")
print(f"Agents discovered: {metrics['agents_discovered']}")
print(f"Workspace operations: {metrics['workspace_ops']}")
print(f"Average message latency: {metrics['avg_message_latency_ms']}ms")
```

### Custom Monitoring
```python
# Add custom monitoring hooks
def custom_message_monitor(agent_id, message, latency_ms):
    if latency_ms > 100:
        logger.warning(f"Slow message from {agent_id}: {latency_ms}ms")

def custom_workspace_monitor(operation, file_path, duration_ms):
    logger.info(f"Workspace {operation} on {file_path}: {duration_ms}ms")

orchestrator.add_monitoring_hooks(
    message_hook=custom_message_monitor,
    workspace_hook=custom_workspace_monitor
)
```

## Common Issues & Solutions

### Issue: Redis Connection Failed
```python
# Problem: Can't connect to Redis
# Solution 1: Graceful fallback
collaboration_config = {
    'enable_messaging': True,
    'fallback_mode': 'file_based',  # Falls back to file-based messaging
    'redis_url': 'redis://localhost:6379'
}

# Solution 2: Check Redis status
import redis
try:
    r = redis.Redis.from_url('redis://localhost:6379')
    r.ping()
    print("Redis OK")
except redis.ConnectionError:
    print("Redis not available - will use fallback")
```

### Issue: WebSocket Port Conflict
```python
# Problem: Port 8765 already in use
# Solution: Use different port
collaboration_config = {
    'enable_messaging': True,
    'websocket_port': 8766  # Use different port
}

# Or let system assign port
collaboration_config = {
    'enable_messaging': True,
    'websocket_port': 0  # Auto-assign available port
}
```

### Issue: High Memory Usage
```python
# Problem: Memory usage growing
# Solution: Configure limits and cleanup
collaboration_config = {
    'enable_messaging': True,
    'shared_workspace': True,
    'cleanup': {
        'message_retention_hours': 24,    # Keep messages for 24 hours
        'workspace_cleanup_interval': 3600,  # Clean every hour
        'max_workspace_files': 1000       # Limit files in workspace
    }
}
```

## Advanced Configuration

### High-Availability Setup
```python
# Redis cluster configuration
collaboration_config = {
    'enable_messaging': True,
    'redis_config': {
        'cluster_nodes': [
            'redis-1:6379',
            'redis-2:6379',
            'redis-3:6379'
        ],
        'cluster_mode': True,
        'health_check_interval': 30
    }
}
```

### Load Balancing
```python
# Multiple WebSocket servers
collaboration_config = {
    'enable_messaging': True,
    'websocket_servers': [
        'ws://localhost:8765',
        'ws://localhost:8766',
        'ws://localhost:8767'
    ],
    'load_balancing': {
        'strategy': 'round_robin',  # or 'least_connections'
        'health_check': True
    }
}
```

## Success Metrics

### Migration Success Criteria
- [ ] **Backwards Compatibility**: All existing tests pass unchanged
- [ ] **Performance**: <5% overhead for non-collaborative tasks
- [ ] **Functionality**: Basic collaboration features work as designed
- [ ] **Reliability**: 99.9% uptime for collaboration services
- [ ] **Documentation**: Migration process documented and validated

### Collaboration Effectiveness Metrics
- **Agent Discovery Time**: <1 second to find relevant agents
- **Message Latency**: <100ms end-to-end message delivery
- **Workspace Sync**: <500ms for file change propagation
- **Resource Efficiency**: <50% memory overhead for collaboration features

## Next Steps

After successful migration:

1. **Monitor Performance**: Track metrics for 1 week post-migration
2. **Optimize Workflows**: Identify opportunities for better collaboration patterns
3. **Scale Testing**: Test with larger numbers of concurrent agents
4. **Feature Enhancement**: Explore advanced collaboration features
5. **Documentation**: Document lessons learned and best practices

## Support & Resources

### Migration Support
- **Migration Script**: `scripts/migrate_to_collaborative.py` (automated migration)
- **Validation Tools**: `tools/validate_migration.py` (verify migration success)
- **Performance Benchmarks**: `benchmarks/collaboration_performance.py`

### Documentation
- **Integration Architecture**: `integration_architecture.md`
- **Compatibility Matrix**: `compatibility_matrix.md`
- **API Reference**: `docs/collaborative_orchestrator_api.md`

### Community
- **Migration Issues**: Report at `github.com/project/issues` with `migration` tag
- **Best Practices**: Share experiences in `discussions/migration-stories`
- **Performance Tips**: Community wiki at `wiki/performance-optimization`

---

**Migration Complete! 🎉**

You now have a collaboration-ready orchestrator that maintains 100% backwards compatibility while enabling powerful multi-agent coordination capabilities.
