#!/usr/bin/env python3
"""
Autonomous Semantic Relationship Enhancer
Phase 2: Build compound learning through cross-domain semantic relationships
"""

import sys
from datetime import datetime
from typing import Dict, List, Any
import itertools

# Database configuration
DATABASE_CONFIG = {
    "host": "http://127.0.0.1:8531",
    "database": "asea_prod_db",
    "username": "root",
    "password": "arango_production_password",
}


class AutonomousSemanticRelationshipEnhancer:
    """Build compound learning capabilities through advanced semantic relationships"""

    def __init__(self):
        self.relationship_types = {
            "enables": {
                "compound_potential": 0.9,
                "description": "One concept enables another",
                "indicators": ["enables", "allows", "facilitates", "makes possible"],
            },
            "requires": {
                "compound_potential": 0.8,
                "description": "One concept requires another as prerequisite",
                "indicators": ["requires", "needs", "depends on", "prerequisite"],
            },
            "amplifies": {
                "compound_potential": 0.95,
                "description": "One concept amplifies the effectiveness of another",
                "indicators": ["amplifies", "multiplies", "enhances", "boosts"],
            },
            "compounds_with": {
                "compound_potential": 1.0,
                "description": "Concepts work together for compound effects",
                "indicators": ["combined with", "together with", "synergizes"],
            },
            "prevents": {
                "compound_potential": 0.7,
                "description": "One concept prevents problems in another",
                "indicators": ["prevents", "stops", "avoids", "blocks"],
            },
            "builds_upon": {
                "compound_potential": 0.85,
                "description": "One concept builds upon another",
                "indicators": ["builds on", "extends", "enhances", "improves"],
            },
            "contradicts": {
                "compound_potential": 0.6,
                "description": "Concepts contradict each other",
                "indicators": ["contradicts", "conflicts with", "opposes"],
            },
        }

        self.cross_domain_patterns = {
            ("infrastructure", "behavioral"): {
                "typical_relationships": ["enables", "requires"],
                "compound_multiplier": 1.2,
            },
            ("cognitive", "operational"): {
                "typical_relationships": ["amplifies", "builds_upon"],
                "compound_multiplier": 1.15,
            },
            ("technical", "behavioral"): {
                "typical_relationships": ["enables", "prevents"],
                "compound_multiplier": 1.1,
            },
        }

    def query_arango_database(self, query: str, bind_vars: Dict = None) -> List[Dict]:
        """Query ArangoDB directly"""
        try:
            from arango import ArangoClient

            client = ArangoClient(hosts=DATABASE_CONFIG["host"])
            db = client.db(
                DATABASE_CONFIG["database"],
                username=DATABASE_CONFIG["username"],
                password=DATABASE_CONFIG["password"],
            )

            cursor = db.aql.execute(query, bind_vars=bind_vars or {})
            return list(cursor)

        except Exception as e:
            print(f"Database query error: {e}")
            return []

    def insert_arango_documents(
        self, collection: str, documents: List[Dict]
    ) -> List[str]:
        """Insert documents into ArangoDB"""
        try:
            from arango import ArangoClient

            client = ArangoClient(hosts=DATABASE_CONFIG["host"])
            db = client.db(
                DATABASE_CONFIG["database"],
                username=DATABASE_CONFIG["username"],
                password=DATABASE_CONFIG["password"],
            )

            collection_obj = db.collection(collection)

            inserted_ids = []
            for doc in documents:
                try:
                    result = collection_obj.insert(doc)
                    if result:
                        inserted_ids.append(result.get("_id", ""))
                except Exception as e:
                    print(f"Error inserting document: {e}")
                    continue

            return inserted_ids

        except Exception as e:
            print(f"Database insert error: {e}")
            return []

    def discover_semantic_relationships(
        self, concepts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Discover semantic relationships between concepts"""
        relationships = []

        # Analyze all concept pairs for relationships
        for concept1, concept2 in itertools.combinations(concepts, 2):
            discovered_relationships = self.analyze_concept_pair(concept1, concept2)
            relationships.extend(discovered_relationships)

        return relationships

    def analyze_concept_pair(
        self, concept1: Dict[str, Any], concept2: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analyze a pair of concepts for semantic relationships"""
        relationships = []

        # Extract content for analysis
        content1 = self.extract_concept_content(concept1)
        content2 = self.extract_concept_content(concept2)

        # Check for explicit relationship indicators
        explicit_relationships = self.find_explicit_relationships(
            content1, content2, concept1, concept2
        )
        relationships.extend(explicit_relationships)

        # Check for domain-based relationships
        domain_relationships = self.find_domain_relationships(concept1, concept2)
        relationships.extend(domain_relationships)

        # Check for problem-solution relationships
        problem_solution_relationships = self.find_problem_solution_relationships(
            concept1, concept2
        )
        relationships.extend(problem_solution_relationships)

        return relationships

    def extract_concept_content(self, concept: Dict[str, Any]) -> str:
        """Extract all textual content from a concept for analysis"""
        content_parts = []

        # Add basic fields
        content_parts.append(concept.get("concept_id", ""))

        # Add knowledge content
        knowledge_content = concept.get("knowledge_content", {})
        content_parts.append(knowledge_content.get("title", ""))
        content_parts.append(knowledge_content.get("problem", ""))
        content_parts.append(knowledge_content.get("solution", ""))
        content_parts.append(knowledge_content.get("prevention", ""))

        # Add key insights
        key_insights = knowledge_content.get("key_insights", [])
        content_parts.extend(key_insights)

        return " ".join(filter(None, content_parts)).lower()

    def find_explicit_relationships(
        self, content1: str, content2: str, concept1: Dict, concept2: Dict
    ) -> List[Dict[str, Any]]:
        """Find explicit relationship indicators between concept contents"""
        relationships = []

        for rel_type, rel_info in self.relationship_types.items():
            for indicator in rel_info["indicators"]:
                # Check if concept1 content mentions concept2 with relationship indicator
                if self.check_relationship_indicator(content1, content2, indicator):
                    relationship = self.create_relationship(
                        concept1,
                        concept2,
                        rel_type,
                        "explicit_textual",
                        rel_info["compound_potential"],
                    )
                    relationships.append(relationship)

                # Check reverse relationship
                elif self.check_relationship_indicator(content2, content1, indicator):
                    relationship = self.create_relationship(
                        concept2,
                        concept1,
                        rel_type,
                        "explicit_textual",
                        rel_info["compound_potential"],
                    )
                    relationships.append(relationship)

        return relationships

    def check_relationship_indicator(
        self, content1: str, content2: str, indicator: str
    ) -> bool:
        """Check if content1 mentions content2 with a relationship indicator"""
        # Extract key terms from content2
        content2_terms = [term for term in content2.split() if len(term) > 4][
            :5
        ]  # Top 5 terms

        # Check if content1 contains the indicator near content2 terms
        for term in content2_terms:
            if term in content1 and indicator in content1:
                # Check if they're within reasonable proximity (simple approach)
                content1_words = content1.split()
                try:
                    term_pos = content1_words.index(term)
                    indicator_positions = [
                        i for i, word in enumerate(content1_words) if indicator in word
                    ]

                    # If indicator is within 10 words of the term
                    for ind_pos in indicator_positions:
                        if abs(term_pos - ind_pos) <= 10:
                            return True
                except ValueError:
                    continue

        return False

    def find_domain_relationships(
        self, concept1: Dict, concept2: Dict
    ) -> List[Dict[str, Any]]:
        """Find relationships based on knowledge domain patterns"""
        relationships = []

        domain1 = concept1.get("knowledge_domain", "")
        domain2 = concept2.get("knowledge_domain", "")

        if domain1 != domain2:  # Cross-domain relationships are most valuable
            domain_pair = tuple(sorted([domain1, domain2]))

            if domain_pair in self.cross_domain_patterns:
                pattern = self.cross_domain_patterns[domain_pair]

                for rel_type in pattern["typical_relationships"]:
                    # Create relationship with domain-based compound potential
                    base_potential = self.relationship_types[rel_type][
                        "compound_potential"
                    ]
                    enhanced_potential = min(
                        base_potential * pattern["compound_multiplier"], 1.0
                    )

                    relationship = self.create_relationship(
                        concept1,
                        concept2,
                        rel_type,
                        "cross_domain_pattern",
                        enhanced_potential,
                    )
                    relationships.append(relationship)

        return relationships

    def find_problem_solution_relationships(
        self, concept1: Dict, concept2: Dict
    ) -> List[Dict[str, Any]]:
        """Find problem-solution relationships between concepts"""
        relationships = []

        # Extract problem/solution content
        content1 = concept1.get("knowledge_content", {})
        content2 = concept2.get("knowledge_content", {})

        problem1 = content1.get("problem", "").lower()
        solution1 = content1.get("solution", "").lower()
        problem2 = content2.get("problem", "").lower()
        solution2 = content2.get("solution", "").lower()

        # Check if one concept's solution relates to another's problem
        if problem1 and solution2:
            similarity_score = self.calculate_content_similarity(problem1, solution2)
            if similarity_score > 0.3:  # Threshold for relationship
                relationship = self.create_relationship(
                    concept2, concept1, "enables", "problem_solution_matching", 0.85
                )
                relationships.append(relationship)

        if problem2 and solution1:
            similarity_score = self.calculate_content_similarity(problem2, solution1)
            if similarity_score > 0.3:
                relationship = self.create_relationship(
                    concept1, concept2, "enables", "problem_solution_matching", 0.85
                )
                relationships.append(relationship)

        return relationships

    def calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Calculate simple content similarity score"""
        if not content1 or not content2:
            return 0.0

        # Simple word overlap approach
        words1 = set(content1.split())
        words2 = set(content2.split())

        if not words1 or not words2:
            return 0.0

        overlap = len(words1.intersection(words2))
        total = len(words1.union(words2))

        return overlap / total if total > 0 else 0.0

    def create_relationship(
        self,
        from_concept: Dict,
        to_concept: Dict,
        relationship_type: str,
        derivation_method: str,
        compound_potential: float,
    ) -> Dict[str, Any]:
        """Create a semantic relationship document"""

        # Generate relationship ID
        rel_id = f"{from_concept['concept_id']}_{relationship_type}_{to_concept['concept_id']}"

        return {
            "_key": rel_id.replace("/", "_").replace("-", "_")[
                :250
            ],  # ArangoDB key constraints
            "_from": f"cognitive_concepts/{from_concept['_key']}",
            "_to": f"cognitive_concepts/{to_concept['_key']}",
            "relationship_type": relationship_type,
            "compound_learning_potential": compound_potential,
            "confidence_score": self.calculate_relationship_confidence(
                from_concept, to_concept, derivation_method
            ),
            "relationship_metadata": {
                "derivation_method": derivation_method,
                "from_domain": from_concept.get("knowledge_domain", ""),
                "to_domain": to_concept.get("knowledge_domain", ""),
                "cross_domain": from_concept.get("knowledge_domain")
                != to_concept.get("knowledge_domain"),
                "discovery_timestamp": datetime.utcnow().isoformat() + "Z",
            },
            "autonomous_intelligence_metrics": {
                "amplification_factor": self.calculate_amplification_factor(
                    compound_potential
                ),
                "cognitive_integration_score": self.calculate_cognitive_integration_score(
                    from_concept, to_concept
                ),
                "behavioral_reinforcement": self.calculate_behavioral_reinforcement(
                    from_concept, to_concept
                ),
            },
            "created": datetime.utcnow().isoformat() + "Z",
        }

    def calculate_relationship_confidence(
        self, from_concept: Dict, to_concept: Dict, method: str
    ) -> float:
        """Calculate confidence score for the relationship"""
        base_confidence = {
            "explicit_textual": 0.85,
            "cross_domain_pattern": 0.75,
            "problem_solution_matching": 0.8,
        }.get(method, 0.7)

        # Boost confidence for high-quality concepts
        from_quality = from_concept.get("confidence_score", 0.5)
        to_quality = to_concept.get("confidence_score", 0.5)

        quality_boost = (from_quality + to_quality) / 2 * 0.1

        return min(base_confidence + quality_boost, 1.0)

    def calculate_amplification_factor(self, compound_potential: float) -> float:
        """Calculate how much this relationship amplifies capabilities"""
        # High compound potential means high amplification
        return compound_potential * 1.2  # Can exceed 1.0 for multiplicative effects

    def calculate_cognitive_integration_score(
        self, from_concept: Dict, to_concept: Dict
    ) -> float:
        """Calculate how well concepts integrate cognitively"""
        integration_score = 0.5  # Base score

        # Cross-domain integration is valuable
        if from_concept.get("knowledge_domain") != to_concept.get("knowledge_domain"):
            integration_score += 0.2

        # High AI relevance concepts integrate well
        from_ai_relevance = from_concept.get("autonomous_intelligence_metrics", {}).get(
            "ai_relevance_score", 0.5
        )
        to_ai_relevance = to_concept.get("autonomous_intelligence_metrics", {}).get(
            "ai_relevance_score", 0.5
        )

        integration_score += (from_ai_relevance + to_ai_relevance) / 2 * 0.3

        return min(integration_score, 1.0)

    def calculate_behavioral_reinforcement(
        self, from_concept: Dict, to_concept: Dict
    ) -> float:
        """Calculate how much this relationship reinforces behavioral changes"""
        reinforcement = 0.3  # Base reinforcement

        # Behavioral concepts create strong reinforcement
        if "behavioral" in from_concept.get(
            "knowledge_domain", ""
        ) or "behavioral" in to_concept.get("knowledge_domain", ""):
            reinforcement += 0.3

        # Enhanced directives create strong reinforcement
        if (
            from_concept.get("concept_type") == "enhanced_core_directive"
            or to_concept.get("concept_type") == "enhanced_core_directive"
        ):
            reinforcement += 0.4

        return min(reinforcement, 1.0)


def main():
    """Main autonomous semantic relationship enhancement"""
    print("=== AUTONOMOUS SEMANTIC RELATIONSHIP ENHANCEMENT ===")

    enhancer = AutonomousSemanticRelationshipEnhancer()

    # Query existing cognitive concepts
    print("Querying existing cognitive concepts...")
    concepts_query = "FOR concept IN cognitive_concepts RETURN concept"
    concepts = enhancer.query_arango_database(concepts_query)

    if len(concepts) < 2:
        print("Need at least 2 concepts for relationship discovery. Exiting.")
        return

    print(f"Found {len(concepts)} concepts for relationship analysis")

    # Discover semantic relationships
    print("Discovering semantic relationships...")
    relationships = enhancer.discover_semantic_relationships(concepts)

    print(f"Discovered {len(relationships)} semantic relationships")

    # Insert relationships into database
    if relationships:
        print("Inserting relationships into semantic_relationships collection...")
        inserted_ids = enhancer.insert_arango_documents(
            "semantic_relationships", relationships
        )
        print(f"Successfully inserted {len(inserted_ids)} relationships")

    # Generate enhancement report
    report = {
        "enhancement_phase": "semantic_relationship_enhancement",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "concepts_analyzed": len(concepts),
        "relationships_discovered": len(relationships),
        "relationships_inserted": len(inserted_ids) if relationships else 0,
        "relationship_type_distribution": {},
        "cross_domain_relationships": 0,
        "high_compound_potential_relationships": 0,
        "compound_learning_metrics": {
            "average_compound_potential": 0,
            "max_amplification_factor": 0,
            "cognitive_integration_score": 0,
        },
    }

    # Analyze relationship metrics
    if relationships:
        compound_potentials = [
            r.get("compound_learning_potential", 0) for r in relationships
        ]
        amplification_factors = [
            r.get("autonomous_intelligence_metrics", {}).get("amplification_factor", 0)
            for r in relationships
        ]
        integration_scores = [
            r.get("autonomous_intelligence_metrics", {}).get(
                "cognitive_integration_score", 0
            )
            for r in relationships
        ]

        # Update report metrics
        report["compound_learning_metrics"].update(
            {
                "average_compound_potential": sum(compound_potentials)
                / len(compound_potentials),
                "max_amplification_factor": max(amplification_factors)
                if amplification_factors
                else 0,
                "cognitive_integration_score": sum(integration_scores)
                / len(integration_scores)
                if integration_scores
                else 0,
            }
        )

        # Count relationship types and cross-domain relationships
        for relationship in relationships:
            rel_type = relationship.get("relationship_type", "unknown")
            report["relationship_type_distribution"][rel_type] = (
                report["relationship_type_distribution"].get(rel_type, 0) + 1
            )

            if relationship.get("relationship_metadata", {}).get("cross_domain", False):
                report["cross_domain_relationships"] += 1

            if relationship.get("compound_learning_potential", 0) > 0.8:
                report["high_compound_potential_relationships"] += 1

    # Save report to database
    report_doc = {
        "_key": f"semantic_enhancement_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        "report_type": "semantic_relationship_enhancement",
        "report_data": report,
        "created": datetime.utcnow().isoformat() + "Z",
    }

    report_ids = enhancer.insert_arango_documents(
        "intelligence_analytics", [report_doc]
    )

    # Display results
    print("\n=== SEMANTIC RELATIONSHIP ENHANCEMENT RESULTS ===")
    print(f"Concepts analyzed: {report['concepts_analyzed']}")
    print(f"Relationships discovered: {report['relationships_discovered']}")
    print(f"Relationships inserted: {report['relationships_inserted']}")
    print(f"Cross-domain relationships: {report['cross_domain_relationships']}")
    print(
        f"High compound potential relationships: {report['high_compound_potential_relationships']}"
    )

    print("\nCompound Learning Metrics:")
    metrics = report["compound_learning_metrics"]
    print(f"  Average compound potential: {metrics['average_compound_potential']:.3f}")
    print(f"  Max amplification factor: {metrics['max_amplification_factor']:.3f}")
    print(
        f"  Cognitive integration score: {metrics['cognitive_integration_score']:.3f}"
    )

    print("\nRelationship Type Distribution:")
    for rel_type, count in report["relationship_type_distribution"].items():
        print(f"  {rel_type}: {count}")

    print(f"\nEnhancement report saved: {report_ids}")

    return relationships, report


if __name__ == "__main__":
    try:
        relationships, report = main()
        print("\n=== AUTONOMOUS SEMANTIC RELATIONSHIP ENHANCEMENT SUCCESSFUL ===")
    except Exception as e:
        print(f"Error in semantic relationship enhancement: {e}")
        sys.exit(1)
