# AI Agent's Guide to Agent Orchestrator

**Quick reference for AI agents working with the Agent Orchestrator system.**

---

## 🎯 What This System Does

Agent Orchestrator coordinates multiple AI agents to work together on complex tasks. Think of it as a smart project manager that distributes work, manages dependencies, handles failures, and tracks progress across up to 15 parallel agents.

**NEW: DPO (Development Process Orchestrator) is now integrated** - Automatically enhances vague requests into sophisticated workflows with smart defaults (Level 2 enhancement by default).

## 🎛️ DPO Enhancement System (NEW!)

**DPO is ON by default at Level 2** - No setup needed! It automatically enhances your requests.

### DPO Dial Levels (0-5)
- **0 = OFF**: No enhancement, basic orchestrator only
- **1 = MINIMAL**: 3 agents, 2 tasks per phase
- **2 = ESSENTIAL**: 6 agents, 4 tasks per phase **(DEFAULT)**
- **3 = BALANCED**: 8 agents, includes documentation
- **4 = COMPREHENSIVE**: 12 agents, security & deployment
- **5 = MAXIMUM**: 15 agents, everything possible

### Adjusting DPO Level
```python
from src.dpo.enhancement_config import DPOEnhancementConfig

config = DPOEnhancementConfig()
config.dial(3)  # Set to Level 3 (Balanced)
# Use config when creating orchestrator
```

### What DPO Does For You
- **Analyzes vague requests** → Infers requirements
- **Selects specialist agents** automatically
- **Adds quality gates** and dependencies
- **Generates executable workflows** ready to run

## 🚀 Quick Start Commands

```bash
# Navigate to orchestrator directory
cd /home/opsvi/master_root/apps/agent-orchestrator

# Run with UnifiedOrchestrator (ALL features enabled)
python main.py --tasks-file workflow.json --use-unified --max-parallel 10

# Generate complete documentation for any project
python scripts/run_orchestrator_task.py \
  --task-type system-documentation \
  --app-name "project-name" \
  --app-root "/path/to/project"

# Run system analysis (comprehensive)
python scripts/run_system_analysis.py

# Custom workflow from JSON
python scripts/run_orchestrator_task.py --workflow-file my_tasks.json

# Resume interrupted work
python scripts/run_orchestrator_task.py --resume-checkpoint checkpoint_12345

# Start monitoring dashboard
python production_dashboard.py
```

## 📨 How to Submit Requests to Orchestrator

### Method 1: CLI Script (Recommended)
```bash
# System documentation
python scripts/run_orchestrator_task.py \
  --task-type system-documentation \
  --app-name "my-app" \
  --app-root "/path/to/app"

# Custom workflow
python scripts/run_orchestrator_task.py --workflow-file workflow.json
```

### Method 2: Python API with DPO
```python
from src.dpo.dpo_orchestrator_integration import DPOOrchestrator
from src.dpo.enhancement_config import DPOEnhancementConfig

# Configure enhancement level
config = DPOEnhancementConfig()
config.dial(3)  # Balanced level

# Submit request - DPO enhances it automatically
dpo = DPOOrchestrator()
request = "Build a task management system"
# DPO analyzes and generates executable workflow
```

### Method 3: Direct AgentTask Creation
```python
from src.generic_orchestrator import GenericOrchestrator, AgentTask

tasks = [
    AgentTask(
        task_id="001_analyze",
        task_type="requirements-analyst",
        prompt="Analyze requirements",
        dependencies=[]
    )
]
orchestrator = GenericOrchestrator()
await orchestrator.execute(tasks)
```

### Method 4: JSON Workflow File
```json
{
  "workflow_name": "my_project",
  "tasks": [
    {
      "task_id": "001",
      "task_type": "development-specialist",
      "prompt": "Build feature X",
      "dependencies": []
    }
  ]
}
```

## 📋 Key Scripts & Their Uses

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `scripts/run_orchestrator_task.py` | Main CLI interface | All workflows |
| `scripts/run_system_analysis.py` | System self-analysis | Understand capabilities |
| `main.py` | Core orchestrator | Direct Python usage |
| `resume_orchestrator.py` | Checkpoint management | Resume interrupted work |
| `production_dashboard.py` | Monitoring dashboard | Real-time tracking |

## 🏗️ Task Definition Format

```json
{
  "tasks": [
    {
      "task_id": "analyze_code",
      "task_type": "analysis",
      "prompt": "Analyze the codebase for security issues",
      "context": {"target_dir": "/path/to/code"},
      "dependencies": ["setup_task"],
      "quality_gates": ["security_check"]
    }
  ]
}
```

## 🔧 Common Parameters

```bash
--max-parallel 10        # Max simultaneous agents (1-15)
--output-dir ./results   # Where to save outputs
--use-unified           # Enable UnifiedOrchestrator (ALL features)
--use-enhanced          # Enable EnhancedOrchestrator (quality gates)
--enable-dashboard      # Real-time monitoring
--resume-checkpoint id  # Resume from checkpoint
--template comprehensive # Documentation template
--dpo-level 2           # DPO enhancement level (0-5, default 2)
```

## 📊 Built-in Workflows

### System Documentation (`system-documentation`)
**Generates:** README, ARCHITECTURE, API_REFERENCE, USER_GUIDE, DEVELOPER_GUIDE, DEPLOYMENT
```bash
python run_orchestrator_task.py \
  --task-type system-documentation \
  --app-name "my-app" \
  --app-root "/path/to/app"
```

### System Analysis
**Analyzes:** Architecture, performance, integration points, documentation gaps
```bash
python run_system_analysis.py
```

### Parallel Documentation Update
**Updates:** Multiple docs simultaneously with dependency management
```bash
python run_parallel_doc_update.py
```

## 💡 Key Concepts

**DPO Enhancement:** Automatically enhances requests at Level 2 by default (use `config.dial(n)` to adjust 0-5)

**Dependencies:** Tasks can depend on others (e.g., "write docs" depends on "analyze code")

**Quality Gates:** Built-in validation (security_check, performance_review, completeness_check)

**Checkpoints:** Automatic save points - never lose progress on long workflows

**Token Pool:** Manages Claude API tokens across parallel agents automatically

**Dashboard:** Real-time monitoring at `http://localhost:8765` when enabled

**Specialist Agents:** 28+ specialized agents available (requirements-analyst, solution-architect, development-specialist, security-architect, qa-testing-guru, technical-writer, devops-automation, etc.)

**System Prompts (NEW!):** Every agent automatically receives specialized instructions via `--append-system-prompt` based on their role and DPO enhancement level for maximum effectiveness

## 🔍 Monitoring & Debugging

```bash
# Check logs
tail -f outputs/logs/orchestrator_*.log

# List checkpoints
python resume_orchestrator.py --list-checkpoints

# Monitor system
python agent_background_monitor.py

# Dashboard access
http://localhost:8765 (after starting production_dashboard.py)
```

## 📁 Output Structure

```
outputs/
├── analysis/           # System analysis results
├── doc_update_*/       # Documentation updates
├── workflow_*/         # Custom workflows
├── logs/              # Execution logs
├── checkpoints/       # Recovery points
└── tasks/            # Individual task results
```

## ⚡ Performance Tips

- **DPO Dial Settings:**
  - Use Level 1-2 for simple, well-defined tasks
  - Use Level 3 for professional projects
  - Use Level 4-5 for enterprise/complex requirements
- **Start small:** 3-5 agents for testing, scale up based on results
- **Use templates:** Built-in workflows are optimized and tested
- **Enable checkpoints:** For any workflow > 30 minutes
- **Monitor resources:** Check system RAM/CPU with multiple agents
- **Quality gates:** Use `--use-enhanced` for production workflows

## 🚨 Common Issues & Fixes

**"No tokens available"**
- System auto-loads tokens from multiple sources
- Check: `python -c "from src.token_loader import load_tokens; print(f'Loaded {len(load_tokens())} tokens')"`

**"Task dependency failed"**
- Check logs: `tail -f outputs/logs/orchestrator_*.log`
- Resume from checkpoint: `python resume_orchestrator.py checkpoint_id`

**"Max parallel reached"**
- Reduce `--max-parallel` setting
- Monitor system resources

## 🎛️ Advanced Features

### UnifiedOrchestrator (NEW - Fully Operational!)

**The most advanced orchestration mode with ALL features active:**

```bash
# Enable UnifiedOrchestrator with all advanced features
python main.py --tasks-file workflow.json --use-unified --max-parallel 10
```

**UnifiedOrchestrator Features (100% Functional):**
- ✅ **Quality Gates:** 4 validation gates (input, dependency, complexity, security)
- ✅ **Agent Monitoring:** Real-time tracking at 30-second intervals
- ✅ **Collaboration Module:** Team coordination for up to 5 agents
- ✅ **Execution Plans:** Adaptive phased execution support
- ✅ **Auto-Recovery:** 3 automatic retries on task failure
- ✅ **State Persistence:** Checkpoint-based recovery points
- ✅ **Enhanced Metrics:** Detailed performance analytics
- ✅ **Background Execution:** Non-blocking task processing

**Usage Example:**
```python
from src.unified.unified_orchestrator import UnifiedConfig, UnifiedOrchestrator, FeatureFlag

config = UnifiedConfig(
    output_dir=Path("./outputs"),
    max_parallel=10,
    enabled_features={
        FeatureFlag.QUALITY_GATES,
        FeatureFlag.AGENT_MONITORING,
        FeatureFlag.COLLABORATION,
        FeatureFlag.EXECUTION_PLAN,
        FeatureFlag.ENHANCED_METRICS,
        FeatureFlag.BACKGROUND_EXECUTION,
        FeatureFlag.AUTO_RECOVERY,
        FeatureFlag.STATE_PERSISTENCE,
    },
    enable_monitoring=True,
    enable_quality_gates=True,
    enable_collaboration=True
)
orchestrator = UnifiedOrchestrator(config)
```

### Enhanced Orchestrator

**Enhanced Orchestrator:** `--use-enhanced` enables quality gates, monitoring, optimizations

**Dashboard Integration:** `--enable-dashboard` provides real-time WebSocket updates

**Multi-Provider:** Supports Claude + OpenAI with automatic failover

**Collaboration:** Multi-agent coordination with conflict resolution

**Analytics:** Built-in session analysis and performance metrics

### System Prompts Enhancement (NEW!)

**Every agent now receives specialized instructions via `--append-system-prompt`:**

**How It Works:**
- Each agent type has tailored base prompts (e.g., requirements-analyst focuses on INVEST principles)
- DPO enhancement level adjusts instruction detail (0=minimal, 5=maximum with innovation focus)
- Custom prompts can be added per task via `system_prompt` field

**Agent Types with Specialized Prompts:**
- **Analysis:** requirements-analyst, business-analyst
- **Architecture:** solution-architect, database-specialist
- **Development:** development-specialist, api-integration-specialist
- **Quality:** qa-testing-guru, security-architect
- **Operations:** devops-automation, performance-optimizer
- **Documentation:** technical-writer
- **Research:** research-specialist
- **Monitoring:** monitoring-specialist

**Custom System Prompts in Tasks:**
```python
AgentTask(
    task_id="001",
    task_type="development-specialist",
    prompt="Build the feature",
    system_prompt="Focus on functional programming patterns",  # Custom addition
    enhancement_level=3  # Controls detail level
)
```

**Enhancement Levels Affect Prompts:**
- Level 0-1: Basic instructions with conciseness
- Level 2: Professional instructions (DEFAULT)
- Level 3: Enhanced with traits and tool focus
- Level 4: Production quality emphasis
- Level 5: Innovation and cutting-edge practices

## 🔗 Integration Points

- **MCP Tools:** File ops, web scraping, databases
- **External APIs:** REST endpoints for status and control
- **WebSocket:** Real-time updates for dashboards
- **Checkpoints:** Resume from any point in complex workflows

## 📖 When to Read Full Docs

- **README.md:** Installation, architecture overview, Docker deployment
- **ARCHITECTURE.md:** Technical design, data flow, performance specs
- **API_REFERENCE.md:** Complete API docs, Python classes, error codes
- **USER_GUIDE.md:** Detailed examples, configuration, troubleshooting

## 🎯 Typical Agent Workflow

1. **Plan:** Define tasks with clear dependencies
2. **Configure:** Choose template or create custom JSON
3. **Execute:** Run with appropriate parallel limits
4. **Monitor:** Use dashboard or logs to track progress
5. **Recover:** Use checkpoints if interrupted
6. **Review:** Check outputs directory for results

---

**Key Insight:** This system excels at coordinating complex, multi-step workflows where different agents specialize in different aspects (analysis, documentation, implementation, testing) and need to work together efficiently. With DPO integrated, it now automatically enhances even vague requests into sophisticated, executable workflows.

**Production Ready:** Handles 15 parallel agents, automatic recovery, quality validation, comprehensive monitoring, intelligent request enhancement (DPO), and specialized agent instructions out of the box.

**Latest Updates:**
- DPO integration complete with dial control (0-5), defaulting to Level 2 for smart enhancement
- System Prompts feature: Every agent receives role-specific instructions via `--append-system-prompt`
- UnifiedOrchestrator fully operational with all advanced features active
