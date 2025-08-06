# OPSVI Library Architecture Guide

## Overview

The OPSVI ecosystem follows a **shared foundation architecture** that eliminates code duplication and ensures consistency across all libraries.

## Architecture Principles

### 1. **DRY (Don't Repeat Yourself)**
- Shared functionality lives in `opsvi-foundation`
- Domain libraries contain only domain-specific logic
- No duplication of security, resilience, or observability code

### 2. **Dependency Hierarchy**
```
opsvi-foundation (shared core)
    ↑
opsvi-llm, opsvi-rag, opsvi-agents (domain libraries)
    ↑
apps/applications (consume libraries)
```

### 3. **Single Responsibility**
- Each library has one clear domain focus
- Foundation provides cross-cutting concerns
- Clean separation between shared and domain logic

## Library Types

### **Foundation Library (`opsvi-foundation`)**
**Purpose**: Shared components used by all other libraries

**Contains**:
- **Security**: Authentication, authorization, encryption, input validation
- **Resilience**: Circuit breakers, retry mechanisms, timeouts, fallbacks
- **Observability**: Metrics collection, distributed tracing, structured logging
- **Configuration**: Environment-based config management with validation
- **Patterns**: Base classes, interfaces, lifecycle management
- **Testing**: Shared testing utilities, fixtures, mocks

**Dependencies**: Only external packages (no other OPSVI libraries)

### **Domain Libraries**
**Purpose**: Specific functionality for a business domain

**Examples**:
- `opsvi-llm`: Language model providers, prompt engineering, function calling
- `opsvi-rag`: Vector storage, document processing, retrieval pipelines
- `opsvi-agents`: Agent orchestration, workflow management, communication

**Contains**:
- Domain-specific business logic only
- Specialized data models and schemas
- Domain-specific integrations and providers
- Custom algorithms and processing logic

**Dependencies**: `opsvi-foundation` + domain-specific external packages

### **Application Libraries**
**Purpose**: High-level application patterns and orchestration

**Example**: `opsvi-core` (could be renamed to `opsvi-platform`)

**Contains**:
- Application-level patterns and workflows
- Cross-domain orchestration logic
- High-level APIs and facades
- Application-specific configuration

**Dependencies**: Foundation + multiple domain libraries

## Creating New Libraries

### When to Create a New Library

✅ **CREATE** when:
- New distinct business domain (e.g., "opsvi-workflow", "opsvi-deployment")
- Standalone functionality that others could reuse
- Significant enough scope to warrant separate versioning
- Different release/update cycles needed

❌ **DON'T CREATE** when:
- Adding features to existing domain (extend existing library)
- Small utility functions (add to `opsvi-foundation`)
- Application-specific logic (add to application code)
- Experimental/prototype code (use playground/labs)

### Library Creation Process

1. **Use the Template System**:
   ```bash
   cd libs/templates
   python create_opsvi_library.py opsvi-newdomain "Description" "domain" --deps "extra-dep1" "extra-dep2"
   ```

2. **Follow Naming Conventions**:
   - Library name: `opsvi-{domain}` (kebab-case)
   - Package name: `opsvi_{domain}` (snake_case)
   - Class prefix: `{Domain}` (PascalCase)

3. **Required Components**:
   - Configuration class inheriting foundation config
   - Domain-specific exception hierarchy
   - Comprehensive test suite
   - Documentation with examples
   - Type hints throughout

4. **Integration Requirements**:
   - Must depend on `opsvi-foundation>=1.0.0`
   - Use foundation components for security, resilience, observability
   - Follow async-first patterns
   - Implement proper error handling

## Dependency Management Rules

### **FOUNDATION LIBRARY**
```toml
# opsvi-foundation/pyproject.toml
dependencies = [
    "pydantic>=2.0.0",
    "structlog>=24.1.0",
    "cryptography>=41.0.0",
    "opentelemetry-api>=1.25.0",
    # ... other external dependencies only
]
```

### **DOMAIN LIBRARIES**
```toml
# opsvi-{domain}/pyproject.toml
dependencies = [
    "opsvi-foundation>=1.0.0",  # Required!
    "pydantic>=2.0.0",          # Shared with foundation
    # ... domain-specific dependencies only
]
```

### **APPLICATION LIBRARIES**
```toml
# opsvi-core/pyproject.toml
dependencies = [
    "opsvi-foundation>=1.0.0",
    "opsvi-llm>=1.0.0",
    "opsvi-rag>=1.0.0",
    "opsvi-agents>=1.0.0",
    # ... application-level dependencies
]
```

## Code Organization Standards

### **Directory Structure**
```
opsvi-{domain}/
├── opsvi_{domain}/
│   ├── __init__.py           # Main exports
│   ├── core/                 # Configuration, exceptions
│   │   ├── config.py
│   │   └── exceptions.py
│   ├── {feature_area}/       # Domain-specific modules
│   └── utils/                # Domain-specific utilities
├── tests/                    # Comprehensive test suite
├── docs/                     # Documentation
├── README.md                 # Usage documentation
└── pyproject.toml           # Dependencies and config
```

### **Import Patterns**
```python
# Always import from foundation first
from opsvi_foundation import (
    BaseComponent,
    CircuitBreaker,
    AuthManager,
    get_logger,
)

# Then domain-specific imports
from .core import DomainConfig, DomainError
from .providers import DomainProvider
```

### **Configuration Patterns**
```python
from opsvi_foundation import FoundationConfig
from pydantic import BaseModel, Field

class DomainConfig(BaseModel):
    """Domain-specific configuration."""

    # Inherit all foundation settings
    foundation: FoundationConfig = Field(default_factory=FoundationConfig.from_env)

    # Add domain-specific settings
    domain_api_key: str = Field(..., description="Domain API key")
    domain_timeout: int = Field(default=30, description="Domain operation timeout")
```

### **Exception Patterns**
```python
from opsvi_foundation.patterns import ComponentError

class DomainError(ComponentError):
    """Base exception for domain library."""
    pass

class DomainValidationError(DomainError):
    """Domain-specific validation error."""
    pass
```

### **Component Patterns**
```python
from opsvi_foundation import BaseComponent, CircuitBreaker, get_logger

class DomainComponent(BaseComponent):
    """Domain-specific component following foundation patterns."""

    def __init__(self, config: DomainConfig):
        super().__init__()
        self.config = config
        self.logger = get_logger(__name__)
        self.circuit_breaker = CircuitBreaker(config.circuit_config)

    async def domain_operation(self, data: str) -> str:
        """Perform domain operation with resilience."""
        return await self.circuit_breaker.call(self._internal_operation, data)
```

## Quality Standards

### **Required**
- **Type Coverage**: 100% type annotations
- **Test Coverage**: Minimum 90% code coverage
- **Documentation**: Comprehensive docstrings and README
- **Linting**: Ruff, Black, MyPy compliance
- **Security**: Use foundation security components

### **Testing Requirements**
- Unit tests for all public APIs
- Integration tests with foundation components
- Mock external dependencies
- Async test patterns with pytest-asyncio
- Performance benchmarks for critical paths

### **Documentation Requirements**
- Clear README with installation and usage
- API documentation with examples
- Architecture decision records (ADRs) for significant changes
- Migration guides for breaking changes

## Migration Guide

### **Existing Libraries**
If you have existing libraries with duplicated code:

1. **Identify Shared Code**: Security, resilience, observability, config
2. **Move to Foundation**: Extract shared code to `opsvi-foundation`
3. **Update Dependencies**: Add `opsvi-foundation` dependency
4. **Refactor Imports**: Use foundation components
5. **Remove Duplication**: Delete duplicated implementations
6. **Update Tests**: Test integration with foundation
7. **Update Documentation**: Reflect new architecture

### **Example Migration**
```python
# Before (duplicated)
class OldLibraryAuth:
    def validate_token(self, token: str): ...

# After (using foundation)
from opsvi_foundation import AuthManager

class NewLibraryComponent:
    def __init__(self):
        self.auth = AuthManager(config.auth_config)

    def protected_operation(self, token: str):
        user = self.auth.validate_jwt(token)  # Use foundation
        # ... domain logic only
```

## Versioning Strategy

### **Foundation Library**
- **Semantic Versioning**: MAJOR.MINOR.PATCH
- **Breaking Changes**: Increment MAJOR version
- **New Features**: Increment MINOR version
- **Bug Fixes**: Increment PATCH version

### **Domain Libraries**
- **Independent Versioning**: Each library versions independently
- **Foundation Compatibility**: Specify minimum foundation version
- **Coordinated Releases**: Major ecosystem releases coordinate versions

### **Compatibility Matrix**
```
Foundation 1.x.x → Domain Libraries 1.x.x - 2.x.x
Foundation 2.x.x → Domain Libraries 2.x.x - 3.x.x
```

## Best Practices

### **DO**
✅ Use foundation components for all cross-cutting concerns
✅ Follow async-first patterns throughout
✅ Implement comprehensive error handling
✅ Write thorough tests and documentation
✅ Use type hints and validation everywhere
✅ Follow consistent naming conventions
✅ Leverage the template system for new libraries

### **DON'T**
❌ Duplicate security, resilience, or observability code
❌ Create libraries for small utility functions
❌ Skip testing or documentation
❌ Use blocking/synchronous patterns
❌ Ignore foundation configuration patterns
❌ Create circular dependencies between domain libraries
❌ Bypass foundation components for "performance"

## Future Considerations

### **Planned Enhancements**
- Automated dependency compatibility checking
- Shared CI/CD pipelines and quality gates
- Cross-library integration testing
- Performance monitoring and optimization
- Security scanning and vulnerability management

### **Evolutionary Path**
- Foundation library grows with new shared needs
- Domain libraries remain focused and lightweight
- Application libraries provide higher-level orchestration
- Template system evolves with best practices
- Documentation and tooling improve continuously

---

**Remember**: The goal is a maintainable, scalable ecosystem where each library has a clear purpose and shared concerns are handled consistently across all components.
