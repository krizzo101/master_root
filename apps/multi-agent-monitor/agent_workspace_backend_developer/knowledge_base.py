"""
Knowledge Base Implementation
Shared knowledge repository for agents
"""

import json
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from interfaces import IKnowledgeBase


class KnowledgeBase(IKnowledgeBase):
    """Centralized knowledge management system"""

    def __init__(self, storage_path: Path = None):
        self.storage_path = storage_path or Path("/tmp/agent_knowledge")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.knowledge: Dict[str, Dict[str, Any]] = {}
        self.topic_index: Dict[str, List[str]] = defaultdict(list)
        self.expert_scores: Dict[str, Dict[str, float]] = defaultdict(
            lambda: defaultdict(float)
        )

        self._load_knowledge()

    async def store_knowledge(self, topic: str, content: Dict[str, Any]) -> str:
        """Store new knowledge entry"""
        knowledge_id = str(uuid.uuid4())

        entry = {
            "id": knowledge_id,
            "topic": topic,
            "content": content,
            "created_at": datetime.utcnow().isoformat(),
            "access_count": 0,
            "usefulness_score": 0.5,
            "contributor": content.get("agent_id", "unknown"),
        }

        self.knowledge[knowledge_id] = entry
        self.topic_index[topic].append(knowledge_id)

        # Update expert score
        contributor = entry["contributor"]
        self.expert_scores[topic][contributor] += 1

        # Persist
        await self._save_entry(entry)

        return knowledge_id

    async def query_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """Search knowledge base"""
        results = []
        query_lower = query.lower()

        for knowledge_id, entry in self.knowledge.items():
            # Simple text matching for now
            if (
                query_lower in entry["topic"].lower()
                or query_lower in json.dumps(entry["content"]).lower()
            ):
                # Increment access count
                entry["access_count"] += 1
                results.append(entry)

        # Sort by usefulness and access count
        results.sort(
            key=lambda x: (x["usefulness_score"], x["access_count"]), reverse=True
        )

        return results[:10]  # Return top 10

    async def get_expert(self, topic: str) -> Optional[str]:
        """Find the most knowledgeable agent for a topic"""
        if topic in self.expert_scores:
            experts = self.expert_scores[topic]
            if experts:
                # Return agent with highest contribution score
                return max(experts, key=experts.get)
        return None

    async def update_usefulness(self, knowledge_id: str, useful: bool):
        """Update usefulness score based on feedback"""
        if knowledge_id in self.knowledge:
            entry = self.knowledge[knowledge_id]
            # Simple exponential moving average
            alpha = 0.1
            score_delta = 1.0 if useful else 0.0
            entry["usefulness_score"] = (
                alpha * score_delta + (1 - alpha) * entry["usefulness_score"]
            )

    def _load_knowledge(self):
        """Load knowledge from disk"""
        knowledge_file = self.storage_path / "knowledge.json"
        if knowledge_file.exists():
            with open(knowledge_file, "r") as f:
                data = json.load(f)
                self.knowledge = data.get("knowledge", {})
                self.topic_index = defaultdict(list, data.get("topic_index", {}))
                self.expert_scores = defaultdict(
                    lambda: defaultdict(float), data.get("expert_scores", {})
                )

    async def _save_entry(self, entry: Dict[str, Any]):
        """Persist knowledge entry"""
        # Append to journal
        journal_file = self.storage_path / "knowledge_journal.jsonl"
        with open(journal_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

        # Periodically save full state
        if len(self.knowledge) % 10 == 0:
            await self._save_full_state()

    async def _save_full_state(self):
        """Save complete knowledge base state"""
        knowledge_file = self.storage_path / "knowledge.json"

        state = {
            "knowledge": self.knowledge,
            "topic_index": dict(self.topic_index),
            "expert_scores": {
                topic: dict(scores) for topic, scores in self.expert_scores.items()
            },
        }

        with open(knowledge_file, "w") as f:
            json.dump(state, f, indent=2)
