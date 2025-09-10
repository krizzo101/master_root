#!/usr/bin/env python3
"""
Enhanced Context Retrieval - Gets COMPLETE context, not fragments
This is what I actually need to understand code and documentation fully
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


@dataclass
class CompleteContext:
    """A complete, coherent piece of knowledge with full context"""

    primary_content: str
    source_file: str
    full_section: str  # The complete section, not just a chunk
    before_context: Optional[str]  # What comes before
    after_context: Optional[str]  # What comes after
    related_code: List[Dict]  # Related implementations, calls, etc.
    metadata: Dict


class EnhancedContextRetrieval:
    """
    Gets COMPLETE context for understanding, not fragments
    This is what I actually need to answer questions properly
    """

    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_auth: tuple = ("neo4j", "password"),
    ):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=neo4j_auth)

    def get_complete_context(
        self, knowledge_id: str, expand_chunks: int = 2
    ) -> CompleteContext:
        """
        Get the COMPLETE context for a knowledge item

        Args:
            knowledge_id: The starting knowledge ID
            expand_chunks: How many chunks before/after to include

        Returns:
            Complete context with full section and surrounding context
        """

        with self.driver.session() as session:
            # Get the primary knowledge
            result = session.run(
                """
                MATCH (k:Knowledge {knowledge_id: $kid})
                RETURN k
            """,
                kid=knowledge_id,
            )

            primary = result.single()
            if not primary:
                raise ValueError(f"Knowledge {knowledge_id} not found")

            primary_node = primary["k"]

            # Get the complete section by following NEXT_CHUNK in both directions
            full_section = self._assemble_complete_section(
                session, knowledge_id, primary_node["source"]
            )

            # Get before/after context
            before_context = self._get_context_before(
                session, knowledge_id, expand_chunks
            )
            after_context = self._get_context_after(
                session, knowledge_id, expand_chunks
            )

            # Get related code (same file, related functionality)
            related_code = self._get_related_code(
                session, primary_node["source"], primary_node.get("tags", [])
            )

            return CompleteContext(
                primary_content=primary_node["content"],
                source_file=primary_node["source"],
                full_section=full_section,
                before_context=before_context,
                after_context=after_context,
                related_code=related_code,
                metadata=dict(primary_node),
            )

    def _assemble_complete_section(
        self, session, start_id: str, source_pattern: str
    ) -> str:
        """Assemble the complete section from chunks"""

        # Extract base source (remove [part X/Y])
        import re

        base_source = re.sub(r"\s*\[part \d+/\d+\]", "", source_pattern)

        # Get all chunks from the same logical section
        result = session.run(
            """
            MATCH (k:Knowledge)
            WHERE k.source STARTS WITH $base_source
            AND k.source CONTAINS '[part'
            RETURN k.content as content, k.source as source
            ORDER BY k.source
        """,
            base_source=base_source,
        )

        chunks = []
        for record in result:
            # Extract part number for sorting
            match = re.search(r"\[part (\d+)/\d+\]", record["source"])
            if match:
                part_num = int(match.group(1))
                chunks.append((part_num, record["content"]))

        # Sort by part number and concatenate
        chunks.sort(key=lambda x: x[0])

        if chunks:
            return "\n".join([content for _, content in chunks])
        else:
            # Single chunk or no parts
            return session.run(
                """
                MATCH (k:Knowledge {knowledge_id: $kid})
                RETURN k.content as content
            """,
                kid=start_id,
            ).single()["content"]

    def _get_context_before(
        self, session, knowledge_id: str, num_chunks: int
    ) -> Optional[str]:
        """Get context before this knowledge"""

        result = session.run(
            """
            MATCH path = (k:Knowledge {knowledge_id: $kid})<-[:NEXT_CHUNK*1..%d]-(before:Knowledge)
            RETURN before.content as content
            ORDER BY length(path) DESC
        """
            % num_chunks,
            kid=knowledge_id,
        )

        before_chunks = [record["content"] for record in result]

        if before_chunks:
            return "\n---\n".join(before_chunks)
        return None

    def _get_context_after(
        self, session, knowledge_id: str, num_chunks: int
    ) -> Optional[str]:
        """Get context after this knowledge"""

        result = session.run(
            """
            MATCH path = (k:Knowledge {knowledge_id: $kid})-[:NEXT_CHUNK*1..%d]->(after:Knowledge)
            RETURN after.content as content
            ORDER BY length(path)
        """
            % num_chunks,
            kid=knowledge_id,
        )

        after_chunks = [record["content"] for record in result]

        if after_chunks:
            return "\n---\n".join(after_chunks)
        return None

    def _get_related_code(self, session, source: str, tags: List[str]) -> List[Dict]:
        """Get related code from the same context"""

        # Find code in the same file or with shared tags
        result = session.run(
            """
            MATCH (k:Knowledge)
            WHERE k.knowledge_type = 'CODE'
            AND (k.source = $source OR any(tag IN $tags WHERE tag IN k.tags))
            AND k.direct_ingestion = true
            RETURN k.source as source,
                   k.content as content,
                   k.knowledge_type as type,
                   k.tags as tags
            LIMIT 5
        """,
            source=source,
            tags=tags,
        )

        related = []
        for record in result:
            related.append(
                {
                    "source": record["source"],
                    "content": record["content"][:500],  # First 500 chars
                    "type": record["type"],
                    "tags": record["tags"],
                }
            )

        return related

    def get_complete_function(self, function_name: str) -> Optional[CompleteContext]:
        """
        Get the complete implementation of a function
        Not just where it's mentioned, but the full implementation
        """

        with self.driver.session() as session:
            # Find function definition
            result = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.knowledge_type = 'CODE'
                AND k.content CONTAINS $pattern
                AND k.direct_ingestion = true
                RETURN k.knowledge_id as id
                LIMIT 1
            """,
                pattern=f"def {function_name}",
            )

            record = result.single()
            if record:
                return self.get_complete_context(record["id"])
            return None

    def get_error_solutions(self, error_pattern: str) -> List[CompleteContext]:
        """
        Get complete solutions for an error pattern
        Not just mentions, but full context of how it was solved
        """

        contexts = []

        with self.driver.session() as session:
            # Find error mentions and solutions
            result = session.run(
                """
                MATCH (k:Knowledge)
                WHERE toLower(k.content) CONTAINS toLower($error)
                AND (k.knowledge_type = 'CODE' OR k.knowledge_type = 'DOCUMENTATION')
                AND k.direct_ingestion = true
                RETURN k.knowledge_id as id, k.confidence_score as confidence
                ORDER BY confidence DESC
                LIMIT 5
            """,
                error=error_pattern,
            )

            for record in result:
                try:
                    context = self.get_complete_context(record["id"])
                    contexts.append(context)
                except Exception as e:
                    logger.warning(f"Failed to get context for {record['id']}: {e}")

        return contexts

    def trace_code_flow(
        self, starting_point: str, max_depth: int = 3
    ) -> List[Tuple[str, str]]:
        """
        Trace the flow of code from a starting point
        Shows what calls what, in what order
        """

        flow = []

        with self.driver.session() as session:
            # This would be enhanced with proper CALLS relationships
            # For now, trace through file relationships
            result = session.run(
                """
                MATCH (k:Knowledge {knowledge_id: $start})
                MATCH path = (k)-[:NEXT_CHUNK|SHARES_TAG*1..%d]-(related:Knowledge)
                WHERE related.knowledge_type = 'CODE'
                RETURN DISTINCT related.source as source, related.content as content
                LIMIT 10
            """
                % max_depth,
                start=starting_point,
            )

            for record in result:
                # Extract function/class names from content
                import re

                functions = re.findall(r"def\s+(\w+)", record["content"])
                classes = re.findall(r"class\s+(\w+)", record["content"])

                for func in functions:
                    flow.append((record["source"], f"function: {func}"))
                for cls in classes:
                    flow.append((record["source"], f"class: {cls}"))

        return flow

    def close(self):
        """Clean up"""
        self.driver.close()


# Example usage showing what I actually need
if __name__ == "__main__":
    enhancer = EnhancedContextRetrieval()

    # Get a sample knowledge ID to test with
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    with driver.session() as session:
        result = session.run(
            """
            MATCH (k:Knowledge)
            WHERE k.direct_ingestion = true
            AND k.source CONTAINS 'streaming'
            RETURN k.knowledge_id as id, k.source as source
            LIMIT 1
        """
        )
        record = result.single()

        if record:
            print(f"Testing with: {record['source']}")
            print("=" * 60)

            # Get COMPLETE context
            context = enhancer.get_complete_context(record["id"])

            print(f"Source: {context.source_file}")
            print(f"Primary content length: {len(context.primary_content)} chars")
            print(f"Full section length: {len(context.full_section)} chars")
            print(f"Has before context: {context.before_context is not None}")
            print(f"Has after context: {context.after_context is not None}")
            print(f"Related code items: {len(context.related_code)}")

            if len(context.full_section) > len(context.primary_content):
                print(
                    f"\n✓ Successfully assembled {len(context.full_section)} chars from chunks"
                )
                print(f"  (vs {len(context.primary_content)} in single chunk)")

            # Show the difference
            print(f"\nPrimary chunk (first 200 chars):")
            print(context.primary_content[:200])
            print(f"\nFull section (first 200 chars):")
            print(context.full_section[:200])

    driver.close()
    enhancer.close()
