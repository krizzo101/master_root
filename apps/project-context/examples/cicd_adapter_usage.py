#!/usr/bin/env python3
"""
CI/CD Adapter Usage Examples

This script demonstrates how to use the comprehensive CI/CD adapter system
for ingesting build, deployment, and pipeline data from multiple platforms.

Features demonstrated:
- Multi-platform CI/CD integration (GitHub, GitLab, Jenkins, Azure DevOps, CircleCI)
- Webhook handling and real-time processing
- Performance metrics calculation
- Environment progression tracking
- Commit correlation and deployment correlation
- Artifact management and quality gates
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List

import yaml

# Import CI/CD adapter components
from src.project_context.ingestion.adapters.cicd_adapter import (
    AzureDevOpsAdapter,
    CICDAdapterConfig,
    CICDPlatform,
    CircleCIAdapter,
    GitHubActionsAdapter,
    GitLabCIAdapter,
    JenkinsAdapter,
    create_cicd_adapter,
)
from src.project_context.ingestion.database import IngestionDatabase
from src.project_context.ingestion.webhook_processor import WebhookProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_github_actions_integration():
    """Demonstrate GitHub Actions integration."""
    print("\\n=== GitHub Actions Integration Demo ===")

    # Configure GitHub Actions adapter
    config = CICDAdapterConfig(
        adapter_id="github_demo",
        source_type="cicd",
        platform=CICDPlatform.GITHUB_ACTIONS,
        # GitHub settings
        base_url="https://api.github.com",
        api_token="your_github_token",  # Use environment variable in production
        webhook_secret="your_webhook_secret",
        # Repository configuration
        repositories=["octocat/Hello-World", "microsoft/vscode"],
        track_branches=["main", "develop"],
        # Performance settings
        calculate_performance_metrics=True,
        track_deployment_environments=True,
        enable_artifact_tracking=True,
        # Correlation settings
        enable_commit_correlation=True,
        temporal_window_hours=2,
        # Sync settings
        historical_sync_enabled=True,
        historical_sync_days=30,
        sync_batch_size=50,
    )

    # Create and start adapter
    adapter = GitHubActionsAdapter(config)
    await adapter.start()

    print(
        f"✓ GitHub Actions adapter started for {len(config.repositories)} repositories"
    )

    # Simulate fetching historical data
    print("Fetching historical workflow runs...")
    item_count = 0
    async for item in adapter.fetch_items(limit=10):
        transformed_item = await adapter.transform_item(item)
        print(f"  • {transformed_item.entity_type}: {transformed_item.title}")
        item_count += 1

    print(f"✓ Processed {item_count} historical items")

    # Cleanup
    await adapter.stop()


async def demo_gitlab_ci_integration():
    """Demonstrate GitLab CI integration."""
    print("\\n=== GitLab CI Integration Demo ===")

    config = CICDAdapterConfig(
        adapter_id="gitlab_demo",
        source_type="cicd",
        platform=CICDPlatform.GITLAB_CI,
        # GitLab settings
        base_url="https://gitlab.com/api/v4",
        api_token="your_gitlab_token",
        webhook_secret="your_webhook_secret",
        # Project configuration (GitLab project IDs)
        projects=["278964", "7764"],  # Example project IDs
        # Performance tracking
        calculate_performance_metrics=True,
        environment_promotion_chains=[["dev", "staging", "production"]],
        failure_rate_threshold=0.15,
        # Sync settings
        historical_sync_days=60,
    )

    adapter = GitLabCIAdapter(config)
    await adapter.start()

    print(f"✓ GitLab CI adapter started for {len(config.projects)} projects")

    # Simulate webhook processing
    sample_pipeline_webhook = {
        "object_attributes": {
            "id": 12345,
            "status": "success",
            "ref": "main",
            "sha": "a1b2c3d4",
            "duration": 120,
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:02:00Z",
            "web_url": "https://gitlab.com/project/-/pipelines/12345",
        },
        "project": {"id": 278964, "name": "awesome-project"},
    }

    context_item = await adapter.process_webhook(
        "Pipeline Hook", sample_pipeline_webhook
    )
    if context_item:
        print(f"✓ Processed webhook: {context_item.title}")
        print(f"  Status: {context_item.metrics['status']}")
        print(f"  Duration: {context_item.metrics.get('duration_ms', 'N/A')}ms")

    await adapter.stop()


async def demo_jenkins_integration():
    """Demonstrate Jenkins integration."""
    print("\\n=== Jenkins Integration Demo ===")

    config = CICDAdapterConfig(
        adapter_id="jenkins_demo",
        source_type="cicd",
        platform=CICDPlatform.JENKINS,
        # Jenkins settings
        base_url="https://jenkins.company.com",
        api_token="username:api_token",
        # Job configuration
        projects=["backend-build", "frontend-build", "deployment-prod"],
        # Performance settings
        calculate_performance_metrics=True,
        performance_degradation_threshold=1.3,  # 30% slower alert
        # Sync settings
        historical_sync_days=30,
    )

    adapter = JenkinsAdapter(config)
    await adapter.start()

    print(f"✓ Jenkins adapter started for {len(config.projects)} jobs")

    # Simulate build webhook
    sample_build_webhook = {
        "job_name": "backend-build",
        "build_number": 42,
        "build_status": "SUCCESS",
        "duration": 180000,  # 3 minutes in milliseconds
        "timestamp": datetime.utcnow().timestamp() * 1000,
        "build_url": "https://jenkins.company.com/job/backend-build/42/",
    }

    context_item = await adapter.process_webhook(
        "build_completed", sample_build_webhook
    )
    if context_item:
        print(f"✓ Processed build: {context_item.title}")
        print(f"  Status: {context_item.metrics['status']}")
        print(f"  Build URL: {context_item.metrics.get('build_url')}")

    await adapter.stop()


async def demo_webhook_processor():
    """Demonstrate the centralized webhook processing system."""
    print("\\n=== Webhook Processor Demo ===")

    # Initialize database (mock for demo)
    database = None  # Would be IngestionDatabase() in real usage

    # Create webhook processor
    processor = WebhookProcessor(
        database=database, num_workers=5, queue_maxsize=1000, max_retries=3
    )

    # Register adapters for different platforms
    github_config = CICDAdapterConfig(
        adapter_id="webhook_github",
        source_type="cicd",
        platform=CICDPlatform.GITHUB_ACTIONS,
        webhook_secret="github_secret",
    )
    processor.register_adapter(
        CICDPlatform.GITHUB_ACTIONS, GitHubActionsAdapter(github_config)
    )

    gitlab_config = CICDAdapterConfig(
        adapter_id="webhook_gitlab",
        source_type="cicd",
        platform=CICDPlatform.GITLAB_CI,
        webhook_secret="gitlab_secret",
    )
    processor.register_adapter(CICDPlatform.GITLAB_CI, GitLabCIAdapter(gitlab_config))

    print("✓ Webhook processor configured with GitHub Actions and GitLab CI adapters")

    # Start processor
    # await processor.start()  # Commented out since we don't have a real database

    # Simulate webhook processing
    sample_github_payload = {
        "workflow_run": {
            "id": 12345,
            "name": "CI",
            "status": "completed",
            "conclusion": "success",
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:05:00Z",
        },
        "repository": {"full_name": "octocat/Hello-World"},
    }

    print("✓ Webhook processor ready for real-time CI/CD event processing")
    # In production: result = await processor.process_webhook(...)


async def demo_performance_correlation():
    """Demonstrate performance metrics and correlation features."""
    print("\\n=== Performance Correlation Demo ===")

    # Sample context items for correlation demonstration
    from src.project_context.models.common import ContextItem

    # Create sample CI/CD items
    build_item = ContextItem(
        source_type="cicd",
        source_id="build-123",
        entity_type="github_workflow_run",
        title="Build: Backend Services",
        timestamp=datetime.utcnow(),
        project_id="company/backend",
        metrics={
            "status": "success",
            "duration_ms": 240000,  # 4 minutes
            "commit_sha": "a1b2c3d4e5f6",
            "build_number": 123,
        },
    )

    deployment_item = ContextItem(
        source_type="cicd",
        source_id="deploy-456",
        entity_type="github_deployment",
        title="Deployment to Production",
        timestamp=datetime.utcnow() + timedelta(minutes=10),
        project_id="company/backend",
        metrics={
            "status": "success",
            "environment": "production",
            "commit_sha": "a1b2c3d4e5f6",  # Same commit
            "deployment_strategy": "blue_green",
        },
    )

    error_item = ContextItem(
        source_type="error",
        source_id="error-789",
        entity_type="application_error",
        title="Database Connection Error",
        content="Connection timeout to database server",
        timestamp=datetime.utcnow() + timedelta(minutes=15),
        project_id="company/backend",
    )

    # Demonstrate correlation detection
    config = CICDAdapterConfig(
        adapter_id="correlation_demo",
        source_type="cicd",
        platform=CICDPlatform.GITHUB_ACTIONS,
        enable_commit_correlation=True,
        enable_temporal_correlation=True,
        temporal_window_hours=1,
    )

    adapter = GitHubActionsAdapter(config)

    # Test commit-based correlation
    context_window = [build_item, error_item]
    relationships = await adapter.detect_relationships(deployment_item, context_window)

    print("✓ Correlation analysis results:")
    for rel_type, target_id, confidence in relationships:
        print(f"  • {rel_type}: {target_id} (confidence: {confidence:.2f})")

    # Test performance metrics calculation
    performance_metrics = await adapter._calculate_performance_metrics(
        build_item, [build_item, deployment_item]  # Mock context window
    )

    print("✓ Performance metrics:")
    for metric, value in performance_metrics.items():
        print(f"  • {metric}: {value}")


async def demo_environment_tracking():
    """Demonstrate deployment environment tracking."""
    print("\\n=== Environment Tracking Demo ===")

    # Create deployment items for different environments
    deployments = [
        {
            "environment": "development",
            "timestamp": datetime.utcnow() - timedelta(hours=24),
            "commit_sha": "abc123",
            "status": "success",
        },
        {
            "environment": "staging",
            "timestamp": datetime.utcnow() - timedelta(hours=12),
            "commit_sha": "abc123",
            "status": "success",
        },
        {
            "environment": "production",
            "timestamp": datetime.utcnow() - timedelta(hours=2),
            "commit_sha": "abc123",
            "status": "success",
        },
    ]

    print("✓ Environment promotion chain detected:")
    for i, deployment in enumerate(deployments):
        print(
            f"  {i+1}. {deployment['environment']} at {deployment['timestamp'].strftime('%H:%M')}"
        )
        if i < len(deployments) - 1:
            print("     ↓ (promotes to)")

    # Calculate deployment frequency
    time_diffs = []
    for i in range(1, len(deployments)):
        diff = (
            deployments[i]["timestamp"] - deployments[i - 1]["timestamp"]
        ).total_seconds() / 3600
        time_diffs.append(diff)

    if time_diffs:
        avg_frequency = sum(time_diffs) / len(time_diffs)
        print(f"✓ Average deployment frequency: {avg_frequency:.1f} hours")


async def demo_configuration_loading():
    """Demonstrate loading configuration from YAML file."""
    print("\\n=== Configuration Loading Demo ===")

    config_path = "config/cicd_integration_config.yaml"

    try:
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)

        print(f"✓ Loaded configuration from {config_path}")

        # Show configured platforms
        cicd_adapters = config_data.get("cicd_adapters", {})
        enabled_platforms = [
            name for name, config in cicd_adapters.items() if config.get("enabled")
        ]

        print(f"✓ Enabled platforms: {', '.join(enabled_platforms)}")

        # Show correlation settings
        correlation = config_data.get("correlation", {})
        print(
            f"✓ Cross-platform correlation: {correlation.get('cross_platform_correlation')}"
        )
        print(f"✓ Temporal window: {correlation.get('temporal_window_hours')} hours")

        # Show performance monitoring
        performance = config_data.get("performance_monitoring", {})
        if performance.get("enabled"):
            metrics = performance.get("metrics", [])
            print(f"✓ Performance metrics: {', '.join(metrics)}")

        # Show webhook settings
        webhook = config_data.get("webhook_processing", {})
        if webhook.get("enabled"):
            print(f"✓ Webhook workers: {webhook.get('num_workers')}")
            print(f"✓ Queue size: {webhook.get('queue_maxsize')}")

    except FileNotFoundError:
        print(f"⚠ Configuration file not found: {config_path}")
        print("  Using default configuration values")


async def demo_artifact_and_quality_tracking():
    """Demonstrate artifact management and quality gate tracking."""
    print("\\n=== Artifact & Quality Tracking Demo ===")

    # Sample raw item with artifact and quality data
    sample_build_with_artifacts = {
        "type": "build",
        "data": {
            "id": 12345,
            "status": "success",
            "artifacts": [
                {
                    "url": "https://artifacts.company.com/backend-v1.2.3.jar",
                    "size": 15728640,  # 15MB
                    "type": "jar",
                },
                {
                    "url": "https://registry.company.com/backend:v1.2.3",
                    "size": 157286400,  # 150MB
                    "type": "docker_image",
                },
            ],
            "test_results": {
                "total": 1250,
                "passed": 1245,
                "failed": 5,
                "coverage": 92.5,
            },
            "quality_gate": {
                "status": "PASSED",
                "coverage": 92.5,
                "code_smells": 3,
                "vulnerabilities": 0,
                "duplicated_lines": 1.2,
            },
        },
    }

    # Create adapter and extract metadata
    config = CICDAdapterConfig(
        adapter_id="artifact_demo",
        source_type="cicd",
        platform=CICDPlatform.GITHUB_ACTIONS,
        enable_artifact_tracking=True,
        enable_quality_gates=True,
    )

    adapter = GitHubActionsAdapter(config)
    artifact_metadata = adapter._extract_artifact_metadata(sample_build_with_artifacts)

    print("✓ Artifact metadata extracted:")
    print(f"  • Artifact count: {artifact_metadata.get('artifact_count')}")
    print(
        f"  • Total artifacts size: {sum(artifact_metadata.get('artifact_sizes', []))} bytes"
    )

    print("✓ Test results:")
    print(
        f"  • Tests passed: {artifact_metadata.get('tests_passed')}/{artifact_metadata.get('tests_total')}"
    )
    print(f"  • Coverage: {artifact_metadata.get('test_coverage')}%")

    print("✓ Quality gate status:")
    print(f"  • Overall: {artifact_metadata.get('quality_gate_status')}")
    print(f"  • Code smells: {artifact_metadata.get('code_smells')}")
    print(f"  • Vulnerabilities: {artifact_metadata.get('vulnerabilities')}")


async def main():
    """Run all CI/CD integration demos."""
    print("🚀 CI/CD Adapter Integration Demo")
    print("=" * 50)

    # Load configuration first
    await demo_configuration_loading()

    # Platform-specific demos
    # await demo_github_actions_integration()  # Commented out - requires API tokens
    # await demo_gitlab_ci_integration()       # Commented out - requires API tokens
    # await demo_jenkins_integration()         # Commented out - requires API tokens

    # Feature demos (don't require API tokens)
    await demo_webhook_processor()
    await demo_performance_correlation()
    await demo_environment_tracking()
    await demo_artifact_and_quality_tracking()

    print("\\n✅ All demos completed successfully!")
    print("\\nNext steps:")
    print("1. Configure API tokens for your CI/CD platforms")
    print("2. Set up webhook endpoints in your CI/CD systems")
    print("3. Start the ingestion pipeline with CI/CD adapters enabled")
    print("4. Monitor the webhook processing dashboard")
    print("5. Explore correlation analysis in the temporal knowledge graph")


if __name__ == "__main__":
    asyncio.run(main())
