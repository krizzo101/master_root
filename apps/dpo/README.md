# DPO Request Analyzer Component

## Overview

The Request Analyzer is the first component of the Development Process Orchestrator (DPO) system. It processes natural language development requests and transforms them into structured data for comprehensive SDLC workflow generation.

## Features

✅ **Natural Language Processing**: Parses user development requests for key information
✅ **Project Classification**: Identifies 9+ project types (API, Frontend, Full-stack, CLI, etc.)
✅ **Complexity Assessment**: Evaluates project complexity (Simple to Enterprise)
✅ **Technology Detection**: Extracts programming languages, frameworks, databases, and tools
✅ **Context Enrichment**: Adds ecosystem-specific context and optimization focus
✅ **SDLC Phase Generation**: Determines appropriate development phases
✅ **Agent Estimation**: Calculates required agents (5-25 based on complexity)
✅ **Validation System**: Ensures analysis completeness and accuracy

## Quick Start

```python
from request_analyzer import RequestAnalyzer

# Initialize
analyzer = RequestAnalyzer()

# Analyze a request
request = "Build a REST API for user management with JWT authentication"
analysis = analyzer.analyze(request)

# Use the results
print(f"Project Type: {analysis.project_type.value}")
print(f"Complexity: {analysis.complexity.value}")
print(f"Estimated Agents: {analysis.estimated_agents}")
```

## Installation

```bash
cd /home/opsvi/master_root/apps/dpo
# No additional dependencies required - uses Python standard library
```

## Testing

Run the comprehensive test suite:

```bash
python tests/test_request_analyzer.py
```

All 21 tests passing ✅

## Integration Example

See `examples/integration_example.py` for complete orchestrator integration:

```bash
python examples/integration_example.py
```

This generates workflow JSON files ready for orchestrator execution.

## Project Structure

```
dpo/
├── src/
│   └── request_analyzer.py      # Main component implementation
├── tests/
│   └── test_request_analyzer.py # Comprehensive test suite
├── docs/
│   └── REQUEST_ANALYZER.md      # Detailed documentation
├── examples/
│   └── integration_example.py   # Orchestrator integration demo
└── README.md                     # This file
```

## Supported Project Types

- **Backend API**: REST APIs, GraphQL services
- **Frontend App**: Web UIs, dashboards, SPAs
- **Full Stack**: Complete web applications
- **CLI Tool**: Command-line utilities
- **Library**: Reusable packages and SDKs
- **Integration**: Connectors and bridges
- **Data Pipeline**: ETL and streaming systems
- **Microservice**: Containerized services
- **Automation**: Workflow and orchestration tools

## Output Format

The analyzer produces structured `RequestAnalysis` objects containing:
- Project type and complexity level
- Technology stack (languages, frameworks, databases, tools)
- SDLC phases and estimated agent count
- Focus areas and requirements
- Constraints and implicit requirements
- Ecosystem context and integration opportunities
- Confidence score for the analysis

## Performance

- Analysis completes in < 100ms
- Pattern matching optimized with compiled regex
- Lightweight design for real-time processing
- No external dependencies required

## Integration with DPO System

The Request Analyzer integrates seamlessly with:
- **Intelligence Review Engine**: Enhances specifications
- **SDLC Template System**: Selects appropriate templates
- **Context Injection System**: Provides ecosystem context
- **Orchestrator Integration**: Generates workflow JSON

## Future Enhancements

- Machine learning-based classification
- Multi-language request support
- Custom domain-specific analyzers
- Learning from completed workflows

## License

Part of the DPO system in the master_root ecosystem
