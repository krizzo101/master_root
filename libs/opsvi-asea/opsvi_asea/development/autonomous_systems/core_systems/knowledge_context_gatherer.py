"""
Knowledge Context Gatherer for External Reasoning Service.
Gathers relevant context from ArangoDB knowledge graph for decision analysis.
"""

import logging
from typing import Dict, List, Any

# Try to import arango, but handle gracefully if not available
try:
    from arango import ArangoClient
except ImportError:
    print("Warning: arango client not available, using mock implementation")
    ArangoClient = None


class KnowledgeContextGatherer:
    """
    Gathers relevant context from the ArangoDB knowledge graph for decision analysis.
    Provides semantic search, relationship traversal, and historical pattern analysis.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the knowledge context gatherer.

        Args:
            config: Database configuration
        """
        self.config = config
        self.client = None
        self.db = None
        self.logger = logging.getLogger(__name__)

    async def connect(self):
        """Establish connection to ArangoDB."""
        try:
            if ArangoClient is None:
                self.logger.warning("ArangoClient not available, using mock mode")
                return False

            # Use exact configuration from foundational memories
            self.client = ArangoClient(hosts=self.config["host"])
            self.db = self.client.db(
                self.config["database"],
                username=self.config["username"],
                password=self.config["password"],
            )
            self.logger.info(f"Connected to ArangoDB at {self.config['host']}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to ArangoDB: {e}")
            return False

    def gather_decision_context(
        self,
        decision: str,
        rationale: str,
        max_memories: int = 20,
        max_concepts: int = 10,
        max_relationships: int = 15,
    ) -> Dict[str, Any]:
        """
        Gather comprehensive context for decision analysis.

        Args:
            decision: The decision to analyze
            rationale: The provided rationale
            max_memories: Maximum number of memories to retrieve
            max_concepts: Maximum number of cognitive concepts
            max_relationships: Maximum number of semantic relationships

        Returns:
            Dictionary containing relevant context
        """
        try:
            context = {
                "relevant_memories": self._get_relevant_memories(
                    decision, rationale, max_memories
                ),
                "cognitive_concepts": self._get_relevant_concepts(
                    decision, rationale, max_concepts
                ),
                "semantic_relationships": self._get_relevant_relationships(
                    decision, rationale, max_relationships
                ),
                "historical_patterns": self._get_historical_decision_patterns(decision),
                "operational_knowledge": self._get_operational_knowledge(decision),
                "context_quality_metrics": {},
            }

            # Calculate context quality metrics
            context["context_quality_metrics"] = self._calculate_context_quality(
                context
            )

            return context

        except Exception as e:
            self.logger.error(f"Error gathering decision context: {e}")
            return {
                "relevant_memories": [],
                "cognitive_concepts": [],
                "semantic_relationships": [],
                "historical_patterns": [],
                "operational_knowledge": [],
                "context_quality_metrics": {"error": str(e)},
            }

    def _get_relevant_memories(
        self, decision: str, rationale: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Get relevant memories from agent_memory collection."""
        try:
            # Search for memories related to decision keywords
            decision_keywords = self._extract_keywords(decision + " " + rationale)

            # Query for relevant memories using semantic search
            query = """
            FOR doc IN agent_memory
            FILTER doc.validation_status == "validated" AND doc.foundational == true
            LET relevance_score = (
                FOR keyword IN @keywords
                FILTER CONTAINS(LOWER(doc.content), LOWER(keyword)) OR
                       CONTAINS(LOWER(doc.title), LOWER(keyword)) OR
                       keyword IN doc.tags
                RETURN 1
            )
            FILTER LENGTH(relevance_score) > 0
            SORT LENGTH(relevance_score) DESC, doc.quality_score DESC
            LIMIT @limit
            RETURN {
                title: doc.title,
                content: doc.content,
                tags: doc.tags,
                quality_score: doc.quality_score,
                type: doc.type,
                tier: doc.tier,
                relevance_keywords: relevance_score
            }
            """

            cursor = self.db.aql.execute(
                query, bind_vars={"keywords": decision_keywords, "limit": limit}
            )

            return list(cursor)

        except Exception as e:
            self.logger.error(f"Error retrieving relevant memories: {e}")
            return []

    def _get_relevant_concepts(
        self, decision: str, rationale: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Get relevant cognitive concepts."""
        try:
            decision_keywords = self._extract_keywords(decision + " " + rationale)

            query = """
            FOR concept IN cognitive_concepts
            FILTER concept.confidence_score >= 0.7
            LET relevance_score = (
                FOR keyword IN @keywords
                FILTER CONTAINS(LOWER(concept.concept), LOWER(keyword)) OR
                       CONTAINS(LOWER(concept.knowledge_content.problem_statement), LOWER(keyword)) OR
                       CONTAINS(LOWER(concept.knowledge_content.solution_approach), LOWER(keyword))
                RETURN 1
            )
            FILTER LENGTH(relevance_score) > 0
            SORT LENGTH(relevance_score) DESC, concept.confidence_score DESC
            LIMIT @limit
            RETURN {
                concept: concept.concept,
                knowledge_content: concept.knowledge_content,
                confidence_score: concept.confidence_score,
                autonomous_intelligence_metrics: concept.autonomous_intelligence_metrics,
                relevance_score: LENGTH(relevance_score)
            }
            """

            cursor = self.db.aql.execute(
                query, bind_vars={"keywords": decision_keywords, "limit": limit}
            )

            return list(cursor)

        except Exception as e:
            self.logger.error(f"Error retrieving cognitive concepts: {e}")
            return []

    def _get_relevant_relationships(
        self, decision: str, rationale: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Get relevant semantic relationships."""
        try:
            query = """
            FOR rel IN semantic_relationships
            FILTER rel.compound_learning_potential >= 0.8
            SORT rel.compound_learning_potential DESC
            LIMIT @limit
            RETURN {
                relationship_type: rel.relationship_type,
                compound_learning_potential: rel.compound_learning_potential,
                from_concept: rel._from,
                to_concept: rel._to,
                relationship_strength: rel.relationship_strength
            }
            """

            cursor = self.db.aql.execute(query, bind_vars={"limit": limit})

            return list(cursor)

        except Exception as e:
            self.logger.error(f"Error retrieving semantic relationships: {e}")
            return []

    def _get_historical_decision_patterns(self, decision: str) -> List[str]:
        """Get historical decision patterns from intelligence analytics."""
        try:
            query = """
            FOR doc IN intelligence_analytics
            FILTER doc.type == "decision_context" OR doc.type == "decision_analysis"
            FILTER DATE_DIFF(doc.created, DATE_NOW(), "day") <= 30
            SORT doc.created DESC
            LIMIT 10
            RETURN doc.content
            """

            cursor = self.db.aql.execute(query)
            patterns = []

            for doc in cursor:
                if isinstance(doc, str) and len(doc) > 50:
                    patterns.append(doc[:200] + "..." if len(doc) > 200 else doc)

            return patterns

        except Exception as e:
            self.logger.error(f"Error retrieving historical patterns: {e}")
            return []

    def _get_operational_knowledge(self, decision: str) -> List[Dict[str, Any]]:
        """Get operational knowledge relevant to the decision."""
        try:
            # Look for operational memories and behavioral requirements
            query = """
            FOR doc IN agent_memory
            FILTER doc.type == "operational" AND doc.tier == "essential"
            FILTER doc.behavioral_requirement != null
            SORT doc.quality_score DESC
            LIMIT 10
            RETURN {
                title: doc.title,
                behavioral_requirement: doc.behavioral_requirement,
                content: SUBSTRING(doc.content, 0, 300),
                quality_score: doc.quality_score
            }
            """

            cursor = self.db.aql.execute(query)
            return list(cursor)

        except Exception as e:
            self.logger.error(f"Error retrieving operational knowledge: {e}")
            return []

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from decision text."""
        # Simple keyword extraction - could be enhanced with NLP
        words = text.lower().split()

        # Filter for meaningful words (length > 3, not common words)
        common_words = {
            "the",
            "and",
            "for",
            "are",
            "but",
            "not",
            "you",
            "all",
            "can",
            "had",
            "her",
            "was",
            "one",
            "our",
            "out",
            "day",
            "get",
            "has",
            "him",
            "his",
            "how",
            "man",
            "new",
            "now",
            "old",
            "see",
            "two",
            "way",
            "who",
            "boy",
            "did",
            "its",
            "let",
            "put",
            "say",
            "she",
            "too",
            "use",
            "this",
            "that",
            "with",
            "have",
            "from",
            "they",
            "know",
            "want",
            "been",
            "good",
            "much",
            "some",
            "time",
            "very",
            "when",
            "come",
            "here",
            "just",
            "like",
            "long",
            "make",
            "many",
            "over",
            "such",
            "take",
            "than",
            "them",
            "well",
            "were",
        }

        keywords = []
        for word in words:
            # Remove punctuation and filter
            clean_word = "".join(c for c in word if c.isalnum())
            if len(clean_word) > 3 and clean_word not in common_words:
                keywords.append(clean_word)

        # Return unique keywords, limit to top 10
        return list(set(keywords))[:10]

    def _calculate_context_quality(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate quality metrics for gathered context."""
        try:
            memories_count = len(context.get("relevant_memories", []))
            concepts_count = len(context.get("cognitive_concepts", []))
            relationships_count = len(context.get("semantic_relationships", []))
            patterns_count = len(context.get("historical_patterns", []))
            operational_count = len(context.get("operational_knowledge", []))

            total_context_items = (
                memories_count
                + concepts_count
                + relationships_count
                + patterns_count
                + operational_count
            )

            # Calculate quality score based on coverage and relevance
            coverage_score = min(
                1.0, total_context_items / 20
            )  # Ideal: 20+ context items

            # Calculate average quality scores where available
            memory_quality = 0.0
            if memories_count > 0:
                memory_scores = [
                    m.get("quality_score", 0.0) for m in context["relevant_memories"]
                ]
                memory_quality = sum(memory_scores) / len(memory_scores)

            concept_quality = 0.0
            if concepts_count > 0:
                concept_scores = [
                    c.get("confidence_score", 0.0)
                    for c in context["cognitive_concepts"]
                ]
                concept_quality = sum(concept_scores) / len(concept_scores)

            overall_quality = (coverage_score + memory_quality + concept_quality) / 3

            return {
                "total_context_items": total_context_items,
                "coverage_score": round(coverage_score, 3),
                "memory_quality_avg": round(memory_quality, 3),
                "concept_quality_avg": round(concept_quality, 3),
                "overall_context_quality": round(overall_quality, 3),
                "context_breakdown": {
                    "memories": memories_count,
                    "concepts": concepts_count,
                    "relationships": relationships_count,
                    "patterns": patterns_count,
                    "operational": operational_count,
                },
            }

        except Exception as e:
            self.logger.error(f"Error calculating context quality: {e}")
            return {"error": str(e)}

    def close(self):
        """Close database connection."""
        if self.client:
            self.client.close()


# Helper function for easy integration
def gather_context_for_decision(
    config: Dict[str, Any],
    decision: str,
    rationale: str,
    max_memories: int = 20,
    max_concepts: int = 10,
    max_relationships: int = 15,
) -> Dict[str, Any]:
    """
    Convenience function to gather context for a decision.

    Args:
        config: Database configuration
        decision: Decision to analyze
        rationale: Provided rationale
        max_memories: Maximum memories to retrieve
        max_concepts: Maximum concepts to retrieve
        max_relationships: Maximum relationships to retrieve

    Returns:
        Dictionary containing relevant context
    """
    gatherer = KnowledgeContextGatherer(config)

    try:
        if not gatherer.connect():
            return {"error": "Failed to connect to database"}

        return gatherer.gather_decision_context(
            decision, rationale, max_memories, max_concepts, max_relationships
        )
    finally:
        gatherer.close()
