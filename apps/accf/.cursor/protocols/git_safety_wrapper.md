<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"GIT SAFETY WRAPPER PROTOCOL","description":"Documentation detailing mandatory safety checks and protocols for safe file modifications in a multi-agent environment using git.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document focusing on the git safety wrapper protocol for multi-agent file modification safety. Identify and map sections based on the protocol's purpose, implementation steps, safety validation rules, session tracking, commit procedures, and enforcement. Highlight key code blocks that illustrate commands and scripts used, and ensure line numbers correspond precisely to the documented content for accurate navigation.","sections":[{"name":"Document Title","description":"Main title of the document introducing the git safety wrapper protocol.","line_start":7,"line_end":7},{"name":"Purpose","description":"Explains the mandatory safety checks before any file modification to prevent conflicts in multi-agent environments.","line_start":9,"line_end":10},{"name":"Implementation Overview","description":"Introduces the implementation details of the git safety wrapper protocol.","line_start":12,"line_end":12},{"name":"Pre-File-Operation Safety Check","description":"Describes the initial safety check commands to be run before file operations, including git status and diff commands.","line_start":14,"line_end":18},{"name":"Safety Validation Rules","description":"Lists the rules for validating safety before proceeding with file operations based on detected changes and session modifications.","line_start":20,"line_end":28},{"name":"Agent Session Tracking","description":"Details commands for creating session files and logging file modifications to track agent activity.","line_start":29,"line_end":33},{"name":"Commit Safety Protocol","description":"Specifies the commands to commit only files modified by the current agent session, ensuring safe commits.","line_start":34,"line_end":39},{"name":"Enforcement","description":"States the mandatory nature of the wrapper before any file operation with no exceptions allowed.","line_start":40,"line_end":42}],"key_elements":[{"name":"Pre-File-Operation Safety Check Code Block","description":"Shell commands to check git status and list changed files before file operations.","line":15},{"name":"Safety Validation Rules List","description":"Enumerated rules describing conditions under which file operations can proceed safely.","line":21},{"name":"Agent Session Creation Code Block","description":"Shell command to create a session file identifying the current agent session.","line":30},{"name":"File Modification Logging Code Block","description":"Shell command to log file modifications with timestamps for the current agent session.","line":32},{"name":"Commit Safety Protocol Code Block","description":"Shell commands to add and commit only files modified by the current agent session with a standardized commit message.","line":35},{"name":"Enforcement Statement","description":"Clear directive emphasizing the mandatory application of the safety wrapper before any file operation.","line":41}]}
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
