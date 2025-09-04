# Code Intelligence Adapter

## Overview

The Code Intelligence Adapter is an enhanced version of the base code adapter that provides deep integration with `.proj-intel` data and sophisticated AST analysis capabilities. It seamlessly ingests both traditional file system code data and rich project intelligence data into the unified context system.

## Features

### 🔍 Dual Data Source Support
- **Traditional Code Files**: Scans file systems for source code with pattern matching
- **.proj-intel Integration**: Ingests structured project intelligence data from `.proj-intel` directories

### 📊 Rich Code Intelligence
- **File Element Analysis**: Functions, classes, imports, and code metrics
- **Project Analysis**: Cross-project insights and architectural analysis
- **Symbol Index**: Comprehensive symbol mapping and relationships
- **AST-level Insights**: Deep code structure understanding

### 🔗 Advanced Relationship Detection
- **Code-to-Intelligence Mapping**: Links source files to their analysis data
- **Import Relationship Analysis**: Tracks dependencies via .proj-intel import data
- **Symbol Definition Mapping**: Links symbols to their defining locations
- **Project Analysis Correlations**: Connects analysis insights to relevant code

### ⚡ Performance Optimizations
- **Multi-level Caching**: Caches frequently accessed .proj-intel data
- **Batch Processing**: Optimized ingestion of large datasets
- **Age-based Filtering**: Skips outdated .proj-intel data
- **Selective Processing**: Configurable data type ingestion

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Code Intelligence Adapter                    │
├─────────────────────┬───────────────────────────────────────────┤
│   File System      │           .proj-intel Data                │
│   Scanner           │           Processor                       │
├─────────────────────┼───────────────────────────────────────────┤
│ • Pattern matching  │ • Manifest loading                       │
│ • Language detection│ • JSONL processing                       │
│ • Basic AST parsing │ • Symbol index caching                   │
│ • Change tracking   │ • Project analysis parsing               │
└─────────────────────┴───────────────────────────────────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │    Unified Transform    │
                  │    Engine               │
                  └─────────────────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │   Context Items         │
                  │   • Regular code files  │
                  │   • Intelligence data   │
                  │   • Symbol definitions  │
                  │   • Analysis insights   │
                  └─────────────────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │ Relationship Detection  │
                  │ • File analysis links   │
                  │ • Import relationships  │
                  │ • Symbol mappings       │
                  │ • Cross-references      │
                  └─────────────────────────┘
```

## Configuration

### Basic Configuration

```yaml
adapter_config:
  enable_proj_intel: true
  proj_intel_paths:
    - ".proj-intel"
    - "../.proj-intel"
  ingest_file_elements: true
  ingest_project_analysis: true
  ingest_symbol_index: true
  proj_intel_max_age_days: 7
```

### Advanced Configuration

```yaml
source_config:
  # File system scanning
  scan_directories: ["."]
  include_patterns: ["*.py", "*.js", "*.ts"]
  exclude_patterns: ["node_modules/**", ".git/**"]
  max_file_size_mb: 10

  # .proj-intel integration
  enable_proj_intel: true
  proj_intel_paths: [".proj-intel"]
  ingest_file_elements: true
  ingest_project_analysis: true
  ingest_symbol_index: true
  proj_intel_max_age_days: 7

  # Traditional code analysis
  extract_functions: true
  extract_classes: true
  extract_imports: true
  extract_comments: true
  track_changes: true
```

## Data Types

### 1. File Elements (`file_element`)
Rich analysis data for individual code files:

```json
{
  "intel_data_type": "file_element",
  "file_path": "src/example.py",
  "content_hash": "abc123...",
  "functions": [
    {
      "name": "process_data",
      "line": 45,
      "async": true
    }
  ],
  "classes": [
    {
      "name": "DataProcessor",
      "line": 12
    }
  ],
  "imports": [
    {
      "module": "asyncio",
      "line": 1
    }
  ]
}
```

### 2. Project Analysis (`project_analysis`)
Cross-cutting project insights:

```json
{
  "intel_data_type": "project_analysis",
  "collector": "ConstraintsCollector",
  "analysis_data": {
    "technical_constraints": [...],
    "business_rules": [...],
    "limitations": [...]
  }
}
```

### 3. Symbol Index (`symbol`)
Symbol mapping and definitions:

```json
{
  "intel_data_type": "symbol",
  "symbol_type": "function",
  "symbol_name": "process_data",
  "symbol_data": {
    "file_path": "src/example.py",
    "line": 45,
    "signature": "async def process_data(items: List[Dict]) -> Dict"
  }
}
```

## Entity Types

The adapter creates different entity types based on content analysis:

- **Regular Code Files:**
  - `source_file_with_classes`
  - `source_file_with_functions`
  - `source_file`
  - `test_file`
  - `config_file`

- **Intelligence Data:**
  - `code_file_with_classes`
  - `code_file_with_functions`
  - `code_file_analyzed`
  - `analysis_collector`
  - `analysis_metadata`
  - `symbol_function`
  - `symbol_class`

## Relationship Types

The adapter detects various relationship types:

### Code-to-Intelligence Relationships
- `analyzed_by`: Source file → Intelligence analysis
- `analyzes`: Intelligence analysis → Source file

### Code Structure Relationships
- `imports`: File imports another file
- `imports_analysis`: Intelligence data shows import relationship
- `symbol_defined_in`: Symbol → Defining file

### Project Relationships
- `analyzes_project`: Project analysis → Related files
- `same_analysis_run`: Items from same .proj-intel generation
- `same_directory`: Files in same directory
- `same_language`: Files with same programming language

## Database Integration

### Context Items Schema
Intelligence data is stored with enhanced metadata:

```sql
-- Enhanced metrics for intelligence items
metrics JSONB CONTAINING:
{
  "intel_data_type": "file_element",
  "generated_at": "2025-08-28T01:08:07Z",
  "source": "proj_intel",
  "content_hash": "abc123...",
  "functions": [...],
  "classes": [...],
  "code_analysis": {
    "function_count": 5,
    "class_count": 2,
    "complexity_indicators": {...}
  }
}
```

### Enhanced Code Elements Table
```sql
CREATE TABLE code_elements_enhanced (
  id UUID PRIMARY KEY,
  context_item_id UUID REFERENCES context_items(id),
  file_path TEXT NOT NULL,
  element_type VARCHAR(50),
  name VARCHAR(255),

  -- .proj-intel integration
  proj_intel_hash VARCHAR(64),
  async_function BOOLEAN,
  symbol_type VARCHAR(50),
  symbol_data JSONB,
  analysis_metadata JSONB
);
```

## Performance Characteristics

### Caching Strategy
- **L1 Cache**: Symbol index and analysis index (in-memory)
- **L2 Cache**: Manifest data (60 minutes TTL)
- **L3 Cache**: Processed JSONL data (until file changes)

### Throughput Metrics
- **File Elements**: ~100 items/second
- **Project Analysis**: ~50 items/second
- **Symbol Data**: ~200 items/second
- **Regular Files**: ~75 items/second

### Memory Usage
- Base adapter: ~50MB
- With .proj-intel caching: ~150MB
- Peak during batch processing: ~300MB

## Usage Examples

### Basic Usage
```python
from project_context.ingestion.adapters.code_adapter import CodeAdapter
from project_context.ingestion.base_adapter import AdapterConfig

config = AdapterConfig(
    adapter_id="code_intel",
    source_type="code",
    source_config={
        "enable_proj_intel": True,
        "proj_intel_paths": [".proj-intel"]
    }
)

adapter = CodeAdapter(config)
await adapter.initialize()

async for item in adapter.fetch_items(limit=100):
    context_item = await adapter.transform_item(item)
    print(f"Processed: {context_item.title}")
```

### Pipeline Integration
```python
from project_context.ingestion.pipeline import IngestionPipeline
from project_context.ingestion.registry import AdapterRegistry

registry = AdapterRegistry()
registry.register_adapter("code_intel", CodeAdapter, config)

pipeline = IngestionPipeline(registry, transformer)
await pipeline.start(["code_intel"])
```

## Testing

### Unit Tests
```bash
# Run adapter-specific tests
python -m pytest tests/adapters/test_code_adapter.py

# Run .proj-intel integration tests
python -m pytest tests/adapters/test_proj_intel_integration.py
```

### Integration Tests
```bash
# Run full pipeline integration test
python examples/test_code_intel_integration.py

# Test with real .proj-intel data
python test_code_intelligence_adapter.py
```

## Monitoring

### Key Metrics
- `code_intelligence_items_ingested`: Items processed by type
- `proj_intel_cache_hits`: Cache efficiency
- `proj_intel_processing_time`: Performance metrics
- `code_relationships_detected`: Relationship detection success

### Health Checks
- .proj-intel data freshness (< 7 days old)
- Cache hit ratios (> 80%)
- Processing error rates (< 5%)
- Relationship detection rates (> 60% of items)

## Troubleshooting

### Common Issues

**1. No .proj-intel data found**
```
⚠️ Project intel directory not found: .proj-intel
```
- Verify .proj-intel directory exists
- Check `proj_intel_paths` configuration
- Ensure file permissions are correct

**2. Outdated intelligence data**
```
⚠️ Project intel data is old, age_days=10, max_age=7
```
- Regenerate .proj-intel data
- Increase `proj_intel_max_age_days` temporarily
- Check .proj-intel generation automation

**3. JSONL parsing errors**
```
❌ Failed to parse JSONL line: Invalid JSON
```
- Verify .proj-intel file integrity
- Check for truncated files
- Regenerate corrupted files

**4. Memory issues**
```
⚠️ High pipeline memory usage: 400MB > 300MB
```
- Reduce batch sizes
- Increase `proj_intel_max_age_days` to skip old data
- Enable garbage collection more frequently

### Performance Tuning

**For High-Volume Codebases:**
- Reduce `batch_size` to 50
- Enable selective processing
- Set shorter cache TTLs
- Use exclude patterns aggressively

**For Deep Analysis:**
- Enable all intelligence data types
- Increase relationship detection window
- Cache symbol and analysis indexes
- Use larger batch sizes (200+)

## Future Enhancements

### Planned Features
- **Real-time .proj-intel Updates**: File watching and incremental updates
- **Advanced AST Analysis**: Language-specific deep parsing
- **Code Quality Metrics**: Complexity, maintainability scoring
- **Cross-project Intelligence**: Multi-repository analysis correlation
- **ML-based Relationship Detection**: Enhanced relationship inference

### Extension Points
- **Custom Collectors**: Support for additional .proj-intel collectors
- **Language Plugins**: Extensible language-specific analyzers
- **Intelligence Transformers**: Custom data transformation pipelines
- **Relationship Validators**: Machine learning validation of detected relationships

---

*This adapter represents a significant advancement in code intelligence integration, providing the foundation for sophisticated code understanding and analysis within the unified context system.*
