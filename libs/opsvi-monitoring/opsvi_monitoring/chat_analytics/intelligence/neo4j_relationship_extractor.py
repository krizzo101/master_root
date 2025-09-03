"""
Neo4j Relationship Extractor for Unified Context System.
Extracts and builds relationships from PostgreSQL data into Neo4j graph.
"""

import hashlib
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import psycopg2
from neo4j import GraphDatabase

# Add project root to path
sys.path.insert(0, "/home/opsvi/master_root")


class Neo4jRelationshipExtractor:
    """Extracts relationships from PostgreSQL and builds Neo4j graph."""

    def __init__(
        self,
        postgres_url: str = "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context",
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "neo4j_secure_password",
    ):
        self.postgres_url = postgres_url

        # PostgreSQL connection
        self.pg_conn = psycopg2.connect(postgres_url)
        self.pg_conn.autocommit = True

        # Neo4j connection
        self.neo4j_driver = GraphDatabase.driver(
            neo4j_uri, auth=(neo4j_user, neo4j_password)
        )

        # Statistics
        self.stats = {"nodes_created": 0, "relationships_created": 0, "errors": 0}

    def extract_all_relationships(self):
        """Extract all relationships from PostgreSQL to Neo4j."""
        print("🔄 Starting complete relationship extraction...")

        try:
            # Initialize Neo4j schema
            self._initialize_schema()

            # Extract different types of relationships
            self._extract_file_relationships()
            self._extract_code_element_relationships()
            self._extract_session_relationships()
            self._extract_symbol_relationships()
            self._extract_agent_relationships()

            print(f"✅ Relationship extraction complete!")
            print(f"   📊 Stats: {self.stats}")

        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            import traceback

            traceback.print_exc()

    def _initialize_schema(self):
        """Initialize Neo4j constraints and indexes."""
        print("🔧 Initializing Neo4j schema...")

        with self.neo4j_driver.session() as session:
            # Create constraints for unique identifiers
            constraints = [
                "CREATE CONSTRAINT session_id_unique IF NOT EXISTS FOR (s:Session) REQUIRE s.session_id IS UNIQUE",
                "CREATE CONSTRAINT file_path_unique IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE",
                "CREATE CONSTRAINT code_element_unique IF NOT EXISTS FOR (c:CodeElement) REQUIRE c.element_id IS UNIQUE",
                "CREATE CONSTRAINT symbol_unique IF NOT EXISTS FOR (sym:Symbol) REQUIRE sym.symbol_id IS UNIQUE",
                "CREATE CONSTRAINT agent_unique IF NOT EXISTS FOR (a:Agent) REQUIRE a.agent_id IS UNIQUE",
            ]

            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    # Constraint may already exist
                    pass

            # Create indexes
            indexes = [
                "CREATE INDEX session_timestamp IF NOT EXISTS FOR (s:Session) ON s.started_at",
                "CREATE INDEX file_language IF NOT EXISTS FOR (f:File) ON f.language",
                "CREATE INDEX code_element_type IF NOT EXISTS FOR (c:CodeElement) ON c.element_type",
                "CREATE INDEX symbol_type IF NOT EXISTS FOR (sym:Symbol) ON sym.symbol_type",
            ]

            for index in indexes:
                try:
                    session.run(index)
                except Exception as e:
                    # Index may already exist
                    pass

        print("✅ Neo4j schema initialized")

    def _extract_file_relationships(self):
        """Extract file nodes and their relationships."""
        print("📁 Extracting file relationships...")

        with self.pg_conn.cursor() as pg_cursor:
            # Get all files with their code elements
            pg_cursor.execute(
                """
                SELECT DISTINCT
                    file_path,
                    language,
                    COUNT(CASE WHEN element_type = 'function' THEN 1 END) as function_count,
                    COUNT(CASE WHEN element_type = 'class' THEN 1 END) as class_count,
                    COUNT(CASE WHEN element_type = 'import' THEN 1 END) as import_count
                FROM code_elements
                WHERE file_path IS NOT NULL
                GROUP BY file_path, language
            """
            )

            files = pg_cursor.fetchall()

        # Create file nodes in Neo4j
        with self.neo4j_driver.session() as neo4j_session:
            for file_data in files:
                file_path, language, func_count, class_count, import_count = file_data

                # Create file node
                neo4j_session.run(
                    """
                    MERGE (f:File {path: $path})
                    SET f.language = $language,
                        f.function_count = $func_count,
                        f.class_count = $class_count,
                        f.import_count = $import_count,
                        f.updated_at = datetime()
                """,
                    path=file_path,
                    language=language or "unknown",
                    func_count=func_count,
                    class_count=class_count,
                    import_count=import_count,
                )

                self.stats["nodes_created"] += 1

        print(f"   Created {len(files)} file nodes")

    def _extract_code_element_relationships(self):
        """Extract code elements and their relationships to files."""
        print("🔧 Extracting code element relationships...")

        with self.pg_conn.cursor() as pg_cursor:
            # Get code elements (functions, classes)
            pg_cursor.execute(
                """
                SELECT
                    id::text as element_id,
                    file_path,
                    element_type,
                    element_name,
                    signature,
                    line_start,
                    line_end,
                    complexity_score
                FROM code_elements
                WHERE element_type IN ('function', 'class')
                AND element_name IS NOT NULL
            """
            )

            elements = pg_cursor.fetchall()

        # Create code element nodes and relationships
        with self.neo4j_driver.session() as neo4j_session:
            for element in elements:
                (
                    element_id,
                    file_path,
                    element_type,
                    element_name,
                    signature,
                    line_start,
                    line_end,
                    complexity_score,
                ) = element

                # Create code element node
                neo4j_session.run(
                    """
                    MERGE (c:CodeElement {element_id: $element_id})
                    SET c.name = $name,
                        c.element_type = $type,
                        c.signature = $signature,
                        c.line_start = $line_start,
                        c.line_end = $line_end,
                        c.complexity_score = $complexity,
                        c.updated_at = datetime()
                """,
                    element_id=element_id,
                    name=element_name,
                    type=element_type,
                    signature=signature or "",
                    line_start=line_start or 0,
                    line_end=line_end or 0,
                    complexity=complexity_score or 0,
                )

                # Create relationship to file
                neo4j_session.run(
                    """
                    MATCH (c:CodeElement {element_id: $element_id})
                    MATCH (f:File {path: $file_path})
                    MERGE (c)-[:BELONGS_TO]->(f)
                """,
                    element_id=element_id,
                    file_path=file_path,
                )

                self.stats["nodes_created"] += 1
                self.stats["relationships_created"] += 1

        print(f"   Created {len(elements)} code element nodes")

    def _extract_session_relationships(self):
        """Extract chat sessions and their relationships."""
        print("💬 Extracting session relationships...")

        # First, ensure we have some chat sessions in PostgreSQL
        with self.pg_conn.cursor() as pg_cursor:
            # Check for existing sessions
            pg_cursor.execute("SELECT COUNT(*) FROM chat_sessions")
            session_count = pg_cursor.fetchone()[0]

            if session_count == 0:
                print("   No chat sessions found in PostgreSQL")
                return

            # Get all sessions
            pg_cursor.execute(
                """
                SELECT
                    id,
                    started_at,
                    ended_at,
                    user_id,
                    project_path,
                    total_tokens,
                    total_cost,
                    model_used
                FROM chat_sessions
            """
            )

            sessions = pg_cursor.fetchall()

        # Create session nodes in Neo4j
        with self.neo4j_driver.session() as neo4j_session:
            for session in sessions:
                (
                    session_id,
                    started_at,
                    ended_at,
                    user_id,
                    project_path,
                    total_tokens,
                    total_cost,
                    model_used,
                ) = session

                # Create session node
                neo4j_session.run(
                    """
                    MERGE (s:Session {session_id: $session_id})
                    SET s.started_at = $started_at,
                        s.ended_at = $ended_at,
                        s.user_id = $user_id,
                        s.project_path = $project_path,
                        s.total_tokens = $total_tokens,
                        s.total_cost = $total_cost,
                        s.model_used = $model_used,
                        s.updated_at = datetime()
                """,
                    session_id=session_id,
                    started_at=started_at,
                    ended_at=ended_at,
                    user_id=user_id or "",
                    project_path=project_path or "",
                    total_tokens=total_tokens or 0,
                    total_cost=float(total_cost or 0),
                    model_used=model_used or "",
                )

                self.stats["nodes_created"] += 1

        print(f"   Created {len(sessions)} session nodes")

    def _extract_symbol_relationships(self):
        """Extract symbol references and their relationships."""
        print("🔗 Extracting symbol relationships...")

        with self.pg_conn.cursor() as pg_cursor:
            # Get symbol references
            pg_cursor.execute(
                """
                SELECT
                    session_id,
                    symbol_name,
                    symbol_type,
                    file_path,
                    reference_type,
                    COUNT(*) as mention_count
                FROM symbol_references
                GROUP BY session_id, symbol_name, symbol_type, file_path, reference_type
            """
            )

            symbols = pg_cursor.fetchall()

        if not symbols:
            print("   No symbol references found")
            return

        # Create symbol relationships in Neo4j
        with self.neo4j_driver.session() as neo4j_session:
            for symbol in symbols:
                (
                    session_id,
                    symbol_name,
                    symbol_type,
                    file_path,
                    reference_type,
                    mention_count,
                ) = symbol

                # Create symbol node
                symbol_id = hashlib.md5(
                    f"{symbol_name}:{symbol_type}".encode()
                ).hexdigest()[:16]

                neo4j_session.run(
                    """
                    MERGE (sym:Symbol {symbol_id: $symbol_id})
                    SET sym.name = $name,
                        sym.symbol_type = $type,
                        sym.updated_at = datetime()
                """,
                    symbol_id=symbol_id,
                    name=symbol_name,
                    type=symbol_type or "unknown",
                )

                # Create relationship: Session -> REFERENCED -> Symbol
                neo4j_session.run(
                    """
                    MATCH (s:Session {session_id: $session_id})
                    MATCH (sym:Symbol {symbol_id: $symbol_id})
                    MERGE (s)-[r:REFERENCED]->(sym)
                    SET r.mention_count = $mentions,
                        r.reference_type = $ref_type,
                        r.file_path = $file_path,
                        r.updated_at = datetime()
                """,
                    session_id=session_id,
                    symbol_id=symbol_id,
                    mentions=mention_count,
                    ref_type=reference_type or "mentioned",
                    file_path=file_path,
                )

                # If symbol exists as code element, create relationship
                if file_path:
                    neo4j_session.run(
                        """
                        MATCH (sym:Symbol {symbol_id: $symbol_id})
                        MATCH (c:CodeElement {name: $name})
                        MATCH (f:File {path: $file_path})
                        WHERE (c)-[:BELONGS_TO]->(f)
                        MERGE (sym)-[:REFERS_TO]->(c)
                    """,
                        symbol_id=symbol_id,
                        name=symbol_name,
                        file_path=file_path,
                    )

                self.stats["relationships_created"] += 2

        print(f"   Created relationships for {len(symbols)} symbol references")

    def _extract_agent_relationships(self):
        """Extract agent usage relationships."""
        print("🤖 Extracting agent relationships...")

        with self.pg_conn.cursor() as pg_cursor:
            # Get agent usage data
            pg_cursor.execute(
                """
                SELECT
                    session_id,
                    agent_class,
                    agent_token,
                    task_description,
                    execution_time_ms,
                    tokens_used,
                    success,
                    file_paths
                FROM agent_usage
                WHERE agent_class IS NOT NULL
            """
            )

            agents = pg_cursor.fetchall()

        if not agents:
            print("   No agent usage found")
            return

        # Create agent relationships in Neo4j
        with self.neo4j_driver.session() as neo4j_session:
            for agent in agents:
                (
                    session_id,
                    agent_class,
                    agent_token,
                    task_description,
                    execution_time_ms,
                    tokens_used,
                    success,
                    file_paths,
                ) = agent

                # Create agent node
                agent_id = (
                    agent_token or hashlib.md5(agent_class.encode()).hexdigest()[:16]
                )

                neo4j_session.run(
                    """
                    MERGE (a:Agent {agent_id: $agent_id})
                    SET a.agent_class = $agent_class,
                        a.agent_token = $agent_token,
                        a.updated_at = datetime()
                """,
                    agent_id=agent_id,
                    agent_class=agent_class,
                    agent_token=agent_token or "",
                )

                # Create relationship: Session -> USED_AGENT -> Agent
                neo4j_session.run(
                    """
                    MATCH (s:Session {session_id: $session_id})
                    MATCH (a:Agent {agent_id: $agent_id})
                    MERGE (s)-[r:USED_AGENT]->(a)
                    SET r.task_description = $task,
                        r.execution_time_ms = $exec_time,
                        r.tokens_used = $tokens,
                        r.success = $success,
                        r.updated_at = datetime()
                """,
                    session_id=session_id,
                    agent_id=agent_id,
                    task=task_description or "",
                    exec_time=execution_time_ms or 0,
                    tokens=tokens_used or 0,
                    success=success or True,
                )

                # Create relationships to files if available
                if file_paths:
                    for file_path in file_paths:
                        neo4j_session.run(
                            """
                            MATCH (a:Agent {agent_id: $agent_id})
                            MATCH (f:File {path: $file_path})
                            MERGE (a)-[:WORKED_ON]->(f)
                        """,
                            agent_id=agent_id,
                            file_path=file_path,
                        )

                self.stats["relationships_created"] += 2

        print(f"   Created relationships for {len(agents)} agent usages")

    def query_relationships(self, query_type: str = "file_connections") -> List[Dict]:
        """Query relationships from Neo4j for validation."""
        print(f"🔍 Querying {query_type} relationships...")

        queries = {
            "file_connections": """
                MATCH (f:File)
                OPTIONAL MATCH (f)<-[:BELONGS_TO]-(c:CodeElement)
                OPTIONAL MATCH (s:Session)-[:REFERENCED]->(sym:Symbol)-[:REFERS_TO]->(c)
                RETURN f.path as file_path,
                       f.language as language,
                       count(DISTINCT c) as code_elements,
                       count(DISTINCT s) as sessions_referenced
                ORDER BY sessions_referenced DESC
                LIMIT 10
            """,
            "session_activity": """
                MATCH (s:Session)
                OPTIONAL MATCH (s)-[:REFERENCED]->(sym:Symbol)
                OPTIONAL MATCH (s)-[:USED_AGENT]->(a:Agent)
                RETURN s.session_id as session_id,
                       s.total_tokens as tokens,
                       count(DISTINCT sym) as symbols_referenced,
                       count(DISTINCT a) as agents_used
                ORDER BY tokens DESC
                LIMIT 10
            """,
            "code_complexity": """
                MATCH (c:CodeElement)
                WHERE c.complexity_score > 0
                MATCH (c)-[:BELONGS_TO]->(f:File)
                RETURN c.name as element_name,
                       c.element_type as type,
                       c.complexity_score as complexity,
                       f.path as file_path
                ORDER BY complexity DESC
                LIMIT 10
            """,
        }

        if query_type not in queries:
            print(f"   Unknown query type: {query_type}")
            return []

        results = []
        with self.neo4j_driver.session() as session:
            query_result = session.run(queries[query_type])
            results = [dict(record) for record in query_result]

        print(f"   Found {len(results)} results")
        return results

    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get comprehensive graph statistics."""
        print("📊 Getting graph statistics...")

        stats_queries = {
            "node_counts": """
                MATCH (n)
                RETURN labels(n)[0] as node_type, count(*) as count
                ORDER BY count DESC
            """,
            "relationship_counts": """
                MATCH ()-[r]->()
                RETURN type(r) as relationship_type, count(*) as count
                ORDER BY count DESC
            """,
            "top_connected_files": """
                MATCH (f:File)<-[:BELONGS_TO]-(c:CodeElement)
                RETURN f.path as file_path,
                       f.language as language,
                       count(c) as element_count
                ORDER BY element_count DESC
                LIMIT 5
            """,
        }

        stats = {}
        with self.neo4j_driver.session() as session:
            for stat_name, query in stats_queries.items():
                result = session.run(query)
                stats[stat_name] = [dict(record) for record in result]

        return stats

    def close(self):
        """Close connections."""
        if self.pg_conn:
            self.pg_conn.close()
        if self.neo4j_driver:
            self.neo4j_driver.close()


def main():
    """Main extraction workflow."""
    print("🚀 Starting Neo4j relationship extraction")

    extractor = Neo4jRelationshipExtractor()

    try:
        # Extract all relationships
        extractor.extract_all_relationships()

        # Validate with some queries
        file_connections = extractor.query_relationships("file_connections")
        print("\n📁 Top connected files:")
        for conn in file_connections[:5]:
            print(
                f"   {conn['file_path']} ({conn['language']}) - {conn['code_elements']} elements, {conn['sessions_referenced']} sessions"
            )

        # Get comprehensive stats
        graph_stats = extractor.get_graph_statistics()
        print(f"\n📊 Graph Statistics:")
        print(f"   Node counts: {graph_stats.get('node_counts', [])}")
        print(f"   Relationship counts: {graph_stats.get('relationship_counts', [])}")

        print(f"\n🎉 Neo4j relationship extraction complete!")

    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback

        traceback.print_exc()

    finally:
        extractor.close()


if __name__ == "__main__":
    main()
