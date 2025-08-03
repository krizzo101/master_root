<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"MULTI-AGENT COORDINATION PROTOCOL","description":"Comprehensive documentation for a unified Git safety and multi-agent change management system, detailing protocols, modules, implementation phases, and emergency procedures for coordinated autonomous operations.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document to identify major thematic sections reflecting the multi-agent coordination protocol structure. Group related headings into broader sections to maintain manageable navigation. Capture key elements such as code blocks, YAML configurations, safety rules, and emergency protocols. Ensure line numbers are precise and sections do not overlap. Provide clear, descriptive section names and highlight critical navigation points to facilitate understanding and usage of the protocol.","sections":[{"name":"Protocol Overview and Status","description":"Introduces the multi-agent coordination protocol, its purpose, version, status, and implementation phases.","line_start":7,"line_end":16},{"name":"Agent Identification System","description":"Defines the standard format for agent IDs, context codes, usage requirements across commits, change records, session files, and database entries.","line_start":17,"line_end":44},{"name":"Module A: Git Safety","description":"Details mandatory pre-operation checks, critical safety rules, file operation safety wrappers, and session ownership tracking to ensure safe Git operations by agents.","line_start":45,"line_end":92},{"name":"Module B: Change Coordination","description":"Describes the active coordination dashboard, change record templates, and agent handoff protocols for managing multi-agent change workflows.","line_start":93,"line_end":119},{"name":"Module C: Startup Integration","description":"Specifies the mandatory startup sequence and workflow revisions to integrate agents safely into the coordination system.","line_start":120,"line_end":152},{"name":"Module D: Emergency Protocols","description":"Outlines conflict detection triggers and emergency response procedures to handle conflicts and crises during multi-agent operations.","line_start":153,"line_end":173},{"name":"Implementation Phases","description":"Breaks down the protocol deployment into three phases: Git safety, coordination integration, and validation, with timelines and ownership.","line_start":174,"line_end":198},{"name":"Active Agent Coordination and ACTIVE_AGENTS.yml Specification","description":"Defines the ACTIVE_AGENTS.yml file structure, active sessions, conflict zones, and emergency status for real-time agent coordination.","line_start":199,"line_end":229},{"name":"Validation Checkpoints","description":"Lists validation criteria for Phase 1 Git safety and integration validation to ensure protocol compliance and operational readiness.","line_start":230,"line_end":247},{"name":"Emergency Coordination Procedures","description":"Details steps to follow if conflicts occur during implementation and the emergency contact protocol format for incident documentation.","line_start":248,"line_end":269},{"name":"Protocol Enforcement","description":"States the mandatory nature of the protocol, risks of violations, and activation status to ensure adherence by all agents.","line_start":270,"line_end":281}],"key_elements":[{"name":"Agent ID Standard Format YAML","description":"YAML code block defining the agent ID format, context codes, and examples for consistent agent identification.","line":21},{"name":"Git Safety Pre-Operation Checks Bash Script","description":"Bash commands to verify git status and differences before any file modification to ensure safety.","line":49},{"name":"Critical Safety Rules List","description":"Enumerated safety rules emphasizing verification steps and commit standards to prevent unsafe operations.","line":54},{"name":"File Operation Safety Wrapper Bash Function","description":"Bash function 'safety_check' to validate file modifications and prevent unauthorized changes by other agents.","line":60},{"name":"Session Ownership Tracking YAML Example","description":"YAML snippet illustrating session log format tracking files modified during an agent's session.","line":72},{"name":"Change Record Template YAML","description":"YAML template for recording change details including status, agent ID, priority, affected files, and notes.","line":102},{"name":"Startup Sequence YAML","description":"YAML block outlining mandatory startup steps including git safety checks, active agent validation, and session initialization.","line":124},{"name":"Emergency Protocol Triggers YAML","description":"YAML list of triggers that initiate emergency protocols such as merge conflicts and simultaneous edits.","line":157},{"name":"ACTIVE_AGENTS.yml Specification YAML","description":"YAML configuration detailing active agent sessions, claimed files, conflict zones, and emergency status for coordination.","line":202},{"name":"Validation Checklists","description":"Bullet lists enumerating criteria for Git safety and integration validation phases to ensure protocol adherence.","line":231},{"name":"Emergency Contact Protocol YAML","description":"YAML format for documenting emergency incidents including incident ID, agents involved, conflict description, and status.","line":258}]}
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
