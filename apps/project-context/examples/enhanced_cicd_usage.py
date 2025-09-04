#!/usr/bin/env python3
"""
Enhanced CI/CD Adapter Usage Example

This example demonstrates how to use the enhanced CI/CD adapter with advanced features
including ML-based failure classification, performance analytics, security analysis,
deployment health monitoring, and cross-platform intelligence.
"""

import asyncio
import os
from datetime import datetime
from typing import List

from src.project_context.ingestion.adapters.cicd_adapter import (
    BuildConstellation,
    CICDAdapterConfig,
    CICDEventType,
    CICDPlatform,
    DeploymentHealth,
    FailureCategory,
    FailureClassification,
    GitHubActionsAdapter,
    PerformanceProfile,
    SecurityAnalysis,
    create_cicd_adapter,
)
from src.project_context.models.common import ContextItem


async def main():
    """Main example demonstrating enhanced CI/CD adapter usage."""

    # Example 1: Basic GitHub Actions setup with advanced features
    await github_actions_example()

    # Example 2: Multi-platform setup with cross-correlation
    await multi_platform_example()

    # Example 3: Webhook processing with intelligence
    await webhook_processing_example()

    # Example 4: Performance analytics and alerting
    await performance_analytics_example()

    # Example 5: Security analysis integration
    await security_analysis_example()


async def github_actions_example():
    """Example of GitHub Actions adapter with advanced features."""
    print("\n=== GitHub Actions Enhanced Example ===")

    # Create enhanced configuration
    config = CICDAdapterConfig(
        platform=CICDPlatform.GITHUB_ACTIONS,
        base_url="https://api.github.com",
        api_token=os.getenv("GITHUB_TOKEN", "your-token-here"),
        webhook_secret=os.getenv("GITHUB_WEBHOOK_SECRET", "your-secret"),
        repositories=["your-org/backend-service", "your-org/frontend-app"],
        # Advanced Intelligence Features
        enable_ml_failure_classification=True,
        enable_performance_profiling=True,
        enable_security_analysis=True,
        enable_deployment_health_monitoring=True,
        enable_cross_platform_correlation=True,
        enable_build_constellation_tracking=True,
        # ML Configuration
        failure_classification_confidence_threshold=0.75,
        # Performance Analytics
        performance_baseline_days=30,
        performance_alert_threshold=2.0,
        # Security Settings
        security_scan_integrations=["snyk", "sonarqube", "github-security"],
        compliance_frameworks=["sox", "pci", "gdpr"],
        security_risk_threshold=0.7,
        # Deployment Health
        health_check_endpoints=["https://api.yourcompany.com/health"],
        canary_monitoring_duration_minutes=30,
        rollback_trigger_error_rate=0.05,
        # Cross-Platform Intelligence
        constellation_correlation_window_hours=2,
        constellation_minimum_correlation_score=0.6,
    )

    # Create the adapter
    adapter = GitHubActionsAdapter(config)

    # Start the adapter (initializes advanced intelligence components)
    await adapter.start()

    print(f"GitHub Actions adapter started with advanced features:")
    print(f"- ML Failure Classification: {bool(adapter.failure_classifier)}")
    print(f"- Performance Analytics: {bool(adapter.performance_analyzer)}")
    print(f"- Security Analysis: {bool(adapter.security_analyzer)}")
    print(f"- Deployment Health: {bool(adapter.deployment_health_monitor)}")
    print(f"- Build Constellations: {bool(adapter.build_constellation_manager)}")

    # Example: Process historical data with intelligence
    count = 0
    async for raw_item in adapter.fetch_items(limit=5):
        item = await adapter.transform_item(raw_item)

        print(f"\nProcessed Item {count + 1}:")
        print(f"- Title: {item.title}")
        print(f"- Type: {item.entity_type}")
        print(
            f"- Intelligence Applied: {item.metrics.get('intelligence_applied', {}).get('features', [])}"
        )

        # Show advanced analytics results
        if "failure_classification" in item.metrics:
            fc = item.metrics["failure_classification"]
            print(
                f"- Failure Category: {fc['primary_category']} (confidence: {fc['confidence']:.2f})"
            )
            print(f"- Suggested Fixes: {fc['suggested_fixes'][:2]}")  # Show first 2 fixes

        if "performance_profile" in item.metrics:
            pp = item.metrics["performance_profile"]
            print(f"- Performance Score: {pp['performance_score']:.1f}/100")
            print(f"- Trend: {pp['trend_direction']}")

        if "security_analysis" in item.metrics:
            sa = item.metrics["security_analysis"]
            print(f"- Security Risk: {sa['risk_score']:.2f}")
            print(f"- Gates Passed: {sa['security_gates_passed']}")

        count += 1
        if count >= 5:
            break

    await adapter.stop()


async def multi_platform_example():
    """Example of multi-platform setup with cross-correlation."""
    print("\n=== Multi-Platform Cross-Correlation Example ===")

    adapters = []

    # GitHub Actions Adapter
    github_config = CICDAdapterConfig(
        platform=CICDPlatform.GITHUB_ACTIONS,
        api_token=os.getenv("GITHUB_TOKEN", "token"),
        repositories=["company/service"],
        enable_cross_platform_correlation=True,
        enable_build_constellation_tracking=True,
    )
    github_adapter = create_cicd_adapter(CICDPlatform.GITHUB_ACTIONS, github_config)
    adapters.append(("GitHub", github_adapter))

    # GitLab CI Adapter
    gitlab_config = CICDAdapterConfig(
        platform=CICDPlatform.GITLAB_CI,
        base_url="https://gitlab.com/api/v4",
        api_token=os.getenv("GITLAB_TOKEN", "token"),
        projects=["12345"],
        enable_cross_platform_correlation=True,
        enable_build_constellation_tracking=True,
    )
    gitlab_adapter = create_cicd_adapter(CICDPlatform.GITLAB_CI, gitlab_config)
    adapters.append(("GitLab", gitlab_adapter))

    # Start all adapters
    for name, adapter in adapters:
        await adapter.start()
        print(f"{name} adapter started")

    # Example: Simulate processing builds from different platforms for the same commit
    commit_sha = "abc123def456"

    # Simulate GitHub Actions build
    github_item = await simulate_build_item("GitHub Actions", commit_sha, "success", 45000)
    github_result = await github_adapter.transform_item(github_item)

    # Simulate GitLab CI build for same commit
    gitlab_item = await simulate_build_item("GitLab CI", commit_sha, "success", 52000)
    gitlab_result = await gitlab_adapter.transform_item(gitlab_item)

    print(f"\nCross-Platform Build Constellation:")

    # Check build constellation information
    github_constellation = github_result.metrics.get("build_constellation", {})
    gitlab_constellation = gitlab_result.metrics.get("build_constellation", {})

    if github_constellation:
        print(f"- GitHub Build Constellation ID: {github_constellation.get('constellation_id')}")
        print(f"- Total Builds: {github_constellation.get('total_builds')}")
        print(f"- Status: {github_constellation.get('completion_status')}")

    if gitlab_constellation:
        print(f"- GitLab Build Constellation ID: {gitlab_constellation.get('constellation_id')}")
        print(f"- Correlation Strength: {gitlab_constellation.get('correlation_strength', 0):.2f}")

    # Stop all adapters
    for name, adapter in adapters:
        await adapter.stop()


async def webhook_processing_example():
    """Example of webhook processing with advanced intelligence."""
    print("\n=== Webhook Processing with Intelligence Example ===")

    config = CICDAdapterConfig(
        platform=CICDPlatform.GITHUB_ACTIONS,
        api_token=os.getenv("GITHUB_TOKEN", "token"),
        webhook_secret="test-secret",
        enable_ml_failure_classification=True,
        enable_performance_profiling=True,
        enable_real_time_alerts=True,
        webhook_processing_timeout_ms=3000,
    )

    adapter = GitHubActionsAdapter(config)
    await adapter.start()

    # Simulate webhook payloads
    webhooks = [
        {
            "event_type": "workflow_run",
            "payload": create_sample_workflow_payload("success", 60000),
        },
        {
            "event_type": "workflow_run",
            "payload": create_sample_workflow_payload("failure", 35000, has_errors=True),
        },
        {
            "event_type": "deployment",
            "payload": create_sample_deployment_payload("success", "production"),
        },
    ]

    print("Processing webhook events...")

    for i, webhook in enumerate(webhooks):
        start_time = datetime.now()

        # Process webhook
        context_item = await adapter.process_webhook(webhook["event_type"], webhook["payload"])

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        if context_item:
            print(f"\nWebhook {i+1} processed in {processing_time:.1f}ms:")
            print(f"- Event: {webhook['event_type']}")
            print(f"- Status: {context_item.metrics.get('status')}")
            print(
                f"- Intelligence Features: {len(context_item.metrics.get('intelligence_applied', {}).get('features', []))}"
            )

            # Show real-time metrics
            real_time_metrics = adapter.real_time_metrics
            print(
                f"- Average Processing Time: {real_time_metrics.get('average_processing_time', 0):.1f}ms"
            )

    await adapter.stop()


async def performance_analytics_example():
    """Example of performance analytics and alerting."""
    print("\n=== Performance Analytics Example ===")

    config = CICDAdapterConfig(
        platform=CICDPlatform.GITHUB_ACTIONS,
        enable_performance_profiling=True,
        performance_baseline_days=30,
        performance_alert_threshold=2.0,
        resource_efficiency_threshold=0.6,
    )

    adapter = GitHubActionsAdapter(config)
    await adapter.start()

    # Simulate builds with varying performance
    builds = [
        {"duration": 45000, "status": "success", "job": "backend-tests"},
        {"duration": 95000, "status": "success", "job": "backend-tests"},  # Slower
        {"duration": 180000, "status": "failure", "job": "backend-tests"},  # Much slower + failed
        {"duration": 40000, "status": "success", "job": "backend-tests"},  # Back to normal
    ]

    print("Analyzing build performance trends:")

    for i, build_data in enumerate(builds):
        # Create build item
        raw_item = await simulate_build_item(
            "GitHub Actions",
            f"commit-{i}",
            build_data["status"],
            build_data["duration"],
            job_name=build_data["job"],
        )

        # Process with performance analytics
        item = await adapter.transform_item(raw_item)

        # Extract performance profile
        perf_profile = item.metrics.get("performance_profile")
        if perf_profile:
            print(f"\nBuild {i+1} ({build_data['duration']/1000:.1f}s):")
            print(f"- Performance Score: {perf_profile['performance_score']:.1f}/100")
            print(f"- Trend: {perf_profile['trend_direction']}")
            print(f"- Resource Efficiency: {perf_profile['resource_efficiency']:.1%}")

            if perf_profile["bottleneck_stages"]:
                print(f"- Bottlenecks: {', '.join(perf_profile['bottleneck_stages'])}")

            # Alert conditions
            if perf_profile["performance_score"] < 50:
                print("  ⚠️  ALERT: Performance degradation detected!")

    await adapter.stop()


async def security_analysis_example():
    """Example of security analysis integration."""
    print("\n=== Security Analysis Example ===")

    config = CICDAdapterConfig(
        platform=CICDPlatform.GITHUB_ACTIONS,
        enable_security_analysis=True,
        security_scan_integrations=["snyk", "sonarqube", "github-security"],
        compliance_frameworks=["sox", "pci"],
        security_risk_threshold=0.7,
    )

    adapter = GitHubActionsAdapter(config)
    await adapter.start()

    # Simulate security-related builds
    security_builds = [
        {
            "title": "Security scan passed",
            "status": "success",
            "content": "All security scans passed successfully",
            "has_security_context": True,
        },
        {
            "title": "Vulnerability scan failed",
            "status": "failure",
            "content": "Critical vulnerability found in dependency. Snyk scan failed with 3 high-severity issues.",
            "has_security_context": True,
        },
        {
            "title": "Regular build",
            "status": "success",
            "content": "Normal build without security context",
            "has_security_context": False,
        },
    ]

    print("Processing builds with security analysis:")

    for i, build_info in enumerate(security_builds):
        # Create security-relevant item
        raw_item = {
            "type": "workflow_run",
            "data": {
                "id": f"build-{i}",
                "name": build_info["title"],
                "status": build_info["status"],
                "conclusion": build_info["status"],
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:30:00Z",
                "html_url": f"https://github.com/owner/repo/actions/runs/{i}",
                "head_sha": f"sha-{i}",
                "head_branch": "main",
            },
            "repository": "owner/repo",
        }

        # Override content for security testing
        item = await adapter.transform_item(raw_item)
        item.content = build_info["content"]
        item.title = build_info["title"]

        # Re-apply analysis with updated content
        await adapter._apply_advanced_analysis(item, raw_item)

        print(f"\nBuild {i+1}: {build_info['title']}")
        print(f"- Has Security Context: {build_info['has_security_context']}")

        # Show security analysis results
        security_analysis = item.metrics.get("security_analysis")
        if security_analysis:
            print(f"- Security Risk Score: {security_analysis['risk_score']:.2f}")
            print(f"- Security Gates Passed: {security_analysis['security_gates_passed']}")
            print(f"- Requires Approval: {security_analysis['requires_approval']}")
            print(f"- Vulnerability Count: {security_analysis['vulnerability_count']}")

            if security_analysis["compliance_violations"]:
                print(
                    f"- Compliance Violations: {', '.join(security_analysis['compliance_violations'])}"
                )

            if security_analysis["security_recommendations"]:
                print(f"- Recommendations: {security_analysis['security_recommendations'][0]}")

            # Alert for high risk
            if security_analysis["risk_score"] >= 0.7:
                print("  🚨 SECURITY ALERT: High risk deployment blocked!")
        else:
            print("- No security analysis performed (no security context)")

    await adapter.stop()


# Utility Functions


async def simulate_build_item(
    platform: str, commit_sha: str, status: str, duration_ms: int, job_name: str = "build"
) -> dict:
    """Create a simulated build item for testing."""
    return {
        "type": "workflow_run" if platform == "GitHub Actions" else "pipeline",
        "data": {
            "id": f"{platform.lower().replace(' ', '-')}-{commit_sha[:8]}",
            "name": f"{job_name}",
            "status": status,
            "conclusion": status,
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:30:00Z",
            "duration": duration_ms // 1000,  # Some platforms use seconds
            "head_sha": commit_sha,
            "head_branch": "main",
        },
        "repository": "company/service" if platform == "GitHub Actions" else None,
        "project_id": "12345" if platform == "GitLab CI" else None,
    }


def create_sample_workflow_payload(status: str, duration_ms: int, has_errors: bool = False) -> dict:
    """Create a sample GitHub Actions workflow payload."""
    payload = {
        "action": "completed",
        "workflow_run": {
            "id": 12345,
            "name": "CI Pipeline",
            "status": "completed",
            "conclusion": status,
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:30:00Z",
            "head_sha": "abc123def456",
            "head_branch": "main",
            "html_url": "https://github.com/owner/repo/actions/runs/12345",
            "actor": {"login": "developer"},
            "run_number": 42,
            "run_attempt": 1,
        },
        "repository": {
            "full_name": "owner/repo",
            "html_url": "https://github.com/owner/repo",
        },
    }

    if has_errors:
        payload["workflow_run"][
            "logs_url"
        ] = "https://api.github.com/repos/owner/repo/actions/runs/12345/logs"
        # Would typically include error logs or failure details

    return payload


def create_sample_deployment_payload(status: str, environment: str) -> dict:
    """Create a sample deployment payload."""
    return {
        "action": "created",
        "deployment": {
            "id": 67890,
            "environment": environment,
            "ref": "main",
            "sha": "abc123def456",
            "created_at": "2024-01-01T12:00:00Z",
            "creator": {"login": "developer"},
            "task": "deploy",
            "auto_merge": False,
            "production_environment": environment == "production",
        },
        "repository": {
            "full_name": "owner/repo",
        },
    }


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
