# OPSVI Library Ecosystem

A comprehensive, AI-driven library ecosystem for building autonomous, multi-agent AI/ML operations systems with observability, RAG, and MCP integration.

## Overview

The OPSVI Library Ecosystem is designed to enforce **DRY (Don't Repeat Yourself)** principles while providing a robust foundation for AI/ML applications. It consists of 16 specialized libraries organized into 4 categories, each serving specific domains within the AI operations landscape.

## Architecture

### Library Categories

#### 🏗️ **Core Libraries**
- **`opsvi-foundation`** - Base components, configuration, exceptions, and utilities
- **`opsvi-core`** - Application-level components and service orchestration

#### 🔌 **Service Libraries**
- **`opsvi-llm`** - Language model integration and management
- **`opsvi-rag`** - Retrieval Augmented Generation systems
- **`opsvi-http`** - HTTP client and server functionality
- **`opsvi-fs`** - File system and storage management
- **`opsvi-data`** - Data management and database access
- **`opsvi-auth`** - Authentication and authorization system
- **`opsvi-memory`** - Memory and caching systems
- **`opsvi-communication`** - Communication and messaging systems
- **`opsvi-monitoring`** - Monitoring and observability
- **`opsvi-security`** - Security and encryption utilities

#### 🎯 **Manager Libraries**
- **`opsvi-agents`** - Multi-agent system management
- **`opsvi-pipeline`** - Data processing pipeline orchestration
- **`opsvi-orchestration`** - Workflow and task orchestration
- **`opsvi-deploy`** - Deployment and infrastructure management
- **`opsvi-gateway`** - Multi-interface gateway and API management

## Multi-Level AI-Driven Development

This ecosystem is designed to be built using a sophisticated multi-level AI-driven development approach:

### Development Levels

1. **Project Level** - Entire OPSVI workspace scope
2. **Category Level** - Library category (core, service, rag, manager)
3. **Library Level** - Individual library scope
4. **Component Level** - Library component (core, config, providers, etc.)
5. **File Level** - Individual file implementation

### AI Agent Workflow

Each level is processed by specialized AI agents:

- **Research Agent** - Performs deep research on relevant topics
- **Context Agent** - Gathers and synthesizes context information
- **Code Agent** - Generates implementation code using templates

## Key Files

### Structure Definition
- **`recommended_structure.yaml`** - Complete library ecosystem definition
  - 16 libraries with detailed specifications
  - Multi-level development process
  - AI development standards and rules
  - Context requirements for each level
  - Template references and file definitions
  - YAML anchor system for reusable template patterns

### Template System
- **`templates.yaml`** - Comprehensive template registry (YAML-driven)
  - Project, category, library, component, and file-level templates
  - Python, configuration, and documentation templates
  - Variable substitution and conditional processing
  - Template processing rules and validation
  - Specialized templates for different library types (core, service, rag, manager)
  - Provider templates (OpenAI, base providers)
  - Event system templates
  - Utility and helper function templates

### Scaffolding Scripts
- **`generate_ecosystem_v2.py`** - **CURRENT** - Advanced ecosystem generator
  - YAML-driven template registry; string substitution with optional conditional blocks
  - YAML anchor resolution (handles both string and dictionary references)
  - Comprehensive variable generation for all library types
  - Template key resolution against `templates.yaml`
  - Error handling and validation
  - Support for all 16 libraries with specialized templates

### Legacy Scripts (Archived)
- **`scaffold_shared_libs.py`** - Individual library scaffolding with DRY analysis
- **`scaffold_all_shared_libs.py`** - Batch library generation with manifest support

## Recent Improvements

### ✅ YAML Anchor Resolution Fix
- **Issue**: YAML anchors were resolving as dictionaries, but generator expected strings
- **Solution**: Updated `generate_ecosystem_v2.py` to handle both string and dictionary anchor references
- **Impact**: Preserves rich template metadata while maintaining compatibility
- **Decision Rationale**: Changed generator instead of YAML to preserve template system design

### ✅ Template System Enhancements
- **Added Specialized Templates**: `core_services_py`, `events_base_py`, `utils_helpers_py`
- **Provider Templates**: `providers_base_py`, `providers_openai_py`
- **Prompt Management**: `prompts_manager_py`
- **Enhanced Test Templates**: Comprehensive test patterns with async support

### ✅ Template Reference Standardization
- **Updated**: All library-specific file references use registry keys (no `.j2` file suffixes)
- **Standardized**: Template naming convention (e.g., `core_base_py` instead of `core_base.py.j2`)
- **Improved**: Template key resolution with multiple fallback strategies

### ✅ Generator Improvements
- **Enhanced Variable Generation**: More comprehensive variables for all library types
- **Better Error Handling**: Graceful fallbacks and informative error messages
- **Template Validation**: Ensures all required templates are available
- **YAML Template Registry**: Rendering via registry-defined templates

## Design Principles

### DRY (Don't Repeat Yourself)
- **Centralized Base Classes** - Common functionality in `opsvi-foundation`
- **Template System** - Reusable patterns for all file types
- **Shared Components** - Symlinks to common files like logging
- **Factory Functions** - Dynamic class generation for specific libraries
- **YAML Anchors** - Reusable template definitions across libraries

### Naming Conventions
- **Directories**: kebab-case (e.g., `opsvi-foundation`)
- **Packages**: snake_case (e.g., `opsvi_foundation`)
- **Classes**: PascalCase (e.g., `OpsviFoundation`)
- **Functions**: snake_case (e.g., `initialize_component`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_TIMEOUT`)
- **Templates**: snake_case with `_py` suffix (e.g., `core_base_py`)

### Code Standards
- **Async/Await** - Throughout for scalability
- **Type Hints** - Comprehensive typing with generics
- **Pydantic** - Configuration validation and data modeling
- **Structured Logging** - With correlation IDs and context
- **Comprehensive Testing** - Unit, integration, and performance tests

## Library Structure

Each library follows a consistent structure:

```
opsvi-library/
├── opsvi_library/
│   ├── __init__.py          # Package initialization
│   ├── core/
│   │   ├── __init__.py      # Core exports
│   │   ├── base.py          # Base classes
│   │   └── services.py      # Service management (for core libraries)
│   ├── config/
│   │   ├── __init__.py      # Config exports
│   │   └── settings.py      # Configuration management
│   ├── exceptions/
│   │   ├── __init__.py      # Exception exports
│   │   └── base.py          # Exception hierarchy
│   ├── providers/
│   │   ├── __init__.py      # Provider exports
│   │   ├── base.py          # Base provider classes
│   │   └── openai.py        # OpenAI provider (for LLM libraries)
│   ├── events/
│   │   ├── __init__.py      # Event exports
│   │   └── base.py          # Event system (for service libraries)
│   └── utils/
│       ├── __init__.py      # Utility exports
│       └── helpers.py       # Utility functions
├── tests/
│   ├── __init__.py
│   └── test_library.py      # Test suite
├── pyproject.toml           # Package configuration
├── README.md               # Documentation
└── logging.py              # Shared logging (symlink)
```

## AI Development Standards

### Code Quality
- **SOLID Principles** - Single responsibility, open/closed, etc.
- **DRY Principle** - Centralize common patterns
- **Comprehensive Documentation** - Google-style docstrings
- **Type Safety** - Full type annotations with MyPy

### Architecture
- **Component-Based Design** - All components inherit from BaseComponent
- **Dependency Injection** - For loose coupling
- **Event-Driven Communication** - Between components
- **Configuration-Driven** - Behavior and settings

### Error Handling
- **Hierarchical Exceptions** - Custom exception hierarchies
- **Context Preservation** - Include operation and parameters
- **Recovery Strategies** - Provide recovery suggestions
- **Structured Logging** - Appropriate log levels

### Performance
- **Async/Await** - For I/O operations
- **Connection Pooling** - For external services
- **Caching Strategies** - For expensive operations
- **Resource Management** - Proper cleanup and monitoring

### Security
- **Input Validation** - Sanitize all user inputs
- **Authentication/Authorization** - Proper security models
- **Secure Defaults** - Principle of least privilege
- **Audit Logging** - Security event tracking

## Development Workflow

### 1. Context Gathering
AI agents research and gather context at each level:
- **Project Level** - Overall architecture and standards
- **Category Level** - Domain-specific patterns and best practices
- **Library Level** - Library-specific capabilities and requirements
- **Component Level** - Component interfaces and implementation details
- **File Level** - File-specific implementation requirements

### 2. Template Processing
Templates are processed with:
- **Variable Substitution** - Replace placeholders with actual values
- **Conditional Processing** - Include/exclude based on library type
- **Validation** - Ensure all required variables are provided
- **Customization** - Library-specific template overrides
- **Registry-Based Rendering** - Keys resolved from `templates.yaml`

### 3. Code Generation
AI agents generate code using:
- **Established Patterns** - Following defined standards
- **Context Integration** - Using gathered research and context
- **Quality Assurance** - Automated checks and validation
- **Documentation** - Comprehensive docs and examples

## Usage Examples

### Basic Library Usage
```python
from opsvi_foundation import BaseComponent
from opsvi_foundation.config.settings import BaseSettings

# Create configuration
config = MyLibrarySettings(
    enabled=True,
    debug=False,
    log_level="INFO"
)

# Create and initialize component
component = MyLibraryComponent(config=config)
await component.initialize()

# Use the component
result = await component.process_data(data)

# Cleanup
await component.shutdown()
```

### Library Integration
```python
from opsvi_llm import LLMProvider
from opsvi_rag import VectorStore
from opsvi_http import HTTPClient

# Integrate multiple libraries
llm = LLMProvider(config=llm_config)
vector_store = VectorStore(config=vector_config)
http_client = HTTPClient(config=http_config)

# Use together in a workflow
embeddings = await llm.embed_text(text)
results = await vector_store.search(embeddings)
response = await http_client.post("/api/process", data=results)
```

### Event-Driven Architecture
```python
from opsvi_core.events.base import Event, EventManager

# Create event manager
event_manager = EventManager(config=config)

# Subscribe to events
async def handle_data_processed(event: Event):
    print(f"Data processed: {event.data}")

await event_manager.subscribe("data.processed", handle_data_processed)

# Publish events
event = Event("data.processed", {"result": "success"})
await event_manager.publish(event)
```

## Contributing

### Development Setup
```bash
# Clone the repository
git clone <repository-url>
cd opsvi-master-workspace

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Code quality checks
ruff check .
black .
mypy .
```

### Adding New Libraries
1. **Define Library** - Add to `recommended_structure.yaml`
2. **Research Context** - Use AI agents to gather domain knowledge
3. **Generate Scaffold** - Use `generate_ecosystem_v2.py`
4. **Implement Components** - Follow established patterns
5. **Add Tests** - Comprehensive test coverage
6. **Document** - Update README and API docs

### AI Agent Development
1. **Context Research** - Use research agents for domain knowledge
2. **Template Processing** - Apply templates with proper variables
3. **Code Generation** - Generate implementation following standards
4. **Quality Validation** - Automated checks and testing
5. **Integration Testing** - Ensure compatibility with existing libraries

## Current Status

### ✅ Completed
- **Structure Definition** - Complete YAML definition with 16 libraries
- **Template System** - Comprehensive templates for all file types
- **Generator Script** - `generate_ecosystem_v2.py` using the YAML template registry
- **YAML Anchor Resolution** - Handles both string and dictionary references
- **Template Standardization** - Consistent naming and reference system
- **Specialized Templates** - Provider, event, and utility templates

### 🔄 In Progress
- **Template Completion** - Adding remaining specialized templates
- **Generator Testing** - Validating all template references
- **Library Generation** - Testing full ecosystem generation

### 📋 Next Steps
- **AI Agent Implementation** - Multi-level research and code generation
- **Library Implementation** - Actual code generation for all 16 libraries
- **Integration Testing** - Cross-library compatibility validation
- **Documentation** - Complete API documentation and examples

## Future Roadmap

### Phase 1: Foundation (Current)
- ✅ Complete structure definition
- ✅ Template system development
- ✅ Scaffolding scripts
- ✅ AI development standards
- ✅ YAML anchor resolution
- ✅ Template system enhancements

### Phase 2: AI Agent Orchestration
- 🔄 Multi-level research agent implementation
- 🔄 Context gathering and synthesis
- 🔄 Automated code generation
- 🔄 Quality assurance automation

### Phase 3: Library Implementation
- 📋 Core libraries (foundation, core)
- 📋 Service libraries (llm, rag, http, etc.)
- 📋 Manager libraries (agents, orchestration, etc.)
- 📋 Integration testing and validation

### Phase 4: Ecosystem Maturity
- 📋 Performance optimization
- 📋 Security hardening
- 📋 Documentation completion
- 📋 Community adoption

## Standards and Compliance

### Code Quality
- **Black** - Code formatting
- **Ruff** - Linting and import sorting
- **MyPy** - Type checking
- **Pytest** - Testing framework
- **Coverage** - Test coverage reporting

### Documentation
- **Google-style Docstrings** - Function and class documentation
- **Comprehensive READMEs** - Usage examples and API docs
- **Type Hints** - Full type annotations
- **Changelog** - Version history and breaking changes

### Security
- **Input Validation** - All user inputs validated
- **Authentication** - Proper auth mechanisms
- **Authorization** - Role-based access control
- **Audit Logging** - Security event tracking
- **Vulnerability Scanning** - Automated security checks

## Support and Community

### Getting Help
- **Documentation** - Comprehensive guides and examples
- **Issues** - GitHub issues for bugs and feature requests
- **Discussions** - Community discussions and Q&A
- **Contributing** - Guidelines for contributors

### Resources
- **Architecture Guide** - Detailed system architecture
- **API Reference** - Complete API documentation
- **Best Practices** - Development guidelines and patterns
- **Examples** - Working code examples and tutorials

---

**OPSVI Library Ecosystem** - Building the future of AI/ML operations with intelligent, scalable, and maintainable libraries.
