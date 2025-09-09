# Session Optimizer Troubleshooting Guide

> **Comprehensive troubleshooting guide for session optimization system issues, performance problems, and integration challenges**

## 🚨 Quick Diagnostic Commands

Before diving into specific issues, run these diagnostic commands to understand your system state:

```bash
# System status and health check
python gpt5_cli.py status --detailed

# Validate all dependencies and integrations
python test_integration.py

# Check Phase 1.5 component health
python test_gpt5_system.py --health-check

# Memory and performance diagnostics
python size_reporter.py system-info
```

## 🔧 Common Issues and Solutions

### 1. Memory and Performance Issues

#### Large Session Memory Errors
**Symptoms**:
- `MemoryError` when processing sessions >1GB
- System becomes unresponsive during optimization
- Process killed by OS (OOM killer)

**Diagnosis**:
```bash
# Check session size and memory requirements
python size_reporter.py analyze large_session.jsonl --memory-estimate

# Monitor memory usage during processing
python gpt5_cli.py optimize large_session.jsonl --memory-monitor
```

**Solutions**:
```bash
# Enable streaming for large sessions
python gpt5_cli.py stream large_session.jsonl --memory-limit 1024

# Use chunked processing
python gpt5_cli.py optimize large_session.jsonl --chunk-size 50000

# Enable memory-efficient mode
python gpt5_cli.py optimize large_session.jsonl --memory-efficient
```

**Prevention**:
- Always use streaming for sessions >100K tokens
- Set appropriate memory limits based on available RAM
- Monitor memory usage with `--memory-monitor` flag

#### Poor Processing Performance
**Symptoms**:
- Processing speed <1000 tokens/second
- Batch processing takes excessive time
- High CPU usage with low throughput

**Diagnosis**:
```bash
# Run performance benchmark
python gpt5_cli.py test --benchmark

# Profile specific session
python gpt5_cli.py optimize session.jsonl --profile
```

**Solutions**:
```bash
# Enable parallel processing
python gpt5_cli.py batch sessions/ --parallel --max-workers 8

# Use optimized chunking strategy
python gpt5_cli.py optimize session.jsonl --strategy tool_usage

# Enable performance optimizations
python gpt5_cli.py optimize session.jsonl --fast-mode
```

### 2. Format and Compatibility Issues

#### Claude .jsonl Format Problems
**Symptoms**:
- `InvalidFormatError` when processing Claude sessions
- Missing tool calls or incomplete message extraction
- Timestamp parsing failures

**Diagnosis**:
```bash
# Validate session format
python claude_session_analyzer.py validate session.jsonl

# Test format compatibility
python test_enhanced_integration.py --format-check
```

**Solutions**:
```bash
# Use enhanced Claude adapter
python claude_session_analyzer.py /path/to/claude/sessions --enhanced

# Fix format issues automatically
python claude_session_analyzer.py session.jsonl --auto-fix

# Convert to compatible format
python claude_session_analyzer.py session.jsonl --convert --output fixed_session.jsonl
```

#### SessionAnalyticsEngine Integration Issues
**Symptoms**:
- `AttributeError: 'NoneType' object has no attribute 'analyze'`
- Missing session analysis data
- Integration test failures

**Diagnosis**:
```bash
# Test SessionAnalyticsEngine directly
python -c "from session_analytics_engine import SessionAnalyticsEngine; engine = SessionAnalyticsEngine(); print('OK')"

# Validate integration
python test_enhanced_integration.py --integration-test
```

**Solutions**:
```bash
# Reinstall/reset SessionAnalyticsEngine
python -c "from session_analytics_engine import SessionAnalyticsEngine; SessionAnalyticsEngine().reset()"

# Use enhanced integration
from src.enhanced_claude_format_adapter import create_enhanced_session_analytics_engine
enhanced_engine = create_enhanced_session_analytics_engine()
```

### 3. Dependency and Installation Issues

#### tiktoken Installation Problems
**Symptoms**:
- `ModuleNotFoundError: No module named 'tiktoken'`
- Token counting failures
- Incorrect cost calculations

**Diagnosis**:
```bash
# Check tiktoken installation
python -c "import tiktoken; print(tiktoken.__version__)"

# Test token counting
python -c "import tiktoken; enc = tiktoken.get_encoding('cl100k_base'); print(len(enc.encode('test')))"
```

**Solutions**:
```bash
# Install/upgrade tiktoken
pip install --upgrade tiktoken

# Force reinstall if corrupted
pip uninstall tiktoken && pip install tiktoken

# Test installation
python gpt5_cli.py status --tiktoken-check
```

#### Python Version Compatibility
**Symptoms**:
- Syntax errors in modern Python features
- Module import failures
- Async/await issues

**Diagnosis**:
```bash
# Check Python version
python --version

# Test async support
python -c "import asyncio; print('Async OK')"
```

**Solutions**:
- Upgrade to Python 3.9+ for full compatibility
- Use synchronous APIs if async not available
- Check virtual environment configuration

### 4. Optimization and Strategy Issues

#### Poor Compression Ratios
**Symptoms**:
- Compression ratios <1.5x (below expectations)
- Minimal cost savings
- Strategy comparison shows poor performance

**Diagnosis**:
```bash
# Compare all strategies
python gpt5_cli.py compare session.jsonl

# Analyze session characteristics
python size_reporter.py analyze session.jsonl --detailed
```

**Solutions**:
```bash
# Try different strategies
python gpt5_cli.py optimize session.jsonl --strategy tool_usage
python gpt5_cli.py optimize session.jsonl --strategy conversation
python gpt5_cli.py optimize session.jsonl --strategy adaptive

# Adjust chunking parameters
python gpt5_cli.py optimize session.jsonl --max-chunk-tokens 30000
python gpt5_cli.py optimize session.jsonl --context-overlap 2000

# Use auto-strategy selection
python gpt5_cli.py optimize session.jsonl --auto-strategy
```

#### Cost Analysis Inaccuracies
**Symptoms**:
- Cost estimates don't match actual usage
- Negative cost savings reported
- Inconsistent pricing calculations

**Diagnosis**:
```bash
# Validate cost configuration
python gpt5_cli.py status --cost-config

# Test cost calculations
python -c "from src.size_analyzer import SizeAnalyzer; analyzer = SizeAnalyzer(); print(analyzer.get_pricing_info())"
```

**Solutions**:
```bash
# Update pricing configuration
python gpt5_cli.py config --update-pricing

# Recalibrate cost models
python gpt5_cli.py calibrate --cost-models

# Use manual cost override
python gpt5_cli.py optimize session.jsonl --input-cost 0.025 --output-cost 0.05
```

### 5. CLI and Interface Issues

#### Command Not Found or Execution Errors
**Symptoms**:
- `python: can't open file 'gpt5_cli.py'`
- Permission denied errors
- Command parsing failures

**Diagnosis**:
```bash
# Check file permissions
ls -la gpt5_cli.py payload_cli.py size_reporter.py

# Test Python execution
python --version
which python
```

**Solutions**:
```bash
# Navigate to correct directory
cd /home/opsvi/master_root/apps/session-optimizer

# Fix permissions
chmod +x gpt5_cli.py payload_cli.py size_reporter.py

# Use absolute paths
python /home/opsvi/master_root/apps/session-optimizer/gpt5_cli.py status
```

#### Output Format Issues
**Symptoms**:
- Malformed HTML/JSON output
- Missing visualization elements
- Dashboard rendering problems

**Diagnosis**:
```bash
# Test output formats
python size_reporter.py analyze session.jsonl --format json --validate
python size_reporter.py analyze session.jsonl --format html --validate
```

**Solutions**:
```bash
# Force output format
python size_reporter.py analyze session.jsonl --format html --force-render

# Use text fallback
python size_reporter.py analyze session.jsonl --format text

# Debug output generation
python size_reporter.py analyze session.jsonl --debug-output
```

## 🔬 Advanced Diagnostics

### System Health Monitoring

#### Complete System Diagnostic
```bash
#!/bin/bash
# Run comprehensive system health check

echo "=== Session Optimizer Health Check ==="

echo "1. Python Environment:"
python --version
which python

echo "2. Dependencies:"
python -c "import tiktoken; print(f'tiktoken: {tiktoken.__version__}')"

echo "3. Component Health:"
python test_gpt5_system.py --health-check

echo "4. Integration Status:"
python test_enhanced_integration.py --integration-check

echo "5. Performance Baseline:"
python gpt5_cli.py test --benchmark

echo "6. Memory Usage:"
python -c "import psutil; print(f'Available Memory: {psutil.virtual_memory().available / 1024**3:.2f} GB')"

echo "7. Session Analytics Engine:"
python -c "from session_analytics_engine import SessionAnalyticsEngine; print('SessionAnalyticsEngine: OK')"

echo "=== Health Check Complete ==="
```

#### Performance Profiling
```python
# profile_session_optimization.py
import cProfile
import pstats
from src.gpt5_payload_system import GPT5PayloadSystem

def profile_optimization():
    system = GPT5PayloadSystem()
    result = system.optimize_session_file("test_sessions/sample_session.jsonl")
    return result

if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()

    result = profile_optimization()

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions
```

### Component-Specific Diagnostics

#### SessionAnalyticsEngine Diagnostic
```python
# test_session_analytics_health.py
from session_analytics_engine import SessionAnalyticsEngine
import json

def diagnose_session_analytics():
    try:
        engine = SessionAnalyticsEngine()

        # Test basic functionality
        test_session = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ]
        }

        result = engine.analyze_session_data(test_session)
        print("✅ SessionAnalyticsEngine basic functionality: OK")

        # Test file processing
        result = engine.analyze_session("test_sessions/sample_session.jsonl")
        print("✅ SessionAnalyticsEngine file processing: OK")

        return True

    except Exception as e:
        print(f"❌ SessionAnalyticsEngine error: {e}")
        return False
```

#### GPT5PayloadSystem Diagnostic
```python
# test_gpt5_system_health.py
from src.gpt5_payload_system import GPT5PayloadSystem

def diagnose_gpt5_system():
    try:
        system = GPT5PayloadSystem()

        # Test configuration
        config = system.get_configuration()
        print(f"✅ GPT5PayloadSystem configuration: {config}")

        # Test token analysis
        analyzer = system.token_analyzer
        result = analyzer.count_tokens("Test message")
        print(f"✅ Token counting: {result} tokens")

        # Test chunking
        chunker = system.chunking_engine
        test_data = {"messages": [{"role": "user", "content": "Test"}]}
        chunks = chunker.chunk_session(test_data, "adaptive")
        print(f"✅ Chunking engine: {len(chunks.chunks)} chunks")

        return True

    except Exception as e:
        print(f"❌ GPT5PayloadSystem error: {e}")
        return False
```

## 📊 Performance Optimization

### Memory Optimization Strategies

#### For Large Sessions (>1GB)
```bash
# Enable all memory optimizations
python gpt5_cli.py optimize large_session.jsonl \
  --memory-efficient \
  --streaming \
  --memory-limit 1024 \
  --chunk-size 25000 \
  --gc-threshold 100
```

#### For Batch Processing
```bash
# Optimize for throughput
python gpt5_cli.py batch sessions/ \
  --parallel \
  --max-workers 8 \
  --memory-per-worker 512 \
  --queue-size 20
```

### Speed Optimization

#### CPU-Bound Optimization
```bash
# Maximize CPU utilization
python gpt5_cli.py optimize session.jsonl \
  --fast-mode \
  --parallel-chunks \
  --aggressive-caching \
  --skip-validation
```

#### I/O-Bound Optimization
```bash
# Optimize file operations
python gpt5_cli.py batch sessions/ \
  --io-threads 4 \
  --buffer-size 1048576 \
  --preload-sessions \
  --async-io
```

## 🛡️ Error Recovery Procedures

### Corrupted Session Recovery
```bash
# Attempt automatic recovery
python claude_session_analyzer.py corrupted_session.jsonl --auto-fix --backup

# Manual validation and repair
python claude_session_analyzer.py corrupted_session.jsonl --validate --repair

# Extract partial data
python claude_session_analyzer.py corrupted_session.jsonl --partial-recovery
```

### Failed Optimization Recovery
```bash
# Resume from checkpoint
python gpt5_cli.py resume optimization_checkpoint.json

# Retry with different strategy
python gpt5_cli.py optimize session.jsonl --strategy conversation --force-retry

# Fallback to minimal optimization
python gpt5_cli.py optimize session.jsonl --minimal-mode --no-analytics
```

### System State Reset
```bash
# Clear all caches and temporary files
python gpt5_cli.py cleanup --deep

# Reset configuration to defaults
python gpt5_cli.py config --reset

# Rebuild all indices
python gpt5_cli.py rebuild --all
```

## 📞 Support and Escalation

### Self-Service Diagnostics
1. **Run health check**: `python gpt5_cli.py status --detailed`
2. **Check logs**: Review `optimization.log` and `error.log`
3. **Validate environment**: `python test_integration.py`
4. **Performance test**: `python gpt5_cli.py test --benchmark`

### Issue Documentation Template
When reporting issues, include:

```
**Environment:**
- Python version:
- Operating system:
- Available memory:
- Session optimizer version:

**Issue Description:**
- What were you trying to do?
- What happened instead?
- Error messages (if any):

**Reproduction Steps:**
1.
2.
3.

**Diagnostic Output:**
```bash
python gpt5_cli.py status --detailed
```

**Session Information:**
- Session size: X tokens
- Session format: Claude .jsonl / Other
- Optimization strategy attempted:
```

### Known Issues and Workarounds

#### Issue: Large sessions cause memory spikes
**Workaround**: Use streaming mode with memory limits
```bash
python gpt5_cli.py stream session.jsonl --memory-limit 1024
```

#### Issue: Poor compression on dialogue-heavy sessions
**Workaround**: Use conversation strategy explicitly
```bash
python gpt5_cli.py optimize session.jsonl --strategy conversation
```

#### Issue: Batch processing stops unexpectedly
**Workaround**: Enable checkpoint mode for resumability
```bash
python gpt5_cli.py batch sessions/ --checkpoint-interval 10
```

## 🔧 Emergency Procedures

### Critical System Failure
```bash
# Emergency reset sequence
cd /home/opsvi/master_root/apps/session-optimizer

# 1. Stop all running processes
pkill -f "gpt5_cli.py"
pkill -f "payload_cli.py"
pkill -f "size_reporter.py"

# 2. Clear locks and temporary files
rm -f *.lock
rm -rf temp/*
rm -rf cache/*

# 3. Reset system state
python gpt5_cli.py emergency-reset

# 4. Validate system health
python test_integration.py --emergency-check

# 5. Restart with minimal configuration
python gpt5_cli.py status --minimal
```

### Data Recovery
```bash
# Recover optimization results from logs
python gpt5_cli.py recover --from-logs optimization.log

# Restore from backup
python gpt5_cli.py restore --backup backup_YYYYMMDD.tar.gz

# Rebuild from source data
python gpt5_cli.py rebuild --from-sessions /path/to/original/sessions
```

---

## 📋 Troubleshooting Checklist

### Pre-Optimization Checklist
- [ ] Python 3.9+ installed and accessible
- [ ] tiktoken dependency installed and working
- [ ] Sufficient memory available (2GB+ for large sessions)
- [ ] Session files are accessible and readable
- [ ] SessionAnalyticsEngine integration functional

### During Optimization Checklist
- [ ] Monitor memory usage with `--memory-monitor`
- [ ] Check progress with `--verbose` output
- [ ] Validate intermediate results if possible
- [ ] Monitor system resources (CPU, memory, disk)
- [ ] Watch for error messages or warnings

### Post-Optimization Checklist
- [ ] Verify compression ratios meet expectations
- [ ] Validate cost savings calculations
- [ ] Check output file integrity
- [ ] Review optimization logs for warnings
- [ ] Test optimized payloads if possible

### Performance Troubleshooting Checklist
- [ ] Baseline performance with `python gpt5_cli.py test --benchmark`
- [ ] Compare with expected metrics (5,300+ tokens/sec)
- [ ] Check memory usage patterns
- [ ] Validate chunking strategy selection
- [ ] Review system resource utilization

---

**🛠️ Session Optimizer Troubleshooting Guide v1.0**
**🚨 Emergency Support • 🔧 Self-Service Diagnostics • 📊 Performance Optimization**
