"""
AI Pattern Engine - Semantic pattern recognition using Claude AI
Replaces all regex/string matching with AI understanding

This module uses Claude's semantic understanding to identify patterns
that would be impossible to detect with traditional pattern matching.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.utils.logger import get_logger

logger = get_logger(__name__)


class PatternType(Enum):
    """Types of patterns AI can recognize"""
    BEHAVIORAL = "behavioral"          # How system behaves over time
    STRUCTURAL = "structural"          # Code/architecture patterns
    TEMPORAL = "temporal"              # Time-based patterns
    CAUSAL = "causal"                 # Cause-effect relationships
    EMERGENT = "emergent"              # System-level emergent behaviors
    ANOMALY = "anomaly"                # Deviations from normal
    OPTIMIZATION = "optimization"      # Performance patterns
    ERROR_PATTERN = "error_pattern"    # Error occurrence patterns
    USER_BEHAVIOR = "user_behavior"    # User interaction patterns
    RESOURCE_USAGE = "resource_usage"  # Resource consumption patterns


@dataclass
class AIPattern:
    """Container for AI-recognized patterns"""
    pattern_id: str
    pattern_type: PatternType
    description: str
    confidence: float
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    implications: List[str] = field(default_factory=list)
    predictive_value: str = ""
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    discovered_at: datetime = field(default_factory=datetime.now)
    
    def is_actionable(self, threshold: float = 0.7) -> bool:
        """Determine if pattern is actionable based on confidence"""
        return self.confidence >= threshold
    
    def get_primary_implication(self) -> Optional[str]:
        """Get the most important implication"""
        return self.implications[0] if self.implications else None


class AIPatternEngine:
    """
    Semantic pattern recognition using AI instead of regex/string matching.
    
    This replaces:
    - Regex pattern matching with semantic understanding
    - Keyword searching with conceptual matching
    - Simple correlations with causal analysis
    - Surface patterns with deep behavioral understanding
    """
    
    def __init__(self, claude_client):
        self.claude = claude_client
        self.pattern_memory = []
        self.pattern_library = {}
        self.relationship_graph = {}
        self.max_memory = 1000
        
    async def recognize_patterns(self,
                                data: Any,
                                pattern_type: Optional[PatternType] = None,
                                context: Optional[Dict[str, Any]] = None,
                                depth: str = "deep") -> Dict[str, Any]:
        """
        Use AI to understand patterns semantically.
        
        This is the PRIMARY method that replaces ALL pattern matching logic.
        
        Args:
            data: Data to analyze for patterns
            pattern_type: Specific type to look for (None = auto-detect)
            context: Additional context for pattern recognition
            depth: Analysis depth - "shallow", "deep", or "comprehensive"
            
        Returns:
            Comprehensive pattern analysis with semantic understanding
        """
        
        # Build comprehensive prompt for pattern recognition
        prompt = self._build_pattern_prompt(data, pattern_type, context, depth)
        
        try:
            # Execute AI pattern recognition
            result = await self.claude.execute(prompt, mode="sync")
            
            # Parse and store patterns
            patterns = self._parse_patterns(result, pattern_type)
            
            # Update pattern memory and library
            self._update_pattern_memory(patterns)
            
            # Build relationship graph
            self._update_relationship_graph(patterns)
            
            logger.info(f"AI recognized {len(patterns)} patterns with "
                       f"average confidence {self._avg_confidence(patterns):.2f}")
            
            return {
                'patterns': patterns,
                'relationships': result.get('relationships', []),
                'insights': result.get('insights', {}),
                'predictions': result.get('predictions', [])
            }
            
        except Exception as e:
            logger.error(f"AI pattern recognition failed: {e}")
            return {
                'patterns': [],
                'error': str(e)
            }
    
    def _build_pattern_prompt(self,
                             data: Any,
                             pattern_type: Optional[PatternType],
                             context: Optional[Dict[str, Any]],
                             depth: str) -> str:
        """Build comprehensive prompt for AI pattern recognition"""
        
        # Depth-specific instructions
        depth_instructions = {
            "shallow": "Identify obvious patterns and direct relationships.",
            "deep": "Perform deep analysis including hidden patterns, causal relationships, and non-obvious connections.",
            "comprehensive": "Exhaustive analysis including all patterns, relationships, predictions, and meta-patterns."
        }
        
        # Pattern type specific focus
        pattern_focus = ""
        if pattern_type:
            pattern_focuses = {
                PatternType.BEHAVIORAL: "Focus on behavioral patterns, sequences, and recurring actions.",
                PatternType.STRUCTURAL: "Focus on structural patterns in code, architecture, and organization.",
                PatternType.TEMPORAL: "Focus on time-based patterns, cycles, and temporal correlations.",
                PatternType.CAUSAL: "Focus on cause-effect relationships and causal chains.",
                PatternType.EMERGENT: "Focus on emergent behaviors and system-level patterns.",
                PatternType.ANOMALY: "Focus on anomalies, outliers, and deviations from normal.",
                PatternType.OPTIMIZATION: "Focus on performance patterns and optimization opportunities.",
                PatternType.ERROR_PATTERN: "Focus on error patterns, failure modes, and recovery patterns.",
                PatternType.USER_BEHAVIOR: "Focus on user interaction patterns and preferences.",
                PatternType.RESOURCE_USAGE: "Focus on resource consumption and efficiency patterns."
            }
            pattern_focus = pattern_focuses.get(pattern_type, "")
        
        # Convert data to string representation
        data_str = json.dumps(data) if isinstance(data, (dict, list)) else str(data)
        
        prompt = f"""
        Perform semantic pattern recognition using AI intelligence.
        
        Data to Analyze:
        {data_str[:5000]}  # Limit to prevent token overflow
        
        {"Context: " + json.dumps(context) if context else ""}
        
        Analysis Depth: {depth}
        {depth_instructions[depth]}
        
        {pattern_focus}
        
        Historical Patterns (for comparison):
        {json.dumps(self.pattern_memory[-5:]) if self.pattern_memory else "No history"}
        
        Use semantic understanding to identify:
        1. Patterns that cannot be found with regex or keyword matching
        2. Behavioral patterns showing how the system operates
        3. Causal relationships explaining why things happen
        4. Hidden dependencies and connections
        5. Emergent properties from component interactions
        6. Predictive indicators of future behavior
        7. Anomalies with contextual understanding of why they're anomalous
        
        Return comprehensive analysis:
        {{
            "patterns_found": [
                {{
                    "pattern_id": "unique_id",
                    "type": "behavioral|structural|temporal|causal|emergent|anomaly|optimization|error_pattern|user_behavior|resource_usage",
                    "description": "semantic description of pattern",
                    "confidence": 0.0-1.0,
                    "evidence": [
                        {{"data_point": "...", "significance": "why this is evidence"}}
                    ],
                    "implications": [
                        "what this pattern means for the system"
                    ],
                    "predictive_value": "what this pattern predicts about future behavior",
                    "semantic_signature": "conceptual representation of pattern"
                }}
            ],
            "relationships": [
                {{
                    "from": "entity or pattern",
                    "to": "entity or pattern",
                    "relationship_type": "causes|correlates|depends_on|triggers|inhibits",
                    "strength": 0.0-1.0,
                    "evidence": "why this relationship exists"
                }}
            ],
            "insights": {{
                "key_finding": "most important discovery",
                "behavioral_model": "how the system behaves based on patterns",
                "optimization_opportunities": ["opportunity1", ...],
                "risk_factors": ["risk1", ...],
                "recommendations": ["action1", ...]
            }},
            "predictions": [
                {{
                    "prediction": "what will likely happen",
                    "confidence": 0.0-1.0,
                    "timeframe": "when",
                    "based_on_patterns": ["pattern_id1", ...]
                }}
            ],
            "meta_patterns": {{
                "pattern_evolution": "how patterns are changing over time",
                "pattern_interactions": "how patterns affect each other",
                "system_trajectory": "where the system is heading"
            }}
        }}
        """
        
        return prompt
    
    async def match_pattern(self,
                          candidate: Any,
                          pattern_library: Optional[List[AIPattern]] = None,
                          match_type: str = "semantic") -> Dict[str, Any]:
        """
        Semantic pattern matching using AI understanding.
        
        This replaces regex.match() and string.contains() with semantic matching.
        
        Args:
            candidate: Data to match against patterns
            pattern_library: Patterns to match against (uses internal library if None)
            match_type: "semantic", "behavioral", "structural", or "exact"
            
        Returns:
            Match results with semantic understanding
        """
        
        # Use internal library if not provided
        if pattern_library is None:
            pattern_library = list(self.pattern_library.values())
        
        if not pattern_library:
            return {'matches': [], 'best_match': None}
        
        prompt = f"""
        Perform semantic pattern matching using AI understanding.
        
        Candidate to Match:
        {json.dumps(candidate) if isinstance(candidate, dict) else str(candidate)}
        
        Known Patterns:
        {json.dumps([self._pattern_to_dict(p) for p in pattern_library[:20]], indent=2)}
        
        Match Type: {match_type}
        
        Don't just match keywords or surface features. Use semantic understanding to find:
        1. Conceptual similarity (same idea, different implementation)
        2. Behavioral equivalence (same outcome, different approach)
        3. Structural similarity (same organization, different details)
        4. Contextual relevance (appropriate for the situation)
        5. Partial matches with adaptation potential
        
        Return:
        {{
            "best_match": {{
                "pattern_id": "id of best matching pattern",
                "confidence": 0.0-1.0,
                "match_type": "exact|semantic|behavioral|structural|partial",
                "reasoning": "why this is the best match"
            }},
            "all_matches": [
                {{
                    "pattern_id": "...",
                    "confidence": 0.0-1.0,
                    "match_aspects": ["what aspects match"],
                    "differences": ["what aspects differ"],
                    "adaptation_needed": "how to adapt pattern for this case"
                }}
            ],
            "semantic_analysis": {{
                "candidate_concepts": ["key concepts in candidate"],
                "pattern_concepts": ["key concepts in patterns"],
                "conceptual_overlap": 0.0-1.0,
                "behavioral_similarity": 0.0-1.0
            }},
            "no_match_reason": "if no good match, why not"
        }}
        """
        
        result = await self.claude.execute(prompt, mode="sync")
        
        return result
    
    async def predict_next_pattern(self,
                                  pattern_sequence: List[AIPattern],
                                  context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Predict what pattern will occur next based on AI understanding.
        
        Args:
            pattern_sequence: Recent sequence of patterns
            context: Current context
            
        Returns:
            Prediction of next pattern with reasoning
        """
        
        prompt = f"""
        Predict the next pattern based on semantic understanding of the sequence.
        
        Recent Pattern Sequence:
        {json.dumps([self._pattern_to_dict(p) for p in pattern_sequence[-10:]], indent=2)}
        
        Current Context:
        {json.dumps(context) if context else "No specific context"}
        
        Use AI intelligence to:
        1. Understand the pattern trajectory
        2. Identify causal chains
        3. Recognize cycles or progressions
        4. Consider context effects
        5. Account for system dynamics
        
        Return:
        {{
            "predicted_pattern": {{
                "type": "pattern type",
                "description": "what will happen",
                "confidence": 0.0-1.0,
                "expected_timing": "when it will occur",
                "preconditions": ["what needs to be true"]
            }},
            "reasoning": {{
                "pattern_trajectory": "where patterns are heading",
                "causal_chain": "what causes what",
                "contextual_factors": ["relevant context"],
                "alternative_scenarios": [
                    {{"scenario": "...", "probability": 0.0-1.0}}
                ]
            }},
            "early_indicators": ["what to watch for"],
            "intervention_points": ["where you could change the outcome"]
        }}
        """
        
        return await self.claude.execute(prompt, mode="sync")
    
    async def find_meta_patterns(self,
                                patterns: List[AIPattern]) -> Dict[str, Any]:
        """
        Find patterns in the patterns themselves (meta-patterns).
        
        Args:
            patterns: Collection of patterns to analyze
            
        Returns:
            Meta-pattern analysis
        """
        
        prompt = f"""
        Analyze patterns to find meta-patterns (patterns in the patterns).
        
        Patterns to Analyze:
        {json.dumps([self._pattern_to_dict(p) for p in patterns[:30]], indent=2)}
        
        Look for:
        1. How patterns evolve over time
        2. Which patterns trigger other patterns
        3. Pattern clusters that occur together
        4. Cyclical pattern sequences
        5. Pattern hierarchies and dependencies
        6. Emergent properties from pattern interactions
        
        Return:
        {{
            "meta_patterns": [
                {{
                    "type": "evolution|interaction|cluster|cycle|hierarchy|emergence",
                    "description": "meta-pattern description",
                    "involved_patterns": ["pattern_id1", ...],
                    "significance": "why this matters",
                    "implications": ["implication1", ...]
                }}
            ],
            "pattern_dynamics": {{
                "dominant_patterns": ["patterns that drive the system"],
                "subordinate_patterns": ["patterns that follow"],
                "pattern_stability": "how stable patterns are",
                "change_indicators": ["signs patterns are changing"]
            }},
            "system_insights": {{
                "system_state": "what patterns reveal about system state",
                "system_direction": "where the system is heading",
                "intervention_leverage": ["high-impact intervention points"]
            }}
        }}
        """
        
        return await self.claude.execute(prompt, mode="sync")
    
    def _pattern_to_dict(self, pattern: AIPattern) -> Dict[str, Any]:
        """Convert AIPattern to dictionary for serialization"""
        
        return {
            'pattern_id': pattern.pattern_id,
            'type': pattern.pattern_type.value,
            'description': pattern.description,
            'confidence': pattern.confidence,
            'evidence': pattern.evidence[:3],  # Limit for space
            'implications': pattern.implications[:2],
            'predictive_value': pattern.predictive_value
        }
    
    def _parse_patterns(self,
                       result: Dict[str, Any],
                       pattern_type: Optional[PatternType]) -> List[AIPattern]:
        """Parse AI response into AIPattern objects"""
        
        patterns = []
        for pattern_data in result.get('patterns_found', []):
            # Determine pattern type
            if pattern_type:
                ptype = pattern_type
            else:
                type_str = pattern_data.get('type', 'behavioral')
                ptype = PatternType[type_str.upper()] if hasattr(PatternType, type_str.upper()) else PatternType.BEHAVIORAL
            
            pattern = AIPattern(
                pattern_id=pattern_data.get('pattern_id', str(datetime.now().timestamp())),
                pattern_type=ptype,
                description=pattern_data.get('description', ''),
                confidence=float(pattern_data.get('confidence', 0.5)),
                evidence=pattern_data.get('evidence', []),
                implications=pattern_data.get('implications', []),
                predictive_value=pattern_data.get('predictive_value', ''),
                relationships=pattern_data.get('relationships', []),
                metadata={
                    'semantic_signature': pattern_data.get('semantic_signature', ''),
                    'discovered_at': datetime.now().isoformat()
                }
            )
            patterns.append(pattern)
            
            # Store in library
            self.pattern_library[pattern.pattern_id] = pattern
        
        return patterns
    
    def _update_pattern_memory(self, patterns: List[AIPattern]):
        """Update pattern memory with new patterns"""
        
        for pattern in patterns:
            self.pattern_memory.append({
                'timestamp': datetime.now().isoformat(),
                'pattern_id': pattern.pattern_id,
                'type': pattern.pattern_type.value,
                'confidence': pattern.confidence,
                'description': pattern.description[:100]  # Truncate for space
            })
        
        # Limit memory size
        if len(self.pattern_memory) > self.max_memory:
            self.pattern_memory = self.pattern_memory[-self.max_memory:]
    
    def _update_relationship_graph(self, patterns: List[AIPattern]):
        """Update relationship graph with pattern relationships"""
        
        for pattern in patterns:
            if pattern.pattern_id not in self.relationship_graph:
                self.relationship_graph[pattern.pattern_id] = {
                    'connections': [],
                    'strength': {}
                }
            
            for rel in pattern.relationships:
                target = rel.get('to', '')
                if target and target not in self.relationship_graph[pattern.pattern_id]['connections']:
                    self.relationship_graph[pattern.pattern_id]['connections'].append(target)
                    self.relationship_graph[pattern.pattern_id]['strength'][target] = rel.get('strength', 0.5)
    
    def _avg_confidence(self, patterns: List[AIPattern]) -> float:
        """Calculate average confidence of patterns"""
        
        if not patterns:
            return 0.0
        return sum(p.confidence for p in patterns) / len(patterns)
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get statistics about recognized patterns"""
        
        if not self.pattern_library:
            return {'total_patterns': 0}
        
        patterns = list(self.pattern_library.values())
        
        stats = {
            'total_patterns': len(patterns),
            'average_confidence': self._avg_confidence(patterns),
            'pattern_types': {},
            'high_confidence_patterns': sum(1 for p in patterns if p.confidence > 0.8),
            'actionable_patterns': sum(1 for p in patterns if p.is_actionable()),
            'patterns_with_predictions': sum(1 for p in patterns if p.predictive_value),
            'relationship_count': sum(len(p.relationships) for p in patterns)
        }
        
        # Count by type
        for pattern in patterns:
            type_name = pattern.pattern_type.value
            stats['pattern_types'][type_name] = stats['pattern_types'].get(type_name, 0) + 1
        
        return stats