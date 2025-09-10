# Hecaton System Architecture Diagrams

## 1. Directory Structure Overview

```mermaid
graph TD
    subgraph "Hecaton Root"
        root["/apps/hecaton/"]

        subgraph "Source Code"
            src["/src/hecaton/"]
            agents["/agents/"]
            core["/core/"]
            orchestration["/orchestration/"]
            execution["/execution/"]
            messaging["/messaging/"]
            monitoring["/monitoring/"]
            resources["/resources/"]
            config_src["/config/"]
            utils["/utils/"]
        end

        subgraph "Configuration"
            config["/config/"]
            dev["/development/"]
            prod["/production/"]
            staging["/staging/"]
        end

        subgraph "Documentation"
            docs["/docs/"]
            api_docs["/api/"]
            arch["/architecture/"]
            guides["/guides/"]
            diagrams["/diagrams/"]
        end

        subgraph "Runtime"
            runtime["/runtime/"]
            checkpoints["/checkpoints/"]
            outputs["/outputs/"]
            worktrees["/worktrees/"]
        end

        subgraph "Testing"
            tests["/tests/"]
            unit["/unit/"]
            integration["/integration/"]
            e2e["/e2e/"]
            perf["/performance/"]
        end

        root --> src
        src --> agents
        src --> core
        src --> orchestration
        src --> execution
        src --> messaging
        src --> monitoring
        src --> resources
        src --> config_src
        src --> utils

        root --> config
        config --> dev
        config --> prod
        config --> staging

        root --> docs
        docs --> api_docs
        docs --> arch
        docs --> guides
        docs --> diagrams

        root --> runtime
        runtime --> checkpoints
        runtime --> outputs
        runtime --> worktrees

        root --> tests
        tests --> unit
        tests --> integration
        tests --> e2e
        tests --> perf
    end
```

## 2. Core Models and Relationships

```mermaid
classDiagram
    class Agent {
        <<abstract>>
        +String id
        +String name
        +List~String~ capabilities
        +DateTime created_at
        +List task_history
        +execute(task: Dict) Dict
        +log_task(task, result)
        +get_capabilities() List
        +get_info() Dict
    }

    class BaseAgent {
        <<interface>>
        +execute(task)
        +log_task()
    }

    class CodeAgent {
        +language: String
        +frameworks: List
        +execute_code_task()
        +analyze_code()
        +refactor()
    }

    class ResearchAgent {
        +sources: List
        +execute_research()
        +analyze_data()
        +synthesize()
    }

    class AgentRegistry {
        -Dict agents
        -Dict agent_classes
        +register_agent_type(type, class)
        +create_agent(type, name)
        +get_agent(id)
        +list_agents()
        +remove_agent(id)
    }

    class AgentStatus {
        <<enumeration>>
        IDLE
        RUNNING
        COMPLETED
        ERROR
        PAUSED
    }

    class TokenPool {
        -List tokens
        -Queue available_tokens
        -Dict token_usage
        +acquire() String
        +release(token)
        +expand(new_tokens)
        +get_stats() Dict
    }

    class SecureTokenPool {
        -encrypted_tokens: List
        -rotation_interval: int
        +rotate_tokens()
        +validate_token(token)
        +encrypt_token(token)
        +decrypt_token(token)
    }

    class WorktreeManager {
        +base_path: Path
        +repo_path: Path
        -Dict worktrees
        +create_worktree(name, branch)
        +cleanup_worktree(name)
        +list_worktrees() List
    }

    class MessageBroker {
        -Queue messages
        -Dict subscribers
        +publish(message)
        +subscribe(topic, handler)
        +process_messages()
    }

    class Message {
        +String id
        +String type
        +String sender
        +String recipient
        +Dict payload
        +DateTime timestamp
    }

    Agent <|-- CodeAgent
    Agent <|-- ResearchAgent
    BaseAgent <|.. Agent

    AgentRegistry "1" --> "*" Agent : manages
    Agent --> AgentStatus : has

    TokenPool <|-- SecureTokenPool
    SecureTokenPool <|-- ExpandableTokenPool

    Agent --> TokenPool : uses
    Agent --> WorktreeManager : uses
    Agent --> MessageBroker : communicates via
    MessageBroker --> Message : handles
```

## 3. Orchestrator Architecture

```mermaid
graph TB
    subgraph "Orchestration Layer"
        HO[HecatonOrchestrator]
        EO[EnhancedOrchestrator]
        SO[SelfImprovingOrchestrator]
        LGO[LangGraphOrchestrator]

        HO --> |inherits| EO
        EO --> |inherits| SO
        HO --> |uses| LGO
    end

    subgraph "Execution Layer"
        HE[HeadlessExecutor]
        OHE[OptimizedHeadlessExecutor]
        RCE[RealClaudeExecutor]
        ORCE[OptimizedRealClaudeExecutor]

        HE --> |optimized by| OHE
        RCE --> |optimized by| ORCE
    end

    subgraph "Agent Management"
        AR[AgentRegistry]
        AP[AgentProfile]
        AEO[AgentEnvironmentOptimizer]
        DAS[DynamicAgentSpawner]

        AR --> |profiles| AP
        AEO --> |spawns| DAS
    end

    subgraph "Resource Management"
        TP[TokenPool]
        STP[SecureTokenPool]
        WM[WorktreeManager]

        TP --> |secured by| STP
    end

    subgraph "Support Systems"
        MB[MessageBroker]
        EH[ErrorHandler]
        PM[PerformanceMonitor]
        DL[DebugLogger]
        ST[SessionTracker]
    end

    HO --> AR
    HO --> TP
    HO --> WM
    HO --> MB
    HO --> EH
    HO --> PM

    EO --> HE
    SO --> ORCE

    RCE --> ST
    RCE --> DL
```

## 4. Functional Code Map - Agent Lifecycle

```mermaid
sequenceDiagram
    participant User
    participant CLI as HecatonCLI
    participant Orch as HecatonOrchestrator
    participant Reg as AgentRegistry
    participant Agent
    participant Token as TokenPool
    participant Work as WorktreeManager
    participant Exec as ClaudeExecutor
    participant Monitor as PerformanceMonitor

    User->>CLI: hecaton run "task"
    CLI->>Orch: initialize(task)

    Note over Orch: Setup Phase
    Orch->>Token: initialize_pool()
    Orch->>Work: setup_workspace()
    Orch->>Reg: initialize_registry()

    Note over Orch: Agent Selection
    Orch->>Orch: _auto_select_agents(task)
    Orch->>Reg: create_agent(type, name)
    Reg->>Agent: new Agent()
    Reg-->>Orch: agent_instance

    Note over Orch: Task Distribution
    loop For each agent
        Orch->>Token: acquire()
        Token-->>Orch: token
        Orch->>Work: create_worktree(agent_id)
        Work-->>Orch: worktree_path
        Orch->>Agent: assign_task(task_subset)
    end

    Note over Agent: Parallel Execution
    par Agent 1
        Agent->>Exec: execute_headless(prompt, token)
        Exec->>Monitor: start_tracking()
        Exec-->>Agent: result_1
        Agent->>Monitor: log_metrics()
    and Agent 2
        Agent->>Exec: execute_headless(prompt, token)
        Exec->>Monitor: start_tracking()
        Exec-->>Agent: result_2
        Agent->>Monitor: log_metrics()
    and Agent N
        Agent->>Exec: execute_headless(prompt, token)
        Exec->>Monitor: start_tracking()
        Exec-->>Agent: result_n
        Agent->>Monitor: log_metrics()
    end

    Note over Orch: Result Synthesis
    Agent-->>Orch: all_results
    Orch->>Orch: synthesize_results()

    Note over Orch: Cleanup
    Orch->>Token: release_all()
    Orch->>Work: cleanup_worktrees()
    Orch->>Monitor: generate_report()

    Orch-->>CLI: final_result
    CLI-->>User: display_output
```

## 5. Command Factory Pattern

```mermaid
classDiagram
    class ClaudeCommandFactory {
        +create_command(task, profile, complexity)
        +optimize_for_headless(command)
        +add_safety_checks(command)
        +build_environment(profile)
    }

    class AgentProfile {
        <<enumeration>>
        RESEARCH
        CODING
        TESTING
        DOCUMENTATION
        REVIEW
    }

    class TaskComplexity {
        <<enumeration>>
        SIMPLE
        MODERATE
        COMPLEX
        EXTREME
    }

    class PermissionMode {
        <<enumeration>>
        BYPASS_PERMISSIONS
        ACCEPT_EDITS
        DEFAULT
        PLAN
    }

    class CommandConfig {
        +prompt: String
        +permission_mode: PermissionMode
        +output_format: String
        +working_dir: Path
        +env_vars: Dict
        +safety_checks: List
    }

    ClaudeCommandFactory --> AgentProfile : uses
    ClaudeCommandFactory --> TaskComplexity : evaluates
    ClaudeCommandFactory --> PermissionMode : sets
    ClaudeCommandFactory --> CommandConfig : creates

    class ClaudeProcess {
        +process: subprocess.Popen
        +stdout_thread: Thread
        +stderr_thread: Thread
        +start()
        +terminate()
        +get_output()
    }

    class RealClaudeExecutor {
        -token_pool: TokenPool
        -active_processes: Dict
        +execute_task(task, token)
        +monitor_process(process_id)
        +handle_errors(error)
    }

    CommandConfig --> ClaudeProcess : configures
    ClaudeProcess --> RealClaudeExecutor : managed by
```

## 6. Error Handling and Recovery Flow

```mermaid
stateDiagram-v2
    [*] --> Idle

    Idle --> TaskReceived: receive_task()

    TaskReceived --> Validating: validate_task()

    Validating --> Invalid: validation_failed
    Validating --> Preparing: validation_passed

    Invalid --> ErrorHandling

    Preparing --> Executing: resources_ready
    Preparing --> ErrorHandling: resource_error

    Executing --> Processing: agent_running
    Processing --> Monitoring: track_progress()

    Monitoring --> Success: task_completed
    Monitoring --> Timeout: timeout_exceeded
    Monitoring --> Failed: execution_error

    Timeout --> ErrorHandling
    Failed --> ErrorHandling

    ErrorHandling --> Retrying: can_retry
    ErrorHandling --> Cleanup: max_retries_exceeded

    Retrying --> Preparing: retry_attempt

    Success --> ResultProcessing
    ResultProcessing --> Cleanup

    Cleanup --> Idle: resources_released

    note right of ErrorHandling
        - Log error details
        - Capture stack trace
        - Notify monitoring
        - Determine retry strategy
    end note

    note right of Cleanup
        - Release tokens
        - Clean worktrees
        - Save checkpoints
        - Generate reports
    end note
```

## 7. Data Flow Architecture

```mermaid
graph LR
    subgraph "Input Layer"
        UI[User Input]
        API[API Request]
        CLI[CLI Command]
    end

    subgraph "Processing Pipeline"
        PP[Prompt Processor]
        TC[Task Classifier]
        TD[Task Decomposer]

        PP --> TC
        TC --> TD
    end

    subgraph "Agent Layer"
        AS[Agent Selector]
        AQ[Agent Queue]
        AE[Agent Executor]

        AS --> AQ
        AQ --> AE
    end

    subgraph "Execution Environment"
        TP[Token Pool]
        WT[Worktree]
        CE[Claude Engine]

        TP --> CE
        WT --> CE
    end

    subgraph "Result Processing"
        RC[Result Collector]
        RS[Result Synthesizer]
        RV[Result Validator]

        RC --> RS
        RS --> RV
    end

    subgraph "Output Layer"
        Report[Report Generator]
        Metrics[Metrics Logger]
        Response[Response Builder]
    end

    UI --> PP
    API --> PP
    CLI --> PP

    TD --> AS
    AE --> TP
    AE --> WT

    CE --> RC
    RV --> Report
    RV --> Metrics
    RV --> Response
```

## 8. Performance Monitoring System

```mermaid
classDiagram
    class PerformanceMonitor {
        -metrics: Dict
        -thresholds: Dict
        +start_tracking(task_id)
        +stop_tracking(task_id)
        +log_metric(name, value)
        +get_metrics() Dict
        +generate_report() Report
    }

    class TaskMetrics {
        +task_id: String
        +start_time: DateTime
        +end_time: DateTime
        +token_usage: Int
        +api_calls: Int
        +error_count: Int
        +retry_count: Int
        +success: Boolean
    }

    class SessionTracker {
        +session_id: String
        +start_time: DateTime
        +tasks: List~TaskMetrics~
        +add_task(task)
        +get_session_stats()
        +export_session()
    }

    class DebugLogger {
        +log_level: String
        +output_file: Path
        +log(level, message)
        +log_exception(exception)
        +flush()
    }

    class ClaudeSessionMonitor {
        +session_id: String
        +log_path: Path
        +parse_logs()
        +extract_metrics()
        +analyze_errors()
        +generate_insights()
    }

    PerformanceMonitor --> TaskMetrics : tracks
    SessionTracker --> TaskMetrics : aggregates
    SessionTracker --> PerformanceMonitor : uses
    DebugLogger --> ClaudeSessionMonitor : feeds
    ClaudeSessionMonitor --> PerformanceMonitor : reports to
```

## 9. Multi-Agent Coordination Pattern

```mermaid
graph TD
    subgraph "Orchestrator"
        O[Main Orchestrator]
        O --> TS[Task Splitter]
        O --> AS[Agent Selector]
        O --> QM[Queue Manager]
    end

    subgraph "Agent Pool"
        A1[Research Agent]
        A2[Code Agent]
        A3[Test Agent]
        A4[Review Agent]
        A5[Doc Agent]
    end

    subgraph "Shared Resources"
        TP[Token Pool<br/>15 tokens]
        WM[Worktree Manager<br/>Isolated branches]
        MB[Message Broker<br/>Inter-agent comm]
    end

    subgraph "Execution Contexts"
        C1[Context 1<br/>Research]
        C2[Context 2<br/>Implementation]
        C3[Context 3<br/>Testing]
        C4[Context 4<br/>Review]
        C5[Context 5<br/>Documentation]
    end

    TS --> A1
    TS --> A2
    TS --> A3
    TS --> A4
    TS --> A5

    A1 --> C1
    A2 --> C2
    A3 --> C3
    A4 --> C4
    A5 --> C5

    A1 --> TP
    A2 --> TP
    A3 --> TP
    A4 --> TP
    A5 --> TP

    A1 --> WM
    A2 --> WM
    A3 --> WM
    A4 --> WM
    A5 --> WM

    A1 <--> MB
    A2 <--> MB
    A3 <--> MB
    A4 <--> MB
    A5 <--> MB

    C1 --> |Results| QM
    C2 --> |Results| QM
    C3 --> |Results| QM
    C4 --> |Results| QM
    C5 --> |Results| QM

    QM --> O
```

## Usage Notes

These diagrams represent the Hecaton multi-agent orchestration system architecture:

1. **Directory Structure**: Shows the complete project organization
2. **Core Models**: Class relationships and inheritance hierarchy
3. **Orchestrator Architecture**: Component interactions and dependencies
4. **Agent Lifecycle**: Sequence of operations from task receipt to completion
5. **Command Factory**: Pattern for creating optimized Claude commands
6. **Error Handling**: State machine for error recovery and retries
7. **Data Flow**: Pipeline from input to output
8. **Performance Monitoring**: Metrics collection and analysis system
9. **Multi-Agent Coordination**: Parallel execution with shared resources

Each diagram can be rendered using any Mermaid-compatible viewer or documentation system.
