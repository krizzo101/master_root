# Request Analyzer Component Documentation

## Overview

The Request Analyzer is a critical component of the Development Process Orchestrator (DPO) system. It processes natural language development requests and transforms them into structured data that can be used to generate comprehensive SDLC workflows.

## Architecture

### Core Components

1. **RequestAnalyzer Class**: Main analyzer that coordinates all processing
2. **ProjectType Enum**: Categorizes projects (API, Frontend, Full-stack, etc.)
3. **ComplexityLevel Enum**: Assesses project complexity (Simple to Enterprise)
4. **TechnologyStack**: Captures identified technologies and frameworks
5. **RequestAnalysis**: Complete analysis result with all extracted information

### Processing Pipeline

```
User Request → Normalization → Classification → Tech Extraction →
Complexity Assessment → Phase Determination → Context Enrichment →
Validation → RequestAnalysis Output
```

## Features

### Project Type Classification

Automatically identifies project types:
- **Backend API**: REST APIs, GraphQL services, microservices
- **Frontend App**: Web UIs, dashboards, SPAs
- **Full Stack**: Complete web applications
- **CLI Tool**: Command-line utilities
- **Library**: Reusable packages and SDKs
- **Integration**: Connectors and bridges
- **Data Pipeline**: ETL and streaming systems
- **Microservice**: Containerized services
- **Automation**: Workflow and orchestration tools

### Technology Detection

Extracts mentioned technologies:
- **Languages**: Python, JavaScript, TypeScript, Go, Rust, Java, C#
- **Frameworks**: FastAPI, Django, Flask, Express, React, Vue, Angular
- **Databases**: PostgreSQL, MySQL, MongoDB, Redis, SQLite
- **Tools**: Docker, Kubernetes, JWT, OAuth, WebSockets, Message Queues

### Complexity Assessment

Evaluates project complexity based on:
- Explicit complexity indicators in request
- Number of features required
- Technology stack complexity
- Integration requirements

Complexity levels determine:
- **Simple**: 5-8 agents
- **Moderate**: 9-15 agents
- **Complex**: 16-20 agents
- **Enterprise**: 21-25 agents

### Context Enrichment

Adds ecosystem-specific context:
- Available tools in master_root ecosystem
- Integration opportunities
- Performance targets for solo developer
- Reusable components from existing systems

## Usage

### Basic Usage

```python
from request_analyzer import RequestAnalyzer

# Initialize analyzer
analyzer = RequestAnalyzer()

# Analyze a request
request = "Build a REST API for user management with JWT authentication"
analysis = analyzer.analyze(request)

# Access results
print(f"Project Type: {analysis.project_type.value}")
print(f"Complexity: {analysis.complexity.value}")
print(f"Estimated Agents: {analysis.estimated_agents}")
print(f"Tech Stack: {analysis.tech_stack.to_dict()}")
print(f"Phases: {analysis.phases}")
print(f"Focus Areas: {analysis.focus_areas}")
```

### Advanced Usage with Validation

```python
# Analyze request
analysis = analyzer.analyze(request)

# Validate the analysis
is_valid, issues = analyzer.validate_analysis(analysis)

if not is_valid:
    print("Analysis validation failed:")
    for issue in issues:
        print(f"  - {issue}")
else:
    # Proceed with workflow generation
    workflow_json = analysis.to_dict()
```

## Output Format

The RequestAnalysis object provides structured output:

```json
{
  "original_request": "User's request text",
  "project_type": "backend_api",
  "complexity": "moderate",
  "tech_stack": {
    "languages": ["python"],
    "frameworks": ["fastapi"],
    "databases": ["postgresql"],
    "tools": ["jwt", "docker"],
    "integrations": []
  },
  "phases": [
    "requirements",
    "architecture",
    "api_design",
    "implementation",
    "testing",
    "documentation",
    "deployment"
  ],
  "estimated_agents": 12,
  "focus_areas": [
    "api_design",
    "security",
    "performance",
    "documentation"
  ],
  "requirements": {
    "functional": ["user authentication", "data validation"],
    "non_functional": ["high performance", "secure"],
    "features": ["user management", "JWT tokens"],
    "constraints": []
  },
  "constraints": [
    "scope: single developer",
    "limitation: no enterprise complexity"
  ],
  "implicit_requirements": [
    "RESTful design principles",
    "Input validation and sanitization",
    "Error handling and status codes",
    "API documentation (OpenAPI/Swagger)"
  ],
  "ecosystem_context": {
    "environment": "master_root ecosystem",
    "optimization_focus": "solo developer efficiency",
    "available_tools": [
      "agent-orchestrator",
      "knowledge_system (mcp__knowledge)",
      "monitoring-dashboard"
    ],
    "integration_opportunities": [
      "monitoring-dashboard integration"
    ],
    "performance_targets": {
      "response_time": "< 100ms for API calls",
      "startup_time": "< 2 seconds",
      "memory_usage": "< 500MB"
    },
    "reusable_components": [
      "TokenPool from orchestrator",
      "AsyncIO patterns"
    ]
  },
  "confidence_score": 0.85
}
```

## Integration with DPO System

The Request Analyzer integrates with other DPO components:

1. **Intelligence Review Engine**: Uses analysis to enhance specifications
2. **SDLC Template System**: Selects templates based on project type
3. **Context Injection System**: Provides ecosystem context to agents
4. **Orchestrator Integration**: Converts analysis to workflow JSON

### Example Integration Flow

```python
class DevelopmentProcessOrchestrator:
    def __init__(self):
        self.request_analyzer = RequestAnalyzer()
        # ... other components

    def process_development_request(self, request: str):
        # Step 1: Analyze request
        analysis = self.request_analyzer.analyze(request)

        # Step 2: Validate analysis
        is_valid, issues = self.request_analyzer.validate_analysis(analysis)
        if not is_valid:
            raise ValueError(f"Invalid request analysis: {issues}")

        # Step 3: Pass to next component
        enhanced_spec = self.intelligence_engine.enhance(analysis)
        # ... continue pipeline
```

## Configuration

The analyzer can be configured with custom patterns:

```python
config = {
    "custom_project_types": {
        "data_science": [r'\bmachine learning\b', r'\bdata science\b']
    },
    "custom_technologies": {
        "ml_frameworks": {
            "tensorflow": [r'\btensorflow\b', r'\btf\b'],
            "pytorch": [r'\bpytorch\b', r'\btorch\b']
        }
    }
}

analyzer = RequestAnalyzer(config=config)
```

## Performance Considerations

- Request analysis typically completes in < 100ms
- Pattern matching is optimized with compiled regex
- Caching can be enabled for repeated requests
- Lightweight design suitable for real-time processing

## Testing

Run the comprehensive test suite:

```bash
cd /home/opsvi/master_root/apps/dpo
python -m pytest tests/test_request_analyzer.py -v
```

Or using unittest:

```bash
python tests/test_request_analyzer.py
```

## Troubleshooting

### Low Confidence Scores

If analysis confidence is consistently low:
- Ensure requests include specific technical details
- Mention explicit technologies and frameworks
- Include clear project requirements

### Unknown Project Type

If project type cannot be determined:
- Add more descriptive keywords (API, frontend, CLI, etc.)
- Specify the type of application being built
- Use standard terminology for project categories

### Incorrect Complexity Assessment

If complexity is misidentified:
- Be explicit about project scope
- Mention specific features and requirements
- Use complexity indicators (simple, complex, enterprise)

## Future Enhancements

Planned improvements:
1. Machine learning-based classification for better accuracy
2. Custom domain-specific analyzers
3. Multi-language request support
4. Integration with GPT models for enhanced NLP
5. Learning from completed workflows to improve analysis
