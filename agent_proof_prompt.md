# Nested Agent Spawn Proof - Clean Session Prompt

Copy and paste this entire prompt into a fresh Claude Code session with no hooks or CLAUDE.md configured:

---

## SYSTEM INSTRUCTIONS FOR ROOT ORCHESTRATOR - PROOF OF NESTED SPAWN VIA TASK TOOL

You are the root orchestrator that will prove agents can spawn other agents using the Task tool.

### Goal
Create a 2-level hierarchy: Root → 2 children → 2 grandchildren each (7 agents total)
Each agent logs its lifecycle and writes an artifact file proving execution.

### Filesystem Layout
- Base dir: `./agent_proof/`
  - `./agent_proof/logs/actions.jsonl` (append-only log file)
  - `./agent_proof/artifacts/{depth}-{agent_id}.json` (one per agent)

### Execute these steps exactly:

1. **SETUP** - Create directories and initialize root:
```bash
mkdir -p ./agent_proof/logs ./agent_proof/artifacts
```

2. **LOG ROOT START** - Write to `./agent_proof/logs/actions.jsonl`:
```json
{"ts":"2025-09-02T03:00:00Z","event":"START","depth":0,"agent_id":"root","parent_id":null,"details":"Root orchestrator started"}
```

3. **WRITE ROOT ARTIFACT** - Create `./agent_proof/artifacts/0-root.json`:
```json
{
  "agent_id": "root",
  "parent_id": null,
  "depth": 0,
  "task": "proof_of_nested_spawn",
  "started_at": "2025-09-02T03:00:00Z",
  "finished_at": "2025-09-02T03:00:10Z",
  "workspace": ".",
  "nonce": "root-001",
  "notes": "Root orchestrator spawning 2 children"
}
```

4. **LOG ROOT ARTIFACT EVENT**:
```json
{"ts":"2025-09-02T03:00:01Z","event":"WRITE_ARTIFACT","depth":0,"agent_id":"root","parent_id":null,"details":"Root artifact written"}
```

5. **SPAWN CHILDREN IN PARALLEL** - Use ONE Task tool invocation with TWO agents:

```
Task tool parameters:
- description: "Spawn child-1 and child-2"
- subagent_type: "general-purpose"
- prompt: [SEE CHILD AGENT PROMPT BELOW]
```

### CHILD AGENT PROMPT (use this exactly):

```
Execute these TWO parallel agents:

==== AGENT 1: child-1 ====
1. Append to ./agent_proof/logs/actions.jsonl:
{"ts":"2025-09-02T03:00:02Z","event":"START","depth":1,"agent_id":"child-1","parent_id":"root","details":"Child-1 started"}

2. Write ./agent_proof/artifacts/1-child-1.json:
{"agent_id":"child-1","parent_id":"root","depth":1,"task":"proof_of_nested_spawn","started_at":"2025-09-02T03:00:02Z","finished_at":"2025-09-02T03:00:05Z","workspace":".","nonce":"c1-001","notes":"Child-1 spawning grandchildren"}

3. Append to logs:
{"ts":"2025-09-02T03:00:02Z","event":"WRITE_ARTIFACT","depth":1,"agent_id":"child-1","parent_id":"root","details":"Artifact written"}
{"ts":"2025-09-02T03:00:03Z","event":"SPAWN","depth":1,"agent_id":"child-1","parent_id":"root","details":"Spawning 2 grandchildren"}

4. Use ONE Task tool to spawn BOTH child-1-g1 and child-1-g2:
Prompt: "Write these grandchildren artifacts and logs:
- child-1-g1: Append START, WRITE_ARTIFACT, END to logs; write 2-child-1-g1.json
- child-1-g2: Append START, WRITE_ARTIFACT, END to logs; write 2-child-1-g2.json"

5. Append:
{"ts":"2025-09-02T03:00:05Z","event":"END","depth":1,"agent_id":"child-1","parent_id":"root","details":"Child-1 completed"}

==== AGENT 2: child-2 ====
[Mirror exact same pattern for child-2 with child-2-g1 and child-2-g2]
```

6. **VALIDATE** after children complete:
- Count files in ./agent_proof/artifacts/ (expect 7)
- Count lines in ./agent_proof/logs/actions.jsonl (expect ~26 events)
- List all artifacts to confirm: 0-root.json, 1-child-1.json, 1-child-2.json, 2-child-1-g1.json, 2-child-1-g2.json, 2-child-2-g1.json, 2-child-2-g2.json

7. **LOG ROOT END**:
```json
{"ts":"2025-09-02T03:00:10Z","event":"END","depth":0,"agent_id":"root","parent_id":null,"details":"Root completed - all agents executed"}
```

8. **FINAL SUMMARY** - Display:
```
Nested Spawn Proof Complete:
root
├── child-1
│   ├── child-1-g1
│   └── child-1-g2
└── child-2
    ├── child-2-g1
    └── child-2-g2

Total: 7 agents executed
Artifacts: 7 files created
Events: X logged
```

### SUCCESS CRITERIA
- 7 artifact files exist with correct naming
- Each agent logged START, WRITE_ARTIFACT, and END
- Children successfully spawned grandchildren
- All operations completed without errors

BEGIN EXECUTION NOW.
