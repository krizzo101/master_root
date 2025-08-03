<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"MULTI-AGENT COORDINATION PROTOCOL","description":"Comprehensive documentation detailing the unified Git safety and change management system for multi-agent coordination, including identification, operational modules, emergency protocols, implementation phases, and enforcement.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document by focusing on major thematic sections rather than every subheading to maintain clarity and navigability. Identify and map logical high-level sections based on content themes such as protocol overview, agent identification, operational modules, emergency procedures, implementation phases, and enforcement. Capture key elements including code blocks, configuration templates, safety rules, and critical procedural instructions with precise line references. Ensure all line numbers are accurate and sections do not overlap. Provide concise, descriptive names and explanations for sections and key elements to facilitate efficient navigation and comprehension within the multi-agent coordination context.","sections":[{"name":"Protocol Overview and Status","description":"Introduces the Multi-Agent Coordination Protocol, its version, status, implementation phases, and general purpose.","line_start":7,"line_end":16},{"name":"Agent Identification System","description":"Defines the standard agent ID format, context codes, usage requirements for commits, change records, session files, and database entries.","line_start":17,"line_end":44},{"name":"Module A: Git Safety","description":"Details mandatory pre-operation checks, critical safety rules, file operation safety wrappers, and session ownership tracking to ensure safe Git operations.","line_start":45,"line_end":92},{"name":"Module B: Change Coordination","description":"Describes the active coordination dashboard, change record templates, and agent handoff protocols to manage change workflows and coordination among agents.","line_start":93,"line_end":119},{"name":"Module C: Startup Integration","description":"Outlines the mandatory startup sequence and workflow revisions to integrate Git safety and change coordination at startup.","line_start":120,"line_end":152},{"name":"Module D: Emergency Protocols","description":"Specifies conflict detection triggers and emergency response procedures to handle conflicts and emergencies during multi-agent operations.","line_start":153,"line_end":173},{"name":"Implementation Phases","description":"Defines the phased rollout plan for Git safety, coordination integration, and validation with timelines and ownership.","line_start":174,"line_end":198},{"name":"Active Agent Coordination and ACTIVE_AGENTS.yml Specification","description":"Provides the specification and example structure of the ACTIVE_AGENTS.yml file used for tracking active sessions and coordination status.","line_start":199,"line_end":229},{"name":"Validation Checkpoints","description":"Lists validation criteria for Phase 1 Git safety and integration validation to ensure protocol compliance and operational readiness.","line_start":230,"line_end":247},{"name":"Emergency Coordination Procedures","description":"Details steps to follow if conflicts occur during implementation and the emergency contact protocol format for incident reporting.","line_start":248,"line_end":269},{"name":"Protocol Enforcement","description":"States the mandatory nature of the protocol, risks of violations, and activation status to emphasize compliance.","line_start":270,"line_end":279}],"key_elements":[{"name":"Agent ID Standard Format Code Block","description":"YAML code block defining the standard agent ID format, context codes, and example agent IDs.","line":21},{"name":"Mandatory Pre-Operation Checks Script","description":"Bash script snippet listing commands to check Git status and diffs before any file modification.","line":49},{"name":"Critical Safety Rules List","description":"Enumerated list of essential safety rules for Git operations to prevent unauthorized or unsafe commits.","line":52},{"name":"File Operation Safety Wrapper Function","description":"Bash function 'safety_check' to validate file modifications ensuring no unauthorized changes before operations.","line":59},{"name":"Session Ownership Tracking YAML Example","description":"YAML formatted example showing session log structure for tracking files modified during an agent's session.","line":69},{"name":"Change Record Template Code Block","description":"YAML template defining the structure of change records including status, agent ID, priority, and coordination notes.","line":102},{"name":"Startup Sequence YAML Protocol","description":"YAML block outlining the mandatory startup sequence steps including git safety checks and session initialization.","line":124},{"name":"Emergency Protocol Triggers YAML","description":"YAML snippet listing triggers for conflict detection and required emergency actions.","line":157},{"name":"ACTIVE_AGENTS.yml Specification Code Block","description":"YAML example showing the structure of ACTIVE_AGENTS.yml including active sessions, statuses, and claimed files.","line":202},{"name":"Validation Checkpoints Lists","description":"Checklist items for Phase 1 Git safety and integration validation to verify protocol adherence.","line":231},{"name":"Emergency Contact Protocol YAML","description":"YAML format defining the emergency incident report structure including incident ID, agents involved, and status.","line":258}]}
-->
<!-- FILE_MAP_END -->

# MULTI-AGENT COORDINATION PROTOCOL
*Unified Git Safety + Change Management System*

## 🎯 **PROTOCOL STATUS**
- **Version**: 1.0
- **Status**: ACTIVE
- **Implementation**: Phase 1 (Git Safety) + Phase 2 (Integration)
- **Last Updated**: 2025-06-28T07:45:00Z

---

## 🆔 **AGENT IDENTIFICATION SYSTEM**

### **Standard Format**:
```yaml
agent_id: "AGENT-{context}-{date}-{sequence}"

context_codes:
  STARTUP: "Initial system activation and assessment"
  TASK: "Specific assigned work completion"
  EMERGENCY: "Crisis response and conflict resolution"
  VALIDATION: "Testing and verification activities"
  HANDOFF: "Session transfer and coordination"

examples:
  - "AGENT-STARTUP-2025-06-28-001"
  - "AGENT-TASK-2025-06-28-002"
  - "AGENT-EMERGENCY-2025-06-28-003"
```

### **Usage Requirements**:
- **Git Commits**: `[{agent_id}] {action}: {description}`
- **Change Records**: `agent_id: {agent_id}`
- **Session Files**: `{agent_id}-session.log`
- **Database Entries**: `agent_id: {agent_id}`

---

## 🛡️ **MODULE A: GIT SAFETY**
*Owner: AGENT-STARTUP-2025-06-28*

### **MANDATORY PRE-OPERATION CHECKS**:
```bash
# Before ANY file modification
git status --porcelain
git diff --name-only
# Verify only agent's own changes present
```

### **CRITICAL SAFETY RULES**:
1. ❌ **NEVER auto-commit** without explicit verification
2. ✅ **ALWAYS check git status** before file modifications
3. ❌ **NEVER commit changes made by other agents**
4. ✅ **ALWAYS use [AGENT-ID] format** in commits
5. ✅ **ALWAYS track file ownership** in session log

### **FILE OPERATION SAFETY WRAPPER**:
```bash
# Required before edit_file, search_replace, delete_file
safety_check() {
  local file=$1
  git status --porcelain "$file"
  git diff "$file"
  # Validate: file not modified by other agents
  # If other agent changes detected: STOP and coordinate
}
```

### **SESSION OWNERSHIP TRACKING**:
- **Session Log**: `.cursor/{agent_id}-session.log`
- **Track**: All files modified during session
- **Validate**: Only commit files in session log
- **Format**:
  ```yaml
  session: "AGENT-STARTUP-2025-06-28-001"
  start_time: "2025-06-28T07:45:00Z"
  files_modified:
    - file: ".cursor/workflows/startup.yml"
      action: "modified"
      lines: "10-25"
    - file: ".cursor/protocols/new-protocol.md"
      action: "created"
  ```

---

## 📊 **MODULE B: CHANGE COORDINATION**
*Owner: Change Management Agent*

### **ACTIVE COORDINATION DASHBOARD**:
- **File**: `.cursor/ACTIVE_CHANGES.md`
- **Purpose**: Real-time work coordination
- **Update**: Mandatory for all agents

### **CHANGE RECORD TEMPLATES**:
```yaml
change_id: "CHANGE-{date}-{sequence}"
status: "IN_PROGRESS" # PLANNED | IN_PROGRESS | COMPLETED | ABANDONED
agent_id: "{agent_identifier}"
priority: "HIGH" # LOW | MEDIUM | HIGH | CRITICAL
files_affected: []
coordination_notes: "Instructions for other agents"
completion_criteria: "How to know it's done"
```

### **AGENT HANDOFF PROTOCOLS**:
1. **Session End**: Update all change statuses
2. **Session Start**: Read active changes before modifications
3. **Conflict Detection**: Coordinate via dashboard updates
4. **Emergency**: Document state and pause operations

---

## 🚀 **MODULE C: STARTUP INTEGRATION**
*Joint Ownership*

### **MANDATORY STARTUP SEQUENCE**:
```yaml
startup_protocol:
  1. git_safety_check:
     command: "git status --porcelain"
     action: "Document findings, detect conflicts"

  2. active_agents_check:
     file: ".cursor/ACTIVE_AGENTS.yml"
     action: "Check for concurrent sessions"

  3. change_coordination:
     file: ".cursor/ACTIVE_CHANGES.md"
     action: "Load ongoing work context"

  4. session_initialization:
     create: "{agent_id}-session.log"
     register: "ACTIVE_AGENTS.yml"

  5. safety_validation:
     verify: "No conflicts detected"
     proceed: "Begin coordinated work"
```

### **STARTUP WORKFLOW REVISIONS**:
- ❌ **REMOVED**: "COMMIT before AND AFTER every significant change"
- ✅ **ADDED**: "CHECK git status, COORDINATE via dashboard, ONLY commit verified changes"

---

## 🆘 **MODULE D: EMERGENCY PROTOCOLS**
*Joint Responsibility*

### **CONFLICT DETECTION**:
```yaml
triggers:
  - git_merge_conflicts: "automatic_pause"
  - simultaneous_file_edits: "coordination_required"
  - abandoned_changes: "handoff_protocol"
  - session_overlap: "agent_coordination"
```

### **EMERGENCY RESPONSE**:
1. **IMMEDIATE**: Stop all file operations
2. **BACKUP**: Create emergency branch
3. **DOCUMENT**: Record conflict details
4. **COORDINATE**: Update dashboard with emergency status
5. **RESOLVE**: Follow conflict resolution protocol

---

## 📋 **IMPLEMENTATION PHASES**

### **PHASE 1: GIT SAFETY** (IMMEDIATE)
- ✅ Remove auto-commit from startup
- ✅ Add git status safety checks
- ✅ Deploy [AGENT-ID] commit format
- ✅ Create session ownership tracking
- **Owner**: AGENT-STARTUP-2025-06-28

### **PHASE 2: COORDINATION INTEGRATION** (24 hours)
- 🔄 Create ACTIVE_AGENTS.yml system
- 🔄 Integrate change dashboard with git safety
- 🔄 Test multi-agent scenarios
- 🔄 Deploy unified startup protocol
- **Owner**: Joint

### **PHASE 3: VALIDATION** (48 hours)
- 🔄 Comprehensive testing
- 🔄 Emergency protocol validation
- 🔄 Performance optimization
- 🔄 Documentation completion
- **Owner**: Joint

---

## 📊 **ACTIVE AGENT COORDINATION**

### **ACTIVE_AGENTS.yml Specification**:
```yaml
# .cursor/ACTIVE_AGENTS.yml
coordination_version: "1.0"
last_updated: "2025-06-28T07:45:00Z"

active_sessions:
  - agent_id: "AGENT-STARTUP-2025-06-28-001"
    status: "ACTIVE"
    start_time: "2025-06-28T07:30:00Z"
    files_claimed:
      - ".cursor/workflows/"
      - ".cursor/protocols/multi-agent-git-protocol.md"
    branch: "main"
    session_log: ".cursor/AGENT-STARTUP-2025-06-28-001-session.log"

  - agent_id: "AGENT-TASK-2025-06-28-002"
    status: "STANDBY"
    waiting_for: "git_safety_implementation"
    files_claimed:
      - ".cursor/ACTIVE_CHANGES.md"
      - ".cursor/protocols/multi-agent-coordination-protocol.md"

conflict_zones: []
emergency_status: "GREEN"
```

---

## ✅ **VALIDATION CHECKPOINTS**

### **Phase 1 Git Safety Validation**:
- [ ] Auto-commit removed from startup workflow
- [ ] Git status checks implemented before file operations
- [ ] [AGENT-ID] format deployed in all commits
- [ ] Session ownership tracking operational
- [ ] No git conflicts during implementation

### **Integration Validation**:
- [ ] ACTIVE_AGENTS.yml system operational
- [ ] Change dashboard coordination working
- [ ] Multi-agent conflict prevention active
- [ ] Emergency protocols tested
- [ ] Performance impact acceptable

---

## 🚨 **EMERGENCY COORDINATION**

### **If Conflicts Occur During Implementation**:
1. **AGENT-STARTUP**: Immediately update ACTIVE_AGENTS.yml with emergency status
2. **Change Management Agent**: Pause all modifications, document conflict
3. **Both**: Coordinate via `.cursor/EMERGENCY_COORDINATION.md`
4. **Resolution**: Joint debugging and conflict resolution
5. **Recovery**: Validate system integrity before proceeding

### **Emergency Contact Protocol**:
```yaml
emergency_file: ".cursor/EMERGENCY_COORDINATION.md"
format:
  incident_id: "EMERGENCY-{timestamp}"
  agents_involved: []
  conflict_description: ""
  proposed_resolution: ""
  status: "ACTIVE|RESOLVED"
```

---

## 🎯 **ENFORCEMENT**

This protocol is **MANDATORY** for all agent operations. Violations risk:
- Data loss and corruption
- Operational conflicts
- System instability
- Development chaos

**ACTIVATION**: This protocol is ACTIVE immediately and supersedes all previous coordination directives.

---

*Multi-Agent Coordination Protocol v1.0 - Ensuring Safe, Coordinated Autonomous Operations*
