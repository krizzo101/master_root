# HECATON Function Call Flow

## Complete Execution Flow from Start to Finish

### 1. Entry Point & Initialization

```
main() [__main__.py:225]
├── argparse.ArgumentParser() - Parse command line arguments
├── HecatonApp.__init__(mode="send-api", verbose=False) [__main__.py:26]
│   ├── _init_token_pool() [__main__.py:71]
│   │   ├── Load config/claude_tokens.json OR
│   │   └── SecureTokenPool(tokens=[...])
│   ├── WorktreeManager(base_path="/tmp/hecaton_worktrees")
│   ├── AgentRegistry()
│   ├── PerformanceMonitor()
│   └── [mode == "send-api"]
│       ├── RealClaudeSubprocessExecutor(token_pool, worktree_manager)
│       └── SendAPIOrchestrator(executor, token_pool, worktree_manager, performance_monitor)
└── asyncio.run(app.run(task, agents)) [__main__.py:290]
```

### 2. Main Execution Flow (Send API Mode - Default)

```
app.run(task="Build a REST API", agents=2) [__main__.py:91]
├── [use_send_api=True]
└── orchestrator.execute(task, num_agents=2) [send_api.py]
    ├── _prepare_execution_graph(task) [send_api.py:88]
    │   ├── ExecutionGraph() - Create graph structure
    │   ├── _determine_agent_types(task, num_agents)
    │   │   └── Returns: ["code", "research", "test", etc.]
    │   └── graph.add_node() for each agent type
    │       └── Creates nodes with task specifications
    │
    ├── _execute_parallel_send_api(graph) [send_api.py:213]
    │   ├── performance_monitor.start_tracking(graph.graph_id)
    │   ├── asyncio.create_task() for each node
    │   │   └── _execute_agent_node(node, graph) [send_api.py:242]
    │   │       ├── token_pool.acquire_token(agent_id)
    │   │       ├── worktree_manager.setup_agent(agent_id)
    │   │       ├── executor.execute_task(task_data)
    │   │       │   └── [See RealClaudeExecutor Flow below]
    │   │       ├── graph.update_node_result(node_id, result)
    │   │       ├── worktree_manager.cleanup_agent(agent_id)
    │   │       └── token_pool.release_token(agent_id)
    │   ├── await asyncio.gather(*tasks)
    │   └── performance_monitor.end_tracking(graph.graph_id)
    │
    └── _collect_results(graph) [send_api.py:283]
        └── Returns aggregated results dictionary
```

### 3. Real Claude Executor Flow

```
RealClaudeSubprocessExecutor.execute_task(task) [real_claude_executor.py:124]
├── _prepare_task(task) [real_claude_executor.py:181]
│   ├── Extract task parameters
│   ├── Determine agent type and model
│   └── Set working directory
│
├── _create_claude_process(task) [real_claude_executor.py:201]
│   ├── ClaudeCommandFactory().create_command(config)
│   │   ├── _auto_select_profile(config) [claude_command_factory.py:274]
│   │   ├── _build_base_command(config) [claude_command_factory.py:162]
│   │   └── _add_advanced_options(cmd, config) [claude_command_factory.py:257]
│   ├── subprocess.Popen(command, ...)
│   └── ClaudeProcess(process, agent_id, start_time)
│
├── _monitor_process(claude_process) [real_claude_executor.py:238]
│   ├── [Loop until complete or timeout]
│   │   ├── process.poll() - Check if finished
│   │   ├── _check_timeout(claude_process)
│   │   └── await asyncio.sleep(0.1)
│   └── process.communicate() - Get output
│
└── _parse_result(output, error, return_code) [real_claude_executor.py:287]
    └── Returns: {"status", "output", "error", "execution_time"}
```

### 4. Safety & Coordination Components

#### 4.1 Error Boundary Flow
```
ErrorBoundary.execute_with_boundary(func, context) [error_boundaries.py:44]
├── [Try execution with retries]
│   ├── func(*args, **kwargs)
│   └── [On Exception]
│       ├── _classify_error(error) → ErrorSeverity
│       ├── _check_custom_handler(error)
│       ├── [If retryable and retries < max_retries]
│       │   └── Exponential backoff → Retry
│       └── [If critical and propagate_critical]
│           └── raise error
├── [If all retries exhausted]
│   ├── _suggest_action(error) → suggestion
│   ├── [If fallback_handler exists]
│   │   └── fallback_handler(ErrorResult)
│   └── Return ErrorResult(error, severity, suggestion)
└── Return successful result
```

#### 4.2 Checkpoint Manager Flow
```
CheckpointManager.create_checkpoint(state, metadata) [checkpoint_manager.py:53]
├── Generate checkpoint_id (ckpt_timestamp_uuid)
├── Checkpoint(id, state, metadata, timestamp)
├── self.checkpoints[checkpoint_id] = checkpoint
├── self.checkpoint_order.append(checkpoint_id)
├── [If auto_cleanup and len > max_checkpoints]
│   └── _cleanup_old_checkpoints()
├── _persist_checkpoint(checkpoint)
│   └── Save to disk as JSON
└── Return checkpoint_id

CheckpointManager.rollback_to_checkpoint(checkpoint_id) [checkpoint_manager.py:85]
├── checkpoint = self.checkpoints[checkpoint_id]
├── [Remove all checkpoints after this one]
│   └── del self.checkpoints[id] for each newer
├── _load_from_disk(checkpoint_id) if not in memory
└── Return checkpoint.state
```

#### 4.3 Meta-Agent Delegation Flow
```
MetaAgent.decide_delegation(task, available_agents) [meta_agent.py:99]
├── _extract_task_requirements(task)
│   └── Parse task type, complexity, requirements
├── [For each registered agent]
│   ├── _calculate_agent_score(agent, requirements)
│   │   ├── Capability match score
│   │   ├── Current load penalty
│   │   ├── Performance history bonus
│   │   └── Specialization weight
│   └── scores[agent_id] = score
├── Select best_agent (highest score)
└── Return DelegationDecision(agent_id, confidence, reasoning)
```

#### 4.4 Swarm Task Decomposer Flow
```
SwarmTaskDecomposer.decompose_task(complex_task) [swarm_decomposer.py:46]
├── _extract_subtasks(complex_task) [swarm_decomposer.py:172]
│   └── _generate_subtasks(complex_task) or use provided
├── _build_task_graph(subtasks) [swarm_decomposer.py:231]
│   └── add_task_node() for each subtask
│       └── nx.DiGraph.add_node() and add_edge()
├── _optimize_execution_plan() [swarm_decomposer.py:237]
│   ├── nx.is_directed_acyclic_graph() - Check for cycles
│   └── nx.topological_generations() - Find parallel groups
└── _create_execution_groups(execution_plan) [swarm_decomposer.py:267]
    └── Return List[ExecutionGroup] with parallel/sequential tasks
```

### 5. Message Broker Flow

```
MessageBroker.publish(topic, message) [message_broker.py:113]
├── [If topic has subscribers]
│   └── [For each callback in self.subscribers[topic]]
│       └── asyncio.create_task(_invoke_callback(callback, message))
│           ├── callback(message)
│           └── [Handle exceptions gracefully]
└── self.message_history[topic].append(message)

MessageBroker.subscribe(topic, callback) [message_broker.py:90]
├── self.subscribers[topic].append(callback)
└── self.subscription_count[topic] += 1
```

### 6. Performance Monitoring Flow

```
PerformanceMonitor.start_tracking(task_id) [performance_monitor.py:48]
├── TaskMetrics(task_id, start_time=now)
└── self.active_tasks[task_id] = metrics

PerformanceMonitor.end_tracking(task_id, success) [performance_monitor.py:61]
├── metrics = self.active_tasks[task_id]
├── metrics.end_time = now
├── metrics.duration = end_time - start_time
├── metrics.success = success
├── self.completed_tasks.append(metrics)
├── del self.active_tasks[task_id]
└── _update_statistics(metrics)

PerformanceMonitor.calculate_statistics() [performance_monitor.py:85]
├── [For each completed task]
│   ├── Calculate avg_execution_time
│   ├── Calculate success_rate
│   └── Track min/max times
└── Return aggregated statistics
```

### 7. Worktree Manager Flow

```
WorktreeManager.setup_agent(agent_id) [worktree.py:46]
├── branch_name = f"agent/{agent_id}/{timestamp}"
├── worktree_path = base_path / agent_id
├── subprocess.run("git rev-parse HEAD") - Get current branch
├── subprocess.run(f"git branch {branch_name}") - Create branch
├── subprocess.run(f"git worktree add {worktree_path} {branch_name}")
├── self.agent_worktrees[agent_id] = worktree_path
└── Return worktree_path

WorktreeManager.cleanup_agent(agent_id) [worktree.py:88]
├── worktree_path = self.agent_worktrees[agent_id]
├── subprocess.run(f"git worktree remove {worktree_path}")
├── subprocess.run(f"git branch -D {branch_name}")
└── del self.agent_worktrees[agent_id]
```

## Complete Execution Example

When a user runs: `python -m hecaton run "Build a REST API" --agents 3`

1. **main()** parses arguments → creates HecatonApp(mode="send-api")
2. **HecatonApp.__init__** initializes all components
3. **app.run()** delegates to SendAPIOrchestrator
4. **SendAPIOrchestrator.execute()** creates ExecutionGraph with 3 nodes
5. **_execute_parallel_send_api()** launches 3 async tasks simultaneously
6. Each task:
   - Acquires a token from SecureTokenPool
   - Sets up isolated git worktree
   - Executes via RealClaudeSubprocessExecutor
   - Updates graph with results
   - Cleans up resources
7. **_collect_results()** aggregates all agent outputs
8. Results displayed to user with success/failure status

## Key Design Patterns

1. **Send API Pattern**: True parallel execution via asyncio.gather()
2. **Error Boundary Pattern**: Fault isolation with retry logic
3. **Checkpoint Pattern**: State snapshots for recovery
4. **Meta-Agent Pattern**: Intelligent task delegation
5. **Swarm Decomposition**: Complex task parallelization
6. **Resource Pool Pattern**: Token and worktree management
7. **Observer Pattern**: Message broker for inter-component communication
8. **Strategy Pattern**: Multiple execution modes (send-api vs simple)

## Performance Characteristics

- **Parallel Execution**: Up to N agents running simultaneously
- **Resource Management**: Token pool prevents API rate limits
- **Isolation**: Each agent has dedicated git worktree
- **Fault Tolerance**: Error boundaries and checkpoints
- **Monitoring**: Real-time performance tracking
- **Scalability**: Swarm decomposition for complex tasks
