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

### Template System
- **`templates.yaml`** - Comprehensive template system
  - Project, category, library, component, and file-level templates
  - Python, configuration, and documentation templates
  - Variable substitution and conditional processing
  - Template processing rules and validation

### Scaffolding Scripts
- **`scaffold_shared_libs.py`** - Individual library scaffolding with DRY analysis
- **`scaffold_all_shared_libs.py`** - Batch library generation with manifest support

## Design Principles

### DRY (Don't Repeat Yourself)
- **Centralized Base Classes** - Common functionality in `opsvi-foundation`
- **Template System** - Reusable patterns for all file types
- **Shared Components** - Symlinks to common files like logging
- **Factory Functions** - Dynamic class generation for specific libraries

### Naming Conventions
- **Directories**: kebab-case (e.g., `opsvi-foundation`)
- **Packages**: snake_case (e.g., `opsvi_foundation`)
- **Classes**: PascalCase (e.g., `OpsviFoundation`)
- **Functions**: snake_case (e.g., `initialize_component`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_TIMEOUT`)

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
│   │   └── base.py          # Base classes
│   ├── config/
│   │   ├── __init__.py      # Config exports
│   │   └── settings.py      # Configuration management
│   ├── exceptions/
│   │   ├── __init__.py      # Exception exports
│   │   └── base.py          # Exception hierarchy
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
3. **Generate Scaffold** - Use scaffolding scripts
4. **Implement Components** - Follow established patterns
5. **Add Tests** - Comprehensive test coverage
6. **Document** - Update README and API docs

### AI Agent Development
1. **Context Research** - Use research agents for domain knowledge
2. **Template Processing** - Apply templates with proper variables
3. **Code Generation** - Generate implementation following standards
4. **Quality Validation** - Automated checks and testing
5. **Integration Testing** - Ensure compatibility with existing libraries

## Future Roadmap

### Phase 1: Foundation (Current)
- ✅ Complete structure definition
- ✅ Template system development
- ✅ Scaffolding scripts
- ✅ AI development standards

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
