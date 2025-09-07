# Enhanced Log Tailer - Examples and Demonstrations

## Overview

This directory contains interactive examples and demonstrations for the Enhanced Log Tailer system, showcasing its advanced capabilities including swarm detection, pattern matching, and real-time monitoring.

## Example Scripts

### 1. **log_tailer_examples.py** - Full Feature Demo
Interactive demonstration of all Enhanced Log Tailer features with the full system.

**Features Demonstrated:**
- Basic log tailing with pattern matching
- Advanced swarm behavior detection
- Integration with Agent Orchestrator
- Performance benchmarking
- Custom pattern configuration

**Usage:**
```bash
python log_tailer_examples.py
```

Then select from the interactive menu:
1. Basic Log Tailing - Real-time monitoring with pattern highlighting
2. Swarm Detection - Advanced collective behavior identification
3. Orchestrator Integration - Automated analysis and response
4. Performance Benchmark - Throughput and efficiency testing
5. Custom Patterns - Domain-specific log analysis
6. Run All Demos - Execute complete demonstration suite

### 2. **simple_log_tailer_demo.py** - Standalone Demonstrations
Simplified, dependency-free demonstrations of core log tailing concepts.

**Features Demonstrated:**
- Pattern matching in log files
- Simple swarm detection algorithm
- Real-time monitoring simulation
- Performance analysis

**Usage:**
```bash
python simple_log_tailer_demo.py
```

Automatically runs all demonstrations in sequence.

## Demo Scenarios

### Pattern Matching Demo
Shows how the system identifies and categorizes log entries:
- ERROR detection (database failures, service errors)
- WARNING identification (high resource usage)
- INFO tracking (normal operations)
- Custom pattern support

### Swarm Detection Demo
Demonstrates advanced collective behavior detection:
- Time-based clustering of events
- Agent coordination identification
- Burst pattern recognition
- Confidence scoring

### Real-time Monitoring Demo
Simulates live log monitoring:
- Dynamic event generation
- Color-coded output by severity
- Statistical summaries
- Performance metrics

### Orchestrator Integration Demo
Shows automated response capabilities:
- Task creation and management
- Automated issue detection
- Response action triggering
- Incident tracking

### Performance Benchmarks
Tests system efficiency:
- Line processing throughput (>300,000 lines/second)
- Pattern matching speed
- Memory usage optimization
- Scalability testing

## Key Capabilities Demonstrated

### 1. **High-Performance Processing**
- Asynchronous file monitoring
- Parallel pattern matching
- Efficient buffer management
- Minimal memory footprint

### 2. **Intelligent Pattern Recognition**
- Regex-based pattern matching
- Custom pattern configuration
- Multi-pattern simultaneous detection
- Performance-optimized matching

### 3. **Swarm Behavior Detection**
- Time-window clustering
- Agent coordination tracking
- Burst detection algorithms
- Behavioral pattern classification

### 4. **Interactive Visualization**
- Color-coded severity levels
- Real-time statistics
- Progress indicators
- Summary reports

### 5. **Integration Features**
- Orchestrator compatibility
- Task automation support
- Alert generation
- Incident management

## Example Output

### Pattern Matching Results
```
📊 Pattern Match Results:
  ERROR     :   5 ██
  WARNING   :   5 ██
  INFO      :  40 ████████████████████
```

### Swarm Detection Output
```
🎯 Detected 6 swarm clusters:
  Timestamp: 2025-09-07T06:30:15
  Agents: 6 agents
  IDs: 003, 004, 005, 002, 006...
```

### Performance Metrics
```
📖 Testing read performance...
  Read 10,000 lines in 0.001s
  Throughput: 7,634,048 lines/second
```

## Educational Value

These examples serve multiple purposes:

1. **Learning Tool** - Understand log tailing concepts and implementation
2. **Testing Framework** - Validate system functionality
3. **Performance Baseline** - Establish performance expectations
4. **Integration Guide** - Show how to integrate with other systems
5. **Pattern Library** - Demonstrate various pattern configurations

## Customization

Both demo scripts can be easily modified to:
- Add new pattern types
- Adjust swarm detection parameters
- Modify performance test sizes
- Create custom scenarios
- Test specific use cases

## Requirements

### For log_tailer_examples.py:
- Python 3.8+
- enhanced_swarm_log_tailer module
- src.generic_orchestrator module

### For simple_log_tailer_demo.py:
- Python 3.8+
- No external dependencies (standalone)

## Best Practices Demonstrated

1. **Asynchronous Processing** - Non-blocking I/O operations
2. **Resource Management** - Proper cleanup and memory management
3. **Error Handling** - Graceful degradation and recovery
4. **Performance Optimization** - Efficient algorithms and data structures
5. **User Experience** - Clear feedback and intuitive interfaces

## Conclusion

These examples provide a comprehensive demonstration of the Enhanced Log Tailer's capabilities, from basic pattern matching to advanced swarm detection and orchestrator integration. They serve as both educational tools and practical templates for implementing log monitoring solutions in production environments.