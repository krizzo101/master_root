---
description: Quick onboarding for the Project Intelligence system
allowed-tools: Read, Bash, Grep
---

## 🧠 Project Intelligence Quick Start

You're working with **Project Intelligence** - a high-performance codebase analysis system that creates byte-offset indexed data for instant O(1) lookups.

### ⚡ Essential Commands

**1. Generate Project Intelligence**
```bash
# Standard generation (run in target directory)
project-intelligence full-package
# This auto-overwrites existing data - no cleanup needed
```

**2. Read Intelligence Data**
```bash
# ALWAYS use the reader script - NEVER read JSONL directly!
python /home/opsvi/master_root/scripts/proj_intel_reader.py --help
```

### 📂 Key Files
- `.proj-intel/project_analysis.jsonl` - Main data (NEVER read directly!)
- `.proj-intel/reverse_index.json` - O(1) path→data mapping
- `.proj-intel/symbol_index.json` - O(1) symbol→location

### ⚠️ CRITICAL Rules
1. **NEVER read project_analysis.jsonl directly** - Use proj_intel_reader.py
2. **ALWAYS check for .proj-intel/ directory** before using
3. **Regenerate after code changes** - Not automated yet

### 🎯 Common Tasks
```bash
# Understand project structure
python /home/opsvi/master_root/scripts/proj_intel_reader.py --action file-elements --format summary

# Find agents/classes
python /home/opsvi/master_root/scripts/proj_intel_reader.py --action agents --format summary

# Read specific file data
python /home/opsvi/master_root/scripts/proj_intel_reader.py --action read-by-path --path "src/main.py"
```
