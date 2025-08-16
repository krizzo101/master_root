#!/usr/bin/env python3
"""
Bulk Cognitive Migration: Transform ALL memories efficiently
"""

import sys

sys.path.append("/home/opsvi/asea/development")

from cognitive_data_transformer import CognitiveDataTransformer


def process_all_memories(memories_data):
    """Process all memories in bulk"""
    transformer = CognitiveDataTransformer()

    all_concepts = []
    all_domains = set()

    print(f"🚀 BULK PROCESSING {len(memories_data)} memories...")

    for memory in memories_data:
        concepts = transformer.extract_concepts_from_memory(memory)
        all_concepts.extend(concepts)

        for concept in concepts:
            all_domains.add(concept["knowledge_domain"])

    # Generate domain records
    domain_records = []
    for domain in all_domains:
        domain_concepts = [c for c in all_concepts if c["knowledge_domain"] == domain]
        domain_records.append(
            {
                "_key": domain,
                "domain_name": domain.replace("_", " ").title(),
                "concept_count": len(domain_concepts),
                "relationship_density": 0.0,
                "learning_velocity": "medium",
                "key_patterns": list(set([c["concept_type"] for c in domain_concepts])),
            }
        )

    print("✅ BULK RESULTS:")
    print(f"   🧠 Concepts: {len(all_concepts)}")
    print(f"   🏷️  Domains: {len(all_domains)}")

    return all_concepts, domain_records


def main():
    # This will be called with the actual memory data
    print("🔧 Bulk Cognitive Migration Ready")
    print("Call with: process_all_memories(memory_data)")


if __name__ == "__main__":
    main()
