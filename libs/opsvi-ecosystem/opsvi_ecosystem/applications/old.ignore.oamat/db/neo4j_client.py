"""
Neo4j client integration for OAMAT knowledge graph.

Schema:
- Document: {document_id, title, source, author, created_at, metadata}
- Chunk: {chunk_id, text, embedding, order, document_id, created_at}
- Entity: {entity_id, name, type, attributes, source_chunk_id}

Relationships:
- (Document)-[:CONTAINS]->(Chunk)
- (Chunk)-[:REFERENCES]->(Entity)
- (Chunk)-[:GENERATED_BY]->(Agent)
- (Entity)-[:RELATED_TO]->(Entity)

Vector Index:
- On Chunk.embedding (3072 dims, euclidean)
"""

from typing import Optional
import uuid
from datetime import datetime
import logging
import json

logger = logging.getLogger("Neo4jClient")
logging.basicConfig(level=logging.INFO)
try:
    from neo4j import GraphDatabase

    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

from src.applications.oamat.utils.chunking_embedding import chunk_and_embed_document


class Neo4jClient:
    """Client for connecting to and querying Neo4j."""

    def __init__(self, uri: str, user: str, password: str, raise_on_fail: bool = False):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        if NEO4J_AVAILABLE:
            try:
                self.driver = GraphDatabase.driver(uri, auth=(user, password))
                # Test connection
                with self.driver.session() as session:
                    session.run("RETURN 1")
            except Exception as e:
                if raise_on_fail:
                    logger.error(f"[Neo4jClient] Connection failed: {e}. Aborting.")
                    raise
                else:
                    logger.warning(
                        f"[Neo4jClient] Connection failed: {e}. Falling back to mock mode."
                    )
                    self.driver = None
        else:
            logger.warning(
                "[Neo4jClient] neo4j package not available. Using mock mode."
            )

    def check_connection(self) -> bool:
        """Check if the Neo4j connection is healthy."""
        if self.driver is None:
            return False
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            return True
        except Exception as e:
            logger.error(f"[Neo4jClient] Health check failed: {e}")
            return False

    def close(self):
        """Close the Neo4j driver connection."""
        if self.driver:
            try:
                self.driver.close()
                logger.info("[Neo4jClient] Connection closed successfully")
            except Exception as e:
                logger.error(f"[Neo4jClient] Error closing connection: {e}")
        else:
            logger.info("[Neo4jClient] No connection to close (mock mode)")

    def query(self, cypher: str) -> list:
        """Run a Cypher query and return results as a list."""
        if self.driver:
            try:
                with self.driver.session() as session:
                    result = session.run(cypher)
                    return [record.data() for record in result]
            except Exception as e:
                logger.error(f"[Neo4jClient] Query failed: {e}")
                return [{"error": str(e)}]
        logger.info(f"[Neo4jClient] Mock query: {cypher}")
        return []

    def create_agent(self, name: str, role: str) -> str:
        """
        Create an Agent node in Neo4j and return the agent_id.
        """
        agent_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        cypher = (
            "CREATE (a:Agent {agent_id: $agent_id, name: $name, role: $role, created_at: $created_at}) "
            "RETURN a.agent_id AS agent_id"
        )
        params = {
            "agent_id": agent_id,
            "name": name,
            "role": role,
            "created_at": created_at,
        }
        if self.driver:
            try:
                with self.driver.session() as session:
                    result = session.run(cypher, params)
                    return result.single()["agent_id"]
            except Exception as e:
                logger.error(f"[Neo4jClient] create_agent failed: {e}")
                return {"error": str(e), "agent_id": agent_id}
        logger.info(f"[Neo4jClient] Mock create_agent: {params}")
        return agent_id

    def create_workflow(
        self, agent_id: str, topic: str, status: str = "submitted"
    ) -> str:
        """
        Create a Workflow node in Neo4j and return the workflow_id.
        """
        workflow_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        cypher = (
            "CREATE (w:Workflow {workflow_id: $workflow_id, agent_id: $agent_id, topic: $topic, status: $status, created_at: $created_at}) "
            "RETURN w.workflow_id AS workflow_id"
        )
        params = {
            "workflow_id": workflow_id,
            "agent_id": agent_id,
            "topic": topic,
            "status": status,
            "created_at": created_at,
        }
        if self.driver:
            try:
                with self.driver.session() as session:
                    result = session.run(cypher, params)
                    return result.single()["workflow_id"]
            except Exception as e:
                logger.error(f"[Neo4jClient] create_workflow failed: {e}")
                return {"error": str(e), "workflow_id": workflow_id}
        logger.info(f"[Neo4jClient] Mock create_workflow: {params}")
        return workflow_id

    def update_workflow_status(
        self, workflow_id: str, status: str, result: str = None
    ) -> None:
        """
        Update the status (and optionally result) of a workflow node in Neo4j.
        """
        cypher = (
            "MATCH (w:Workflow {workflow_id: $workflow_id}) "
            "SET w.status = $status "
            + (", w.result = $result " if result is not None else "")
            + "RETURN w"
        )
        params = {"workflow_id": workflow_id, "status": status}
        if result is not None:
            params["result"] = result
        if self.driver:
            try:
                with self.driver.session() as session:
                    session.run(cypher, params)
                return
            except Exception as e:
                logger.error(f"[Neo4jClient] update_workflow_status failed: {e}")
                return {"error": str(e), "workflow_id": workflow_id}
        logger.info(f"[Neo4jClient] Mock update_workflow_status: {params}")
        return None

    def get_workflow(self, workflow_id: str) -> dict:
        """
        Retrieve workflow node details by ID.
        """
        cypher = "MATCH (w:Workflow {workflow_id: $workflow_id}) RETURN w"
        params = {"workflow_id": workflow_id}
        if self.driver:
            try:
                with self.driver.session() as session:
                    result = session.run(cypher, params)
                    record = result.single()
                    if record:
                        w = record["w"]
                        return dict(w)
            except Exception as e:
                logger.error(f"[Neo4jClient] get_workflow failed: {e}")
                return {"error": str(e), "workflow_id": workflow_id}
        logger.info(f"[Neo4jClient] Mock get_workflow: {params}")
        return {
            "workflow_id": workflow_id,
            "agent_id": "mock-agent-id",
            "topic": "mock topic",
            "status": "submitted",
            "created_at": "2025-07-07T00:00:00Z",
            "result": None,
        }

    def list_workflows(
        self, agent_id: Optional[str] = None, status: Optional[str] = None
    ) -> list:
        """
        List workflows, optionally filtered by agent or status.
        """
        cypher = "MATCH (w:Workflow"
        filters = []
        params = {}
        if agent_id:
            filters.append("w.agent_id = $agent_id")
            params["agent_id"] = agent_id
        if status:
            filters.append("w.status = $status")
            params["status"] = status
        if filters:
            cypher += " {" + ", ".join(filters) + "}"
        cypher += ") RETURN w"
        if self.driver:
            try:
                with self.driver.session() as session:
                    result = session.run(cypher, params)
                    return [dict(record["w"]) for record in result]
            except Exception as e:
                logger.error(f"[Neo4jClient] list_workflows failed: {e}")
                return [{"error": str(e)}]
        logger.info(f"[Neo4jClient] Mock list_workflows: {params}")
        return [
            {
                "workflow_id": "mock-wf-1",
                "agent_id": agent_id or "mock-agent-id",
                "topic": "mock topic 1",
                "status": status or "submitted",
                "created_at": "2025-07-07T00:00:00Z",
                "result": None,
            },
            {
                "workflow_id": "mock-wf-2",
                "agent_id": agent_id or "mock-agent-id",
                "topic": "mock topic 2",
                "status": status or "submitted",
                "created_at": "2025-07-07T00:00:00Z",
                "result": None,
            },
        ]

    def create_document(
        self, title: str, source: str, author: str, metadata: dict = None
    ) -> str:
        """
        Create or merge a Document node in Neo4j and return the document_id.
        Enforces schema and attaches standardized metadata (see schema_config.yaml).
        """
        document_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        # Standardized metadata
        meta = metadata or {}
        meta.update(
            {
                "created_by": "system",  # TODO: pass agent/user
                "created_at": created_at,
                "source": source,
                "version": meta.get("version", "1.0.0"),
                "provenance": meta.get("provenance", "ingest"),
                "last_updated": created_at,
                "lineage": meta.get("lineage", []),
                "confidence": meta.get("confidence", 1.0),
            }
        )
        meta_str = json.dumps(meta)
        cypher = (
            "MERGE (d:Document {document_id: $document_id}) "
            "SET d.title = $title, d.source = $source, d.author = $author, d.created_at = $created_at, d.metadata = $metadata "
            "RETURN d.document_id AS document_id"
        )
        params = {
            "document_id": document_id,
            "title": title,
            "source": source,
            "author": author,
            "created_at": created_at,
            "metadata": meta_str,
        }
        if self.driver:
            try:
                with self.driver.session() as session:
                    result = session.run(cypher, params)
                    return result.single()["document_id"]
            except Exception as e:
                logger.error(f"[Neo4jClient] create_document failed: {e}")
                return {"error": str(e), "document_id": document_id}
        logger.info(f"[Neo4jClient] Mock create_document: {params}")
        return document_id

    def upsert_chunk(
        self,
        document_id: str,
        text: str,
        embedding: list,
        order: int,
        metadata: dict = None,
    ) -> str:
        """
        Upsert a Chunk node and create CONTAINS relationship from Document.
        Enforces schema, attaches standardized metadata, and validates embedding.
        """
        expected_dim = 1536
        if not isinstance(embedding, list) or not all(
            isinstance(x, float) for x in embedding
        ):
            logger.error(
                f"[Neo4jClient] Embedding must be a flat list of floats. Got: {type(embedding)} {embedding}"
            )
            raise ValueError("Embedding must be a flat list of floats.")
        if len(embedding) != expected_dim:
            logger.error(
                f"[Neo4jClient] Embedding dimension mismatch: expected {expected_dim}, got {len(embedding)}"
            )
            raise ValueError(
                f"Embedding dimension mismatch: expected {expected_dim}, got {len(embedding)}"
            )
        chunk_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        meta = metadata or {}
        meta.update(
            {
                "created_by": "system",
                "created_at": created_at,
                "document_id": document_id,
                "order": order,
            }
        )
        meta_str = json.dumps(meta)
        cypher = (
            "MERGE (c:Chunk {chunk_id: $chunk_id}) "
            "SET c.text = $text, c.embedding = $embedding, c.order = $order, c.document_id = $document_id, c.created_at = $created_at, c.metadata = $metadata "
            "WITH c MATCH (d:Document {document_id: $document_id}) "
            "MERGE (d)-[:CONTAINS]->(c) "
            "RETURN c.chunk_id AS chunk_id"
        )
        params = {
            "chunk_id": chunk_id,
            "text": text,
            "embedding": embedding,
            "order": order,
            "document_id": document_id,
            "created_at": created_at,
            "metadata": meta_str,
        }
        if self.driver:
            try:
                with self.driver.session() as session:
                    result = session.run(cypher, params)
                    return result.single()["chunk_id"]
            except Exception as e:
                logger.error(f"[Neo4jClient] upsert_chunk failed: {e}")
                return {"error": str(e), "chunk_id": chunk_id}
        logger.info(f"[Neo4jClient] Mock upsert_chunk: {params}")
        return chunk_id

    def upsert_entity(
        self,
        name: str,
        type_: str,
        attributes: dict,
        source_chunk_id: str,
        metadata: dict = None,
    ) -> str:
        """
        Upsert an Entity node and create REFERENCES relationship from Chunk.
        Enforces schema, attaches standardized metadata, and performs entity resolution (MERGE on name/type).
        """
        entity_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        attr = attributes or {}
        attr_str = json.dumps(attr)
        meta = metadata or {}
        meta.update(
            {
                "created_by": "system",
                "created_at": created_at,
                "source_chunk_id": source_chunk_id,
            }
        )
        meta_str = json.dumps(meta)
        cypher = (
            "MERGE (e:Entity {name: $name, type: $type}) "  # Entity resolution by name/type
            "SET e.entity_id = $entity_id, e.attributes = $attributes, e.source_chunk_id = $source_chunk_id, e.metadata = $metadata "
            "RETURN e.entity_id AS entity_id"
        )
        params = {
            "entity_id": entity_id,
            "name": name,
            "type": type_,
            "attributes": attr_str,
            "source_chunk_id": source_chunk_id,
            "metadata": meta_str,
        }
        if self.driver:
            try:
                with self.driver.session() as session:
                    result = session.run(cypher, params)
                    return result.single()["entity_id"]
            except Exception as e:
                logger.error(f"[Neo4jClient] upsert_entity failed: {e}")
                return {"error": str(e), "entity_id": entity_id}
        logger.info(f"[Neo4jClient] Mock upsert_entity: {params}")
        return entity_id

    def create_chunk_entity_relationship(self, chunk_id: str, entity_id: str):
        """
        Create REFERENCES relationship from Chunk to Entity.
        """
        cypher = (
            "MATCH (c:Chunk {chunk_id: $chunk_id}), (e:Entity {entity_id: $entity_id}) "
            "MERGE (c)-[:REFERENCES]->(e)"
        )
        params = {"chunk_id": chunk_id, "entity_id": entity_id}
        if self.driver:
            try:
                with self.driver.session() as session:
                    session.run(cypher, params)
                return True
            except Exception as e:
                logger.error(
                    f"[Neo4jClient] create_chunk_entity_relationship failed: {e}"
                )
                return False
        logger.info(f"[Neo4jClient] Mock create_chunk_entity_relationship: {params}")
        return True

    def create_entity(
        self,
        name: str,
        type_: str,
        attributes: dict = None,
        source_chunk_id: str = None,
    ) -> str:
        """
        Create an Entity node and optionally link to a Chunk.
        """
        entity_id = str(uuid.uuid4())
        cypher = (
            "CREATE (e:Entity {entity_id: $entity_id, name: $name, type: $type, attributes: $attributes, source_chunk_id: $source_chunk_id}) "
            "RETURN e.entity_id AS entity_id"
        )
        params = {
            "entity_id": entity_id,
            "name": name,
            "type": type_,
            "attributes": attributes or {},
            "source_chunk_id": source_chunk_id,
        }
        if self.driver:
            try:
                with self.driver.session() as session:
                    result = session.run(cypher, params)
                    return result.single()["entity_id"]
            except Exception as e:
                logger.error(f"[Neo4jClient] create_entity failed: {e}")
                return {"error": str(e), "entity_id": entity_id}
        logger.info(f"[Neo4jClient] Mock create_entity: {params}")
        return entity_id

    def create_vector_index_on_chunk(
        self,
        embedding_property: str = "embedding",
        dimensions: int = 1536,
        similarity_fn: str = "euclidean",
    ) -> bool:
        """
        Create a vector index on Chunk.embedding for vector search.
        Default dimensions=1536 matches OpenAI text-embedding-ada-002
        """
        cypher = (
            f"CREATE VECTOR INDEX chunk_vector_index IF NOT EXISTS FOR (c:Chunk) ON (c.{embedding_property}) "
            f"OPTIONS {{ indexConfig: {{ `vector.dimensions`: {dimensions}, `vector.similarity_function`: '{similarity_fn}' }} }}"
        )
        if self.driver:
            try:
                with self.driver.session() as session:
                    session.run(cypher)
                logger.info("[Neo4jClient] Vector index created or already exists.")
                return True
            except Exception as e:
                logger.error(f"[Neo4jClient] create_vector_index_on_chunk failed: {e}")
                return False
        logger.info(f"[Neo4jClient] Mock create_vector_index_on_chunk: {cypher}")
        return True

    def ingest_document_with_embedding(
        self,
        title: str,
        source: str,
        author: str,
        text: str,
        metadata: dict = None,
        entity_extractor=None,
    ) -> str:
        """
        Ingest a document: chunk, embed, upsert Document/Chunk/Entity nodes and relationships.
        entity_extractor: optional callable to extract entities from chunk text.
        Attaches standardized metadata to all nodes (see schema_config.yaml).
        """
        document_id = self.create_document(title, source, author, metadata)
        chunks = chunk_and_embed_document(text)
        for i, chunk in enumerate(chunks):
            chunk_meta = metadata.copy() if metadata else {}
            chunk_id = self.upsert_chunk(
                document_id, chunk["text"], chunk["embedding"], i, metadata=chunk_meta
            )
            if entity_extractor:
                entities = entity_extractor(chunk["text"])
                for ent in entities:
                    ent_meta = metadata.copy() if metadata else {}
                    entity_id = self.upsert_entity(
                        ent["name"],
                        ent["type"],
                        ent.get("attributes", {}),
                        chunk_id,
                        metadata=ent_meta,
                    )
                    self.create_chunk_entity_relationship(chunk_id, entity_id)
        return document_id

    def find_relevant_chunks(self, query_embedding: list, top_k: int = 5) -> list:
        """
        Find the top_k most relevant chunks by vector similarity (euclidean distance).
        Uses the new Neo4j vector index procedure.
        See: https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/
        """
        # Validate query_embedding is a flat list of floats and correct dimension
        expected_dim = 1536  # OpenAI text-embedding-ada-002 dimensions
        if not isinstance(query_embedding, list) or not all(
            isinstance(x, (float, int)) for x in query_embedding
        ):
            logger.error(
                f"[Neo4jClient] Query embedding must be a flat list of floats. Got: {type(query_embedding)}"
            )
            raise ValueError("Query embedding must be a flat list of floats.")
        if len(query_embedding) != expected_dim:
            logger.error(
                f"[Neo4jClient] Query embedding dimension mismatch: expected {expected_dim}, got {len(query_embedding)}"
            )
            raise ValueError(
                f"Query embedding dimension mismatch: expected {expected_dim}, got {len(query_embedding)}"
            )

        # Convert to float to ensure compatibility
        query_embedding = [float(x) for x in query_embedding]

        # Neo4j expects: index name (str), top_k (int), embedding (list[float])
        cypher = (
            "CALL db.index.vector.queryNodes('chunk_vector_index', $top_k, $embedding) "
            "YIELD node, score "
            "RETURN node.chunk_id AS chunk_id, node.text AS text, node.embedding AS embedding, "
            "node.document_id AS document_id, node.metadata AS metadata, score AS similarity_score "
            "ORDER BY score DESC"
        )
        params = {"embedding": query_embedding, "top_k": top_k}
        if self.driver:
            try:
                with self.driver.session() as session:
                    result = session.run(cypher, params)
                    return [record.data() for record in result]
            except Exception as e:
                logger.error(f"[Neo4jClient] find_relevant_chunks failed: {e}")
                return [{"error": str(e)}]
        logger.info(f"[Neo4jClient] Mock find_relevant_chunks: {params}")
        return []

    def create_user(
        self, name: str, email: str, role: str, metadata: dict = None
    ) -> str:
        """
        Create a User node.
        """
        import uuid, datetime, json

        user_id = str(uuid.uuid4())
        created_at = datetime.datetime.utcnow().isoformat()
        meta = metadata or {}
        meta.setdefault("created_at", created_at)
        meta_str = json.dumps(meta)
        cypher = (
            "CREATE (u:User {user_id: $user_id, name: $name, email: $email, role: $role, created_at: $created_at, metadata: $metadata}) "
            "RETURN u.user_id AS user_id"
        )
        params = {
            "user_id": user_id,
            "name": name,
            "email": email,
            "role": role,
            "created_at": created_at,
            "metadata": meta_str,
        }
        if self.driver:
            try:
                with self.driver.session() as session:
                    result = session.run(cypher, params)
                    return result.single()["user_id"]
            except Exception as e:
                logger.error(f"[Neo4jClient] create_user failed: {e}")
                return {"error": str(e), "user_id": user_id}
        logger.info(f"[Neo4jClient] Mock create_user: {params}")
        return user_id

    def create_step(
        self,
        workflow_id: str,
        step_number: int,
        name: str,
        type_: str,
        status: str,
        performed_by_agent_id: str,
        started_at: str = None,
        finished_at: str = None,
        parameters: dict = None,
        outputs: dict = None,
        metadata: dict = None,
    ) -> str:
        """
        Create a Step node and attach PERFORMED_BY edge to Agent, HAS_STEP to Workflow.
        """
        import uuid, datetime, json

        step_id = str(uuid.uuid4())
        started_at = started_at or datetime.datetime.utcnow().isoformat()
        finished_at = finished_at or None
        parameters = parameters or {}
        outputs = outputs or {}
        meta = metadata or {}
        meta_str = json.dumps(meta)
        cypher = (
            "MATCH (w:Workflow {workflow_id: $workflow_id}), (a:Agent {agent_id: $agent_id}) "
            "CREATE (s:Step {step_id: $step_id, workflow_id: $workflow_id, step_number: $step_number, name: $name, type: $type, status: $status, started_at: $started_at, finished_at: $finished_at, parameters: $parameters, outputs: $outputs, metadata: $metadata}) "
            "MERGE (w)-[:HAS_STEP]->(s) "
            "MERGE (s)-[:PERFORMED_BY]->(a) "
            "RETURN s.step_id AS step_id"
        )
        params = {
            "step_id": step_id,
            "workflow_id": workflow_id,
            "step_number": step_number,
            "name": name,
            "type": type_,
            "status": status,
            "started_at": started_at,
            "finished_at": finished_at,
            "parameters": json.dumps(parameters),
            "outputs": json.dumps(outputs),
            "metadata": meta_str,
            "agent_id": performed_by_agent_id,
        }
        if self.driver:
            try:
                with self.driver.session() as session:
                    result = session.run(cypher, params)
                    return result.single()["step_id"]
            except Exception as e:
                logger.error(f"[Neo4jClient] create_step failed: {e}")
                return {"error": str(e), "step_id": step_id}
        logger.info(f"[Neo4jClient] Mock create_step: {params}")
        return step_id

    def create_tag(
        self, name: str, description: str = "", metadata: dict = None
    ) -> str:
        """
        Create a Tag node.
        """
        import uuid, json

        tag_id = str(uuid.uuid4())
        meta = metadata or {}
        meta_str = json.dumps(meta)
        cypher = (
            "CREATE (t:Tag {tag_id: $tag_id, name: $name, description: $description, metadata: $metadata}) "
            "RETURN t.tag_id AS tag_id"
        )
        params = {
            "tag_id": tag_id,
            "name": name,
            "description": description,
            "metadata": meta_str,
        }
        if self.driver:
            try:
                with self.driver.session() as session:
                    result = session.run(cypher, params)
                    return result.single()["tag_id"]
            except Exception as e:
                logger.error(f"[Neo4jClient] create_tag failed: {e}")
                return {"error": str(e), "tag_id": tag_id}
        logger.info(f"[Neo4jClient] Mock create_tag: {params}")
        return tag_id

    def create_comment(
        self,
        user_id: str,
        text: str,
        target_label: str,
        target_id: str,
        metadata: dict = None,
    ) -> str:
        """
        Create a Comment node and attach WROTE and COMMENTED_ON edges.
        """
        import uuid, datetime, json

        comment_id = str(uuid.uuid4())
        created_at = datetime.datetime.utcnow().isoformat()
        meta = metadata or {}
        meta_str = json.dumps(meta)
        cypher = (
            f"MATCH (u:User {{user_id: $user_id}}), (target:{target_label} {{{target_label.lower()}_id: $target_id}}) "
            "CREATE (c:Comment {comment_id: $comment_id, text: $text, created_at: $created_at, user_id: $user_id, metadata: $metadata}) "
            "MERGE (u)-[:WROTE]->(c) "
            "MERGE (u)-[:COMMENTED_ON]->(target) "
            "RETURN c.comment_id AS comment_id"
        )
        params = {
            "comment_id": comment_id,
            "text": text,
            "created_at": created_at,
            "user_id": user_id,
            "target_id": target_id,
            "metadata": meta_str,
        }
        if self.driver:
            try:
                with self.driver.session() as session:
                    result = session.run(cypher, params)
                    return result.single()["comment_id"]
            except Exception as e:
                logger.error(f"[Neo4jClient] create_comment failed: {e}")
                return {"error": str(e), "comment_id": comment_id}
        logger.info(f"[Neo4jClient] Mock create_comment: {params}")
        return comment_id

    def create_approval(
        self, step_id: str, approved_by: str, status: str, metadata: dict = None
    ) -> str:
        """
        Create an Approval node and attach GAVE and APPROVED edges.
        """
        import uuid, datetime, json

        approval_id = str(uuid.uuid4())
        timestamp = datetime.datetime.utcnow().isoformat()
        meta = metadata or {}
        meta_str = json.dumps(meta)
        cypher = (
            "MATCH (u:User {user_id: $approved_by}), (s:Step {step_id: $step_id}) "
            "CREATE (a:Approval {approval_id: $approval_id, status: $status, step_id: $step_id, approved_by: $approved_by, timestamp: $timestamp, metadata: $metadata}) "
            "MERGE (u)-[:GAVE]->(a) "
            "MERGE (u)-[:APPROVED]->(s) "
            "RETURN a.approval_id AS approval_id"
        )
        params = {
            "approval_id": approval_id,
            "status": status,
            "step_id": step_id,
            "approved_by": approved_by,
            "timestamp": timestamp,
            "metadata": meta_str,
        }
        if self.driver:
            try:
                with self.driver.session() as session:
                    result = session.run(cypher, params)
                    return result.single()["approval_id"]
            except Exception as e:
                logger.error(f"[Neo4jClient] create_approval failed: {e}")
                return {"error": str(e), "approval_id": approval_id}
        logger.info(f"[Neo4jClient] Mock create_approval: {params}")
        return approval_id

    def create_annotation(
        self,
        user_id: str,
        type_: str,
        value,
        target_label: str,
        target_id: str,
        metadata: dict = None,
    ) -> str:
        """
        Create an Annotation node and attach MADE edge to User and target.
        """
        import uuid, datetime, json

        annotation_id = str(uuid.uuid4())
        created_at = datetime.datetime.utcnow().isoformat()
        meta = metadata or {}
        meta_str = json.dumps(meta)
        cypher = (
            f"MATCH (u:User {{user_id: $user_id}}), (target:{target_label} {{{target_label.lower()}_id: $target_id}}) "
            "CREATE (n:Annotation {annotation_id: $annotation_id, type: $type, value: $value, created_at: $created_at, user_id: $user_id, target_id: $target_id, metadata: $metadata}) "
            "MERGE (u)-[:MADE]->(n) "
            "MERGE (n)-[:ANNOTATES]->(target) "
            "RETURN n.annotation_id AS annotation_id"
        )
        params = {
            "annotation_id": annotation_id,
            "type": type_,
            "value": json.dumps(value),
            "created_at": created_at,
            "user_id": user_id,
            "target_id": target_id,
            "metadata": meta_str,
        }
        if self.driver:
            try:
                with self.driver.session() as session:
                    result = session.run(cypher, params)
                    return result.single()["annotation_id"]
            except Exception as e:
                logger.error(f"[Neo4jClient] create_annotation failed: {e}")
                return {"error": str(e), "annotation_id": annotation_id}
        logger.info(f"[Neo4jClient] Mock create_annotation: {params}")
        return annotation_id

    def add_step_uses(self, step_id: str, target_label: str, target_id: str) -> bool:
        """
        Add a USES edge from Step to Document/Chunk/Entity.
        """
        cypher = f"MATCH (s:Step {{step_id: $step_id}}), (target:{target_label} {{{target_label.lower()}_id: $target_id}}) MERGE (s)-[:USES]->(target)"
        params = {"step_id": step_id, "target_id": target_id}
        if self.driver:
            try:
                with self.driver.session() as session:
                    session.run(cypher, params)
                return True
            except Exception as e:
                logger.error(f"[Neo4jClient] add_step_uses failed: {e}")
                return False
        logger.info(f"[Neo4jClient] Mock add_step_uses: {params}")
        return True

    def add_step_creates(self, step_id: str, target_label: str, target_id: str) -> bool:
        """
        Add a CREATES edge from Step to Document/Chunk/Entity.
        """
        cypher = f"MATCH (s:Step {{step_id: $step_id}}), (target:{target_label} {{{target_label.lower()}_id: $target_id}}) MERGE (s)-[:CREATES]->(target)"
        params = {"step_id": step_id, "target_id": target_id}
        if self.driver:
            try:
                with self.driver.session() as session:
                    session.run(cypher, params)
                return True
            except Exception as e:
                logger.error(f"[Neo4jClient] add_step_creates failed: {e}")
                return False
        logger.info(f"[Neo4jClient] Mock add_step_creates: {params}")
        return True

    def add_user_initiated_workflow(self, user_id: str, workflow_id: str) -> bool:
        """
        Add an INITIATED edge from User to Workflow.
        """
        cypher = "MATCH (u:User {user_id: $user_id}), (w:Workflow {workflow_id: $workflow_id}) MERGE (u)-[:INITIATED]->(w)"
        params = {"user_id": user_id, "workflow_id": workflow_id}
        if self.driver:
            try:
                with self.driver.session() as session:
                    session.run(cypher, params)
                return True
            except Exception as e:
                logger.error(f"[Neo4jClient] add_user_initiated_workflow failed: {e}")
                return False
        logger.info(f"[Neo4jClient] Mock add_user_initiated_workflow: {params}")
        return True

    def add_tag(self, tag_id: str, target_label: str, target_id: str) -> bool:
        """
        Add a TAGS edge from Tag to Workflow/Step/Document/Chunk/Entity.
        """
        cypher = f"MATCH (t:Tag {{tag_id: $tag_id}}), (target:{target_label} {{{target_label.lower()}_id: $target_id}}) MERGE (t)-[:TAGS]->(target)"
        params = {"tag_id": tag_id, "target_id": target_id}
        if self.driver:
            try:
                with self.driver.session() as session:
                    session.run(cypher, params)
                return True
            except Exception as e:
                logger.error(f"[Neo4jClient] add_tag failed: {e}")
                return False
        logger.info(f"[Neo4jClient] Mock add_tag: {params}")
        return True


if __name__ == "__main__":
    import os
    import time

    logging.basicConfig(level=logging.DEBUG)
    # OAMAT app Neo4j defaults
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "oamatdbtest")
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[AuthTest] Attempt {attempt}: Connecting to {uri} as {user}...")
            client = Neo4jClient(uri, user, password)
            if client.check_connection():
                print("[AuthTest] SUCCESS: Connected to Neo4j!")
                break
            else:
                print("[AuthTest] FAILURE: Could not connect (driver not ready)")
        except Exception as e:
            print(f"[AuthTest] ERROR: {e}")
        if attempt < max_retries:
            print(f"[AuthTest] Retrying in 2 seconds...")
            time.sleep(2)
    else:
        print(
            "[AuthTest] FINAL FAILURE: Could not authenticate to Neo4j after retries."
        )
