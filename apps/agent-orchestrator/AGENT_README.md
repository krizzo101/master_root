# 🤖 AGENT QUICK START GUIDE

**For all Claude Code agents working in this codebase**

## 🚀 ESSENTIAL FIRST ACTIONS

### **1. Query Knowledge Base (MANDATORY)**
```python
# Run this on session start to get current project context
mcp__knowledge__knowledge_query(
    query_type="recent", 
    limit=5
)

# Search for specific project info
mcp__knowledge__knowledge_query(
    query_type="search",
    search_text="orchestrator parallel agent coordination",
    limit=3
)
```

### **2. Check Current Time & Status**
```python
mcp__time__current_time("YYYY-MM-DD HH:mm:ss")
```

---

## 🎯 KEY SYSTEMS AVAILABLE

### **🔧 Multi-Agent Orchestrator** (PRODUCTION READY)
**Location**: `apps/agent-orchestrator/` (you are here)  
**Status**: ✅ 100% validated, parallel execution confirmed  
**Purpose**: Coordinate multiple specialized agents in parallel

**Quick Test**:
```python
cd apps/agent-orchestrator
python -c "
from pathlib import Path
import sys
sys.path.append('./src')
from generic_orchestrator import GenericOrchestrator, AgentTask

# Test basic orchestrator functionality
print('✅ Orchestrator imports working')
"
```

**Essential Documentation**:
- `ORCHESTRATOR_USAGE_README.md` - Core usage patterns (in this directory)
- `README.md` - Main documentation (in this directory)
- `PARALLEL_EXECUTION_COMPREHENSIVE_REPORT.md` - Validation results (in this directory)
- `docs/TUTORIALS.md` - Step-by-step examples

### **📊 Knowledge Base** (ACTIVE)
**Status**: ✅ Online and responsive  
**Purpose**: Project memory and context sharing between agents

**Key Queries**:
```python
# Get recent project work
mcp__knowledge__knowledge_query(query_type="recent", limit=5)

# Find specific topics  
mcp__knowledge__knowledge_query(
    query_type="search", 
    search_text="your topic here", 
    limit=3
)

# Store your findings
mcp__knowledge__knowledge_store(
    content="Your important findings or solutions",
    knowledge_type="WORKFLOW", 
    tags="relevant,tags,here"
)
```

### **🔍 Chat Log Search** 
**Location**: `apps/chat-search/chat_search.py`  
**Purpose**: Search previous agent sessions and find context

```bash
# Search for specific topics in previous sessions
python apps/chat-search/chat_search.py "orchestrator" --limit 5

# Find user requests
python apps/chat-search/chat_search.py "implement" --type user --limit 3

# Search by date
python apps/chat-search/chat_search.py "parallel" --date-from 2025-09-04
```

---

## 🏗️ PROJECT STRUCTURE

```
/home/opsvi/master_root/
├── AGENT_README.md (this file)
├── CLAUDE.md (project instructions)
├── apps/
│   ├── agent-orchestrator/ (multi-agent coordination)
│   ├── chat-search/ (session search tool)
│   └── [other apps...]
├── libs/ (shared libraries)
└── docs/ (project documentation)
```

---

## 📋 COMMON AGENT TASKS

### **🔄 Multi-Agent Coordination**
When your task can benefit from multiple specialized agents:

```python
# Example: Research → Design → Implement workflow
# Run this from the orchestrator directory
from src.generic_orchestrator import GenericOrchestrator, AgentTask

orchestrator = GenericOrchestrator(
    output_dir=Path("./coordination_output"),
    max_parallel=3
)

tasks = [
    AgentTask("research", "research-genius", "Research the problem domain"),
    AgentTask("design", "solution-architect", "Design solution", dependencies=["research"]),
    AgentTask("implement", "development-specialist", "Implement design", dependencies=["design"])
]

results = await orchestrator.execute_batch(tasks)
```

### **📚 Session Handoff**
When taking over from previous agents:

```bash
# Use handoff command to get session context
/handoff "find previous agent session"

# Or search manually
python apps/chat-search/chat_search.py "Agent [X]" --limit 10
```

### **🧠 Knowledge Management**
Always store important findings:

```python
# After completing significant work
mcp__knowledge__knowledge_store(
    content="SYSTEM_TRUTH: Your key findings and solutions...",
    knowledge_type="WORKFLOW",
    tags="project-area,your-role,solution"
)
```

---

## ⚡ QUICK VALIDATION CHECKLIST

Before starting major work, validate your environment:

- [ ] **Knowledge Base responds** to queries
- [ ] **Current time/date** retrieved  
- [ ] **Project structure** confirmed at `/home/opsvi/master_root/`
- [ ] **Orchestrator available** if doing multi-agent work
- [ ] **Previous session context** understood (if continuation)
- [ ] **Git status** checked for current branch/changes

---

## 🎯 DECISION FRAMEWORKS

### **When to Use Multi-Agent Orchestrator**
✅ **YES**: Task needs 2+ specialized roles (research + coding + testing)  
✅ **YES**: Work can be parallelized (multiple independent parts)  
✅ **YES**: Complex enough to benefit from specialization  
❌ **NO**: Simple single-agent task  
❌ **NO**: Only 1 token available  

### **When to Search Previous Sessions**
✅ **YES**: Continuing previous agent's work  
✅ **YES**: Understanding project context  
✅ **YES**: Finding solutions to similar problems  
❌ **NO**: Completely new unrelated task

---

## 🚨 CRITICAL REMINDERS

### **Knowledge Base is Your Memory**
- Query it first to understand current project state
- Store all significant findings for future agents
- Use descriptive tags for easy retrieval

### **Orchestrator is Production Ready**
- 100% validated with 12 successful parallel agent tests
- Supports 4-token pool with 3 max parallel agents
- Use for ANY multi-agent coordination needs

### **Documentation May Be Incomplete**
- If referenced docs don't exist, create them
- Always validate file paths before referencing
- Update this guide if you find gaps

---

## 🆘 TROUBLESHOOTING

### **Knowledge Base Issues**
```python
# Test KB connectivity
try:
    result = mcp__knowledge__knowledge_query(query_type="recent", limit=1)
    print("✅ KB online")
except:
    print("❌ KB offline - work without it")
```

### **Orchestrator Issues**
```bash
# Quick orchestrator test
cd apps/agent-orchestrator
python -c "
from pathlib import Path
import sys
sys.path.append('./src')
try:
    from generic_orchestrator import GenericOrchestrator
    print('✅ Orchestrator ready')
except Exception as e:
    print(f'❌ Orchestrator issue: {e}')
"
```

### **Missing Documentation**
If docs referenced don't exist:
1. Search for similar files in the directory
2. Check knowledge base for the information
3. Create missing documentation if needed
4. Update this guide with corrections

---

**🎉 You're Ready to Start!**

This guide provides everything needed to discover and use the key systems in this codebase. Always start with KB queries to get current context, then choose the right tools for your task.

*Last updated: September 4, 2025 by Agent 2*