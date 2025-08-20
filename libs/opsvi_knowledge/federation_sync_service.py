#!/usr/bin/env python3
"""
Knowledge Federation Sync Service
Enables cross-project knowledge sharing and synchronization
"""

import asyncio
import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

import aiohttp
from neo4j import AsyncGraphDatabase

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SyncDirection(Enum):
    """Sync direction for federation"""

    PUSH = "push"
    PULL = "pull"
    BIDIRECTIONAL = "bidirectional"


class KnowledgeVisibility(Enum):
    """Visibility levels for federated knowledge"""

    PRIVATE = "private"  # Local only
    PROJECT = "project"  # Within project
    FEDERATED = "federated"  # Shared across projects
    PUBLIC = "public"  # Publicly available


@dataclass
class FederationConfig:
    """Configuration for federation sync"""

    project_id: str
    federation_url: str
    api_key: str
    sync_interval: int = 3600  # 1 hour
    sync_direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    min_confidence: float = 0.85
    max_sync_items: int = 100
    enable_auto_sync: bool = True
    anonymize_data: bool = True


@dataclass
class SyncMetrics:
    """Metrics for sync operations"""

    last_sync: Optional[datetime] = None
    items_pushed: int = 0
    items_pulled: int = 0
    sync_errors: int = 0
    average_sync_time: float = 0.0
    success_rate: float = 1.0


class KnowledgeAnonymizer:
    """Anonymize sensitive data before federation"""

    @staticmethod
    def anonymize(knowledge: Dict) -> Dict:
        """Remove sensitive information from knowledge"""
        anonymized = knowledge.copy()

        # Remove project-specific identifiers
        sensitive_fields = ["project_path", "user_id", "api_keys", "credentials"]
        for field in sensitive_fields:
            anonymized.pop(field, None)

        # Generalize file paths
        if "file_path" in anonymized:
            anonymized["file_path"] = KnowledgeAnonymizer._generalize_path(
                anonymized["file_path"]
            )

        # Abstract domain-specific terms
        if "content" in anonymized:
            anonymized["content"] = KnowledgeAnonymizer._abstract_content(
                anonymized["content"]
            )

        # Add anonymization metadata
        anonymized["anonymized"] = True
        anonymized["anonymized_at"] = datetime.utcnow().isoformat()

        return anonymized

    @staticmethod
    def _generalize_path(path: str) -> str:
        """Generalize file paths to remove project specifics"""
        # Remove absolute paths
        if path.startswith("/"):
            parts = path.split("/")
            # Keep only relative structure
            return "/".join(["..."] + parts[-3:]) if len(parts) > 3 else path
        return path

    @staticmethod
    def _abstract_content(content: str) -> str:
        """Abstract domain-specific content"""
        # This is a simple implementation
        # In production, use more sophisticated NLP techniques
        abstractions = {
            r"https?://[^\s]+": "[URL]",
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b": "[EMAIL]",
            r"\b(?:\d{1,3}\.){3}\d{1,3}\b": "[IP_ADDRESS]",
            r"[a-zA-Z0-9]{20,}": "[TOKEN]",
        }

        result = content
        import re

        for pattern, replacement in abstractions.items():
            result = re.sub(pattern, replacement, result)

        return result


class ConflictResolver:
    """Resolve conflicts between local and federated knowledge"""

    @staticmethod
    def resolve(local: Dict, federated: Dict) -> Dict:
        """Resolve conflict between local and federated knowledge"""
        # Resolution strategy based on multiple factors

        # Factor 1: Confidence score
        local_confidence = local.get("confidence_score", 0)
        federated_confidence = federated.get("confidence_score", 0)

        # Factor 2: Usage count
        local_usage = local.get("usage_count", 0)
        federated_usage = federated.get("usage_count", 0)

        # Factor 3: Recency
        local_updated = local.get("updated_at", local.get("created_at", ""))
        federated_updated = federated.get("updated_at", federated.get("created_at", ""))

        # Factor 4: Source diversity
        federated_sources = len(federated.get("source_projects", []))

        # Calculate scores
        local_score = (
            local_confidence * 0.3
            + min(local_usage / 100, 1.0) * 0.2
            + (1.0 if local_updated > federated_updated else 0.0) * 0.3
            + 0.2  # Local bias
        )

        federated_score = (
            federated_confidence * 0.3
            + min(federated_usage / 100, 1.0) * 0.2
            + (1.0 if federated_updated > local_updated else 0.0) * 0.3
            + min(federated_sources / 10, 1.0) * 0.2
        )

        # Resolve based on scores
        if federated_score > local_score:
            # Use federated version but preserve local metadata
            result = federated.copy()
            result["local_metadata"] = {
                "previous_confidence": local_confidence,
                "previous_usage": local_usage,
                "conflict_resolved": True,
                "resolution_score": federated_score,
            }
            return result
        else:
            # Keep local version
            return local


class FederationSyncService:
    """Main federation sync service"""

    def __init__(self, config: FederationConfig):
        self.config = config
        self.metrics = SyncMetrics()
        self.anonymizer = KnowledgeAnonymizer()
        self.resolver = ConflictResolver()
        self.session: Optional[aiohttp.ClientSession] = None
        self.neo4j_driver = None
        self._sync_task = None

    async def initialize(self):
        """Initialize the service"""
        # Create HTTP session
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "X-Project-ID": self.config.project_id,
        }
        self.session = aiohttp.ClientSession(headers=headers)

        # Initialize Neo4j connection
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "password")

        self.neo4j_driver = AsyncGraphDatabase.driver(
            neo4j_uri, auth=(neo4j_user, neo4j_password)
        )

        # Start auto-sync if enabled
        if self.config.enable_auto_sync:
            self._sync_task = asyncio.create_task(self._auto_sync_loop())

        logger.info(
            f"Federation sync service initialized for project {self.config.project_id}"
        )

    async def close(self):
        """Close the service"""
        if self._sync_task:
            self._sync_task.cancel()

        if self.session:
            await self.session.close()

        if self.neo4j_driver:
            await self.neo4j_driver.close()

    async def _auto_sync_loop(self):
        """Auto sync loop"""
        while True:
            try:
                await asyncio.sleep(self.config.sync_interval)

                if self.config.sync_direction in [
                    SyncDirection.PUSH,
                    SyncDirection.BIDIRECTIONAL,
                ]:
                    await self.push_knowledge()

                if self.config.sync_direction in [
                    SyncDirection.PULL,
                    SyncDirection.BIDIRECTIONAL,
                ]:
                    await self.pull_knowledge()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto sync error: {e}")
                self.metrics.sync_errors += 1

    async def push_knowledge(self) -> Dict:
        """Push local knowledge to federation"""
        start_time = datetime.utcnow()

        try:
            # Select knowledge for sharing
            shareable = await self._select_shareable_knowledge()

            if not shareable:
                logger.info("No knowledge to push")
                return {"status": "success", "pushed": 0}

            # Anonymize if configured
            if self.config.anonymize_data:
                shareable = [self.anonymizer.anonymize(k) for k in shareable]

            # Push to federation
            async with self.session.post(
                f"{self.config.federation_url}/api/v1/federation/push",
                json={
                    "project_id": self.config.project_id,
                    "knowledge": shareable,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            ) as response:
                if response.status == 200:
                    result = await response.json()

                    # Update metrics
                    self.metrics.items_pushed += len(shareable)
                    self.metrics.last_sync = datetime.utcnow()

                    # Mark knowledge as federated
                    await self._mark_as_federated(
                        [k["knowledge_id"] for k in shareable]
                    )

                    logger.info(f"Pushed {len(shareable)} knowledge items")
                    return result
                else:
                    error = await response.text()
                    raise Exception(f"Push failed: {error}")

        except Exception as e:
            logger.error(f"Push knowledge error: {e}")
            self.metrics.sync_errors += 1
            return {"status": "error", "message": str(e)}
        finally:
            # Update average sync time
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.average_sync_time = (
                self.metrics.average_sync_time * 0.9 + elapsed * 0.1
            )

    async def pull_knowledge(self) -> Dict:
        """Pull knowledge from federation"""
        try:
            # Get project context
            context = await self._get_project_context()

            # Query federation
            params = {
                "context": json.dumps(context),
                "limit": self.config.max_sync_items,
                "min_confidence": self.config.min_confidence,
            }

            async with self.session.get(
                f"{self.config.federation_url}/api/v1/federation/pull", params=params
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    knowledge_items = result.get("knowledge", [])

                    if not knowledge_items:
                        logger.info("No knowledge to pull")
                        return {"status": "success", "pulled": 0}

                    # Process and store
                    stored = await self._process_federated_knowledge(knowledge_items)

                    # Update metrics
                    self.metrics.items_pulled += stored
                    self.metrics.last_sync = datetime.utcnow()

                    logger.info(f"Pulled {stored} knowledge items")
                    return {"status": "success", "pulled": stored}
                else:
                    error = await response.text()
                    raise Exception(f"Pull failed: {error}")

        except Exception as e:
            logger.error(f"Pull knowledge error: {e}")
            self.metrics.sync_errors += 1
            return {"status": "error", "message": str(e)}

    async def _select_shareable_knowledge(self) -> List[Dict]:
        """Select knowledge eligible for federation"""
        query = """
        MATCH (k:Knowledge)
        WHERE k.confidence_score >= $min_confidence
        AND k.visibility IN ['federated', 'public']
        AND (k.federated_at IS NULL OR k.updated_at > k.federated_at)
        AND k.usage_count >= 3
        RETURN k
        LIMIT $limit
        """

        async with self.neo4j_driver.session() as session:
            result = await session.run(
                query,
                min_confidence=self.config.min_confidence,
                limit=self.config.max_sync_items,
            )

            knowledge = []
            async for record in result:
                k = dict(record["k"])
                knowledge.append(k)

            return knowledge

    async def _mark_as_federated(self, knowledge_ids: List[str]):
        """Mark knowledge as federated"""
        query = """
        MATCH (k:Knowledge)
        WHERE k.knowledge_id IN $ids
        SET k.federated_at = datetime(),
            k.federation_status = 'synced'
        """

        async with self.neo4j_driver.session() as session:
            await session.run(query, ids=knowledge_ids)

    async def _get_project_context(self) -> Dict:
        """Get project context for federation queries"""
        # Analyze local knowledge to understand project context
        query = """
        MATCH (k:Knowledge)
        WITH k.knowledge_type as type, count(*) as count
        ORDER BY count DESC
        LIMIT 5
        RETURN collect({type: type, count: count}) as distribution
        """

        async with self.neo4j_driver.session() as session:
            result = await session.run(query)
            record = await result.single()

            return {
                "project_id": self.config.project_id,
                "knowledge_distribution": record["distribution"] if record else [],
                "interests": await self._get_project_interests(),
            }

    async def _get_project_interests(self) -> List[str]:
        """Get project interests based on recent queries"""
        # This would analyze recent searches and usage patterns
        # For now, return common interests
        return ["error_handling", "performance", "best_practices", "patterns"]

    async def _process_federated_knowledge(self, knowledge_items: List[Dict]) -> int:
        """Process and store federated knowledge"""
        stored = 0

        for item in knowledge_items:
            try:
                # Check if exists locally
                existing = await self._find_local_knowledge(item["id"])

                if existing:
                    # Resolve conflict
                    resolved = self.resolver.resolve(existing, item)
                    await self._update_knowledge(resolved)
                else:
                    # Store new knowledge
                    item["source"] = "federated"
                    item["federated_from"] = item.get("source_projects", [])
                    await self._store_knowledge(item)

                stored += 1

            except Exception as e:
                logger.error(f"Error processing federated knowledge: {e}")

        return stored

    async def _find_local_knowledge(self, knowledge_id: str) -> Optional[Dict]:
        """Find local knowledge by ID or similarity"""
        query = """
        MATCH (k:Knowledge {knowledge_id: $id})
        RETURN k
        """

        async with self.neo4j_driver.session() as session:
            result = await session.run(query, id=knowledge_id)
            record = await result.single()

            if record:
                return dict(record["k"])
            return None

    async def _update_knowledge(self, knowledge: Dict):
        """Update existing knowledge"""
        query = """
        MATCH (k:Knowledge {knowledge_id: $id})
        SET k += $updates,
            k.updated_at = datetime()
        """

        updates = {
            k: v
            for k, v in knowledge.items()
            if k not in ["knowledge_id", "created_at"]
        }

        async with self.neo4j_driver.session() as session:
            await session.run(query, id=knowledge["knowledge_id"], updates=updates)

    async def _store_knowledge(self, knowledge: Dict):
        """Store new federated knowledge"""
        query = """
        CREATE (k:Knowledge $props)
        SET k.created_at = datetime(),
            k.source = 'federated'
        """

        async with self.neo4j_driver.session() as session:
            await session.run(query, props=knowledge)

    def get_metrics(self) -> Dict:
        """Get sync metrics"""
        return asdict(self.metrics)

    async def force_sync(self) -> Dict:
        """Force immediate sync"""
        results = {}

        if self.config.sync_direction in [
            SyncDirection.PUSH,
            SyncDirection.BIDIRECTIONAL,
        ]:
            results["push"] = await self.push_knowledge()

        if self.config.sync_direction in [
            SyncDirection.PULL,
            SyncDirection.BIDIRECTIONAL,
        ]:
            results["pull"] = await self.pull_knowledge()

        return results


# Example usage
async def main():
    """Example federation sync"""
    config = FederationConfig(
        project_id="project-123",
        federation_url="https://federation.ai-factory.dev",
        api_key="test-api-key",
        sync_interval=300,  # 5 minutes for testing
        enable_auto_sync=False,  # Manual for testing
    )

    service = FederationSyncService(config)

    try:
        await service.initialize()

        # Force sync
        result = await service.force_sync()
        print(f"Sync result: {json.dumps(result, indent=2)}")

        # Get metrics
        metrics = service.get_metrics()
        print(f"Metrics: {json.dumps(metrics, indent=2, default=str)}")

    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(main())
