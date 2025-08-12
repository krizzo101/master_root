"""
Meta-Conceptual Synthesis Agent
==============================

Persistent, autonomous agent for extracting, synthesizing, and persisting meta-level, conceptual, and actionable knowledge from chat logs and agent artifacts. Augments atomic parser outputs with lessons, themes, realizations, anti-patterns, best practices, recommendations, and more. Enables all agents to access and learn from this knowledge in real time.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

from shared.interfaces.database.arango_interface import DirectArangoDB

CONCEPTUAL_NODE_COLLECTION = "meta_conceptual_nodes"
CONCEPTUAL_EDGE_COLLECTION = "meta_conceptual_edges"
DRY_RUN = True  # Set to False to enable DB writes


class MetaConceptualSynthesisAgent:
    def __init__(
        self, history_dir: str, arango_config: dict[str, Any], poll_interval: int = 60
    ):
        self.history_dir = Path(history_dir)
        self.db_client = DirectArangoDB(**arango_config)
        self.poll_interval = poll_interval
        self.logger = logging.getLogger("meta_conceptual_synthesis_agent")
        self.logger.setLevel(logging.INFO)
        self.processed_sessions = set()

    def run(self):
        self.logger.info(
            "Meta-Conceptual Synthesis Agent started. Entering persistent autonomous loop."
        )
        while True:
            try:
                # 1. Check for new sessions to process
                sessions = [d for d in self.history_dir.iterdir() if d.is_dir()]
                new_sessions = [
                    s for s in sessions if s.name not in self.processed_sessions
                ]
                if new_sessions:
                    for session_dir in new_sessions:
                        session_id = session_dir.name
                        try:
                            self.logger.info(f"Processing session: {session_id}")
                            chat_log, plans = self.load_session(session_dir)
                            (
                                conceptual_nodes,
                                conceptual_edges,
                            ) = self.synthesize_conceptual_knowledge(
                                session_id, chat_log, plans
                            )
                            self.persist_conceptual_knowledge(
                                conceptual_nodes, conceptual_edges
                            )
                            self.logger.info(
                                f"Session {session_id} processed: {len(conceptual_nodes)} concepts, {len(conceptual_edges)} edges."
                            )
                            self.processed_sessions.add(session_id)
                        except Exception as e:
                            self.logger.error(
                                f"Error processing session {session_id}: {e}"
                            )
                else:
                    # 2. If no new sessions, perform self-improvement, maintenance, or monitoring
                    self.logger.info(
                        "No new sessions found. Performing self-improvement and maintenance."
                    )
                    self.self_improve()
                    self.maintenance()
                    self.logger.info("Self-improvement and maintenance cycle complete.")
                # 3. Log progress and evidence
                self.logger.info(
                    f"Processed sessions: {len(self.processed_sessions)}. Still monitoring for new work."
                )
                # 4. Never yield for user input unless a true hard blocker is encountered
                # 5. Sleep briefly before next cycle to avoid busy-waiting
                time.sleep(self.poll_interval)
            except Exception as e:
                self.logger.error(f"[FATAL] Unhandled error in main loop: {e}")
                # Only stop if a true hard blocker (e.g., missing credentials, fatal error)
                if "OpenAI API key not found" in str(
                    e
                ) or "OpenAI interface unavailable" in str(e):
                    self.logger.error("Critical dependency missing. Exiting.")
                    break
                # Otherwise, log and continue
                continue

    def load_session(self, session_dir: Path):
        # Load cleaned chat log
        chat_log = []
        for file in session_dir.glob("*_clean.md"):
            with open(file) as f:
                chat_log = f.readlines()
        # Load plan files
        plans = []
        plans_dir = session_dir / "plans"
        if plans_dir.exists():
            for plan_file in plans_dir.glob("plan_*.md"):
                with open(plan_file) as f:
                    plans.append(f.read())
        return chat_log, plans

    def synthesize_conceptual_knowledge(
        self, session_id: str, chat_log: list[str], plans: list[str]
    ):
        # TODO: Use LLM/NLP/analytics for deep reflection and pattern recognition
        # For now, extract simple meta-level concepts as a stub
        conceptual_nodes = []
        conceptual_edges = []
        # Example: If user asks for templates, create a 'lesson' node
        for line in chat_log:
            if "template" in line.lower():
                node = {
                    "concept_id": f"lesson_{session_id}_template",
                    "concept_type": "lesson",
                    "content": "User frequently requests templates. Agents should have template generation capabilities.",
                    "evidence": [session_id],
                    "context": {"session_id": session_id},
                    "confidence": 0.8,
                    "validation_status": "needs_review",
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "source": "meta_conceptual_synthesis_agent_v1",
                }
                conceptual_nodes.append(node)
        # Example: If plan mentions 'autonomous', create a 'best_practice' node
        for plan in plans:
            if "autonomous" in plan.lower():
                node = {
                    "concept_id": f"best_practice_{session_id}_autonomous",
                    "concept_type": "best_practice",
                    "content": "Agents should operate in fully autonomous, persistent mode for maximum efficiency.",
                    "evidence": [session_id],
                    "context": {"session_id": session_id},
                    "confidence": 0.9,
                    "validation_status": "needs_review",
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "source": "meta_conceptual_synthesis_agent_v1",
                }
                conceptual_nodes.append(node)
        # TODO: Add more sophisticated extraction and edge creation
        return conceptual_nodes, conceptual_edges

    def persist_conceptual_knowledge(
        self, conceptual_nodes: list[dict], conceptual_edges: list[dict]
    ):
        if DRY_RUN:
            self.logger.info("[DRY RUN] Would persist conceptual nodes:")
            for node in conceptual_nodes:
                self.logger.info(json.dumps(node, indent=2))
            if conceptual_edges:
                self.logger.info("[DRY RUN] Would persist conceptual edges:")
                for edge in conceptual_edges:
                    self.logger.info(json.dumps(edge, indent=2))
            print("\n[DRY RUN] Conceptual nodes:")
            for node in conceptual_nodes:
                print(json.dumps(node, indent=2))
            if conceptual_edges:
                print("\n[DRY RUN] Conceptual edges:")
                for edge in conceptual_edges:
                    print(json.dumps(edge, indent=2))
        else:
            if conceptual_nodes:
                self.db_client.batch_insert(
                    CONCEPTUAL_NODE_COLLECTION, conceptual_nodes
                )
            if conceptual_edges:
                self.db_client.batch_insert(
                    CONCEPTUAL_EDGE_COLLECTION, conceptual_edges
                )

    def self_improve(self):
        # TODO: Analyze outputs, refine extraction logic, update guardrails
        self.logger.info("Self-improvement cycle complete.")

    def maintenance(self):
        # Placeholder for maintenance tasks: archiving, cleaning, validating data, etc.
        self.logger.info("Maintenance: archiving, cleaning, validating data (stub).")


def check_openai_available():
    """
    Fail-fast check for OpenAI/LLM availability. Exits if not available.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print(
            "[FATAL] OpenAI API key not found. Set OPENAI_API_KEY in environment.",
            file=sys.stderr,
        )
        sys.exit(1)
    try:
        from shared.openai_interfaces.responses_interface import (
            OpenAIResponsesInterface,
        )

        client = OpenAIResponsesInterface(api_key=api_key)
        # Optionally, make a minimal test call (e.g., list models or a dummy completion)
        # client.ping()  # Uncomment if supported
    except Exception as e:
        print(f"[FATAL] OpenAI interface unavailable: {e}. Exiting.", file=sys.stderr)
        sys.exit(1)


def main():
    check_openai_available()
    arango_config = {
        "host": os.getenv("ARANGO_URL", "http://127.0.0.1:8550"),
        "database": os.getenv("ARANGO_DB", "_system"),
        "username": os.getenv("ARANGO_USERNAME", "root"),
        "password": os.getenv("ARANGO_PASSWORD", "change_me"),
    }
    history_dir = ".cursor/history/"
    agent = MetaConceptualSynthesisAgent(history_dir, arango_config)
    agent.run()


if __name__ == "__main__":
    main()
