#!/usr/bin/env python3
"""
Cognitive Relationship Builder
Transforms sparse graph into useful cognitive knowledge network
"""

import re
from typing import List, Dict, Tuple
from collections import defaultdict


class CognitiveRelationshipBuilder:
    def __init__(self):
        self.relationship_types = {
            "builds_upon": "One concept builds upon another",
            "supports": "One concept supports another's implementation",
            "contradicts": "Concepts are in tension or conflict",
            "enables": "One concept enables another's possibility",
            "requires": "One concept requires another as prerequisite",
            "synthesizes": "Multiple concepts combine into new understanding",
            "reinforces": "Concepts mutually strengthen each other",
            "supersedes": "New concept replaces or improves old one",
        }

    def analyze_semantic_similarity(self, memory1: Dict, memory2: Dict) -> float:
        """Calculate semantic similarity between two memories"""
        content1 = memory1.get("content", "").lower()
        content2 = memory2.get("content", "").lower()
        tags1 = set(memory1.get("tags", []))
        tags2 = set(memory2.get("tags", []))

        # Tag overlap scoring
        tag_overlap = len(tags1.intersection(tags2)) / max(len(tags1.union(tags2)), 1)

        # Content keyword overlap
        words1 = set(re.findall(r"\w+", content1))
        words2 = set(re.findall(r"\w+", content2))
        word_overlap = len(words1.intersection(words2)) / max(
            len(words1.union(words2)), 1
        )

        # Combined similarity score
        return (tag_overlap * 0.6) + (word_overlap * 0.4)

    def detect_relationship_type(
        self, memory1: Dict, memory2: Dict
    ) -> Tuple[str, float]:
        """Detect the type of relationship between two memories"""
        content1 = memory1.get("content", "").lower()
        content2 = memory2.get("content", "").lower()

        # Pattern matching for relationship types
        patterns = {
            "builds_upon": [
                r"based on",
                r"building upon",
                r"extends",
                r"improves",
                r"enhanced",
                r"advanced",
                r"next step",
            ],
            "supports": [
                r"supports",
                r"enables",
                r"facilitates",
                r"helps",
                r"assists",
                r"reinforces",
                r"validates",
            ],
            "contradicts": [
                r"contradicts",
                r"conflicts",
                r"violates",
                r"fails",
                r"incorrect",
                r"wrong",
                r"error",
                r"mistake",
            ],
            "requires": [
                r"requires",
                r"needs",
                r"depends",
                r"prerequisite",
                r"must have",
                r"necessary",
                r"essential",
            ],
            "supersedes": [
                r"replaces",
                r"supersedes",
                r"obsoletes",
                r"deprecated",
                r"new version",
                r"updated",
                r"corrected",
            ],
        }

        best_type = "supports"  # default
        best_score = 0.0

        for rel_type, pattern_list in patterns.items():
            score = 0
            for pattern in pattern_list:
                if re.search(pattern, content1) or re.search(pattern, content2):
                    score += 1

            if score > best_score:
                best_score = score
                best_type = rel_type

        # Convert to confidence score
        confidence = min(best_score / 3.0, 1.0)  # normalize to 0-1
        return best_type, confidence

    def build_domain_clusters(self, memories: List[Dict]) -> Dict[str, List[Dict]]:
        """Group memories by cognitive domain"""
        domains = defaultdict(list)

        domain_keywords = {
            "operational": ["operational", "system", "tool", "command", "protocol"],
            "procedural": ["procedure", "process", "workflow", "step", "method"],
            "semantic": [
                "concept",
                "understanding",
                "knowledge",
                "principle",
                "insight",
            ],
            "technical": ["technical", "implementation", "code", "api", "database"],
            "behavioral": [
                "behavior",
                "rule",
                "directive",
                "enforcement",
                "compliance",
            ],
            "research": [
                "research",
                "analysis",
                "investigation",
                "study",
                "validation",
            ],
        }

        for memory in memories:
            content = memory.get("content", "").lower()
            tags = memory.get("tags", [])
            memory_type = memory.get("memory_type", "unknown")

            # Primary classification by memory_type
            if memory_type in domain_keywords:
                domains[memory_type].append(memory)
                continue

            # Secondary classification by content analysis
            domain_scores = {}
            for domain, keywords in domain_keywords.items():
                score = 0
                for keyword in keywords:
                    if keyword in content:
                        score += 1
                    if keyword in " ".join(tags):
                        score += 2  # tags are more specific
                domain_scores[domain] = score

            # Assign to highest scoring domain
            best_domain = max(domain_scores, key=domain_scores.get)
            if domain_scores[best_domain] > 0:
                domains[best_domain].append(memory)
            else:
                domains["general"].append(memory)

        return dict(domains)

    def generate_relationship_candidates(self, memories: List[Dict]) -> List[Dict]:
        """Generate high-value relationship candidates"""
        candidates = []

        # Build domain clusters first
        domains = self.build_domain_clusters(memories)

        # Intra-domain relationships (within same domain)
        for domain, domain_memories in domains.items():
            for i, mem1 in enumerate(domain_memories):
                for mem2 in domain_memories[i + 1 :]:
                    similarity = self.analyze_semantic_similarity(mem1, mem2)
                    if similarity > 0.3:  # threshold for meaningful similarity
                        rel_type, confidence = self.detect_relationship_type(mem1, mem2)

                        candidates.append(
                            {
                                "from_memory": mem1["_id"],
                                "to_memory": mem2["_id"],
                                "relationship_type": rel_type,
                                "confidence": confidence * similarity,
                                "domain": domain,
                                "relationship_context": "intra_domain",
                            }
                        )

        # Inter-domain relationships (cross-domain connections)
        domain_pairs = [
            ("operational", "procedural"),
            ("procedural", "technical"),
            ("semantic", "behavioral"),
            ("research", "operational"),
        ]

        for domain1, domain2 in domain_pairs:
            if domain1 in domains and domain2 in domains:
                for mem1 in domains[domain1][:5]:  # limit to top 5 per domain
                    for mem2 in domains[domain2][:5]:
                        similarity = self.analyze_semantic_similarity(mem1, mem2)
                        if similarity > 0.4:  # higher threshold for cross-domain
                            rel_type, confidence = self.detect_relationship_type(
                                mem1, mem2
                            )

                            candidates.append(
                                {
                                    "from_memory": mem1["_id"],
                                    "to_memory": mem2["_id"],
                                    "relationship_type": rel_type,
                                    "confidence": confidence * similarity,
                                    "domain": f"{domain1}-{domain2}",
                                    "relationship_context": "inter_domain",
                                }
                            )

        # Sort by confidence and return top candidates
        candidates.sort(key=lambda x: x["confidence"], reverse=True)
        return candidates[:50]  # Top 50 relationships


def analyze_memories_and_build_relationships(memories: List[Dict]) -> Dict:
    """Main function to analyze memories and generate relationship recommendations"""
    builder = CognitiveRelationshipBuilder()

    # Generate relationship candidates
    candidates = builder.generate_relationship_candidates(memories)

    # Build domain analysis
    domains = builder.build_domain_clusters(memories)

    # Generate summary statistics
    stats = {
        "total_memories": len(memories),
        "domains_identified": len(domains),
        "relationship_candidates": len(candidates),
        "high_confidence_relationships": len(
            [c for c in candidates if c["confidence"] > 0.7]
        ),
        "domain_distribution": {domain: len(mems) for domain, mems in domains.items()},
    }

    return {
        "relationship_candidates": candidates,
        "domain_clusters": {k: [m["_id"] for m in v] for k, v in domains.items()},
        "analysis_stats": stats,
        "recommendations": {
            "immediate_relationships": candidates[:15],
            "domain_bridges": [
                c for c in candidates if c["relationship_context"] == "inter_domain"
            ][:10],
            "compound_learning_paths": candidates[:20],
        },
    }


if __name__ == "__main__":
    print("Cognitive Relationship Builder ready for analysis")
