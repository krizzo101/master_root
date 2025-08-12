#!/usr/bin/env python3
"""
Complete Cognitive Architecture Migration System
Transforms ALL foundational knowledge into semantic cognitive concepts
"""

import hashlib
from datetime import datetime
import re


class CompleteCognitiveMigrator:
    def __init__(self):
        self.concept_count = 0
        self.relationship_count = 0
        self.cognitive_concepts = []
        self.semantic_relationships = []

    def analyze_memory_content(self, memory):
        """Extract semantic concepts from memory content"""
        content = memory.get("content", "")
        title = memory.get("title", "")
        tags = memory.get("tags", [])

        # Identify knowledge domain
        domain = self.classify_domain(content, title, tags)

        # Identify concept type
        concept_type = self.classify_concept_type(content, title)

        # Extract key insights
        insights = self.extract_insights(content)

        # Determine abstraction level
        abstraction = self.determine_abstraction_level(content, concept_type)

        # Calculate confidence score
        confidence = self.calculate_confidence(memory)

        return {
            "domain": domain,
            "concept_type": concept_type,
            "insights": insights,
            "abstraction": abstraction,
            "confidence": confidence,
        }

    def classify_domain(self, content, title, tags):
        """Classify knowledge into cognitive domains"""
        content_lower = content.lower() + " " + title.lower()

        # Domain classification patterns
        if any(
            word in content_lower
            for word in ["rule", "behavioral", "protocol", "enforcement", "violation"]
        ):
            return "behavioral"
        elif any(
            word in content_lower
            for word in ["database", "connection", "arangodb", "query", "mcp"]
        ):
            return "infrastructure"
        elif any(
            word in content_lower
            for word in ["research", "analysis", "investigation", "study"]
        ):
            return "research"
        elif any(
            word in content_lower
            for word in ["tool", "command", "shell", "filesystem", "operation"]
        ):
            return "operational"
        elif any(
            word in content_lower
            for word in ["cognitive", "reasoning", "intelligence", "autonomous"]
        ):
            return "cognitive"
        else:
            return "general"

    def classify_concept_type(self, content, title):
        """Classify the type of cognitive concept"""
        content_lower = content.lower() + " " + title.lower()

        if any(
            word in content_lower
            for word in ["failure", "error", "violation", "problem"]
        ):
            return "failure_pattern"
        elif any(
            word in content_lower
            for word in ["success", "complete", "operational", "working"]
        ):
            return "success_pattern"
        elif any(
            word in content_lower
            for word in ["must", "mandatory", "required", "protocol"]
        ):
            return "behavioral_rule"
        elif any(
            word in content_lower
            for word in ["insight", "realization", "learning", "understanding"]
        ):
            return "knowledge_insight"
        elif any(
            word in content_lower
            for word in ["system", "architecture", "implementation"]
        ):
            return "system_knowledge"
        else:
            return "general_knowledge"

    def extract_insights(self, content):
        """Extract key insights from content"""
        insights = []

        # Look for explicit insights
        insight_patterns = [
            r"Key insight[s]?:([^.]+)",
            r"Core realization:([^.]+)",
            r"Critical learning:([^.]+)",
            r"Main finding:([^.]+)",
            r"Root cause[s]?:([^.]+)",
        ]

        for pattern in insight_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            insights.extend([match.strip() for match in matches])

        # Extract problem-solution pairs
        if "problem:" in content.lower() and "solution:" in content.lower():
            problem_match = re.search(r"problem:([^.]+)", content, re.IGNORECASE)
            solution_match = re.search(r"solution:([^.]+)", content, re.IGNORECASE)
            if problem_match and solution_match:
                insights.append("Problem-solution pair identified")

        return insights[:5]  # Limit to top 5 insights

    def determine_abstraction_level(self, content, concept_type):
        """Determine cognitive abstraction level"""
        content_lower = content.lower()

        if concept_type == "behavioral_rule" or "operational" in content_lower:
            return "operational"
        elif "strategic" in content_lower or "architecture" in content_lower:
            return "strategic"
        else:
            return "tactical"

    def calculate_confidence(self, memory):
        """Calculate confidence score based on memory characteristics"""
        score = 0.7  # Base score

        # Higher confidence for validated memories
        if memory.get("foundational") == True:
            score += 0.1

        # Higher confidence for essential tier
        if memory.get("tier") == "essential":
            score += 0.1

        # Higher confidence for detailed content
        content_length = len(memory.get("content", ""))
        if content_length > 500:
            score += 0.05

        # Higher confidence for specific tags
        tags = memory.get("tags", [])
        if len(tags) >= 3:
            score += 0.05

        return min(score, 1.0)

    def create_cognitive_concept(self, memory, analysis):
        """Create a cognitive concept from memory analysis"""
        memory_id = memory.get("_key", "unknown")

        # Generate concept ID
        concept_hash = hashlib.md5(
            f"{analysis['domain']}_{analysis['concept_type']}_{memory_id}".encode()
        ).hexdigest()[:8]
        concept_id = f"{analysis['domain']}_{analysis['concept_type']}_{concept_hash}"

        concept = {
            "_key": concept_id,
            "concept_id": concept_id,
            "semantic_embedding": None,  # For future semantic search
            "knowledge_domain": analysis["domain"],
            "concept_type": analysis["concept_type"],
            "abstraction_level": analysis["abstraction"],
            "confidence_score": analysis["confidence"],
            "evidence_strength": "high" if analysis["confidence"] > 0.8 else "medium",
            "learning_context": {
                "original_memory_id": memory_id,
                "memory_tier": memory.get("tier", "foundational"),
                "foundational": memory.get("foundational", True),
                "validation_method": "systematic_cognitive_migration",
            },
            "knowledge_content": {
                "title": memory.get("title", "Untitled"),
                "original_content": memory.get("content", ""),
                "key_insights": analysis["insights"],
                "original_tags": memory.get("tags", []),
                "memory_type": memory.get("memory_type"),
            },
            "created": datetime.utcnow().isoformat() + "Z",
            "last_validated": datetime.utcnow().isoformat() + "Z",
        }

        self.cognitive_concepts.append(concept)
        self.concept_count += 1
        return concept

    def find_semantic_relationships(self):
        """Discover semantic relationships between cognitive concepts"""
        relationships = []

        for i, concept_a in enumerate(self.cognitive_concepts):
            for j, concept_b in enumerate(self.cognitive_concepts[i + 1 :], i + 1):
                relationship = self.analyze_concept_relationship(concept_a, concept_b)
                if relationship:
                    relationships.append(relationship)

        self.semantic_relationships = relationships
        self.relationship_count = len(relationships)
        return relationships

    def analyze_concept_relationship(self, concept_a, concept_b):
        """Analyze potential relationship between two concepts"""
        # Same domain relationships
        if concept_a["knowledge_domain"] == concept_b["knowledge_domain"]:
            relationship_strength = 0.8
            relationship_type = "compounds_with"

        # Behavioral rule + failure pattern relationships
        elif (
            concept_a["concept_type"] == "behavioral_rule"
            and concept_b["concept_type"] == "failure_pattern"
        ):
            relationship_strength = 0.9
            relationship_type = "prevents"

        # Success pattern + behavioral rule relationships
        elif (
            concept_a["concept_type"] == "success_pattern"
            and concept_b["concept_type"] == "behavioral_rule"
        ):
            relationship_strength = 0.85
            relationship_type = "enables"

        # Knowledge insight relationships
        elif (
            concept_a["concept_type"] == "knowledge_insight"
            or concept_b["concept_type"] == "knowledge_insight"
        ):
            relationship_strength = 0.75
            relationship_type = "informs"

        # System knowledge relationships
        elif (
            concept_a["concept_type"] == "system_knowledge"
            and concept_b["concept_type"] == "system_knowledge"
        ):
            relationship_strength = 0.8
            relationship_type = "integrates_with"

        else:
            return None  # No significant relationship

        # Check for tag overlap to strengthen relationships
        tags_a = set(concept_a["knowledge_content"].get("original_tags", []))
        tags_b = set(concept_b["knowledge_content"].get("original_tags", []))
        tag_overlap = len(tags_a.intersection(tags_b)) / max(
            len(tags_a.union(tags_b)), 1
        )

        if tag_overlap > 0.3:  # Significant tag overlap
            relationship_strength += 0.1

        # Only create relationships above threshold
        if relationship_strength < 0.7:
            return None

        return {
            "_from": f"cognitive_concepts/{concept_a['_key']}",
            "_to": f"cognitive_concepts/{concept_b['_key']}",
            "relationship_type": relationship_type,
            "semantic_similarity": relationship_strength,
            "relationship_strength": "high"
            if relationship_strength > 0.85
            else "medium",
            "discovery_method": "systematic_cognitive_analysis",
            "compound_learning_potential": min(relationship_strength + 0.1, 1.0),
            "evidence": [
                f"domain_alignment_{concept_a['knowledge_domain']}_{concept_b['knowledge_domain']}",
                f"concept_type_synergy_{concept_a['concept_type']}_{concept_b['concept_type']}",
                f"tag_overlap_{tag_overlap:.2f}",
            ],
            "created": datetime.utcnow().isoformat() + "Z",
        }

    def generate_migration_summary(self):
        """Generate comprehensive migration summary"""
        domain_counts = {}
        concept_type_counts = {}

        for concept in self.cognitive_concepts:
            domain = concept["knowledge_domain"]
            concept_type = concept["concept_type"]

            domain_counts[domain] = domain_counts.get(domain, 0) + 1
            concept_type_counts[concept_type] = (
                concept_type_counts.get(concept_type, 0) + 1
            )

        return {
            "migration_complete": True,
            "total_concepts": self.concept_count,
            "total_relationships": self.relationship_count,
            "domain_distribution": domain_counts,
            "concept_type_distribution": concept_type_counts,
            "relationship_density": self.relationship_count
            / max(self.concept_count, 1),
            "migration_timestamp": datetime.utcnow().isoformat() + "Z",
        }


def main():
    print("🧠 COMPLETE COGNITIVE ARCHITECTURE MIGRATION")
    print("=" * 50)

    migrator = CompleteCognitiveMigrator()

    # This would be called with actual memory data
    print("✅ Cognitive migration system ready")
    print("📊 Prepared for systematic knowledge transformation")

    return migrator


if __name__ == "__main__":
    migrator = main()
