#!/usr/bin/env python3
"""
Knowledge Base Export/Import Utilities
Enables backup, migration, and sharing of knowledge bases
"""

import json
import logging
import os
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

import pandas as pd
import yaml
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """Supported export formats"""

    JSON = "json"
    CSV = "csv"
    YAML = "yaml"
    CYPHER = "cypher"
    MARKDOWN = "markdown"


class KnowledgeExporter:
    """Export knowledge from Neo4j"""

    def __init__(
        self, neo4j_uri: str = None, neo4j_user: str = None, neo4j_password: str = None
    ):
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD", "password")
        self.driver = GraphDatabase.driver(
            self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password)
        )

    def export_knowledge(
        self,
        output_path: str,
        format: ExportFormat = ExportFormat.JSON,
        filters: Optional[Dict] = None,
        include_embeddings: bool = False,
        include_relationships: bool = True,
    ) -> Dict:
        """Export knowledge to file"""

        # Fetch knowledge
        knowledge = self._fetch_knowledge(filters, include_embeddings)

        # Fetch relationships if requested
        relationships = []
        if include_relationships:
            relationships = self._fetch_relationships(filters)

        # Export based on format
        if format == ExportFormat.JSON:
            return self._export_json(output_path, knowledge, relationships)
        elif format == ExportFormat.CSV:
            return self._export_csv(output_path, knowledge, relationships)
        elif format == ExportFormat.YAML:
            return self._export_yaml(output_path, knowledge, relationships)
        elif format == ExportFormat.CYPHER:
            return self._export_cypher(output_path, knowledge, relationships)
        elif format == ExportFormat.MARKDOWN:
            return self._export_markdown(output_path, knowledge, relationships)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _fetch_knowledge(
        self, filters: Optional[Dict], include_embeddings: bool
    ) -> List[Dict]:
        """Fetch knowledge from database"""

        # Build query
        where_clauses = []
        params = {}

        if filters:
            if "type" in filters:
                where_clauses.append("k.knowledge_type = $type")
                params["type"] = filters["type"]
            if "min_confidence" in filters:
                where_clauses.append("k.confidence_score >= $min_confidence")
                params["min_confidence"] = filters["min_confidence"]
            if "since" in filters:
                where_clauses.append("k.created_at >= $since")
                params["since"] = filters["since"]

        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Exclude embeddings if not needed (they're large)
        if include_embeddings:
            query = f"""
            MATCH (k:Knowledge)
            WHERE {where_clause}
            RETURN k
            ORDER BY k.created_at DESC
            """
        else:
            query = f"""
            MATCH (k:Knowledge)
            WHERE {where_clause}
            RETURN k {{.*, embedding: null}} as k
            ORDER BY k.created_at DESC
            """

        knowledge = []
        with self.driver.session() as session:
            result = session.run(query, **params)
            for record in result:
                k = dict(record["k"])
                # Convert datetime objects to strings
                for key, value in k.items():
                    if hasattr(value, "isoformat"):
                        k[key] = value.isoformat()
                knowledge.append(k)

        return knowledge

    def _fetch_relationships(self, filters: Optional[Dict]) -> List[Dict]:
        """Fetch relationships from database"""

        query = """
        MATCH (k1:Knowledge)-[r:RELATED_TO]->(k2:Knowledge)
        RETURN k1.knowledge_id as source,
               k2.knowledge_id as target,
               r.similarity as similarity,
               r.created_at as created_at,
               r.created_by as created_by
        """

        relationships = []
        with self.driver.session() as session:
            result = session.run(query)
            for record in result:
                rel = dict(record)
                # Convert datetime to string
                if rel.get("created_at"):
                    rel["created_at"] = rel["created_at"].isoformat()
                relationships.append(rel)

        return relationships

    def _export_json(
        self, output_path: str, knowledge: List[Dict], relationships: List[Dict]
    ) -> Dict:
        """Export to JSON format"""

        data = {
            "metadata": {
                "export_date": datetime.utcnow().isoformat(),
                "source": self.neo4j_uri,
                "version": "1.0",
                "counts": {
                    "knowledge": len(knowledge),
                    "relationships": len(relationships),
                },
            },
            "knowledge": knowledge,
            "relationships": relationships,
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Exported {len(knowledge)} knowledge entries to {output_path}")
        return data["metadata"]

    def _export_csv(
        self, output_path: str, knowledge: List[Dict], relationships: List[Dict]
    ) -> Dict:
        """Export to CSV format"""

        # Export knowledge
        knowledge_df = pd.DataFrame(knowledge)
        knowledge_path = output_path.replace(".csv", "_knowledge.csv")
        knowledge_df.to_csv(knowledge_path, index=False)

        # Export relationships
        if relationships:
            relationships_df = pd.DataFrame(relationships)
            relationships_path = output_path.replace(".csv", "_relationships.csv")
            relationships_df.to_csv(relationships_path, index=False)

        logger.info(f"Exported to CSV: {knowledge_path}")

        return {
            "knowledge_file": knowledge_path,
            "relationships_file": relationships_path if relationships else None,
            "knowledge_count": len(knowledge),
            "relationships_count": len(relationships),
        }

    def _export_yaml(
        self, output_path: str, knowledge: List[Dict], relationships: List[Dict]
    ) -> Dict:
        """Export to YAML format"""

        data = {
            "metadata": {
                "export_date": datetime.utcnow().isoformat(),
                "source": self.neo4j_uri,
                "version": "1.0",
            },
            "knowledge": knowledge,
            "relationships": relationships,
        }

        with open(output_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Exported to YAML: {output_path}")
        return data["metadata"]

    def _export_cypher(
        self, output_path: str, knowledge: List[Dict], relationships: List[Dict]
    ) -> Dict:
        """Export as Cypher queries for import"""

        with open(output_path, "w") as f:
            f.write("// Knowledge Base Export - Cypher Queries\n")
            f.write(f"// Generated: {datetime.utcnow().isoformat()}\n\n")

            # Write knowledge creation queries
            f.write("// Create Knowledge Nodes\n")
            for k in knowledge:
                props = json.dumps(k, default=str)
                f.write(f"CREATE (k:Knowledge {props});\n")

            f.write("\n// Create Relationships\n")
            for r in relationships:
                f.write(f"MATCH (k1:Knowledge {{knowledge_id: '{r['source']}'}})\n")
                f.write(f"MATCH (k2:Knowledge {{knowledge_id: '{r['target']}'}})\n")
                f.write("CREATE (k1)-[:RELATED_TO {")
                f.write(f"similarity: {r.get('similarity', 0)}, ")
                f.write(f"created_at: datetime('{r.get('created_at', '')}')")
                f.write("}]->(k2);\n\n")

        logger.info(f"Exported Cypher queries to {output_path}")
        return {
            "file": output_path,
            "knowledge_count": len(knowledge),
            "relationships_count": len(relationships),
        }

    def _export_markdown(
        self, output_path: str, knowledge: List[Dict], relationships: List[Dict]
    ) -> Dict:
        """Export to Markdown format for documentation"""

        with open(output_path, "w") as f:
            f.write("# Knowledge Base Export\n\n")
            f.write(f"**Export Date**: {datetime.utcnow().isoformat()}\n")
            f.write(f"**Total Entries**: {len(knowledge)}\n")
            f.write(f"**Total Relationships**: {len(relationships)}\n\n")

            # Group by type
            by_type = {}
            for k in knowledge:
                k_type = k.get("knowledge_type", "UNKNOWN")
                if k_type not in by_type:
                    by_type[k_type] = []
                by_type[k_type].append(k)

            # Write each type
            for k_type, entries in sorted(by_type.items()):
                f.write(f"## {k_type} ({len(entries)} entries)\n\n")

                for entry in entries[:10]:  # Limit to first 10 per type
                    f.write(f"### {entry.get('knowledge_id', 'Unknown')}\n")
                    f.write(f"**Confidence**: {entry.get('confidence_score', 0):.2%}\n")
                    f.write(f"**Created**: {entry.get('created_at', 'Unknown')}\n\n")
                    f.write(f"{entry.get('content', 'No content')}\n\n")

                    if entry.get("context"):
                        f.write("**Context**:\n```json\n")
                        f.write(json.dumps(entry["context"], indent=2))
                        f.write("\n```\n\n")

                    f.write("---\n\n")

                if len(entries) > 10:
                    f.write(f"*... and {len(entries) - 10} more entries*\n\n")

        logger.info(f"Exported Markdown to {output_path}")
        return {"file": output_path, "knowledge_count": len(knowledge)}

    def close(self):
        """Close database connection"""
        self.driver.close()


class KnowledgeImporter:
    """Import knowledge to Neo4j"""

    def __init__(
        self, neo4j_uri: str = None, neo4j_user: str = None, neo4j_password: str = None
    ):
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD", "password")
        self.driver = GraphDatabase.driver(
            self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password)
        )

    def import_knowledge(
        self,
        input_path: str,
        format: ExportFormat = ExportFormat.JSON,
        merge_strategy: str = "skip",  # skip, overwrite, merge
        validate: bool = True,
    ) -> Dict:
        """Import knowledge from file"""

        if format == ExportFormat.JSON:
            return self._import_json(input_path, merge_strategy, validate)
        elif format == ExportFormat.CSV:
            return self._import_csv(input_path, merge_strategy, validate)
        elif format == ExportFormat.YAML:
            return self._import_yaml(input_path, merge_strategy, validate)
        elif format == ExportFormat.CYPHER:
            return self._import_cypher(input_path)
        else:
            raise ValueError(f"Unsupported import format: {format}")

    def _import_json(
        self, input_path: str, merge_strategy: str, validate: bool
    ) -> Dict:
        """Import from JSON format"""

        with open(input_path, "r") as f:
            data = json.load(f)

        knowledge = data.get("knowledge", [])
        relationships = data.get("relationships", [])

        imported_knowledge = self._import_knowledge_entries(
            knowledge, merge_strategy, validate
        )
        imported_relationships = self._import_relationships(relationships)

        return {
            "imported_knowledge": imported_knowledge,
            "imported_relationships": imported_relationships,
            "skipped_knowledge": len(knowledge) - imported_knowledge,
            "skipped_relationships": len(relationships) - imported_relationships,
        }

    def _import_csv(self, input_path: str, merge_strategy: str, validate: bool) -> Dict:
        """Import from CSV format"""

        # Import knowledge
        knowledge_path = input_path.replace(".csv", "_knowledge.csv")
        if not os.path.exists(knowledge_path):
            knowledge_path = input_path

        knowledge_df = pd.read_csv(knowledge_path)
        knowledge = knowledge_df.to_dict("records")

        # Import relationships if available
        relationships = []
        relationships_path = input_path.replace(".csv", "_relationships.csv")
        if os.path.exists(relationships_path):
            relationships_df = pd.read_csv(relationships_path)
            relationships = relationships_df.to_dict("records")

        imported_knowledge = self._import_knowledge_entries(
            knowledge, merge_strategy, validate
        )
        imported_relationships = self._import_relationships(relationships)

        return {
            "imported_knowledge": imported_knowledge,
            "imported_relationships": imported_relationships,
        }

    def _import_yaml(
        self, input_path: str, merge_strategy: str, validate: bool
    ) -> Dict:
        """Import from YAML format"""

        with open(input_path, "r") as f:
            data = yaml.safe_load(f)

        knowledge = data.get("knowledge", [])
        relationships = data.get("relationships", [])

        imported_knowledge = self._import_knowledge_entries(
            knowledge, merge_strategy, validate
        )
        imported_relationships = self._import_relationships(relationships)

        return {
            "imported_knowledge": imported_knowledge,
            "imported_relationships": imported_relationships,
        }

    def _import_cypher(self, input_path: str) -> Dict:
        """Import from Cypher queries"""

        with open(input_path, "r") as f:
            queries = f.read()

        # Execute queries
        executed = 0
        with self.driver.session() as session:
            for query in queries.split(";"):
                query = query.strip()
                if query and not query.startswith("//"):
                    try:
                        session.run(query)
                        executed += 1
                    except Exception as e:
                        logger.error(f"Failed to execute query: {e}")

        return {"executed_queries": executed}

    def _import_knowledge_entries(
        self, knowledge: List[Dict], merge_strategy: str, validate: bool
    ) -> int:
        """Import knowledge entries"""

        imported = 0

        with self.driver.session() as session:
            for entry in knowledge:
                try:
                    # Check if exists
                    exists_query = """
                    MATCH (k:Knowledge {knowledge_id: $id})
                    RETURN k
                    """

                    result = session.run(exists_query, id=entry.get("knowledge_id"))
                    existing = result.single()

                    if existing:
                        if merge_strategy == "skip":
                            continue
                        elif merge_strategy == "overwrite":
                            # Delete existing
                            session.run(
                                "MATCH (k:Knowledge {knowledge_id: $id}) DELETE k",
                                id=entry.get("knowledge_id"),
                            )
                        elif merge_strategy == "merge":
                            # Merge properties
                            merge_query = """
                            MATCH (k:Knowledge {knowledge_id: $id})
                            SET k += $props
                            """
                            session.run(
                                merge_query, id=entry.get("knowledge_id"), props=entry
                            )
                            imported += 1
                            continue

                    # Create new entry
                    create_query = """
                    CREATE (k:Knowledge $props)
                    """
                    session.run(create_query, props=entry)
                    imported += 1

                except Exception as e:
                    logger.error(f"Failed to import knowledge: {e}")

        logger.info(f"Imported {imported} knowledge entries")
        return imported

    def _import_relationships(self, relationships: List[Dict]) -> int:
        """Import relationships"""

        imported = 0

        with self.driver.session() as session:
            for rel in relationships:
                try:
                    # Check if relationship exists
                    check_query = """
                    MATCH (k1:Knowledge {knowledge_id: $source})
                    MATCH (k2:Knowledge {knowledge_id: $target})
                    MATCH (k1)-[r:RELATED_TO]-(k2)
                    RETURN r
                    """

                    result = session.run(
                        check_query, source=rel["source"], target=rel["target"]
                    )

                    if result.single():
                        continue  # Skip existing

                    # Create relationship
                    create_query = """
                    MATCH (k1:Knowledge {knowledge_id: $source})
                    MATCH (k2:Knowledge {knowledge_id: $target})
                    CREATE (k1)-[:RELATED_TO {
                        similarity: $similarity,
                        created_at: datetime(),
                        created_by: 'import'
                    }]->(k2)
                    """

                    session.run(
                        create_query,
                        source=rel["source"],
                        target=rel["target"],
                        similarity=rel.get("similarity", 0),
                    )
                    imported += 1

                except Exception as e:
                    logger.error(f"Failed to import relationship: {e}")

        logger.info(f"Imported {imported} relationships")
        return imported

    def close(self):
        """Close database connection"""
        self.driver.close()


def main():
    """Example usage"""
    import argparse

    parser = argparse.ArgumentParser(description="Knowledge Base Export/Import")
    parser.add_argument(
        "action", choices=["export", "import"], help="Action to perform"
    )
    parser.add_argument("path", help="File path for export/import")
    parser.add_argument(
        "--format",
        default="json",
        choices=["json", "csv", "yaml", "cypher", "markdown"],
    )
    parser.add_argument(
        "--include-embeddings", action="store_true", help="Include embeddings in export"
    )
    parser.add_argument(
        "--merge-strategy", default="skip", choices=["skip", "overwrite", "merge"]
    )

    args = parser.parse_args()

    if args.action == "export":
        exporter = KnowledgeExporter()
        result = exporter.export_knowledge(
            args.path,
            format=ExportFormat(args.format),
            include_embeddings=args.include_embeddings,
        )
        print(f"Export complete: {json.dumps(result, indent=2)}")
        exporter.close()

    elif args.action == "import":
        importer = KnowledgeImporter()
        result = importer.import_knowledge(
            args.path,
            format=ExportFormat(args.format),
            merge_strategy=args.merge_strategy,
        )
        print(f"Import complete: {json.dumps(result, indent=2)}")
        importer.close()


if __name__ == "__main__":
    main()
