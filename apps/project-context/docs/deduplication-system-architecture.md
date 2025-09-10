# Comprehensive Deduplication System Architecture

## Overview

The Unified Context System's deduplication system provides advanced duplicate detection and intelligent merging capabilities across all data sources including chat messages, code files, git commits, error logs, and CI/CD events. The system combines multiple algorithms and strategies to ensure high-quality, deduplicated data while maintaining system performance and data integrity.

## Architecture Components

### 1. Core Deduplication System (`deduplication_system.py`)

The main orchestrator that coordinates all deduplication activities through several specialized components:

#### ContentHasher
- **Purpose**: Exact duplicate detection using cryptographic hashing
- **Algorithm**: SHA256 (configurable to MD5)
- **Features**:
  - Content normalization for consistent hashing
  - Source-type specific hash generation
  - Support for structural elements (functions, classes, files)
  - Case-insensitive and whitespace-normalized comparison

#### SemanticSimilarityDetector
- **Purpose**: Near-duplicate detection using embedding similarity
- **Algorithm**: Cosine similarity on vector embeddings
- **Features**:
  - Configurable similarity thresholds (default: 0.95)
  - Source-type grouping for efficient comparison
  - Content-based Jaccard similarity fallback
  - Performance optimization with similarity matrix batching

#### TemporalClusterAnalyzer
- **Purpose**: Group related events occurring in temporal proximity
- **Algorithm**: DBSCAN clustering on timestamp features
- **Features**:
  - Configurable temporal windows (default: 60 minutes)
  - Actor-based grouping for improved clustering
  - Minimum cluster size validation
  - Noise point handling for outlier events

#### IntelligentMerger
- **Purpose**: Apply merge strategies based on confidence levels
- **Strategies**:
  - **Auto-merge**: High confidence (>0.95) automatic merging
  - **Conservative merge**: Preserve original data with duplicate flagging
- **Features**:
  - Content selection based on completeness
  - Metadata aggregation and preservation
  - Merge provenance tracking
  - Conflict resolution mechanisms

### 2. Monitoring and Quality System (`deduplication_monitor.py`)

Comprehensive monitoring and quality assessment system:

#### QualityAnalyzer
- **Metrics**:
  - Accuracy scoring (precision, recall, F1)
  - Efficiency measurement (items/second, processing time)
  - Reliability assessment (confidence distribution, merge success)
- **Features**:
  - Ground truth validation support
  - Heuristic quality estimation
  - Automated recommendation generation
  - Warning condition detection

#### PerformanceMonitor
- **Real-time Monitoring**:
  - Processing speed tracking
  - Quality score monitoring
  - Alert generation for threshold violations
- **Metrics Collection**:
  - Sliding window metrics (configurable size)
  - Historical performance tracking
  - Alert management and resolution

#### DeduplicationDashboard
- **Status Reporting**:
  - System health assessment
  - Performance trend analysis
  - Alert summarization
  - Comprehensive status reports

## Data Models

### DeduplicationConfig
```python
@dataclass
class DeduplicationConfig:
    # Content hashing
    content_hash_algorithm: str = "sha256"
    normalize_content: bool = True

    # Semantic similarity
    embedding_similarity_threshold: float = 0.95
    content_similarity_threshold: float = 0.85

    # Temporal clustering
    temporal_window_minutes: int = 60
    temporal_cluster_epsilon: float = 0.3
    temporal_min_samples: int = 2

    # Merge strategies
    confidence_threshold: float = 0.8
    auto_merge_threshold: float = 0.95

    # Performance
    batch_size: int = 1000
```

### DuplicateGroup
Represents a collection of duplicate items with associated metadata:
- Primary item selection
- Similarity scores for all duplicates
- Confidence assessment
- Merge strategy determination
- Temporal cluster association

### DeduplicationResult
Comprehensive results including:
- Processing statistics
- Duplicate counts by type
- Quality metrics
- Performance measurements

## Algorithm Details

### Content Hashing Algorithm

1. **Content Canonicalization**:
   - Normalize whitespace and line endings
   - Convert to lowercase for case-insensitive comparison
   - Extract structural elements (functions, classes, files)
   - Sort content parts for deterministic ordering

2. **Hash Generation**:
   - Combine canonical content with metadata
   - Generate SHA256 hash of combined string
   - Store hash with content for future comparisons

3. **Duplicate Detection**:
   - Group items by identical content hashes
   - Handle hash collisions with secondary validation
   - Preserve timestamp ordering for primary selection

### Semantic Similarity Detection

1. **Embedding Preparation**:
   - Group items by source type for efficient processing
   - Extract embedding vectors from stored embeddings
   - Convert to numpy arrays for matrix operations

2. **Similarity Calculation**:
   - Compute pairwise cosine similarity matrix
   - Apply configurable similarity threshold
   - Identify pairs above threshold for grouping

3. **Content Fallback**:
   - Use Jaccard similarity for items without embeddings
   - Compare word sets for content overlap
   - Apply secondary threshold for content similarity

### Temporal Clustering

1. **Time Series Preparation**:
   - Extract timestamps and convert to numeric features
   - Group by source type and actor for better clustering
   - Normalize timestamps to minute resolution

2. **DBSCAN Clustering**:
   - Apply density-based clustering algorithm
   - Use configurable epsilon (temporal distance)
   - Require minimum samples for cluster formation
   - Handle noise points as individual items

3. **Cluster Validation**:
   - Validate cluster sizes meet minimum requirements
   - Assign unique cluster identifiers
   - Associate clustered items for temporal context

## Integration Points

### Database Integration
- Leverages existing `content_hash` field in `context_items` table
- Stores deduplication metadata in `source_data` JSON field
- Uses PostgreSQL conflict resolution for duplicate handling
- Supports batch processing for large datasets

### Embedding System Integration
- Utilizes existing embedding generation pipeline
- Requires vector embeddings for semantic similarity
- Falls back to content comparison when embeddings unavailable
- Integrates with pgvector for efficient similarity queries

### Monitoring Integration
- Connects to structured logging system
- Provides metrics for dashboard integration
- Supports alert generation for operational monitoring
- Integrates with existing health check systems

## Performance Characteristics

### Scalability
- **Small datasets** (<1,000 items): ~100+ items/second
- **Medium datasets** (1,000-10,000 items): ~50+ items/second
- **Large datasets** (10,000+ items): ~20+ items/second
- Memory usage scales linearly with dataset size
- CPU usage dominated by similarity matrix calculations

### Optimization Strategies
- Batch processing for database operations
- Source-type grouping reduces comparison space
- Similarity matrix caching for repeated operations
- Configurable batch sizes for memory management
- Parallel processing support for large datasets

## Configuration Examples

### Production Configuration
```python
production_config = DeduplicationConfig(
    embedding_similarity_threshold=0.92,
    temporal_window_minutes=30,
    auto_merge_threshold=0.90,
    batch_size=500
)
```

### Development Configuration
```python
development_config = DeduplicationConfig(
    embedding_similarity_threshold=0.85,
    temporal_window_minutes=120,
    auto_merge_threshold=0.95,
    batch_size=100
)
```

### Aggressive Deduplication
```python
aggressive_config = DeduplicationConfig(
    embedding_similarity_threshold=0.80,
    content_similarity_threshold=0.75,
    auto_merge_threshold=0.85,
    confidence_threshold=0.70
)
```

## Quality Assurance

### Automated Quality Metrics
- **Precision**: Ratio of correctly identified duplicates
- **Recall**: Ratio of actual duplicates found
- **F1 Score**: Harmonic mean of precision and recall
- **Processing Efficiency**: Items processed per second
- **Merge Success Rate**: Automatic merges vs. manual review

### Quality Thresholds
- Overall quality score > 0.8 (good)
- Processing time < 300 seconds (acceptable)
- Auto-merge success rate > 0.7 (efficient)
- False positive rate < 0.1 (accurate)

### Monitoring Alerts
- **Performance**: Low processing speed, long processing time
- **Quality**: Low quality scores, high false positive rates
- **System**: Memory usage, error rates, alert fatigue

## API Usage Examples

### Basic Deduplication
```python
from project_context.ingestion.deduplication_system import create_deduplicator

# Create deduplicator with default settings
deduplicator = create_deduplicator()

# Process items
result = await deduplicator.deduplicate_items(context_items)

print(f"Processed {result.total_items} items")
print(f"Found {result.exact_duplicates} exact duplicates")
print(f"Found {result.semantic_duplicates} semantic duplicates")
```

### Advanced Configuration
```python
from project_context.ingestion.deduplication_system import (
    ComprehensiveDeduplicator,
    DeduplicationConfig
)

# Custom configuration
config = DeduplicationConfig(
    embedding_similarity_threshold=0.90,
    temporal_window_minutes=45,
    auto_merge_threshold=0.88
)

deduplicator = ComprehensiveDeduplicator(config)
result = await deduplicator.deduplicate_items(items)
```

### Quality Monitoring
```python
from project_context.ingestion.deduplication_monitor import (
    create_dashboard,
    QualityAnalyzer
)

# Create monitoring dashboard
dashboard = create_dashboard()

# Assess quality
analyzer = QualityAnalyzer()
quality = await analyzer.assess_quality(result)

print(f"Overall quality score: {quality.overall_score}")
print(f"Recommendations: {quality.recommendations}")
```

## Future Enhancements

### Planned Features
- Machine learning-based similarity scoring
- Graph-based duplicate detection algorithms
- Real-time streaming deduplication
- Cross-project duplicate detection
- Advanced merge conflict resolution

### Performance Improvements
- GPU acceleration for embedding similarity
- Distributed processing for large datasets
- Incremental deduplication for continuous ingestion
- Advanced caching strategies
- Optimized database queries

### Quality Enhancements
- Active learning for threshold tuning
- Human-in-the-loop validation
- Domain-specific similarity models
- Advanced temporal pattern detection
- Multi-modal similarity assessment

## Conclusion

The comprehensive deduplication system provides a robust, scalable solution for maintaining data quality across the Unified Context System. Through the combination of exact matching, semantic similarity, temporal clustering, and intelligent merging, the system ensures high-quality deduplicated data while maintaining performance and providing comprehensive monitoring capabilities.
