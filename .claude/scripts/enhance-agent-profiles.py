#!/usr/bin/env python3
"""
Enhance agent profiles with explicit tool usage instructions.
"""

import re
from pathlib import Path

# Enhanced tool awareness section to inject
TOOL_AWARENESS_SECTION = """
## 🛠️ CRITICAL: YOU HAVE THESE TOOLS - USE THEM!

### **MANDATORY: Check Time First**
```python
mcp__time__current_time("YYYY-MM-DD HH:mm:ss")  # ALWAYS FIRST
```

### **File Operations**
- `Read(file_path)` - Read files (NOT cat/head/tail)
- `Write(file_path, content)` - Create files
- `Edit(file_path, old, new)` - Modify files
- `MultiEdit(file_path, edits[])` - Batch edits

### **Search Operations (USE BEFORE READING)**
- `Grep(pattern, path)` - Search contents (NOT grep command)
- `Glob(pattern)` - Find files (NOT find command)
- `LS(path)` - List directories

### **Execution & Tracking**
- `Bash(command)` - Shell commands
- `TodoWrite(todos)` - Task tracking (use for 3+ steps)

### **MCP Tools (PREFER OVER BASH)**
- `mcp__firecrawl__*` - Web scraping (NOT curl)
- `mcp__tech_docs__*` - Documentation lookup
- `mcp__knowledge__*` - Pattern storage/retrieval
- `mcp__thinking__*` - Complex reasoning
- `mcp__consult_suite_enhanced()` - Expert consultation

## ✅ CORRECT TOOL USAGE PATTERNS

1. **ALWAYS**: Grep → Read (search before reading)
2. **NEVER**: cat/head/tail/find/curl → Use tool equivalents
3. **BATCH**: Use MultiEdit for multiple changes
4. **TRACK**: Use TodoWrite for multi-step tasks
5. **FILTER**: Limit output with head -20, grep relevant

## ⚠️ YOU MUST USE THESE TOOLS
Don't just describe what you would do - ACTUALLY DO IT using the tools above!
"""


def enhance_agent_profile(file_path):
    """Enhance a single agent profile with tool awareness."""

    with open(file_path, "r") as f:
        content = f.read()

    # Skip if already enhanced
    if "YOU HAVE THESE TOOLS - USE THEM!" in content:
        print(f"  ✓ Already enhanced: {file_path.name}")
        return False

    # Find the YAML front matter end
    yaml_end = content.find("---", 3)
    if yaml_end == -1:
        print(f"  ✗ No YAML front matter: {file_path.name}")
        return False

    # Find where to insert (after the agent description paragraph)
    insert_point = yaml_end + 3

    # Look for the first major section (## heading)
    first_section = re.search(r"\n## ", content[insert_point:])
    if first_section:
        insert_point += first_section.start()
    else:
        # Insert after the first paragraph
        double_newline = content.find("\n\n", insert_point)
        if double_newline != -1:
            insert_point = double_newline

    # Insert the tool awareness section
    enhanced = (
        content[:insert_point]
        + "\n"
        + TOOL_AWARENESS_SECTION
        + "\n"
        + content[insert_point:]
    )

    # Write back
    with open(file_path, "w") as f:
        f.write(enhanced)

    print(f"  ✅ Enhanced: {file_path.name}")
    return True


def main():
    """Enhance all agent profiles."""

    agents_dir = Path("/home/opsvi/master_root/.claude/agents")

    # Skip templates and already enhanced files
    skip_patterns = ["TEMPLATE", "template", "ENHANCED"]

    enhanced_count = 0
    skipped_count = 0

    print("Enhancing agent profiles with tool awareness...")
    print("-" * 50)

    for agent_file in sorted(agents_dir.glob("*.md")):
        # Skip templates
        if any(pattern in agent_file.name for pattern in skip_patterns):
            print(f"  → Skipping: {agent_file.name}")
            skipped_count += 1
            continue

        if enhance_agent_profile(agent_file):
            enhanced_count += 1

    print("-" * 50)
    print(f"Enhanced: {enhanced_count} agents")
    print(f"Skipped: {skipped_count} files")
    print("\nAll agents now have explicit tool usage instructions!")


if __name__ == "__main__":
    main()
