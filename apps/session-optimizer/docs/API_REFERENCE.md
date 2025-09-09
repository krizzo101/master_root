# Session Optimizer API Reference

A comprehensive API reference for the session-optimizer system - a GPT-5 payload generation system that optimizes Claude Code sessions with 2.23x-3.14x compression ratios and 60-80% cost savings.

## Table of Contents

- [Overview](#overview)
- [CLI API](#cli-api)
- [Python Library API](#python-library-api)
- [Data Structures](#data-structures)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Configuration](#configuration)

## Overview

The session-optimizer system provides multiple API interfaces:

- **CLI API**: Command-line tools (`gpt5_cli.py`, `payload_cli.py`)
- **Python Library API**: Direct integration classes and methods
- **Analytics Engine**: Session analysis and metrics
- **Streaming API**: Memory-efficient processing for large sessions

### Key Features

- Multi-strategy chunking (conversation, tool_usage, adaptive)
- Memory-efficient streaming for 4.5M+ token sessions
- Claude .jsonl format compatibility
- Parallel processing support
- Comprehensive cost analysis

## CLI API

### Main CLI Tool: `gpt5_cli.py`

The primary command-line interface for GPT-5 session optimization.

#### Global Options

```bash
python gpt5_cli.py [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]
```

| Option | Description | Default |
|--------|-------------|---------|
| `--config PATH` | Configuration file path | None |
| `--quiet, -q` | Quiet mode | False |

#### Commands

##### `optimize` - Single Session Optimization

Optimize a single Claude session file.

```bash
python gpt5_cli.py optimize SESSION_FILE [OPTIONS]
```

**Parameters:**
- `SESSION_FILE` (required): Path to Claude .jsonl session file

**Options:**
| Option | Choices | Default | Description |
|--------|---------|---------|-------------|
| `--output, -o PATH` | | None | Output directory for results |
| `--strategy` | `conversation`, `tool_usage`, `adaptive` | `adaptive` | Chunking strategy |
| `--verbose, -v` | | False | Verbose output |

**Example:**
```bash
python gpt5_cli.py optimize session.jsonl --output results/ --strategy tool_usage --verbose
```

**Output:**
```
✅ Session session optimized successfully
   📊 45,234 → 20,150 tokens
   🗜️  2.25x compression (tool_usage)
   💰 $0.8421 cost savings
   📦 3 payloads generated
   ⏱️  1.24s processing time
```

##### `batch` - Batch Processing

Process multiple session files in parallel.

```bash
python gpt5_cli.py batch INPUT_DIR [OPTIONS]
```

**Parameters:**
- `INPUT_DIR` (required): Directory containing .jsonl files

**Options:**
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--output, -o PATH` | Path | None | Output directory |
| `--parallel` | Flag | False | Enable parallel processing |
| `--pattern` | String | `*.jsonl` | File pattern |
| `--max-workers` | Integer | 4 | Max parallel workers |

**Example:**
```bash
python gpt5_cli.py batch /path/to/sessions/ --output results/ --parallel --max-workers 8
```

##### `stream` - Large Session Streaming

Process very large sessions with memory-efficient streaming.

```bash
python gpt5_cli.py stream SESSION_FILE [OPTIONS]
```

**Parameters:**
- `SESSION_FILE` (required): Large Claude .jsonl session file

**Options:**
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--memory-limit` | Integer | 2048 | Memory limit in MB |
| `--output, -o PATH` | Path | None | Output directory |

**Example:**
```bash
python gpt5_cli.py stream large_session.jsonl --memory-limit 1024 --output streaming_results/
```

##### `compare` - Strategy Comparison

Compare all chunking strategies for a session.

```bash
python gpt5_cli.py compare SESSION_FILE [OPTIONS]
```

**Parameters:**
- `SESSION_FILE` (required): Claude .jsonl session file

**Options:**
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--output, -o PATH` | Path | None | Output file for comparison |

**Example:**
```bash
python gpt5_cli.py compare session.jsonl --output comparison.json
```

##### `analyze` - Session Analysis

Analyze session cost and size metrics.

```bash
python gpt5_cli.py analyze SESSION_FILE [OPTIONS]
```

**Parameters:**
- `SESSION_FILE` (required): Claude .jsonl session file

**Options:**
| Option | Description |
|--------|-------------|
| `--cost-only` | Show only cost analysis |
| `--tokens-only` | Show only token analysis |

##### `status` - System Status

Show system status and statistics.

```bash
python gpt5_cli.py status [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--detailed` | Show detailed component status |

##### `test` - Run Tests

Execute system tests and benchmarks.

```bash
python gpt5_cli.py test [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--benchmark` | Run performance benchmarks |
| `--quick` | Quick test mode |

### Payload CLI Tool: `payload_cli.py`

Alternative CLI tool focused on payload generation with enhanced reporting.

#### Commands

##### `generate` - Generate Payload

```bash
python payload_cli.py generate SESSION_FILE [OPTIONS]
```

**Options:**
| Option | Choices | Default | Description |
|--------|---------|---------|-------------|
| `--strategy` | `conversation`, `tool_usage`, `adaptive`, `none` | `adaptive` | Chunking strategy |
| `--format` | `json`, `text`, `html` | `json` | Output format |
| `--output, -o PATH` | | None | Output file |
| `--verbose, -v` | | False | Verbose output |

##### `batch` - Batch Processing with Reports

```bash
python payload_cli.py batch INPUT_DIR --output OUTPUT_DIR [OPTIONS]
```

**Options:**
| Option | Choices | Default | Description |
|--------|---------|---------|-------------|
| `--format` | `json`, `html`, `csv` | `json` | Output format |
| `--strategy` | `conversation`, `tool_usage`, `adaptive`, `none` | `adaptive` | Chunking strategy |
| `--parallel` | | False | Enable parallel processing |
| `--workers` | | 4 | Number of workers |
| `--pattern` | | `*.jsonl` | File pattern |

##### `compare` - Strategy Comparison

```bash
python payload_cli.py compare SESSION_FILE [OPTIONS]
```

**Options:**
| Option | Choices | Default | Description |
|--------|---------|---------|-------------|
| `--all-strategies` | | False | Compare all strategies |
| `--strategies` | Multiple choices | None | Specific strategies |
| `--format` | `json`, `html`, `table` | `table` | Output format |

##### `report` - Comprehensive Reports

```bash
python payload_cli.py report SESSION_FILE [OPTIONS]
```

**Options:**
| Option | Choices | Default | Description |
|--------|---------|---------|-------------|
| `--format` | `json`, `html` | `html` | Report format |
| `--include-analytics` | | False | Include session analytics |

## Python Library API

### Core Classes

#### GPT5PayloadSystem

The main orchestration class that integrates all components.

```python
from src.gpt5_payload_system import GPT5PayloadSystem, GPT5OptimizationConfig

# Initialize system
config = GPT5OptimizationConfig(
    max_chunk_tokens=25000,
    default_chunking_strategy="adaptive",
    enable_streaming=True,
    enable_parallel_processing=True,
    max_workers=4
)
system = GPT5PayloadSystem(config)
```

##### Methods

###### `optimize_session_file(session_file_path: Path) -> OptimizationResult`

Complete end-to-end optimization of a single session file.

**Parameters:**
- `session_file_path` (Path): Path to Claude .jsonl session file

**Returns:**
- `OptimizationResult`: Complete optimization result

**Example:**
```python
from pathlib import Path

result = system.optimize_session_file(Path("session.jsonl"))
if result.success:
    print(f"Compression: {result.processing_stats['compression_ratio']:.2f}x")
    print(f"Cost savings: ${result.processing_stats['cost_savings']:.4f}")
```

###### `optimize_session_streaming(session_file_path: Path, max_memory_mb: Optional[int] = None) -> Generator`

Memory-efficient streaming optimization for very large sessions.

**Parameters:**
- `session_file_path` (Path): Path to large session file
- `max_memory_mb` (Optional[int]): Memory limit in MB

**Yields:**
- `Dict[str, Any]`: Chunk processing results

**Example:**
```python
for chunk_result in system.optimize_session_streaming(Path("large_session.jsonl")):
    if chunk_result.get("is_final", False):
        print("Streaming complete")
        break
    else:
        print(f"Processed chunk {chunk_result['chunk_index']}")
```

###### `batch_optimize_sessions(session_files: List[Path], output_dir: Optional[Path] = None, parallel: bool = None) -> Dict[str, Any]`

Optimize multiple session files with optional parallel processing.

**Parameters:**
- `session_files` (List[Path]): List of session files
- `output_dir` (Optional[Path]): Output directory
- `parallel` (Optional[bool]): Enable parallel processing

**Returns:**
- `Dict[str, Any]`: Batch optimization summary

**Example:**
```python
from pathlib import Path

session_files = [Path("session1.jsonl"), Path("session2.jsonl")]
summary = system.batch_optimize_sessions(session_files, parallel=True)
print(f"Success rate: {summary['summary']['success_rate']:.1f}%")
```

###### `get_system_status() -> Dict[str, Any]`

Get current system status and statistics.

**Returns:**
- `Dict[str, Any]`: System status information

#### TokenCountAnalyzer

Accurate token counting using tiktoken for GPT-5 models.

```python
from src.token_count_analyzer import TokenCountAnalyzer

analyzer = TokenCountAnalyzer(model="gpt-4o")
```

##### Methods

###### `count_tokens(content: Union[str, List[Dict], Dict]) -> int`

Count tokens in content using tiktoken.

**Parameters:**
- `content` (Union[str, List[Dict], Dict]): Content to analyze

**Returns:**
- `int`: Token count

**Example:**
```python
tokens = analyzer.count_tokens("Hello, world!")
print(f"Token count: {tokens}")
```

###### `analyze_session_tokens(session_data: Dict) -> TokenAnalysisResult`

Comprehensive token analysis of a session.

**Parameters:**
- `session_data` (Dict): Session data

**Returns:**
- `TokenAnalysisResult`: Detailed token analysis

**Example:**
```python
analysis = analyzer.analyze_session_tokens(session_data)
print(f"Total tokens: {analysis.total_tokens}")
print(f"Cost: ${analysis.estimated_cost:.4f}")
print(f"Category: {analysis.size_category}")
```

#### ChunkingEngine

Implements multiple chunking strategies for optimization.

```python
from src.chunking_engine import ChunkingEngine, ChunkingConfig

config = ChunkingConfig(
    max_chunk_tokens=25000,
    overlap_tokens=1000,
    preserve_conversation_flow=True
)
engine = ChunkingEngine(config)
```

##### Methods

###### `chunk_session(session_data: Dict[str, Any], strategy: str = "adaptive") -> ChunkResult`

Chunk session data using specified strategy.

**Parameters:**
- `session_data` (Dict[str, Any]): Session data
- `strategy` (str): Chunking strategy ("conversation", "tool_usage", "adaptive")

**Returns:**
- `ChunkResult`: Chunking results

**Example:**
```python
result = engine.chunk_session(session_data, "tool_usage")
print(f"Chunks: {len(result.chunks)}")
print(f"Compression: {result.compression_ratio:.2f}x")
```

###### `compare_strategies(session_data: Dict[str, Any]) -> Dict[str, ChunkResult]`

Compare all available chunking strategies.

**Parameters:**
- `session_data` (Dict[str, Any]): Session data

**Returns:**
- `Dict[str, ChunkResult]`: Strategy comparison results

#### SessionAnalyticsEngine

Comprehensive session analysis and metrics.

```python
from session_analytics_engine import SessionAnalyticsEngine

analytics = SessionAnalyticsEngine()
```

##### Methods

###### `analyze_session(session_file: Path) -> SessionAnalysisReport`

Analyze session structure and patterns.

**Parameters:**
- `session_file` (Path): Session file path

**Returns:**
- `SessionAnalysisReport`: Complete analysis report

**Example:**
```python
report = analytics.analyze_session(Path("session.jsonl"))
print(f"User messages: {report.conversation_flow.user_messages}")
print(f"Tool usage: {len(report.tool_usage.tool_counts)}")
print(f"Complexity: {report.complexity_rating}")
```

## Data Structures

### Core Data Classes

#### OptimizationResult

Complete optimization result for a session.

```python
@dataclass
class OptimizationResult:
    session_id: str
    original_analysis: SessionAnalysisReport
    token_analysis: TokenAnalysisResult
    chunking_result: ChunkResult
    generated_payloads: List[GeneratedPayload]
    optimization_analysis: OptimizationAnalysis
    processing_stats: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None
```

#### TokenAnalysisResult

Results from token analysis.

```python
@dataclass
class TokenAnalysisResult:
    total_tokens: int
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    content_breakdown: Dict[str, int]
    optimization_potential: float
    size_category: str
```

#### ChunkResult

Result from chunking operation.

```python
@dataclass
class ChunkResult:
    chunks: List[Dict[str, Any]]
    strategy_used: str
    original_tokens: int
    final_tokens: int
    compression_ratio: float
    chunk_metadata: List[Dict[str, Any]]
```

#### GeneratedPayload

Generated GPT-5 payload structure.

```python
@dataclass
class GeneratedPayload:
    payload: str
    estimated_tokens: int
    compression_achieved: float
    payload_type: str
    quality_score: float
```

### Configuration Classes

#### GPT5OptimizationConfig

Master configuration for GPT-5 optimization system.

```python
@dataclass
class GPT5OptimizationConfig:
    # TokenCountAnalyzer settings
    gpt5_model: str = "gpt-4o"
    input_cost_per_1k: float = 0.025
    output_cost_per_1k: float = 0.05

    # ChunkingEngine settings
    max_chunk_tokens: int = 25000
    chunk_overlap_tokens: int = 1000
    default_chunking_strategy: str = "adaptive"

    # PayloadGenerator settings
    max_context_tokens: int = 15000
    prompt_style: str = "conversational"
    optimization_level: str = "balanced"

    # System settings
    enable_streaming: bool = True
    enable_parallel_processing: bool = True
    max_workers: int = 4
    memory_limit_mb: int = 2048
```

### Session Analysis Structures

#### SessionAnalysisReport

Comprehensive session analysis results.

```python
@dataclass
class SessionAnalysisReport:
    session_context: SessionContext
    conversation_flow: ConversationFlow
    tool_usage: ToolUsageMetrics
    file_operations: FileOperationMetrics
    optimization_score: float = 0.0
    complexity_rating: str = "Unknown"
    recommended_chunks: int = 1
    patterns_detected: List[str] = field(default_factory=list)
```

#### ConversationFlow

Dialog flow patterns.

```python
@dataclass
class ConversationFlow:
    session_id: str
    user_messages: int = 0
    assistant_messages: int = 0
    system_messages: int = 0
    avg_response_time: float = 0.0
    conversation_length: int = 0
    topic_shifts: int = 0
    patterns: List[str] = field(default_factory=list)
```

## Error Handling

### Exception Types

The system uses standard Python exceptions with descriptive messages:

- `FileNotFoundError`: Session file not found
- `ValueError`: Invalid configuration or data format
- `RuntimeError`: Processing errors
- `MemoryError`: Memory limit exceeded during streaming
- `TimeoutError`: Processing timeout in batch mode

### Error Response Format

When operations fail, detailed error information is provided:

```python
{
    "success": False,
    "error_message": "Detailed error description",
    "error_type": "ValueError",
    "context": {
        "session_id": "session_name",
        "operation": "optimization",
        "timestamp": "2025-09-09T04:53:45Z"
    }
}
```

### CLI Error Codes

| Exit Code | Description |
|-----------|-------------|
| 0 | Success |
| 1 | General error |
| 2 | File not found |
| 3 | Configuration error |
| 4 | Memory limit exceeded |
| 5 | Timeout error |

## Examples

### Basic Session Optimization

```python
from pathlib import Path
from src.gpt5_payload_system import GPT5PayloadSystem

# Initialize system
system = GPT5PayloadSystem()

# Optimize single session
result = system.optimize_session_file(Path("my_session.jsonl"))

if result.success:
    stats = result.processing_stats
    print(f"✅ Optimization successful!")
    print(f"📊 {stats['original_tokens']:,} → {stats['optimized_tokens']:,} tokens")
    print(f"🗜️  {stats['compression_ratio']:.2f}x compression")
    print(f"💰 ${stats['cost_savings']:.4f} saved")
    print(f"📦 {len(result.generated_payloads)} payloads generated")
else:
    print(f"❌ Optimization failed: {result.error_message}")
```

### Batch Processing with Custom Configuration

```python
from pathlib import Path
from src.gpt5_payload_system import GPT5PayloadSystem, GPT5OptimizationConfig

# Custom configuration
config = GPT5OptimizationConfig(
    max_chunk_tokens=20000,
    default_chunking_strategy="tool_usage",
    enable_parallel_processing=True,
    max_workers=8
)

system = GPT5PayloadSystem(config)

# Find all session files
session_files = list(Path("sessions/").glob("*.jsonl"))

# Batch optimize
summary = system.batch_optimize_sessions(
    session_files,
    output_dir=Path("results/"),
    parallel=True
)

# Print results
metrics = summary["optimization_metrics"]
print(f"📊 Batch Summary:")
print(f"   Sessions: {summary['summary']['successful_optimizations']}/{summary['summary']['total_sessions']}")
print(f"   Average compression: {metrics['average_compression_ratio']:.2f}x")
print(f"   Total savings: ${metrics['total_cost_savings']:.2f}")
```

### Streaming Large Sessions

```python
from pathlib import Path
from src.gpt5_payload_system import GPT5PayloadSystem

system = GPT5PayloadSystem()

# Stream process very large session
total_chunks = 0
total_tokens = 0

for chunk_result in system.optimize_session_streaming(
    Path("huge_session.jsonl"),
    max_memory_mb=1024
):
    if chunk_result.get("is_final", False):
        # Final summary
        summary = chunk_result.get("streaming_summary", {})
        print(f"✅ Streaming complete!")
        print(f"📊 Total tokens: {summary.get('total_tokens_processed', 0):,}")
        print(f"📦 Total chunks: {summary.get('total_chunks_generated', 0)}")
        break
    else:
        # Process chunk
        total_chunks += 1
        chunk_tokens = chunk_result.get("chunk_tokens", 0)
        total_tokens += chunk_tokens
        compression = chunk_result.get("chunk_compression", 1.0)

        print(f"Chunk {total_chunks}: {chunk_tokens:,} tokens, {compression:.2f}x compression")
```

### Strategy Comparison

```python
from pathlib import Path
from src.gpt5_payload_system import GPT5PayloadSystem

system = GPT5PayloadSystem()

# Convert session
session_path = Path("session.jsonl")
converted = system.format_adapter.convert_session_file(session_path)

# Get token analysis
token_analysis = system.token_analyzer.analyze_session_tokens(converted)
print(f"📊 Session: {token_analysis.total_tokens:,} tokens ({token_analysis.size_category})")

# Compare strategies
comparison = system.size_analyzer.compare_chunking_strategies(
    token_analysis.total_tokens,
    converted
)

print(f"\n🔍 Strategy Comparison:")
print(f"{'Strategy':<12} {'Compression':<12} {'Savings':<10} {'Quality':<10}")
print("-" * 50)

for strategy, data in comparison["strategy_comparisons"].items():
    print(f"{strategy:<12} {data['compression_ratio']:<12.2f} "
          f"{data['savings_percent']:<9.1f}% {data['quality_impact']:<10}")

print(f"\n🎯 Recommended: {comparison['recommended_strategy']}")
```

### Analytics Integration

```python
from pathlib import Path
from src.gpt5_payload_system import GPT5PayloadSystem
from session_analytics_engine import SessionAnalyticsEngine

# Initialize systems
system = GPT5PayloadSystem()
analytics = SessionAnalyticsEngine()

session_path = Path("session.jsonl")

# Get comprehensive analysis
session_analysis = analytics.analyze_session(session_path)
optimization_result = system.optimize_session_file(session_path)

# Combined insights
print(f"📋 Session Analysis:")
print(f"   Conversation: {session_analysis.conversation_flow.user_messages} user messages")
print(f"   Tools used: {len(session_analysis.tool_usage.tool_counts)}")
print(f"   Complexity: {session_analysis.complexity_rating}")
print(f"   Files touched: {len(session_analysis.file_operations.files_read)}")

if optimization_result.success:
    stats = optimization_result.processing_stats
    print(f"\n💰 Optimization Results:")
    print(f"   Compression: {stats['compression_ratio']:.2f}x")
    print(f"   Cost savings: ${stats['cost_savings']:.4f}")
    print(f"   Strategy used: {stats['strategy_used']}")
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GPT5_MODEL` | GPT-5 model name | `gpt-4o` |
| `INPUT_COST_1K` | Input cost per 1K tokens | `0.025` |
| `OUTPUT_COST_1K` | Output cost per 1K tokens | `0.05` |
| `MAX_CHUNK_TOKENS` | Maximum tokens per chunk | `25000` |
| `DEFAULT_STRATEGY` | Default chunking strategy | `adaptive` |
| `MAX_WORKERS` | Maximum parallel workers | `4` |
| `MEMORY_LIMIT_MB` | Memory limit for streaming | `2048` |

### Configuration File Format

JSON configuration file format:

```json
{
  "gpt5_model": "gpt-4o",
  "input_cost_per_1k": 0.025,
  "output_cost_per_1k": 0.05,
  "max_chunk_tokens": 25000,
  "chunk_overlap_tokens": 1000,
  "default_chunking_strategy": "adaptive",
  "max_context_tokens": 15000,
  "prompt_style": "conversational",
  "optimization_level": "balanced",
  "preserve_all_metadata": false,
  "consolidate_tool_sequences": true,
  "max_content_length": 50000,
  "enable_streaming": true,
  "enable_parallel_processing": true,
  "max_workers": 4,
  "memory_limit_mb": 2048
}
```

### Size Categories

Session size categories and optimization recommendations:

| Category | Token Range | Recommended Strategy | Expected Compression |
|----------|------------|---------------------|---------------------|
| Small | 0 - 10K | `conversation` | 1.8x - 2.2x |
| Medium | 10K - 50K | `adaptive` | 2.0x - 2.5x |
| Large | 50K - 200K | `adaptive` | 2.3x - 2.8x |
| Extra Large | 200K+ | `tool_usage` | 2.8x - 3.4x |

### Chunking Strategies

Available chunking strategies with characteristics:

#### Conversation Strategy
- **Target Compression**: 2.36x
- **Best For**: Dialog-heavy sessions, preserving context flow
- **Quality Impact**: Low (maintains conversation coherence)

#### Tool Usage Strategy
- **Target Compression**: 3.14x
- **Best For**: Automation-heavy sessions, tool sequences
- **Quality Impact**: Minimal (groups related tool operations)

#### Adaptive Strategy
- **Target Compression**: 2.23x
- **Best For**: General purpose, mixed content sessions
- **Quality Impact**: Low (balanced approach)

### Performance Tuning

Recommendations for different use cases:

#### High-Throughput Batch Processing
```python
config = GPT5OptimizationConfig(
    enable_parallel_processing=True,
    max_workers=8,
    default_chunking_strategy="tool_usage",  # Fastest compression
    max_chunk_tokens=30000,  # Larger chunks
    enable_streaming=False   # Disable for smaller sessions
)
```

#### Memory-Constrained Environment
```python
config = GPT5OptimizationConfig(
    enable_streaming=True,
    memory_limit_mb=512,     # Low memory limit
    max_workers=2,           # Fewer parallel processes
    max_chunk_tokens=15000   # Smaller chunks
)
```

#### Quality-Focused Processing
```python
config = GPT5OptimizationConfig(
    default_chunking_strategy="conversation",  # Preserve quality
    chunk_overlap_tokens=2000,  # More overlap
    preserve_all_metadata=True, # Keep all metadata
    optimization_level="quality"  # Quality over speed
)
```

---

## Version Information

- **API Version**: 1.0
- **System Version**: GPT-5 Payload Generation System v1.0
- **Compatibility**: Python 3.9+, tiktoken library
- **Last Updated**: 2025-09-09

## Support

For additional support:
1. Check system status: `python gpt5_cli.py status --detailed`
2. Run diagnostics: `python gpt5_cli.py test`
3. Review logs in processing output directories
4. Consult the troubleshooting section in README.md
