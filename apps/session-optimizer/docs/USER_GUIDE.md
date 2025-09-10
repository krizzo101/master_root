# Session Optimizer User Guide

A comprehensive guide to using the Session Optimizer for optimizing AI conversation sessions for cost and performance.

> **📋 Related Documentation**: [README.md](README.md) | [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) | [API_REFERENCE.md](API_REFERENCE.md) | [DEPLOYMENT.md](DEPLOYMENT.md)

## Table of Contents

1. [Getting Started](#getting-started)
2. [Core Features](#core-features)
3. [Common Tasks](#common-tasks)
4. [Configuration](#configuration)
5. [Understanding Results](#understanding-results)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)
8. [Advanced Usage](#advanced-usage)
9. [FAQ](#faq)

---

## Getting Started

### What is Session Optimizer?

Session Optimizer is a powerful tool that analyzes and optimizes AI conversation sessions (like Claude Code sessions) to reduce costs and improve processing efficiency. It can compress large sessions by **2.23x-3.14x** while maintaining conversation quality, potentially saving you **60-80% on processing costs**.

### Quick Start

#### 1. Check System Status
Before you begin, verify that everything is working:

```bash
python gpt5_cli.py status
```

This will show you system health and available features.

#### 2. Optimize Your First Session
To optimize a single session file:

```bash
python gpt5_cli.py optimize my_session.jsonl
```

You'll see output like:
```
✅ Session my_session optimized successfully
   📊 45,234 → 20,150 tokens (2.25x compression)
   💰 $0.84 cost savings (55% reduction)
   📦 3 optimized payloads generated
   ⏱️  Processing completed in 1.24s
```

#### 3. Analyze Session Size and Potential
To understand what can be optimized:

```bash
python size_reporter.py analyze my_session.jsonl --format html
```

This creates a detailed HTML report showing optimization opportunities.

---

## Core Features

### 1. Session Analysis

**What it does**: Analyzes your session files to understand size, complexity, and optimization potential.

**When to use**: Before optimizing, to understand what you're working with.

**How to use**:
```bash
# Basic analysis
python size_reporter.py analyze session.jsonl

# Detailed HTML report
python size_reporter.py analyze session.jsonl --format html --output report.html

# Quick text summary
python gpt5_cli.py analyze session.jsonl --tokens-only
```

### 2. Session Optimization

**What it does**: Applies intelligent compression strategies to reduce session size while preserving important information.

**When to use**: When you have large sessions (>10K tokens) that need to be processed efficiently.

**How to use**:
```bash
# Basic optimization (uses adaptive strategy)
python gpt5_cli.py optimize session.jsonl

# Choose specific strategy
python gpt5_cli.py optimize session.jsonl --strategy tool_usage

# Save to specific location
python gpt5_cli.py optimize session.jsonl --output optimized_results/
```

### 3. Strategy Comparison

**What it does**: Tests different optimization approaches and shows you which works best for your session.

**When to use**: When you want to find the most effective optimization approach for a particular type of session.

**How to use**:
```bash
python gpt5_cli.py compare session.jsonl
```

### 4. Batch Processing

**What it does**: Processes multiple session files at once with parallel processing for speed.

**When to use**: When you have many sessions to optimize.

**How to use**:
```bash
# Process all .jsonl files in a directory
python gpt5_cli.py batch /path/to/sessions/ --output results/

# Use parallel processing for speed
python gpt5_cli.py batch /path/to/sessions/ --parallel --max-workers 8
```

### 5. Large Session Streaming

**What it does**: Handles extremely large sessions (1GB+) without running out of memory.

**When to use**: When you have sessions with hundreds of thousands of tokens.

**How to use**:
```bash
# Stream process with memory limit
python gpt5_cli.py stream huge_session.jsonl --memory-limit 1024

# Monitor progress with verbose output
python gpt5_cli.py stream huge_session.jsonl --memory-limit 512 --verbose
```

---

## Common Tasks

### Task 1: "I want to reduce costs for a large session"

**Step 1**: Analyze the session to see potential savings:
```bash
python size_reporter.py analyze large_session.jsonl --format text
```

**Step 2**: Compare strategies to find the best approach:
```bash
python gpt5_cli.py compare large_session.jsonl
```

**Step 3**: Apply the recommended strategy:
```bash
python gpt5_cli.py optimize large_session.jsonl --strategy tool_usage
```

### Task 2: "I have many sessions to process"

**Step 1**: Generate a batch analysis report:
```bash
python size_reporter.py batch /my/sessions/ --output batch_report.html --format html
```

**Step 2**: Process all sessions with optimal settings:
```bash
python gpt5_cli.py batch /my/sessions/ --output results/ --parallel
```

**Step 3**: Review results:
```bash
python size_reporter.py summary results/ --format text
```

### Task 3: "My session file is too large to process normally"

**Use streaming mode**:
```bash
python gpt5_cli.py stream massive_session.jsonl --memory-limit 1024 --output streaming_results/
```

This will process the file in chunks without loading everything into memory at once.

### Task 4: "I want to understand session patterns"

**Generate a comprehensive dashboard**:
```bash
python size_reporter.py dashboard /my/sessions/ --output dashboard.html --include-trends
```

This creates an interactive HTML dashboard showing:
- Session size distribution
- Optimization opportunities
- Cost analysis
- Processing trends

---

## Configuration

### Basic Settings

Most users won't need to change these, but you can customize behavior:

```python
# In your Python scripts or config files
from src.gpt5_payload_system import GPT5OptimizationConfig

config = GPT5OptimizationConfig(
    max_chunk_tokens=25000,      # Maximum size of each optimized chunk
    default_chunking_strategy="adaptive",  # Default optimization approach
    enable_streaming=True,        # Allow memory-efficient processing
    max_workers=4,               # Parallel processing threads
    memory_limit_mb=2048         # Memory limit for large files
)
```

### Strategy Selection Guide

Choose the right strategy based on your session content:

| Strategy | Best For | Compression | When to Use |
|----------|----------|-------------|-------------|
| **conversation** | Dialog-heavy sessions | 2.36x | Lots of back-and-forth conversation |
| **tool_usage** | Technical workflows | 3.14x | Many tool calls and technical operations |
| **adaptive** | Mixed content | 2.23x | General purpose, unsure what type |
| **none** | Small sessions | 1.0x | Sessions under 10K tokens |

### Memory Management

For large sessions, adjust memory settings:

```bash
# For systems with limited RAM (4GB or less)
python gpt5_cli.py stream session.jsonl --memory-limit 512

# For systems with plenty of RAM (16GB+)
python gpt5_cli.py stream session.jsonl --memory-limit 4096
```

---

## Understanding Results

### Size Categories

The system classifies your sessions into categories:

- **Small** (0-10K tokens): Usually don't need optimization
- **Medium** (10K-50K tokens): Good candidates for optimization
- **Large** (50K-200K tokens): High optimization priority
- **Extra Large** (200K+ tokens): Critical optimization needed

### Optimization Scores

Scores range from 0-100 and indicate optimization priority:

- **80-100**: Excellent opportunity - optimize immediately
- **60-79**: Good potential - worthwhile for high-cost sessions
- **40-59**: Moderate benefits - consider for efficiency
- **0-39**: Low potential - may not be worth optimizing

### Compression Ratios

- **2.0x**: Decent compression, good for most use cases
- **2.5x**: Good compression, noticeable cost savings
- **3.0x+**: Excellent compression, significant cost reduction

### Cost Analysis

Results show you:
- **Original Cost**: What you'd pay without optimization
- **Optimized Cost**: What you'll pay after optimization
- **Savings**: Absolute dollar amount saved
- **Savings %**: Percentage cost reduction

---

## Troubleshooting

### Common Issues

#### "Memory Error" or "Out of Memory"
**Cause**: Session too large for available RAM
**Solution**: Use streaming mode with lower memory limit
```bash
python gpt5_cli.py stream large_session.jsonl --memory-limit 512
```

#### "tiktoken not found"
**Cause**: Missing required dependency
**Solution**: Install the tiktoken library
```bash
pip install tiktoken
```

#### "Slow processing speed"
**Cause**: Not using parallel processing or system overloaded
**Solution**: Enable parallel processing
```bash
python gpt5_cli.py batch sessions/ --parallel --max-workers 4
```

#### "Poor compression results"
**Cause**: Wrong strategy for your session type
**Solution**: Try strategy comparison first
```bash
python gpt5_cli.py compare session.jsonl
```

#### "File not found" errors
**Cause**: Incorrect file paths
**Solution**: Use absolute paths and check file exists
```bash
ls -la /absolute/path/to/session.jsonl
python gpt5_cli.py optimize /absolute/path/to/session.jsonl
```

### Performance Issues

#### Slow Analysis
- Use `--format json` instead of HTML for faster processing
- Reduce parallel workers if system is overloaded
- Use `--quick` flag for basic analysis

#### High Memory Usage
- Enable streaming mode for large files
- Reduce memory limit settings
- Process files one at a time instead of batch

#### Disk Space Issues
- Clean up old optimization results
- Use compression on stored results
- Process smaller batches

---

## Best Practices

### For Cost Optimization
1. **Always analyze first**: Use `size_reporter.py analyze` before optimizing
2. **Focus on large sessions**: Prioritize sessions >50K tokens
3. **Use strategy comparison**: Don't guess which strategy works best
4. **Batch process similar sessions**: Process sessions of similar type together

### For Performance
1. **Enable parallel processing**: Use `--parallel` for batch operations
2. **Use appropriate memory limits**: Match limits to your system capabilities
3. **Stream large files**: Use streaming mode for sessions >100K tokens
4. **Choose the right format**: Use JSON for speed, HTML for detailed review

### For Quality
1. **Validate results**: Review optimized payloads before using
2. **Test on samples first**: Try optimization on small samples before batch processing
3. **Monitor compression ratios**: Aim for 2.0x+ compression for meaningful savings
4. **Keep originals**: Always preserve original session files

### For Workflow Integration
1. **Automate regular processing**: Set up batch jobs for frequent optimization
2. **Use dashboards**: Generate regular reports to track optimization benefits
3. **Document settings**: Keep track of which strategies work best for your use cases
4. **Monitor trends**: Track optimization effectiveness over time

---

## Advanced Usage

### Custom Analysis Workflows

**Create comprehensive session intelligence**:
```bash
# Full analysis pipeline
python size_reporter.py analyze session.jsonl --include-analytics --format html
python payload_cli.py report session.jsonl --include-analytics --format html
python gpt5_cli.py compare session.jsonl --all-strategies
```

### Automated Optimization Pipeline

**Set up batch processing automation**:
```bash
#!/bin/bash
# optimization_pipeline.sh

# 1. Analyze all sessions
python size_reporter.py batch /input/sessions/ --output analysis_report.html

# 2. Optimize high-priority sessions
python gpt5_cli.py batch /input/sessions/ --output /optimized/ --parallel

# 3. Generate summary report
python size_reporter.py summary /optimized/ --format html --output final_report.html
```

### Integration with External Systems

**Using Python API directly**:
```python
from src.gpt5_payload_system import GPT5PayloadSystem
from session_analytics_engine import SessionAnalyticsEngine

# Initialize systems
gpt5_system = GPT5PayloadSystem()
analytics = SessionAnalyticsEngine()

# Analyze session
session_report = analytics.analyze_session('session.jsonl')
optimization_result = gpt5_system.optimize_session_file('session.jsonl')

# Process results
print(f"Original tokens: {optimization_result.original_tokens}")
print(f"Compressed tokens: {optimization_result.compressed_tokens}")
print(f"Compression ratio: {optimization_result.compression_ratio}x")
print(f"Cost savings: ${optimization_result.cost_savings}")
```

### Performance Monitoring

**Track optimization effectiveness over time**:
```bash
# Daily optimization report
python size_reporter.py batch /daily/sessions/ --output daily_$(date +%Y%m%d).html
python payload_cli.py batch /daily/sessions/ --output /optimized/daily/ --parallel

# Weekly trend analysis
python size_reporter.py dashboard /weekly/sessions/ --include-trends --output weekly_trends.html
```

---

## FAQ

### Q: What file formats are supported?
**A**: The system primarily works with `.jsonl` files (Claude session format). It can also process JSON files with proper session structure.

### Q: How much can I really save on costs?
**A**: Based on testing, typical savings range from 55-80% depending on session size and content. Larger, more complex sessions see the biggest savings.

### Q: Will optimization affect the quality of my sessions?
**A**: The system is designed to preserve important information while removing redundancy. Quality impact is typically minimal to none for technical content.

### Q: Can I process sessions while they're being generated?
**A**: It's recommended to process complete sessions. For active sessions, wait until they're finished or use streaming mode for partial processing.

### Q: How do I know which strategy to use?
**A**: Always use `python gpt5_cli.py compare session.jsonl` first. The system will recommend the best strategy based on your specific session content.

### Q: Is my data secure during processing?
**A**: All processing happens locally on your system. Session data is not sent to external services during optimization.

### Q: Can I undo optimization?
**A**: The original session files are never modified. Optimized results are saved separately, so you always have the originals.

### Q: What if I have sessions larger than my available RAM?
**A**: Use streaming mode: `python gpt5_cli.py stream large_session.jsonl --memory-limit 1024`. This processes files in chunks.

### Q: How often should I optimize sessions?
**A**: Optimize sessions before using them with expensive AI models. For regular analysis, weekly or monthly batch optimization works well.

### Q: Can I customize the optimization strategies?
**A**: The current version has three built-in strategies. Custom strategy development requires modifying the source code in the `chunking_engine.py` module.

---

## Support and Next Steps

### Getting Help
1. **Check system status**: `python gpt5_cli.py status --detailed`
2. **Run diagnostics**: `python gpt5_cli.py test`
3. **Review logs**: Check output for specific error messages
4. **Try simpler approach**: Use basic optimization before advanced features

### Learning More
- Review the technical documentation in `README.md`
- Examine the CLI tools documentation for advanced features
- Check the architecture documentation for system details
- Explore the comprehensive integration test report for validation details

### Contributing and Feedback
The Session Optimizer is actively developed. Your usage patterns and feedback help improve the system for everyone.

---

*Session Optimizer User Guide v1.0*
*For technical support and advanced configuration, see the additional documentation files in the docs/ directory.*
