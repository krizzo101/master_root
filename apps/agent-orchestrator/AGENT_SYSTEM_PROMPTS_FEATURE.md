# Agent System Prompts Enhancement Feature

## Overview
The orchestrator now provides **specialized system prompts** to every agent using the `--append-system-prompt` flag, giving agents role-specific instructions that maximize their effectiveness.

## What Was Implemented

### 1. Enhanced AgentTask Class
Added three new fields to `AgentTask`:
- `system_prompt`: Custom system prompt text
- `system_prompt_file`: File to load system prompt from
- `enhancement_level`: DPO enhancement level (0-5)

### 2. Comprehensive Agent Templates
Created 13+ specialized agent types with tailored instructions:
- **Requirements & Analysis**: requirements-analyst, business-analyst
- **Architecture & Design**: solution-architect, database-specialist
- **Development**: development-specialist, api-integration-specialist
- **Quality & Testing**: qa-testing-guru, security-architect
- **DevOps**: devops-automation, performance-optimizer
- **Documentation**: technical-writer
- **Research**: research-specialist
- **Monitoring**: monitoring-specialist

### 3. DPO Integration
System prompts automatically adjust based on DPO enhancement level:
- **Level 0-1**: Minimal - Basic instructions with conciseness focus
- **Level 2**: Essential - Standard professional instructions
- **Level 3**: Balanced - Enhanced with traits and tool focus
- **Level 4**: Comprehensive - Adds production quality focus
- **Level 5**: Maximum - Includes innovation and cutting-edge practices

### 4. Automatic Agent Selection
The system can automatically select the best agent type based on task description keywords.

## How It Works

### Basic Usage
```python
from src.generic_orchestrator import AgentTask

# Task automatically gets specialized prompt based on type
task = AgentTask(
    task_id="001",
    task_type="security-architect",  # Gets security-focused instructions
    prompt="Review the authentication system",
    dependencies=[]
)
```

### With Custom System Prompt
```python
task = AgentTask(
    task_id="002",
    task_type="development-specialist",
    prompt="Implement the feature",
    system_prompt="Focus on functional programming patterns",  # Additional instructions
    enhancement_level=3  # Control detail level
)
```

### With DPO Enhancement
```python
from src.dpo.enhancement_config import DPOEnhancementConfig
from src.dpo.dpo_agent_prompts_integration import DPOAgentPromptsIntegration

# Set DPO level
config = DPOEnhancementConfig()
config.dial(4)  # Comprehensive level

# Tasks automatically get enhanced prompts
integration = DPOAgentPromptsIntegration(config)
enhanced_tasks = integration.enhance_tasks_with_prompts(tasks)
```

## Example System Prompts

### Security Architect (Level 3)
```
You are a security architecture expert. Implement security best practices,
identify vulnerabilities, and design secure systems. Follow OWASP guidelines
and implement defense in depth. Apply zero-trust architecture, implement
comprehensive threat modeling (STRIDE, PASTA), design for compliance
(GDPR, HIPAA, SOC2). Include security automation and DevSecOps practices.
```

### Development Specialist (Level 5)
```
You are a senior software engineer. Write clean, efficient, well-tested code
following best practices. Include comprehensive error handling, logging, and
documentation. Focus on maintainability and performance. Apply advanced design
patterns, implement comprehensive testing (unit, integration, e2e), use
dependency injection, follow 12-factor app principles. Consider observability
and monitoring from the start. Be extremely thorough and consider all edge
cases. Provide detailed explanations and comprehensive solutions. Apply
cutting-edge best practices and innovative approaches. Consider future
scalability and emerging technologies. Provide multiple solution options
with trade-off analysis.
```

## Benefits

1. **Specialized Instructions**: Each agent type receives role-specific guidance
2. **Automatic Enhancement**: DPO dial controls instruction detail (0-5)
3. **Flexibility**: Support for custom prompts and file-based prompts
4. **Better Results**: Agents perform better with clear, specialized instructions
5. **Consistency**: All agents of same type get consistent instructions

## Files Created/Modified

### New Files
- `/src/agent_system_prompts.py` - Core system prompt manager
- `/src/dpo/dpo_agent_prompts_integration.py` - DPO integration
- `/test_agent_prompts.py` - Test suite

### Modified Files
- `/src/generic_orchestrator.py` - Added system_prompt fields to AgentTask
- `/src/generic_orchestrator.py` - Updated execute_agent() to use prompt manager

## Testing
Run the test suite to see the feature in action:
```bash
cd /home/opsvi/master_root/apps/agent-orchestrator
python test_agent_prompts.py
```

## Key Insight
This implementation ensures every agent receives the `--append-system-prompt` flag with specialized instructions, giving them every advantage to perform their tasks effectively. The integration with DPO means the level of detail automatically adjusts based on project complexity needs.
