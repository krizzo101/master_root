"""
AI Pattern Engine - Semantic pattern recognition using Claude's intelligence
Replaces ALL regex and string matching with AI understanding
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class PatternType(Enum):
    """Types of patterns the AI can recognize"""
    BEHAVIORAL = "behavioral"           # Action-outcome relationships
    TEMPORAL = "temporal"               # Time-based sequences
    CAUSAL = "causal"                  # Cause-effect chains
    OPTIMIZATION = "optimization"       # Performance improvements
    ANOMALY = "anomaly"                # Unusual patterns
    EMERGENT = "emergent"              # Unexpected correlations
    PREDICTIVE = "predictive"          # Future predictions
    META = "meta"                      # Patterns about patterns


@dataclass
class AIPattern:
    """AI-discovered pattern with semantic understanding"""
    id: str
    type: PatternType
    description: str
    semantic_meaning: str              # What this pattern MEANS
    trigger_conditions: List[str]      # When it applies (AI-understood)
    expected_outcomes: List[str]       # What happens next
    confidence: float
    evidence: List[Dict[str, Any]]    # Supporting observations
    relationships: List[Dict[str, Any]] # Related patterns
    predictive_power: float            # How well it predicts
    metadata: Dict[str, Any] = field(default_factory=dict)
    discovered_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'type': self.type.value,
            'description': self.description,
            'semantic_meaning': self.semantic_meaning,
            'trigger_conditions': self.trigger_conditions,
            'expected_outcomes': self.expected_outcomes,
            'confidence': self.confidence,
            'predictive_power': self.predictive_power,
            'evidence_count': len(self.evidence),
            'relationships': self.relationships,
            'metadata': self.metadata,
            'discovered_at': self.discovered_at.isoformat()
        }


class AIPatternEngine:
    """
    Semantic pattern recognition using Claude's intelligence
    No regex, no string matching - only AI understanding
    """
    
    def __init__(self, claude_client=None, ai_decision_engine=None):
        """Initialize with Claude client and decision engine"""
        self.claude = claude_client
        self.decision_engine = ai_decision_engine
        self.patterns: Dict[str, AIPattern] = {}
        self.pattern_graph = {}  # Relationships between patterns
        self.observation_buffer = []
        self.semantic_index = {}  # Semantic similarity index
        
    async def observe_and_learn(self, 
                               observation: Dict[str, Any],
                               context: Optional[Dict[str, Any]] = None) -> List[AIPattern]:
        """
        Observe data and discover patterns using AI
        
        Args:
            observation: New observation data
            context: Additional context
            
        Returns:
            List of discovered patterns
        """
        
        # Add to buffer
        self.observation_buffer.append({
            'observation': observation,
            'context': context,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep buffer manageable
        if len(self.observation_buffer) > 1000:
            self.observation_buffer = self.observation_buffer[-1000:]
        
        # AI pattern discovery
        discovered_patterns = await self._ai_discover_patterns(observation, context)
        
        # Update pattern relationships
        if discovered_patterns:
            await self._ai_find_relationships(discovered_patterns)
        
        # Update predictive power
        await self._ai_validate_predictions()
        
        return discovered_patterns
    
    async def find_matching_patterns(self, 
                                   context: Dict[str, Any],
                                   threshold: float = 0.5) -> List[Tuple[AIPattern, float]]:
        """
        Find patterns that match the context using AI semantic understanding
        
        Args:
            context: Current context to match
            threshold: Minimum confidence threshold
            
        Returns:
            List of (pattern, match_score) tuples
        """
        
        if not self.patterns:
            return []
        
        prompt = f"""
        You are a pattern matching AI with deep semantic understanding.
        
        Current Context: {json.dumps(context, indent=2)}
        
        Available Patterns:
        {json.dumps([p.to_dict() for p in self.patterns.values()], indent=2)}
        
        Task:
        1. Find patterns that semantically match this context
        2. Consider implicit relationships, not just keywords
        3. Understand meaning and intent, not surface features
        4. Identify partial matches and near-matches
        5. Consider temporal and causal relationships
        
        DO NOT do simple string matching. Use semantic understanding.
        
        Return JSON:
        {{
            "matches": [
                {{
                    "pattern_id": "...",
                    "match_score": 0.0-1.0,
                    "reasoning": "why this pattern matches semantically",
                    "trigger_conditions_met": [...],
                    "expected_outcomes": [...],
                    "confidence_adjustment": "reason for confidence level"
                }}
            ],
            "potential_new_pattern": {{
                "detected": true/false,
                "description": "...",
                "evidence": [...]
            }}
        }}
        """
        
        if self.claude:
            try:
                result = await self.claude.execute(prompt, mode="sync")
                
                matches = []
                for match in result.get('matches', []):
                    if match['match_score'] >= threshold:
                        pattern = self.patterns.get(match['pattern_id'])
                        if pattern:
                            matches.append((pattern, match['match_score']))
                
                # Check for new pattern opportunity
                if result.get('potential_new_pattern', {}).get('detected'):
                    await self._create_pattern_from_insight(
                        result['potential_new_pattern'], context
                    )
                
                return sorted(matches, key=lambda x: x[1], reverse=True)
                
            except Exception as e:
                print(f"AI pattern matching failed: {e}")
        
        return []
    
    async def predict_next(self, 
                         current_state: Dict[str, Any],
                         time_horizon: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Predict what will happen next based on learned patterns
        
        Args:
            current_state: Current system state
            time_horizon: How far ahead to predict (steps/time)
            
        Returns:
            List of predictions with confidence scores
        """
        
        prompt = f"""
        You are a predictive AI using learned patterns to forecast future states.
        
        Current State: {json.dumps(current_state, indent=2)}
        
        Known Patterns: {json.dumps([p.to_dict() for p in self.patterns.values()], indent=2)}
        
        Recent History: {json.dumps(self.observation_buffer[-10:], indent=2)}
        
        Task:
        1. Identify which patterns are currently active
        2. Predict likely next states/events
        3. Consider pattern interactions and cascading effects
        4. Account for uncertainty and alternatives
        5. Estimate timing if possible
        
        Time Horizon: {time_horizon or 'next immediate step'}
        
        Return JSON:
        {{
            "active_patterns": [
                {{"pattern_id": "...", "activation_strength": 0.0-1.0}}
            ],
            "predictions": [
                {{
                    "event": "what will happen",
                    "probability": 0.0-1.0,
                    "timing": "when (if known)",
                    "reasoning": "why this is predicted",
                    "based_on_patterns": [...],
                    "confidence": 0.0-1.0,
                    "preconditions": [...],
                    "side_effects": [...]
                }}
            ],
            "alternative_scenarios": [
                {{
                    "scenario": "...",
                    "probability": 0.0-1.0,
                    "triggers": [...]
                }}
            ],
            "warnings": [
                "potential risks or unexpected outcomes"
            ]
        }}
        """
        
        if self.claude:
            try:
                result = await self.claude.execute(prompt, mode="sync")
                return result.get('predictions', [])
            except Exception as e:
                print(f"AI prediction failed: {e}")
        
        return []
    
    async def _ai_discover_patterns(self, 
                                  observation: Dict[str, Any],
                                  context: Optional[Dict[str, Any]]) -> List[AIPattern]:
        """Use AI to discover patterns in observations"""
        
        # Get recent observations for pattern detection
        recent = self.observation_buffer[-20:] if len(self.observation_buffer) > 20 else self.observation_buffer
        
        prompt = f"""
        You are an expert pattern discovery AI. Find meaningful patterns in this data.
        
        New Observation: {json.dumps(observation, indent=2)}
        Context: {json.dumps(context or {}, indent=2)}
        Recent Observations: {json.dumps(recent, indent=2)}
        
        Existing Patterns: {json.dumps([p.description for p in self.patterns.values()], indent=2)}
        
        Discover:
        1. BEHAVIORAL patterns - What actions lead to what outcomes?
        2. TEMPORAL patterns - What sequences occur over time?
        3. CAUSAL patterns - What causes what? (not just correlation)
        4. OPTIMIZATION patterns - Where can performance improve?
        5. ANOMALY patterns - What's unusual or unexpected?
        6. EMERGENT patterns - What complex behaviors emerge?
        7. META patterns - Are there patterns in how patterns form?
        
        Requirements:
        - Use SEMANTIC understanding, not keyword matching
        - Find implicit relationships
        - Consider multi-step causation
        - Identify feedback loops
        - Recognize system dynamics
        
        Return JSON:
        {{
            "discovered_patterns": [
                {{
                    "type": "behavioral|temporal|causal|optimization|anomaly|emergent|meta",
                    "description": "clear pattern description",
                    "semantic_meaning": "what this pattern MEANS for the system",
                    "trigger_conditions": ["semantic conditions, not keywords"],
                    "expected_outcomes": ["what happens when pattern activates"],
                    "confidence": 0.0-1.0,
                    "evidence": [
                        {{"observation": "...", "supports": "which aspect of pattern"}}
                    ],
                    "predictive_power": 0.0-1.0,
                    "relationships": [
                        {{"related_to": "other_pattern", "relationship_type": "..."}}
                    ]
                }}
            ],
            "pattern_interactions": [
                {{"pattern_a": "...", "pattern_b": "...", "interaction": "how they affect each other"}}
            ],
            "insights": [
                "deeper understanding gained from these patterns"
            ]
        }}
        """
        
        if self.claude:
            try:
                result = await self.claude.execute(prompt, mode="sync")
                
                new_patterns = []
                for pattern_data in result.get('discovered_patterns', []):
                    pattern = AIPattern(
                        id=f"pattern_{len(self.patterns)}_{datetime.now().timestamp()}",
                        type=PatternType(pattern_data['type']),
                        description=pattern_data['description'],
                        semantic_meaning=pattern_data['semantic_meaning'],
                        trigger_conditions=pattern_data['trigger_conditions'],
                        expected_outcomes=pattern_data['expected_outcomes'],
                        confidence=pattern_data['confidence'],
                        evidence=pattern_data['evidence'],
                        relationships=pattern_data.get('relationships', []),
                        predictive_power=pattern_data.get('predictive_power', 0.5),
                        metadata={'discovery_context': context}
                    )
                    
                    self.patterns[pattern.id] = pattern
                    new_patterns.append(pattern)
                
                return new_patterns
                
            except Exception as e:
                print(f"AI pattern discovery failed: {e}")
        
        return []
    
    async def _ai_find_relationships(self, new_patterns: List[AIPattern]):
        """Use AI to find relationships between patterns"""
        
        if len(self.patterns) < 2:
            return
        
        prompt = f"""
        You are analyzing relationships between patterns.
        
        New Patterns: {json.dumps([p.to_dict() for p in new_patterns], indent=2)}
        Existing Patterns: {json.dumps([p.to_dict() for p in self.patterns.values()], indent=2)}
        
        Identify:
        1. Causal relationships (A causes B)
        2. Temporal relationships (A precedes B)
        3. Hierarchical relationships (A contains B)
        4. Antagonistic relationships (A prevents B)
        5. Synergistic relationships (A+B > A or B alone)
        6. Cyclic relationships (A→B→C→A)
        
        Return JSON:
        {{
            "relationships": [
                {{
                    "from_pattern": "pattern_id",
                    "to_pattern": "pattern_id",
                    "relationship_type": "causal|temporal|hierarchical|antagonistic|synergistic|cyclic",
                    "strength": 0.0-1.0,
                    "description": "nature of relationship",
                    "evidence": [...]
                }}
            ],
            "pattern_clusters": [
                {{
                    "cluster_theme": "what unites these patterns",
                    "pattern_ids": [...],
                    "emergent_behavior": "what emerges from this cluster"
                }}
            ]
        }}
        """
        
        if self.claude:
            try:
                result = await self.claude.execute(prompt, mode="sync")
                
                # Update pattern graph
                for rel in result.get('relationships', []):
                    from_id = rel['from_pattern']
                    to_id = rel['to_pattern']
                    
                    if from_id not in self.pattern_graph:
                        self.pattern_graph[from_id] = []
                    
                    self.pattern_graph[from_id].append({
                        'to': to_id,
                        'type': rel['relationship_type'],
                        'strength': rel['strength']
                    })
                    
            except Exception as e:
                print(f"AI relationship discovery failed: {e}")
    
    async def _ai_validate_predictions(self):
        """Validate and update predictive power of patterns"""
        
        # This would track predictions and validate them against actual outcomes
        # Updates pattern.predictive_power based on accuracy
        pass
    
    async def _create_pattern_from_insight(self, insight: Dict[str, Any], context: Dict[str, Any]):
        """Create a new pattern from AI insight"""
        
        # This would create a new pattern when AI detects something not yet captured
        pass
    
    async def explain_pattern(self, pattern: AIPattern) -> str:
        """Get detailed AI explanation of a pattern"""
        
        prompt = f"""
        Explain this pattern in detail:
        
        Pattern: {json.dumps(pattern.to_dict(), indent=2)}
        
        Explain:
        1. What this pattern means in practical terms
        2. When and why it occurs
        3. How to recognize it
        4. What to do when it's detected
        5. How it relates to system behavior
        
        Make it clear for a human operator.
        """
        
        if self.claude:
            try:
                explanation = await self.claude.execute(prompt, mode="sync")
                return explanation
            except:
                pass
        
        return pattern.semantic_meaning
    
    async def merge_patterns(self, pattern_ids: List[str]) -> Optional[AIPattern]:
        """Use AI to merge related patterns into a higher-level pattern"""
        
        patterns_to_merge = [self.patterns[pid] for pid in pattern_ids if pid in self.patterns]
        
        if len(patterns_to_merge) < 2:
            return None
        
        prompt = f"""
        Merge these related patterns into a higher-level pattern:
        
        Patterns: {json.dumps([p.to_dict() for p in patterns_to_merge], indent=2)}
        
        Create a unified pattern that:
        1. Captures the essence of all sub-patterns
        2. Identifies the higher-level behavior
        3. Maintains predictive power
        4. Describes emergent properties
        
        Return the merged pattern specification.
        """
        
        if self.claude:
            try:
                result = await self.claude.execute(prompt, mode="sync")
                # Create merged pattern
                # ... implementation
            except:
                pass
        
        return None
    
    def get_pattern_graph(self) -> Dict[str, Any]:
        """Get the pattern relationship graph"""
        return self.pattern_graph
    
    def get_all_patterns(self) -> List[AIPattern]:
        """Get all discovered patterns"""
        return list(self.patterns.values())
    
    def get_patterns_by_type(self, pattern_type: PatternType) -> List[AIPattern]:
        """Get patterns of a specific type"""
        return [p for p in self.patterns.values() if p.type == pattern_type]