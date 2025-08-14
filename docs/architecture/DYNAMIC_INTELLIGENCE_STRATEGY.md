# Dynamic Project Intelligence Strategy

## Core Principle: Think First, Check Intelligence Second

Instead of keyword triggers, the agent should ask itself: **"What am I about to do, and would intelligence help?"**

## 1. Intent-Based Recognition (Not Keywords)

### The Agent's Internal Checklist

Before ANY action, the agent evaluates:

```python
def should_use_intelligence(self, planned_action):
    """
    Agent's internal decision process - runs automatically
    """
    
    # 1. Am I about to look for something?
    if self.planning_to(['search', 'grep', 'find', 'locate', 'look up']):
        return True, "symbol_index"  # Use intelligence instead
    
    # 2. Am I about to read multiple files to understand something?
    if self.need_to_understand(['relationship', 'flow', 'structure', 'how things connect']):
        return True, "architecture"
    
    # 3. Am I about to make changes to code?
    if self.planning_to(['edit', 'modify', 'add code', 'implement']):
        return True, "similar_patterns"  # Learn from existing code first
    
    # 4. Am I trying to understand an error or problem?
    if self.analyzing(['exception', 'failure', 'issue', 'problem']):
        return True, "dependencies"  # Check relationships
    
    # 5. Am I about to create something new?
    if self.planning_to(['create', 'new file', 'new class', 'new function']):
        return True, "patterns"  # Don't reinvent the wheel
    
    # 6. Do I need context about the codebase?
    if self.need_context_for_any_reason():
        return True, "general"
    
    return False, None
```

## 2. Proactive Self-Triggering Patterns

### Pattern A: Pre-Action Intelligence Check
**Before the agent acts, it asks itself:**

```
Planned Action: "I need to find where user authentication happens"
↓
Self-Check: "I'm about to search. Intelligence would be faster."
↓
Use Intelligence First: intel.find("authentication")
↓
Then Act: Edit the specific file found
```

### Pattern B: Context Building
**When starting any task:**

```
Task Received: "The app is slow"
↓
Self-Check: "I need to understand the app structure first"
↓
Automatic Intelligence Load:
- intel.architecture()  # Get overview
- intel.stats()  # Understand scale
- intel.find("performance")  # Find related code
↓
Then Investigate: With full context loaded
```

### Pattern C: Learning Before Doing
**Before writing code:**

```
About to: Write a new validator function
↓
Self-Check: "How do validators work in this codebase?"
↓
Automatic Pattern Search:
- intel.find("validator")  # Find existing validators
- Review top 3 implementations
- Extract patterns (naming, structure, location)
↓
Then Write: Consistent with existing patterns
```

## 3. Reasoning-Triggered Intelligence

### The agent recognizes its own thought patterns:

```python
class AgentReasoning:
    def process_thought(self, thought):
        """
        Monitor own reasoning for intelligence opportunities
        """
        
        # Detect when I'm uncertain
        if "I need to check" in thought:
            self.use_intelligence_first()
        
        # Detect when I'm guessing
        if "probably in" in thought or "might be" in thought:
            self.stop_guessing_use_intelligence()
        
        # Detect when I'm doing manual work
        if "let me search through" in thought:
            self.use_intelligence_instead()
        
        # Detect when I need context
        if "I should understand" in thought:
            self.load_architecture_context()
        
        # Detect exploration needs
        if "let me see what's in" in thought:
            self.use_file_stats_first()
```

## 4. Task Decomposition Triggers

### Break down tasks to recognize intelligence needs:

```python
def decompose_task(task):
    """
    Decompose any task to identify intelligence needs
    """
    steps = []
    
    # Every task involves:
    # 1. Understanding what exists (→ use intelligence)
    # 2. Finding the right place (→ use intelligence)  
    # 3. Checking patterns (→ use intelligence)
    # 4. Making changes
    # 5. Verifying impact (→ use intelligence)
    
    for step in task.get_steps():
        if step.requires_knowledge():
            step.prepend(UseIntelligence())
        if step.involves_search():
            step.replace_with(IntelligenceQuery())
        if step.needs_context():
            step.add_context(LoadIntelligence())
    
    return steps
```

## 5. Default-On Intelligence

### Instead of "when to use", make it "when NOT to use":

```python
# Current approach (wrong):
if keyword in user_input:
    use_intelligence()

# New approach (right):
intelligence_data = load_intelligence()  # Always load

# Only skip intelligence if:
if task.is_trivial() and task.affects_single_line():
    # Maybe skip intelligence
else:
    # Always use intelligence as primary source
```

## 6. Continuous Intelligence Awareness

### The agent maintains persistent awareness:

```python
class IntelligenceAwareAgent:
    def __init__(self):
        # Load intelligence on startup
        self.intel = ProjectIntelligence()
        self.context_cache = {}
        
    def before_every_action(self, action):
        """
        Run before EVERY action, not just on keywords
        """
        # What files might this action affect?
        affected = self.predict_affected_files(action)
        
        # Pre-load their context
        for file in affected:
            if file not in self.context_cache:
                self.context_cache[file] = self.intel.get_context(file)
        
        # What patterns apply?
        patterns = self.intel.find_patterns(action.type)
        
        # Apply intelligence to action
        action.enhance_with(self.context_cache, patterns)
        
        return action
```

## 7. Natural Language Independence

### Understand intent regardless of phrasing:

```python
# All of these should trigger intelligence:
"Make the API faster"  → intel.find("api", "performance")
"Something's wrong with login"  → intel.find("login", "auth")  
"Add user preferences"  → intel.find("preferences", "settings", "user")
"Why is this happening?"  → intel.dependencies(current_file)
"Set up testing"  → intel.find("test", "spec", "mock")

# The agent detects the NEED, not the WORDS:
need_to_find_code → use intelligence
need_to_understand → use intelligence  
need_to_modify → use intelligence
need_to_create → use intelligence
need_to_debug → use intelligence
```

## 8. Self-Correction Triggers

### The agent recognizes when it should have used intelligence:

```python
def self_monitor(self):
    """
    Detect inefficient patterns and self-correct
    """
    
    if self.last_action_was("grep"):
        self.note("Should have used symbol_index instead")
        self.redo_with_intelligence()
    
    if self.read_files_count > 3:
        self.note("Should have used architecture overview")
        self.load_intelligence_context()
    
    if self.search_iterations > 1:
        self.note("Intelligence would have found this immediately")
        self.switch_to_intelligence()
    
    if self.editing_without_context:
        self.pause()
        self.load_pattern_examples()
        self.resume_with_context()
```

## 9. Implementation Rules

### Updated CLAUDE.md directives:

```markdown
## PROJECT INTELLIGENCE - DEFAULT BEHAVIOR

### USE INTELLIGENCE BY DEFAULT
- Load project intelligence at session start
- Check intelligence BEFORE any file operation
- Update cache when switching task contexts
- Refresh if older than 24 hours

### THINK → CHECK → ACT Pattern
1. THINK: What do I need to do?
2. CHECK: What does intelligence tell me?
3. ACT: Proceed with intelligence-informed action

### Self-Triggering Rules
- If you're about to search → Use symbol_index first
- If you're about to read files → Check architecture first
- If you're about to edit → Find patterns first
- If you're debugging → Check dependencies first
- If you're creating → Study existing examples first

### Intent Recognition (Not Keywords)
- Detect the NEED behind the request
- Use intelligence for ANY non-trivial task
- Default to using intelligence unless explicitly unnecessary

### Performance Monitoring
- If an action takes >1 second, consider if intelligence would help
- If you read >3 files, you should have used intelligence
- If you grep/search manually, you should have used indices
```

## 10. Dynamic Decision Tree

```
Task Received
    ↓
Is it a single-line change to a known file?
    ├─ Yes → Maybe skip intelligence
    └─ No → USE INTELLIGENCE
            ↓
        What is my intent?
            ├─ Understand → Load architecture
            ├─ Find → Use symbol/file index
            ├─ Fix → Check dependencies
            ├─ Create → Find patterns
            ├─ Review → Load context
            └─ Unknown → Load everything relevant
```

## Benefits of This Approach

1. **No keyword memorization** - Users speak naturally
2. **Proactive usage** - Agent self-triggers based on intent
3. **Self-correcting** - Recognizes when it should have used intelligence
4. **Context-aware** - Maintains persistent awareness
5. **Performance-optimized** - Always chooses fastest path
6. **Pattern-learning** - Continuously improves from intelligence data

## Example: Dynamic Recognition in Action

**User says:** "The app crashes when users log out"

**Agent's internal process:**
```
1. Intent detected: Debug a crash
2. Automatically loads:
   - intel.find("logout")  # Find logout code
   - intel.find("session")  # Related functionality
   - intel.dependencies("auth/logout.py")  # Check dependencies
3. Identifies 3 likely problem files
4. Reads only those 3 files (not searching blindly)
5. Finds the issue faster with targeted investigation
```

No keywords needed - the agent recognized "debug intent" from context.