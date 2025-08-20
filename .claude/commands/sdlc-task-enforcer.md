# SDLC Task Execution Enforcement

## Problem
Tasks from planning phase are created but not followed sequentially.

## Solution: Sequential Task Execution Protocol

### 1. Task State Machine
Each task MUST go through these states in order:
```
pending → in_progress → testing → completed
```

### 2. Enforcement Rules

```python
class TaskEnforcer:
    """Enforce sequential task execution."""
    
    def start_task(self, task_id: str):
        # Rule 1: Can only have ONE task in_progress at a time
        current_in_progress = self.get_tasks_by_status("in_progress")
        if current_in_progress:
            raise Exception(f"Must complete {current_in_progress[0]} before starting {task_id}")
        
        # Rule 2: Must complete dependencies first
        deps = self.get_dependencies(task_id)
        for dep in deps:
            if self.get_status(dep) != "completed":
                raise Exception(f"Must complete {dep} before starting {task_id}")
        
        # Rule 3: Must be next in sequence (unless deps allow parallel)
        if not self.can_start(task_id):
            next_task = self.get_next_task()
            raise Exception(f"Must start {next_task} before {task_id}")
        
        # Mark as in_progress
        self.update_status(task_id, "in_progress")
        
    def complete_task(self, task_id: str):
        # Rule 4: Must have test evidence
        if not self.has_test_evidence(task_id):
            raise Exception(f"Cannot complete {task_id} without test evidence")
        
        # Rule 5: Must meet acceptance criteria
        if not self.meets_criteria(task_id):
            raise Exception(f"Cannot complete {task_id} - acceptance criteria not met")
        
        self.update_status(task_id, "completed")
```

### 3. Implementation Protocol

```bash
# For EACH task in plan:

# Step 1: Start task
TodoWrite(todos=[{"id": "SETUP-1", "status": "in_progress", ...}])

# Step 2: Do the work
# - Write test first (if code task)
# - Implement feature
# - Verify locally

# Step 3: Show evidence
git diff --stat  # Show what changed
pytest tests/test_feature.py  # Run test

# Step 4: Complete task
TodoWrite(todos=[{"id": "SETUP-1", "status": "completed", ...}])

# Step 5: Commit
git add -A
git commit -m "feat(SETUP-1): implement project structure"

# ONLY THEN proceed to next task
```

### 4. Batch Operations Ban

```python
# ❌ BANNED - Completing multiple tasks at once:
TodoWrite(todos=[
    {"id": "SETUP-1", "status": "completed"},
    {"id": "SETUP-2", "status": "completed"},
    {"id": "SETUP-3", "status": "completed"},
])

# ✅ REQUIRED - One at a time:
TodoWrite(todos=[{"id": "SETUP-1", "status": "in_progress"}])
# ... do work ...
TodoWrite(todos=[{"id": "SETUP-1", "status": "completed"}])
# ... then next ...
TodoWrite(todos=[{"id": "SETUP-2", "status": "in_progress"}])
```

### 5. Shortcut Detection

```python
def detect_shortcuts(commits: List[str]) -> List[str]:
    """Detect when shortcuts were taken."""
    violations = []
    
    # Check 1: Large commits (>20 files changed)
    for commit in commits:
        files_changed = get_files_changed(commit)
        if len(files_changed) > 20:
            violations.append(f"Commit {commit}: Changed {len(files_changed)} files (likely bulk generation)")
    
    # Check 2: No test commits before implementation
    for task in tasks:
        test_commit = find_commit_with_pattern(f"test.*{task}")
        impl_commit = find_commit_with_pattern(f"feat.*{task}")
        if impl_commit and not test_commit:
            violations.append(f"Task {task}: Implementation without test")
    
    # Check 3: All tasks completed in single session
    completion_times = [get_completion_time(t) for t in tasks]
    if max(completion_times) - min(completion_times) < timedelta(hours=1):
        violations.append("All tasks completed too quickly - likely not followed")
    
    return violations
```

### 6. Usage Example

```python
# Correct task execution flow:

# 1. Convert plan to tasks
tasks = parse_planning_document("docs/3-planning.md")
TodoWrite(todos=tasks)

# 2. Work through sequentially
for task in tasks:
    # Start
    print(f"Starting task: {task['id']}")
    TodoWrite(todos=[{**task, "status": "in_progress"}])
    
    # Work
    if task['id'].startswith('TEST'):
        # Write test first
        Write(file_path=f"tests/test_{task['id']}.py", content="...")
        Bash("pytest tests/test_{task['id']}.py")
    
    # Complete
    TodoWrite(todos=[{**task, "status": "completed"}])
    
    # Commit
    Bash(f"git add -A && git commit -m 'feat({task['id']}): {task['content']}'")
    
    # Record in artifact
    update_artifact("development-complete.json", task['id'])
```