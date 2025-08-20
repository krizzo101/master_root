#!/usr/bin/env python3
"""
Verify that required MCP tools were used in each SDLC phase.
Creates audit trail of tool usage.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class SDLCToolVerification:
    """Enforce and track required tool usage per SDLC phase."""
    
    REQUIRED_TOOLS = {
        "discovery": [
            "mcp__resource_discovery__search_resources",
            "mcp__knowledge__knowledge_query", 
            "mcp__mcp_web_search__brave_web_search"
        ],
        "design": [
            "mcp__resource_discovery__check_package_exists",
            "mcp__knowledge__knowledge_query"
        ],
        "planning": [
            "TodoWrite"
        ],
        "development": [
            "Write",
            "MultiEdit",
            "Bash",
            "TodoWrite"
        ],
        "testing": [
            "Bash",  # For running tests
            "Read"   # For checking results
        ]
    }
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.audit_file = self.project_path / ".sdlc" / "tool_audit.json"
        self.audit_file.parent.mkdir(parents=True, exist_ok=True)
        self.audit = self.load_audit()
    
    def load_audit(self) -> Dict:
        """Load existing audit trail."""
        if self.audit_file.exists():
            with open(self.audit_file) as f:
                return json.load(f)
        return {"phases": {}, "project": str(self.project_path)}
    
    def save_audit(self):
        """Save audit trail."""
        with open(self.audit_file, 'w') as f:
            json.dump(self.audit, f, indent=2)
    
    def record_tool_use(self, phase: str, tool: str, details: Dict[str, Any] = None):
        """Record that a tool was used."""
        if phase not in self.audit["phases"]:
            self.audit["phases"][phase] = {
                "tools_used": [],
                "started": datetime.now().isoformat()
            }
        
        tool_record = {
            "tool": tool,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        
        self.audit["phases"][phase]["tools_used"].append(tool_record)
        self.save_audit()
        print(f"✅ Recorded use of {tool} in {phase} phase")
    
    def verify_phase_tools(self, phase: str) -> bool:
        """Verify all required tools were used in a phase."""
        required = set(self.REQUIRED_TOOLS.get(phase, []))
        
        if phase not in self.audit["phases"]:
            print(f"❌ No tool usage recorded for {phase} phase")
            return False
        
        used_tools = set([
            record["tool"] 
            for record in self.audit["phases"][phase]["tools_used"]
        ])
        
        missing = required - used_tools
        
        if missing:
            print(f"❌ Missing required tools in {phase}: {missing}")
            return False
        
        print(f"✅ All required tools used in {phase} phase")
        return True
    
    def generate_phase_checklist(self, phase: str) -> str:
        """Generate executable checklist for a phase."""
        required = self.REQUIRED_TOOLS.get(phase, [])
        
        checklist = f"""
# {phase.upper()} Phase Tool Checklist
# Generated: {datetime.now().isoformat()}

## Required Tools:
"""
        for tool in required:
            checklist += f"- [ ] {tool}\n"
        
        checklist += f"""
## Execute in order:

```python
# 1. Resource Discovery (if discovery/design phase)
"""
        if "mcp__resource_discovery__search_resources" in required:
            checklist += """result = mcp__resource_discovery__search_resources(
    functionality="<describe what you're looking for>",
    search_depth=2
)
verifier.record_tool_use("{phase}", "mcp__resource_discovery__search_resources", {"results": len(result)})
"""
        
        if "mcp__knowledge__knowledge_query" in required:
            checklist += """
# 2. Knowledge System Query  
result = mcp__knowledge__knowledge_query(
    query_type="search",
    query_text="<your search terms>"
)
verifier.record_tool_use("{phase}", "mcp__knowledge__knowledge_query", {"results": len(result)})
"""
        
        if "TodoWrite" in required:
            checklist += """
# 3. Task Management
TodoWrite(todos=[...])  # From planning document
verifier.record_tool_use("{phase}", "TodoWrite", {"task_count": len(todos)})
"""
        
        checklist += """```

## Verify completion:
```bash
python .claude/commands/sdlc-tool-verification.py verify {project_path} {phase}
```
"""
        return checklist

def main():
    """CLI for tool verification."""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage:")
        print("  Record: python sdlc-tool-verification.py record <project> <phase> <tool> [details]")
        print("  Verify: python sdlc-tool-verification.py verify <project> <phase>")
        print("  Checklist: python sdlc-tool-verification.py checklist <project> <phase>")
        sys.exit(1)
    
    action = sys.argv[1]
    project = Path(sys.argv[2])
    
    verifier = SDLCToolVerification(project)
    
    if action == "record":
        phase = sys.argv[3]
        tool = sys.argv[4]
        details = json.loads(sys.argv[5]) if len(sys.argv) > 5 else {}
        verifier.record_tool_use(phase, tool, details)
        
    elif action == "verify":
        phase = sys.argv[3]
        if not verifier.verify_phase_tools(phase):
            sys.exit(1)
            
    elif action == "checklist":
        phase = sys.argv[3]
        print(verifier.generate_phase_checklist(phase))
    
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)

if __name__ == "__main__":
    main()