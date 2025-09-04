#!/usr/bin/env python3
"""Example usage of the enhanced Git history adapter.

This script demonstrates how to use the comprehensive Git adapter for:
- Incremental commit processing with checkpoint management
- Advanced commit analysis and metadata extraction
- Branch topology mapping and merge detection
- Cross-domain temporal correlation
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the source directory to Python path for local testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from project_context.ingestion.adapters.git_adapter import GitAdapter
from project_context.ingestion.base_adapter import AdapterConfig, BatchMode
from project_context.ingestion.database import DatabaseConnectionPool, IngestionDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Main example execution."""
    logger.info("🚀 Starting Enhanced Git Adapter Usage Example")

    # Configuration for the Git adapter
    config = AdapterConfig(
        adapter_id="example_git_adapter",
        source_type="git",
        batch_mode=BatchMode.BATCH,
        batch_size=100,  # Smaller batch for demo
        generate_embeddings=True,
        generate_summaries=False,
        extract_relationships=True,
        source_config={
            # Repository settings
            "repository_path": ".",  # Current directory
            "include_commits": True,
            "include_branches": True,
            "include_tags": True,
            "include_file_changes": True,
            # Incremental processing
            "enable_incremental": True,
            "checkpoint_interval": 10,  # More frequent checkpoints for demo
            "max_commits_per_batch": 50,
            # Analysis features
            "enable_semantic_analysis": True,
            "enable_impact_scoring": True,
            "enable_relationship_detection": True,
            "enable_branch_detection": True,
            "enable_merge_analysis": True,
            "track_file_impacts": True,
            # Cross-domain correlation
            "correlate_with_chat": True,
            "correlate_with_errors": True,
            "temporal_window_hours": 48,
            # Performance settings
            "parallel_processing": True,
            "max_parallel_workers": 2,
            # Filtering options (for demo, limit to recent commits)
            "max_commit_age_days": 30,  # Last 30 days only
            "exclude_merge_commits": False,
            "include_diff_content": True,
            "max_diff_size_kb": 50,  # Smaller diffs for demo
            "author_filters": [],
            "branch_filters": [],  # Process all branches
        },
    )

    # Initialize database connection (if available)
    db_connection = None
    try:
        # Attempt to connect to database (this would use actual connection string in production)
        # For this demo, we'll skip database integration
        logger.info("⚠️ Database integration skipped for demo (would use actual DB in production)")
    except Exception as e:
        logger.warning(f"Database connection failed: {e}")

    # Initialize the Git adapter
    logger.info("🔧 Initializing Enhanced Git Adapter")
    adapter = GitAdapter(config, db_connection)

    try:
        # Initialize adapter resources
        await adapter.initialize()
        logger.info("✅ Git adapter initialized successfully")

        # Fetch and analyze git items
        logger.info("📊 Fetching and analyzing git items...")

        # Fetch recent commits with analysis
        since_date = datetime.utcnow() - timedelta(days=7)  # Last week

        commit_count = 0
        branch_count = 0
        tag_count = 0

        high_impact_commits = []
        high_risk_commits = []
        interesting_patterns = set()

        async for raw_item in adapter.fetch_items(since=since_date, limit=20):  # Limit for demo
            item_type = raw_item.get("type", "unknown")

            if item_type == "commit":
                commit_count += 1

                # Display commit information
                commit_hash = raw_item.get("hash", "")[:8]
                subject = raw_item.get("subject", "No subject")
                author = raw_item.get("author", "Unknown")
                branch = raw_item.get("branch", "unknown")

                logger.info(f"📝 Commit {commit_hash} by {author} on {branch}: {subject[:60]}...")

                # Show analysis results if available
                analysis = raw_item.get("analysis", {})
                if analysis:
                    commit_type = analysis.get("commit_type", "unknown")
                    impact_score = analysis.get("impact_score", 0.0)
                    risk_score = analysis.get("risk_score", 0.0)
                    semantic_tags = analysis.get("semantic_tags", [])
                    patterns = analysis.get("patterns", [])

                    logger.info(
                        f"   🔍 Analysis: type={commit_type}, impact={impact_score:.2f}, risk={risk_score:.2f}"
                    )
                    if semantic_tags:
                        logger.info(f"   🏷️  Tags: {', '.join(semantic_tags)}")
                    if patterns:
                        logger.info(f"   📈 Patterns: {', '.join(patterns)}")
                        interesting_patterns.update(patterns)

                    # Track high-impact and high-risk commits
                    if impact_score > 0.7:
                        high_impact_commits.append(
                            {"hash": commit_hash, "subject": subject, "impact_score": impact_score}
                        )
                    if risk_score > 0.7:
                        high_risk_commits.append(
                            {"hash": commit_hash, "subject": subject, "risk_score": risk_score}
                        )

                # Show file analysis if available
                file_analysis = raw_item.get("file_analysis", {})
                if file_analysis:
                    total_files = file_analysis.get("total_files", 0)
                    core_files = file_analysis.get("core_files_affected", [])
                    if total_files > 0:
                        logger.info(
                            f"   📁 Files: {total_files} total, {len(core_files)} core files"
                        )

                # Transform to ContextItem for demonstration
                try:
                    context_item = await adapter.transform_item(raw_item)
                    logger.info(f"   ✅ Transformed to ContextItem: {context_item.title}")

                    # Show some metadata
                    if context_item.metrics:
                        files_changed = context_item.metrics.get("files_changed", 0)
                        if files_changed > 0:
                            logger.info(f"   📊 Metadata: {files_changed} files changed")

                except Exception as e:
                    logger.error(f"   ❌ Failed to transform commit: {e}")

            elif item_type == "branch":
                branch_count += 1
                branch_name = raw_item.get("name", "unknown")
                branch_type = raw_item.get("branch_type", "unknown")
                commit_count_branch = raw_item.get("commit_count", 0)
                is_merged = raw_item.get("is_merged", False)

                logger.info(
                    f"🌿 Branch: {branch_name} (type: {branch_type}, commits: {commit_count_branch}, merged: {is_merged})"
                )

            elif item_type == "tag":
                tag_count += 1
                tag_name = raw_item.get("name", "unknown")
                tag_subject = raw_item.get("subject", "")

                logger.info(f"🏷️  Tag: {tag_name} - {tag_subject}")

        # Show summary statistics
        logger.info("\n📈 Analysis Summary:")
        logger.info(
            f"   • Processed {commit_count} commits, {branch_count} branches, {tag_count} tags"
        )
        logger.info(f"   • High-impact commits: {len(high_impact_commits)}")
        logger.info(f"   • High-risk commits: {len(high_risk_commits)}")
        logger.info(f"   • Interesting patterns found: {len(interesting_patterns)}")

        if high_impact_commits:
            logger.info("\n🚨 High-Impact Commits:")
            for commit in high_impact_commits:
                logger.info(
                    f"   • {commit['hash']}: {commit['subject'][:50]}... (impact: {commit['impact_score']:.2f})"
                )

        if high_risk_commits:
            logger.info("\n⚠️ High-Risk Commits:")
            for commit in high_risk_commits:
                logger.info(
                    f"   • {commit['hash']}: {commit['subject'][:50]}... (risk: {commit['risk_score']:.2f})"
                )

        if interesting_patterns:
            logger.info(f"\n🔍 Detected Patterns: {', '.join(sorted(interesting_patterns))}")

        # Demonstrate relationship detection
        logger.info("\n🔗 Testing Relationship Detection...")

        # Create some mock context items for relationship testing
        mock_context = []  # In real usage, this would come from database

        logger.info(
            "   (Relationship detection would work with actual context window from database)"
        )

        logger.info("\n✅ Enhanced Git Adapter demonstration completed successfully!")

    except Exception as e:
        logger.error(f"❌ Error during git processing: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Clean up adapter resources
        logger.info("🧹 Cleaning up adapter resources...")
        try:
            await adapter.cleanup()
            logger.info("✅ Cleanup completed")
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")


async def demonstrate_incremental_processing():
    """Demonstrate incremental processing capabilities."""
    logger.info("\n🔄 Demonstrating Incremental Processing:")

    # This would show how checkpoints work in real usage
    logger.info("   • Checkpoints are saved every N commits (configurable)")
    logger.info("   • On restart, processing resumes from last checkpoint")
    logger.info("   • Branch-specific checkpoints enable parallel processing")
    logger.info("   • Error recovery allows resuming after failures")

    # In real usage:
    # 1. First run processes all commits and saves checkpoints
    # 2. Subsequent runs only process new commits since last checkpoint
    # 3. Database stores checkpoint state persistently
    # 4. Multiple branches can be processed independently


async def demonstrate_analysis_features():
    """Demonstrate advanced analysis features."""
    logger.info("\n🧠 Advanced Analysis Features:")

    # Commit Analysis
    logger.info("   📊 Commit Analysis:")
    logger.info("      • Semantic classification (feature/bugfix/hotfix/etc.)")
    logger.info("      • Impact scoring based on files changed and diff size")
    logger.info("      • Risk assessment for potential issues")
    logger.info("      • Complexity delta calculation")
    logger.info("      • Behavioral pattern detection")

    # Branch Analysis
    logger.info("   🌿 Branch Analysis:")
    logger.info("      • Branch type classification from naming conventions")
    logger.info("      • Topology mapping and base branch detection")
    logger.info("      • Merge detection and conflict analysis")
    logger.info("      • Activity tracking and lifecycle management")

    # Author Analysis
    logger.info("   👤 Author Analysis:")
    logger.info("      • Contribution patterns and behavioral insights")
    logger.info("      • Time-based activity analysis")
    logger.info("      • Collaboration metrics")
    logger.info("      • Code quality trends")

    # Cross-Domain Correlation
    logger.info("   🔗 Cross-Domain Correlation:")
    logger.info("      • Temporal correlation with chat logs")
    logger.info("      • Error causation detection")
    logger.info("      • Code context correlation")
    logger.info("      • Issue tracking integration")


if __name__ == "__main__":
    try:
        # Run the main demonstration
        asyncio.run(main())

        # Show additional feature descriptions
        asyncio.run(demonstrate_incremental_processing())
        asyncio.run(demonstrate_analysis_features())

        print("\n" + "=" * 60)
        print("🎉 Enhanced Git Adapter Example Completed!")
        print("=" * 60)
        print("\nThis adapter provides:")
        print("• ✅ Incremental processing with checkpoints")
        print("• ✅ Advanced commit analysis and classification")
        print("• ✅ Branch topology mapping")
        print("• ✅ Impact and risk scoring")
        print("• ✅ Cross-domain temporal correlation")
        print("• ✅ Performance optimization")
        print("• ✅ Production-ready error handling")
        print("\nReady for Phase 2 deployment! 🚀")

    except KeyboardInterrupt:
        print("\n⚠️ Example interrupted by user")
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
