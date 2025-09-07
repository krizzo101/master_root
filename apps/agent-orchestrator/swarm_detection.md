# Agent Swarm Detection Algorithms

## Executive Summary

This document presents a comprehensive analysis of algorithms and strategies for detecting and grouping agent swarms in multi-agent orchestration systems. Based on research of clustering algorithms, existing orchestrator patterns, and swarm intelligence principles, we provide practical implementations for identifying collaborative agent groups.

## 1. Core Detection Algorithms

### 1.1 Time-Based Clustering Algorithms

#### DBSCAN (Density-Based Spatial Clustering of Applications with Noise)
**Best for:** Detecting agent swarms with arbitrary shapes and identifying outliers

```python
def dbscan_agent_clustering(agents, eps_seconds=5, min_samples=3):
    """
    Cluster agents based on temporal proximity using DBSCAN
    
    Parameters:
    - agents: List of (agent_id, timestamp) tuples
    - eps_seconds: Maximum time gap between agents in same cluster
    - min_samples: Minimum agents required to form a cluster
    
    Returns:
    - cluster_assignments: Dict mapping agent_id to cluster_id
    """
    from sklearn.cluster import DBSCAN
    import numpy as np
    
    # Convert timestamps to numerical format
    timestamps = np.array([ts.timestamp() for _, ts in agents]).reshape(-1, 1)
    
    # Apply DBSCAN
    clustering = DBSCAN(eps=eps_seconds, min_samples=min_samples)
    labels = clustering.fit_predict(timestamps)
    
    # Map agents to clusters
    clusters = {}
    for (agent_id, _), label in zip(agents, labels):
        if label != -1:  # -1 indicates noise/outlier
            clusters[agent_id] = f"swarm_{label}"
    
    return clusters
```

#### Hierarchical Temporal Clustering
**Best for:** Multi-scale swarm detection with dendrogram visualization

```python
def hierarchical_temporal_clustering(agents, distance_threshold=10):
    """
    Hierarchical clustering for agents with temporal relationships
    
    Parameters:
    - agents: List of agent task objects with start_time
    - distance_threshold: Maximum time distance for clustering
    
    Returns:
    - hierarchy: Nested cluster structure
    """
    from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
    import numpy as np
    
    # Create time-based feature matrix
    time_matrix = np.array([[a.start_time] for a in agents])
    
    # Perform hierarchical clustering
    linkage_matrix = linkage(time_matrix, method='ward')
    clusters = fcluster(linkage_matrix, distance_threshold, criterion='distance')
    
    return {
        'clusters': clusters,
        'linkage': linkage_matrix,
        'dendrogram': lambda: dendrogram(linkage_matrix)
    }
```

#### Sliding Window Clustering
**Best for:** Real-time swarm detection in streaming scenarios

```python
def sliding_window_clustering(window_size_seconds=30, overlap=0.5):
    """
    Detect swarms using sliding time windows
    
    Parameters:
    - window_size_seconds: Size of time window
    - overlap: Fraction of window overlap (0-1)
    
    Returns:
    - SwarmDetector instance for streaming detection
    """
    class SwarmDetector:
        def __init__(self, window_size, overlap):
            self.window_size = window_size
            self.stride = window_size * (1 - overlap)
            self.agent_buffer = []
            self.swarms = {}
            
        def add_agent(self, agent_id, timestamp):
            self.agent_buffer.append((agent_id, timestamp))
            self._detect_swarms()
            
        def _detect_swarms(self):
            current_time = max(t for _, t in self.agent_buffer)
            window_start = current_time - self.window_size
            
            # Get agents in current window
            window_agents = [
                (aid, ts) for aid, ts in self.agent_buffer 
                if window_start <= ts <= current_time
            ]
            
            # Detect swarm if threshold met
            if len(window_agents) >= 3:
                swarm_id = f"swarm_{int(current_time)}"
                for aid, _ in window_agents:
                    self.swarms[aid] = swarm_id
                    
            # Clean old entries
            self.agent_buffer = [
                (aid, ts) for aid, ts in self.agent_buffer 
                if ts > current_time - self.window_size * 2
            ]
    
    return SwarmDetector(window_size_seconds, overlap)
```

### 1.2 Directory-Based Grouping Strategies

#### Hierarchical Directory Analysis
**Best for:** Identifying agent relationships through file system structure

```python
def directory_based_grouping(base_path):
    """
    Group agents based on directory structure and naming patterns
    
    Parameters:
    - base_path: Root directory containing agent workspaces
    
    Returns:
    - groups: Dict of group_name -> [agent_ids]
    """
    from pathlib import Path
    import re
    
    groups = {
        'by_project': {},
        'by_task_type': {},
        'by_timestamp': {},
        'by_team': {}
    }
    
    base = Path(base_path)
    
    for agent_dir in base.glob("**/agent_*"):
        agent_id = agent_dir.name
        
        # Group by parent project
        project = agent_dir.parent.name
        groups['by_project'].setdefault(project, []).append(agent_id)
        
        # Extract task type from directory structure
        if 'tasks' in agent_dir.parts:
            task_idx = agent_dir.parts.index('tasks')
            if task_idx > 0:
                task_type = agent_dir.parts[task_idx - 1]
                groups['by_task_type'].setdefault(task_type, []).append(agent_id)
        
        # Group by timestamp patterns in path
        timestamp_match = re.search(r'(\d{8}_\d{6})', str(agent_dir))
        if timestamp_match:
            timestamp = timestamp_match.group(1)
            groups['by_timestamp'].setdefault(timestamp, []).append(agent_id)
        
        # Team-based grouping from naming convention
        team_match = re.search(r'team_(\w+)', str(agent_dir))
        if team_match:
            team = team_match.group(1)
            groups['by_team'].setdefault(team, []).append(agent_id)
    
    return groups
```

#### Workspace Proximity Detection
**Best for:** Finding agents working on related files

```python
def workspace_proximity_detection(agent_workspaces):
    """
    Detect agent swarms based on shared workspace resources
    
    Parameters:
    - agent_workspaces: Dict of agent_id -> [file_paths]
    
    Returns:
    - proximity_graph: Agent relationships based on file overlap
    """
    from collections import defaultdict
    
    file_to_agents = defaultdict(set)
    proximity_scores = defaultdict(lambda: defaultdict(float))
    
    # Build file-to-agent mapping
    for agent_id, files in agent_workspaces.items():
        for file_path in files:
            file_to_agents[file_path].add(agent_id)
    
    # Calculate proximity scores
    for agents in file_to_agents.values():
        if len(agents) > 1:
            agent_list = list(agents)
            for i, agent1 in enumerate(agent_list):
                for agent2 in agent_list[i+1:]:
                    proximity_scores[agent1][agent2] += 1
                    proximity_scores[agent2][agent1] += 1
    
    # Identify swarms (agents with high proximity)
    swarms = []
    threshold = 2  # Minimum shared files
    processed = set()
    
    for agent1, neighbors in proximity_scores.items():
        if agent1 not in processed:
            swarm = {agent1}
            for agent2, score in neighbors.items():
                if score >= threshold:
                    swarm.add(agent2)
                    processed.add(agent2)
            if len(swarm) > 1:
                swarms.append(swarm)
                processed.add(agent1)
    
    return {
        'swarms': swarms,
        'proximity_scores': dict(proximity_scores)
    }
```

### 1.3 Swarm Identification Heuristics

#### Behavioral Pattern Detection
**Best for:** Identifying coordinated agent behaviors

```python
class SwarmBehaviorDetector:
    """
    Detect swarm patterns through behavioral analysis
    """
    
    def __init__(self):
        self.patterns = {
            'burst': self._detect_burst_pattern,
            'sequential': self._detect_sequential_pattern,
            'parallel': self._detect_parallel_pattern,
            'hierarchical': self._detect_hierarchical_pattern
        }
        
    def detect_swarm_patterns(self, agent_tasks):
        """
        Analyze agent tasks for swarm behavior patterns
        
        Parameters:
        - agent_tasks: List of task objects with metadata
        
        Returns:
        - detected_patterns: Dict of pattern_type -> agent_groups
        """
        results = {}
        
        for pattern_name, detector in self.patterns.items():
            detected = detector(agent_tasks)
            if detected:
                results[pattern_name] = detected
                
        return results
    
    def _detect_burst_pattern(self, tasks):
        """Detect sudden burst of agent activity"""
        from collections import defaultdict
        
        # Group tasks by 1-second windows
        time_buckets = defaultdict(list)
        for task in tasks:
            bucket = int(task.start_time)
            time_buckets[bucket].append(task.agent_id)
        
        # Find bursts (>5 agents in same second)
        bursts = []
        for timestamp, agents in time_buckets.items():
            if len(agents) > 5:
                bursts.append({
                    'timestamp': timestamp,
                    'agents': agents,
                    'intensity': len(agents)
                })
        
        return bursts if bursts else None
    
    def _detect_sequential_pattern(self, tasks):
        """Detect sequential task handoffs between agents"""
        sequences = []
        
        # Sort tasks by completion time
        sorted_tasks = sorted(tasks, key=lambda t: t.end_time or float('inf'))
        
        current_sequence = []
        for i in range(len(sorted_tasks) - 1):
            task1 = sorted_tasks[i]
            task2 = sorted_tasks[i + 1]
            
            # Check if task2 depends on task1
            if task1.task_id in task2.dependencies:
                if not current_sequence:
                    current_sequence = [task1.agent_id]
                current_sequence.append(task2.agent_id)
            elif current_sequence:
                if len(current_sequence) > 2:
                    sequences.append(current_sequence)
                current_sequence = []
        
        return sequences if sequences else None
    
    def _detect_parallel_pattern(self, tasks):
        """Detect parallel execution patterns"""
        from collections import defaultdict
        
        # Group by execution overlap
        parallel_groups = []
        processed = set()
        
        for i, task1 in enumerate(tasks):
            if task1.task_id in processed:
                continue
                
            group = [task1.agent_id]
            processed.add(task1.task_id)
            
            for task2 in tasks[i+1:]:
                if task2.task_id not in processed:
                    # Check temporal overlap
                    if self._tasks_overlap(task1, task2):
                        group.append(task2.agent_id)
                        processed.add(task2.task_id)
            
            if len(group) > 2:
                parallel_groups.append(group)
        
        return parallel_groups if parallel_groups else None
    
    def _detect_hierarchical_pattern(self, tasks):
        """Detect master-worker hierarchical patterns"""
        hierarchies = []
        
        # Identify coordinator agents (those creating many subtasks)
        task_creators = defaultdict(list)
        for task in tasks:
            if task.created_by:
                task_creators[task.created_by].append(task.agent_id)
        
        for master, workers in task_creators.items():
            if len(workers) > 2:
                hierarchies.append({
                    'master': master,
                    'workers': workers,
                    'depth': self._calculate_hierarchy_depth(tasks, master)
                })
        
        return hierarchies if hierarchies else None
    
    def _tasks_overlap(self, task1, task2):
        """Check if two tasks overlap in time"""
        start1, end1 = task1.start_time, task1.end_time or float('inf')
        start2, end2 = task2.start_time, task2.end_time or float('inf')
        return max(start1, start2) < min(end1, end2)
    
    def _calculate_hierarchy_depth(self, tasks, root_agent):
        """Calculate depth of task hierarchy"""
        # Implementation would trace dependency chains
        return 1  # Simplified
```

#### Communication Pattern Analysis
**Best for:** Detecting swarms through message passing patterns

```python
def analyze_communication_patterns(message_log):
    """
    Detect swarms through inter-agent communication analysis
    
    Parameters:
    - message_log: List of (timestamp, sender, receiver, message_type) tuples
    
    Returns:
    - communication_clusters: Detected agent clusters
    """
    from collections import defaultdict
    import networkx as nx
    
    # Build communication graph
    G = nx.DiGraph()
    edge_weights = defaultdict(int)
    
    for timestamp, sender, receiver, msg_type in message_log:
        G.add_edge(sender, receiver)
        edge_weights[(sender, receiver)] += 1
    
    # Add edge weights
    for edge, weight in edge_weights.items():
        G[edge[0]][edge[1]]['weight'] = weight
    
    # Detect communities (swarms)
    if len(G.nodes()) > 0:
        # Use Louvain method for community detection
        import community as community_louvain
        
        # Convert to undirected for community detection
        G_undirected = G.to_undirected()
        communities = community_louvain.best_partition(G_undirected)
        
        # Group agents by community
        swarms = defaultdict(list)
        for agent, community_id in communities.items():
            swarms[f"comm_{community_id}"].append(agent)
        
        return {
            'swarms': dict(swarms),
            'graph_metrics': {
                'density': nx.density(G),
                'avg_clustering': nx.average_clustering(G.to_undirected()),
                'connected_components': list(nx.weakly_connected_components(G))
            }
        }
    
    return {'swarms': {}, 'graph_metrics': {}}
```

## 2. Optimal Grouping Strategies

### 2.1 Hybrid Approach: Multi-Criteria Swarm Detection

```python
class HybridSwarmDetector:
    """
    Combines multiple detection strategies for robust swarm identification
    """
    
    def __init__(self, config=None):
        self.config = config or {
            'temporal_weight': 0.4,
            'spatial_weight': 0.3,
            'behavioral_weight': 0.3,
            'min_swarm_size': 3,
            'confidence_threshold': 0.6
        }
        
        self.detectors = {
            'temporal': self._temporal_detection,
            'spatial': self._spatial_detection,
            'behavioral': self._behavioral_detection
        }
        
    def detect_swarms(self, agent_data):
        """
        Perform multi-criteria swarm detection
        
        Parameters:
        - agent_data: Comprehensive agent activity data
        
        Returns:
        - swarms: List of detected swarms with confidence scores
        """
        detection_results = {}
        
        # Run all detectors
        for detector_name, detector_func in self.detectors.items():
            detection_results[detector_name] = detector_func(agent_data)
        
        # Merge and score results
        merged_swarms = self._merge_detections(detection_results)
        
        # Filter by confidence
        confident_swarms = [
            swarm for swarm in merged_swarms 
            if swarm['confidence'] >= self.config['confidence_threshold']
        ]
        
        return confident_swarms
    
    def _temporal_detection(self, data):
        """Time-based clustering using DBSCAN"""
        # Implementation using DBSCAN as shown earlier
        return []  # Placeholder
    
    def _spatial_detection(self, data):
        """Directory and workspace-based detection"""
        # Implementation using directory analysis
        return []  # Placeholder
    
    def _behavioral_detection(self, data):
        """Pattern-based behavior detection"""
        # Implementation using behavior detector
        return []  # Placeholder
    
    def _merge_detections(self, results):
        """Merge results from multiple detectors with weighted scoring"""
        from collections import defaultdict
        
        agent_scores = defaultdict(lambda: defaultdict(float))
        
        # Weight and combine scores
        weights = {
            'temporal': self.config['temporal_weight'],
            'spatial': self.config['spatial_weight'],
            'behavioral': self.config['behavioral_weight']
        }
        
        for detector_name, detections in results.items():
            weight = weights.get(detector_name, 0.33)
            for swarm in detections:
                for agent in swarm:
                    agent_scores[swarm['id']][agent] += weight
        
        # Form final swarms
        final_swarms = []
        for swarm_id, agents in agent_scores.items():
            swarm_agents = [
                agent for agent, score in agents.items() 
                if score >= 0.5
            ]
            
            if len(swarm_agents) >= self.config['min_swarm_size']:
                final_swarms.append({
                    'id': swarm_id,
                    'agents': swarm_agents,
                    'confidence': sum(agents.values()) / len(agents),
                    'size': len(swarm_agents)
                })
        
        return final_swarms
```

### 2.2 Recommended Implementation Strategy

1. **For Real-time Systems**: Use sliding window clustering with behavioral pattern detection
2. **For Batch Processing**: Apply DBSCAN with hierarchical clustering for multi-scale analysis
3. **For File-based Systems**: Combine directory-based grouping with workspace proximity
4. **For Complex Orchestration**: Implement the hybrid detector with weighted multi-criteria analysis

## 3. Performance Considerations

### 3.1 Algorithm Complexity

| Algorithm | Time Complexity | Space Complexity | Best Use Case |
|-----------|----------------|------------------|---------------|
| DBSCAN | O(n log n)* | O(n) | Medium datasets, arbitrary shapes |
| Hierarchical | O(n² log n) | O(n²) | Small datasets, visualization needed |
| Sliding Window | O(n) | O(w) | Streaming data, real-time |
| Directory-based | O(n) | O(n) | File system analysis |
| Communication Graph | O(n + e) | O(n + e) | Message-heavy systems |

*With spatial index

### 3.2 Optimization Strategies

```python
class OptimizedSwarmDetector:
    """
    Performance-optimized swarm detection
    """
    
    def __init__(self):
        self.index = {}  # Spatial/temporal index
        self.cache = {}  # Result cache
        self.batch_size = 1000
        
    def detect_with_indexing(self, agents):
        """Use indexing for faster lookups"""
        import numpy as np
        from sklearn.neighbors import BallTree
        
        # Build temporal index
        timestamps = np.array([[a.start_time] for a in agents])
        tree = BallTree(timestamps, metric='manhattan')
        
        # Query for neighbors within time window
        neighbors = tree.query_radius(timestamps, r=5.0)
        
        # Form swarms from neighbor sets
        swarms = []
        processed = set()
        
        for i, neighbor_indices in enumerate(neighbors):
            if i not in processed and len(neighbor_indices) >= 3:
                swarm = [agents[j].agent_id for j in neighbor_indices]
                swarms.append(swarm)
                processed.update(neighbor_indices)
        
        return swarms
    
    def detect_incremental(self, new_agent, existing_swarms):
        """Incremental swarm update for streaming scenarios"""
        updated_swarms = existing_swarms.copy()
        
        # Check if new agent belongs to existing swarm
        for swarm_id, swarm_data in updated_swarms.items():
            if self._agent_fits_swarm(new_agent, swarm_data):
                swarm_data['agents'].append(new_agent.agent_id)
                swarm_data['last_updated'] = new_agent.start_time
                return updated_swarms
        
        # Check if new agent forms new swarm with recent agents
        recent_window = 10  # seconds
        recent_agents = self._get_recent_agents(new_agent.start_time, recent_window)
        
        if len(recent_agents) >= 2:  # New agent + 2 others = swarm
            new_swarm_id = f"swarm_{int(new_agent.start_time)}"
            updated_swarms[new_swarm_id] = {
                'agents': [new_agent.agent_id] + recent_agents,
                'created': new_agent.start_time,
                'last_updated': new_agent.start_time
            }
        
        return updated_swarms
    
    def _agent_fits_swarm(self, agent, swarm_data):
        """Check if agent fits existing swarm criteria"""
        time_threshold = 10  # seconds
        return abs(agent.start_time - swarm_data['last_updated']) < time_threshold
    
    def _get_recent_agents(self, timestamp, window):
        """Get agents within time window (from cache/index)"""
        # Implementation would use the index
        return []  # Placeholder
```

### 3.3 Scalability Guidelines

1. **< 100 agents**: Any algorithm works well
2. **100-1000 agents**: Use DBSCAN or sliding window
3. **1000-10000 agents**: Implement indexing and incremental updates
4. **> 10000 agents**: Distributed processing with Apache Spark or similar

## 4. Integration with Existing Orchestrator

### 4.1 Integration Points

```python
class SwarmAwareOrchestrator(UnifiedOrchestrator):
    """
    Orchestrator enhanced with swarm detection capabilities
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.swarm_detector = HybridSwarmDetector()
        self.active_swarms = {}
        
    async def execute_batch(self, tasks):
        """Execute tasks with swarm awareness"""
        
        # Detect swarms in task batch
        swarms = self.swarm_detector.detect_swarms({
            'tasks': tasks,
            'timestamps': [t.start_time for t in tasks],
            'workspaces': self._extract_workspaces(tasks)
        })
        
        # Assign swarm IDs to tasks
        for swarm in swarms:
            swarm_id = swarm['id']
            self.active_swarms[swarm_id] = swarm
            
            for agent_id in swarm['agents']:
                task = self._find_task_by_agent(tasks, agent_id)
                if task:
                    task.swarm_id = swarm_id
                    task.swarm_confidence = swarm['confidence']
        
        # Execute with swarm-aware scheduling
        return await super().execute_batch(tasks)
    
    def get_swarm_metrics(self):
        """Get metrics about detected swarms"""
        return {
            'active_swarms': len(self.active_swarms),
            'total_swarmed_agents': sum(
                len(s['agents']) for s in self.active_swarms.values()
            ),
            'average_swarm_size': np.mean([
                len(s['agents']) for s in self.active_swarms.values()
            ]) if self.active_swarms else 0,
            'swarm_details': self.active_swarms
        }
```

## 5. Example Usage

```python
# Initialize swarm-aware orchestrator
config = UnifiedConfig(
    output_dir=Path("/tmp/orchestrator"),
    enabled_features={FeatureFlag.ENHANCED_METRICS}
)

orchestrator = SwarmAwareOrchestrator(config)

# Generate tasks that might form swarms
tasks = []
base_time = time.time()

# Create burst pattern (swarm 1)
for i in range(5):
    task = EnhancedAgentTask(
        task_id=f"burst_{i}",
        agent_id=f"agent_{i}",
        start_time=base_time + i * 0.1,  # Rapid succession
        task_type="analysis"
    )
    tasks.append(task)

# Create sequential pattern (swarm 2)
for i in range(5, 10):
    task = EnhancedAgentTask(
        task_id=f"seq_{i}",
        agent_id=f"agent_{i}",
        start_time=base_time + 60 + i * 5,  # Sequential with gaps
        dependencies=[f"seq_{i-1}"] if i > 5 else [],
        task_type="processing"
    )
    tasks.append(task)

# Execute and analyze
results = await orchestrator.execute_batch(tasks)
swarm_metrics = orchestrator.get_swarm_metrics()

print(f"Detected {swarm_metrics['active_swarms']} swarms")
print(f"Average swarm size: {swarm_metrics['average_swarm_size']:.1f}")
for swarm_id, swarm_data in swarm_metrics['swarm_details'].items():
    print(f"  {swarm_id}: {len(swarm_data['agents'])} agents")
```

## 6. Conclusion

The optimal swarm detection strategy depends on your specific use case:

- **For general purpose**: Use the hybrid detector with weighted multi-criteria
- **For real-time monitoring**: Implement sliding window with behavioral patterns
- **For post-hoc analysis**: Apply DBSCAN with hierarchical clustering
- **For file-based systems**: Combine directory analysis with workspace proximity

The provided implementations offer a solid foundation for detecting and managing agent swarms in orchestration systems, with considerations for performance, scalability, and integration with existing infrastructure.