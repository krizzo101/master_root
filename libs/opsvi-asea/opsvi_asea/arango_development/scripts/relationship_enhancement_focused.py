#!/usr/bin/env python3
"""
Focused Relationship Enhancement Script
Following Rule 602 (Multi-Modal Data Architecture) for relationship quality standards

This script addresses the relationship enhancement gaps identified in the main pipeline
and implements intelligent relationship discovery with proper validation.
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Any
from arango import ArangoClient

# ArangoDB Connection Configuration
ARANGO_CONFIG = {
    "host": "http://127.0.0.1:8529",
    "username": "root",
    "password": "arango_dev_password",
    "database": "asea_prod_db",
}


class RelationshipEnhancer:
    """
    Focused relationship enhancement following Rule 602 standards
    """

    def __init__(self):
        self.client = ArangoClient(hosts=ARANGO_CONFIG["host"])
        self.db = self.client.db(
            ARANGO_CONFIG["database"],
            username=ARANGO_CONFIG["username"],
            password=ARANGO_CONFIG["password"],
        )
        self.enhancement_id = f"rel_enhance_{int(time.time())}"
        self.results = {
            "enhancement_id": self.enhancement_id,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "phases": {},
        }

    def execute_relationship_enhancement(self):
        """Execute focused relationship enhancement"""
        print(f"Starting Relationship Enhancement: {self.enhancement_id}")

        try:
            # Phase 1: Fix existing relationship quality scores
            self.fix_existing_relationships()

            # Phase 2: Create intelligent relationships between high-quality entities
            self.create_intelligent_relationships()

            # Phase 3: Validate and score all relationships
            self.validate_all_relationships()

            # Phase 4: Generate enhancement report
            self.generate_enhancement_report()

        except Exception as e:
            print(f"Enhancement failed: {e}")
            raise

        finally:
            self.save_results()

    def fix_existing_relationships(self):
        """Fix existing relationships that failed in the main pipeline"""
        print("Phase 1: Fixing existing relationships...")

        try:
            # Get all relationships
            all_relationships = list(
                self.db.collection("knowledge_relationships").all()
            )

            fixed_count = 0
            for rel in all_relationships:
                try:
                    # Get source and target entities
                    source_doc = (
                        self.db.document(rel["_from"]) if rel.get("_from") else None
                    )
                    target_doc = (
                        self.db.document(rel["_to"]) if rel.get("_to") else None
                    )

                    if not source_doc or not target_doc:
                        continue

                    # Calculate missing fields
                    updates = {}

                    if not rel.get("type"):
                        updates["type"] = self.determine_relationship_type(
                            source_doc, target_doc
                        )

                    if not rel.get("strength"):
                        updates["strength"] = self.calculate_relationship_strength(
                            source_doc, target_doc
                        )

                    if not rel.get("confidence"):
                        updates["confidence"] = self.calculate_relationship_confidence(
                            source_doc, target_doc
                        )

                    if not rel.get("quality_score"):
                        strength = updates.get("strength", rel.get("strength", 0.5))
                        confidence = updates.get(
                            "confidence", rel.get("confidence", 0.5)
                        )
                        updates["quality_score"] = self.calculate_quality_score(
                            strength, confidence, source_doc, target_doc
                        )

                    if not rel.get("validation_status"):
                        quality_score = updates.get(
                            "quality_score", rel.get("quality_score", 0.5)
                        )
                        updates["validation_status"] = self.determine_validation_status(
                            quality_score
                        )

                    # Add enhancement metadata
                    updates.update(
                        {
                            "last_verified": datetime.now(timezone.utc).isoformat(),
                            "verification_method": "focused_relationship_enhancement",
                            "enhanced_by": "relationship_enhancer_v2",
                            "bidirectional": True,
                            "temporal_scope": "current",
                        }
                    )

                    # Update the relationship
                    self.db.collection("knowledge_relationships").update(rel, updates)
                    fixed_count += 1

                except Exception as e:
                    print(
                        f"Failed to fix relationship {rel.get('_id', 'unknown')}: {e}"
                    )
                    continue

            self.results["phases"]["fix_existing"] = {
                "status": "completed",
                "relationships_fixed": fixed_count,
                "total_processed": len(all_relationships),
            }

            print(f"Fixed {fixed_count} relationships")

        except Exception as e:
            self.results["phases"]["fix_existing"] = {
                "status": "failed",
                "error": str(e),
            }
            raise

    def create_intelligent_relationships(self):
        """Create intelligent relationships between entities"""
        print("Phase 2: Creating intelligent relationships...")

        try:
            # Get entities with semantic tags for relationship discovery
            entities_query = """
            FOR entity IN entities
              FILTER entity.semantic_tags != null AND LENGTH(entity.semantic_tags) > 0
              RETURN {
                _id: entity._id,
                title: entity.title,
                type: entity.type,
                category: entity.category,
                semantic_tags: entity.semantic_tags,
                relevance_score: entity.relevance_score,
                completeness_score: entity.completeness_score
              }
            """

            entities = list(self.db.aql.execute(entities_query))
            relationships_created = 0

            # Create relationships between entities with semantic similarity
            for i, entity1 in enumerate(entities):
                for j, entity2 in enumerate(entities[i + 1 :], i + 1):
                    try:
                        # Check if relationship already exists
                        existing_query = """
                        FOR rel IN knowledge_relationships
                          FILTER (rel._from == @from AND rel._to == @to) OR 
                                 (rel._from == @to AND rel._to == @from)
                          RETURN rel
                        """
                        existing = list(
                            self.db.aql.execute(
                                existing_query,
                                {"from": entity1["_id"], "to": entity2["_id"]},
                            )
                        )

                        if existing:
                            continue  # Skip if relationship already exists

                        # Calculate semantic similarity
                        similarity = self.calculate_semantic_similarity(
                            entity1["semantic_tags"], entity2["semantic_tags"]
                        )

                        # Create relationship if similarity is sufficient (lowered threshold)
                        if similarity >= 0.15:  # Lowered from 0.3
                            relationship_type = self.determine_relationship_type(
                                entity1, entity2
                            )
                            strength = min(
                                0.95, similarity * 1.5
                            )  # Boost strength slightly
                            confidence = (
                                entity1.get("completeness_score", 0.5)
                                + entity2.get("completeness_score", 0.5)
                            ) / 2
                            quality_score = self.calculate_quality_score(
                                strength, confidence, entity1, entity2
                            )

                            relationship_data = {
                                "_from": entity1["_id"],
                                "_to": entity2["_id"],
                                "type": relationship_type,
                                "strength": strength,
                                "confidence": confidence,
                                "quality_score": quality_score,
                                "validation_status": self.determine_validation_status(
                                    quality_score
                                ),
                                "bidirectional": True,
                                "temporal_scope": "current",
                                "evidence": [
                                    "semantic_similarity_analysis",
                                    "automated_relationship_discovery",
                                ],
                                "context": f"Discovered through semantic analysis: {similarity:.3f} similarity",
                                "derivation_method": "automated_inference",
                                "created_by": "relationship_enhancer_v2",
                                "last_verified": datetime.now(timezone.utc).isoformat(),
                                "verification_method": "semantic_similarity_analysis",
                            }

                            # Insert relationship
                            self.db.collection("knowledge_relationships").insert(
                                relationship_data
                            )
                            relationships_created += 1

                            if relationships_created % 10 == 0:
                                print(
                                    f"Created {relationships_created} relationships..."
                                )

                    except Exception as e:
                        print(
                            f"Failed to create relationship between {entity1.get('title', 'unknown')} and {entity2.get('title', 'unknown')}: {e}"
                        )
                        continue

            self.results["phases"]["create_intelligent"] = {
                "status": "completed",
                "relationships_created": relationships_created,
                "entities_processed": len(entities),
            }

            print(f"Created {relationships_created} new relationships")

        except Exception as e:
            self.results["phases"]["create_intelligent"] = {
                "status": "failed",
                "error": str(e),
            }
            raise

    def validate_all_relationships(self):
        """Validate and score all relationships"""
        print("Phase 3: Validating all relationships...")

        try:
            # Update validation status for all relationships
            validation_query = """
            FOR rel IN knowledge_relationships
              FILTER rel.quality_score != null
              LET validation_status = rel.quality_score >= 0.8 ? "confirmed" :
                                     rel.quality_score >= 0.6 ? "pending" : "disputed"
              UPDATE rel WITH {
                validation_status: validation_status,
                last_verified: DATE_NOW()
              } IN knowledge_relationships
              RETURN {updated: rel._id, quality_score: rel.quality_score, status: validation_status}
            """

            validation_results = list(self.db.aql.execute(validation_query))

            self.results["phases"]["validate_all"] = {
                "status": "completed",
                "relationships_validated": len(validation_results),
            }

            print(f"Validated {len(validation_results)} relationships")

        except Exception as e:
            self.results["phases"]["validate_all"] = {
                "status": "failed",
                "error": str(e),
            }
            raise

    def generate_enhancement_report(self):
        """Generate comprehensive enhancement report"""
        print("Phase 4: Generating enhancement report...")

        try:
            # Get final metrics
            metrics_query = """
            RETURN {
              total_relationships: LENGTH(FOR r IN knowledge_relationships RETURN r),
              confirmed_relationships: LENGTH(FOR r IN knowledge_relationships FILTER r.validation_status == "confirmed" RETURN r),
              pending_relationships: LENGTH(FOR r IN knowledge_relationships FILTER r.validation_status == "pending" RETURN r),
              disputed_relationships: LENGTH(FOR r IN knowledge_relationships FILTER r.validation_status == "disputed" RETURN r),
              average_quality_score: AVERAGE(FOR r IN knowledge_relationships FILTER r.quality_score != null RETURN r.quality_score),
              average_strength: AVERAGE(FOR r IN knowledge_relationships FILTER r.strength != null RETURN r.strength),
              average_confidence: AVERAGE(FOR r IN knowledge_relationships FILTER r.confidence != null RETURN r.confidence),
              relationship_types: (
                FOR type IN (FOR r IN knowledge_relationships FILTER r.type != null RETURN r.type)
                  COLLECT t = type WITH COUNT INTO count
                  RETURN {type: t, count: count}
              )
            }
            """

            metrics = list(self.db.aql.execute(metrics_query))[0]
            self.results["final_metrics"] = metrics

            # Calculate improvement metrics
            total_entities = len(list(self.db.collection("entities").all()))
            relationship_density = (
                metrics["total_relationships"] / total_entities
                if total_entities > 0
                else 0
            )

            self.results["improvement_summary"] = {
                "relationship_density": relationship_density,
                "validation_coverage": (
                    metrics["confirmed_relationships"]
                    + metrics["pending_relationships"]
                )
                / metrics["total_relationships"]
                if metrics["total_relationships"] > 0
                else 0,
                "quality_distribution": {
                    "confirmed": metrics["confirmed_relationships"],
                    "pending": metrics["pending_relationships"],
                    "disputed": metrics["disputed_relationships"],
                },
            }

            self.results["phases"]["generate_report"] = {
                "status": "completed",
                "metrics_collected": True,
            }

            print("Enhancement report generated successfully")

        except Exception as e:
            self.results["phases"]["generate_report"] = {
                "status": "failed",
                "error": str(e),
            }
            raise

    def save_results(self):
        """Save enhancement results"""
        self.results["end_time"] = datetime.now(timezone.utc).isoformat()
        filename = f"relationship_enhancement_results_{self.enhancement_id}.json"

        try:
            with open(filename, "w") as f:
                json.dump(self.results, f, indent=2)
            print(f"Results saved to: {filename}")
        except Exception as e:
            print(f"Failed to save results: {e}")

    # Helper methods
    def calculate_semantic_similarity(
        self, tags1: List[str], tags2: List[str]
    ) -> float:
        """Calculate semantic similarity between tag lists"""
        if not tags1 or not tags2:
            return 0.0

        intersection = set(tags1) & set(tags2)
        union = set(tags1) | set(tags2)

        return len(intersection) / len(union) if union else 0.0

    def determine_relationship_type(
        self, entity1: Dict[str, Any], entity2: Dict[str, Any]
    ) -> str:
        """Determine relationship type between entities"""
        type1, type2 = entity1.get("type"), entity2.get("type")
        cat1, cat2 = entity1.get("category"), entity2.get("category")

        # Enhanced relationship type determination
        if type1 == "methodology" and type2 == "technique":
            return "uses"
        elif type1 == "concept" and type2 == "concept":
            return "relates_to"
        elif type1 == "system" and type2 == "algorithm":
            return "implements"
        elif type1 == "process" and type2 == "methodology":
            return "follows"
        elif cat1 == cat2:  # Same category
            return "parallels"
        elif type1 == "algorithm" and type2 == "technique":
            return "enables"
        else:
            return "relates_to"

    def calculate_relationship_strength(
        self, entity1: Dict[str, Any], entity2: Dict[str, Any]
    ) -> float:
        """Calculate relationship strength"""
        base_strength = 0.5

        # Boost for same type
        if entity1.get("type") == entity2.get("type"):
            base_strength += 0.2

        # Boost for same category
        if entity1.get("category") == entity2.get("category"):
            base_strength += 0.2

        # Boost for high-quality entities
        avg_completeness = (
            entity1.get("completeness_score", 0.5)
            + entity2.get("completeness_score", 0.5)
        ) / 2
        base_strength += avg_completeness * 0.2

        return min(base_strength, 1.0)

    def calculate_relationship_confidence(
        self, entity1: Dict[str, Any], entity2: Dict[str, Any]
    ) -> float:
        """Calculate relationship confidence"""
        # Base confidence from entity quality
        completeness1 = entity1.get("completeness_score", 0.5)
        completeness2 = entity2.get("completeness_score", 0.5)
        relevance1 = entity1.get("relevance_score", 0.5)
        relevance2 = entity2.get("relevance_score", 0.5)

        return (completeness1 + completeness2 + relevance1 + relevance2) / 4

    def calculate_quality_score(
        self,
        strength: float,
        confidence: float,
        entity1: Dict[str, Any],
        entity2: Dict[str, Any],
    ) -> float:
        """Calculate overall relationship quality score"""
        # Weighted combination of factors
        quality = (strength * 0.4) + (confidence * 0.3)

        # Add bonus for semantic tag overlap
        if entity1.get("semantic_tags") and entity2.get("semantic_tags"):
            similarity = self.calculate_semantic_similarity(
                entity1["semantic_tags"], entity2["semantic_tags"]
            )
            quality += similarity * 0.3
        else:
            quality += 0.15  # Default bonus for entities without tags

        return min(quality, 1.0)

    def determine_validation_status(self, quality_score: float) -> str:
        """Determine validation status from quality score"""
        if quality_score >= 0.8:
            return "confirmed"
        elif quality_score >= 0.6:
            return "pending"
        else:
            return "disputed"


def main():
    """Execute focused relationship enhancement"""
    print("Starting Focused Relationship Enhancement...")
    print("Following Rule 602 (Multi-Modal Data Architecture)")
    print("=" * 60)

    enhancer = RelationshipEnhancer()

    try:
        enhancer.execute_relationship_enhancement()
        print("\n" + "=" * 60)
        print("Relationship Enhancement Completed Successfully!")

    except Exception as e:
        print(f"\nRelationship Enhancement Failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
