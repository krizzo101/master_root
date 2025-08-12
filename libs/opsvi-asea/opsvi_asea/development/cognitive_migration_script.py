#!/usr/bin/env python3
"""
Cognitive Migration Script: Transform all memories to semantic cognitive concepts
"""

import json
import sys

sys.path.append("/home/opsvi/asea/development")

from cognitive_data_transformer import CognitiveDataTransformer


def main():
    transformer = CognitiveDataTransformer()

    print("🧠 Starting Cognitive Data Migration...")
    print("=" * 50)

    # This will output JSON arrays for batch insertion via MCP tools
    all_concepts = []
    all_domains = set()

    # Sample memories to transform (we'll get real ones from database)
    sample_memories = [
        {
            "_key": "1590",
            "title": "Database Connection Issue Resolution - Complete Success",
            "content": "Fixed persistent HTTP 404 database connection errors for python-arango direct connections. Root cause: Incorrect default database name, missing password. Solution: Use absolute configuration with correct credentials.",
            "tags": [
                "database",
                "connectivity",
                "python-arango",
                "configuration",
                "validation",
            ],
            "tier": "essential",
            "foundational": True,
            "validation_status": "validated",
            "behavioral_requirement": True,
        },
        {
            "_key": "1596",
            "title": "DO NOT Ask For Permission to Continue; Operate Continuously",
            "content": "Critical behavioral correction: Never stop and ask for permission ('Please advise') instead of continuing autonomously. Violation: Stopped working after completing basic analysis instead of proceeding with comprehensive solution implementation.",
            "tags": [
                "autonomy",
                "behavioral",
                "continuous_operation",
                "permission",
                "agency",
            ],
            "tier": "essential",
            "foundational": True,
            "behavioral_requirement": True,
        },
        {
            "_key": "1602",
            "title": "MANDATORY: Always Use Absolute Paths in Shell Commands",
            "content": "Critical operational learning: All file paths in shell commands MUST be absolute, starting from workspace root (/home/opsvi/asea/...). Failure cause: Relative paths fail in different execution contexts.",
            "tags": ["shell", "paths", "absolute", "commands", "filesystem"],
            "tier": "essential",
            "foundational": True,
            "behavioral_requirement": True,
        },
    ]

    print(f"📊 Processing {len(sample_memories)} sample memories...")

    for i, memory in enumerate(sample_memories, 1):
        print(f"\n🔄 Processing Memory {i}: {memory['title'][:50]}...")

        concepts = transformer.extract_concepts_from_memory(memory)
        all_concepts.extend(concepts)

        # Track domains
        for concept in concepts:
            all_domains.add(concept["knowledge_domain"])

        print(f"   ✅ Generated {len(concepts)} concepts")

    print("\n📈 Migration Summary:")
    print(f"   🧠 Total Concepts: {len(all_concepts)}")
    print(f"   🏷️  Knowledge Domains: {len(all_domains)}")
    print(f"   🌐 Domains: {', '.join(sorted(all_domains))}")

    # Output for MCP batch insertion
    print("\n🔧 Concepts for batch insertion:")
    print("=" * 50)
    print(json.dumps(all_concepts, indent=2))

    # Generate domain records
    domain_records = []
    for domain in all_domains:
        domain_concepts = [c for c in all_concepts if c["knowledge_domain"] == domain]
        domain_records.append(
            {
                "_key": domain,
                "domain_name": domain.replace("_", " ").title(),
                "concept_count": len(domain_concepts),
                "relationship_density": 0.0,  # Will be calculated after relationships
                "learning_velocity": "medium",
                "key_patterns": list(set([c["concept_type"] for c in domain_concepts])),
            }
        )

    print("\n🏷️  Domain records for batch insertion:")
    print("=" * 50)
    print(json.dumps(domain_records, indent=2))


if __name__ == "__main__":
    main()
