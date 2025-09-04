# CI/CD Adapter Implementation

## Overview

The CI/CD Adapter system provides comprehensive integration with multiple CI/CD platforms, enabling real-time ingestion of build, deployment, and pipeline data into the Unified Context System. The system supports webhook handling, performance correlation, environment tracking, and artifact management.

## Architecture

### Core Components

1. **BaseCICDAdapter**: Abstract base class providing common functionality
2. **Platform-Specific Adapters**: Concrete implementations for each CI/CD platform
3. **WebhookProcessor**: Centralized webhook processing system
4. **CICDAdapterConfig**: Configuration management
5. **Correlation Engine**: Advanced relationship detection

### Supported Platforms

| Platform | Status | API Support | Webhook Support | Key Features |
|----------|--------|-------------|-----------------|--------------|
| GitHub Actions | ✅ Complete | ✅ REST API v3 | ✅ Webhooks | Workflows, Jobs, Deployments, Check Runs |
| GitLab CI | ✅ Complete | ✅ REST API v4 | ✅ Webhooks | Pipelines, Jobs, Deployments |
| Jenkins | ✅ Complete | ✅ REST API | ✅ Notifications | Builds, Jobs, Deployments |
| Azure DevOps | ✅ Complete | ✅ REST API 7.0 | ✅ Service Hooks | Builds, Releases, Deployments |
| CircleCI | ✅ Complete | ✅ REST API v2 | ✅ Webhooks | Pipelines, Workflows, Jobs |

## Implementation Details

### 1. Base Adapter Structure

```python
class BaseCICDAdapter(BaseAdapter):
    \"\"\"Base class for CI/CD platform adapters.\"\"\"

    async def fetch_historical_data(self, limit: Optional[int] = None) -> AsyncIterator[Dict[str, Any]]:
        \"\"\"Fetch historical CI/CD data from platform API.\"\"\"
        pass

    async def fetch_real_time_updates(self, limit: Optional[int] = None) -> AsyncIterator[Dict[str, Any]]:
        \"\"\"Handle real-time updates via webhooks.\"\"\"
        pass

    async def process_webhook(self, event_type: str, payload: dict) -> Optional[ContextItem]:
        \"\"\"Process incoming webhook payload.\"\"\"
        pass

    def validate_webhook_signature(self, payload: bytes, signature: str) -> bool:
        \"\"\"Validate webhook signature for security.\"\"\"
        pass
```

### 2. Platform-Specific Implementations

#### GitHub Actions Adapter

**Key Features:**
- Workflow run tracking with job-level granularity
- Deployment status monitoring
- Check run integration
- Artifact tracking
- HMAC-SHA256 signature validation

**Supported Events:**
- `workflow_run`: Complete workflow execution
- `workflow_job`: Individual job execution
- `deployment`: Deployment events
- `deployment_status`: Deployment status updates
- `check_run`: Check run completion

**API Endpoints:**
- `/repos/{owner}/{repo}/actions/runs` - Workflow runs
- `/repos/{owner}/{repo}/actions/runs/{run_id}/jobs` - Job details

#### GitLab CI Adapter

**Key Features:**
- Pipeline and job tracking
- Multi-project support
- Deployment environment tracking
- Token-based webhook authentication

**Supported Events:**
- `Pipeline Hook`: Pipeline state changes
- `Job Hook`: Job state changes
- `Deployment Hook`: Deployment events

**API Endpoints:**
- `/projects/{id}/pipelines` - Pipeline data
- `/projects/{id}/pipelines/{pipeline_id}/jobs` - Job data

#### Jenkins Adapter

**Key Features:**
- Build and job tracking
- Changeset correlation
- Flexible webhook payload handling
- Basic authentication support

**Event Types:**
- `build_started`: Build initiation
- `build_completed`: Build completion
- `deployment_completed`: Deployment events

**API Endpoints:**
- `/job/{job_name}/api/json` - Job and build data

#### Azure DevOps Adapter

**Key Features:**
- Build and release tracking
- Organization/project structure support
- Personal Access Token (PAT) authentication
- Service hook integration

**Supported Events:**
- `build.complete`: Build completion
- `ms.vss-release.deployment-completed-event`: Deployment completion

**API Endpoints:**
- `/{organization}/{project}/_apis/build/builds` - Build data
- `/{organization}/{project}/_apis/release/deployments` - Deployment data

#### CircleCI Adapter

**Key Features:**
- Pipeline and workflow tracking
- Project slug-based identification
- API token authentication
- Webhook signature validation

**Supported Events:**
- `workflow-completed`: Workflow completion
- `job-completed`: Job completion

**API Endpoints:**
- `/project/{project-slug}/pipeline` - Pipeline data

### 3. Correlation Engine

The correlation engine provides advanced relationship detection between CI/CD events and other context items.

#### Correlation Types

1. **Commit-based Correlation**
   - Links builds/deployments to specific Git commits
   - High confidence (1.0) for exact SHA matches
   - Supports abbreviated SHA matching

2. **Temporal Correlation**
   - Links events based on time proximity
   - Configurable time window (default: 2 hours)
   - Confidence decreases with time distance

3. **CI/CD Chain Correlation**
   - Links related CI/CD events (build → deploy → etc.)
   - Environment progression tracking
   - Pipeline/job containment relationships

4. **Error Correlation**
   - Links failed builds with error logs
   - Keyword-based correlation
   - Temporal proximity weighting

#### Performance Metrics

The system calculates comprehensive performance metrics:

- **Success Rate**: Percentage of successful builds/deployments
- **Average Duration**: Mean execution time with percentiles
- **Performance Comparison**: Current vs. historical performance
- **Deployment Frequency**: Time between deployments
- **Environment Progression**: Promotion chain analysis

### 4. Webhook Processing

The centralized webhook processor handles real-time events from all platforms.

#### Features

- **Multi-worker Architecture**: Configurable worker pool for parallel processing
- **Rate Limiting**: Per-IP rate limiting to prevent abuse
- **Signature Validation**: Platform-specific signature verification
- **Retry Logic**: Automatic retry with exponential backoff
- **Queue Management**: Bounded queues with overflow handling
- **Monitoring**: Comprehensive metrics and health checks

#### Processing Flow

```
Webhook Request → Rate Limiting → Signature Validation → Queue → Worker Pool → Database Storage
```

### 5. Configuration Management

#### Adapter Configuration

```yaml
cicd_adapters:
  github_actions:
    enabled: true
    platform: github_actions
    api_token: "${GITHUB_API_TOKEN}"
    webhook_secret: "${GITHUB_WEBHOOK_SECRET}"
    repositories:
      - "owner/repo1"
      - "owner/repo2"
    calculate_performance_metrics: true
    enable_commit_correlation: true
    temporal_window_hours: 2
```

#### Key Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `platform` | CI/CD platform type | Required |
| `api_token` | Authentication token | Required |
| `webhook_secret` | Webhook validation secret | Optional |
| `repositories/projects` | Repository/project list | Required |
| `historical_sync_days` | Days of historical data | 90 |
| `calculate_performance_metrics` | Enable performance analysis | true |
| `enable_commit_correlation` | Enable commit-based correlation | true |
| `temporal_window_hours` | Correlation time window | 2 |
| `failure_rate_threshold` | Alert threshold for failures | 0.2 (20%) |

## Data Model

### ContextItem Structure

CI/CD items are stored as `ContextItem` objects with standardized fields:

```python
ContextItem(
    source_type="cicd",
    source_id="platform-specific-id",
    entity_type="platform_item_type",  # e.g., "github_workflow_run"
    title="Human-readable title",
    content="Descriptive content",
    timestamp=event_timestamp,
    timestamp_end=completion_timestamp,  # For duration events
    project_id="repository/project",
    actor_id="user_or_system",
    actor_type="human|system",
    metrics={
        "status": "success|failure|running",
        "duration_ms": execution_time,
        "commit_sha": "git_commit_sha",
        "environment": "deployment_environment",
        # Platform-specific metrics
    },
    source_data=original_payload  # Raw platform data
)
```

### Entity Types

| Entity Type | Description | Platforms |
|-------------|-------------|-----------|
| `github_workflow_run` | GitHub Actions workflow execution | GitHub |
| `github_workflow_job` | Individual job in workflow | GitHub |
| `github_deployment` | Deployment event | GitHub |
| `github_check_run` | Check run completion | GitHub |
| `gitlab_pipeline` | GitLab CI pipeline | GitLab |
| `gitlab_job` | GitLab CI job | GitLab |
| `gitlab_deployment` | GitLab deployment | GitLab |
| `jenkins_build` | Jenkins build | Jenkins |
| `jenkins_deployment` | Jenkins deployment | Jenkins |
| `azure_build` | Azure DevOps build | Azure |
| `azure_deployment` | Azure DevOps deployment | Azure |
| `circleci_pipeline` | CircleCI pipeline | CircleCI |
| `circleci_workflow` | CircleCI workflow | CircleCI |
| `circleci_job` | CircleCI job | CircleCI |

## Advanced Features

### 1. Artifact Management

Tracks build artifacts and deployment packages:

```python
artifact_metadata = {
    "artifact_count": 3,
    "artifact_urls": ["https://...", "https://..."],
    "artifact_sizes": [10485760, 52428800],  # Bytes
    "artifact_types": ["jar", "docker_image"]
}
```

### 2. Quality Gates

Monitors code quality metrics:

```python
quality_metrics = {
    "quality_gate_status": "PASSED",
    "code_coverage": 92.5,
    "test_coverage": 95.2,
    "code_smells": 3,
    "vulnerabilities": 0,
    "duplicated_lines": 1.2
}
```

### 3. Environment Tracking

Tracks deployment progression through environments:

```python
environment_chain = ["dev", "staging", "production"]
deployment_metadata = {
    "environment": "production",
    "deployment_strategy": "blue_green",
    "rollback_enabled": true,
    "canary_percentage": 10
}
```

### 4. Performance Analytics

Comprehensive performance analysis:

```python
performance_metrics = {
    "success_rate": 0.95,
    "avg_duration_ms": 240000,
    "duration_percentile_90": 360000,
    "performance_vs_avg": "faster",
    "performance_ratio": 0.8,
    "deployment_frequency_hours": 24
}
```

## Usage Examples

### 1. Basic Adapter Setup

```python
from src.project_context.ingestion.adapters.cicd_adapter import (
    CICDPlatform, CICDAdapterConfig, create_cicd_adapter
)

# Configure GitHub Actions adapter
config = CICDAdapterConfig(
    adapter_id="github_main",
    source_type="cicd",
    platform=CICDPlatform.GITHUB_ACTIONS,
    api_token=os.environ["GITHUB_TOKEN"],
    webhook_secret=os.environ["GITHUB_WEBHOOK_SECRET"],
    repositories=["owner/repo1", "owner/repo2"],
    calculate_performance_metrics=True
)

# Create and start adapter
adapter = create_cicd_adapter(CICDPlatform.GITHUB_ACTIONS, config)
await adapter.start()

# Fetch historical data
async for item in adapter.fetch_items(limit=100):
    context_item = await adapter.transform_item(item)
    # Store in database...
```

### 2. Webhook Processing

```python
from src.project_context.ingestion.webhook_processor import WebhookProcessor

# Initialize webhook processor
processor = WebhookProcessor(database, num_workers=10)

# Register adapters
processor.register_adapter(CICDPlatform.GITHUB_ACTIONS, github_adapter)
processor.register_adapter(CICDPlatform.GITLAB_CI, gitlab_adapter)

# Start processing
await processor.start()

# Process webhook (called by FastAPI endpoint)
result = await processor.process_webhook(
    platform=CICDPlatform.GITHUB_ACTIONS,
    event_type="workflow_run",
    payload=webhook_payload,
    signature=webhook_signature
)
```

### 3. Performance Correlation

```python
# Get performance metrics for context item
performance_metrics = await adapter._calculate_performance_metrics(
    context_item,
    recent_context_items
)

# Detect relationships
relationships = await adapter.detect_relationships(
    context_item,
    context_window
)

for rel_type, target_id, confidence in relationships:
    print(f"{rel_type}: {target_id} (confidence: {confidence:.2f})")
```

## Deployment

### 1. Environment Setup

```bash
# Install dependencies
pip install aiohttp structlog tenacity

# Set environment variables
export GITHUB_API_TOKEN="your_token"
export GITLAB_API_TOKEN="your_token"
export JENKINS_API_TOKEN="username:token"
export AZURE_DEVOPS_PAT="your_pat"
export CIRCLECI_API_TOKEN="your_token"
```

### 2. Configuration

Place configuration in `config/cicd_integration_config.yaml` and customize for your environment.

### 3. Webhook Setup

Configure webhooks in your CI/CD platforms to point to:
- GitHub: `https://your-domain/webhooks/github`
- GitLab: `https://your-domain/webhooks/gitlab`
- Jenkins: `https://your-domain/webhooks/jenkins`
- Azure: `https://your-domain/webhooks/azure`
- CircleCI: `https://your-domain/webhooks/circleci`

### 4. Monitoring

The system provides comprehensive monitoring through:
- Health check endpoints: `/webhooks/health`
- Metrics endpoints: `/webhooks/stats`
- Structured logging with correlation IDs
- Performance metrics tracking

## Security Considerations

### 1. Authentication

- **API Tokens**: Stored in environment variables, not configuration files
- **Webhook Secrets**: Used for payload validation
- **Rate Limiting**: Per-IP limits to prevent abuse
- **Network Security**: HTTPS required for webhook endpoints

### 2. Signature Validation

Each platform uses different signature validation:
- **GitHub**: HMAC-SHA256 with `X-Hub-Signature-256` header
- **GitLab**: Token comparison with `X-Gitlab-Token` header
- **Jenkins**: Typically relies on network security
- **CircleCI**: HMAC-SHA256 signature validation

### 3. Data Privacy

- **Sensitive Data**: Excluded from stored payloads
- **Retention**: Configurable data retention periods
- **Access Control**: Database-level access restrictions

## Troubleshooting

### Common Issues

1. **API Rate Limits**
   - Reduce `sync_batch_size` and `concurrent_requests`
   - Increase delays between requests
   - Monitor rate limit headers

2. **Webhook Signature Validation Failures**
   - Verify webhook secret configuration
   - Check payload encoding (UTF-8)
   - Validate signature algorithm

3. **Missing Correlations**
   - Increase `temporal_window_hours`
   - Verify commit SHA formats
   - Check project/repository matching

4. **Performance Issues**
   - Increase worker pool size
   - Optimize database indexes
   - Reduce historical sync period

### Debugging

Enable debug logging:
```python
import logging
logging.getLogger('src.project_context.ingestion.adapters.cicd_adapter').setLevel(logging.DEBUG)
```

Monitor webhook processing:
```bash
curl https://your-domain/webhooks/health
curl https://your-domain/webhooks/stats?hours=24
```

## Future Enhancements

### Planned Features

1. **Machine Learning Correlation**: AI-based relationship detection
2. **Advanced Analytics**: Trend analysis and prediction
3. **Integration Testing**: Automated CI/CD pipeline testing
4. **Custom Metrics**: User-defined performance indicators
5. **Real-time Dashboard**: Live CI/CD monitoring interface

### Extension Points

The system is designed for extensibility:

1. **Custom Platforms**: Implement `BaseCICDAdapter` for new platforms
2. **Correlation Algorithms**: Add custom relationship detection
3. **Performance Metrics**: Define platform-specific metrics
4. **Notification Systems**: Integrate alerting mechanisms
5. **Data Transformations**: Custom payload processing

## API Reference

### Factory Function

```python
def create_cicd_adapter(platform: CICDPlatform, config: CICDAdapterConfig) -> BaseCICDAdapter:
    \"\"\"Create appropriate CI/CD adapter for platform.\"\"\"
```

### Configuration Class

```python
class CICDAdapterConfig(AdapterConfig):
    \"\"\"Configuration for CI/CD adapters.\"\"\"

    platform: CICDPlatform
    base_url: str
    api_token: str
    webhook_secret: str
    repositories: List[str]
    projects: List[str]
    # ... additional configuration options
```

### Webhook Processor

```python
class WebhookProcessor:
    \"\"\"Centralized webhook processing system.\"\"\"

    async def process_webhook(
        self,
        platform: CICDPlatform,
        event_type: str,
        payload: dict,
        signature: Optional[str] = None,
        source_ip: Optional[str] = None
    ) -> Dict[str, Any]:
        \"\"\"Process incoming webhook.\"\"\"
```

---

## Summary

The CI/CD Adapter implementation provides a comprehensive solution for integrating multiple CI/CD platforms into the Unified Context System. Key achievements:

✅ **Multi-Platform Support**: GitHub Actions, GitLab CI, Jenkins, Azure DevOps, CircleCI
✅ **Real-time Processing**: Webhook-based event ingestion with queue management
✅ **Advanced Correlation**: Commit-based, temporal, and chain correlation
✅ **Performance Analytics**: Success rates, duration analysis, deployment frequency
✅ **Environment Tracking**: Deployment progression and environment correlation
✅ **Artifact Management**: Build artifact and quality gate tracking
✅ **Security**: Signature validation, rate limiting, and secure token handling
✅ **Extensibility**: Plugin architecture for custom platforms and metrics

The system enables comprehensive CI/CD observability and correlation within the temporal knowledge graph, providing valuable insights into software delivery pipelines and their relationships with code changes, deployments, and system behavior.
