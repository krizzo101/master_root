# Development Process Orchestrator - User Guide

**Your Complete Guide to AI-Powered Development Workflow Automation**

---

## 🚀 Quick Start

### What You'll Accomplish
In 5 minutes, you'll be running your first AI agent workflow that can:
- Generate complete project documentation
- Analyze system architecture
- Coordinate multiple AI agents simultaneously
- Resume work from interruptions automatically

### Prerequisites Check
✅ **Python 3.8+** (Check: `python --version`)
✅ **Claude API access** (Get from [Anthropic Console](https://console.anthropic.com/))
✅ **Basic command line familiarity**

### 30-Second Setup
```bash
# 1. Navigate to the orchestrator
cd /home/opsvi/master_root/apps/agent-orchestrator

# 2. Test the system (creates example workflow)
python run.py

# 3. Choose option 1 for your first workflow
```

**What just happened?** The orchestrator created 3 AI agents:
1. **Research Agent** → Studied Python async programming
2. **Design Agent** → Created a web server architecture
3. **Implementation Agent** → Wrote actual FastAPI code

All working together, automatically, with intelligent coordination.

---

## 📋 Table of Contents

1. [Core Features Overview](#core-features-overview)
2. [Common Workflows](#common-workflows)
3. [Configuration Guide](#configuration-guide)
4. [Troubleshooting](#troubleshooting)
5. [Best Practices](#best-practices)
6. [Advanced Usage](#advanced-usage)
7. [FAQ](#faq)

---

## 🎯 Core Features Overview

### Multi-Agent Coordination
**What it does:** Runs up to 15 AI agents simultaneously, each working on different parts of your task.

**Real example:** Generate documentation for your entire project:
```bash
python run_orchestrator_task.py \
  --task-type system-documentation \
  --app-name "my-project" \
  --app-root "/path/to/project"
```
**Result:** 6 agents create README, API docs, user guide, deployment guide, and architecture docs **simultaneously**.

### Smart Dependency Management
**What it does:** Automatically figures out what order tasks should run in.

**Real example:** "Write tests" runs **after** "analyze code" but **before** "generate report".

**Your benefit:** No manual task ordering - the system is intelligent enough to understand dependencies.

### Checkpoint & Recovery
**What it does:** Never lose work again. Resume from exactly where you left off.

**Real example:**
```bash
# Your internet cut out during a 30-minute workflow
python resume_orchestrator.py --list-checkpoints

# Resume from the last checkpoint
python resume_orchestrator.py checkpoint_abc123
```

### Real-Time Monitoring
**What it does:** Watch your agents work in real-time with a web dashboard.

**How to use:**
```bash
# Start the dashboard server
python production_dashboard.py --host 0.0.0.0 --port 8765

# Visit: http://localhost:8765
```
**What you see:** Live agent status, progress bars, resource usage, and completion times.

---

## 🔄 Common Workflows

### Workflow 1: Complete Project Documentation
**Perfect for:** Any software project that needs professional documentation.

```bash
python run_orchestrator_task.py \
  --task-type system-documentation \
  --app-name "my-awesome-app" \
  --app-root "/Users/me/projects/my-app" \
  --template comprehensive
```

**What happens:**
- 🔍 **Architecture Agent** maps your system structure
- 📖 **API Agent** generates complete API documentation
- 👤 **User Guide Agent** writes end-user instructions
- 🛠️ **Developer Agent** creates setup and contribution guides
- 🚀 **Deployment Agent** documents deployment procedures
- 📋 **README Agent** creates an engaging project overview

**Time:** 15-30 minutes | **Cost:** ~$2-4 | **Output:** Professional-grade documentation suite

### Workflow 2: System Health Analysis
**Perfect for:** Understanding your codebase's current state and getting improvement recommendations.

```bash
python run_system_analysis.py
```

**What happens:**
- 🏗️ **Architecture Analyst** examines system design patterns
- ⚡ **Performance Analyst** identifies optimization opportunities
- 🔒 **Security Analyst** checks for vulnerabilities
- 📊 **Metrics Analyst** evaluates code quality
- 🔧 **Integration Analyst** reviews component relationships

**Time:** 20-40 minutes | **Cost:** ~$3-6 | **Output:** Comprehensive analysis report with actionable recommendations

### Workflow 3: Parallel Documentation Updates
**Perfect for:** Keeping multiple docs in sync across a large project.

```bash
python run_parallel_doc_update.py
```

**What happens:**
- Multiple specialist agents update different documentation files simultaneously
- Changes are coordinated to maintain consistency
- Cross-references between documents are validated
- Style and format consistency is enforced

**Time:** 10-20 minutes | **Cost:** ~$1-3 | **Output:** Synchronized documentation suite

### Workflow 4: Custom Multi-Step Process
**Perfect for:** Complex workflows that need multiple specialized agents.

**Step 1:** Create your workflow file (`my_workflow.json`):
```json
{
  "tasks": [
    {
      "task_id": "security_audit",
      "task_type": "security-expert",
      "prompt": "Perform security analysis focusing on authentication and data protection"
    },
    {
      "task_id": "performance_analysis",
      "task_type": "performance-expert",
      "prompt": "Analyze performance bottlenecks and optimization opportunities"
    },
    {
      "task_id": "integration_report",
      "task_type": "integration-expert",
      "prompt": "Create integration strategy based on security and performance findings",
      "dependencies": ["security_audit", "performance_analysis"]
    }
  ]
}
```

**Step 2:** Execute your workflow:
```bash
python main.py --tasks-file my_workflow.json --max-parallel 5
```

---

## ⚙️ Configuration Guide

### Basic Settings

**Control Parallel Execution:**
```bash
# Conservative (good for testing)
python main.py --max-parallel 3

# Balanced (recommended for most workflows)
python main.py --max-parallel 8

# Aggressive (for powerful systems)
python main.py --max-parallel 15
```

**Choose Output Location:**
```bash
python main.py --output-dir "/custom/results/path"
```

**Enable Real-Time Dashboard:**
```bash
python main.py --enable-dashboard
# Then visit: http://localhost:8765
```

### Token Management (Automatic)
The system automatically:
- Loads tokens from multiple sources
- Distributes requests across available tokens
- Handles rate limits gracefully
- Falls back to alternative providers if needed

**No manual token configuration required** - the orchestrator handles everything.

### Advanced Configuration

**Production Settings:**
Create `production_config.json`:
```json
{
  "host": "0.0.0.0",
  "port": 8765,
  "max_connections": 500,
  "max_parallel": 15,
  "enable_monitoring": true,
  "checkpoint_interval": 5,
  "quality_gates_enabled": true
}
```

**Use it:**
```bash
python production_dashboard.py --config production_config.json
```

### Templates Available

| Template | Best For | Agents Used | Time |
|----------|----------|-------------|------|
| `minimal` | Small utilities, scripts | 2-3 agents | 5-10 min |
| `standard` | Most projects | 4-6 agents | 15-25 min |
| `comprehensive` | Large applications | 6-8 agents | 25-40 min |
| `api-focused` | Libraries, services | 3-5 agents | 10-20 min |

**Usage:**
```bash
python run_orchestrator_task.py \
  --task-type system-documentation \
  --template api-focused \
  --app-name "my-api"
```

---

## 🔧 Troubleshooting

### "No tokens available"
**What it means:** The orchestrator can't access Claude API tokens.

**Solutions:**
1. **Check token status:**
   ```bash
   python -c "from src.token_loader import load_tokens; print(f'Found {len(load_tokens())} tokens')"
   ```

2. **Verify token sources:** The orchestrator tries these in order:
   - Enhanced token loader (typically 19 tokens)
   - Environment variables
   - Configuration files
   - Default token files

3. **Check logs for details:**
   ```bash
   tail -f outputs/logs/orchestrator_*.log
   ```

### "Task failed with dependency error"
**What it means:** A task couldn't run because something it depends on failed.

**Solutions:**
1. **Check what failed:**
   ```bash
   # Look at the most recent logs
   ls -la outputs/logs/ | tail -5
   cat outputs/logs/orchestrator_LATEST.log | grep ERROR
   ```

2. **Resume from last working point:**
   ```bash
   python resume_orchestrator.py --list-checkpoints
   python resume_orchestrator.py checkpoint_ID_HERE
   ```

3. **Modify dependencies:** Edit your JSON task file to remove problematic dependencies.

### "Max parallel limit reached"
**What it means:** Too many agents trying to run at once.

**Solutions:**
1. **Reduce parallel limit:**
   ```bash
   python main.py --max-parallel 5  # Instead of 15
   ```

2. **Check system resources:**
   ```bash
   # Monitor memory usage
   python agent_background_monitor.py
   ```

3. **Optimize task design:** Break large tasks into smaller, more focused ones.

### "Dashboard not updating"
**What it means:** The web dashboard isn't showing real-time updates.

**Solutions:**
1. **Ensure dashboard is enabled:**
   ```bash
   python main.py --enable-dashboard
   ```

2. **Check the dashboard port:**
   ```bash
   # Default is 8765
   curl http://localhost:8765/health
   ```

3. **Restart with explicit configuration:**
   ```bash
   python production_dashboard.py --host 0.0.0.0 --port 8765
   ```

### Getting Detailed Help

**Enable verbose logging:**
```bash
python main.py --debug --verbose
```

**Check specific checkpoint details:**
```bash
python resume_orchestrator.py --details checkpoint_abc123
```

**Monitor active processes:**
```bash
python agent_background_monitor.py
```

---

## 🎯 Best Practices

### Workflow Design

**✅ DO:**
- Start with 3-5 agents for your first workflows
- Use clear, specific task descriptions
- Define dependencies explicitly when tasks depend on each other
- Test with `--max-parallel 3` before scaling up

**❌ DON'T:**
- Create overly broad tasks ("Analyze everything")
- Skip dependency definitions when order matters
- Run more than 15 agents without monitoring resources
- Ignore checkpoint warnings

### Resource Management

**Optimal Parallel Settings by Use Case:**
- **Documentation:** 3-6 agents
- **Code Analysis:** 5-8 agents
- **Complex Workflows:** 8-12 agents
- **Production Systems:** Monitor at 12+ agents

**Memory Guidelines:**
- **4GB RAM:** Max 5 parallel agents
- **8GB RAM:** Max 10 parallel agents
- **16GB+ RAM:** Up to 15 parallel agents

### Cost Optimization

**Typical Costs:**
- Simple documentation: $1-2
- System analysis: $2-5
- Complex workflows: $3-8

**Cost-saving tips:**
- Use focused, specific prompts (reduces token usage)
- Start with smaller agent counts to test workflows
- Use checkpoints for long workflows (avoid re-running work)
- Monitor token usage in dashboard

### Quality Assurance

**Enable quality gates for production:**
```bash
python main.py --use-enhanced --enable-dashboard
```

**Review outputs systematically:**
1. Check logs for any errors or warnings
2. Verify all expected outputs were created
3. Review checkpoint status for completeness
4. Test any generated code or configurations

---

## 🚀 Advanced Usage

### Available Scripts Quick Reference

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `main.py` | Core orchestrator | Custom workflows, JSON task files |
| `run_orchestrator_task.py` | Template workflows | System documentation, standard tasks |
| `run_system_analysis.py` | Self-analysis | Understanding orchestrator capabilities |
| `run_parallel_doc_update.py` | Documentation sync | Keeping multiple docs synchronized |
| `resume_orchestrator.py` | Checkpoint management | Resuming interrupted work |
| `production_dashboard.py` | Monitoring dashboard | Real-time workflow monitoring |
| `agent_background_monitor.py` | Process monitoring | Checking background agent status |

### Custom Agent Development

**Create specialized agents for your domain:**

```python
from src.generic_orchestrator import AgentTask

# Create a specialized security audit agent
security_task = AgentTask(
    task_id="security_audit",
    task_type="security-specialist",
    prompt="Analyze authentication security and data protection measures",
    quality_gates=["security_checklist", "vulnerability_scan"],
    context={"focus_areas": ["auth", "data_protection", "encryption"]}
)
```

### Production Monitoring

**Real-time Dashboard:**
```bash
# Start production dashboard with custom config
python production_dashboard.py --config production_config.json --log-level INFO

# Access at: http://localhost:8765
```

**Background Process Monitoring:**
```bash
# Monitor all background agents
python agent_background_monitor.py

# Check specific orchestration status
python agent_background_monitor.py --orchestration-id abc123
```

### Integration with External Systems

**Webhook Integration:**
```python
def dashboard_callback(state_data):
    # Send updates to your monitoring system
    requests.post("https://your-dashboard.com/api/updates", json=state_data)

orchestrator = GenericOrchestrator(
    dashboard_state_callback=dashboard_callback
)
```

**Custom Quality Gates:**
```python
# Add custom validation rules
custom_gates = {
    "code_security": "Check for security vulnerabilities",
    "performance_standards": "Verify performance requirements",
    "documentation_completeness": "Ensure all sections covered"
}
```

### Performance Optimization

**Memory Optimization:**
- Monitor with `agent_background_monitor.py`
- Adjust `--max-parallel` based on available RAM
- Use checkpoints for long-running workflows

**Token Efficiency:**
- Use specific, focused prompts
- Enable context sharing between related tasks
- Leverage built-in optimization features

**Network Optimization:**
- Multiple token pools distribute API load
- Automatic rate limit handling
- Built-in retry mechanisms with exponential backoff

---

## ❓ FAQ

### General Usage

**Q: How many agents can I run at once?**
A: Up to 15 agents simultaneously. Start with 5-8 and monitor system performance. The orchestrator automatically manages resources and prevents system overload.

**Q: What happens if my internet disconnects?**
A: The orchestrator creates automatic checkpoints every few completed tasks. Use `resume_orchestrator.py --list-checkpoints` to see recovery points and resume exactly where you left off.

**Q: Can I run multiple orchestrations simultaneously?**
A: Yes, but use different output directories: `--output-dir /path/1` and `--output-dir /path/2`. Monitor system resources when running multiple orchestrations.

### Cost and Performance

**Q: How much does it cost to run workflows?**
A: Typical costs:
- Documentation generation: $1-3
- System analysis: $2-5
- Complex multi-step workflows: $3-8
The orchestrator optimizes token usage to minimize costs.

**Q: How long do workflows take?**
A: Timing varies by complexity:
- Simple documentation: 10-20 minutes
- System analysis: 20-40 minutes
- Complex workflows: 30-60+ minutes
Parallel execution significantly reduces total time.

**Q: Can I speed up workflows?**
A: Yes:
- Increase `--max-parallel` (up to system limits)
- Use more focused, specific prompts
- Enable optimizations with `--use-enhanced`
- Use templates instead of custom workflows

### Technical Questions

**Q: What's the difference between the various scripts?**
A:
- **`main.py`** - Core engine for custom JSON workflows
- **`run_orchestrator_task.py`** - Template-based workflows (system docs, etc.)
- **`run_system_analysis.py`** - Pre-configured system analysis
- **`resume_orchestrator.py`** - Checkpoint and recovery management
- **`production_dashboard.py`** - Web-based monitoring interface

**Q: How do I know if my workflow succeeded?**
A: Check multiple indicators:
- All tasks show "completed" status in logs
- No errors in `outputs/logs/orchestrator_*.log`
- Expected output files created in results directory
- Dashboard shows 100% completion (if enabled)

**Q: Can I modify running workflows?**
A: No, but you can:
- Add new follow-up tasks after completion
- Resume with modifications from checkpoints
- Create dependent workflows that build on results

### Troubleshooting

**Q: What if a task keeps failing?**
A: Common solutions:
1. Check logs for specific error details
2. Simplify the task prompt (may be too complex)
3. Remove dependencies that might be causing issues
4. Try running the task individually to isolate the problem

**Q: How do I optimize for my specific use case?**
A:
- **Documentation:** Use `api-focused` or `comprehensive` templates
- **Analysis:** Start with `run_system_analysis.py`
- **Custom workflows:** Begin with simple 3-task examples
- **Production:** Enable `--use-enhanced` and monitoring

---

## 📚 Additional Resources

### Output Structure
When you run any workflow, results are organized clearly:

```
outputs/
├── system-documentation_20240115_143022/    # Timestamped workflow results
│   ├── README.md                            # Generated documentation
│   ├── ARCHITECTURE.md
│   ├── API_REFERENCE.md
│   └── logs/                                # Detailed execution logs
├── checkpoints/                             # Recovery points
│   └── checkpoint_abc123.json
└── logs/                                    # Global orchestrator logs
    └── orchestrator_20240115.log
```

### System Requirements

**Minimum:**
- Python 3.8+
- 4GB RAM
- Claude API access
- Internet connection

**Recommended:**
- Python 3.10+
- 8GB RAM
- Multiple API tokens
- 16GB+ RAM for large-scale workflows

**Optimal:**
- 16GB+ RAM
- SSD storage
- Multiple API providers configured
- Dedicated network connection

### Integration Examples

**CI/CD Integration:**
```bash
# Add to your pipeline
python run_orchestrator_task.py \
  --task-type system-documentation \
  --app-name "$CI_PROJECT_NAME" \
  --app-root "$CI_PROJECT_DIR" \
  --output-dir "$CI_PROJECT_DIR/docs"
```

**Development Workflow:**
```bash
# Daily documentation updates
python run_parallel_doc_update.py

# Weekly system health check
python run_system_analysis.py

# Before major releases
python main.py --tasks-file release_preparation.json
```

---

*For technical implementation details, see [Developer Guide](DEVELOPER_GUIDE.md). For system architecture, see [Architecture Documentation](ARCHITECTURE.md).*

**Need help?** Check the logs first, then use `--debug` mode for detailed troubleshooting information.
