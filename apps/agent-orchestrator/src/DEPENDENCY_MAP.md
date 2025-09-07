# Agent Orchestrator - Code Dependency Map

*Generated on: 2025-09-07 13:06:21*

## Overview
This document provides a comprehensive map of all code dependencies within the agent-orchestrator system, showing both internal module relationships and external library dependencies.

## Architecture Summary

The agent-orchestrator follows a layered architecture with clear separation of concerns:

1. **Core Orchestrator Layer** - Base orchestration functionality
2. **Enhancement Layers** - Extended features and capabilities  
3. **Specialized Modules** - Domain-specific functionality
4. **Support Systems** - Utility and infrastructure components

## Core Dependencies

### 1. Core Orchestrator Files

#### `generic_orchestrator.py` (Foundation)
- **Role**: Base orchestrator implementation
- **Internal Dependencies**: 
  - `token_loader.py` (TokenLoader)
  - `simple_async_system.py` (AsyncTask, AsyncQueue, AsyncTimer)
- **External Dependencies**: asyncio, json, logging, uuid, dataclasses, datetime, pathlib, typing
- **Exports**: GenericOrchestrator, AgentTask, TokenPool, DependencyManager, MessageBus

#### `enhanced_orchestrator.py` (Enhanced Features)
- **Role**: Adds quality gates and advanced dependency management
- **Internal Dependencies**:
  - `generic_orchestrator.py` (AgentTask, DependencyManager, GenericOrchestrator, MessageBus, TokenPool)
  - `quality_gates.py` (GateStatus, QualityGateManager, ValidationResult)
  - `agent_monitor.py` (AgentStatus, AgentStatusMonitor) - optional
- **External Dependencies**: asyncio, json, logging, os, sys, uuid, dataclasses, datetime, pathlib, typing

#### `collaborative_orchestrator.py` (Collaboration)
- **Role**: Real-time multi-agent collaboration
- **Internal Dependencies**:
  - `generic_orchestrator.py` (AgentTask, GenericOrchestrator)
  - `collaboration/` module components
- **External Dependencies**: asyncio, json, logging, uuid, dataclasses, datetime, pathlib, typing

#### `unified/unified_orchestrator.py` (Unified System)
- **Role**: Consolidates all orchestrator features with modular loading
- **Internal Dependencies**:
  - `generic_orchestrator.py` components
  - `unified/orchestrator_module.py` (ModuleConfig, ModuleRegistry, OrchestratorModule)
- **External Dependencies**: asyncio, json, logging, os, sys, uuid, dataclasses, datetime, enum, pathlib, typing

### 2. Support Systems

#### `token_loader.py`
- **Role**: Token management and distribution
- **Dependencies**: json, os, pathlib, typing
- **Used by**: All orchestrator implementations

#### `simple_async_system.py`
- **Role**: Lightweight async framework
- **Dependencies**: asyncio, logging, dataclasses, enum, typing
- **Used by**: generic_orchestrator.py

#### `quality_gates.py`
- **Role**: Basic validation system
- **Dependencies**: dataclasses, enum, typing
- **Used by**: enhanced_orchestrator.py, quality gates enhanced modules

#### `token_coordinator.py`
- **Role**: Cross-process token coordination
- **Dependencies**: asyncio, fcntl, hashlib, json, logging, os, socket, time, pathlib, typing

## Specialized Module Systems

### 3. Message Bus System (`message_bus/`)

**Architecture**: Hierarchical messaging system with Redis backend

#### Core Components:
- `core/message_types.py` - Message definitions and types
- `core/message_bus.py` - Redis-based message bus implementation
- `routing/message_router.py` - Message routing logic
- `client/agent_client.py` - Agent client interface
- `admin/admin_interface.py` - Administrative interface
- `gateway/websocket_gateway.py` - WebSocket gateway

#### Dependencies Flow:
```
message_types.py (base types)
    ↓
message_bus.py → routing/message_router.py
    ↓               ↓
client/agent_client.py ← admin/admin_interface.py → gateway/websocket_gateway.py
    ↓
simple_client.py
```

#### External Dependencies:
- `redis.asyncio` (Redis client)
- `asyncio`, `json`, `logging`, `ssl`, `uuid`, `gzip`, `time`

### 4. Persistence System (`persistence/`)

**Architecture**: PostgreSQL + Redis caching layer

#### Core Components:
- `models.py` - SQLAlchemy models and Pydantic schemas
- `database.py` - Database connection management
- `repositories.py` - Data access layer
- `query_engine.py` - Query optimization and caching
- `cache.py` - Redis caching implementation
- `backup.py` - Backup and recovery

#### Dependencies Flow:
```
models.py (base models)
    ↓
database.py → repositories.py → query_engine.py
    ↓              ↓               ↓
cache.py ←────────┴───────────────┘
    ↓
backup.py
```

#### External Dependencies:
- `asyncpg`, `sqlalchemy`, `redis.asyncio`
- `pydantic`, `asyncio`, `logging`, `contextlib`

### 5. Monitoring System (`monitoring/`)

**Architecture**: Real-time metrics collection and WebSocket broadcasting

#### Core Components:
- `metrics_collector.py` - Core metrics collection
- `realtime_monitor.py` - Real-time monitoring orchestrator
- `websocket_server.py` - WebSocket server for live updates
- `dashboard_server.py` - Dashboard web server
- `orchestrator_integration.py` - Integration with orchestrators

#### Dependencies Flow:
```
metrics_collector.py (central metrics hub)
    ↓
realtime_monitor.py → websocket_server.py
    ↓                     ↓
dashboard_server.py ←─────┘
    ↓
orchestrator_integration.py
```

#### External Dependencies:
- `psutil` (system metrics)
- `asyncio`, `json`, `logging`, `ssl`, `websockets`

### 6. Load Balancing System (`load_balancing/`)

**Architecture**: Intelligent task distribution and resource management

#### Core Components:
- `resource_monitor.py` - System resource monitoring
- `load_balancer.py` - Load balancing algorithms
- `task_scheduler.py` - Task scheduling logic
- `load_balancing_orchestrator.py` - Main orchestrator integration

#### Dependencies Flow:
```
resource_monitor.py (resource metrics)
    ↓
load_balancer.py → task_scheduler.py
    ↓                   ↓
load_balancing_orchestrator.py
```

#### External Dependencies:
- `psutil` (resource monitoring)
- `asyncio`, `logging`, `collections`, `dataclasses`, `enum`

### 7. Events System (`events/`)

**Architecture**: Event-driven communication and coordination

#### Core Components:
- `event_types.py` - Event definitions
- `event_bus.py` - Central event bus
- `event_processors.py` - Event processing logic
- `event_history.py` - Event persistence
- `notification_engine.py` - Notification system
- `coordination_events.py` - Coordination-specific events

#### Dependencies Flow:
```
event_types.py (base event types)
    ↓
event_bus.py (central hub)
    ↓
event_processors.py → event_history.py → notification_engine.py
    ↓
coordination_events.py
```

### 8. Collaboration System (`collaboration/`)

**Architecture**: Real-time collaboration and workspace management

#### Core Components:
- `change_tracker.py` - File change tracking
- `collaborative_filesystem.py` - Shared filesystem
- `workspace_manager.py` - Workspace management
- `sync_engine.py` - Synchronization logic
- `workspace_sdk.py` - Developer SDK
- `coordination_engine.py` - Agent coordination
- `collaboration_orchestrator.py` - Main orchestrator

#### Dependencies Flow:
```
change_tracker.py (base tracking)
    ↓
collaborative_filesystem.py → workspace_manager.py → sync_engine.py
    ↓                             ↓                     ↓
workspace_sdk.py ←───────────────┴─────────────────────┘
    ↓
coordination_engine.py → collaboration_orchestrator.py
```

### 9. Unified Module System (`unified/`)

**Architecture**: Modular orchestrator framework

#### Core Components:
- `orchestrator_module.py` - Base module interface
- `mcp_registry_builder.py` - MCP registry building
- `enhanced_agent_task.py` - Enhanced task definitions
- `collaboration_config.py` - Collaboration configuration
- `modules/enhanced_module.py` - Enhanced module implementation
- `modules/collaboration_module.py` - Collaboration module

### 10. Quality Gates Enhanced (`quality_gates_enhanced/`)

**Architecture**: Advanced quality validation and security

#### Core Components:
- `enhanced_quality_gate_manager.py` - Main quality gate manager
- `security_validator.py` - Security validation
- `compliance_checker.py` - Compliance checking
- `code_security_analyzer.py` - Code security analysis

#### Dependencies Flow:
```
security_validator.py → enhanced_quality_gate_manager.py
compliance_checker.py → enhanced_quality_gate_manager.py
code_security_analyzer.py → enhanced_quality_gate_manager.py
```

## External Library Dependencies

### Core Python Libraries
- `asyncio` - Asynchronous programming
- `json` - JSON serialization
- `logging` - Logging framework
- `uuid` - UUID generation
- `dataclasses` - Data class definitions
- `datetime` - Date/time handling
- `pathlib` - Path operations
- `typing` - Type hints
- `enum` - Enumerations
- `collections` - Data structures

### Database & Caching
- `asyncpg` - PostgreSQL async driver
- `sqlalchemy` - ORM and database toolkit
- `redis.asyncio` - Redis async client
- `pydantic` - Data validation

### System & Monitoring
- `psutil` - System resource monitoring
- `ssl` - SSL/TLS support
- `websockets` - WebSocket implementation

### Validation & Security
- `jsonschema` - JSON schema validation
- `networkx` - Graph algorithms (execution planning)

### Optional Dependencies
- `agent_monitor` - Agent monitoring (fallback handling)
- `practical_orchestrator` - Legacy orchestrator support

## Key Dependency Patterns

### 1. Layered Dependencies
- Core orchestrators depend on support systems
- Enhanced features extend core functionality
- Specialized modules are self-contained

### 2. Plugin Architecture
- Modules implement common interfaces
- Graceful degradation when optional components unavailable
- Configuration-driven feature loading

### 3. Event-Driven Communication
- Loose coupling between components
- Asynchronous message passing
- Centralized event coordination

### 4. Resource Management
- Token-based access control
- Load balancing and resource monitoring
- Connection pooling and caching

## Integration Points

### 1. Main Entry Point (`__init__.py`)
Exports core components:
- `GenericOrchestrator`, `AgentTask`, `TokenPool`, `DependencyManager`, `MessageBus`
- `TokenLoader`
- `SimpleAsyncExecutor`, `AsyncTask`, `AsyncQueue`, `AsyncTimer`

### 2. Cross-System Integration
- Enhanced orchestrator integrates monitoring
- Collaborative orchestrator uses collaboration system
- Unified orchestrator supports all features modularly
- Load balancing integrates with all orchestrator types

### 3. Configuration Systems
- Environment-based configuration
- File-based token management
- Dynamic module loading
- Feature toggles and graceful degradation

## Architectural Insights

### Strengths
1. **Modular Design**: Clear separation of concerns
2. **Extensibility**: Plugin-based architecture
3. **Scalability**: Async-first design with resource management
4. **Reliability**: Graceful degradation and error handling
5. **Observability**: Comprehensive monitoring and events

### Areas of Complexity
1. **Import Hierarchy**: Some circular dependencies handled with try/except
2. **Optional Dependencies**: Multiple fallback mechanisms
3. **Configuration**: Multiple configuration sources and formats
4. **Version Compatibility**: Legacy and modern orchestrator support

## Recommendations for Developers

### 1. When Adding New Features
- Follow the module interface pattern
- Implement graceful degradation
- Add comprehensive logging
- Include monitoring integration

### 2. When Modifying Core Components
- Consider backward compatibility
- Update all affected orchestrator types
- Test with optional dependencies disabled
- Verify token pool integration

### 3. When Debugging Dependencies
- Check import order and circular dependencies
- Verify optional dependency handling
- Review configuration loading
- Examine event flow and message routing

This dependency map provides a foundation for understanding the agent-orchestrator codebase and guides development decisions for maintaining the system's architectural integrity.
