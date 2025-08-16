#!/usr/bin/env python3
"""
Review & Connect Agent
- Scans the atomic graph in ArangoDB
- Detects and creates higher-level conceptual relationships (Q&A, decisions, themes, orphans)
- Upserts new edges/nodes with provenance
- Can be run as a batch job or on-demand
"""

import argparse
import logging
import os
from datetime import datetime

from arango import ArangoClient

# Config
ARANGO_URL = os.environ.get("ARANGO_URL", "http://127.0.0.1:8550")
DB_NAME = os.environ.get("ARANGO_DB", "_system")
USERNAME = os.environ.get("ARANGO_USER", "root")
PASSWORD = os.environ.get("ARANGO_PASS", "change_me")
GRAPH_NAME = os.environ.get("ARANGO_GRAPH", "specstory_graph")
VERTEX_COLLECTION = os.environ.get("ARANGO_VERTICES", "specstory_components")
EDGE_COLLECTION = os.environ.get("ARANGO_EDGES", "specstory_relationships")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class ReviewConnectAgent:
    def __init__(self):
        self.client = ArangoClient(hosts=ARANGO_URL)
        self.db = self.client.db(DB_NAME, username=USERNAME, password=PASSWORD)
        self.graph = self.db.graph(GRAPH_NAME)
        self.vertices = self.db.collection(VERTEX_COLLECTION)
        self.edges = self.db.collection(EDGE_COLLECTION)
        self.now = datetime.utcnow().isoformat()

    def run(self):
        logging.info("Starting Review & Connect Agent run...")
        self.detect_and_link_qa_pairs()
        self.detect_and_link_decision_chains()
        self.detect_and_link_themes()
        self.detect_and_link_orphans()
        logging.info("Review & Connect Agent run complete.")

    def detect_and_link_qa_pairs(self):
        """Detect Q&A pairs and create 'answers' edges."""
        logging.info("[Q&A] Scanning for Q&A pairs...")
        # Find all conversation_turn nodes with type 'question'
        query = f"""
        FOR n IN {VERTEX_COLLECTION}
            FILTER n.component_type == 'conversation_turn' && n.content.processed_content.speech_act == 'question'
            SORT n.metadata.session_id, n.metadata.turn_index
            RETURN n
        """
        questions = list(self.db.aql.execute(query))
        logging.info(f"[Q&A] Found {len(questions)} question nodes.")
        for q in questions:
            session_id = q.get("metadata", {}).get("session_id")
            turn_index = q.get("metadata", {}).get("turn_index")
            if session_id is None or turn_index is None:
                continue
            # Find the next turn in the same session
            next_turn_query = f"""
            FOR n IN {VERTEX_COLLECTION}
                FILTER n.component_type == 'conversation_turn'
                    && n.metadata.session_id == @session_id
                    && n.metadata.turn_index == @next_index
                RETURN n
            """
            next_turns = list(
                self.db.aql.execute(
                    next_turn_query,
                    bind_vars={"session_id": session_id, "next_index": turn_index + 1},
                )
            )
            if not next_turns:
                continue
            answer = next_turns[0]
            # Heuristic: if answer's speech_act is 'answer' or 'response'
            speech_act = (
                answer.get("content", {})
                .get("processed_content", {})
                .get("speech_act", "")
            )
            if speech_act not in ("answer", "response"):
                continue
            from_id = q["_id"]
            to_id = answer["_id"]
            self.upsert_edge(
                from_id,
                to_id,
                "answers",
                evidence={
                    "detected_by": "review_connect_agent",
                    "timestamp": self.now,
                    "reason": "Q&A adjacency in session",
                    "session_id": session_id,
                    "question_turn": turn_index,
                    "answer_turn": turn_index + 1,
                },
            )

    def detect_and_link_decision_chains(self):
        """Detect decision chains and create 'decision_about'/'affects' edges."""
        # TODO: Implement decision chain detection and linking
        logging.info("[Decision Chains] Pattern detection not yet implemented.")

    def detect_and_link_themes(self):
        """Detect recurring themes/entities and create 'relates_to' edges."""
        # TODO: Implement theme/entity detection and linking
        logging.info("[Themes] Pattern detection not yet implemented.")

    def detect_and_link_orphans(self):
        """Detect orphaned nodes and link to context (e.g., session/file)."""
        # TODO: Implement orphan detection and context linking
        logging.info("[Orphans] Pattern detection not yet implemented.")

    def upsert_edge(self, from_id, to_id, rel_type, evidence=None):
        """Upsert an edge with provenance and idempotency check."""
        # Check if edge already exists
        query = f"""
        FOR e IN {EDGE_COLLECTION}
            FILTER e._from == @from_id && e._to == @to_id && e.relationship_type == @rel_type
            RETURN e
        """
        existing = list(
            self.db.aql.execute(
                query,
                bind_vars={"from_id": from_id, "to_id": to_id, "rel_type": rel_type},
            )
        )
        if existing:
            logging.info(f"[Edge Exists] {from_id} --{rel_type}--> {to_id}")
            return
        # Insert new edge
        edge_doc = {
            "_from": from_id,
            "_to": to_id,
            "relationship_type": rel_type,
            "provenance": evidence or {},
            "created_by": "review_connect_agent",
            "created_timestamp": self.now,
        }
        self.edges.insert(edge_doc)
        logging.info(f"[Edge Created] {from_id} --{rel_type}--> {to_id}")

    def log_provenance(self, action, details):
        """Log provenance for new connections."""
        # TODO: Implement provenance logging
        pass


def main():
    parser = argparse.ArgumentParser(
        description="Review & Connect Agent for SpecStory Graph"
    )
    parser.add_argument("--batch", action="store_true", help="Run as batch job")
    args = parser.parse_args()
    agent = ReviewConnectAgent()
    agent.run()


if __name__ == "__main__":
    main()
