# Unified Context System - Database Architecture & Data Models

<!-- cspell:words varchar timestamptz tsvector hypertables hypertable asyncpg -->

## Overview
This document provides comprehensive Mermaid diagrams describing the database architecture, data models, relationships, and interfaces for the Unified Context System. The system integrates PostgreSQL (with TimescaleDB), Neo4j, and Redis to provide a complete development intelligence platform.

---

## 1. High-Level System Architecture

```mermaid
graph TB
    subgraph "User Interfaces"
        UI1[Chat Dashboard<br/>Flask Web UI]
        UI2[Claude Monitor<br/>Rich Terminal UI]
        UI3[Project Context<br/>MCP Tools]
        UI4[pgAdmin<br/>Database Admin]
    end

    subgraph "API Layer"
        API1[Unified Query API<br/>GraphQL/REST]
        API2[WebSocket Stream<br/>Real-time Events]
        API3[MCP Protocol<br/>FastMCP Server]
    end

    subgraph "Data Processing"
        PROC1[Dual-Write Adapter<br/>Migration Support]
        PROC2[Correlation Engine<br/>Chat/Code Analysis]
        PROC3[Ingestion Pipeline<br/>Multi-source ETL]
        PROC4[Relationship Extractor<br/>Neo4j Sync]
    end

    subgraph "Storage Layer"
        DB1[(PostgreSQL<br/>TimescaleDB<br/>Primary Data)]
        DB2[(Neo4j<br/>Graph Database<br/>Relationships)]
        DB3[(Redis<br/>Cache & PubSub<br/>Real-time)]
        DB4[(SQLite<br/>Legacy<br/>Migration)]
    end

    subgraph "Data Sources"
        SRC1[Chat Logs<br/>Real-time]
        SRC2[.proj-intel<br/>Code Analysis]
        SRC3[Claude Monitor<br/>System Metrics]
        SRC4[IDE Context<br/>VS Code Bridge]
        SRC5[Git History<br/>Version Control]
    end

    %% Connections
    UI1 --> API1
    UI2 --> API2
    UI3 --> API3
    UI4 --> DB1

    API1 --> PROC1
    API2 --> PROC1
    API3 --> PROC1

    PROC1 --> DB1
    PROC1 --> DB4
    PROC2 --> DB1
    PROC3 --> DB1
    PROC4 --> DB2

    DB1 <--> DB2
    DB1 --> DB3

    SRC1 --> PROC3
    SRC2 --> PROC3
    SRC3 --> PROC3
    SRC4 --> PROC3
    SRC5 --> PROC3

    %% Styling
    classDef database fill:#e1f5fe
    classDef processing fill:#f3e5f5
    classDef api fill:#e8f5e8
    classDef ui fill:#fff3e0
    classDef source fill:#fce4ec

    class DB1,DB2,DB3,DB4 database
    class PROC1,PROC2,PROC3,PROC4 processing
    class API1,API2,API3 api
    class UI1,UI2,UI3,UI4 ui
    class SRC1,SRC2,SRC3,SRC4,SRC5 source
```

---

## 2. PostgreSQL Database Schema & Relationships

```mermaid
erDiagram
    %% Core Tables
    context_items {
        uuid id PK
        varchar source_type
        varchar source_id
        varchar entity_type
        timestamptz timestamp
        timestamptz timestamp_end
        timestamptz ingested_at
        text title
        text content
        varchar content_hash
        text summary
        varchar project_id
        text file_path
        int line_start
        int line_end
        varchar function_name
        varchar class_name
        varchar actor_id
        varchar actor_type
        varchar session_id
        varchar severity
        text[] tags
        jsonb metrics
        jsonb source_data
        tsvector search_vector
        varchar neo4j_node_id
    }

    chat_sessions {
        varchar id PK
        timestamptz started_at
        timestamptz ended_at
        varchar user_id
        text project_path
        int total_tokens
        numeric total_cost
        varchar model_used
        jsonb session_metadata
        text[] primary_files
        int error_count
        int tool_use_count
        varchar neo4j_node_id
    }

    code_elements {
        uuid id PK
        text file_path
        varchar element_type
        varchar element_name
        text signature
        text docstring
        int line_start
        int line_end
        numeric complexity_score
        numeric test_coverage
        jsonb dependencies
        varchar language
        timestamptz last_modified
        varchar content_hash
        jsonb proj_intel_data
        tsvector search_vector
        varchar neo4j_node_id
    }

    %% Chat/Intel Correlation Tables
    code_context {
        int id PK
        varchar session_id
        timestamptz timestamp
        text file_path
        jsonb symbols
        varchar content_hash
        varchar change_type
        varchar chat_session_id FK
        uuid code_element_id FK
        varchar neo4j_node_id
        numeric relevance_score
        int discussion_depth
    }

    agent_usage {
        int id PK
        varchar session_id
        timestamptz timestamp
        varchar agent_class
        varchar agent_token
        text task_description
        int execution_time_ms
        int tokens_used
        boolean success
        text[] file_paths
        jsonb methods_invoked
        jsonb context_data
        varchar neo4j_node_id
    }

    symbol_references {
        int id PK
        varchar message_id
        varchar session_id
        varchar symbol_name
        varchar symbol_type
        text file_path
        int line_number
        varchar reference_type
        timestamptz timestamp
    }

    file_activity {
        int id PK
        varchar session_id
        timestamptz timestamp
        text file_path
        varchar action
        varchar tool_used
        jsonb functions_affected
        jsonb classes_affected
        varchar before_hash
        varchar after_hash
    }

    %% TimescaleDB Hypertables
    monitoring_metrics {
        timestamptz time PK
        varchar source PK
        varchar metric_name PK
        numeric metric_value
        varchar container_id PK
        varchar agent_token PK
        int process_id
        jsonb labels
        jsonb metadata
    }

    ide_context_snapshots {
        uuid id PK
        timestamptz timestamp
        text active_file
        text selected_text
        jsonb cursor_position
        int error_count
        int warning_count
        jsonb diagnostics
        text project_root
        text[] open_files
        text[] recent_files
        varchar session_id
        tsvector search_vector
    }

    %% Relationships
    chat_sessions ||--o{ context_items : "session_id"
    chat_sessions ||--o{ code_context : "chat_session_id"
    chat_sessions ||--o{ agent_usage : "session_id"
    chat_sessions ||--o{ symbol_references : "session_id"
    chat_sessions ||--o{ file_activity : "session_id"
    chat_sessions ||--o{ ide_context_snapshots : "session_id"

    code_elements ||--o{ code_context : "code_element_id"
    code_elements ||--o{ context_items : "file_path"

    context_items ||--o{ monitoring_metrics : "timestamp"
```

---

## 3. Neo4j Graph Database Schema

```mermaid
graph LR
    subgraph "Node Types"
        K[Knowledge<br/>knowledge_id<br/>content<br/>embedding<br/>confidence]
        S[Session<br/>session_id<br/>started_at<br/>user_id<br/>project]
        C[CodeElement<br/>element_id<br/>file_path<br/>element_type<br/>name]
        F[File<br/>path<br/>language<br/>last_modified]
        E[Error<br/>error_id<br/>type<br/>message<br/>first_seen]
        A[Agent<br/>agent_token<br/>agent_type]
        CONT[Container<br/>container_id<br/>name<br/>image]
        T[Task<br/>task_id<br/>description<br/>status]
    end

    subgraph "Relationship Types"
        K -.->|RELATED_TO| K
        K -.->|DERIVED_FROM| S
        S -.->|DISCUSSED| F
        S -.->|REFERENCED| C
        S -.->|ENCOUNTERED| E
        S -.->|USED_AGENT| A
        C -.->|CALLS| C
        C -.->|BELONGS_TO| F
        C -.->|DEPENDS_ON| C
        F -.->|IMPORTS| F
        E -.->|OCCURRED_IN| F
        E -.->|CAUSED_BY| C
        E -.->|FIXED_IN| S
        CONT -.->|RUNS| S
        CONT -.->|USES_AGENT| A
        A -.->|EXECUTED_TASK| T
    end

    %% Styling
    classDef node fill:#e3f2fd
    classDef relationship fill:#f1f8e9

    class K,S,C,F,E,A,CONT,T node
```

---

## 4. Data Flow & Ingestion Pipelines

```mermaid
flowchart TD
    subgraph "Data Sources"
        DS1[Chat Messages<br/>Real-time Stream]
        DS2[.proj-intel Files<br/>JSONL Batch]
        DS3[System Metrics<br/>TimeSeries]
        DS4[IDE Events<br/>WebSocket]
        DS5[Git Commits<br/>Webhook]
    end

    subgraph "Ingestion Layer"
        IL1[Chat Log Parser<br/>Extract entities]
        IL2[ProjectIntel Reader<br/>Byte-offset JSONL]
        IL3[Metrics Collector<br/>Aggregation]
        IL4[Context Bridge<br/>IDE Integration]
        IL5[Git Hook Handler<br/>Commit Analysis]
    end

    subgraph "Processing Engine"
        PE1[Correlation Engine<br/>Symbol Extraction]
        PE2[Dual-Write Adapter<br/>Migration Support]
        PE3[Entity Extractor<br/>NLP Processing]
        PE4[Relationship Builder<br/>Graph Creation]
        PE5[Embedding Generator<br/>Vector Search]
    end

    subgraph "Storage Layer"
        SL1[(PostgreSQL<br/>context_items<br/>TimescaleDB)]
        SL2[(Neo4j<br/>Relationships<br/>Graph Queries)]
        SL3[(Redis<br/>Real-time Cache<br/>Pub/Sub)]
        SL4[(SQLite<br/>Legacy Support<br/>Dual-Write)]
    end

    subgraph "Query Layer"
        QL1[Unified API<br/>GraphQL/REST]
        QL2[MCP Tools<br/>Semantic Queries]
        QL3[WebSocket Stream<br/>Live Updates]
        QL4[Materialized Views<br/>Aggregations]
    end

    %% Data Flow
    DS1 --> IL1 --> PE1 --> PE2 --> SL1
    DS2 --> IL2 --> PE3 --> PE2 --> SL1
    DS3 --> IL3 --> PE2 --> SL1
    DS4 --> IL4 --> PE2 --> SL1
    DS5 --> IL5 --> PE3 --> PE2 --> SL1

    PE1 --> PE4 --> SL2
    PE3 --> PE5 --> SL1
    PE2 --> SL4

    SL1 --> SL3
    SL2 --> SL3

    SL1 --> QL1
    SL2 --> QL1
    SL3 --> QL3
    SL1 --> QL4

    QL1 --> QL2

    %% Styling
    classDef source fill:#ffebee
    classDef ingestion fill:#e8f5e8
    classDef processing fill:#fff3e0
    classDef storage fill:#e1f5fe
    classDef query fill:#f3e5f5

    class DS1,DS2,DS3,DS4,DS5 source
    class IL1,IL2,IL3,IL4,IL5 ingestion
    class PE1,PE2,PE3,PE4,PE5 processing
    class SL1,SL2,SL3,SL4 storage
    class QL1,QL2,QL3,QL4 query
```

---

## 5. API Interfaces & Service Architecture

```mermaid
graph TB
    subgraph "Client Applications"
        APP1[Chat Dashboard<br/>React/Flask]
        APP2[Claude Monitor<br/>Rich TUI]
        APP3[VS Code Extension<br/>Context Bridge]
        APP4[MCP Clients<br/>Claude Code]
    end

    subgraph "API Gateway"
        GW[Unified Gateway<br/>Rate Limiting<br/>Authentication]
    end

    subgraph "Service Layer"
        SVC1[Context API<br/>GET /api/context/*<br/>POST /api/context/search]
        SVC2[Session API<br/>GET /api/sessions/*<br/>WebSocket /ws/sessions]
        SVC3[Code Intelligence API<br/>GET /api/code/*<br/>GET /api/dependencies]
        SVC4[Monitoring API<br/>GET /api/metrics<br/>GET /api/containers]
        SVC5[MCP Protocol<br/>Semantic Tools<br/>FastMCP Server]
        SVC6[GraphQL API<br/>Unified Schema<br/>Subscriptions]
    end

    subgraph "Business Logic"
        BL1[Correlation Engine<br/>Symbol Tracking<br/>Change Detection]
        BL2[Query Optimizer<br/>Multi-DB Queries<br/>Caching Strategy]
        BL3[Real-time Processor<br/>Event Streaming<br/>WebSocket Manager]
        BL4[Embedding Service<br/>Vector Search<br/>Semantic Similarity]
    end

    subgraph "Data Access Layer"
        DAL1[PostgreSQL Adapter<br/>Connection Pool<br/>Query Builder]
        DAL2[Neo4j Adapter<br/>Graph Queries<br/>Relationship API]
        DAL3[Redis Adapter<br/>Cache Manager<br/>Pub/Sub Handler]
        DAL4[Migration Adapter<br/>Dual-Write Support<br/>SQLite Fallback]
    end

    %% Connections
    APP1 --> GW
    APP2 --> GW
    APP3 --> GW
    APP4 --> GW

    GW --> SVC1
    GW --> SVC2
    GW --> SVC3
    GW --> SVC4
    GW --> SVC5
    GW --> SVC6

    SVC1 --> BL1
    SVC2 --> BL3
    SVC3 --> BL2
    SVC4 --> BL2
    SVC5 --> BL1
    SVC6 --> BL2

    BL1 --> DAL1
    BL2 --> DAL1
    BL2 --> DAL2
    BL3 --> DAL3
    BL4 --> DAL1

    BL1 --> DAL4
    BL2 --> DAL4

    %% Styling
    classDef client fill:#e8f5e8
    classDef gateway fill:#fff3e0
    classDef service fill:#e3f2fd
    classDef business fill:#f3e5f5
    classDef data fill:#fce4ec

    class APP1,APP2,APP3,APP4 client
    class GW gateway
    class SVC1,SVC2,SVC3,SVC4,SVC5,SVC6 service
    class BL1,BL2,BL3,BL4 business
    class DAL1,DAL2,DAL3,DAL4 data
```

---

## 6. Migration & Dual-Write Strategy

```mermaid
sequenceDiagram
    participant App as Application
    participant DW as Dual-Write Adapter
    participant PG as PostgreSQL
    participant SQ as SQLite (Legacy)
    participant N4J as Neo4j
    participant Cache as Redis Cache

    Note over App,Cache: Phase 1: Dual-Write Implementation

    App->>DW: write_code_context(data)

    par PostgreSQL Write
        DW->>PG: INSERT INTO code_context
        PG-->>DW: success (id: 123)
    and SQLite Write (Fallback)
        DW->>SQ: INSERT INTO code_context
        Note over SQ: May fail gracefully<br/>if table doesn't exist
        SQ-->>DW: success/failure
    end

    DW->>N4J: Extract relationships
    N4J-->>DW: Graph nodes created

    DW->>Cache: Invalidate cached data
    Cache-->>DW: Cache cleared

    DW-->>App: PostgreSQL ID returned

    Note over App,Cache: Phase 2: Read Migration

    App->>DW: query_code_context(session_id)
    DW->>PG: SELECT with JOINs
    PG-->>DW: Enhanced results with JSONB
    DW-->>App: Rich correlation data

    Note over App,Cache: Phase 3: Legacy Deprecation

    App->>DW: write_code_context(data)
    DW->>PG: INSERT (PostgreSQL only)
    PG-->>DW: success
    Note over SQ: SQLite writes disabled
    DW-->>App: Success
```

---

## 7. Performance Optimization & Indexing Strategy

```mermaid
graph TB
    subgraph "TimescaleDB Hypertables"
        HT1[context_items<br/>Partitioned by timestamp<br/>1-day chunks]
        HT2[monitoring_metrics<br/>Partitioned by time<br/>1-hour chunks]
        HT3[ide_context_snapshots<br/>Partitioned by timestamp<br/>1-hour chunks]
    end

    subgraph "PostgreSQL Indexes"
        IDX1[B-Tree Indexes<br/>• timestamp DESC<br/>• session_id<br/>• file_path]
        IDX2[GIN Indexes<br/>• JSONB fields<br/>• Text arrays<br/>• Full-text search]
        IDX3[Partial Indexes<br/>• WHERE file_path IS NOT NULL<br/>• WHERE source_type = 'chat']
    end

    subgraph "Materialized Views"
        MV1[hourly_token_usage<br/>Aggregated metrics<br/>Refresh every hour]
        MV2[daily_file_activity<br/>File touch patterns<br/>Refresh daily]
        MV3[hot_symbols_view<br/>Popular symbols<br/>Refresh every 15min]
    end

    subgraph "Neo4j Optimization"
        N4J1[Node Indexes<br/>• knowledge_id<br/>• session_id<br/>• file_path]
        N4J2[Composite Indexes<br/>• (type, name)<br/>• (session, timestamp)]
        N4J3[Full-text Indexes<br/>• content search<br/>• code search]
    end

    subgraph "Redis Caching Strategy"
        CACHE1[Query Result Cache<br/>TTL: 5 minutes<br/>LRU eviction]
        CACHE2[Session State Cache<br/>TTL: 1 hour<br/>Real-time updates]
        CACHE3[Hot Data Cache<br/>Frequently accessed<br/>symbols, files, contexts]
    end

    subgraph "Connection Pooling"
        POOL1[PostgreSQL Pool<br/>Min: 5, Max: 20<br/>asyncpg for async ops]
        POOL2[Neo4j Pool<br/>Min: 2, Max: 10<br/>Bolt protocol]
        POOL3[Redis Pool<br/>Connection per worker<br/>Pub/Sub dedicated]
    end

    %% Performance Flow
    HT1 --> IDX1
    HT2 --> IDX1
    HT3 --> IDX1

    IDX1 --> MV1
    IDX2 --> MV2
    IDX3 --> MV3

    MV1 --> CACHE1
    MV2 --> CACHE1
    MV3 --> CACHE2

    N4J1 --> CACHE3
    N4J2 --> CACHE3
    N4J3 --> CACHE3

    POOL1 --> CACHE1
    POOL2 --> CACHE2
    POOL3 --> CACHE3

    %% Styling
    classDef hypertable fill:#e1f5fe
    classDef index fill:#e8f5e8
    classDef view fill:#fff3e0
    classDef neo4j fill:#f3e5f5
    classDef cache fill:#fce4ec
    classDef pool fill:#e0f2f1

    class HT1,HT2,HT3 hypertable
    class IDX1,IDX2,IDX3 index
    class MV1,MV2,MV3 view
    class N4J1,N4J2,N4J3 neo4j
    class CACHE1,CACHE2,CACHE3 cache
    class POOL1,POOL2,POOL3 pool
```

---

## 8. Real-time Event Processing

```mermaid
sequenceDiagram
    participant IDE as VS Code
    participant Bridge as Context Bridge
    participant Ingest as Ingestion Pipeline
    participant PG as PostgreSQL
    participant Redis as Redis PubSub
    participant WS as WebSocket Server
    participant UI as Dashboard UI

    Note over IDE,UI: Real-time Context Updates

    IDE->>Bridge: File changed event
    Bridge->>Ingest: Process IDE context

    par Database Write
        Ingest->>PG: INSERT ide_context_snapshot
        PG-->>Ingest: Snapshot saved
    and Event Broadcasting
        Ingest->>Redis: PUBLISH context:file_changed
        Redis-->>WS: Event received
        WS->>UI: WebSocket message
        UI-->>UI: Update dashboard
    and Correlation Processing
        Ingest->>Ingest: Extract symbols/references
        Ingest->>PG: UPDATE correlation tables
        PG-->>Ingest: Correlations updated
    end

    Note over IDE,UI: Chat Message Processing

    UI->>Ingest: New chat message

    par Store Message
        Ingest->>PG: INSERT context_items
        PG-->>Ingest: Message stored
    and Real-time Correlation
        Ingest->>Ingest: Analyze code references
        Ingest->>PG: INSERT code_context
        Ingest->>PG: INSERT symbol_references
        PG-->>Ingest: Correlations saved
    and Live Updates
        Ingest->>Redis: PUBLISH chat:new_message
        Redis-->>WS: Broadcast to all clients
        WS->>Bridge: Update IDE context
        WS->>UI: Update chat display
    end

    Note over IDE,UI: Background Processing

    loop Every 15 minutes
        Ingest->>PG: REFRESH MATERIALIZED VIEW hot_symbols_view
        Ingest->>Redis: PUBLISH analytics:updated
        Redis-->>UI: Refresh dashboard metrics
    end
```

---

## Summary

This comprehensive database architecture provides:

1. **Unified Data Storage**: PostgreSQL as single source of truth with TimescaleDB for time-series
2. **Graph Relationships**: Neo4j for complex correlations and impact analysis
3. **Real-time Processing**: Redis pub/sub for live updates and caching
4. **Migration Support**: Dual-write pattern for seamless SQLite transition
5. **Performance Optimization**: Hypertables, materialized views, and strategic indexing
6. **API Flexibility**: REST, GraphQL, WebSocket, and MCP protocol support
7. **Correlation Intelligence**: Advanced chat/code correlation with JSONB queries

The system is designed for high performance, scalability, and rich analytical capabilities across all development intelligence sources.
