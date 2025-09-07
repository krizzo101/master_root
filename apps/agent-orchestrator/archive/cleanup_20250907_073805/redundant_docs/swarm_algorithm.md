# Swarm Detection Algorithm Specification

## Executive Summary

This document specifies the production-ready swarm detection algorithm for agent orchestration systems. The algorithm uses a multi-stage approach combining temporal clustering, behavioral analysis, and resource correlation to identify agent swarms with high accuracy and performance.

## 1. Core Algorithm Design

### 1.1 Primary Detection Algorithm

```python
class SwarmDetectionEngine:
    """
    High-performance swarm detection engine using optimized DBSCAN variant
    with incremental updates and intelligent caching.
    """

    def __init__(self, config=None):
        self.config = config or SwarmConfig()
        self.agent_index = TemporalIndex()
        self.swarm_cache = LRUCache(maxsize=1000)
        self.active_swarms = {}
        self.stats = SwarmStatistics()

    def detect_swarms(self, agents, mode='batch'):
        """
        Main entry point for swarm detection

        Parameters:
        - agents: List of agent objects or events
        - mode: 'batch', 'streaming', or 'incremental'

        Returns:
        - SwarmDetectionResult with identified swarms
        """
        if mode == 'batch':
            return self._batch_detection(agents)
        elif mode == 'streaming':
            return self._streaming_detection(agents)
        else:
            return self._incremental_detection(agents)

    def _batch_detection(self, agents):
        """Optimized batch detection for complete agent sets"""

        # Stage 1: Temporal clustering
        temporal_clusters = self._temporal_clustering(agents)

        # Stage 2: Behavioral analysis
        behavioral_groups = self._behavioral_analysis(agents)

        # Stage 3: Resource correlation
        resource_groups = self._resource_correlation(agents)

        # Stage 4: Merge and score
        final_swarms = self._merge_and_score(
            temporal_clusters,
            behavioral_groups,
            resource_groups
        )

        return SwarmDetectionResult(
            swarms=final_swarms,
            confidence_scores=self._calculate_confidence(final_swarms),
            statistics=self.stats.compute()
        )
```

### 1.2 Temporal Clustering Implementation

```python
def _temporal_clustering(self, agents):
    """
    Fast temporal clustering using optimized DBSCAN with KD-tree indexing

    Time Complexity: O(n log n) average case
    Space Complexity: O(n)
    """
    import numpy as np
    from scipy.spatial import KDTree

    # Convert timestamps to numerical features
    timestamps = np.array([[
        agent.start_time,
        agent.priority_score,  # Secondary clustering dimension
    ] for agent in agents])

    # Normalize features for balanced clustering
    timestamps_norm = self._normalize_features(timestamps)

    # Build KD-tree for efficient neighbor queries
    tree = KDTree(timestamps_norm)

    # DBSCAN parameters
    eps = self.config.temporal_epsilon  # Default: 5 seconds
    min_pts = self.config.min_swarm_size  # Default: 3 agents

    # Core DBSCAN algorithm with optimizations
    clusters = []
    visited = np.zeros(len(agents), dtype=bool)
    cluster_id = 0

    for i in range(len(agents)):
        if visited[i]:
            continue

        # Find neighbors within epsilon
        neighbors = tree.query_ball_point(timestamps_norm[i], eps)

        if len(neighbors) < min_pts:
            continue  # Noise point

        # Start new cluster
        cluster = self._expand_cluster(
            i, neighbors, tree, timestamps_norm,
            visited, eps, min_pts
        )

        if len(cluster) >= min_pts:
            clusters.append({
                'id': f'temporal_{cluster_id}',
                'agents': [agents[idx] for idx in cluster],
                'type': 'temporal',
                'centroid': self._compute_centroid(cluster, timestamps),
                'density': len(cluster) / (2 * eps)
            })
            cluster_id += 1

    return clusters

def _expand_cluster(self, seed_idx, neighbors, tree, data,
                    visited, eps, min_pts):
    """Expand cluster from seed point using density reachability"""
    cluster = set([seed_idx])
    queue = list(neighbors)

    while queue:
        point_idx = queue.pop(0)

        if visited[point_idx]:
            continue

        visited[point_idx] = True
        cluster.add(point_idx)

        # Find neighbors of this point
        point_neighbors = tree.query_ball_point(data[point_idx], eps)

        if len(point_neighbors) >= min_pts:
            # Core point - add unvisited neighbors to queue
            for neighbor in point_neighbors:
                if not visited[neighbor]:
                    queue.append(neighbor)

    return list(cluster)
```

### 1.3 Behavioral Pattern Analysis

```python
def _behavioral_analysis(self, agents):
    """
    Detect behavioral patterns indicating coordinated swarm activity

    Patterns detected:
    - Burst: Sudden spike in agent creation
    - Sequential: Chain of dependent agents
    - Parallel: Concurrent execution patterns
    - Hierarchical: Master-worker relationships
    """
    patterns = {
        'burst': [],
        'sequential': [],
        'parallel': [],
        'hierarchical': []
    }

    # Burst detection using sliding window
    window_size = self.config.burst_window  # 1 second default
    time_buckets = self._create_time_buckets(agents, window_size)

    for timestamp, bucket_agents in time_buckets.items():
        if len(bucket_agents) >= self.config.burst_threshold:  # 5+ agents
            patterns['burst'].append({
                'id': f'burst_{timestamp}',
                'agents': bucket_agents,
                'intensity': len(bucket_agents),
                'timestamp': timestamp
            })

    # Sequential pattern detection
    dependency_chains = self._find_dependency_chains(agents)
    for chain_id, chain in enumerate(dependency_chains):
        if len(chain) >= 3:  # Minimum chain length
            patterns['sequential'].append({
                'id': f'seq_{chain_id}',
                'agents': chain,
                'length': len(chain)
            })

    # Parallel execution detection
    parallel_groups = self._find_parallel_execution(agents)
    for group_id, group in enumerate(parallel_groups):
        if len(group) >= 3:
            patterns['parallel'].append({
                'id': f'parallel_{group_id}',
                'agents': group,
                'overlap_ratio': self._calculate_overlap(group)
            })

    # Hierarchical pattern detection
    hierarchies = self._find_hierarchies(agents)
    for hier_id, hierarchy in enumerate(hierarchies):
        patterns['hierarchical'].append({
            'id': f'hier_{hier_id}',
            'master': hierarchy['master'],
            'workers': hierarchy['workers'],
            'depth': hierarchy['depth']
        })

    return patterns

def _find_dependency_chains(self, agents):
    """Find sequential execution chains through dependency analysis"""
    from collections import defaultdict

    # Build dependency graph
    dep_graph = defaultdict(list)
    agent_map = {a.agent_id: a for a in agents}

    for agent in agents:
        if hasattr(agent, 'dependencies'):
            for dep_id in agent.dependencies:
                if dep_id in agent_map:
                    dep_graph[dep_id].append(agent.agent_id)

    # Find chains using DFS
    chains = []
    visited = set()

    for agent in agents:
        if agent.agent_id not in visited:
            chain = self._dfs_chain(agent.agent_id, dep_graph, visited)
            if len(chain) >= 3:
                chains.append(chain)

    return chains
```

### 1.4 Resource Correlation Analysis

```python
def _resource_correlation(self, agents):
    """
    Identify swarms through shared resource access patterns

    Resources analyzed:
    - File system paths
    - Database connections
    - API endpoints
    - Memory segments
    """
    resource_graph = self._build_resource_graph(agents)

    # Apply community detection on resource graph
    communities = self._detect_communities(resource_graph)

    resource_groups = []
    for comm_id, community in enumerate(communities):
        if len(community) >= self.config.min_swarm_size:
            resource_groups.append({
                'id': f'resource_{comm_id}',
                'agents': community,
                'shared_resources': self._get_shared_resources(community),
                'cohesion': self._calculate_cohesion(community, resource_graph)
            })

    return resource_groups

def _build_resource_graph(self, agents):
    """Build bipartite graph of agents and resources"""
    import networkx as nx

    G = nx.Graph()

    for agent in agents:
        agent_node = f'agent_{agent.agent_id}'
        G.add_node(agent_node, bipartite=0)

        # Add resource connections
        for resource in self._extract_resources(agent):
            resource_node = f'resource_{resource}'
            G.add_node(resource_node, bipartite=1)
            G.add_edge(agent_node, resource_node)

    # Project to agent-agent graph based on shared resources
    agent_nodes = {n for n, d in G.nodes(data=True) if d['bipartite'] == 0}
    agent_projection = nx.bipartite.projected_graph(G, agent_nodes)

    return agent_projection
```

## 2. Swarm Identification Criteria

### 2.1 Classification Rules

```python
class SwarmClassifier:
    """
    Classify detected agent groups into swarm types
    """

    def classify_swarm(self, agent_group):
        """
        Determine swarm type and characteristics

        Returns:
        - SwarmClassification with type, confidence, and metadata
        """
        features = self._extract_features(agent_group)

        # Rule-based classification with confidence scoring
        classifications = []

        # Check for burst swarm
        if features['temporal_density'] > 0.8:
            classifications.append({
                'type': 'burst_swarm',
                'confidence': features['temporal_density'],
                'subtype': self._classify_burst_subtype(features)
            })

        # Check for pipeline swarm
        if features['dependency_ratio'] > 0.6:
            classifications.append({
                'type': 'pipeline_swarm',
                'confidence': features['dependency_ratio'],
                'stages': features['chain_length']
            })

        # Check for parallel swarm
        if features['overlap_ratio'] > 0.7:
            classifications.append({
                'type': 'parallel_swarm',
                'confidence': features['overlap_ratio'],
                'concurrency': features['max_concurrent']
            })

        # Check for hierarchical swarm
        if features['hierarchy_depth'] > 1:
            classifications.append({
                'type': 'hierarchical_swarm',
                'confidence': min(1.0, features['hierarchy_depth'] / 3),
                'levels': features['hierarchy_depth']
            })

        # Select primary classification
        if classifications:
            primary = max(classifications, key=lambda x: x['confidence'])
            return SwarmClassification(
                primary_type=primary['type'],
                confidence=primary['confidence'],
                all_types=classifications,
                features=features
            )

        return SwarmClassification(
            primary_type='unclassified',
            confidence=0.0,
            features=features
        )
```

### 2.2 Swarm Validation Rules

```python
def validate_swarm(self, swarm_candidate):
    """
    Validate that a candidate group meets swarm criteria

    Returns:
    - (is_valid, validation_score, issues)
    """
    issues = []
    score = 1.0

    # Size validation
    if len(swarm_candidate.agents) < self.config.min_swarm_size:
        issues.append('below_minimum_size')
        score *= 0.5

    # Temporal cohesion validation
    time_spread = self._calculate_time_spread(swarm_candidate)
    if time_spread > self.config.max_time_spread:
        issues.append('temporal_dispersion')
        score *= 0.7

    # Activity validation
    if not self._has_meaningful_activity(swarm_candidate):
        issues.append('insufficient_activity')
        score *= 0.6

    # Connectivity validation
    connectivity = self._calculate_connectivity(swarm_candidate)
    if connectivity < self.config.min_connectivity:
        issues.append('low_connectivity')
        score *= 0.8

    is_valid = len(issues) == 0 or score >= self.config.validation_threshold

    return is_valid, score, issues
```

## 3. Icon and Color Assignment Strategy

### 3.1 Visual Encoding System

```python
class SwarmVisualizer:
    """
    Assign visual properties to detected swarms for UI representation
    """

    def __init__(self):
        self.icon_mapping = {
            'burst_swarm': '⚡',
            'pipeline_swarm': '→',
            'parallel_swarm': '⫽',
            'hierarchical_swarm': '🔺',
            'data_processing': '📊',
            'analysis': '🔍',
            'synthesis': '🔗',
            'monitoring': '👁',
            'unclassified': '●'
        }

        self.color_schemes = {
            'burst_swarm': {
                'primary': '#FF6B6B',    # Red for urgency
                'secondary': '#FFE66D',   # Yellow for activity
                'gradient': ['#FF6B6B', '#FFE66D']
            },
            'pipeline_swarm': {
                'primary': '#4ECDC4',    # Teal for flow
                'secondary': '#95E1D3',   # Light teal
                'gradient': ['#4ECDC4', '#95E1D3', '#F3F3F3']
            },
            'parallel_swarm': {
                'primary': '#5C7CFA',    # Blue for parallelism
                'secondary': '#748FFC',   # Light blue
                'gradient': ['#5C7CFA', '#748FFC', '#91A7FF']
            },
            'hierarchical_swarm': {
                'primary': '#8B5CF6',    # Purple for hierarchy
                'secondary': '#A78BFA',   # Light purple
                'gradient': ['#8B5CF6', '#A78BFA', '#C4B5FD']
            }
        }

    def assign_visuals(self, swarm):
        """
        Assign icon and color scheme to a swarm

        Returns:
        - SwarmVisuals object with all visual properties
        """
        swarm_type = swarm.classification.primary_type

        # Get base icon
        icon = self.icon_mapping.get(swarm_type, '●')

        # Enhance icon based on properties
        if swarm.size > 10:
            icon = f'{icon}+'  # Large swarm indicator

        if swarm.confidence < 0.6:
            icon = f'{icon}?'  # Low confidence indicator

        # Get color scheme
        colors = self.color_schemes.get(swarm_type, self._default_colors())

        # Adjust colors based on swarm state
        if swarm.is_active:
            colors = self._brighten_colors(colors)
        elif swarm.is_completed:
            colors = self._dim_colors(colors)

        return SwarmVisuals(
            icon=icon,
            primary_color=colors['primary'],
            secondary_color=colors['secondary'],
            gradient=colors['gradient'],
            opacity=self._calculate_opacity(swarm),
            animation=self._get_animation(swarm_type)
        )

    def _calculate_opacity(self, swarm):
        """Calculate opacity based on confidence and recency"""
        base_opacity = 0.3 + (swarm.confidence * 0.7)

        # Fade older swarms
        age_seconds = time.time() - swarm.last_activity
        if age_seconds > 60:
            fade_factor = max(0.5, 1.0 - (age_seconds / 300))
            base_opacity *= fade_factor

        return base_opacity

    def _get_animation(self, swarm_type):
        """Get animation properties for swarm type"""
        animations = {
            'burst_swarm': 'pulse',
            'pipeline_swarm': 'flow',
            'parallel_swarm': 'wave',
            'hierarchical_swarm': 'expand'
        }
        return animations.get(swarm_type, 'none')
```

### 3.2 Dynamic Color Assignment

```python
class DynamicColorAssigner:
    """
    Dynamically assign colors to avoid conflicts and maintain consistency
    """

    def __init__(self):
        self.color_pool = self._generate_color_pool()
        self.assigned_colors = {}
        self.color_history = deque(maxlen=100)

    def assign_color(self, swarm_id, swarm_type):
        """
        Assign unique color to swarm, maintaining consistency
        """
        # Check if already assigned
        if swarm_id in self.assigned_colors:
            return self.assigned_colors[swarm_id]

        # Get base color for type
        base_color = self._get_base_color(swarm_type)

        # Find available variation
        color = self._find_unique_variation(base_color)

        # Record assignment
        self.assigned_colors[swarm_id] = color
        self.color_history.append((swarm_id, color))

        return color

    def _find_unique_variation(self, base_color):
        """Find unique color variation not currently in use"""
        import colorsys

        h, s, v = colorsys.rgb_to_hsv(*self._hex_to_rgb(base_color))

        # Try variations
        for offset in range(0, 360, 15):
            new_h = (h + offset/360) % 1.0

            # Vary saturation and value slightly
            for s_var in [0, -0.1, 0.1]:
                for v_var in [0, -0.1, 0.1]:
                    new_s = max(0.3, min(1.0, s + s_var))
                    new_v = max(0.5, min(1.0, v + v_var))

                    new_color = self._hsv_to_hex(new_h, new_s, new_v)

                    if not self._color_in_use(new_color):
                        return new_color

        # Fallback to base color
        return base_color
```

## 4. Performance Optimization Strategies

### 4.1 Indexing and Caching

```python
class PerformanceOptimizer:
    """
    Performance optimizations for swarm detection
    """

    def __init__(self):
        self.temporal_index = self._build_temporal_index()
        self.spatial_index = self._build_spatial_index()
        self.result_cache = LRUCache(maxsize=1000)
        self.incremental_state = {}

    def _build_temporal_index(self):
        """Build B-tree index for temporal queries"""
        from BTrees.OOBTree import OOBTree
        return OOBTree()

    def _build_spatial_index(self):
        """Build R-tree for spatial/resource queries"""
        from rtree import index
        return index.Index()

    def optimized_query(self, query_params):
        """
        Optimized query using indices and cache

        Performance characteristics:
        - Cache hit: O(1)
        - Temporal query: O(log n)
        - Spatial query: O(log n)
        - Full scan: O(n)
        """
        # Check cache
        cache_key = self._compute_cache_key(query_params)
        if cache_key in self.result_cache:
            return self.result_cache[cache_key]

        # Use appropriate index
        if query_params.query_type == 'temporal':
            result = self._temporal_query(query_params)
        elif query_params.query_type == 'spatial':
            result = self._spatial_query(query_params)
        else:
            result = self._full_scan(query_params)

        # Cache result
        self.result_cache[cache_key] = result
        return result
```

### 4.2 Incremental Updates

```python
def incremental_swarm_update(self, new_agent, existing_swarms):
    """
    Incrementally update swarm detection with new agent

    Time Complexity: O(k) where k is number of active swarms
    Space Complexity: O(1)
    """
    updated = False
    affected_swarms = []

    # Check temporal proximity to existing swarms
    for swarm_id, swarm in existing_swarms.items():
        if self._agent_fits_swarm_temporal(new_agent, swarm):
            swarm.agents.append(new_agent)
            swarm.last_update = new_agent.timestamp
            affected_swarms.append(swarm_id)
            updated = True

    # Check if forms new swarm with recent unassigned agents
    if not updated:
        recent_agents = self._get_recent_unassigned(new_agent.timestamp)
        if len(recent_agents) >= self.config.min_swarm_size - 1:
            new_swarm = self._create_swarm(
                [new_agent] + recent_agents,
                swarm_type='incremental'
            )
            existing_swarms[new_swarm.id] = new_swarm
            affected_swarms.append(new_swarm.id)

    # Revalidate affected swarms
    for swarm_id in affected_swarms:
        is_valid, score, _ = self.validate_swarm(existing_swarms[swarm_id])
        if not is_valid:
            self._dissolve_swarm(swarm_id, existing_swarms)

    return existing_swarms
```

### 4.3 Batch Processing Optimizations

```python
def batch_process_optimized(self, agents, batch_size=1000):
    """
    Process large agent sets in optimized batches

    Optimizations:
    - Parallel processing for independent batches
    - Streaming aggregation
    - Memory-efficient processing
    """
    from concurrent.futures import ThreadPoolExecutor
    import numpy as np

    # Sort agents by timestamp for better cache locality
    agents_sorted = sorted(agents, key=lambda a: a.start_time)

    # Create batches
    batches = [
        agents_sorted[i:i+batch_size]
        for i in range(0, len(agents_sorted), batch_size)
    ]

    # Process batches in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        batch_results = list(executor.map(self._process_batch, batches))

    # Merge batch results
    merged_swarms = self._merge_batch_results(batch_results)

    # Post-processing: merge cross-batch swarms
    final_swarms = self._merge_cross_batch_swarms(merged_swarms)

    return final_swarms

def _process_batch(self, batch):
    """Process single batch with local optimizations"""
    # Use vectorized operations where possible
    timestamps = np.array([a.start_time for a in batch])

    # Fast clustering using optimized DBSCAN
    clusters = self._fast_dbscan(timestamps.reshape(-1, 1))

    # Build swarms from clusters
    swarms = []
    for cluster_id, cluster_indices in enumerate(clusters):
        if len(cluster_indices) >= self.config.min_swarm_size:
            swarm_agents = [batch[i] for i in cluster_indices]
            swarms.append(self._create_swarm(swarm_agents))

    return swarms
```

## 5. Edge Case Handling

### 5.1 Boundary Conditions

```python
class EdgeCaseHandler:
    """
    Handle edge cases in swarm detection
    """

    def handle_edge_cases(self, agents, swarms):
        """
        Process and resolve edge cases

        Edge cases handled:
        - Overlapping swarms
        - Singleton agents
        - Temporal boundaries
        - Resource conflicts
        - Circular dependencies
        """

        # Handle overlapping swarms
        swarms = self._resolve_overlaps(swarms)

        # Handle singleton agents
        singletons = self._identify_singletons(agents, swarms)
        swarms = self._process_singletons(singletons, swarms)

        # Handle temporal boundaries
        swarms = self._handle_temporal_boundaries(swarms)

        # Handle resource conflicts
        swarms = self._resolve_resource_conflicts(swarms)

        # Handle circular dependencies
        swarms = self._break_circular_dependencies(swarms)

        return swarms

    def _resolve_overlaps(self, swarms):
        """Resolve agents belonging to multiple swarms"""
        agent_memberships = defaultdict(list)

        # Find overlapping memberships
        for swarm in swarms:
            for agent in swarm.agents:
                agent_memberships[agent.agent_id].append(swarm.id)

        # Resolve conflicts
        for agent_id, swarm_ids in agent_memberships.items():
            if len(swarm_ids) > 1:
                # Assign to swarm with highest confidence
                best_swarm = max(
                    swarm_ids,
                    key=lambda sid: self._get_swarm_confidence(sid, swarms)
                )

                # Remove from other swarms
                for swarm_id in swarm_ids:
                    if swarm_id != best_swarm:
                        self._remove_agent_from_swarm(agent_id, swarm_id, swarms)

        return swarms

    def _handle_temporal_boundaries(self, swarms):
        """Handle swarms at time window boundaries"""
        for swarm in swarms:
            # Check if swarm spans boundary
            if self._spans_boundary(swarm):
                # Split or extend based on activity pattern
                if self._should_split(swarm):
                    new_swarms = self._split_swarm(swarm)
                    swarms.extend(new_swarms)
                    swarms.remove(swarm)
                else:
                    swarm = self._extend_swarm(swarm)

        return swarms
```

### 5.2 Error Recovery

```python
def recover_from_errors(self, error_context):
    """
    Graceful error recovery strategies

    Strategies:
    - Fallback to simpler algorithm
    - Partial result return
    - State reconstruction
    - Diagnostic logging
    """
    try:
        if error_context.error_type == 'memory_error':
            # Switch to streaming mode
            return self._streaming_fallback(error_context.agents)

        elif error_context.error_type == 'timeout':
            # Return partial results
            return self._partial_results(error_context.partial_swarms)

        elif error_context.error_type == 'corruption':
            # Attempt state reconstruction
            return self._reconstruct_state(error_context.last_known_good)

        else:
            # Log and return empty result
            self._log_error(error_context)
            return SwarmDetectionResult(swarms=[], error=True)

    except Exception as e:
        # Ultimate fallback
        return SwarmDetectionResult(
            swarms=[],
            error=True,
            error_message=str(e)
        )
```

## 6. Algorithm Complexity Analysis

### 6.1 Time Complexity

| Operation | Average Case | Worst Case | Best Case |
|-----------|-------------|------------|-----------|
| Temporal Clustering | O(n log n) | O(n²) | O(n) |
| Behavioral Analysis | O(n) | O(n²) | O(n) |
| Resource Correlation | O(n + e) | O(n²) | O(n) |
| Merge & Score | O(k²) | O(n²) | O(k) |
| **Overall** | **O(n log n)** | **O(n²)** | **O(n)** |

Where:
- n = number of agents
- e = number of resource edges
- k = number of detected swarms

### 6.2 Space Complexity

| Component | Space Usage |
|-----------|------------|
| Agent Index | O(n) |
| Temporal Index | O(n) |
| Resource Graph | O(n + e) |
| Swarm Cache | O(k) |
| **Total** | **O(n + e)** |

### 6.3 Optimization Impact

| Optimization | Performance Gain | Trade-off |
|--------------|-----------------|-----------|
| KD-tree Index | 10-100x for queries | O(n) build time |
| Caching | 100-1000x for hits | O(k) memory |
| Incremental Updates | 10-50x for streaming | Complexity |
| Parallel Processing | 2-4x on multi-core | Coordination overhead |

## 7. Implementation Checklist

- [ ] Core detection engine implementation
- [ ] Temporal clustering with KD-tree
- [ ] Behavioral pattern detectors
- [ ] Resource correlation analysis
- [ ] Swarm classification system
- [ ] Visual assignment module
- [ ] Performance optimizations
- [ ] Edge case handlers
- [ ] Error recovery mechanisms
- [ ] Unit tests for all components
- [ ] Integration tests with orchestrator
- [ ] Performance benchmarks
- [ ] Documentation and examples

## 8. Usage Example

```python
# Initialize detection engine
config = SwarmConfig(
    temporal_epsilon=5.0,
    min_swarm_size=3,
    burst_threshold=5,
    validation_threshold=0.6
)

engine = SwarmDetectionEngine(config)
visualizer = SwarmVisualizer()

# Detect swarms in batch mode
agents = load_agents_from_orchestrator()
result = engine.detect_swarms(agents, mode='batch')

# Assign visuals
for swarm in result.swarms:
    visuals = visualizer.assign_visuals(swarm)
    swarm.set_visuals(visuals)

# Output results
print(f"Detected {len(result.swarms)} swarms")
for swarm in result.swarms:
    print(f"  {swarm.icon} Swarm {swarm.id}:")
    print(f"    Type: {swarm.classification.primary_type}")
    print(f"    Size: {len(swarm.agents)} agents")
    print(f"    Confidence: {swarm.confidence:.2f}")
    print(f"    Color: {swarm.visuals.primary_color}")
```

## Conclusion

This algorithm specification provides a robust, performant, and extensible swarm detection system. The multi-stage approach ensures high accuracy while maintaining O(n log n) average-case performance. The visual encoding system provides intuitive representation of swarm types and states, while comprehensive edge case handling ensures reliability in production environments.
