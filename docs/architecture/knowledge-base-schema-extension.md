# Knowledge Base Schema Extension Plan
## For Enhanced SDLC Agent Orchestration

### Current Schema Analysis

#### Existing Structure
- **Knowledge Node**: Basic storage with string-based context field
- **Properties**: id, type, content, context (STRING), confidence_score, tags, usage counts
- **Relationships**: RELATED_TO, USED_KNOWLEDGE
- **Limitations**:
  - Context stored as JSON string (not queryable)
  - No SDLC phase tracking
  - Missing agent orchestration metadata
  - No versioning or evolution tracking
  - Limited relationship types

### Proposed Extensions

#### 1. New Node Types

```cypher
// Agent execution tracking
CREATE (ae:AgentExecution {
  execution_id: STRING (indexed),
  agent_type: STRING (indexed),
  task_description: STRING,
  start_time: DATETIME,
  end_time: DATETIME,
  duration_minutes: FLOAT,
  status: STRING, // 'success', 'failure', 'timeout'
  checkpoint_count: INTEGER,
  worktree_id: STRING,
  error_message: STRING,
  tokens_used: INTEGER,
  model_used: STRING
})

// SDLC Phase representation
CREATE (sp:SDLCPhase {
  phase_id: STRING (indexed),
  phase_name: STRING, // 'discovery', 'design', 'development', etc.
  project_name: STRING (indexed),
  started_at: DATETIME,
  completed_at: DATETIME,
  gate_status: STRING,
  artifacts_produced: LIST
})

// Reusable workflow patterns
CREATE (wp:WorkflowPattern {
  pattern_id: STRING (indexed),
  pattern_name: STRING,
  pattern_type: STRING, // 'orchestration', 'compensation', 'parallel'
  description: STRING,
  implementation: STRING, // Code/config
  success_rate: FLOAT,
  avg_execution_time: FLOAT
})

// Performance metrics aggregation
CREATE (am:AgentMetrics {
  metric_id: STRING (indexed),
  agent_type: STRING (indexed),
  period: STRING, // 'daily', 'weekly', 'monthly'
  total_executions: INTEGER,
  success_count: INTEGER,
  failure_count: INTEGER,
  timeout_count: INTEGER,
  avg_duration_minutes: FLOAT,
  p95_duration_minutes: FLOAT,
  total_tokens_used: INTEGER
})
```

#### 2. Enhanced Knowledge Node Properties

```cypher
// Extend existing Knowledge node
ALTER Knowledge ADD PROPERTIES {
  // SDLC Integration
  sdlc_phase: STRING (indexed),
  agent_types: LIST, // Which agents can use this

  // Execution characteristics
  execution_time_minutes: FLOAT,
  parallel_capable: BOOLEAN,
  checkpoint_enabled: BOOLEAN,
  requires_human_review: BOOLEAN,

  // Structured context (replace string context)
  architecture_pattern: STRING,
  performance_metrics: MAP, // Proper map instead of JSON string
  error_patterns: LIST,
  resource_requirements: MAP,

  // Versioning
  version: INTEGER,
  version_date: DATETIME,
  deprecation_date: DATETIME,
  replacement_id: STRING,

  // Quality metrics
  reliability_score: FLOAT, // 0-1 based on success/failure ratio
  complexity_score: INTEGER, // 1-10
  reusability_score: FLOAT // 0-1
}
```

#### 3. New Relationship Types

```cypher
// Workflow dependencies
CREATE (k1:Knowledge)-[:DEPENDS_ON {
  dependency_type: STRING, // 'required', 'optional'
  order: INTEGER
}]->(k2:Knowledge)

// Compensation patterns (Saga)
CREATE (k1:Knowledge)-[:COMPENSATES {
  compensation_type: STRING, // 'rollback', 'forward_recovery'
  trigger_condition: STRING
}]->(k2:Knowledge)

// Parallel execution
CREATE (k1:Knowledge)-[:PARALLELIZES_WITH {
  max_parallel: INTEGER,
  isolation_level: STRING // 'worktree', 'container', 'none'
}]->(k2:Knowledge)

// Workflow triggering
CREATE (k1:Knowledge)-[:TRIGGERS {
  trigger_type: STRING, // 'on_success', 'on_failure', 'always'
  condition: STRING
}]->(k2:Knowledge)

// Version evolution
CREATE (k1:Knowledge)-[:SUPERSEDES {
  migration_notes: STRING,
  breaking_changes: BOOLEAN
}]->(k2:Knowledge)

// Phase relationships
CREATE (k:Knowledge)-[:BELONGS_TO_PHASE]->(sp:SDLCPhase)
CREATE (ae:AgentExecution)-[:EXECUTED_IN]->(sp:SDLCPhase)
CREATE (ae:AgentExecution)-[:USED_KNOWLEDGE]->(k:Knowledge)
CREATE (wp:WorkflowPattern)-[:IMPLEMENTS]->(k:Knowledge)
```

### Implementation Plan

#### Phase 1: Schema Migration (Day 1)
```python
# scripts/migrate_knowledge_schema.py

import neo4j
from datetime import datetime

def migrate_schema(driver):
    """Add new properties and indexes"""

    with driver.session() as session:
        # Create indexes
        session.run("""
            CREATE INDEX knowledge_phase IF NOT EXISTS
            FOR (k:Knowledge) ON (k.sdlc_phase)
        """)

        session.run("""
            CREATE INDEX knowledge_reliability IF NOT EXISTS
            FOR (k:Knowledge) ON (k.reliability_score)
        """)

        # Migrate existing context strings to structured data
        session.run("""
            MATCH (k:Knowledge)
            WHERE k.context IS NOT NULL
            SET k.context_legacy = k.context,
                k.context_migrated_at = datetime()
            REMOVE k.context
        """)

        # Calculate reliability scores
        session.run("""
            MATCH (k:Knowledge)
            WHERE k.success_count IS NOT NULL
              AND k.failure_count IS NOT NULL
            SET k.reliability_score =
                CASE
                    WHEN k.success_count + k.failure_count = 0 THEN 0.5
                    ELSE toFloat(k.success_count) /
                         (k.success_count + k.failure_count)
                END
        """)
```

#### Phase 2: Helper Functions (Day 2)
```python
# libs/opsvi_knowledge/enhanced_store.py

class EnhancedKnowledgeStore:
    def store_with_structure(
        self,
        knowledge_type: str,
        content: str,
        sdlc_phase: str = None,
        agent_types: list = None,
        performance_metrics: dict = None,
        parallel_capable: bool = False,
        checkpoint_enabled: bool = False,
        dependencies: list = None
    ):
        """Store knowledge with proper structure"""

        query = """
        CREATE (k:Knowledge {
            knowledge_id: $id,
            knowledge_type: $type,
            content: $content,
            sdlc_phase: $phase,
            agent_types: $agents,
            performance_metrics: $metrics,
            parallel_capable: $parallel,
            checkpoint_enabled: $checkpoint,
            created_at: datetime(),
            version: 1
        })
        """

        # Create dependency relationships
        if dependencies:
            for dep in dependencies:
                self.create_dependency(knowledge_id, dep)

        return knowledge_id

    def create_workflow_pattern(
        self,
        pattern_name: str,
        pattern_type: str,
        implementation: str,
        related_knowledge: list
    ):
        """Create reusable workflow pattern"""

        pattern_id = f"pattern_{pattern_name}_{datetime.now().isoformat()}"

        query = """
        CREATE (wp:WorkflowPattern {
            pattern_id: $id,
            pattern_name: $name,
            pattern_type: $type,
            implementation: $impl,
            created_at: datetime()
        })
        """

        # Link to knowledge entries
        for kid in related_knowledge:
            self.link_pattern_to_knowledge(pattern_id, kid)
```

#### Phase 3: Query Templates (Day 3)
```python
# libs/opsvi_knowledge/queries.py

class KnowledgeQueries:

    @staticmethod
    def get_phase_knowledge(phase: str, min_reliability: float = 0.7):
        """Get all knowledge for an SDLC phase"""
        return """
        MATCH (k:Knowledge)
        WHERE k.sdlc_phase = $phase
          AND k.reliability_score >= $min_reliability
        RETURN k
        ORDER BY k.reliability_score DESC
        """

    @staticmethod
    def get_parallel_workflows(max_duration: int = 10):
        """Find workflows that can run in parallel"""
        return """
        MATCH (k1:Knowledge)-[p:PARALLELIZES_WITH]->(k2:Knowledge)
        WHERE k1.execution_time_minutes <= $max_duration
          AND k2.execution_time_minutes <= $max_duration
          AND k1.parallel_capable = true
          AND k2.parallel_capable = true
        RETURN k1, p, k2
        """

    @staticmethod
    def get_compensation_chain(workflow_id: str):
        """Get compensation workflow for failures"""
        return """
        MATCH path = (k:Knowledge {knowledge_id: $workflow_id})
                     -[:COMPENSATES*]->(compensation:Knowledge)
        RETURN path
        ORDER BY length(path)
        """

    @staticmethod
    def get_agent_performance(agent_type: str, period: str = 'daily'):
        """Get agent performance metrics"""
        return """
        MATCH (am:AgentMetrics)
        WHERE am.agent_type = $agent_type
          AND am.period = $period
        RETURN am
        ORDER BY am.metric_id DESC
        LIMIT 30
        """
```

#### Phase 4: Validation & Constraints (Day 4)
```cypher
// Add constraints to ensure data quality

// Unique constraints
CREATE CONSTRAINT unique_knowledge_id IF NOT EXISTS
FOR (k:Knowledge) REQUIRE k.knowledge_id IS UNIQUE;

CREATE CONSTRAINT unique_execution_id IF NOT EXISTS
FOR (ae:AgentExecution) REQUIRE ae.execution_id IS UNIQUE;

// Property existence constraints
CREATE CONSTRAINT knowledge_must_have_type IF NOT EXISTS
FOR (k:Knowledge) REQUIRE k.knowledge_type IS NOT NULL;

CREATE CONSTRAINT execution_must_have_status IF NOT EXISTS
FOR (ae:AgentExecution) REQUIRE ae.status IS NOT NULL;

// Value constraints
CREATE CONSTRAINT valid_confidence_score IF NOT EXISTS
FOR (k:Knowledge) REQUIRE k.confidence_score >= 0 AND k.confidence_score <= 1;

CREATE CONSTRAINT valid_phase_name IF NOT EXISTS
FOR (sp:SDLCPhase) REQUIRE sp.phase_name IN [
  'discovery', 'design', 'planning', 'development',
  'testing', 'deployment', 'production', 'postmortem'
];
```

### Migration Checklist

- [ ] Backup existing Neo4j database
- [ ] Run schema migration script
- [ ] Migrate existing context strings to structured properties
- [ ] Create new indexes
- [ ] Add constraints
- [ ] Update knowledge store functions
- [ ] Update query functions
- [ ] Test with sample data
- [ ] Update documentation
- [ ] Train existing knowledge entries with new properties

### Benefits

1. **Better Querying**: Can query by SDLC phase, agent type, performance metrics
2. **Workflow Management**: Track dependencies, compensations, parallel execution
3. **Performance Tracking**: Monitor agent and pattern performance over time
4. **Version Control**: Track knowledge evolution and deprecation
5. **Reliability**: Calculate and use reliability scores for better decision making
6. **Reusability**: Identify and reuse successful workflow patterns

### Example Usage

```python
# Store orchestration pattern
store.store_with_structure(
    knowledge_type="WORKFLOW",
    content="Parallel agent orchestration for SDLC discovery",
    sdlc_phase="discovery",
    agent_types=["research", "requirements", "analysis"],
    performance_metrics={
        "avg_duration_minutes": 8.5,
        "success_rate": 0.92,
        "parallel_agents": 5
    },
    parallel_capable=True,
    checkpoint_enabled=True,
    dependencies=["kb-001", "kb-002"]
)

# Query for parallel workflows
parallel_workflows = session.run(
    KnowledgeQueries.get_parallel_workflows(max_duration=10)
)

# Get compensation chain for failed workflow
compensation = session.run(
    KnowledgeQueries.get_compensation_chain("workflow-dev-001")
)
```

This enhanced schema will provide the foundation for sophisticated SDLC automation with proper tracking, querying, and evolution of knowledge over time.
