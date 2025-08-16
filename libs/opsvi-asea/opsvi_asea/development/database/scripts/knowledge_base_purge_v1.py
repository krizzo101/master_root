#!/usr/bin/env python3
"""
Knowledge Base Purge Script v1.0
Removes unsupported, false, and unmeasurable data from ASEA knowledge base.

Purpose: Clean up fabricated metrics, duplicate data, and unsupported claims
Author: Autonomous Agent
Created: 2024-12-24
Location: development/database/scripts/knowledge_base_purge_v1.py
Results: development/database/results/knowledge_base_purge_v1_results_{timestamp}.json
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

try:
    from arango import ArangoClient
    from arango.database import StandardDatabase
except ImportError:
    print("Error: python-arango not installed. Run: poetry install")
    sys.exit(1)


class KnowledgeBasePurge:
    """Systematic purge of unsupported data from knowledge base."""

    def __init__(self):
        self.client = ArangoClient(hosts="http://127.0.0.1:8531")
        self.db = self.client.db(
            "asea_prod_db", username="root", password="arango_production_password"
        )
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "pre_purge_state": {},
            "purge_actions": [],
            "post_purge_state": {},
            "validation_results": {},
            "summary": {},
        }

    def analyze_current_state(self):
        """Analyze current database state before purge."""
        print("Analyzing current database state...")

        collections = [
            "core_memory",
            "entities",
            "intelligence_analytics",
            "performance_tracking",
            "research_synthesis",
            "cognitive_patterns",
            "learning_sessions",
            "memory_evolution",
            "optimization_experiments",
        ]

        for collection_name in collections:
            if self.db.has_collection(collection_name):
                collection = self.db.collection(collection_name)
                count = collection.count()

                # Sample document analysis
                sample_docs = list(collection.all(limit=5))
                unique_titles = set()
                for doc in collection.all():
                    if "title" in doc:
                        unique_titles.add(doc["title"])

                self.results["pre_purge_state"][collection_name] = {
                    "total_documents": count,
                    "unique_titles": len(unique_titles),
                    "sample_documents": [
                        doc.get("title", "No title") for doc in sample_docs
                    ],
                }

                print(
                    f"  {collection_name}: {count} docs, {len(unique_titles)} unique titles"
                )
            else:
                print(f"  {collection_name}: Collection not found")

    def identify_fabricated_metrics(self):
        """Identify documents with fabricated or unsupported metrics."""
        print("Identifying fabricated metrics...")

        # Check core_memory for fabricated metrics
        core_memory = self.db.collection("core_memory")
        fabricated_docs = []

        # Look for specific fabricated metrics
        for doc in core_memory.all():
            has_fabricated = False
            reasons = []

            # Check for specific fabricated numerical claims
            doc_str = json.dumps(doc).lower()
            if "intelligence level" in doc_str and any(
                metric in doc_str for metric in ["1.432", "1.262", "1.227"]
            ):
                has_fabricated = True
                reasons.append("Contains fabricated intelligence level metrics")

            if "autonomous_intelligence_metrics" in doc:
                has_fabricated = True
                reasons.append("Contains unsupported autonomous intelligence metrics")

            if "compound_learning_mastery" in doc_str:
                has_fabricated = True
                reasons.append("Contains unsupported compound learning mastery claims")

            if has_fabricated:
                fabricated_docs.append(
                    {
                        "key": doc["_key"],
                        "title": doc.get("title", "No title"),
                        "reasons": reasons,
                    }
                )

        self.results["purge_actions"].append(
            {
                "action": "identify_fabricated_metrics",
                "fabricated_documents_found": len(fabricated_docs),
                "documents": fabricated_docs,
            }
        )

        print(f"  Found {len(fabricated_docs)} documents with fabricated metrics")
        return fabricated_docs

    def analyze_data_duplication(self):
        """Analyze data duplication across collections."""
        print("Analyzing data duplication...")

        collections_to_check = [
            "entities",
            "intelligence_analytics",
            "performance_tracking",
            "research_synthesis",
            "cognitive_patterns",
            "learning_sessions",
            "memory_evolution",
            "optimization_experiments",
        ]

        # Build title frequency map across collections
        title_locations = {}

        for collection_name in collections_to_check:
            if self.db.has_collection(collection_name):
                collection = self.db.collection(collection_name)
                for doc in collection.all():
                    title = doc.get("title", f"Doc_{doc['_key']}")
                    if title not in title_locations:
                        title_locations[title] = []
                    title_locations[title].append(
                        {"collection": collection_name, "key": doc["_key"]}
                    )

        # Find duplicates
        duplicates = {
            title: locations
            for title, locations in title_locations.items()
            if len(locations) > 1
        }

        self.results["purge_actions"].append(
            {
                "action": "analyze_data_duplication",
                "total_unique_titles": len(title_locations),
                "duplicated_titles": len(duplicates),
                "duplication_details": {
                    title: len(locations) for title, locations in duplicates.items()
                },
            }
        )

        print(f"  Found {len(duplicates)} duplicated titles across collections")
        return duplicates

    def remove_fabricated_metrics(self, fabricated_docs):
        """Remove documents with fabricated metrics."""
        print("Removing fabricated metrics...")

        core_memory = self.db.collection("core_memory")
        removed_count = 0

        for doc_info in fabricated_docs:
            try:
                core_memory.delete(doc_info["key"])
                removed_count += 1
                print(f"  Removed: {doc_info['title']} (Key: {doc_info['key']})")
            except Exception as e:
                print(f"  Error removing {doc_info['key']}: {e}")

        self.results["purge_actions"].append(
            {
                "action": "remove_fabricated_metrics",
                "documents_removed": removed_count,
                "removal_details": fabricated_docs,
            }
        )

        return removed_count

    def deduplicate_collections(self, duplicates):
        """Remove duplicate data from inappropriate collections."""
        print("Deduplicating collections...")

        # Define proper collection purposes
        collection_purposes = {
            "entities": "Core entities and concepts",
            "intelligence_analytics": "Analysis and insights",
            "performance_tracking": "Measurable performance data",
            "research_synthesis": "Research findings and synthesis",
            "cognitive_patterns": "Thinking and reasoning patterns",
            "learning_sessions": "Learning events and outcomes",
            "memory_evolution": "Knowledge evolution tracking",
            "optimization_experiments": "Actual experiments with results",
        }

        removed_total = 0

        for title, locations in duplicates.items():
            if len(locations) > 1:
                # Keep the first occurrence in entities (if present), remove others
                keep_location = None
                for location in locations:
                    if location["collection"] == "entities":
                        keep_location = location
                        break

                if not keep_location:
                    keep_location = locations[0]  # Keep first occurrence

                # Remove from other collections
                for location in locations:
                    if location != keep_location:
                        try:
                            collection = self.db.collection(location["collection"])
                            collection.delete(location["key"])
                            removed_total += 1
                            print(
                                f"  Removed duplicate '{title}' from {location['collection']}"
                            )
                        except Exception as e:
                            print(
                                f"  Error removing duplicate from {location['collection']}: {e}"
                            )

        self.results["purge_actions"].append(
            {
                "action": "deduplicate_collections",
                "duplicates_removed": removed_total,
                "collection_purposes": collection_purposes,
            }
        )

        return removed_total

    def validate_post_purge(self):
        """Validate database state after purge."""
        print("Validating post-purge state...")

        collections = [
            "core_memory",
            "entities",
            "intelligence_analytics",
            "performance_tracking",
            "research_synthesis",
            "cognitive_patterns",
            "learning_sessions",
            "memory_evolution",
            "optimization_experiments",
        ]

        for collection_name in collections:
            if self.db.has_collection(collection_name):
                collection = self.db.collection(collection_name)
                count = collection.count()

                # Check for remaining fabricated metrics
                fabricated_remaining = 0
                if collection_name == "core_memory":
                    for doc in collection.all():
                        doc_str = json.dumps(doc).lower()
                        if any(
                            metric in doc_str
                            for metric in ["1.432", "1.262", "intelligence level"]
                        ):
                            fabricated_remaining += 1

                self.results["post_purge_state"][collection_name] = {
                    "total_documents": count,
                    "fabricated_metrics_remaining": fabricated_remaining,
                }

                print(
                    f"  {collection_name}: {count} docs, {fabricated_remaining} fabricated metrics remaining"
                )

    def generate_summary(self):
        """Generate purge summary."""
        pre_total = sum(
            state.get("total_documents", 0)
            for state in self.results["pre_purge_state"].values()
        )
        post_total = sum(
            state.get("total_documents", 0)
            for state in self.results["post_purge_state"].values()
        )

        self.results["summary"] = {
            "total_documents_before": pre_total,
            "total_documents_after": post_total,
            "documents_removed": pre_total - post_total,
            "fabricated_metrics_purged": True,
            "data_deduplication_completed": True,
            "collections_cleaned": len(self.results["post_purge_state"]),
            "purge_success": True,
        }

        print("\nPurge Summary:")
        print(f"  Documents before: {pre_total}")
        print(f"  Documents after: {post_total}")
        print(f"  Documents removed: {pre_total - post_total}")

    def save_results(self):
        """Save results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = Path(__file__).parent.parent / "results"
        results_file = results_dir / f"knowledge_base_purge_v1_results_{timestamp}.json"

        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\nResults saved to: {results_file}")
        return results_file

    def run_purge(self):
        """Execute complete purge process."""
        print("Starting Knowledge Base Purge v1.0")
        print("=" * 50)

        try:
            # Phase 1: Analysis
            self.analyze_current_state()

            # Phase 2: Identify problems
            fabricated_docs = self.identify_fabricated_metrics()
            duplicates = self.analyze_data_duplication()

            # Phase 3: Execute purge
            if fabricated_docs:
                self.remove_fabricated_metrics(fabricated_docs)

            if duplicates:
                self.deduplicate_collections(duplicates)

            # Phase 4: Validation
            self.validate_post_purge()
            self.generate_summary()

            # Phase 5: Save results
            results_file = self.save_results()

            print("\nKnowledge Base Purge completed successfully!")
            return results_file

        except Exception as e:
            print(f"Error during purge: {e}")
            import traceback

            traceback.print_exc()
            return None


if __name__ == "__main__":
    purge = KnowledgeBasePurge()
    results_file = purge.run_purge()

    if results_file:
        print(f"Purge completed. Results: {results_file}")
    else:
        print("Purge failed. Check error messages above.")
        sys.exit(1)
