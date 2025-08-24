#!/usr/bin/env python3
"""
Complete System Validation for Dynamic Instructions & Hierarchical Scoping
This script validates the entire flow from project analysis to KB storage to
agent retrieval with proper scoping and isolation.
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue
from sentence_transformers import SentenceTransformer


class SystemValidator:
    """Complete system validation"""

    def __init__(self):
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687", auth=("neo4j", "password")
        )
        self.qdrant = QdrantClient(host="localhost", port=6333)
        self.embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.results = {"passed": [], "failed": [], "warnings": []}

    def validate_kb_connectivity(self) -> bool:
        """Validate Neo4j and Qdrant are accessible"""
        print("\n[1] Validating KB Connectivity...")

        try:
            # Test Neo4j
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                assert result.single()["test"] == 1
            self.results["passed"].append("✓ Neo4j connection successful")

            # Test Qdrant
            collections = self.qdrant.get_collections()
            self.results["passed"].append(
                f"✓ Qdrant connection successful ({len(collections.collections)} collections)"
            )

            return True
        except Exception as e:
            self.results["failed"].append(f"✗ KB connectivity failed: {e}")
            return False

    def validate_project_structure(self) -> bool:
        """Validate master_root project structure exists"""
        print("\n[2] Validating Project Structure...")

        required_paths = [
            "/home/opsvi/master_root",
            "/home/opsvi/master_root/apps",
            "/home/opsvi/master_root/apps/ACCF",
            "/home/opsvi/master_root/apps/project-intelligence",
            "/home/opsvi/master_root/libs",
        ]

        all_exist = True
        for path in required_paths:
            if Path(path).exists():
                self.results["passed"].append(f"✓ {path} exists")
            else:
                self.results["failed"].append(f"✗ {path} missing")
                all_exist = False

        return all_exist

    def validate_instruction_system(self) -> bool:
        """Validate dynamic instruction system is working"""
        print("\n[3] Validating Instruction System...")

        with self.driver.session() as session:
            # Check for instruction types
            result = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.knowledge_type IN ['GLOBAL_INSTRUCTIONS', 'PROJECT_INSTRUCTIONS', 'APP_INSTRUCTIONS']
                RETURN k.knowledge_type as type, count(*) as count
                ORDER BY count DESC
            """
            )

            instruction_counts = {r["type"]: r["count"] for r in result}

            if instruction_counts:
                for itype, count in instruction_counts.items():
                    self.results["passed"].append(f"✓ {itype}: {count} entries")
                return True
            else:
                self.results["warnings"].append(
                    "⚠ No instructions found in KB (run demo_dynamic_instructions.py)"
                )
                return False

    def validate_project_scoping(self) -> bool:
        """Validate project scoping is working correctly"""
        print("\n[4] Validating Project Scoping...")

        with self.driver.session() as session:
            # Check for Project nodes
            project_count = session.run(
                """
                MATCH (p:Project)
                RETURN count(p) as count
            """
            ).single()["count"]

            if project_count > 0:
                self.results["passed"].append(f"✓ {project_count} projects registered")

                # Check for scoped knowledge
                scoped = session.run(
                    """
                    MATCH (p:Project)-[r]->(k:Knowledge)
                    RETURN type(r) as rel_type, count(*) as count
                """
                )

                for record in scoped:
                    self.results["passed"].append(
                        f"✓ {record['count']} {record['rel_type']} relationships"
                    )

                return True
            else:
                self.results["warnings"].append("⚠ No projects registered in KB")
                return False

    def validate_accf_integration(self) -> bool:
        """Validate ACCF is properly integrated"""
        print("\n[5] Validating ACCF Integration...")

        accf_path = Path("/home/opsvi/master_root/apps/ACCF")

        # Check key files
        key_files = [
            accf_path / "src/accf/tools/kb_gatekeeper.py",
            accf_path / "batch_ingest_kb_v2.py",
        ]

        all_found = True
        for file in key_files:
            if file.exists():
                self.results["passed"].append(f"✓ {file.name} exists")
            else:
                self.results["failed"].append(f"✗ {file.name} missing")
                all_found = False

        # Check if ACCF appears in .mcp.json
        mcp_config = Path("/home/opsvi/monitoring/.mcp.json")
        if mcp_config.exists():
            config = json.loads(mcp_config.read_text())
            accf_in_config = False

            for server_name, server_config in config.get("mcpServers", {}).items():
                if "ACCF" in str(
                    server_config.get("env", {}).get("ACCF_PROJECT_ROOT", "")
                ):
                    accf_in_config = True
                    self.results["passed"].append(f"✓ ACCF configured in .mcp.json")
                    break

            if not accf_in_config:
                self.results["warnings"].append(
                    "⚠ ACCF not found in .mcp.json configuration"
                )

        return all_found

    def validate_embedding_sync(self) -> bool:
        """Validate embeddings are synced to Qdrant"""
        print("\n[6] Validating Embedding Sync...")

        with self.driver.session() as session:
            # Count knowledge with embeddings
            kb_count = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.embedding IS NOT NULL
                RETURN count(k) as count
            """
            ).single()["count"]

            # Check Qdrant collections
            try:
                collections = self.qdrant.get_collections().collections
                qdrant_counts = {}

                for collection in collections:
                    info = self.qdrant.get_collection(collection.name)
                    qdrant_counts[collection.name] = info.points_count

                if qdrant_counts:
                    for name, count in qdrant_counts.items():
                        self.results["passed"].append(
                            f"✓ Qdrant collection '{name}': {count} vectors"
                        )

                    if kb_count > 0:
                        self.results["passed"].append(
                            f"✓ Neo4j has {kb_count} embeddings stored"
                        )
                    else:
                        self.results["warnings"].append(
                            f"⚠ Neo4j shows 0 embeddings (may need sync)"
                        )

                    return True
                else:
                    self.results["warnings"].append("⚠ No Qdrant collections found")
                    return False

            except Exception as e:
                self.results["failed"].append(f"✗ Qdrant check failed: {e}")
                return False

    def validate_search_functionality(self) -> bool:
        """Validate semantic search is working"""
        print("\n[7] Validating Search Functionality...")

        test_queries = [
            ("How to use gatekeeper for file selection", "instructions"),
            ("Find complex code analysis", "knowledge_vectors"),
            ("Project structure and conventions", "instructions"),
        ]

        all_working = True
        for query, collection in test_queries:
            try:
                # Check if collection exists
                collections = [
                    c.name for c in self.qdrant.get_collections().collections
                ]
                if collection not in collections:
                    self.results["warnings"].append(
                        f"⚠ Collection '{collection}' not found for query: {query[:30]}..."
                    )
                    continue

                # Generate embedding
                embedding = self.embedder.encode(query).tolist()

                # Search using the correct API
                results = self.qdrant.search(
                    collection_name=collection, query_vector=embedding, limit=3
                )

                if results:
                    self.results["passed"].append(
                        f"✓ Search for '{query[:30]}...' returned {len(results)} results"
                    )
                else:
                    self.results["warnings"].append(
                        f"⚠ No results for: {query[:30]}..."
                    )

            except Exception as e:
                self.results["failed"].append(
                    f"✗ Search failed for '{query[:30]}...': {e}"
                )
                all_working = False

        return all_working

    def validate_end_to_end_flow(self) -> bool:
        """Validate complete end-to-end flow"""
        print("\n[8] Validating End-to-End Flow...")

        # Simulate agent startup query
        with self.driver.session() as session:
            # Query for global instructions
            global_inst = session.run(
                """
                MATCH (k:Knowledge {knowledge_type: 'GLOBAL_INSTRUCTIONS'})
                RETURN k.content as content
                LIMIT 1
            """
            ).single()

            if global_inst:
                self.results["passed"].append(
                    "✓ Agent can retrieve global instructions"
                )
            else:
                self.results["warnings"].append("⚠ No global instructions available")

            # Query for project-specific knowledge
            project_knowledge = session.run(
                """
                MATCH (p:Project)-[:HAS_ANALYSIS|HAS_INSTRUCTION]->(k:Knowledge)
                RETURN p.path as project, k.knowledge_type as type, count(*) as count
                ORDER BY count DESC
                LIMIT 5
            """
            )

            knowledge_by_project = list(project_knowledge)
            if knowledge_by_project:
                self.results["passed"].append(
                    f"✓ Found knowledge in {len(set(r['project'] for r in knowledge_by_project))} projects"
                )
                return True
            else:
                self.results["warnings"].append("⚠ No project-scoped knowledge found")
                return False

    def generate_report(self):
        """Generate validation report"""
        print("\n" + "=" * 70)
        print("VALIDATION REPORT")
        print("=" * 70)

        if self.results["passed"]:
            print("\n✅ PASSED CHECKS:")
            for item in self.results["passed"]:
                print(f"  {item}")

        if self.results["warnings"]:
            print("\n⚠️  WARNINGS:")
            for item in self.results["warnings"]:
                print(f"  {item}")

        if self.results["failed"]:
            print("\n❌ FAILED CHECKS:")
            for item in self.results["failed"]:
                print(f"  {item}")

        # Summary
        total = (
            len(self.results["passed"])
            + len(self.results["warnings"])
            + len(self.results["failed"])
        )
        success_rate = (len(self.results["passed"]) / total * 100) if total > 0 else 0

        print("\n" + "-" * 70)
        print(
            f"Summary: {len(self.results['passed'])} passed, "
            f"{len(self.results['warnings'])} warnings, "
            f"{len(self.results['failed'])} failed"
        )
        print(f"Success Rate: {success_rate:.1f}%")

        if success_rate >= 80:
            print("\n🎉 System is functioning well!")
        elif success_rate >= 60:
            print("\n⚠️  System needs attention - check warnings")
        else:
            print("\n❌ System has critical issues - review failed checks")

    def cleanup(self):
        """Clean up resources"""
        self.driver.close()


def main():
    """Run complete system validation"""
    print("=" * 70)
    print("Complete System Validation")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 70)

    validator = SystemValidator()

    try:
        # Run all validations
        validator.validate_kb_connectivity()
        validator.validate_project_structure()
        validator.validate_instruction_system()
        validator.validate_project_scoping()
        validator.validate_accf_integration()
        validator.validate_embedding_sync()
        validator.validate_search_functionality()
        validator.validate_end_to_end_flow()

        # Generate report
        validator.generate_report()

        print("\n" + "=" * 70)
        print("Validation Complete")
        print("=" * 70)

    finally:
        validator.cleanup()


if __name__ == "__main__":
    main()
