#!/usr/bin/env python3
"""
Process Real Foundational Memories into Cognitive Concepts
Autonomous Intelligence Evolution Phase 1
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Add the development directory to Python path
sys.path.append("/home/opsvi/asea")

from autonomous_cognitive_enhancement import AutonomousCognitiveEnhancer

# Database configuration
DATABASE_CONFIG = {
    "host": "http://127.0.0.1:8531",
    "database": "asea_prod_db",
    "username": "root",
    "password": "arango_production_password",
}


def query_arango_database(query: str, bind_vars: Dict = None) -> List[Dict]:
    """Query ArangoDB directly using python-arango"""
    try:
        from arango import ArangoClient

        # Initialize the client
        client = ArangoClient(hosts=DATABASE_CONFIG["host"])

        # Connect to database
        db = client.db(
            DATABASE_CONFIG["database"],
            username=DATABASE_CONFIG["username"],
            password=DATABASE_CONFIG["password"],
        )

        # Execute query
        cursor = db.aql.execute(query, bind_vars=bind_vars or {})
        return list(cursor)

    except Exception as e:
        print(f"Database query error: {e}")
        return []


def insert_arango_documents(collection: str, documents: List[Dict]) -> List[str]:
    """Insert documents into ArangoDB collection"""
    try:
        from arango import ArangoClient

        # Initialize the client
        client = ArangoClient(hosts=DATABASE_CONFIG["host"])

        # Connect to database
        db = client.db(
            DATABASE_CONFIG["database"],
            username=DATABASE_CONFIG["username"],
            password=DATABASE_CONFIG["password"],
        )

        # Get collection
        collection_obj = db.collection(collection)

        # Insert documents
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


def main():
    """Main processing function for autonomous cognitive enhancement"""
    print("=== AUTONOMOUS COGNITIVE ENHANCEMENT - REAL DATA PROCESSING ===")

    # Initialize enhancer
    enhancer = AutonomousCognitiveEnhancer()

    # Query foundational memories from database
    print("Querying foundational memories from database...")
    foundational_query = """
    FOR memory IN core_memory 
    FILTER memory.foundational == true 
    AND memory.type IN ["critical_learning_correction", "enhanced_core_directive", 
                        "foundational_self_awareness_requirement", "technical_breakthrough_resolution"]
    SORT memory.created DESC 
    LIMIT 10 
    RETURN memory
    """

    foundational_memories = query_arango_database(foundational_query)

    if not foundational_memories:
        print("No foundational memories found. Exiting.")
        return

    print(f"Found {len(foundational_memories)} foundational memories to process")

    # Transform memories to enhanced concepts
    print("Transforming memories to enhanced cognitive concepts...")
    enhanced_concepts = enhancer.transform_foundational_memories(foundational_memories)

    # Save concepts to file
    concepts_file = enhancer.save_enhanced_concepts(enhanced_concepts)

    # Insert concepts into database
    print("Inserting enhanced concepts into cognitive_concepts collection...")
    inserted_ids = insert_arango_documents("cognitive_concepts", enhanced_concepts)

    # Insert relationship mappings
    if enhancer.relationship_mappings:
        print(
            "Inserting relationship mappings into semantic_relationships collection..."
        )
        relationship_ids = insert_arango_documents(
            "semantic_relationships", enhancer.relationship_mappings
        )
        print(f"Inserted {len(relationship_ids)} relationship mappings")

    # Generate comprehensive report
    report = enhancer.generate_enhancement_report(enhanced_concepts)

    # Save report to database
    report_doc = {
        "_key": f"enhancement_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        "report_type": "cognitive_enhancement",
        "report_data": report,
        "processing_metadata": {
            "foundational_memories_processed": len(foundational_memories),
            "concepts_generated": len(enhanced_concepts),
            "concepts_inserted": len(inserted_ids),
            "relationships_generated": len(enhancer.relationship_mappings),
        },
        "created": datetime.utcnow().isoformat() + "Z",
    }

    report_ids = insert_arango_documents("intelligence_analytics", [report_doc])

    # Display results
    print("\n=== AUTONOMOUS COGNITIVE ENHANCEMENT RESULTS ===")
    print(f"Foundational memories processed: {len(foundational_memories)}")
    print(f"Enhanced concepts generated: {len(enhanced_concepts)}")
    print(f"Concepts inserted to database: {len(inserted_ids)}")
    print(f"Relationship mappings generated: {len(enhancer.relationship_mappings)}")
    print(f"Enhancement report saved: {report_ids}")

    print("\nQuality Metrics:")
    quality_metrics = report["quality_metrics"]
    print(f"  High-quality concepts: {quality_metrics['high_quality_concepts']}")
    print(f"  AI-relevant concepts: {quality_metrics['ai_relevant_concepts']}")
    print(
        f"  Compound learning concepts: {quality_metrics['compound_learning_concepts']}"
    )
    print(f"  Quality percentage: {quality_metrics['high_quality_percentage']:.1%}")
    print(
        f"  AI relevance percentage: {quality_metrics['ai_relevance_percentage']:.1%}"
    )

    print("\nDomain Distribution:")
    for domain, count in report["domain_distribution"].items():
        print(f"  {domain}: {count}")

    print("\nAutonomous Intelligence Enhancements:")
    ai_enhancements = report["autonomous_intelligence_enhancements"]
    print(
        f"  Failure prevention concepts: {ai_enhancements['failure_prevention_concepts']}"
    )
    print(
        f"  Behavioral enforcement concepts: {ai_enhancements['behavioral_enforcement_concepts']}"
    )
    print(f"  Self-evolution concepts: {ai_enhancements['self_evolution_concepts']}")

    # Store completion status
    completion_status = {
        "_key": f"cognitive_enhancement_phase1_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        "phase": "cognitive_enhancement_phase_1",
        "status": "completed",
        "autonomous_evolution_step": "foundational_memory_transformation",
        "metrics": report,
        "next_phase": "semantic_relationship_enhancement",
        "compound_learning_enabled": True,
        "created": datetime.utcnow().isoformat() + "Z",
    }

    completion_ids = insert_arango_documents("cognitive_patterns", [completion_status])

    print(f"\nCognitive enhancement phase 1 completed successfully!")
    print(f"Status stored: {completion_ids}")
    print(f"Enhanced concepts file: {concepts_file}")

    # Return for further autonomous processing
    return enhanced_concepts, report, completion_status


if __name__ == "__main__":
    try:
        enhanced_concepts, report, completion_status = main()
        print("\n=== AUTONOMOUS COGNITIVE ENHANCEMENT SUCCESSFUL ===")
    except Exception as e:
        print(f"Error in autonomous cognitive enhancement: {e}")
        sys.exit(1)
