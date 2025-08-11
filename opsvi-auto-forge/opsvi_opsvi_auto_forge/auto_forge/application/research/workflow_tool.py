"""Main workflow tool for the research stack."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .config import get_research_config, ResearchConfig
from .errors import OrchestrationError, PersistenceError
from .models import RankedResult, ResearchSummary
from .orchestrator import ResearchOrchestrator

logger = logging.getLogger(__name__)


class ResearchWorkflowTool:
    """Main workflow tool for executing research tasks."""

    def __init__(self, config: Optional[ResearchConfig] = None) -> None:
        self.config = config or get_research_config()
        self.orchestrator = ResearchOrchestrator(self.config)
        self._setup_persistence()

    def _setup_persistence(self) -> None:
        """Setup persistence directory."""
        self.persistence_dir = Path("/home/opsvi/auto_forge/research_store")
        self.persistence_dir.mkdir(exist_ok=True)

    async def execute(
        self,
        query: str,
        k: int = 10,
        persist: bool = True,
        enable_synthesis: bool | None = None,
        **kwargs,
    ) -> ResearchSummary:
        """Execute research workflow and optionally persist results."""
        try:
            # Execute research
            summary = await self.orchestrator.execute_research(
                query=query,
                k=k,
                enable_synthesis=enable_synthesis,
                **kwargs,
            )

            # Persist results if requested
            if persist and self.config.enable_persistence:
                await self._persist_results(summary)

            return summary

        except Exception as e:
            logger.error(f"Research workflow failed: {e}")
            raise OrchestrationError(f"Research execution failed: {e}")

    async def _persist_results(self, summary: ResearchSummary) -> None:
        """Persist research results to JSONL storage."""
        try:
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            query_safe = summary.query.replace(" ", "_").replace("/", "_")[:50]
            filename = f"{timestamp}_{query_safe}.jsonl"
            filepath = self.persistence_dir / filename

            # Convert summary to JSON-serializable format
            summary_dict = self._summary_to_dict(summary)

            # Write to JSONL file
            with open(filepath, "w") as f:
                f.write(json.dumps(summary_dict, default=str) + "\n")

            logger.info(f"Research results persisted to: {filepath}")

        except Exception as e:
            logger.error(f"Failed to persist results: {e}")
            raise PersistenceError(f"Failed to persist research results: {e}")

    def _summary_to_dict(self, summary: ResearchSummary) -> dict[str, Any]:
        """Convert ResearchSummary to dictionary for JSON serialization."""
        return {
            "query": summary.query,
            "top_results": [
                {
                    "source": result.source.value,
                    "url": result.url,
                    "title": result.title,
                    "snippet": result.snippet,
                    "content": result.content,
                    "score": result.score,
                    "relevance": float(result.relevance),
                    "ranking_factors": result.ranking_factors,
                    "metadata": result.metadata,
                    "timestamp": result.timestamp.isoformat(),
                }
                for result in summary.top_results
            ],
            "synthesis": summary.synthesis,
            "total_sources": summary.total_sources,
            "successful_sources": summary.successful_sources,
            "failed_sources": summary.failed_sources,
            "execution_time": summary.execution_time,
            "metadata": summary.metadata,
            "timestamp": summary.timestamp.isoformat(),
        }

    async def load_persisted_results(
        self, query: Optional[str] = None, limit: int = 10
    ) -> list[ResearchSummary]:
        """Load previously persisted research results."""
        try:
            results = []

            # Get all JSONL files in persistence directory
            jsonl_files = list(self.persistence_dir.glob("*.jsonl"))
            jsonl_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            for filepath in jsonl_files[:limit]:
                try:
                    with open(filepath) as f:
                        for line in f:
                            if line.strip():
                                summary_dict = json.loads(line)

                                # Filter by query if specified
                                if (
                                    query
                                    and query.lower()
                                    not in summary_dict["query"].lower()
                                ):
                                    continue

                                # Convert back to ResearchSummary
                                summary = self._dict_to_summary(summary_dict)
                                results.append(summary)

                except Exception as e:
                    logger.warning(f"Failed to load file {filepath}: {e}")
                    continue

            return results

        except Exception as e:
            logger.error(f"Failed to load persisted results: {e}")
            raise PersistenceError(f"Failed to load persisted results: {e}")

    def _dict_to_summary(self, summary_dict: dict[str, Any]) -> ResearchSummary:
        """Convert dictionary back to ResearchSummary."""
        from .models import RankingScore, SourceType

        # Convert results back to RankedResult objects
        top_results = []
        for result_dict in summary_dict["top_results"]:
            result = RankedResult(
                source=SourceType(result_dict["source"]),
                url=result_dict["url"],
                title=result_dict["title"],
                snippet=result_dict["snippet"],
                content=result_dict.get("content"),
                score=result_dict["score"],
                relevance=RankingScore(result_dict["relevance"]),
                ranking_factors=result_dict["ranking_factors"],
                metadata=result_dict["metadata"],
                timestamp=datetime.fromisoformat(result_dict["timestamp"]),
            )
            top_results.append(result)

        return ResearchSummary(
            query=summary_dict["query"],
            top_results=top_results,
            synthesis=summary_dict["synthesis"],
            total_sources=summary_dict["total_sources"],
            successful_sources=summary_dict["successful_sources"],
            failed_sources=summary_dict["failed_sources"],
            execution_time=summary_dict["execution_time"],
            metadata=summary_dict["metadata"],
            timestamp=datetime.fromisoformat(summary_dict["timestamp"]),
        )

    async def get_research_stats(self) -> dict[str, Any]:
        """Get statistics about persisted research."""
        try:
            jsonl_files = list(self.persistence_dir.glob("*.jsonl"))

            total_files = len(jsonl_files)
            total_size = sum(f.stat().st_size for f in jsonl_files)

            # Get recent activity
            recent_files = sorted(
                jsonl_files, key=lambda x: x.stat().st_mtime, reverse=True
            )[:5]
            recent_queries = []

            for filepath in recent_files:
                try:
                    with open(filepath) as f:
                        for line in f:
                            if line.strip():
                                summary_dict = json.loads(line)
                                recent_queries.append(
                                    {
                                        "query": summary_dict["query"],
                                        "timestamp": summary_dict["timestamp"],
                                        "results_count": len(
                                            summary_dict["top_results"]
                                        ),
                                    }
                                )
                                break
                except Exception:
                    continue

            return {
                "total_research_sessions": total_files,
                "total_storage_bytes": total_size,
                "recent_queries": recent_queries,
                "persistence_directory": str(self.persistence_dir),
            }

        except Exception as e:
            logger.error(f"Failed to get research stats: {e}")
            return {"error": str(e)}

    async def cleanup_old_results(self, days_old: int = 30) -> int:
        """Clean up research results older than specified days."""
        try:
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            deleted_count = 0

            for filepath in self.persistence_dir.glob("*.jsonl"):
                if filepath.stat().st_mtime < cutoff_time:
                    filepath.unlink()
                    deleted_count += 1

            logger.info(f"Cleaned up {deleted_count} old research result files")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old results: {e}")
            raise PersistenceError(f"Failed to cleanup old results: {e}")
