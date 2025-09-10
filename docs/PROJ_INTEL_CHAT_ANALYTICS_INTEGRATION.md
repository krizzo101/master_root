# Project Intelligence + Chat Analytics Integration Design

## Executive Summary

This design document outlines the comprehensive integration of `.proj-intel/` project intelligence data with the existing chat analytics dashboard to create a unified development intelligence platform that correlates conversations with code evolution.

## Current State Analysis

### .proj-intel/ Data Structure

The project intelligence system provides rich, indexed data about the codebase:

#### Core Data Files
- **project_analysis.jsonl** (9.9MB): Primary JSONL with metadata, collectors, and collector items
- **file_elements.jsonl** (2.7MB): Detailed file-level metrics (functions, classes, imports)
- **agent_architecture.jsonl** (1.3MB): Agent/class discovery with methods and docstrings
- **symbol_index.json** (4.4MB): O(1) symbol → file/offset mapping
- **reverse_index.json** (1MB): O(1) path → JSONL byte ranges mapping

#### Available Collectors (12 types)
1. **FileElementsCollector**: Per-file functions, classes, imports with content hash
2. **AgentArchitectureCollector**: Discovered agents/classes with methods
3. **EntryPointsCollector**: CLI/module entry points
4. **DependenciesCollector**: Import graph and cycles
5. **ApiEndpointsCollector**: HTTP endpoints (FastAPI/Flask)
6. **DataModelsCollector**: Pydantic/SQLAlchemy models
7. **ConfigEnvCollector**: Config files and env vars
8. **TestsTopologyCollector**: Test files and target mapping
9. **DepsExtendedCollector**: Third-party dependencies
10. **QualityQuickCollector**: Metrics/complexity/lint
11. **CallGraphCollector**: Function calls and imports
12. **ChangesetCollector**: Added/removed/modified files

#### Key Tool: proj_intel_reader.py
- Implements proper byte-offset reading strategy
- Provides streaming access without memory overload
- Actions: read-bytes, read-by-path, read-collector, file-elements, agents

### Current Chat Analytics

The dashboard (`/libs/opsvi-monitoring/opsvi_monitoring/chat_analytics/`) provides:
- Response time analysis
- Tool usage metrics
- Session summaries (AI-powered)
- Activity patterns visualization
- SQLite database at `chat_logs.db`

Currently only checks if `.proj-intel/` exists but doesn't use the data.

## Integration Architecture

### 1. Data Correlation Layer

Create a new module: `libs/opsvi-monitoring/opsvi_monitoring/chat_analytics/intelligence/`

```python
intelligence/
├── __init__.py
├── correlator.py         # Main correlation engine
├── code_context.py       # Code context extraction
├── change_tracker.py     # Track code changes during sessions
├── agent_analyzer.py     # Agent usage correlation
└── symbol_tracker.py     # Symbol discussion tracking
```

### 2. Enhanced Database Schema

Add new tables to `chat_logs.db`:

```sql
-- Code context for chat sessions
CREATE TABLE code_context (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    timestamp DATETIME,
    file_path TEXT,
    symbols JSON,          -- Functions/classes discussed
    content_hash TEXT,     -- From file_elements
    change_type TEXT       -- added/modified/deleted
);

-- Agent architecture usage
CREATE TABLE agent_usage (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    timestamp DATETIME,
    agent_class TEXT,
    file_path TEXT,
    methods_invoked JSON,
    context JSON
);

-- Symbol references in chat
CREATE TABLE symbol_references (
    id INTEGER PRIMARY KEY,
    message_id TEXT,
    session_id TEXT,
    symbol_name TEXT,
    symbol_type TEXT,      -- function/class/variable
    file_path TEXT,
    line_number INTEGER,
    reference_type TEXT    -- mentioned/modified/created/deleted
);

-- File activity correlation
CREATE TABLE file_activity (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    timestamp DATETIME,
    file_path TEXT,
    action TEXT,           -- read/write/edit/delete
    tool_used TEXT,
    functions_affected JSON,
    classes_affected JSON,
    before_hash TEXT,
    after_hash TEXT
);
```

### 3. Real-time Correlation Engine

```python
class ProjectIntelligenceCorrelator:
    """Correlates chat activity with project intelligence data."""

    def __init__(self):
        self.reader = ProjectIntelReader()
        self.db = sqlite3.connect('chat_logs.db')
        self.symbol_index = self._load_symbol_index()
        self.file_cache = {}

    def process_message(self, message):
        """Process a chat message for code references."""
        # Extract file paths mentioned
        file_paths = self._extract_file_paths(message)

        # Extract symbols (functions, classes)
        symbols = self._extract_symbols(message)

        # Correlate with project intelligence
        context = self._build_code_context(file_paths, symbols)

        # Track changes if tools were used
        if self._has_code_modification(message):
            self._track_code_changes(message, context)

        return context

    def _extract_symbols(self, message):
        """Extract code symbols from message using symbol_index."""
        symbols = []
        for symbol in self.symbol_index:
            if symbol in message['content']:
                symbols.append({
                    'name': symbol,
                    'locations': self.symbol_index[symbol]
                })
        return symbols
```

### 4. Enhanced Dashboard Features

#### New API Endpoints

```python
@app.route('/api/code-evolution/<session_id>')
def api_code_evolution(session_id):
    """Track how code evolved during a session."""
    # Returns timeline of file changes with before/after metrics

@app.route('/api/symbol-discussion/<symbol_name>')
def api_symbol_discussion(symbol_name):
    """Find all chat discussions about a symbol."""
    # Returns messages mentioning the symbol with context

@app.route('/api/agent-utilization')
def api_agent_utilization():
    """Analyze which agents are most discussed/modified."""
    # Correlates agent_architecture with chat activity

@app.route('/api/hot-files')
def api_hot_files():
    """Identify files with most chat activity."""
    # Combines file_elements with chat references

@app.route('/api/complexity-impact/<session_id>')
def api_complexity_impact(session_id):
    """Analyze complexity changes during session."""
    # Uses QualityQuickCollector data
```

#### New Visualizations

1. **Code Evolution Timeline**
   - Shows file modifications over session time
   - Displays function/class count changes
   - Highlights complexity increases/decreases

2. **Symbol Discussion Heatmap**
   - Visual map of most discussed code elements
   - Color-coded by discussion frequency
   - Clickable to see chat context

3. **Agent Architecture Explorer**
   - Interactive graph of agent relationships
   - Shows which agents were discussed/modified
   - Links to relevant chat segments

4. **Dependency Impact Graph**
   - Visualizes import graph changes
   - Shows ripple effects of modifications
   - Identifies potential breaking changes

5. **Test Coverage Correlation**
   - Maps chat discussions to test files
   - Shows test coverage for discussed code
   - Highlights untested modifications

### 5. Intelligence Mining Features

#### Pattern Detection

```python
class PatternDetector:
    """Detects patterns in code-chat correlation."""

    def find_refactoring_patterns(self):
        """Identify refactoring discussions and outcomes."""

    def detect_debugging_sessions(self):
        """Find debugging patterns and resolutions."""

    def analyze_feature_development(self):
        """Track feature development from discussion to implementation."""

    def identify_knowledge_gaps(self):
        """Find areas where documentation is needed based on questions."""
```

#### Automated Insights

1. **Session Intelligence Report**
   - Files most affected
   - Complexity changes
   - New symbols introduced
   - Dependencies modified
   - Test coverage impact

2. **Code Health Metrics**
   - Technical debt discussions
   - Refactoring opportunities identified
   - Performance concerns raised
   - Security issues discussed

3. **Developer Productivity Analytics**
   - Time spent per file/feature
   - Problem resolution patterns
   - Tool usage efficiency
   - Knowledge reuse opportunities

### 6. Implementation Pipeline

#### Phase 1: Data Integration (Week 1)
- [ ] Create intelligence module structure
- [ ] Implement ProjectIntelReader wrapper
- [ ] Add database schema migrations
- [ ] Build basic correlation engine

#### Phase 2: Core Features (Week 2)
- [ ] Implement symbol extraction
- [ ] Add file activity tracking
- [ ] Create code evolution API
- [ ] Build agent utilization metrics

#### Phase 3: Visualizations (Week 3)
- [ ] Develop code evolution timeline
- [ ] Create symbol discussion heatmap
- [ ] Build dependency impact graph
- [ ] Add test coverage correlation

#### Phase 4: Advanced Analytics (Week 4)
- [ ] Implement pattern detection
- [ ] Add automated insights
- [ ] Create intelligence reports
- [ ] Build knowledge gap analysis

### 7. Technical Implementation Details

#### Efficient Data Access

```python
class IntelligenceCache:
    """Caches frequently accessed project intelligence data."""

    def __init__(self, ttl=3600):
        self.symbol_cache = TTLCache(maxsize=1000, ttl=ttl)
        self.file_cache = TTLCache(maxsize=500, ttl=ttl)
        self.agent_cache = TTLCache(maxsize=100, ttl=ttl)

    def get_file_elements(self, file_path):
        if file_path not in self.file_cache:
            self.file_cache[file_path] = self._load_file_elements(file_path)
        return self.file_cache[file_path]
```

#### Streaming Processing

```python
class StreamingCorrelator:
    """Processes chat logs and project intel in streaming fashion."""

    def correlate_session(self, session_id):
        """Stream-process correlation for memory efficiency."""
        for message in self._stream_messages(session_id):
            # Process without loading entire dataset
            intel_data = self._stream_related_intel(message)
            yield self._correlate(message, intel_data)
```

#### Change Detection

```python
class ChangeDetector:
    """Detects code changes between chat messages."""

    def detect_changes(self, session_id):
        """Track file changes throughout session."""
        baseline = self._establish_baseline(session_id)
        for checkpoint in self._get_checkpoints(session_id):
            changes = self._compare_to_baseline(checkpoint, baseline)
            if changes:
                self._record_changes(session_id, checkpoint, changes)
```

### 8. Performance Considerations

1. **Indexing Strategy**
   - Pre-index symbol references on startup
   - Use bloom filters for quick symbol existence checks
   - Implement LRU cache for frequently accessed data

2. **Batch Processing**
   - Process correlation in batches during off-peak
   - Use background workers for heavy analysis
   - Implement progressive loading for UI

3. **Storage Optimization**
   - Compress historical correlation data
   - Archive old sessions to separate storage
   - Use columnar storage for time-series data

### 9. Monitoring & Metrics

Track integration health with:
- Correlation accuracy rate
- Processing latency
- Cache hit rates
- Memory usage
- Query performance

### 10. Future Enhancements

1. **Machine Learning Integration**
   - Predict code changes from chat patterns
   - Auto-suggest refactoring based on discussions
   - Identify recurring problem patterns

2. **Knowledge Base Generation**
   - Auto-generate documentation from chat explanations
   - Create FAQ from common questions
   - Build troubleshooting guides

3. **Team Collaboration Features**
   - Share code discussion insights
   - Track knowledge transfer sessions
   - Identify expertise areas

## Conclusion

This integration creates a powerful development intelligence platform that:
- Provides unprecedented visibility into code evolution
- Correlates discussions with actual code changes
- Identifies patterns and opportunities for improvement
- Enhances developer productivity through insights

The modular design allows incremental implementation while maintaining system stability.
