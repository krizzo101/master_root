# Project Intelligence Integration Strategy for Agentic Coding

## Executive Summary
This document defines how AI agents operating in the Claude coding environment should discover, access, and utilize the `.proj-intel/` knowledge store to enhance their effectiveness, accuracy, and speed when working with the codebase.

## Core Integration Principles

### 1. Persistent Awareness
Agents must be inherently aware of the project intelligence system through:
- **CLAUDE.md directives** - Permanent instructions in project root
- **System reminders** - Contextual prompts during operations
- **Pre-flight checks** - Automatic intelligence consultation before tasks

### 2. Zero-Friction Access
Intelligence must be accessible with minimal cognitive load:
- **Shell functions** - One-command queries
- **Python imports** - Native tool integration
- **MCP tools** - Direct IDE/agent tool access

### 3. Intelligent Defaults
Agents should automatically use intelligence when appropriate without explicit instruction.

---

## Use Case Decision Tree

### WHEN to Use Project Intelligence

```
Task Received
    ↓
Is it about:
├─> Understanding Architecture? → USE: agent_architecture.jsonl
├─> Finding Files/Functions? → USE: symbol_index.json + reverse_index.json
├─> Debugging Issues? → USE: reverse_index.json for dependencies
├─> Adding Features? → USE: file_elements.min.jsonl for similar patterns
├─> Reviewing Code? → USE: file stats + quality metrics
├─> Answering Questions? → USE: Full intelligence query
└─> Simple File Edit? → Maybe skip (unless checking dependencies)
```

### Specific Triggers for Intelligence Consultation

| Task Type | Trigger Keywords | Intelligence Used | Priority |
|-----------|-----------------|-------------------|----------|
| Architecture | "how does", "explain", "understand", "design" | agent_architecture.jsonl, reverse_index | HIGH |
| Search | "find", "where", "locate", "search" | symbol_index, file_elements.min | HIGH |
| Debug | "error", "fix", "broken", "fails" | reverse_index, dependencies | HIGH |
| Feature Dev | "add", "implement", "create", "new" | Similar file patterns, architecture | MEDIUM |
| Refactor | "refactor", "optimize", "improve" | Quality metrics, dependencies | MEDIUM |
| Documentation | "document", "explain", "describe" | File elements, architecture | LOW |

---

## Access Patterns & Tools

### 1. Shell-Based Quick Access (Immediate Implementation)

```bash
# Add to CLAUDE.md or .bashrc
function proj-intel() {
    local query="$1"
    case "$query" in
        "files")
            # List files matching pattern
            jq -r '.path' .proj-intel/file_elements.min.jsonl | grep -i "$2"
            ;;
        "symbols")
            # Find symbol locations
            jq -r --arg sym "$2" '.[$sym] | .[]' .proj-intel/symbol_index.json
            ;;
        "arch")
            # Find architectural components
            jq -r 'select(.data.name | contains($2))' .proj-intel/agent_architecture.jsonl
            ;;
        "deps")
            # Find file dependencies
            jq -r --arg file "$2" '.[$file]' .proj-intel/reverse_index.json
            ;;
        *)
            echo "Usage: proj-intel [files|symbols|arch|deps] <search_term>"
            ;;
    esac
}

# Agent should run this before any task
function intel-preflight() {
    echo "=== Project Intelligence Available ==="
    echo "Files indexed: $(wc -l < .proj-intel/file_elements.min.jsonl)"
    echo "Classes/Agents: $(wc -l < .proj-intel/agent_architecture.jsonl)"
    echo "Last updated: $(jq -r .generated_at .proj-intel/proj_intel_manifest.json)"
}
```

### 2. Python Tool Integration

```python
# proj_intel_tools.py - Core access library
import json
import os
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from pathlib import Path

@dataclass
class FileInfo:
    path: str
    line_count: int
    fn_count: int
    class_count: int
    import_count: int
    content_hash: str

class ProjectIntelligence:
    """Unified interface to project intelligence data"""
    
    def __init__(self, intel_dir: str = ".proj-intel"):
        self.intel_dir = Path(intel_dir)
        self._load_indices()
    
    def _load_indices(self):
        """Lazy-load indices on first use"""
        self.manifest = None
        self.reverse_index = None
        self.symbol_index = None
        self.file_elements = []
        
    def find_files_by_pattern(self, pattern: str, 
                             min_functions: int = 0,
                             min_classes: int = 0) -> List[FileInfo]:
        """Find files matching pattern with optional filters"""
        if not self.file_elements:
            with open(self.intel_dir / "file_elements.min.jsonl") as f:
                self.file_elements = [FileInfo(**json.loads(line)) for line in f]
        
        results = []
        for file in self.file_elements:
            if pattern.lower() in file.path.lower():
                if file.fn_count >= min_functions and file.class_count >= min_classes:
                    results.append(file)
        
        return sorted(results, key=lambda x: (x.class_count, x.fn_count), reverse=True)
    
    def find_symbol(self, symbol_name: str) -> List[Dict[str, str]]:
        """Find where a symbol is defined"""
        if not self.symbol_index:
            with open(self.intel_dir / "symbol_index.json") as f:
                self.symbol_index = json.load(f)
        
        return self.symbol_index.get(symbol_name, [])
    
    def get_file_context(self, file_path: str) -> Dict:
        """Get all intelligence about a specific file"""
        if not self.reverse_index:
            with open(self.intel_dir / "reverse_index.json") as f:
                self.reverse_index = json.load(f)
        
        byte_ranges = self.reverse_index.get(file_path, [])
        
        context = {
            "path": file_path,
            "items": []
        }
        
        with open(self.intel_dir / "project_analysis.jsonl", "rb") as f:
            for entry in byte_ranges:
                f.seek(entry["byte_offset"])
                data = f.read(entry["byte_size"])
                context["items"].append(json.loads(data))
        
        return context
    
    def find_related_files(self, file_path: str, max_files: int = 10) -> List[str]:
        """Find files related through imports/dependencies"""
        context = self.get_file_context(file_path)
        
        related = set()
        for item in context["items"]:
            if item.get("collector") == "FileElementsCollector":
                imports = item.get("data", {}).get("imports", [])
                for imp in imports:
                    # Convert import to likely file path
                    if imp.startswith("."):
                        base = os.path.dirname(file_path)
                        related.add(os.path.join(base, imp.replace(".", "/") + ".py"))
                    else:
                        related.add(imp.replace(".", "/") + ".py")
        
        return list(related)[:max_files]
    
    def get_architecture_summary(self, component_filter: str = None) -> Dict:
        """Get architectural overview"""
        summary = {
            "total_classes": 0,
            "total_agents": 0,
            "components": []
        }
        
        with open(self.intel_dir / "agent_architecture.jsonl") as f:
            for line in f:
                item = json.loads(line)
                data = item.get("data", {})
                
                if component_filter and component_filter not in data.get("file_path", ""):
                    continue
                
                summary["total_classes"] += 1
                if "agent" in data.get("name", "").lower():
                    summary["total_agents"] += 1
                
                summary["components"].append({
                    "name": data.get("name"),
                    "file": data.get("file_path"),
                    "methods": len(data.get("methods", [])),
                    "bases": data.get("bases", [])
                })
        
        return summary

# Singleton for easy access
proj_intel = ProjectIntelligence()
```

### 3. Agent Decision Logic

```python
# agent_intel_integration.py
from typing import Optional, List, Dict
import re

class IntelligentContextLoader:
    """Automatically loads relevant context based on task analysis"""
    
    TASK_PATTERNS = {
        "architecture": ["how does", "explain", "architecture", "design", "structure"],
        "search": ["find", "where", "locate", "search", "look for"],
        "debug": ["error", "fix", "broken", "fails", "debug", "issue"],
        "feature": ["add", "implement", "create", "new feature", "build"],
        "refactor": ["refactor", "optimize", "improve", "clean up"],
        "review": ["review", "check", "analyze", "quality"],
    }
    
    def __init__(self, proj_intel):
        self.intel = proj_intel
    
    def analyze_task(self, user_prompt: str) -> str:
        """Determine task type from user prompt"""
        prompt_lower = user_prompt.lower()
        
        for task_type, patterns in self.TASK_PATTERNS.items():
            if any(pattern in prompt_lower for pattern in patterns):
                return task_type
        
        return "general"
    
    def load_context(self, user_prompt: str, 
                    mentioned_files: List[str] = None) -> Dict:
        """Load appropriate context based on task analysis"""
        
        task_type = self.analyze_task(user_prompt)
        context = {
            "task_type": task_type,
            "relevant_files": [],
            "symbols": [],
            "architecture": None,
            "suggestions": []
        }
        
        # Extract potential file/symbol references from prompt
        file_pattern = r'[a-zA-Z_][a-zA-Z0-9_]*\.py'
        symbol_pattern = r'\b[A-Z][a-zA-Z0-9]*\b'  # Class-like names
        
        potential_files = re.findall(file_pattern, user_prompt)
        potential_symbols = re.findall(symbol_pattern, user_prompt)
        
        # Load context based on task type
        if task_type == "architecture":
            context["architecture"] = self.intel.get_architecture_summary()
            context["suggestions"].append("Consider using agent_architecture.jsonl for detailed class information")
            
        elif task_type == "search":
            for symbol in potential_symbols:
                found = self.intel.find_symbol(symbol)
                if found:
                    context["symbols"].extend(found)
            
            # Search for files by keywords
            keywords = self._extract_keywords(user_prompt)
            for keyword in keywords:
                files = self.intel.find_files_by_pattern(keyword)
                context["relevant_files"].extend(files[:5])
                
        elif task_type == "debug":
            if mentioned_files:
                for file in mentioned_files:
                    related = self.intel.find_related_files(file)
                    context["relevant_files"].extend(related)
                    context["suggestions"].append(f"Check dependencies of {file}")
                    
        elif task_type == "feature":
            # Find similar existing features
            keywords = self._extract_keywords(user_prompt)
            for keyword in keywords:
                similar = self.intel.find_files_by_pattern(keyword, min_classes=1)
                context["relevant_files"].extend(similar[:3])
                context["suggestions"].append(f"Review {similar[0].path} for patterns")
                
        elif task_type == "refactor":
            # Load quality metrics and dependencies
            if mentioned_files:
                for file in mentioned_files:
                    context["relevant_files"].append(self.intel.get_file_context(file))
                    
        return context
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Remove common words and extract significant terms
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}
        words = re.findall(r'\b[a-z]+\b', text.lower())
        return [w for w in words if len(w) > 3 and w not in stopwords][:5]
```

---

## Implementation Roadmap

### Phase 1: Immediate Actions (Now)
1. ✅ Create this strategy document
2. Add intelligence awareness to CLAUDE.md
3. Create basic shell functions for access
4. Test with simple queries

### Phase 2: Tool Development (Next Session)
1. Implement `proj_intel_tools.py` library
2. Create MCP tool wrapper for direct access
3. Add automatic context loading hooks
4. Create usage examples and tests

### Phase 3: Agent Integration (Following Session)
1. Modify agent base classes to use intelligence
2. Add pre-flight intelligence checks
3. Implement context caching for performance
4. Create feedback loop for intelligence updates

### Phase 4: Advanced Features (Future)
1. Real-time intelligence updates on file changes
2. Machine learning for relevance ranking
3. Cross-project intelligence sharing
4. Performance analytics and optimization

---

## Usage Examples

### Example 1: Architecture Question
```python
# User asks: "How does the agent orchestration system work?"

# Agent automatically:
intel = ProjectIntelligence()
arch = intel.get_architecture_summary(component_filter="orchestrat")
print(f"Found {arch['total_classes']} orchestration components")

# Then examines specific classes
for component in arch['components'][:5]:
    context = intel.get_file_context(component['file'])
    # Analyze and explain...
```

### Example 2: Debugging Task
```python
# User reports: "The ConsultAgent is failing with an import error"

# Agent automatically:
intel = ProjectIntelligence()

# Find the ConsultAgent
symbols = intel.find_symbol("ConsultAgent")
if symbols:
    file_path = symbols[0]['file_path']
    
    # Get all related files
    related = intel.find_related_files(file_path)
    print(f"Checking {len(related)} related files for import issues")
    
    # Examine each for potential problems
    for rel_file in related:
        context = intel.get_file_context(rel_file)
        # Check imports, versions, etc.
```

### Example 3: Feature Development
```python
# User requests: "Add a new caching mechanism to the research agent"

# Agent automatically:
intel = ProjectIntelligence()
loader = IntelligentContextLoader(intel)

# Load relevant context
context = loader.load_context("Add a new caching mechanism to the research agent")

# Find existing caching patterns
cache_files = intel.find_files_by_pattern("cache")
print(f"Found {len(cache_files)} files with caching patterns to review")

# Find the research agent
research_files = intel.find_files_by_pattern("research")
print(f"Found {len(research_files)} research agent files")

# Analyze patterns and implement...
```

---

## Success Metrics

### Quantitative
- **Context Load Time**: < 500ms for any query
- **Relevance Score**: > 80% of loaded files are actually used
- **Task Completion**: 30% faster with intelligence vs without
- **Error Reduction**: 50% fewer wrong-file edits

### Qualitative
- Agents proactively use intelligence without prompting
- Developers report improved agent accuracy
- Reduced token usage from targeted context
- Faster onboarding for new features

---

## Maintenance & Updates

### Intelligence Refresh Schedule
- **Automatic**: On significant commits (>10 files changed)
- **Scheduled**: Daily at 2 AM for active projects
- **Manual**: Via `project-intelligence full-package` command

### Quality Assurance
1. Verify intelligence freshness before major operations
2. Alert if intelligence is >24 hours old
3. Validate file paths still exist before using
4. Update intelligence after large refactoring

---

## Conclusion

By deeply integrating the `.proj-intel/` knowledge store into the agent workflow, we transform reactive code assistance into proactive, context-aware development partners. Agents become knowledgeable about the codebase structure, making them faster, more accurate, and more helpful.

The key is making this integration invisible to users while ensuring agents always have the context they need to excel.