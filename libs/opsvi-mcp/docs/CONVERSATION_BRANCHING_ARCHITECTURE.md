# Conversation Branching & Aggregation Architecture

## Critical Findings on Claude Code Conversation Management

### Executive Summary

When agents resume conversations in headless mode, they create **independent branches** that don't merge back. This requires explicit aggregation strategies for multi-agent knowledge synthesis.

---

## 1. Core Behavior: Conversation Branching

### 1.1 What Actually Happens

When multiple agents resume the same parent conversation:

```
Parent Conversation (Session A)
    ├── Agent 1 resumes → Creates Session B (has A's history + Agent 1's additions)
    ├── Agent 2 resumes → Creates Session C (has A's history + Agent 2's additions)
    └── Agent 3 resumes → Creates Session D (has A's history + Agent 3's additions)
```

**Result:** 4 separate conversations (1 parent + 3 branches)

### 1.2 Key Properties

1. **Parent remains unmodified** - Original conversation is never changed
2. **Each branch is independent** - No cross-contamination
3. **Full history inherited** - Each branch has complete parent context
4. **One-way inheritance** - Changes don't flow back to parent
5. **No automatic merging** - Branches remain separate forever

### 1.3 Test Results

```bash
# Parent knows: Apple is red, Sky is blue, Grass is green

# After 3 agents resume and add facts:
Agent 1 knows: red, blue, green, yellow (added Sun is yellow)
Agent 2 knows: red, blue, green, wet (added Water is wet)
Agent 3 knows: red, blue, green, hot (added Fire is hot)

# Parent still only knows: red, blue, green (unchanged!)
```

---

## 2. The Aggregation Challenge

### 2.1 The Problem

**Question:** "How could we initialize a 7th instance with context from all 5 prior agents?"

**Answer:** Claude doesn't support multi-parent resume. You can only resume from ONE conversation.

### 2.2 Current Limitations

- **No `--resume-multiple`** flag
- **No conversation merging** capability
- **No shared memory** between branches
- **No automatic aggregation** mechanism

---

## 3. Aggregation Strategies

### 3.1 Strategy 1: Manual Knowledge Injection

```python
def aggregate_via_prompt(parent_session: str, agent_results: List[Dict]) -> str:
    """Aggregate by injecting all discoveries into prompt"""
    
    # Collect discoveries from all agents
    discoveries = []
    for result in agent_results:
        discoveries.append(result['discovery'])
    
    # Create aggregation prompt
    prompt = f"""
    Previous agents discovered:
    {json.dumps(discoveries, indent=2)}
    
    Please incorporate all these discoveries.
    """
    
    # Resume parent with aggregated knowledge
    aggregated = claude_resume(parent_session, prompt)
    return aggregated['session_id']  # New branch with all knowledge
```

**Pros:** Simple, explicit, traceable
**Cons:** Token intensive, manual process

### 3.2 Strategy 2: File-Based Context Sharing

```python
def aggregate_via_files(parent_session: str, agent_sessions: List[str]) -> str:
    """Aggregate through shared files"""
    
    # Write discoveries to file
    discoveries_file = f"/tmp/discoveries_{uuid.uuid4()}.json"
    discoveries = collect_discoveries(agent_sessions)
    
    with open(discoveries_file, 'w') as f:
        json.dump(discoveries, f)
    
    # New agent reads file
    prompt = f"Read discoveries from {discoveries_file} and incorporate them."
    return claude_resume(parent_session, prompt)
```

**Pros:** Handles large context, structured data
**Cons:** File management overhead, cleanup needed

### 3.3 Strategy 3: Hierarchical Aggregation

```python
def hierarchical_aggregation(parent: str, branches: List[str]) -> str:
    """Aggregate in stages to manage complexity"""
    
    # Level 1: Pairwise aggregation
    level1 = []
    for i in range(0, len(branches), 2):
        pair = branches[i:i+2]
        aggregated = aggregate_pair(parent, pair)
        level1.append(aggregated)
    
    # Level 2: Aggregate the aggregations
    if len(level1) > 1:
        return hierarchical_aggregation(parent, level1)
    
    return level1[0]
```

**Pros:** Scales better, manages token limits
**Cons:** Multiple rounds, slower

### 3.4 Strategy 4: External State Management

```python
class ConversationAggregator:
    """Manage conversation state externally"""
    
    def __init__(self):
        self.knowledge_base = {}
        self.conversation_graph = {}
    
    def track_branch(self, session_id: str, parent_id: str, discoveries: Dict):
        """Track what each branch discovered"""
        self.knowledge_base[session_id] = {
            'parent': parent_id,
            'discoveries': discoveries,
            'timestamp': datetime.now()
        }
    
    def create_aggregated_context(self, branch_ids: List[str]) -> Dict:
        """Build aggregated context from multiple branches"""
        context = {
            'facts': set(),
            'patterns': [],
            'errors': [],
            'solutions': {}
        }
        
        for branch_id in branch_ids:
            branch_knowledge = self.knowledge_base.get(branch_id, {})
            # Merge discoveries
            context['facts'].update(branch_knowledge.get('facts', []))
            context['patterns'].extend(branch_knowledge.get('patterns', []))
            
        return context
    
    def spawn_with_aggregated_context(self, parent: str, branch_ids: List[str]):
        """Spawn new agent with aggregated knowledge"""
        context = self.create_aggregated_context(branch_ids)
        
        prompt = f"""
        You are starting with aggregated knowledge from {len(branch_ids)} agents:
        {json.dumps(context, indent=2)}
        """
        
        return claude_resume(parent, prompt)
```

**Pros:** Full control, complex aggregation logic
**Cons:** External infrastructure needed

---

## 4. Practical Patterns

### 4.1 Map-Reduce Pattern

```python
async def map_reduce_analysis(base_session: str, files: List[str]):
    """Map-reduce pattern for parallel analysis"""
    
    # MAP: Analyze files in parallel
    map_tasks = []
    for file in files:
        task = analyze_file(base_session, file)  # Each creates branch
        map_tasks.append(task)
    
    map_results = await asyncio.gather(*map_tasks)
    
    # REDUCE: Aggregate results
    aggregated_session = aggregate_results(base_session, map_results)
    
    # Final synthesis
    return synthesize(aggregated_session)
```

### 4.2 Tournament Pattern

```python
def tournament_selection(base: str, approaches: List[str]) -> str:
    """Try approaches in parallel, select winner"""
    
    # Parallel exploration
    branches = []
    for approach in approaches:
        branch = try_approach(base, approach)
        score = evaluate_approach(branch)
        branches.append((branch, score))
    
    # Select best
    best_branch = max(branches, key=lambda x: x[1])
    
    # Continue from best branch
    return continue_from_best(best_branch[0])
```

### 4.3 Consensus Pattern

```python
def consensus_decision(base: str, validators: int = 3) -> str:
    """Multiple agents validate and reach consensus"""
    
    # Multiple validators
    validations = []
    for i in range(validators):
        validation = validate_solution(base, f"Validator {i}")
        validations.append(validation)
    
    # Aggregate consensus
    consensus = find_consensus(validations)
    
    # Create final with consensus
    return create_with_consensus(base, consensus)
```

---

## 5. Architecture Implications

### 5.1 Conversation Tree Structure

```
Root Session
├── Generation 1
│   ├── Agent 1.1
│   ├── Agent 1.2
│   └── Agent 1.3
├── Aggregation Point 1 (manual merge)
├── Generation 2
│   ├── Agent 2.1 (from aggregation)
│   └── Agent 2.2 (from aggregation)
└── Final Aggregation
```

### 5.2 State Management Requirements

1. **Session Registry** - Track all sessions and relationships
2. **Discovery Store** - Persist findings from each branch
3. **Aggregation Engine** - Merge discoveries intelligently
4. **Cleanup Manager** - Prune old branches

### 5.3 Resource Considerations

```python
def estimate_resources(agents: int, generations: int) -> Dict:
    """Estimate conversation proliferation"""
    
    total_conversations = 0
    current_branches = 1  # Start with root
    
    for gen in range(generations):
        new_branches = current_branches * agents
        total_conversations += new_branches
        
        # Assuming aggregation after each generation
        current_branches = 1  # Reset to aggregated
    
    return {
        'total_sessions': total_conversations,
        'memory_estimate': total_conversations * AVG_SESSION_SIZE,
        'cleanup_needed': total_conversations > 100
    }
```

---

## 6. Best Practices

### 6.1 DO's

1. **Track lineage** - Maintain parent-child relationships
2. **Aggregate early** - Don't let branches proliferate
3. **Use structured formats** - JSON for discoveries
4. **Clean up branches** - Delete after aggregation
5. **Document decisions** - Why each branch was created

### 6.2 DON'Ts

1. **Don't assume merging** - Branches never auto-merge
2. **Don't lose parent reference** - Need it for aggregation
3. **Don't ignore token limits** - Aggregation can be expensive
4. **Don't create unnecessary branches** - Each costs resources
5. **Don't forget cleanup** - Sessions accumulate

---

## 7. Implementation Example

```python
class MultiAgentOrchestrator:
    """Orchestrate multi-agent execution with aggregation"""
    
    def __init__(self):
        self.session_tree = {}
        self.discoveries = {}
    
    async def execute_parallel_analysis(
        self,
        base_task: str,
        sub_tasks: List[str]
    ) -> str:
        """Execute parallel analysis with aggregation"""
        
        # Create base session
        base_session = create_session(base_task)
        self.session_tree[base_session] = {
            'parent': None,
            'children': []
        }
        
        # Spawn parallel agents
        branches = []
        for sub_task in sub_tasks:
            branch = await self.spawn_branch(base_session, sub_task)
            branches.append(branch)
            self.session_tree[base_session]['children'].append(branch)
        
        # Collect discoveries
        discoveries = await self.collect_discoveries(branches)
        
        # Aggregate into new session
        aggregated = await self.aggregate_knowledge(
            base_session,
            discoveries
        )
        
        # Clean up branches (optional)
        for branch in branches:
            await self.cleanup_branch(branch)
        
        return aggregated
    
    async def aggregate_knowledge(
        self,
        parent: str,
        discoveries: List[Dict]
    ) -> str:
        """Create new session with aggregated knowledge"""
        
        # Format discoveries
        knowledge_summary = self.format_discoveries(discoveries)
        
        # Create aggregation prompt
        prompt = f"""
        Aggregating discoveries from {len(discoveries)} parallel analyses:
        
        {knowledge_summary}
        
        Synthesize these findings into a coherent understanding.
        """
        
        # Resume parent with aggregated knowledge
        result = await claude_resume(parent, prompt)
        
        # Track new aggregated session
        new_session = result['session_id']
        self.session_tree[new_session] = {
            'parent': parent,
            'children': [],
            'aggregated_from': discoveries
        }
        
        return new_session
```

---

## 8. Future Considerations

### 8.1 Potential Claude Enhancements

1. **Multi-parent resume** - `--resume-multiple session1,session2`
2. **Session merging** - `--merge-sessions session1,session2`
3. **Shared memory** - Cross-session knowledge store
4. **Branch diffing** - See what each branch added
5. **Automatic aggregation** - Built-in merge strategies

### 8.2 Workaround Improvements

1. **Graph databases** - Neo4j for conversation relationships
2. **Vector embeddings** - Semantic discovery matching
3. **Streaming aggregation** - Real-time knowledge synthesis
4. **Federated learning** - Agents learn from each other
5. **Blockchain consensus** - Immutable aggregation records

---

## 9. Conclusion

### Key Takeaways

1. **Each resume creates an independent branch** - Plan accordingly
2. **Parent conversations remain immutable** - Good for reproducibility
3. **Aggregation requires explicit strategies** - No automatic merging
4. **Token management is critical** - Aggregation can be expensive
5. **External state management helps** - Track discoveries outside Claude

### Design Principles

1. **Plan aggregation points** - Don't let branches proliferate
2. **Use structured data** - Easier to aggregate
3. **Maintain session genealogy** - Track relationships
4. **Implement cleanup** - Manage resource usage
5. **Choose appropriate strategy** - Match to use case

### The Bottom Line

Claude's conversation branching model is powerful for parallel exploration but requires thoughtful design for knowledge aggregation. The lack of automatic merging is a limitation but also ensures reproducibility and isolation.

For the "7th agent with all knowledge" scenario, manual aggregation through prompt injection or file-based context sharing are the current best practices.