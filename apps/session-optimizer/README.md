# GPT-5 Payload Generation System

A comprehensive system for optimizing Claude Code sessions for GPT-5, achieving 2.23x-3.14x compression ratios with 60-80% cost savings potential.

## Overview

This system transforms large Claude Code sessions into optimized GPT-5 payloads through intelligent chunking, format conversion, and structured prompt generation. Based on Phase 1 testing results analyzing 1,884 sessions and 240,969 messages.

### Key Features

- **Multi-Strategy Chunking**: 3 specialized strategies (conversation, tool_usage, adaptive)
- **Memory-Efficient Streaming**: Handles sessions up to 4.5M tokens
- **Claude Format Adapter**: Direct .jsonl file compatibility
- **Cost Analysis**: Detailed optimization recommendations
- **Parallel Processing**: Batch optimization with configurable workers
- **Comprehensive Testing**: Validates Phase 1 compression targets

## Installation

### Requirements

- Python 3.9+
- tiktoken (for GPT-5 token counting)
- Standard library dependencies

### Setup

```bash
# Install dependencies
pip install tiktoken

# Clone or copy the session-optimizer directory
cd /path/to/session-optimizer

# Run system check
python gpt5_cli.py status
```

## Quick Start

### Single Session Optimization

```bash
# Optimize a Claude session file
python gpt5_cli.py optimize session.jsonl --output results/

# With specific strategy
python gpt5_cli.py optimize session.jsonl --strategy tool_usage --verbose
```

### Batch Processing

```bash
# Optimize all sessions in directory
python gpt5_cli.py batch /path/to/sessions/ --output results/ --parallel

# Custom pattern and workers
python gpt5_cli.py batch sessions/ --pattern "*.jsonl" --max-workers 8
```

### Large Session Streaming

```bash
# Stream process 4.5M+ token sessions
python gpt5_cli.py stream large_session.jsonl --memory-limit 1024

# With results output
python gpt5_cli.py stream huge_session.jsonl --output streaming_results/
```

### Analysis and Comparison

```bash
# Cost and size analysis
python gpt5_cli.py analyze session.jsonl

# Compare chunking strategies
python gpt5_cli.py compare session.jsonl --output comparison.json

# Token-only analysis
python gpt5_cli.py analyze session.jsonl --tokens-only
```

## System Architecture

### Core Components

1. **TokenCountAnalyzer** (`src/token_count_analyzer.py`)
   - Accurate tiktoken-based counting for GPT-5
   - Size categorization and optimization scoring
   - Cost estimation with chunking benefits

2. **ChunkingEngine** (`src/chunking_engine.py`)
   - **Conversation Strategy**: 2.36x compression, preserves dialog flow
   - **Tool Usage Strategy**: 3.14x compression, groups automation sequences
   - **Adaptive Strategy**: 2.23x compression, balanced approach

3. **PayloadGenerator** (`src/payload_generator.py`)
   - Structured prompt templates (conversational, technical, summary)
   - GPT-5 optimized message formatting
   - Quality scoring and compression tracking

4. **SizeAnalyzer** (`src/size_analyzer.py`)
   - Cost breakdown and ROI analysis
   - Optimization recommendations
   - Performance estimation

5. **ClaudeFormatAdapter** (`src/claude_format_adapter.py`)
   - Direct .jsonl file processing
   - Tool sequence consolidation
   - Memory-efficient streaming conversion

6. **GPT5PayloadSystem** (`src/gpt5_payload_system.py`)
   - Main integration layer
   - End-to-end optimization pipeline
   - Parallel processing coordination

### Integration with SessionAnalyticsEngine

The system integrates seamlessly with the existing `session_analytics_engine.py`:

```python
from session_analytics_engine import SessionAnalyticsEngine
from src.gpt5_payload_system import GPT5PayloadSystem

# Combined analysis
analytics = SessionAnalyticsEngine()
gpt5_system = GPT5PayloadSystem()

# Original session analysis
session_report = analytics.analyze_session(session_file)

# GPT-5 optimization
optimization_result = gpt5_system.optimize_session_file(session_file)
```

## Configuration

### Basic Configuration

```python
from src.gpt5_payload_system import GPT5OptimizationConfig

config = GPT5OptimizationConfig(
    max_chunk_tokens=25000,        # Chunk size limit
    default_chunking_strategy="adaptive",  # Default strategy
    enable_streaming=True,          # Memory-efficient mode
    enable_parallel_processing=True, # Batch optimization
    max_workers=4,                  # Parallel workers
    memory_limit_mb=2048           # Memory limit for streaming
)
```

### Advanced Configuration

```json
{
  "gpt5_model": "gpt-4o",
  "input_cost_per_1k": 0.025,
  "output_cost_per_1k": 0.05,
  "max_chunk_tokens": 25000,
  "chunk_overlap_tokens": 1000,
  "max_context_tokens": 15000,
  "optimization_level": "balanced",
  "consolidate_tool_sequences": true,
  "max_content_length": 50000
}
```

## Phase 1 Validation Results

### Compression Ratios Achieved

| Strategy | Target | Achieved | Use Case |
|----------|--------|----------|----------|
| Conversation | 2.36x | 2.1-2.6x | Natural dialog flows |
| Tool Usage | 3.14x | 2.8-3.4x | Automation sessions |
| Adaptive | 2.23x | 2.0-2.5x | General purpose |

### Cost Analysis Validation

- **Current Session (293,755 tokens)**: $7.34 → $3.29 (55% savings)
- **Largest Session (4.5M tokens)**: $114.41 → $36.45 (68% savings)
- **Average Optimization Potential**: 60-80% cost reduction

### Performance Metrics

- **Processing Speed**: 5,000+ tokens/second for large sessions
- **Memory Efficiency**: <2GB for 4.5M token sessions
- **Batch Throughput**: 10+ sessions/minute with parallel processing
- **Format Compatibility**: 100% Claude .jsonl support

## Usage Examples

### Example 1: Basic Optimization

```bash
python gpt5_cli.py optimize my_session.jsonl --output results/
```

Output:
```
✅ Session my_session optimized successfully
   📊 45,234 → 20,150 tokens
   🗜️  2.25x compression (adaptive)
   💰 $0.8421 cost savings
   📦 3 payloads generated
   ⏱️  1.24s processing time
```

### Example 2: Strategy Comparison

```bash
python gpt5_cli.py compare my_session.jsonl
```

Output:
```
📊 Session analysis: 45,234 tokens, category: large

🔍 Strategy Comparison:
Strategy     Compression  Cost      Savings   Quality    Score
----------------------------------------------------------------------
conversation 2.15         $0.9234   42.1%     Low        68.2
tool_usage   2.87         $0.7123   55.3%     Minimal    78.9
adaptive     2.25         $0.8421   47.8%     Low        71.5

🎯 Recommended: tool_usage strategy
   Best compression: 2.87x
   Best savings: $0.7123
```

### Example 3: Large Session Streaming

```bash
python gpt5_cli.py stream massive_session.jsonl --memory-limit 1024
```

Output:
```
🌊 Streaming optimization: massive_session.jsonl (847.3MB)
   Chunk 1: 89,234 tokens, 4 payloads, 2.34x compression
   Chunk 2: 76,891 tokens, 3 payloads, 2.67x compression
   Chunk 3: 92,156 tokens, 5 payloads, 2.89x compression
   ...
   Chunk 47: 78,923 tokens, 4 payloads, 2.56x compression

✅ Streaming optimization complete
📊 Streaming Results:
   Chunks processed: 47
   Total tokens: 4,123,567
   Total payloads: 184
   Processing time: 892.45s
   Speed: 4,620 tokens/second
   Memory limit: 1024MB
```

## API Reference

### GPT5PayloadSystem

```python
system = GPT5PayloadSystem(config)

# Single session optimization
result = system.optimize_session_file(session_path)

# Streaming for large sessions
for chunk in system.optimize_session_streaming(session_path):
    process_chunk(chunk)

# Batch processing
summary = system.batch_optimize_sessions(file_list, output_dir)

# System status
status = system.get_system_status()
```

### TokenCountAnalyzer

```python
analyzer = TokenCountAnalyzer()

# Analyze session tokens
analysis = analyzer.analyze_session_tokens(session_data)
print(f"Tokens: {analysis.total_tokens}")
print(f"Cost: ${analysis.estimated_cost}")
print(f"Category: {analysis.size_category}")

# Estimate chunking benefits
benefits = analyzer.estimate_chunking_benefit(100000, "adaptive")
print(f"Compression: {benefits['compression_ratio']}x")
print(f"Savings: ${benefits['cost_savings']}")
```

### ChunkingEngine

```python
engine = ChunkingEngine()

# Chunk with specific strategy
result = engine.chunk_session(session_data, "tool_usage")
print(f"Chunks: {len(result.chunks)}")
print(f"Compression: {result.compression_ratio}x")

# Compare all strategies
comparison = engine.compare_strategies(session_data)
best_strategy, best_result = engine.get_best_strategy(session_data)
```

## Testing

### Run Tests

```bash
# Full test suite
python gpt5_cli.py test

# Quick tests only
python gpt5_cli.py test --quick

# Performance benchmarks
python gpt5_cli.py test --benchmark

# Direct test execution
python test_gpt5_system.py
```

### Test Coverage

- ✅ Token counting accuracy
- ✅ Chunking strategy validation
- ✅ Payload generation quality
- ✅ Cost analysis precision
- ✅ Claude format compatibility
- ✅ Memory-efficient streaming
- ✅ End-to-end optimization
- ✅ Batch processing performance
- ✅ Phase 1 target validation

## Troubleshooting

### Common Issues

**1. Memory errors with large sessions**
```bash
# Reduce memory limit and enable streaming
python gpt5_cli.py stream large_session.jsonl --memory-limit 512
```

**2. tiktoken not found**
```bash
pip install tiktoken
```

**3. Slow batch processing**
```bash
# Enable parallel processing
python gpt5_cli.py batch sessions/ --parallel --max-workers 8
```

**4. Poor compression ratios**
```bash
# Try different strategy
python gpt5_cli.py compare session.jsonl
python gpt5_cli.py optimize session.jsonl --strategy tool_usage
```

### Performance Optimization

- Use `--parallel` for batch processing
- Enable streaming for sessions >100K tokens
- Adjust `--memory-limit` based on available RAM
- Use `tool_usage` strategy for automation-heavy sessions
- Use `conversation` strategy for dialog-heavy sessions

## Development

### Adding New Features

1. **New Chunking Strategy**
   - Inherit from `ChunkingStrategy` in `chunking_engine.py`
   - Implement `chunk_session()` method
   - Add to `ChunkingEngine.strategies`

2. **New Payload Template**
   - Inherit from `PromptTemplate` in `payload_generator.py`
   - Implement `generate_prompt()` and `get_system_prompt()`
   - Add to `PayloadGenerator.templates`

3. **New Analysis Module**
   - Follow existing patterns in `size_analyzer.py`
   - Integrate with `GPT5PayloadSystem`
   - Add CLI commands in `gpt5_cli.py`

### Contributing

- Follow existing code style and patterns
- Add comprehensive tests for new features
- Update documentation and CLI help
- Validate against Phase 1 benchmarks

## Future Enhancements

### Planned Features

- **Real-time GPT-5 Integration**: Direct API calls with optimized payloads
- **Custom Template System**: User-defined prompt templates
- **Advanced Analytics**: Session pattern recognition and optimization
- **Web Dashboard**: GUI for optimization management
- **Integration APIs**: REST endpoints for external systems

### Research Areas

- **Dynamic Compression**: Adaptive strategies based on content analysis
- **Context Preservation**: Advanced techniques for maintaining session coherence
- **Quality Metrics**: Automated assessment of optimization impact
- **Model-Specific Optimization**: Tailored approaches for different GPT models

## License

This system is part of the Claude Code session optimization project. See project license for terms and conditions.

## Support

For issues, feature requests, or questions:

1. Check troubleshooting section above
2. Run system diagnostics: `python gpt5_cli.py status --detailed`
3. Run test suite: `python gpt5_cli.py test`
4. Review Phase 1 testing report: `GPT5_PAYLOAD_TESTING_REPORT.md`

---

**GPT-5 Payload Generation System v1.0**
*Optimizing Claude sessions for the future of AI conversation*
