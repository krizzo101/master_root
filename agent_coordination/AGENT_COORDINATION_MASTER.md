# AGENT COORDINATION MASTER INSTRUCTIONS

## UNIVERSAL PROMPT FOR ALL AGENTS

**Copy and paste this exact prompt to all 3 agents:**

---

You are participating in a coordinated 3-agent development effort to build ExecutionPlan functionality for the agent-orchestrator system.

**Your mission**: Find and execute YOUR specific instructions based on your Agent ID.

### STEP 1: IDENTIFY YOUR AGENT NUMBER
Based on your session ID, identify which agent you are:

- **Agent 1**: Session ID `754c498a-aa2e-4e24-b50b-b9add5bb9c99` (Functionality Validator)
- **Agent 2**: Session ID `73e9afda-d056-40b8-917f-9c1845706830` (Gap Analysis Engineer)
- **Agent 3**: Session ID `93abe5ee-145c-4d5f-812f-fd36bc4f8b34` (Implementation Coordinator)

### STEP 2: READ YOUR SPECIFIC INSTRUCTIONS
Navigate to `/home/opsvi/master_root/agent_coordination/` and read YOUR instruction file:

```bash
cd /home/opsvi/master_root/agent_coordination
ls -la  # You should see agent_1_instructions.md, agent_2_instructions.md, agent_3_instructions.md

# Read YOUR specific instructions based on your Agent ID:
cat agent_1_instructions.md  # If you are Agent 1
cat agent_2_instructions.md  # If you are Agent 2
cat agent_3_instructions.md  # If you are Agent 3
```

### STEP 3: EXECUTE YOUR MISSION
Follow the detailed instructions in your specific file. Your instructions include:
- Your specific role and mission
- Parallel execution strategy (you can start immediately)
- Detailed execution plan with deliverables
- Communication protocols with other agents
- Success criteria and validation requirements

### STEP 4: COORDINATION AWARENESS
This is a **parallel execution strategy**:
- **All 3 agents start immediately** - don't wait for others to finish
- **Agent 1**: Test current functionality and publish findings for others
- **Agent 2**: Analyze gaps and create implementation roadmap
- **Agent 3**: Prepare infrastructure and implement based on Agent 2's roadmap

### CRITICAL SUCCESS FACTORS
- **No overclaiming**: Only claim something works if you can demonstrate it
- **Evidence-based**: Every deliverable needs working examples and tests
- **Coordination**: Share your findings with other agents at specified checkpoints
- **Use the orchestrator**: Leverage current working orchestrator capabilities

### FINAL GOAL
Build a working ExecutionPlan system that can coordinate its own development, proving the self-orchestrating concept works.

**NOW GO READ YOUR SPECIFIC INSTRUCTIONS AND BEGIN EXECUTION!**

---

## COORDINATION OVERVIEW (For Reference)

### AGENT ROLES SUMMARY
- **Agent 1** (754c498a): Test what actually works in current orchestrator
- **Agent 2** (73e9afda): Analyze gaps and create realistic implementation plan
- **Agent 3** (93abe5ee): Use working orchestrator to implement missing features

### COMMUNICATION CHECKPOINTS
- **Hour 1**: Agent 1 shares preliminary test results
- **Hour 2**: Agent 2 shares validated implementation roadmap
- **Hour 3+**: Coordinated implementation using working orchestrator

### SUCCESS METRICS
- Working ExecutionPlan system built on validated foundation
- Self-improvement demonstration (orchestrator coordinating its own enhancement)
- All features tested and validated with working examples
- Documentation updated to match implementation reality

**The coordination files are located in `/home/opsvi/master_root/agent_coordination/`**
