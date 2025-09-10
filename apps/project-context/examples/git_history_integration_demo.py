#!/usr/bin/env python3
"""
Git History Integration Demo for Unified Context System Phase 2

This script demonstrates how to integrate Git history analysis with the
existing chat and code adapters to build temporal knowledge relationships.

Usage:
    python git_history_integration_demo.py [--repo-path PATH] [--days DAYS]
"""

import asyncio
import json

# Add the src directory to path
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from project_context.ingestion.adapters.chat_adapter import ChatAdapter
from project_context.ingestion.adapters.git_adapter import GitAdapter
from project_context.ingestion.base_adapter import AdapterConfig, BatchMode
from project_context.ingestion.database import DatabaseConnectionPool, IngestionDatabase
from project_context.models.common import ContextItem, ContextRelationship


class GitHistoryIntegrationDemo:
    """Demonstration of Git history integration with temporal correlation."""

    def __init__(self, repo_path: str = ".", database_url: str = None):
        self.repo_path = repo_path
        self.database_url = (
            database_url
            or "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context"
        )

        # Initialize database connection
        self.db_pool = DatabaseConnectionPool(self.database_url)
        self.db = IngestionDatabase(self.db_pool)

        # Configure adapters
        self.git_adapter = self._create_git_adapter()
        self.results = {
            "commits_processed": 0,
            "relationships_found": 0,
            "temporal_correlations": 0,
            "performance_metrics": {},
        }

    def _create_git_adapter(self) -> GitAdapter:
        """Create and configure Git adapter for demo."""
        config = AdapterConfig(
            adapter_id="demo_git",
            source_type="git",
            batch_mode=BatchMode.BATCH,
            batch_size=50,  # Small batches for demo
            generate_embeddings=False,  # Skip embeddings for demo speed
            generate_summaries=False,
            extract_relationships=True,
            source_config={
                "repository_path": self.repo_path,
                "enable_incremental": True,
                "checkpoint_interval": 25,
                "max_commits_per_batch": 100,
                "enable_semantic_analysis": True,
                "enable_impact_scoring": True,
                "enable_relationship_detection": True,
                "enable_branch_detection": True,
                "correlate_with_chat": True,
                "correlate_with_errors": True,
                "temporal_window_hours": 24,  # Look for correlations within 24 hours
                "include_commits": True,
                "include_branches": True,
                "include_file_changes": True,
                "max_commit_age_days": 30,  # Only last 30 days for demo
                "include_diff_content": True,
                "max_diff_size_kb": 50,  # Smaller diffs for demo
            },
        )

        return GitAdapter(config, self.db_pool)

    async def run_demo(self, days_back: int = 7):
        """Run the complete Git history integration demonstration."""
        print("🚀 Starting Git History Integration Demo")
        print(f"Repository: {self.repo_path}")
        print(f"Looking back: {days_back} days")
        print("-" * 60)

        try:
            # Initialize database connection
            await self.db_pool.initialize()
            print("✅ Database connection established")

            # Initialize Git adapter
            await self.git_adapter.initialize()
            print("✅ Git adapter initialized")

            # Phase 1: Extract and analyze Git commits
            print("\n📊 Phase 1: Extracting Git History...")
            commits = await self._extract_git_commits(days_back)
            print(f"   Found {len(commits)} commits to process")

            # Phase 2: Store commits in database
            print("\n💾 Phase 2: Storing Git Data...")
            await self._store_commits(commits)
            print(f"   Stored {len(commits)} commits")

            # Phase 3: Detect relationships
            print("\n🔗 Phase 3: Detecting Relationships...")
            relationships = await self._detect_relationships(commits)
            print(f"   Found {len(relationships)} relationships")

            # Phase 4: Demonstrate temporal correlations
            print("\n⏰ Phase 4: Temporal Correlation Analysis...")
            correlations = await self._analyze_temporal_correlations()
            print(f"   Found {len(correlations)} temporal correlations")

            # Phase 5: Generate insights
            print("\n🧠 Phase 5: Generating Insights...")
            insights = await self._generate_insights(commits, relationships, correlations)

            # Display results
            await self._display_results(insights)

        except Exception as e:
            print(f"❌ Demo failed: {e}")
            raise
        finally:
            # Cleanup
            await self.git_adapter.cleanup()
            await self.db_pool.close()
            print("\n✅ Demo completed and cleaned up")

    async def _extract_git_commits(self, days_back: int) -> List[ContextItem]:
        """Extract Git commits from the last N days."""
        since = datetime.now() - timedelta(days=days_back)

        commits = []
        async for raw_commit in self.git_adapter.fetch_items(since=since, limit=50):
            try:
                context_item = await self.git_adapter.transform_item(raw_commit)
                commits.append(context_item)

                if len(commits) % 10 == 0:
                    print(f"   Processed {len(commits)} commits...")

            except Exception as e:
                print(f"   ⚠️  Failed to process commit: {e}")
                continue

        self.results["commits_processed"] = len(commits)
        return commits

    async def _store_commits(self, commits: List[ContextItem]) -> None:
        """Store commits in the database."""
        result = await self.db.store_context_items(commits, batch_size=20)

        print(f"   Processing results:")
        print(f"     - Processed: {result.processed_items}")
        print(f"     - Failed: {result.failed_items}")
        print(f"     - Duplicates: {result.duplicate_items}")
        print(f"     - Processing time: {result.processing_time_seconds:.2f}s")

        if result.errors:
            print(f"   ⚠️  {len(result.errors)} errors occurred")

    async def _detect_relationships(self, commits: List[ContextItem]) -> List[ContextRelationship]:
        """Detect relationships between commits."""
        relationships = []

        print("   Analyzing commit relationships...")

        for i, commit in enumerate(commits):
            # Use sliding window for relationship detection
            window_start = max(0, i - 10)
            context_window = commits[window_start:i] + commits[i + 1 : min(len(commits), i + 11)]

            try:
                commit_relationships = await self.git_adapter.detect_relationships(
                    commit, context_window
                )

                for rel_type, target_id, confidence in commit_relationships:
                    relationship = ContextRelationship(
                        source_id=commit.id,
                        target_id=target_id,
                        relationship_type=rel_type,
                        confidence=confidence,
                        created_by="git_demo",
                    )
                    relationships.append(relationship)

            except Exception as e:
                print(
                    f"   ⚠️  Failed to detect relationships for commit {commit.source_id[:8]}: {e}"
                )

        print(f"   Relationship breakdown:")
        rel_types = {}
        for rel in relationships:
            rel_types[rel.relationship_type] = rel_types.get(rel.relationship_type, 0) + 1

        for rel_type, count in sorted(rel_types.items()):
            print(f"     - {rel_type}: {count}")

        self.results["relationships_found"] = len(relationships)
        return relationships

    async def _analyze_temporal_correlations(self) -> List[Dict[str, Any]]:
        """Analyze temporal correlations with other context types."""
        correlations = []

        # This would typically query the database for chat, error, and other context
        # For demo purposes, we'll simulate some temporal correlations

        print("   Simulating temporal correlation analysis...")
        print("   (In production, this would query chat/error/code context)")

        # Simulate finding correlations
        sample_correlations = [
            {
                "type": "commit_chat_correlation",
                "commit_sha": "abc123",
                "chat_session": "session_456",
                "time_difference_minutes": 15,
                "correlation_strength": 0.8,
                "description": "Commit followed discussion about bug fix",
            },
            {
                "type": "commit_error_correlation",
                "commit_sha": "def456",
                "error_id": "error_789",
                "time_difference_minutes": 30,
                "correlation_strength": 0.6,
                "description": "Error occurred after deployment commit",
            },
            {
                "type": "commit_sequence_pattern",
                "commits": ["abc123", "def456", "ghi789"],
                "pattern": "feature_development_sequence",
                "correlation_strength": 0.7,
                "description": "Sequential commits showing feature development",
            },
        ]

        correlations.extend(sample_correlations)

        self.results["temporal_correlations"] = len(correlations)
        return correlations

    async def _generate_insights(
        self,
        commits: List[ContextItem],
        relationships: List[ContextRelationship],
        correlations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate insights from the analyzed Git history."""

        insights = {
            "summary": {
                "total_commits": len(commits),
                "total_relationships": len(relationships),
                "temporal_correlations": len(correlations),
                "time_span_days": 0,
                "active_authors": set(),
                "branches_involved": set(),
                "files_impacted": set(),
            },
            "commit_analysis": {
                "by_type": {},
                "by_impact": {"high": 0, "medium": 0, "low": 0},
                "by_risk": {"high": 0, "medium": 0, "low": 0},
                "by_author": {},
                "by_time_of_day": {str(h): 0 for h in range(24)},
            },
            "relationship_patterns": {
                "most_common_relationships": {},
                "relationship_strength_distribution": {"high": 0, "medium": 0, "low": 0},
                "cross_domain_correlations": {},
            },
            "temporal_patterns": {
                "commit_frequency_by_day": {},
                "author_activity_patterns": {},
                "development_hotspots": [],
            },
        }

        # Analyze commits
        if commits:
            timestamps = [c.timestamp for c in commits if c.timestamp]
            if timestamps:
                time_span = (max(timestamps) - min(timestamps)).days
                insights["summary"]["time_span_days"] = time_span

        for commit in commits:
            # Author analysis
            if commit.actor_id:
                insights["summary"]["active_authors"].add(commit.actor_id)
                insights["commit_analysis"]["by_author"][commit.actor_id] = (
                    insights["commit_analysis"]["by_author"].get(commit.actor_id, 0) + 1
                )

            # Branch analysis
            if commit.metrics and "branch_name" in commit.metrics:
                insights["summary"]["branches_involved"].add(commit.metrics["branch_name"])

            # File impact analysis
            if commit.metrics and "changed_files" in commit.metrics:
                files = commit.metrics["changed_files"]
                insights["summary"]["files_impacted"].update(files)

            # Commit type analysis
            if commit.metrics and "commit_type" in commit.metrics:
                commit_type = commit.metrics["commit_type"]
                insights["commit_analysis"]["by_type"][commit_type] = (
                    insights["commit_analysis"]["by_type"].get(commit_type, 0) + 1
                )

            # Impact and risk scoring
            if commit.metrics:
                impact_score = commit.metrics.get("impact_score", 0.0)
                risk_score = commit.metrics.get("risk_score", 0.0)

                impact_level = (
                    "high" if impact_score > 0.7 else "medium" if impact_score > 0.4 else "low"
                )
                risk_level = "high" if risk_score > 0.7 else "medium" if risk_score > 0.4 else "low"

                insights["commit_analysis"]["by_impact"][impact_level] += 1
                insights["commit_analysis"]["by_risk"][risk_level] += 1

            # Time of day analysis
            if commit.timestamp:
                hour = str(commit.timestamp.hour)
                insights["commit_analysis"]["by_time_of_day"][hour] += 1

        # Analyze relationships
        for rel in relationships:
            rel_type = rel.relationship_type
            insights["relationship_patterns"]["most_common_relationships"][rel_type] = (
                insights["relationship_patterns"]["most_common_relationships"].get(rel_type, 0) + 1
            )

            # Relationship strength analysis
            strength_level = (
                "high" if rel.confidence > 0.7 else "medium" if rel.confidence > 0.4 else "low"
            )
            insights["relationship_patterns"]["relationship_strength_distribution"][
                strength_level
            ] += 1

        # Convert sets to counts for JSON serialization
        insights["summary"]["active_authors"] = len(insights["summary"]["active_authors"])
        insights["summary"]["branches_involved"] = len(insights["summary"]["branches_involved"])
        insights["summary"]["files_impacted"] = len(insights["summary"]["files_impacted"])

        return insights

    async def _display_results(self, insights: Dict[str, Any]) -> None:
        """Display comprehensive analysis results."""

        print("\n" + "=" * 80)
        print("🎯 GIT HISTORY ANALYSIS RESULTS")
        print("=" * 80)

        # Summary
        summary = insights["summary"]
        print(f"\n📈 SUMMARY:")
        print(f"   • Total commits analyzed: {summary['total_commits']}")
        print(f"   • Relationships detected: {summary['total_relationships']}")
        print(f"   • Temporal correlations: {summary['temporal_correlations']}")
        print(f"   • Time span: {summary['time_span_days']} days")
        print(f"   • Active authors: {summary['active_authors']}")
        print(f"   • Branches involved: {summary['branches_involved']}")
        print(f"   • Files impacted: {summary['files_impacted']}")

        # Commit Analysis
        commit_analysis = insights["commit_analysis"]
        print(f"\n💻 COMMIT ANALYSIS:")

        if commit_analysis["by_type"]:
            print("   Commit types:")
            for commit_type, count in sorted(
                commit_analysis["by_type"].items(), key=lambda x: x[1], reverse=True
            ):
                print(f"     - {commit_type}: {count}")

        print("   Impact distribution:")
        for level, count in commit_analysis["by_impact"].items():
            print(f"     - {level}: {count}")

        print("   Risk distribution:")
        for level, count in commit_analysis["by_risk"].items():
            print(f"     - {level}: {count}")

        if commit_analysis["by_author"]:
            print("   Top authors:")
            top_authors = sorted(
                commit_analysis["by_author"].items(), key=lambda x: x[1], reverse=True
            )[:5]
            for author, count in top_authors:
                print(f"     - {author}: {count} commits")

        # Activity patterns
        activity_hours = [
            (int(h), c) for h, c in commit_analysis["by_time_of_day"].items() if c > 0
        ]
        if activity_hours:
            activity_hours.sort(key=lambda x: x[1], reverse=True)
            print("   Most active hours:")
            for hour, count in activity_hours[:5]:
                time_label = f"{hour:02d}:00-{hour+1:02d}:00"
                print(f"     - {time_label}: {count} commits")

        # Relationship Patterns
        relationships = insights["relationship_patterns"]
        print(f"\n🔗 RELATIONSHIP PATTERNS:")

        if relationships["most_common_relationships"]:
            print("   Most common relationship types:")
            top_relationships = sorted(
                relationships["most_common_relationships"].items(), key=lambda x: x[1], reverse=True
            )[:5]
            for rel_type, count in top_relationships:
                print(f"     - {rel_type}: {count}")

        print("   Relationship strength distribution:")
        for level, count in relationships["relationship_strength_distribution"].items():
            print(f"     - {level}: {count}")

        # Performance metrics
        print(f"\n⚡ PERFORMANCE METRICS:")
        print(f"   • Commits processed: {self.results['commits_processed']}")
        print(f"   • Relationships found: {self.results['relationships_found']}")
        print(f"   • Temporal correlations: {self.results['temporal_correlations']}")

        # Save detailed results
        results_file = Path(__file__).parent / "git_analysis_results.json"
        with open(results_file, "w") as f:
            json.dump(
                {
                    "insights": insights,
                    "performance": self.results,
                    "timestamp": datetime.now().isoformat(),
                    "repository": self.repo_path,
                },
                f,
                indent=2,
                default=str,
            )

        print(f"\n💾 Detailed results saved to: {results_file}")

        print("\n" + "=" * 80)
        print("✅ ANALYSIS COMPLETE")
        print("=" * 80)


async def main():
    """Main entry point for the demo."""
    import argparse

    parser = argparse.ArgumentParser(description="Git History Integration Demo")
    parser.add_argument("--repo-path", default=".", help="Path to Git repository")
    parser.add_argument("--days", type=int, default=7, help="Days back to analyze")
    parser.add_argument("--database-url", help="Database connection URL")

    args = parser.parse_args()

    demo = GitHistoryIntegrationDemo(repo_path=args.repo_path, database_url=args.database_url)

    try:
        await demo.run_demo(days_back=args.days)
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
