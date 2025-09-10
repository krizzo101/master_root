# System Architecture - The Actual Truth

*Generated: 2025-08-24*
*This is the definitive documentation of what the system actually does*

## What This System Actually Is

A **multi-project knowledge management platform** that provides:
1. **Persistent memory** across Claude sessions using Neo4j + Qdrant
2. **Project-scoped isolation** preventing knowledge contamination between projects
3. **Dynamic instructions** replacing static config files with KB queries
4. **Semantic search** for intelligent file selection and context retrieval
5. **Code complexity analysis** for understanding and prioritizing code

## How It Actually Works - Step by Step

### 1. Knowledge Storage Flow
```
User provides content →
  Knowledge MCP tool stores in Neo4j →
    Embedding generated (384-dim) →
      Indexed in Qdrant for search →
        Linked to Project node for scoping
```

### 2. Agent Startup Flow
```
Agent starts in directory (e.g., /home/opsvi/master_root/apps/ACCF) →
  Queries KB for GLOBAL_INSTRUCTIONS →
    Queries KB for PROJECT_INSTRUCTIONS (matching path) →
      Queries KB for APP_INSTRUCTIONS (specific app) →
        Performs semantic search for relevant context →
          Combines all instructions: APP > PROJECT > GLOBAL priority
```

### 3. File Selection Flow (ACCF Gatekeeper)
```
Consult request with prompt →
  KB Gatekeeper generates embedding →
    Searches Qdrant knowledge_vectors collection →
      Extracts file paths from results →
        Returns RequestCard with files →
          Falls back to mock if KB unavailable
```

### 4. Project Intelligence Flow
```
Analyze codebase with AST →
  Calculate complexity metrics →
    Store as CODE_ANALYSIS in KB →
      Link to Project node →
        Enable queries like "find most complex code in project X"
```

## Current System State

### Neo4j Database
- **Total Knowledge**: 2,956 entries
- **Knowledge Types**:
  - CODE: 1,816 entries (actual source code)
  - CONFIGURATION: 339 entries (configs)
  - REFERENCE: 305 entries (documentation)
  - DOCUMENTATION: 230 entries
  - CODE_PATTERN: 102 entries
  - Instructions: 12 entries (GLOBAL/PROJECT/APP)
- **Projects**: 6 registered
- **Relationships**:
  - HAS_INSTRUCTION: 9
  - HAS_ANALYSIS: 3

### Qdrant Vector Database
- **knowledge_vectors**: 2,888 vectors (general knowledge)
- **instructions**: 12 vectors (dynamic instructions)
- **monitoring_vectors**: 0 vectors (reserved)

### File Locations
```
/home/opsvi/master_root/
├── apps/
│   ├── ACCF/                          # Consult suite with KB gatekeeper
│   │   ├── src/accf/tools/kb_gatekeeper.py
│   │   └── batch_ingest_kb_v2.py
│   ├── project-intelligence/          # Code analysis
│   │   └── src/project_intelligence/
│   │       ├── kb_project_scoped.py
│   │       └── hierarchical_scoping.py
│   └── kb-auto-docs/                  # Auto-documentation
│       └── src/
│           ├── auto_documentation.py
│           └── template_manager.py
└── libs/
    └── opsvi_mcp/servers/
        └── knowledge.py               # Knowledge MCP tool
```

## Key Components

### Knowledge MCP Tool (`knowledge.py`)
- `knowledge_store()`: Store with auto-embedding
- `knowledge_query()`: Query by type/search/recency
- `knowledge_update()`: Update confidence scores
- `knowledge_supersede()`: Replace outdated knowledge

### KB Gatekeeper (`kb_gatekeeper.py`)
- Extends AutoGenIntegration
- Generates embeddings for prompts
- Searches Qdrant for relevant files
- Returns RequestCard with intelligent selection

### Project Scoping (`kb_project_scoped.py`)
- Creates Project nodes in Neo4j
- Links knowledge to projects
- Enables scoped searches
- Prevents cross-project contamination

### Auto-Documentation (`auto_documentation.py`)
- Generates docs from live KB data
- Creates architecture diagrams
- Produces data flow visualizations
- Ensures docs match reality

### Template Manager (`template_manager.py`)
- Stores doc templates in KB
- Defines diagram generation rules
- Enables self-documenting system
- Tracks template effectiveness

## Critical Design Decisions

### Why 384-dimension embeddings?
- Balance between quality and performance
- Sufficient for semantic similarity
- Fast generation and search
- Model: sentence-transformers/all-MiniLM-L6-v2

### Why Neo4j + Qdrant?
- Neo4j: Relationships and graph traversal
- Qdrant: Fast vector similarity search
- Combined: Semantic + structural understanding

### Why project scoping?
- Prevents "find complex function" returning results from wrong project
- Enables multi-project development
- Maintains knowledge isolation
- Supports hierarchical organization

### Why dynamic instructions?
- Instructions evolve with system
- No static file drift
- Context-aware guidance
- Project-specific customization

## Validation Results

Running `validate_complete_system.py`:
- ✅ 25/25 checks passed (100%)
- ✅ KB connectivity verified
- ✅ Project structure intact
- ✅ Instructions loaded correctly
- ✅ Scoping working properly
- ✅ ACCF integration functional
- ✅ Embeddings synced
- ✅ Search functionality operational
- ✅ End-to-end flow validated

## What This System Is NOT

- ❌ NOT a traditional documentation system (it's live KB-generated)
- ❌ NOT a static configuration (it's dynamic from KB)
- ❌ NOT a single-project tool (it's multi-project scoped)
- ❌ NOT just vector search (it's graph + vector hybrid)
- ❌ NOT volatile memory (it persists across sessions)

## Next Evolution Steps

1. **Automatic Knowledge Decay**: Deprecate outdated knowledge based on usage
2. **Cross-Project Learning**: Share solutions while maintaining isolation
3. **Confidence Scoring**: Track what works and boost successful patterns
4. **Real-time Updates**: Auto-update docs as KB changes
5. **Causal Understanding**: Link errors to solutions with proven effectiveness

## The Truth About Documentation

Traditional documentation drifts from reality. This system generates documentation FROM reality. The KB is the single source of truth, and all documentation is a view into that truth.

When you ask "how does X work?", the answer comes from analyzing what X actually does in the KB, not from what someone wrote about X months ago.

**This is not documentation. This is introspection.**
