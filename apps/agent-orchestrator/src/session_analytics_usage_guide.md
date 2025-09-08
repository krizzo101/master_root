# SessionAnalyticsEngine Usage Guide

## Overview
The SessionAnalyticsEngine is a comprehensive system for analyzing Claude session logs from .jsonl files. It extends existing chat parsing infrastructure with modular, reusable components designed for performance and extensibility.

## Quick Start

### Basic Usage
```python
from session_analytics_engine import SessionAnalyticsEngine

# Initialize with default Claude projects directory
engine = SessionAnalyticsEngine()

# Analyze all sessions
results = engine.analyze_all_sessions()

# Export results
engine.export_analytics(results, '/path/to/output/analytics.json')
```

### Custom Directory
```python
# Initialize with custom directory
engine = SessionAnalyticsEngine('/path/to/claude/sessions')
```

## Architecture

### Core Components
1. **SessionLogParser** - Parses .jsonl files from Claude projects
2. **ConversationAnalyzer** - Analyzes conversation patterns and flow
3. **ToolUsageAnalyzer** - Tracks tool usage and performance
4. **FileOperationAnalyzer** - Analyzes file operations and modifications
5. **SessionAnalyticsEngine** - Main coordinator that orchestrates all analyses

### Modular Analytics Components
- **SessionMetricsExtractor** - Basic session metrics (duration, messages, etc.)
- **ToolUsageExtractor** - Tool usage statistics and success rates
- **FileActivityExtractor** - File operations and modification patterns
- **URLAccessExtractor** - Web access and URL patterns
- **ConversationFlowExtractor** - Message flow and conversation analysis

## Key Features

### 1. Comprehensive Session Metrics
```python
# Extract basic metrics for each session
metrics = engine.analyze_single_session(session_file)
print(f"Duration: {metrics[0].duration_minutes} minutes")
print(f"Messages: {metrics[0].total_messages}")
print(f"Tool Calls: {metrics[0].total_tool_calls}")
```

### 2. Cross-Session Analytics
```python
results = engine.analyze_all_sessions()
insights = results['cross_session_insights']

# Popular tools across all sessions
popular_tools = insights['most_popular_tools']
print(f"Most used tool: {popular_tools[0]}")

# File type distribution
file_types = insights['file_type_distribution']
print(f"Most common file type: {file_types[0]}")
```

### 3. Modular Component Usage
```python
from analytics_components import default_registry

# Use individual components
tool_component = default_registry.get_component('tool_usage')
results = tool_component.analyze(session_data)

# Run all components
all_results = default_registry.run_all_components(session_data)
```

### 4. Custom Component Extension
```python
from analytics_components import AnalyticsComponent, default_registry

class CustomAnalyticsComponent(AnalyticsComponent):
    def __init__(self):
        super().__init__("MyCustomAnalyzer")

    def analyze(self, session_data):
        # Custom analysis logic
        return {"custom_metric": 42}

    def get_schema(self):
        return {"type": "object", "properties": {"custom_metric": {"type": "integer"}}}

# Register and use
default_registry.register_component('custom_analyzer', CustomAnalyticsComponent)
```

## Analytics Output Structure

### Session Metrics
```json
{
  "session_id": "unique-session-id",
  "start_time": "2025-09-08T12:00:00Z",
  "end_time": "2025-09-08T12:30:00Z",
  "duration_minutes": 30.0,
  "total_messages": 15,
  "user_messages": 8,
  "assistant_messages": 7,
  "total_tool_calls": 5,
  "unique_tools_used": 3,
  "total_file_operations": 10,
  "unique_files_touched": 4,
  "working_directory": "/path/to/work",
  "git_branch": "main"
}
```

### Tool Usage Analytics
```json
{
  "session_id": "unique-session-id",
  "tool_name": "Read",
  "usage_count": 5,
  "success_rate": 1.0,
  "average_execution_time": 0.5,
  "error_patterns": [],
  "parameter_patterns": {"file_path": 5}
}
```

### Cross-Session Insights
```json
{
  "most_popular_tools": [["TodoWrite", 1232], ["Bash", 1203]],
  "file_type_distribution": [[".py", 6958], [".md", 3389]],
  "session_duration_patterns": {
    "short_sessions_under_5min": 1126,
    "medium_sessions_5_30min": 347,
    "long_sessions_over_30min": 411
  }
}
```

## Performance Considerations

### Optimizations
- **Concurrent Processing**: Can be extended for parallel session analysis
- **Caching**: Built-in caching for repeated analyses
- **Memory Management**: Efficient handling of large session files
- **Error Resilience**: Individual session failures don't break overall analysis

### Large Dataset Handling
```python
# For very large datasets, process in batches
engine = SessionAnalyticsEngine()
session_files = engine.session_parser.find_session_files()

batch_size = 100
for i in range(0, len(session_files), batch_size):
    batch = session_files[i:i+batch_size]
    # Process batch and save intermediate results
```

## Environment Variables

The system respects the `CLAUDE_PROJECT_ROOT` environment variable:
```bash
export CLAUDE_PROJECT_ROOT=/path/to/claude/projects
```

## Test Results Summary

Based on real-world testing with 2,501 Claude session files:

### Successfully Analyzed
- **1,884 sessions** processed successfully
- **1,885+ hours** of total session time
- **240,969 messages** analyzed
- **83,022 tool calls** tracked
- **25,530 file operations** recorded

### Error Handling
- Graceful handling of malformed/different format files
- Individual session failures don't stop overall analysis
- Comprehensive error logging and reporting

### Performance Metrics
- Average parsing time: ~0.5-1.0 seconds per session file
- Memory efficient handling of large datasets
- Robust cross-session pattern recognition

## Common Use Cases

### 1. Productivity Analysis
```python
# Analyze tool usage efficiency
results = engine.analyze_all_sessions()
tool_stats = results['tool_usage_analytics']

# Find most productive sessions
productive_sessions = [s for s in results['session_metrics']
                      if s.total_tool_calls > 20 and s.duration_minutes < 30]
```

### 2. Workflow Optimization
```python
# Identify common file operation patterns
file_ops = results['file_operation_analytics']
heavy_edit_files = [f for f in file_ops if f.total_operations > 10]

# Find session bottlenecks
long_sessions = [s for s in results['session_metrics']
                if s.duration_minutes > 60]
```

### 3. Usage Pattern Discovery
```python
# Cross-session insights for pattern recognition
insights = results['cross_session_insights']
peak_hours = insights['peak_usage_hours']
duration_patterns = insights['session_duration_patterns']
```

## Extension Points

### Custom Analytics Components
1. Implement `AnalyticsComponent` base class
2. Register with `default_registry`
3. Integrate with main analytics engine

### Data Export Formats
Currently supports JSON export. Can be extended for:
- CSV export for spreadsheet analysis
- Database integration (PostgreSQL/SQLite)
- Real-time streaming analytics
- Dashboard integration

## Troubleshooting

### Common Issues
1. **No sessions found**: Check `CLAUDE_PROJECT_ROOT` path
2. **Parse errors**: Ensure .jsonl files are valid Claude exports
3. **Memory issues**: Process large datasets in batches
4. **Performance**: Use specific components instead of full analysis

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

engine = SessionAnalyticsEngine()
# Detailed logging will show parsing and analysis steps
```

## Integration with Existing Infrastructure

The SessionAnalyticsEngine is designed to complement existing chat parsing infrastructure:
- Compatible with existing `ChatLogParser` patterns
- Extends `ChatReportGenerator` functionality
- Integrates with PostgreSQL chat ingestion systems
- Supports existing database schemas

This makes it easy to incorporate into existing workflows and monitoring systems.
