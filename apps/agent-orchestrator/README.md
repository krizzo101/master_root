# Agent Orchestrator - Production-Ready Multi-Agent Framework

A battle-tested, production-ready framework for orchestrating parallel Claude agents with advanced features including dependency management, token pooling, quality gates, and intelligent escalation systems.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Core Components](#core-components)
- [Features](#features)
- [Documentation](#documentation)
- [Examples](#examples)
- [Testing](#testing)
- [Performance](#performance)

## 🎯 Overview

Agent Orchestrator is a comprehensive framework for managing multiple AI agents working in parallel to solve complex tasks. It provides intelligent task distribution, resource management, and coordination between agents with built-in quality control and escalation mechanisms.

### Key Capabilities

- **Parallel Execution**: Run up to 100+ agents simultaneously
- **Smart Dependencies**: Automatic task scheduling based on dependencies
- **🛡️ Advanced Validation**: Circular dependency detection and comprehensive error handling
- **Resource Management**: Token pooling and intelligent allocation
- **Quality Control**: Built-in quality gates and validation
- **Escalation System**: Automatic escalation for complex tasks
- **Monitoring**: Real-time performance and progress tracking

## 🏗️ Architecture

### System Overview

```mermaid
graph TB
    subgraph "User Layer"
        U[User Application]
    end

    subgraph "Orchestration Layer"
        GO[Generic Orchestrator]
        EO[Enhanced Orchestrator]
        ATM[Agent Team Manager]
    end

    subgraph "Resource Management"
        TP[Token Pool Manager]
        DTP[Dynamic Token Pool]
        STP[Shared Token Pool]
    end

    subgraph "Quality & Control"
        QG[Quality Gates]
        EM[Escalation Manager]
        AM[Agent Monitor]
    end

    subgraph "Agent Layer"
        A1[Agent 1]
        A2[Agent 2]
        A3[Agent 3]
        AN[Agent N]
    end

    subgraph "Storage"
        FS[File System]
        JSON[JSON Output]
        LOGS[Log Files]
    end

    U --> GO
    U --> EO
    U --> ATM

    GO --> TP
    EO --> DTP
    ATM --> STP

    GO --> QG
    EO --> EM
    ATM --> AM

    TP --> A1
    TP --> A2
    DTP --> A3
    STP --> AN

    QG --> EM
    EM --> ATM

    A1 --> FS
    A2 --> JSON
    A3 --> LOGS
    AN --> JSON

    style U fill:#e1f5fe
    style GO fill:#c8e6c9
    style EO fill:#c8e6c9
    style ATM fill:#c8e6c9
    style QG fill:#fff3e0
    style EM fill:#fff3e0
    style AM fill:#fff3e0
    style TP fill:#f3e5f5
    style DTP fill:#f3e5f5
    style STP fill:#f3e5f5
```

### Component Interaction Flow

```mermaid
sequenceDiagram
    participant User
    participant Orchestrator
    participant TokenPool
    participant QualityGate
    participant Agent
    participant Storage

    User->>Orchestrator: Submit Tasks
    Orchestrator->>Orchestrator: Analyze Dependencies
    Orchestrator->>TokenPool: Request Token
    TokenPool-->>Orchestrator: Assign Token

    loop For Each Task
        Orchestrator->>Agent: Execute Task
        Agent->>Agent: Process
        Agent-->>QualityGate: Submit Result
        QualityGate->>QualityGate: Validate

        alt Validation Passed
            QualityGate-->>Storage: Save Result
            QualityGate-->>Orchestrator: Task Complete
        else Validation Failed
            QualityGate-->>Orchestrator: Request Retry
            Orchestrator->>Agent: Retry Task
        end
    end

    Orchestrator-->>User: Return Results
```

### Task Execution Workflow

```mermaid
flowchart TD
    Start([Start]) --> Input[Receive Task Batch]
    Input --> Parse[Parse Tasks & Dependencies]
    Parse --> Build[Build Dependency Graph]
    Build --> Schedule[Schedule Tasks]

    Schedule --> Check{Tasks Available?}
    Check -->|Yes| Parallel[Execute in Parallel]
    Check -->|No| Wait[Wait for Dependencies]

    Parallel --> Token{Token Available?}
    Token -->|Yes| Assign[Assign to Agent]
    Token -->|No| Queue[Queue Task]

    Assign --> Execute[Agent Executes]
    Execute --> Quality{Quality Check}

    Quality -->|Pass| Save[Save Results]
    Quality -->|Fail| Escalate{Escalate?}

    Escalate -->|Yes| Senior[Senior Agent]
    Escalate -->|No| Retry[Retry Task]

    Senior --> Execute
    Retry --> Execute

    Save --> Update[Update Dependencies]
    Update --> Check

    Wait --> Check
    Queue --> Token

    Check -->|No More Tasks| Complete[Complete]
    Complete --> Output[Return Results]
    Output --> End([End])

    style Start fill:#e8f5e9
    style End fill:#ffebee
    style Quality fill:#fff3e0
    style Escalate fill:#fce4ec
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd apps/agent-orchestrator

# Install dependencies
pip install -r requirements.txt

# Add your Claude API tokens
python utils/add_tokens.py
```

### Basic Usage

```python
from src.generic_orchestrator import GenericOrchestrator, AgentTask
import asyncio
from pathlib import Path

async def main():
    # Initialize orchestrator
    orchestrator = GenericOrchestrator(
        output_dir=Path("./output"),
        max_parallel=5,
        use_optimizations=True
    )

    # Define tasks with dependencies
    tasks = [
        AgentTask(
            task_id="research",
            task_type="research",
            prompt="Research best practices for Python async programming"
        ),
        AgentTask(
            task_id="design",
            task_type="design",
            prompt="Design an async web server architecture",
            dependencies=["research"]
        ),
        AgentTask(
            task_id="implement",
            task_type="code",
            prompt="Implement the async web server",
            dependencies=["design"]
        )
    ]

    # Execute tasks
    results = await orchestrator.execute_batch(tasks)

    # Process results
    for task_id, result in results.items():
        print(f"Task {task_id}: {result['status']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### ExecutionPlan with Advanced Validation

**NEW**: Enhanced ExecutionPlan system with comprehensive validation:

```python
from execution_plan_template import ExecutionPlanBuilder
from execution_plan_schema import TaskType
from execution_plan_validation import CircularDependencyError

# Create validated ExecutionPlan
builder = ExecutionPlanBuilder("Production Pipeline")
builder.add_task("research", TaskType.RESEARCH_GENIUS, "Research requirements")
builder.add_task("design", TaskType.SOLUTION_ARCHITECT, "Create design",
                dependencies=["research"])
builder.add_task("implement", TaskType.DEVELOPMENT_SPECIALIST, "Build solution",
                dependencies=["design"])

try:
    plan = builder.build()  # ✅ Automatically validates for circular dependencies
    print(f"✅ Plan created with {len(plan.tasks)} tasks")

    # Execute with orchestrator
    orchestrator = GenericOrchestrator(output_dir=Path("./output"))
    results = await orchestrator.execute_batch(plan.tasks)

except CircularDependencyError as e:
    print(f"❌ Circular dependency detected: {e.dependency_chain}")
```

**Key Validation Features:**
- **Circular Dependency Detection**: Prevents infinite loops
- **Data Integrity**: Validates all task references
- **Flexible Modes**: Production validation or testing mode
- **Clear Error Messages**: Actionable error reporting
- **Performance Optimized**: Validates 100+ tasks in milliseconds

## 🔧 Core Components

### 1. Orchestrators

#### Generic Orchestrator (`src/generic_orchestrator.py`)
- Base orchestration functionality
- Dependency management
- Parallel execution control
- Basic error handling

#### Enhanced Orchestrator (`src/enhanced_orchestrator.py`)
- Advanced features on top of Generic Orchestrator
- Quality gates integration
- Escalation system
- Performance optimization

#### Agent Team Manager (`src/agent_team_manager.py`)
- Team-based agent management
- Role-based task assignment
- Inter-agent communication
- Collaborative problem solving

### 2. Token Management

#### Token Pool Types

```mermaid
graph LR
    subgraph "Token Pool Types"
        Static[Static Pool<br/>Fixed tokens]
        Dynamic[Dynamic Pool<br/>Auto-scaling]
        Shared[Shared Pool<br/>Multi-tenant]
    end

    Static --> RR[Round Robin]
    Dynamic --> AS[Auto Scale]
    Shared --> PQ[Priority Queue]

    style Static fill:#e3f2fd
    style Dynamic fill:#f3e5f5
    style Shared fill:#fff3e0
```

### 3. Quality Control

#### Quality Gates (`src/quality_gates.py`)
- Result validation
- Output format checking
- Error detection
- Automatic retry logic

### 4. Escalation System

```mermaid
stateDiagram-v2
    [*] --> TaskReceived
    TaskReceived --> InitialAttempt
    InitialAttempt --> QualityCheck

    QualityCheck --> Success: Pass
    QualityCheck --> Retry: Fail (< max retries)
    QualityCheck --> Escalate: Fail (>= max retries)

    Retry --> InitialAttempt
    Escalate --> SeniorAgent
    SeniorAgent --> QualityCheck

    Success --> [*]

    note right of Escalate
        Triggers when:
        - Max retries exceeded
        - Complexity threshold met
        - Manual escalation requested
    end note
```

## 📁 Directory Structure

```
agent-orchestrator/
├── src/                        # Core source code
│   ├── generic_orchestrator.py # Base orchestrator
│   ├── enhanced_orchestrator.py # Advanced orchestrator
│   ├── agent_team_manager.py   # Team management
│   ├── token_loader.py         # Token management
│   ├── dynamic_token_pool.py   # Dynamic token pool
│   ├── shared_token_pool.py    # Shared token pool
│   ├── quality_gates.py        # Quality control
│   ├── escalation_manager.py   # Escalation system
│   ├── agent_monitor.py        # Monitoring
│   ├── uuid_monitor.py         # UUID tracking
│   └── simple_async_system.py  # Async utilities
├── examples/                   # Example implementations
│   ├── simple_async_example.py
│   ├── quality_gate_examples.py
│   ├── escalation_demo.py
│   └── agent_team_manager_examples.py
├── tests/                      # Test suite
│   ├── test_*.py              # Unit tests
│   └── *.sh                   # Integration tests
├── scripts/                    # Utility scripts
│   ├── phase1_implementation.py
│   └── research_existing_apps.py
├── utils/                      # Utilities
│   └── add_tokens.py          # Token management
├── docs/                       # Documentation
│   ├── API_REFERENCE.md       # API documentation
│   ├── ARCHITECTURE.md        # Architecture details
│   ├── TUTORIALS.md           # Step-by-step guides
│   └── TROUBLESHOOTING.md     # Common issues
├── output/                     # Default output directory
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── QUICKSTART.md              # Quick start guide
├── run.py                     # Main entry point
└── main.py                    # Alternative entry point
```

## 🎯 Features

### Parallel Execution
- Run multiple agents simultaneously
- Configurable parallelism limits
- Automatic resource allocation
- Load balancing

### Dependency Management
- Directed acyclic graph (DAG) resolution
- Automatic task ordering
- Deadlock prevention
- Circular dependency detection

### Token Management
- Multiple pool strategies
- Fair allocation algorithms
- Priority-based assignment
- Dynamic scaling

### Quality Gates
- Configurable validation rules
- Automatic retry on failure
- Custom validators support
- Result formatting

### Escalation System
- Automatic complexity detection
- Senior agent assignment
- Fallback strategies
- Manual escalation options

### Monitoring & Logging
- Real-time progress tracking
- Performance metrics
- Detailed logging
- UUID-based tracing

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [API Reference](docs/API_REFERENCE.md) | Complete API documentation |
| [Architecture](docs/ARCHITECTURE.md) | System design details |
| [Tutorials](docs/TUTORIALS.md) | Step-by-step guides |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues & solutions |
| [Quality Gates Guide](docs/QUALITY_GATE_SYSTEM_DELIVERABLE.md) | Quality control system |
| [Escalation Guide](docs/ESCALATION_INTEGRATION_README.md) | Escalation system |
| [Token Pool Guide](docs/DYNAMIC_POOL_GUIDE.md) | Token management |
| [Team Manager Guide](docs/AGENT_TEAM_MANAGER_DELIVERABLE.md) | Team coordination |

## 🧪 Testing

### Run Tests

```bash
# Unit tests
python -m pytest tests/

# Integration tests
./tests/test_cli_spawning.sh
./tests/simple_test.sh

# Specific component tests
python tests/test_agent_team_manager.py
python tests/test_quality_gates.py
```

### Test Coverage Areas
- Core orchestration logic
- Dependency resolution
- Token allocation
- Quality validation
- Escalation triggers
- Error handling

## 📊 Performance

### Benchmarks

| Metric | Value | Notes |
|--------|-------|-------|
| Max Parallel Agents | 100+ | Limited by tokens |
| Task Throughput | 50-100/min | With 10 tokens |
| Average Latency | 10-30s | Per task |
| Memory Usage | <500MB | For 100 tasks |
| Success Rate | >95% | With retries |

### Optimization Tips

1. **Token Pool Size**: Match to expected parallelism
2. **Batch Size**: 10-50 tasks optimal
3. **Dependencies**: Minimize deep chains
4. **Quality Gates**: Balance thoroughness vs speed
5. **Monitoring**: Use for bottleneck identification

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Update documentation
5. Submit pull request

## 📄 License

[License information here]

## 🙏 Acknowledgments

Built with Claude API and inspired by modern orchestration patterns.
