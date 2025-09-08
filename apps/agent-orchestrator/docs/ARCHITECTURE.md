# Agent Orchestrator - System Architecture

## Table of Contents
- [System Overview](#system-overview)
- [Component Architecture](#component-architecture)
- [Data Flow](#data-flow)
- [Design Patterns](#design-patterns)
- [Technology Stack](#technology-stack)
- [Security Architecture](#security-architecture)
- [Scalability & Performance](#scalability--performance)
- [Integration Points](#integration-points)
- [Deployment Architecture](#deployment-architecture)
- [Decision Records](#decision-records)

## System Overview

The Agent Orchestrator is a production-grade framework for parallel execution of AI agent tasks with real-time monitoring, quality gates, and comprehensive analytics. It supports both simple task orchestration and complex workflow management with checkpointing, resumption, and dashboard integration.

### High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        CLI[CLI Interface]
        API[REST API]
        Dashboard[Web Dashboard]
    end

    subgraph "Orchestration Layer"
        GO[GenericOrchestrator]
        EO[EnhancedOrchestrator]
        RO[ResumableOrchestrator]
    end

    subgraph "Execution Layer"
        TP[TokenPool]
        AM[Agent Manager]
        QG[Quality Gates]
        MC[Monitoring & Checkpointing]
    end

    subgraph "Storage Layer"
        FS[File System]
        PG[(PostgreSQL)]
        Redis[(Redis)]
    end

    subgraph "External Services"
        Claude[Claude API]
        OpenAI[OpenAI API]
        MCP[MCP Servers]
    end

    CLI --> GO
    API --> EO
    Dashboard --> RO

    GO --> AM
    EO --> QG
    RO --> MC

    AM --> TP
    QG --> TP
    MC --> FS

    TP --> Claude
    TP --> OpenAI

    EO --> PG
    EO --> Redis

    Dashboard <--> Redis
```

## Component Architecture

### Core Components

#### 1. Generic Orchestrator (`src/generic_orchestrator.py`)
**Responsibilities:**
- Task queue management and parallel execution
- Dependency resolution and scheduling
- Token pool management with multi-provider support
- Basic monitoring and logging
- Output collection and result aggregation

**Key Features:**
- Async/await architecture for concurrent execution
- Configurable parallelism limits
- Error handling and retry mechanisms
- Comprehensive logging with structured output

#### 2. Enhanced Orchestrator (`src/enhanced_orchestrator.py`)
**Responsibilities:**
- Advanced quality gates and validation
- Performance monitoring and metrics collection
- Database integration for persistence
- Workflow tracking and analytics
- Advanced error recovery

**Key Features:**
- Quality gate validation pipeline
- PostgreSQL integration for metrics storage
- Real-time performance monitoring
- Enhanced error reporting with context

#### 3. Resumable Orchestrator (`src/workflows/resumable_orchestrator.py`)
**Responsibilities:**
- Checkpoint creation and restoration
- Long-running workflow management
- Progress tracking and state persistence
- Failure recovery and partial completion handling

**Key Features:**
- Automatic checkpointing at configurable intervals
- State serialization and deserialization
- Progress reporting and ETA calculation
- Graceful shutdown and resumption

#### 4. Token Pool (`src/enhanced_token_pool.py`)
**Responsibilities:**
- Multi-provider API token management
- Load balancing across available tokens
- Rate limiting and quota management
- Token health monitoring

**Key Features:**
- Support for Claude and OpenAI APIs
- Automatic token rotation and failover
- Usage tracking and analytics
- Built-in rate limiting

#### 5. Session Analytics Engine (`src/session_analytics_engine.py`)
**Responsibilities:**
- Session log parsing and analysis
- Performance metrics extraction
- Conversation pattern recognition
- Cross-session analytics

**Key Features:**
- Real-time log parsing from .jsonl files
- Tool usage analytics and reporting
- File operation tracking
- Conversation flow analysis

### Supporting Components

#### Quality Gates System
- **Location**: `src/enhanced_quality_gates.py`
- **Purpose**: Validate task outputs against predefined criteria
- **Features**: Configurable validation rules, performance thresholds, content quality checks

#### Message Bus System
- **Location**: `src/message_bus/`
- **Purpose**: Inter-component communication and event distribution
- **Features**: Redis-based pub/sub, WebSocket real-time updates, event routing

#### Dashboard Backend
- **Location**: `production_dashboard.py`, `orchestrator_with_dashboard.py`
- **Purpose**: Real-time monitoring and control interface
- **Features**: WebSocket streaming, REST API, metrics aggregation, workflow visualization

## Data Flow

### Task Execution Flow

```mermaid
sequenceDiagram
    participant Client
    participant Orchestrator
    participant TokenPool
    participant Agent
    participant Storage
    participant Dashboard

    Client->>Orchestrator: Submit task batch
    Orchestrator->>Orchestrator: Parse dependencies
    Orchestrator->>Storage: Create checkpoint

    loop For each ready task
        Orchestrator->>TokenPool: Request token
        TokenPool->>Orchestrator: Provide token
        Orchestrator->>Agent: Execute task
        Agent->>Agent: Process with AI provider
        Agent->>Orchestrator: Return result
        Orchestrator->>Storage: Update checkpoint
        Orchestrator->>Dashboard: Stream progress
    end

    Orchestrator->>Client: Return aggregated results
```

### Dashboard Data Flow

```mermaid
graph LR
    subgraph "Data Sources"
        FS[File System Logs]
        DB[(Database Metrics)]
        Live[Live Orchestrator Events]
    end

    subgraph "Processing"
        Parser[Log Parser]
        Aggregator[Metrics Aggregator]
        StreamProcessor[Real-time Processor]
    end

    subgraph "Dashboard Components"
        WS[WebSocket Server]
        API[REST API]
        UI[Web UI]
    end

    FS --> Parser
    DB --> Aggregator
    Live --> StreamProcessor

    Parser --> WS
    Aggregator --> API
    StreamProcessor --> WS

    WS --> UI
    API --> UI
```

## Design Patterns

### 1. Plugin Architecture
- **Location**: Throughout `src/` directory
- **Purpose**: Extensible provider and processor system
- **Implementation**: Abstract base classes with concrete implementations for different AI providers

### 2. Factory Pattern
- **Location**: Token pool creation, orchestrator initialization
- **Purpose**: Dynamic object creation based on configuration
- **Implementation**: Factory methods for provider-specific instances

### 3. Observer Pattern
- **Location**: Dashboard integration, event system
- **Purpose**: Real-time updates and monitoring
- **Implementation**: Callback registration and event broadcasting

### 4. Command Pattern
- **Location**: Task execution system
- **Purpose**: Encapsulation of task execution logic
- **Implementation**: AgentTask dataclass with execution context

### 5. Strategy Pattern
- **Location**: Quality gates, chunking strategies
- **Purpose**: Pluggable algorithms and validation rules
- **Implementation**: Configurable strategy selection

### 6. Circuit Breaker Pattern
- **Location**: Token pool and API interactions
- **Purpose**: Fault tolerance and graceful degradation
- **Implementation**: Automatic failover and retry logic

## Technology Stack

### Core Technologies
- **Python 3.8+**: Primary runtime environment
- **asyncio**: Asynchronous programming foundation
- **aiohttp**: HTTP client/server for API interactions
- **WebSockets**: Real-time communication for dashboard

### Data Storage
- **PostgreSQL**: Metrics and analytics persistence
- **Redis**: Caching, pub/sub messaging, session storage
- **File System**: Checkpoints, logs, and output artifacts

### AI/ML Integration
- **Anthropic Claude API**: Primary AI provider
- **OpenAI API**: Secondary AI provider support
- **MCP (Model Context Protocol)**: Standardized AI integration

### Monitoring & Observability
- **Prometheus**: Metrics collection (optional)
- **Grafana**: Visualization and dashboards (optional)
- **Custom Dashboard**: Built-in real-time monitoring

### Development & Testing
- **pytest**: Unit and integration testing
- **pydantic**: Data validation and serialization
- **watchdog**: File system monitoring

### Deployment & Operations
- **Docker**: Containerization
- **docker-compose**: Multi-service deployment
- **systemd**: Service management (production)

## Security Architecture

### Authentication & Authorization
- **Token Management**: Secure storage and rotation of API tokens
- **Access Control**: Environment-based token isolation
- **Rate Limiting**: Built-in protection against abuse

### Data Protection
- **Encryption**: In-transit encryption for all API communications
- **Data Sanitization**: Automatic PII detection and masking
- **Audit Logging**: Comprehensive activity tracking

### Network Security
- **CORS Configuration**: Configurable cross-origin policies
- **Input Validation**: Comprehensive request validation
- **Secure Defaults**: Restrictive default configurations

### Operational Security
- **Resource Limits**: Memory and CPU constraints
- **Sandboxing**: Isolated execution environments
- **Monitoring**: Real-time security event detection

## Scalability & Performance

### Horizontal Scaling
- **Stateless Design**: All orchestrators are stateless for easy scaling
- **Database Sharding**: PostgreSQL partitioning support
- **Load Distribution**: Multi-token load balancing

### Performance Optimizations
- **Connection Pooling**: Reused connections for AI providers
- **Caching**: Redis-based result and session caching
- **Async Processing**: Non-blocking I/O throughout

### Resource Management
- **Memory Efficiency**: Streaming processing for large sessions
- **Token Optimization**: Intelligent chunking strategies
- **Garbage Collection**: Automatic cleanup of old workflows

### Monitoring & Alerting
- **Real-time Metrics**: Performance dashboards with <1s latency
- **Health Checks**: Automated service health monitoring
- **Alerting**: Configurable threshold-based notifications

## Integration Points

### External APIs
```mermaid
graph TB
    subgraph "Agent Orchestrator"
        Core[Core System]
    end

    subgraph "AI Providers"
        Claude[Anthropic Claude]
        OpenAI[OpenAI GPT]
        MCP[MCP Servers]
    end

    subgraph "Storage Systems"
        PG[(PostgreSQL)]
        Redis[(Redis Cache)]
        FS[File System]
    end

    subgraph "Monitoring"
        Prom[Prometheus]
        Graf[Grafana]
        Custom[Custom Dashboard]
    end

    Core --> Claude
    Core --> OpenAI
    Core --> MCP
    Core --> PG
    Core --> Redis
    Core --> FS
    Core --> Custom

    Custom --> Prom
    Prom --> Graf
```

### API Endpoints

#### REST API
- `GET /health` - System health check
- `GET /api/summary` - Workflow summary statistics
- `GET /api/metrics` - Performance metrics
- `GET /api/active-tasks` - Currently executing tasks
- `POST /inject_tasks` - Dynamic task injection

#### WebSocket Streams
- `/ws/logs` - Real-time log streaming
- `/ws/metrics` - Live performance metrics
- `/ws/workflows` - Workflow status updates

### File System Integration
- **Input**: Task definitions (JSON), session logs (JSONL)
- **Output**: Results, reports, analytics, checkpoints
- **Monitoring**: Real-time file system watching with `watchdog`

## Deployment Architecture

### Development Environment
```yaml
# Local development setup
services:
  - agent-orchestrator (development mode)
  - postgresql (local instance)
  - redis (local instance)
  - dashboard (development server)
```

### Production Environment
```yaml
# Production deployment via docker-compose
services:
  - agent-orchestrator (containerized)
  - postgresql (managed instance)
  - redis (managed instance)
  - nginx (reverse proxy)
  - prometheus (metrics)
  - grafana (visualization)
```

### Configuration Management
- **Environment Variables**: Runtime configuration
- **JSON Config Files**: Structured configuration
- **Docker Compose**: Service orchestration
- **Secrets Management**: Secure token storage

## Decision Records

### ADR-001: Async-First Architecture
**Decision**: Use asyncio throughout for all I/O operations
**Rationale**: Enables high concurrency with efficient resource usage
**Consequences**: Better scalability, more complex debugging

### ADR-002: Multi-Provider Token Support
**Decision**: Abstract token management to support multiple AI providers
**Rationale**: Vendor flexibility and improved reliability through redundancy
**Consequences**: Additional complexity, better fault tolerance

### ADR-003: Database-Backed Analytics
**Decision**: Use PostgreSQL for persistent metrics storage
**Rationale**: Rich query capabilities and data integrity
**Consequences**: Additional deployment complexity, powerful analytics

### ADR-004: WebSocket Real-Time Updates
**Decision**: Implement WebSocket streaming for dashboard updates
**Rationale**: Low-latency real-time monitoring requirements
**Consequences**: More complex client code, better user experience

### ADR-005: Checkpoint-Based Recovery
**Decision**: Implement comprehensive checkpointing system
**Rationale**: Long-running workflows need reliable recovery mechanisms
**Consequences**: Storage overhead, improved reliability

### ADR-006: Plugin-Based Extensibility
**Decision**: Use plugin architecture for processors and validators
**Rationale**: Enable easy extension without core modifications
**Consequences**: Additional abstraction layers, better maintainability

## Performance Characteristics

### Measured Performance
- **API Response Time**: <1ms for health endpoints, <10ms for metrics
- **Log Streaming**: 276,582 lines/s (56.5 MB/s) with 32KB chunks
- **WebSocket Stability**: 20+ concurrent clients at 60 msg/s
- **Multi-Workflow Support**: 15 concurrent workflows with 146+ req/s
- **Error Recovery**: 100% graceful handling of malformed data/overload

### Scalability Limits
- **Max Parallel Tasks**: Configurable, tested up to 15
- **Token Pool Size**: Up to 20 tokens per pool
- **WebSocket Connections**: 500+ concurrent connections
- **Database Performance**: Optimized for 10k+ sessions

### Resource Requirements
- **Memory**: ~100MB base, +10MB per active workflow
- **CPU**: Single-core sufficient for 5 parallel tasks
- **Storage**: ~1GB for logs and checkpoints per 1000 sessions
- **Network**: Minimal bandwidth requirements (~1MB/s typical)

---

This architecture documentation represents the current state of the Agent Orchestrator system as of September 2025. The system demonstrates production-grade patterns including comprehensive monitoring, fault tolerance, and scalability considerations while maintaining extensibility for future enhancements.
