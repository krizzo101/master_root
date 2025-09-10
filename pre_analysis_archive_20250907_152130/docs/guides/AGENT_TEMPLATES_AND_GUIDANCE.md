# Agent Templates and Guidance System

## Overview

This guide provides templates, patterns, and best practices for agents working with the UnifiedOrchestrator system. Use these templates to avoid common mistakes and ensure consistent, successful task execution.

## 🎯 Core Principles for Agents

### 1. **Read First, Code Second**
- **ALWAYS** use Read tool to examine existing code before making changes
- Understand the current system structure and patterns
- Check imports, dependencies, and existing patterns

### 2. **Follow Existing Patterns**
- Match the coding style and patterns already in use
- Use the same import patterns, class structures, and naming conventions
- Don't reinvent - reuse existing working code

### 3. **Test Your Assumptions**
- Use Bash tool to test commands before assuming they work
- Verify file paths exist before referencing them
- Check that classes/methods exist before using them

### 4. **Document What You Do**
- Create clear deliverable files as requested
- Document changes made and reasoning
- Leave the system better than you found it

## 📋 AGENT TASK TEMPLATES

### Template 1: Code Analysis Task

```python
EnhancedAgentTask(
    task_id="analyze_component_name",
    task_type="code-analyzer",  # or solution-architect
    prompt='''ANALYZE COMPONENT: {component_name}

1. READ AND UNDERSTAND:
   - Use Read tool to examine: {file_path}
   - Understand: {specific_aspects_to_analyze}
   - Check dependencies and imports

2. MANDATORY DELIVERABLE:
   CREATE FILE: {output_file_path}
   CONTENT MUST INCLUDE:
   - {specific_requirements}
   - Analysis findings with line numbers
   - Recommendations for improvements
   - Any issues or concerns found

3. EXECUTION STEPS:
   - USE Read tool to examine all relevant files
   - USE Write tool to create analysis document
   - VERIFY deliverable file exists

CURRENT SYSTEM CONTEXT:
- UnifiedOrchestrator is located at: src/unified/unified_orchestrator.py
- Use FeatureFlag enum for feature configuration
- Follow existing import patterns from working code''',
    agent_uuid="agent_analyze_{component}",
    monitoring_enabled=True
)
```

### Template 2: Implementation Task

```python
EnhancedAgentTask(
    task_id="implement_feature_name",
    task_type="development-specialist",
    prompt='''IMPLEMENT FEATURE: {feature_name}

1. UNDERSTAND CURRENT SYSTEM:
   - Read src/unified/unified_orchestrator.py to understand structure
   - Read existing modules in src/unified/modules/ for patterns
   - Check src/unified/enhanced_agent_task.py for task structure

2. IMPLEMENTATION REQUIREMENTS:
   - Create: {file_path}
   - Follow existing patterns from working modules
   - Use same import structure and error handling
   - Include proper logging and error handling

3. WORKING PATTERNS TO FOLLOW:
   ```python
   # Import pattern:
   from pathlib import Path
   from typing import Dict, List, Optional
   import logging

   # Class pattern:
   class YourClass:
       def __init__(self, config: SomeConfig):
           self.logger = logging.getLogger(__name__)

       async def some_method(self):
           try:
               # implementation
               return result
           except Exception as e:
               self.logger.error(f"Error in {self.__class__.__name__}: {e}")
               raise
   ```

4. VERIFICATION:
   - Test import works: python -c "from {module} import {class}; print('OK')"
   - USE Write tool to create implementation
   - VERIFY file exists and imports work

CRITICAL: Follow existing code patterns exactly. Don't guess - read the working code first.''',
    agent_uuid="agent_implement_{feature}",
    monitoring_enabled=True
)
```

### Template 3: Test Creation Task

```python
EnhancedAgentTask(
    task_id="test_component_name",
    task_type="qa-testing-guru",
    prompt='''CREATE TESTS FOR: {component_name}

1. UNDERSTAND WHAT TO TEST:
   - Read the component: {component_file_path}
   - Read existing tests in tests/ directory for patterns
   - Check test_unified_orchestrator.py for working example

2. WORKING TEST PATTERNS:
   ```python
   import asyncio
   from pathlib import Path
   import sys

   # Add src to path
   sys.path.insert(0, str(Path(__file__).parent / "src"))

   # Test function pattern
   async def test_basic_functionality():
       try:
           from src.unified.unified_orchestrator import UnifiedOrchestrator, UnifiedConfig, FeatureFlag

           # Create config (USE WORKING PATTERN)
           config = UnifiedConfig(
               output_dir=Path("test_output"),
               max_parallel=2,
               enabled_features={FeatureFlag.ENHANCED_METRICS},
               enable_collaboration=False,
               enable_quality_gates=False,
               enable_monitoring=False
           )

           orchestrator = UnifiedOrchestrator(config=config)

           # Test the component
           result = await orchestrator.some_method()

           if result:
               print("✅ Test passed")
               return True
           else:
               print("❌ Test failed")
               return False

       except Exception as e:
           print(f"❌ Test error: {e}")
           return False
   ```

3. CREATE TEST FILE:
   CREATE FILE: tests/test_{component_name}.py
   CONTENT: Working test based on patterns above

USE existing working test patterns - don't reinvent the wheel.''',
    agent_uuid="agent_test_{component}",
    monitoring_enabled=True
)
```

## 🔧 COMMON PATTERNS AND EXAMPLES

### 1. UnifiedOrchestrator Configuration Patterns

**✅ CORRECT - Working Pattern:**
```python
from src.unified.unified_orchestrator import UnifiedOrchestrator, UnifiedConfig, FeatureFlag

config = UnifiedConfig(
    output_dir=Path("output"),
    max_parallel=5,
    enabled_features={FeatureFlag.ENHANCED_METRICS, FeatureFlag.BACKGROUND_EXECUTION},
    enable_collaboration=False,
    enable_quality_gates=False,
    enable_monitoring=True
)

orchestrator = UnifiedOrchestrator(config=config)
```

**❌ WRONG - Don't Do This:**
```python
# Wrong - these parameters don't exist
config = UnifiedConfig(
    enable_enhanced_features=True,  # NO - use enabled_features set
    enable_monitoring=True
)

orchestrator = UnifiedOrchestrator(
    output_dir=Path("output"),     # NO - pass config object
    max_parallel=5,
    config=config
)
```

### 2. Task Creation Patterns

**✅ CORRECT:**
```python
from src.unified.enhanced_agent_task import EnhancedAgentTask

task = EnhancedAgentTask(
    task_id="my_task",
    task_type="development-specialist",
    prompt="Clear task description...",
    agent_uuid="agent_001",           # Optional but recommended
    monitoring_enabled=True           # Optional
)
```

**❌ WRONG:**
```python
task = EnhancedAgentTask(
    task_id="my_task",
    task_type="development-specialist",
    prompt="Task description...",
    collaboration_mode="shared"       # NO - parameter doesn't exist
)
```

### 3. Import Patterns

**✅ CORRECT - Follow This Pattern:**
```python
import asyncio
from pathlib import Path
import sys
from typing import Dict, List, Optional

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.unified.unified_orchestrator import UnifiedOrchestrator, UnifiedConfig, FeatureFlag
    from src.unified.enhanced_agent_task import EnhancedAgentTask
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)
```

## 🚨 COMMON MISTAKES TO AVOID

### 1. **Configuration Mistakes**
- ❌ Using non-existent parameters like `enable_enhanced_features`
- ✅ Use `enabled_features` with FeatureFlag enum values
- ❌ Passing both config object and separate parameters
- ✅ Pass only the config object to UnifiedOrchestrator

### 2. **Import Mistakes**
- ❌ Assuming imports work without testing
- ✅ Test imports with try/except blocks
- ❌ Wrong module paths
- ✅ Follow the working patterns exactly

### 3. **Task Parameter Mistakes**
- ❌ Using non-existent task parameters
- ✅ Check EnhancedAgentTask definition for valid parameters
- ❌ Assuming features exist without verification
- ✅ Read the actual code to see what's available

### 4. **File Path Mistakes**
- ❌ Assuming files exist without checking
- ✅ Use Bash tool to verify file/directory existence
- ❌ Using wrong relative paths
- ✅ Use absolute paths or verify current directory

## 📚 REFERENCE LIBRARY

### Working Code References:
- **UnifiedOrchestrator**: `src/unified/unified_orchestrator.py`
- **Working Test**: `test_unified_orchestrator.py`
- **Task Class**: `src/unified/enhanced_agent_task.py`
- **Feature Flags**: Check UnifiedConfig and FeatureFlag enum
- **Module Patterns**: `src/unified/modules/enhanced_module.py`

### File Structure Reference:
```
src/
├── unified/                    # Main unified orchestrator
│   ├── unified_orchestrator.py # Main orchestrator class
│   ├── enhanced_agent_task.py  # Task class definition
│   ├── orchestrator_module.py  # Base module class
│   └── modules/                # Feature modules
docs/
├── guides/                     # This file and other guides
├── analysis/                   # System analysis reports
└── architecture/               # Architecture documentation
tests/
├── test_unified_orchestrator.py # Working test example
└── outputs/                    # Test output files
```

## 🎯 AGENT SUCCESS CHECKLIST

Before submitting any task result, verify:

- [ ] **Read existing code** to understand current patterns
- [ ] **Follow exact import patterns** from working examples
- [ ] **Use correct class/method parameters** (check definitions)
- [ ] **Test your assumptions** with Bash/Read tools
- [ ] **Create requested deliverable files**
- [ ] **Document what you did and why**
- [ ] **Verify everything works** with test imports if applicable

## 💡 WHEN IN DOUBT

1. **Read the working test file**: `test_unified_orchestrator.py`
2. **Check the actual source code**: Don't assume - verify
3. **Follow existing patterns exactly**: Don't innovate unless necessary
4. **Test your changes**: Use Bash tool to verify
5. **Ask for clarification**: Better to ask than fail repeatedly

---

**Remember: The UnifiedOrchestrator is working and tested. Your job is to work WITH the existing system, not reinvent it.**
