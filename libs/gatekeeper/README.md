# Gatekeeper Module

A reusable module for intelligent file dependency analysis and context management. Can be integrated into any agent that needs to analyze file relationships and optimize context for LLM processing.

## Overview

The Gatekeeper Module provides intelligent context management by:
1. **Auto-attaching related files** based on import relationships and directory structure
2. **Analyzing user requests** to determine what context is needed
3. **Optimizing file selection** to provide the most relevant context for LLM processing
4. **Managing context confidence** to ensure quality recommendations

## Components

### 1. AutoAttach (`auto_attach.py`)

Provides intelligent file dependency analysis using optimized file dependencies.

**Features:**
- O(1) file lookups using pre-computed indexes
- Finds imported files and files that import the target
- Discovers files in the same directory
- Identifies related configuration and test files
- Provides detailed analysis and filtering

**Usage:**
```python
from gatekeeper import AutoAttach

auto_attach = AutoAttach(".proj-intel/file_dependencies.json")
auto_attach.load_dependencies()

# Find related files
related_files = auto_attach.find_related_files(["path/to/file.py"])
print(f"Found {len(related_files)} related files")

# Get detailed analysis
analysis = auto_attach.analyze_file_dependencies("path/to/file.py")
print(f"File imports: {analysis['imports']}")
print(f"Imported by: {len(analysis['imported_by'])} files")
```

### 2. ContextAnalyzer (`context_analyzer.py`)

Analyzes user requests to determine optimal context for LLM processing.

**Features:**
- Classifies requests by type (bug fix, feature development, testing, etc.)
- Generates context recommendations based on request type
- Provides confidence scores for recommendations
- Supports filtering by confidence and priority

**Usage:**
```python
from gatekeeper import ContextAnalyzer

analyzer = ContextAnalyzer()

# Analyze a request
analysis = analyzer.analyze_request(
    "Fix the authentication bug in the security module",
    ["libs/security/auth.py"]
)

print(f"Request type: {analysis.analysis_summary}")
print(f"Confidence: {analysis.confidence_score:.2f}")
print(f"Recommendations: {len(analysis.recommended_context)}")
```

### 3. GatekeeperAgent (`gatekeeper_agent.py`)

Main agent that combines auto-attach and context analysis functionality.

**Features:**
- Processes user requests to determine optimal context
- Combines auto-attach and context analysis
- Filters and prioritizes files based on relevance
- Provides comprehensive results with confidence scores
- Supports export of results for inspection

**Usage:**
```python
from gatekeeper import GatekeeperAgent

gatekeeper = GatekeeperAgent(".proj-intel/file_dependencies.json")
gatekeeper.set_verbose(True)  # Enable detailed logging

# Process a request
result = gatekeeper.process_request(
    user_request="Add error handling to the authentication module",
    user_files=["libs/security/auth.py"],
    max_files=20,
    min_confidence=0.5
)

print(f"Original files: {len(result.original_files)}")
print(f"Final files: {len(result.final_files)}")
print(f"Confidence: {result.confidence_score:.2f}")
print(f"Summary: {result.processing_summary}")

# Export result for inspection
gatekeeper.export_result(result, "gatekeeper_result.json")
```

## Request Classification

The ContextAnalyzer classifies requests into the following categories:

### Bug Fix
- **Keywords**: bug, fix, error, issue, problem, broken, failing, crash
- **Context**: Problematic code, related modules, error handling

### Feature Development
- **Keywords**: add, implement, create, new feature, enhancement, improve, extend
- **Context**: Related modules, interfaces, configuration

### Refactoring
- **Keywords**: refactor, clean up, restructure, reorganize, optimize, simplify
- **Context**: Dependencies, usage patterns, related code

### Testing
- **Keywords**: test, unit test, integration test, coverage, test case, assertion
- **Context**: Test files, test configuration, testing utilities

### Documentation
- **Keywords**: document, comment, readme, docs, explain, describe, clarify
- **Context**: Existing documentation, examples, related docs

### Configuration
- **Keywords**: config, setting, environment, deploy, setup, install, dependency
- **Context**: Configuration files, deployment scripts, dependencies

### Performance
- **Keywords**: performance, speed, slow, optimize, efficient, memory, cpu
- **Context**: Code being optimized, performance monitoring

### Security
- **Keywords**: security, vulnerability, secure, authentication, authorization
- **Context**: Security-related code, authentication modules

## Integration Examples

### Basic Integration
```python
from gatekeeper import GatekeeperAgent

# Initialize gatekeeper
gatekeeper = GatekeeperAgent()
gatekeeper.load_dependencies()

# Process user request
result = gatekeeper.process_request(
    user_request="Fix the login bug",
    user_files=["auth/login.py"]
)

# Use the optimized file list
optimized_files = result.final_files
print(f"Using {len(optimized_files)} files for context")
```

### Advanced Integration with Custom Settings
```python
from gatekeeper import GatekeeperAgent

gatekeeper = GatekeeperAgent()
gatekeeper.set_verbose(True)

# Process with custom parameters
result = gatekeeper.process_request(
    user_request="Implement user management features",
    user_files=["models/user.py", "controllers/user_controller.py"],
    max_files=30,  # Allow more files for complex features
    min_confidence=0.3  # Lower confidence threshold
)

# Check confidence and adjust if needed
if result.confidence_score < 0.5:
    print("Warning: Low confidence in context selection")

# Use the result
context_files = result.final_files
analysis_summary = result.processing_summary
```

### Integration with LLM Agent
```python
from gatekeeper import GatekeeperAgent

class MyAgent:
    def __init__(self):
        self.gatekeeper = GatekeeperAgent()
        self.gatekeeper.load_dependencies()

    def process_user_request(self, request, user_files=None):
        # Use gatekeeper to optimize context
        gatekeeper_result = self.gatekeeper.process_request(
            request, user_files or [], max_files=25
        )

        # Prepare context for LLM
        context_files = gatekeeper_result.final_files
        context_summary = gatekeeper_result.processing_summary

        # Send to LLM with optimized context
        llm_response = self.send_to_llm(request, context_files, context_summary)

        return llm_response
```

## Configuration

### Dependencies File
The gatekeeper requires a `file_dependencies.json` file generated by the auto-attach generator:

```bash
# Generate dependencies from project map
python scripts/auto_attach_generator.py --project-map .proj-intel/project_map.yaml --output .proj-intel/file_dependencies.json
```

### Custom Dependencies Path
```python
# Use custom dependencies file
gatekeeper = GatekeeperAgent("/path/to/custom/dependencies.json")
```

## Performance Characteristics

- **File Lookup**: O(1) using dictionary keys
- **Directory Queries**: O(1) using pre-computed indexes
- **Import Queries**: O(1) using pre-computed indexes
- **Request Analysis**: O(n) where n is the number of keywords
- **Context Processing**: O(m) where m is the number of files

## Testing

Run the comprehensive test suite:

```bash
cd libs/gatekeeper
python test_gatekeeper.py
```

The test suite covers:
- Context analyzer functionality
- Auto-attach functionality
- Gatekeeper agent scenarios
- Integration testing

## Benefits

1. **Intelligent Context Selection**: Automatically finds the most relevant files
2. **Performance Optimized**: O(1) lookups for all operations
3. **Request-Aware**: Adapts context based on request type
4. **Confidence Scoring**: Provides confidence in context selection
5. **Reusable**: Can be integrated into any agent
6. **Configurable**: Supports custom parameters and thresholds

## Future Enhancements

- Support for more request types and patterns
- Enhanced file prioritization algorithms
- Integration with project-specific rules
- Real-time dependency updates
- Advanced filtering and ranking
- Support for different programming languages
- Integration with version control systems

## Dependencies

- Python 3.8+
- JSON file with optimized file dependencies
- No external dependencies required

## License

This module is part of the OPSVI project and follows the same licensing terms.
