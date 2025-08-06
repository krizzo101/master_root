# OPSVI Library Ecosystem - Quick Start Guide

## ✅ **ARCHITECTURE FIXED!**

We've implemented a proper **DRY-based shared foundation architecture** that eliminates code duplication and ensures consistency.

## 🏗️ **New Architecture Overview**

```
libs/
├── opsvi-foundation/          # 🔧 SHARED: Security, resilience, observability
├── opsvi-llm/                 # 🤖 DOMAIN: LLM-specific logic only
├── opsvi-rag/                 # 🔍 DOMAIN: RAG-specific logic only
├── opsvi-agents/              # 👥 DOMAIN: Agent-specific logic only
├── opsvi-core/                # 🏗️ APPLICATION: High-level patterns
├── templates/                 # 📋 Library generation system
├── OPSVI_LIBRARY_ARCHITECTURE.md  # 📚 Complete architectural guide
└── QUICK_START.md             # ⚡ This file
```

## 🚀 **Creating New Libraries**

### Use the Template System
```bash
cd libs/templates

# Create a new domain library
./create_opsvi_library.py opsvi-workflow "Workflow orchestration library" "workflow" --deps "temporal-sdk"

# Creates:
# opsvi-workflow/
# ├── opsvi_workflow/
# │   ├── __init__.py           # Proper foundation imports
# │   ├── core/                 # Config + exceptions only
# │   └── {domain modules}/     # Your specific logic
# ├── tests/                    # Test templates
# ├── README.md                 # Documentation template
# └── pyproject.toml           # Proper dependencies
```

### What You Get
- ✅ **Foundation Integration**: Automatic `opsvi-foundation` dependency
- ✅ **Security**: Use `AuthManager`, encryption, validation from foundation
- ✅ **Resilience**: Use `CircuitBreaker`, retry logic from foundation
- ✅ **Observability**: Use metrics, tracing, logging from foundation
- ✅ **Configuration**: Inherits foundation config patterns
- ✅ **Testing**: Pre-configured test setup
- ✅ **Quality**: Ruff, Black, MyPy configured

## 📋 **Development Rules**

### ✅ **DO**
- Use `opsvi-foundation` for all cross-cutting concerns
- Create new libraries for distinct business domains
- Follow async-first patterns
- Use the template system for consistency
- Write comprehensive tests and documentation

### ❌ **DON'T**
- Duplicate security, resilience, observability code
- Create libraries for small utilities (add to foundation)
- Skip foundation components for "performance"
- Create circular dependencies between domain libraries

## 🔧 **Foundation Components Available**

```python
from opsvi_foundation import (
    # Security
    AuthManager,           # JWT, API keys, encryption
    sanitize_input,        # Input validation

    # Resilience
    CircuitBreaker,        # Fault tolerance
    RetryExecutor,         # Exponential backoff

    # Observability
    MetricsCollector,      # Prometheus metrics
    TracingManager,        # OpenTelemetry tracing
    get_logger,            # Structured logging

    # Patterns
    BaseComponent,         # Lifecycle management
    LifecycleComponent,    # Start/stop patterns

    # Configuration
    FoundationConfig,      # Environment-based config
)
```

## 🎯 **Example: Domain Library Using Foundation**

```python
# opsvi-workflow/opsvi_workflow/orchestrator.py
from opsvi_foundation import (
    BaseComponent,
    CircuitBreaker,
    AuthManager,
    get_logger
)
from .core import WorkflowConfig, WorkflowError

class WorkflowOrchestrator(BaseComponent):
    """Domain-specific orchestrator using foundation components."""

    def __init__(self, config: WorkflowConfig):
        super().__init__()
        self.config = config
        self.logger = get_logger(__name__)

        # Use foundation components - no duplication!
        self.auth = AuthManager(config.foundation.auth_config)
        self.circuit_breaker = CircuitBreaker(config.foundation.circuit_config)

    async def execute_workflow(self, token: str, workflow_def: dict) -> dict:
        """Execute workflow with security and resilience."""
        # Use foundation security
        user = self.auth.validate_jwt(token)
        self.auth.require_permission(user.roles, "workflow:execute")

        # Use foundation resilience
        return await self.circuit_breaker.call(
            self._internal_execute, workflow_def
        )

    async def _internal_execute(self, workflow_def: dict) -> dict:
        """Internal execution logic - domain-specific only."""
        # Your workflow logic here - no security/resilience boilerplate!
        pass
```

## 🔄 **Migration Strategy**

### For Existing Libraries
1. **Add Foundation Dependency**: `pip install opsvi-foundation`
2. **Replace Duplicated Code**: Use foundation components
3. **Update Imports**: Import from foundation
4. **Remove Duplication**: Delete old security/resilience code
5. **Test Integration**: Ensure everything works

### Example Migration
```python
# Before (duplicated)
class MyLibraryAuth:
    def validate_token(self): ...

class MyLibraryRetry:
    def retry_with_backoff(self): ...

# After (using foundation)
from opsvi_foundation import AuthManager, RetryExecutor

class MyLibraryComponent:
    def __init__(self):
        self.auth = AuthManager(config.auth_config)      # Foundation
        self.retry = RetryExecutor(config.retry_config)  # Foundation
        # Focus on your domain logic only!
```

## 📚 **Next Steps**

1. **Read**: `OPSVI_LIBRARY_ARCHITECTURE.md` for complete details
2. **Create**: New libraries using the template system
3. **Migrate**: Existing libraries to use foundation
4. **Contribute**: Improvements to foundation and templates

## 🎉 **Benefits Achieved**

- ✅ **DRY Compliance**: No more code duplication
- ✅ **Consistency**: All libraries use same security/resilience patterns
- ✅ **Maintainability**: Fix once in foundation, benefits all libraries
- ✅ **Scalability**: Easy to add new libraries following patterns
- ✅ **Quality**: Shared testing and quality standards
- ✅ **Developer Experience**: Template system for rapid development

**The OPSVI ecosystem now follows proper software engineering principles!** 🚀
