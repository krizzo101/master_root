"""
Swarm Detection System for Agent Orchestration

This module implements advanced swarm detection algorithms for identifying
coordinated agent groups through temporal clustering, behavioral analysis,
and resource correlation patterns.
"""

import time
import numpy as np
from typing import List, Dict, Tuple, Optional, Set, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
from scipy.spatial import KDTree
import networkx as nx


# ============================================================================
# Data Classes and Enums
# ============================================================================

class SwarmType(Enum):
    """Enumeration of swarm types"""
    BURST = "burst_swarm"
    PIPELINE = "pipeline_swarm"
    PARALLEL = "parallel_swarm"
    HIERARCHICAL = "hierarchical_swarm"
    DATA_PROCESSING = "data_processing"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    MONITORING = "monitoring"
    UNCLASSIFIED = "unclassified"


@dataclass
class SwarmConfig:
    """Configuration parameters for swarm detection"""
    temporal_epsilon: float = 5.0  # seconds
    min_swarm_size: int = 3
    burst_window: float = 1.0  # seconds
    burst_threshold: int = 5
    max_time_spread: float = 30.0  # seconds
    min_connectivity: float = 0.3
    validation_threshold: float = 0.6
    cache_size: int = 1000


@dataclass
class Agent:
    """Agent representation for swarm detection"""
    agent_id: str
    start_time: float
    end_time: Optional[float] = None
    priority_score: float = 0.5
    dependencies: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    task_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_active(self) -> bool:
        return self.end_time is None
    
    @property
    def duration(self) -> float:
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time


@dataclass
class SwarmClassification:
    """Classification result for a detected swarm"""
    primary_type: SwarmType
    confidence: float
    all_types: List[Dict[str, Any]] = field(default_factory=list)
    features: Dict[str, float] = field(default_factory=dict)


@dataclass
class SwarmVisuals:
    """Visual properties for swarm representation"""
    icon: str
    primary_color: str
    secondary_color: str
    gradient: List[str]
    opacity: float
    animation: str


@dataclass
class Swarm:
    """Detected swarm with all properties"""
    id: str
    agents: List[Agent]
    classification: SwarmClassification
    confidence: float
    centroid: Optional[Tuple[float, ...]] = None
    density: float = 0.0
    last_activity: float = field(default_factory=time.time)
    visuals: Optional[SwarmVisuals] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def size(self) -> int:
        return len(self.agents)
    
    @property
    def is_active(self) -> bool:
        return any(agent.is_active for agent in self.agents)
    
    @property
    def is_completed(self) -> bool:
        return all(not agent.is_active for agent in self.agents)


@dataclass
class SwarmDetectionResult:
    """Result of swarm detection process"""
    swarms: List[Swarm]
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    statistics: Dict[str, Any] = field(default_factory=dict)
    error: bool = False
    error_message: Optional[str] = None


# ============================================================================
# Core Detection Engine
# ============================================================================

class SwarmDetectionEngine:
    """
    High-performance swarm detection engine using optimized DBSCAN variant
    with incremental updates and intelligent caching.
    """
    
    def __init__(self, config: Optional[SwarmConfig] = None):
        self.config = config or SwarmConfig()
        self.active_swarms: Dict[str, Swarm] = {}
        self.swarm_counter = 0
        self.cache: Dict[str, Any] = {}
        self.stats = SwarmStatistics()
    
    def detect_swarms(self, agents: List[Agent], mode: str = 'batch') -> SwarmDetectionResult:
        """
        Main entry point for swarm detection
        
        Parameters:
        - agents: List of agent objects
        - mode: 'batch', 'streaming', or 'incremental'
        
        Returns:
        - SwarmDetectionResult with identified swarms
        """
        try:
            if mode == 'batch':
                return self._batch_detection(agents)
            elif mode == 'streaming':
                return self._streaming_detection(agents)
            else:
                return self._incremental_detection(agents)
        except Exception as e:
            return SwarmDetectionResult(
                swarms=[],
                error=True,
                error_message=str(e)
            )
    
    def _batch_detection(self, agents: List[Agent]) -> SwarmDetectionResult:
        """Optimized batch detection for complete agent sets"""
        
        if not agents:
            return SwarmDetectionResult(swarms=[])
        
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
        
        # Stage 5: Classify swarms
        classifier = SwarmClassifier()
        for swarm in final_swarms:
            swarm.classification = classifier.classify_swarm(swarm)
        
        # Stage 6: Validate swarms
        validated_swarms = []
        for swarm in final_swarms:
            is_valid, score, _ = self.validate_swarm(swarm)
            if is_valid:
                swarm.confidence = score
                validated_swarms.append(swarm)
        
        return SwarmDetectionResult(
            swarms=validated_swarms,
            confidence_scores={s.id: s.confidence for s in validated_swarms},
            statistics=self.stats.compute()
        )
    
    def _temporal_clustering(self, agents: List[Agent]) -> List[Dict[str, Any]]:
        """
        Fast temporal clustering using optimized DBSCAN with KD-tree indexing
        
        Time Complexity: O(n log n) average case
        Space Complexity: O(n)
        """
        if not agents:
            return []
        
        # Convert timestamps to numerical features
        timestamps = np.array([[
            agent.start_time,
            agent.priority_score * 10,  # Scale priority for clustering
        ] for agent in agents])
        
        # Normalize features for balanced clustering
        timestamps_norm = self._normalize_features(timestamps)
        
        # Build KD-tree for efficient neighbor queries
        tree = KDTree(timestamps_norm)
        
        # DBSCAN parameters
        eps = 0.5  # Increased epsilon for better clustering
        min_pts = self.config.min_swarm_size
        
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
                cluster_agents = [agents[idx] for idx in cluster]
                clusters.append({
                    'id': f'temporal_{cluster_id}',
                    'agents': cluster_agents,
                    'type': 'temporal',
                    'centroid': self._compute_centroid(cluster, timestamps),
                    'density': len(cluster) / (2 * eps)
                })
                cluster_id += 1
        
        return clusters
    
    def _expand_cluster(self, seed_idx: int, neighbors: List[int], tree: KDTree,
                       data: np.ndarray, visited: np.ndarray, eps: float,
                       min_pts: int) -> List[int]:
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
    
    def _behavioral_analysis(self, agents: List[Agent]) -> Dict[str, List[Dict[str, Any]]]:
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
        window_size = self.config.burst_window
        time_buckets = self._create_time_buckets(agents, window_size)
        
        for timestamp, bucket_agents in time_buckets.items():
            if len(bucket_agents) >= self.config.burst_threshold:
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
    
    def _resource_correlation(self, agents: List[Agent]) -> List[Dict[str, Any]]:
        """
        Identify swarms through shared resource access patterns
        
        Resources analyzed:
        - File system paths
        - Database connections
        - API endpoints
        - Memory segments
        """
        if not agents:
            return []
        
        resource_graph = self._build_resource_graph(agents)
        
        # Apply community detection on resource graph
        if resource_graph.number_of_nodes() == 0:
            return []
        
        communities = self._detect_communities(resource_graph)
        
        resource_groups = []
        for comm_id, community in enumerate(communities):
            if len(community) >= self.config.min_swarm_size:
                community_agents = [a for a in agents if f'agent_{a.agent_id}' in community]
                if community_agents:
                    resource_groups.append({
                        'id': f'resource_{comm_id}',
                        'agents': community_agents,
                        'shared_resources': self._get_shared_resources(community_agents),
                        'cohesion': self._calculate_cohesion(community, resource_graph)
                    })
        
        return resource_groups
    
    def _merge_and_score(self, temporal_clusters: List[Dict],
                        behavioral_groups: Dict[str, List[Dict]],
                        resource_groups: List[Dict]) -> List[Swarm]:
        """Merge different detection results and score swarms"""
        merged_swarms = []
        agent_assignments = defaultdict(list)
        
        # Process temporal clusters
        for cluster in temporal_clusters:
            swarm_id = f"swarm_{self.swarm_counter}"
            self.swarm_counter += 1
            
            swarm = Swarm(
                id=swarm_id,
                agents=cluster['agents'],
                classification=SwarmClassification(
                    primary_type=SwarmType.UNCLASSIFIED,
                    confidence=0.7
                ),
                confidence=0.7,
                centroid=cluster.get('centroid'),
                density=cluster.get('density', 0.0)
            )
            merged_swarms.append(swarm)
            
            for agent in cluster['agents']:
                agent_assignments[agent.agent_id].append(swarm_id)
        
        # Process behavioral patterns
        for pattern_type, groups in behavioral_groups.items():
            for group in groups:
                # Get agents from group
                group_agents = group.get('agents', [])
                if not group_agents:
                    continue
                    
                # Check if agents already in swarm
                existing_swarm = self._find_existing_swarm(
                    group_agents, merged_swarms, agent_assignments
                )
                
                if existing_swarm:
                    # Enhance existing swarm
                    existing_swarm.confidence = min(1.0, existing_swarm.confidence + 0.1)
                    existing_swarm.metadata[pattern_type] = True
                else:
                    # Create new swarm
                    swarm_id = f"swarm_{self.swarm_counter}"
                    self.swarm_counter += 1
                    
                    swarm = Swarm(
                        id=swarm_id,
                        agents=group_agents,
                        classification=SwarmClassification(
                            primary_type=self._pattern_to_type(pattern_type),
                            confidence=0.8
                        ),
                        confidence=0.8,
                        metadata={pattern_type: True}
                    )
                    merged_swarms.append(swarm)
        
        return merged_swarms
    
    def validate_swarm(self, swarm: Swarm) -> Tuple[bool, float, List[str]]:
        """
        Validate that a candidate group meets swarm criteria
        
        Returns:
        - (is_valid, validation_score, issues)
        """
        issues = []
        score = 1.0
        
        # Size validation
        if len(swarm.agents) < self.config.min_swarm_size:
            issues.append('below_minimum_size')
            score *= 0.5
        
        # Temporal cohesion validation
        time_spread = self._calculate_time_spread(swarm)
        if time_spread > self.config.max_time_spread:
            issues.append('temporal_dispersion')
            score *= 0.7
        
        # Activity validation
        if not self._has_meaningful_activity(swarm):
            issues.append('insufficient_activity')
            score *= 0.6
        
        is_valid = len(issues) == 0 or score >= self.config.validation_threshold
        
        return is_valid, score, issues
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def _normalize_features(self, features: np.ndarray) -> np.ndarray:
        """Normalize features for clustering"""
        if features.size == 0:
            return features
        
        min_vals = features.min(axis=0)
        max_vals = features.max(axis=0)
        range_vals = max_vals - min_vals
        
        # Avoid division by zero
        range_vals[range_vals == 0] = 1.0
        
        return (features - min_vals) / range_vals
    
    def _compute_centroid(self, cluster_indices: List[int],
                         features: np.ndarray) -> Tuple[float, ...]:
        """Compute cluster centroid"""
        if not cluster_indices:
            return tuple()
        
        cluster_features = features[cluster_indices]
        centroid = cluster_features.mean(axis=0)
        return tuple(centroid)
    
    def _create_time_buckets(self, agents: List[Agent],
                           window_size: float) -> Dict[float, List[Agent]]:
        """Create time buckets for burst detection"""
        buckets = defaultdict(list)
        
        for agent in agents:
            bucket_key = int(agent.start_time / window_size) * window_size
            buckets[bucket_key].append(agent)
        
        return dict(buckets)
    
    def _find_dependency_chains(self, agents: List[Agent]) -> List[List[Agent]]:
        """Find sequential execution chains through dependency analysis"""
        # Build dependency graph
        dep_graph = defaultdict(list)
        agent_map = {a.agent_id: a for a in agents}
        
        for agent in agents:
            for dep_id in agent.dependencies:
                if dep_id in agent_map:
                    dep_graph[dep_id].append(agent.agent_id)
        
        # Find chains using DFS
        chains = []
        visited = set()
        
        for agent in agents:
            if agent.agent_id not in visited:
                chain = self._dfs_chain(agent.agent_id, dep_graph, agent_map, visited)
                if len(chain) >= 3:
                    chains.append(chain)
        
        return chains
    
    def _dfs_chain(self, start_id: str, dep_graph: Dict[str, List[str]],
                  agent_map: Dict[str, Agent], visited: Set[str]) -> List[Agent]:
        """DFS to find dependency chain"""
        chain = []
        stack = [start_id]
        
        while stack:
            agent_id = stack.pop()
            if agent_id in visited:
                continue
            
            visited.add(agent_id)
            if agent_id in agent_map:
                chain.append(agent_map[agent_id])
            
            # Add dependents to stack
            for dependent in dep_graph.get(agent_id, []):
                if dependent not in visited:
                    stack.append(dependent)
        
        return chain
    
    def _find_parallel_execution(self, agents: List[Agent]) -> List[List[Agent]]:
        """Find groups of agents executing in parallel"""
        parallel_groups = []
        
        # Sort agents by start time
        sorted_agents = sorted(agents, key=lambda a: a.start_time)
        
        # Find overlapping execution windows
        current_group = []
        current_end = 0
        
        for agent in sorted_agents:
            if agent.start_time <= current_end:
                # Overlaps with current group
                current_group.append(agent)
                if agent.end_time:
                    current_end = max(current_end, agent.end_time)
            else:
                # Start new group
                if len(current_group) >= 3:
                    parallel_groups.append(current_group)
                current_group = [agent]
                current_end = agent.end_time or (agent.start_time + 1.0)
        
        # Add last group
        if len(current_group) >= 3:
            parallel_groups.append(current_group)
        
        return parallel_groups
    
    def _calculate_overlap(self, agents: List[Agent]) -> float:
        """Calculate execution overlap ratio for agent group"""
        if len(agents) < 2:
            return 0.0
        
        # Find common execution window
        latest_start = max(a.start_time for a in agents)
        earliest_end = min(a.end_time or float('inf') for a in agents)
        
        if earliest_end == float('inf'):
            # Some agents still running
            overlap_duration = time.time() - latest_start
        else:
            overlap_duration = max(0, earliest_end - latest_start)
        
        # Calculate average duration
        avg_duration = sum(a.duration for a in agents) / len(agents)
        
        return min(1.0, overlap_duration / avg_duration) if avg_duration > 0 else 0.0
    
    def _find_hierarchies(self, agents: List[Agent]) -> List[Dict[str, Any]]:
        """Find hierarchical master-worker patterns"""
        hierarchies = []
        
        # Group agents by task type or other criteria
        task_groups = defaultdict(list)
        for agent in agents:
            if agent.task_type:
                task_groups[agent.task_type].append(agent)
        
        # Identify potential hierarchies
        for task_type, group in task_groups.items():
            if len(group) >= 4:  # Need at least 1 master + 3 workers
                # Find potential master (earliest, highest priority)
                master = min(group, key=lambda a: (a.start_time, -a.priority_score))
                workers = [a for a in group if a != master]
                
                if workers:
                    hierarchies.append({
                        'master': master,
                        'workers': workers,
                        'depth': 2  # Simple two-level hierarchy
                    })
        
        return hierarchies
    
    def _build_resource_graph(self, agents: List[Agent]) -> nx.Graph:
        """Build bipartite graph of agents and resources"""
        G = nx.Graph()
        
        for agent in agents:
            agent_node = f'agent_{agent.agent_id}'
            G.add_node(agent_node, bipartite=0)
            
            # Add resource connections
            for resource in agent.resources:
                resource_node = f'resource_{resource}'
                G.add_node(resource_node, bipartite=1)
                G.add_edge(agent_node, resource_node)
        
        # Project to agent-agent graph based on shared resources
        agent_nodes = {n for n, d in G.nodes(data=True) if d.get('bipartite') == 0}
        if agent_nodes:
            agent_projection = nx.bipartite.projected_graph(G, agent_nodes)
            return agent_projection
        
        return nx.Graph()
    
    def _detect_communities(self, graph: nx.Graph) -> List[Set[str]]:
        """Detect communities in resource graph"""
        if graph.number_of_nodes() == 0:
            return []
        
        # Use Louvain method for community detection
        try:
            import networkx.algorithms.community as nx_comm
            communities = list(nx_comm.louvain_communities(graph))
            return communities
        except:
            # Fallback to connected components
            return list(nx.connected_components(graph))
    
    def _get_shared_resources(self, agents: List[Agent]) -> List[str]:
        """Get resources shared by agent group"""
        if not agents:
            return []
        
        resource_counts = defaultdict(int)
        for agent in agents:
            for resource in agent.resources:
                resource_counts[resource] += 1
        
        # Return resources shared by at least 2 agents
        shared = [r for r, count in resource_counts.items() if count >= 2]
        return shared
    
    def _calculate_cohesion(self, community: Set[str], graph: nx.Graph) -> float:
        """Calculate cohesion score for community"""
        if len(community) < 2:
            return 0.0
        
        # Calculate edge density within community
        subgraph = graph.subgraph(community)
        max_edges = len(community) * (len(community) - 1) / 2
        actual_edges = subgraph.number_of_edges()
        
        return actual_edges / max_edges if max_edges > 0 else 0.0
    
    def _find_existing_swarm(self, agents: List[Agent], swarms: List[Swarm],
                           assignments: Dict[str, List[str]]) -> Optional[Swarm]:
        """Find if agents belong to existing swarm"""
        if not isinstance(agents, list):
            return None
            
        agent_ids = {a.agent_id for a in agents if hasattr(a, 'agent_id')}
        
        for swarm in swarms:
            swarm_agent_ids = {a.agent_id for a in swarm.agents}
            overlap = len(agent_ids & swarm_agent_ids)
            
            if overlap >= len(agent_ids) * 0.5:  # 50% overlap
                return swarm
        
        return None
    
    def _pattern_to_type(self, pattern: str) -> SwarmType:
        """Convert pattern name to swarm type"""
        mapping = {
            'burst': SwarmType.BURST,
            'sequential': SwarmType.PIPELINE,
            'parallel': SwarmType.PARALLEL,
            'hierarchical': SwarmType.HIERARCHICAL
        }
        return mapping.get(pattern, SwarmType.UNCLASSIFIED)
    
    def _calculate_time_spread(self, swarm: Swarm) -> float:
        """Calculate time spread of swarm agents"""
        if not swarm.agents:
            return 0.0
        
        start_times = [a.start_time for a in swarm.agents]
        return max(start_times) - min(start_times)
    
    def _has_meaningful_activity(self, swarm: Swarm) -> bool:
        """Check if swarm has meaningful activity"""
        # Check if agents have resources or dependencies
        has_resources = any(a.resources for a in swarm.agents)
        has_dependencies = any(a.dependencies for a in swarm.agents)
        
        return has_resources or has_dependencies or len(swarm.agents) >= 5
    
    def _streaming_detection(self, agents: List[Agent]) -> SwarmDetectionResult:
        """Streaming detection for continuous agent streams"""
        # Simplified streaming implementation
        return self._batch_detection(agents)
    
    def _incremental_detection(self, agents: List[Agent]) -> SwarmDetectionResult:
        """Incremental detection for updating existing swarms"""
        # Simplified incremental implementation
        return self._batch_detection(agents)


# ============================================================================
# Swarm Classification
# ============================================================================

class SwarmClassifier:
    """Classify detected agent groups into swarm types"""
    
    def classify_swarm(self, swarm: Swarm) -> SwarmClassification:
        """
        Determine swarm type and characteristics
        
        Returns:
        - SwarmClassification with type, confidence, and metadata
        """
        features = self._extract_features(swarm)
        
        # Rule-based classification with confidence scoring
        classifications = []
        
        # Check for burst swarm
        if features['temporal_density'] > 0.8:
            classifications.append({
                'type': SwarmType.BURST,
                'confidence': features['temporal_density'],
                'subtype': 'high_intensity'
            })
        
        # Check for pipeline swarm
        if features['dependency_ratio'] > 0.6:
            classifications.append({
                'type': SwarmType.PIPELINE,
                'confidence': features['dependency_ratio'],
                'stages': features.get('chain_length', 0)
            })
        
        # Check for parallel swarm
        if features['overlap_ratio'] > 0.7:
            classifications.append({
                'type': SwarmType.PARALLEL,
                'confidence': features['overlap_ratio'],
                'concurrency': features.get('max_concurrent', 0)
            })
        
        # Check for hierarchical swarm
        if features['hierarchy_depth'] > 1:
            classifications.append({
                'type': SwarmType.HIERARCHICAL,
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
            primary_type=SwarmType.UNCLASSIFIED,
            confidence=0.0,
            features=features
        )
    
    def _extract_features(self, swarm: Swarm) -> Dict[str, float]:
        """Extract classification features from swarm"""
        features = {}
        
        # Temporal features
        if swarm.agents:
            time_spread = max(a.start_time for a in swarm.agents) - min(a.start_time for a in swarm.agents)
            features['temporal_density'] = len(swarm.agents) / (time_spread + 1.0)
        else:
            features['temporal_density'] = 0.0
        
        # Dependency features
        total_deps = sum(len(a.dependencies) for a in swarm.agents)
        features['dependency_ratio'] = total_deps / max(1, len(swarm.agents))
        
        # Overlap features
        features['overlap_ratio'] = self._calculate_overlap_ratio(swarm.agents)
        
        # Hierarchy features
        features['hierarchy_depth'] = self._calculate_hierarchy_depth(swarm.agents)
        
        return features
    
    def _calculate_overlap_ratio(self, agents: List[Agent]) -> float:
        """Calculate execution overlap for classification"""
        if len(agents) < 2:
            return 0.0
        
        # Simplified overlap calculation
        overlaps = 0
        for i in range(len(agents)):
            for j in range(i + 1, len(agents)):
                if self._agents_overlap(agents[i], agents[j]):
                    overlaps += 1
        
        max_overlaps = len(agents) * (len(agents) - 1) / 2
        return overlaps / max_overlaps if max_overlaps > 0 else 0.0
    
    def _agents_overlap(self, a1: Agent, a2: Agent) -> bool:
        """Check if two agents have overlapping execution"""
        end1 = a1.end_time or time.time()
        end2 = a2.end_time or time.time()
        
        return not (end1 < a2.start_time or end2 < a1.start_time)
    
    def _calculate_hierarchy_depth(self, agents: List[Agent]) -> int:
        """Calculate hierarchy depth for classification"""
        if not agents:
            return 0
        
        # Simple heuristic based on priority scores
        priority_levels = len(set(a.priority_score for a in agents))
        return min(priority_levels, 3)  # Cap at 3 levels


# ============================================================================
# Visual System
# ============================================================================

class SwarmVisualizer:
    """Assign visual properties to detected swarms for UI representation"""
    
    def __init__(self):
        self.icon_mapping = {
            SwarmType.BURST: '⚡',
            SwarmType.PIPELINE: '→',
            SwarmType.PARALLEL: '⫽',
            SwarmType.HIERARCHICAL: '🔺',
            SwarmType.DATA_PROCESSING: '📊',
            SwarmType.ANALYSIS: '🔍',
            SwarmType.SYNTHESIS: '🔗',
            SwarmType.MONITORING: '👁',
            SwarmType.UNCLASSIFIED: '●'
        }
        
        self.color_schemes = {
            SwarmType.BURST: {
                'primary': '#FF6B6B',    # Red for urgency
                'secondary': '#FFE66D',   # Yellow for activity
                'gradient': ['#FF6B6B', '#FFE66D']
            },
            SwarmType.PIPELINE: {
                'primary': '#4ECDC4',    # Teal for flow
                'secondary': '#95E1D3',   # Light teal
                'gradient': ['#4ECDC4', '#95E1D3', '#F3F3F3']
            },
            SwarmType.PARALLEL: {
                'primary': '#5C7CFA',    # Blue for parallelism
                'secondary': '#748FFC',   # Light blue
                'gradient': ['#5C7CFA', '#748FFC', '#91A7FF']
            },
            SwarmType.HIERARCHICAL: {
                'primary': '#8B5CF6',    # Purple for hierarchy
                'secondary': '#A78BFA',   # Light purple
                'gradient': ['#8B5CF6', '#A78BFA', '#C4B5FD']
            }
        }
        
        self.color_assigner = DynamicColorAssigner()
    
    def assign_visuals(self, swarm: Swarm) -> SwarmVisuals:
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
        
        # Get unique color variation
        primary_color = self.color_assigner.assign_color(swarm.id, swarm_type)
        
        # Adjust colors based on swarm state
        if swarm.is_active:
            colors = self._brighten_colors(colors)
        elif swarm.is_completed:
            colors = self._dim_colors(colors)
        
        return SwarmVisuals(
            icon=icon,
            primary_color=primary_color or colors['primary'],
            secondary_color=colors['secondary'],
            gradient=colors['gradient'],
            opacity=self._calculate_opacity(swarm),
            animation=self._get_animation(swarm_type)
        )
    
    def format_swarm_display(self, swarm: Swarm) -> str:
        """Format swarm for terminal display"""
        if not swarm.visuals:
            swarm.visuals = self.assign_visuals(swarm)
        
        v = swarm.visuals
        
        # Build display string
        display_parts = [
            f"{v.icon}",
            f"[{swarm.classification.primary_type.value}]",
            f"({swarm.size} agents)",
            f"conf:{swarm.confidence:.0%}"
        ]
        
        if swarm.is_active:
            display_parts.append("🟢")
        elif swarm.is_completed:
            display_parts.append("⚫")
        
        return " ".join(display_parts)
    
    def _default_colors(self) -> Dict[str, Any]:
        """Default color scheme for unclassified swarms"""
        return {
            'primary': '#6B7280',
            'secondary': '#9CA3AF',
            'gradient': ['#6B7280', '#9CA3AF', '#D1D5DB']
        }
    
    def _brighten_colors(self, colors: Dict[str, Any]) -> Dict[str, Any]:
        """Brighten colors for active swarms"""
        # Simple brightening - in production, use proper color manipulation
        return colors
    
    def _dim_colors(self, colors: Dict[str, Any]) -> Dict[str, Any]:
        """Dim colors for completed swarms"""
        # Simple dimming - in production, use proper color manipulation
        return colors
    
    def _calculate_opacity(self, swarm: Swarm) -> float:
        """Calculate opacity based on confidence and recency"""
        base_opacity = 0.3 + (swarm.confidence * 0.7)
        
        # Fade older swarms
        age_seconds = time.time() - swarm.last_activity
        if age_seconds > 60:
            fade_factor = max(0.5, 1.0 - (age_seconds / 300))
            base_opacity *= fade_factor
        
        return base_opacity
    
    def _get_animation(self, swarm_type: SwarmType) -> str:
        """Get animation properties for swarm type"""
        animations = {
            SwarmType.BURST: 'pulse',
            SwarmType.PIPELINE: 'flow',
            SwarmType.PARALLEL: 'wave',
            SwarmType.HIERARCHICAL: 'expand'
        }
        return animations.get(swarm_type, 'none')


# ============================================================================
# Dynamic Color Assignment
# ============================================================================

class DynamicColorAssigner:
    """Dynamically assign colors to avoid conflicts and maintain consistency"""
    
    def __init__(self):
        self.assigned_colors: Dict[str, str] = {}
        self.color_history = deque(maxlen=100)
        self.base_colors = {
            SwarmType.BURST: '#FF6B6B',
            SwarmType.PIPELINE: '#4ECDC4',
            SwarmType.PARALLEL: '#5C7CFA',
            SwarmType.HIERARCHICAL: '#8B5CF6',
            SwarmType.UNCLASSIFIED: '#6B7280'
        }
    
    def assign_color(self, swarm_id: str, swarm_type: SwarmType) -> str:
        """
        Assign unique color to swarm, maintaining consistency
        """
        # Check if already assigned
        if swarm_id in self.assigned_colors:
            return self.assigned_colors[swarm_id]
        
        # Get base color for type
        base_color = self.base_colors.get(swarm_type, '#6B7280')
        
        # Find available variation
        color = self._find_unique_variation(base_color)
        
        # Record assignment
        self.assigned_colors[swarm_id] = color
        self.color_history.append((swarm_id, color))
        
        return color
    
    def _find_unique_variation(self, base_color: str) -> str:
        """Find unique color variation not currently in use"""
        # For now, return base color with slight variation
        # In production, implement proper HSV manipulation
        import random
        
        if base_color not in self.assigned_colors.values():
            return base_color
        
        # Generate variation
        variations = [
            base_color,
            self._adjust_brightness(base_color, 0.1),
            self._adjust_brightness(base_color, -0.1),
        ]
        
        for var in variations:
            if var not in self.assigned_colors.values():
                return var
        
        # Fallback to base color
        return base_color
    
    def _adjust_brightness(self, hex_color: str, factor: float) -> str:
        """Adjust color brightness"""
        # Simple brightness adjustment
        # In production, use proper color library
        return hex_color  # Placeholder
    
    def release_color(self, swarm_id: str):
        """Release color when swarm is no longer active"""
        if swarm_id in self.assigned_colors:
            del self.assigned_colors[swarm_id]


# ============================================================================
# Statistics
# ============================================================================

class SwarmStatistics:
    """Track and compute swarm detection statistics"""
    
    def __init__(self):
        self.total_agents_processed = 0
        self.total_swarms_detected = 0
        self.swarm_type_counts = defaultdict(int)
        self.detection_times = []
        self.swarm_sizes = []
    
    def compute(self) -> Dict[str, Any]:
        """Compute current statistics"""
        stats = {
            'total_agents': self.total_agents_processed,
            'total_swarms': self.total_swarms_detected,
            'swarm_types': dict(self.swarm_type_counts),
            'avg_swarm_size': sum(self.swarm_sizes) / len(self.swarm_sizes) if self.swarm_sizes else 0,
            'avg_detection_time': sum(self.detection_times) / len(self.detection_times) if self.detection_times else 0
        }
        return stats
    
    def update(self, agents_count: int, swarms: List[Swarm], detection_time: float):
        """Update statistics with new detection results"""
        self.total_agents_processed += agents_count
        self.total_swarms_detected += len(swarms)
        
        for swarm in swarms:
            self.swarm_type_counts[swarm.classification.primary_type.value] += 1
            self.swarm_sizes.append(swarm.size)
        
        self.detection_times.append(detection_time)


# ============================================================================
# Main Entry Point
# ============================================================================

def detect_swarms(agents: List[Agent], config: Optional[SwarmConfig] = None) -> SwarmDetectionResult:
    """
    Main entry point for swarm detection
    
    Args:
        agents: List of Agent objects to analyze
        config: Optional configuration for detection parameters
    
    Returns:
        SwarmDetectionResult with identified swarms and statistics
    """
    engine = SwarmDetectionEngine(config)
    visualizer = SwarmVisualizer()
    
    # Detect swarms
    start_time = time.time()
    result = engine.detect_swarms(agents, mode='batch')
    detection_time = time.time() - start_time
    
    # Assign visuals to each swarm
    for swarm in result.swarms:
        swarm.visuals = visualizer.assign_visuals(swarm)
    
    # Update statistics
    engine.stats.update(len(agents), result.swarms, detection_time)
    result.statistics = engine.stats.compute()
    
    return result


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example usage
    import random
    
    # Create sample agents
    sample_agents = []
    base_time = time.time()
    
    # Create a burst swarm (tighter temporal clustering)
    for i in range(8):
        agent = Agent(
            agent_id=f"burst_{i}",
            start_time=base_time + random.uniform(0, 0.5),  # Tighter clustering
            end_time=base_time + random.uniform(1, 2),
            priority_score=0.8,
            resources=["/api/data", "/api/process"],
            task_type="data_processing"
        )
        sample_agents.append(agent)
    
    # Create a pipeline swarm
    pipeline_start = base_time + 10
    prev_id = None
    for i in range(5):
        agent = Agent(
            agent_id=f"pipeline_{i}",
            start_time=pipeline_start + i * 2,
            priority_score=0.6,
            dependencies=[prev_id] if prev_id else [],
            resources=[f"/stage_{i}"],
            task_type="pipeline"
        )
        sample_agents.append(agent)
        prev_id = agent.agent_id
    
    # Detect swarms
    config = SwarmConfig(
        temporal_epsilon=5.0,
        min_swarm_size=3,
        burst_threshold=5,
        burst_window=1.0  # 1 second window for burst detection
    )
    
    result = detect_swarms(sample_agents, config)
    
    # Display results
    print(f"\n🔍 Swarm Detection Results")
    print(f"{'=' * 50}")
    print(f"Detected {len(result.swarms)} swarms from {len(sample_agents)} agents\n")
    
    visualizer = SwarmVisualizer()
    for swarm in result.swarms:
        print(visualizer.format_swarm_display(swarm))
        print(f"  Agents: {', '.join(a.agent_id for a in swarm.agents[:3])}...")
        print()
    
    print(f"\n📊 Statistics:")
    for key, value in result.statistics.items():
        print(f"  {key}: {value}")