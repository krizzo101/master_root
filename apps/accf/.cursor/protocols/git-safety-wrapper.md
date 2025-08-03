<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"GIT SAFETY WRAPPER PROTOCOL","description":"Documentation detailing mandatory safety checks and protocols for file modifications to prevent multi-agent conflicts using git.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document by identifying its purpose as a safety protocol for git file operations, then map the structure into logical sections based on headings and content themes. Capture code blocks and key procedural rules as important elements. Ensure all line numbers are accurate and sections do not overlap. Provide clear, descriptive section names and descriptions to facilitate navigation and comprehension.","sections":[{"name":"Title and Purpose","description":"Introduces the Git Safety Wrapper Protocol and explains its mandatory purpose to prevent multi-agent conflicts before file modifications.","line_start":7,"line_end":11},{"name":"Implementation Overview","description":"Details the implementation of the safety wrapper including pre-file-operation checks, validation rules, and session tracking.","line_start":12,"line_end":32},{"name":"Pre-File-Operation Safety Check","description":"Contains bash commands to check git status and differences before file operations to ensure safety.","line_start":13,"line_end":17},{"name":"Safety Validation Rules","description":"Lists the rules to validate safety based on file changes and session modifications to prevent conflicts.","line_start":18,"line_end":26},{"name":"Agent Session Tracking","description":"Describes how to create a session file and log file modifications for tracking agent activity.","line_start":27,"line_end":32},{"name":"Commit Safety Protocol","description":"Explains the process to commit only files modified by the current agent session using git commands.","line_start":33,"line_end":38},{"name":"Enforcement Statement","description":"Declares the mandatory nature of the wrapper before any file operation with no exceptions allowed.","line_start":39,"line_end":41}],"key_elements":[{"name":"Pre-File-Operation Safety Check Code Block","description":"Bash commands to check git status and list changed files before performing file operations.","line":14},{"name":"Safety Validation Rules List","description":"Enumerated rules that define when it is safe to proceed with file operations based on git changes and session ownership.","line":18},{"name":"Agent Session Tracking Code Block","description":"Bash commands to create a session file and log modifications for tracking agent activity.","line":28},{"name":"Commit Safety Protocol Code Block","description":"Bash commands to add and commit only files modified by the current agent session to ensure safe commits.","line":34},{"name":"Enforcement Declaration","description":"A clear statement emphasizing the mandatory enforcement of the safety wrapper protocol.","line":40}]}
-->
<!-- FILE_MAP_END -->

# GIT SAFETY WRAPPER PROTOCOL

## PURPOSE
Mandatory safety checks before ANY file modification to prevent multi-agent conflicts.

## IMPLEMENTATION

### Pre-File-Operation Safety Check
```bash
# MANDATORY before edit_file, search_replace, delete_file
git status --porcelain
git diff --name-only
```

### Safety Validation Rules
1. **If no changes**: Proceed with operation
2. **If changes in target file**:
   - Check if I modified it in current session
   - If YES: Safe to proceed
   - If NO: STOP - another agent's work
3. **If changes in other files**: Document but proceed with target file

### Agent Session Tracking
```bash
# Create session file
echo "AGENT-{session-id}" > .cursor/current-agent-session

# Log file modifications
echo "$(date): modified {filename}" >> .cursor/AGENT-{session-id}-modifications.log
```

### Commit Safety Protocol
```bash
# Only commit files I modified
git add {files-from-my-session-log}
git commit -m "[AGENT-{session-id}] {action}: {description}"
```

## ENFORCEMENT
This wrapper is MANDATORY before any file operation. NO EXCEPTIONS.
