# CI/CD Pipeline Integration Patterns for Unified Context System

## Overview

This document outlines comprehensive integration patterns for tracking CI/CD pipelines, builds, and deployments across major platforms. The goal is to correlate build/deployment events with code changes and conversations in the temporal knowledge graph.

## Integration Architecture Patterns

### 1. Real-time Webhook Processing

#### Core Webhook Handler Design
```python
class WebhookProcessor:
    """Central webhook processor supporting multiple CI/CD platforms"""

    async def process_webhook(self, platform: str, event_type: str, payload: dict):
        # Platform-specific payload transformation
        context_item = await self.transform_payload(platform, event_type, payload)

        # Correlation with existing context
        await self.correlate_with_context(context_item)

        # Store in unified schema
        await self.store_context_item(context_item)
```

#### Event Processing Pipeline
1. **Signature Validation**: Verify webhook authenticity
2. **Payload Parsing**: Transform platform-specific data to unified schema
3. **Context Correlation**: Link events to code changes, PRs, conversations
4. **Real-time Updates**: Push to monitoring dashboard
5. **Historical Analysis**: Feed ML pattern detection

### 2. Batch API Polling Architecture

#### Historical Data Sync
```python
class HistoricalSync:
    """Batch synchronization for historical CI/CD data"""

    async def sync_builds(self, platform: str, since: datetime):
        # Rate-limited API calls
        async for batch in self.fetch_builds_paginated(platform, since):
            # Transform and correlate
            context_items = await self.transform_build_batch(batch)

            # Bulk insert with deduplication
            await self.bulk_store(context_items)
```

## Platform-Specific Integration Patterns

### GitHub Actions Integration

#### Webhook Events to Track
- `workflow_run` - Overall workflow execution
- `workflow_job` - Individual job status
- `check_run` - Check suite results
- `deployment` - Deployment events
- `deployment_status` - Deployment progress

#### Payload Transformation
```python
class GitHubActionsAdapter(BaseCIAdapter):
    def transform_workflow_run(self, payload: dict) -> ContextItem:
        return ContextItem(
            source_type="cicd",
            source_id=payload["workflow_run"]["id"],
            entity_type="workflow_run",
            title=f"Workflow: {payload['workflow_run']['name']}",
            content=self.extract_run_summary(payload),
            timestamp=datetime.fromisoformat(payload["workflow_run"]["created_at"]),
            timestamp_end=datetime.fromisoformat(payload["workflow_run"]["updated_at"])
                          if payload["workflow_run"]["conclusion"] else None,
            project_id=payload["repository"]["name"],
            actor_id=payload["workflow_run"]["actor"]["login"],
            actor_type="human",
            metrics={
                "status": payload["workflow_run"]["status"],
                "conclusion": payload["workflow_run"]["conclusion"],
                "attempt": payload["workflow_run"]["run_attempt"],
                "duration_ms": self.calculate_duration(payload),
                "run_number": payload["workflow_run"]["run_number"]
            },
            source_data=payload
        )
```

#### API Integration for Historical Data
```python
# GitHub API patterns
GET /repos/{owner}/{repo}/actions/runs
GET /repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs
GET /repos/{owner}/{repo}/deployments
GET /repos/{owner}/{repo}/check-runs/{check_run_id}
```

### Jenkins Integration

#### Webhook Configuration
```groovy
// Jenkins pipeline webhook setup
post {
    always {
        script {
            httpRequest(
                httpMode: 'POST',
                url: "${WEBHOOK_URL}/jenkins/build",
                contentType: 'APPLICATION_JSON',
                requestBody: writeJSON([
                    build_number: env.BUILD_NUMBER,
                    job_name: env.JOB_NAME,
                    build_status: currentBuild.result,
                    commit_sha: env.GIT_COMMIT,
                    duration: currentBuild.duration
                ])
            )
        }
    }
}
```

#### Jenkins API Integration
```python
class JenkinsAdapter(BaseCIAdapter):
    async def fetch_build_data(self, job_name: str, build_number: int):
        # Jenkins REST API calls
        url = f"{self.jenkins_url}/job/{job_name}/{build_number}/api/json"

        async with self.session.get(url, auth=self.auth) as response:
            build_data = await response.json()

        return self.transform_jenkins_build(build_data)

    def transform_jenkins_build(self, build_data: dict) -> ContextItem:
        return ContextItem(
            source_type="cicd",
            source_id=f"jenkins_{build_data['id']}",
            entity_type="jenkins_build",
            title=f"Build {build_data['displayName']}",
            content=self.extract_build_summary(build_data),
            timestamp=datetime.fromtimestamp(build_data["timestamp"] / 1000),
            timestamp_end=datetime.fromtimestamp(
                (build_data["timestamp"] + build_data["duration"]) / 1000
            ),
            metrics={
                "result": build_data["result"],
                "duration_ms": build_data["duration"],
                "queue_id": build_data.get("queueId"),
                "test_results": self.extract_test_metrics(build_data)
            },
            source_data=build_data
        )
```

### GitLab CI/CD Integration

#### Webhook Events
- `Pipeline Hook` - Pipeline status changes
- `Job Hook` - Individual job completion
- `Deployment Hook` - Deployment events
- `Release Hook` - Release creation

#### GitLab API Integration
```python
class GitLabAdapter(BaseCIAdapter):
    async def sync_pipelines(self, project_id: str, since: datetime):
        url = f"{self.gitlab_url}/api/v4/projects/{project_id}/pipelines"

        params = {
            "updated_after": since.isoformat(),
            "per_page": 100,
            "sort": "desc"
        }

        async for pipeline in self.paginate_api(url, params):
            # Fetch detailed pipeline data
            pipeline_detail = await self.fetch_pipeline_detail(
                project_id, pipeline["id"]
            )

            context_item = self.transform_gitlab_pipeline(pipeline_detail)
            yield context_item
```

### Azure DevOps Integration

#### Service Hooks Configuration
```json
{
    "publisherId": "tfs",
    "eventType": "build.complete",
    "resourceVersion": "1.0",
    "consumerId": "webHooks",
    "consumerActionId": "httpRequest",
    "url": "https://your-endpoint.com/azure/build-complete"
}
```

#### Azure DevOps REST API
```python
class AzureDevOpsAdapter(BaseCIAdapter):
    async def fetch_builds(self, project: str, definition_id: int):
        url = f"{self.org_url}/{project}/_apis/build/builds"

        params = {
            "definitions": definition_id,
            "$top": 100,
            "api-version": "7.0"
        }

        async with self.session.get(url, headers=self.auth_headers) as response:
            data = await response.json()

        for build in data["value"]:
            yield self.transform_azure_build(build)
```

## Unified Schema Extensions for CI/CD Data

### Enhanced Context Items Schema
```sql
-- Add CI/CD specific fields to context_items
ALTER TABLE context_items ADD COLUMN IF NOT EXISTS
    pipeline_id VARCHAR(255),
    build_number INTEGER,
    job_name VARCHAR(255),
    environment_name VARCHAR(100),
    deployment_status VARCHAR(50),
    artifact_urls TEXT[],
    test_results JSONB,
    performance_metrics JSONB;

-- CI/CD specific indexes
CREATE INDEX IF NOT EXISTS idx_context_items_pipeline
    ON context_items(pipeline_id, build_number);
CREATE INDEX IF NOT EXISTS idx_context_items_environment
    ON context_items(environment_name, deployment_status);
```

### CI/CD Relationships Table
```sql
CREATE TABLE IF NOT EXISTS cicd_correlations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    build_context_id UUID REFERENCES context_items(id),
    commit_sha VARCHAR(64),
    pull_request_id VARCHAR(50),
    deployment_id UUID,

    -- Correlation metadata
    correlation_confidence FLOAT DEFAULT 1.0,
    correlation_method VARCHAR(50), -- 'commit_sha', 'branch_name', 'tag'

    -- Performance tracking
    build_duration_ms INTEGER,
    deployment_duration_ms INTEGER,
    success_rate FLOAT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Real-time Processing Architecture

### Event Stream Processing
```python
class CICDEventProcessor:
    """Real-time CI/CD event processing"""

    def __init__(self):
        self.webhook_handlers = {
            "github": GitHubWebhookHandler(),
            "gitlab": GitLabWebhookHandler(),
            "jenkins": JenkinsWebhookHandler(),
            "azure": AzureWebhookHandler()
        }

    async def process_event(self, platform: str, event_data: dict):
        handler = self.webhook_handlers.get(platform)
        if not handler:
            raise ValueError(f"Unsupported platform: {platform}")

        # Transform to unified format
        context_item = await handler.transform(event_data)

        # Real-time correlation
        correlations = await self.detect_correlations(context_item)

        # Store with relationships
        await self.store_with_correlations(context_item, correlations)

        # Trigger real-time updates
        await self.notify_dashboard(context_item)
```

### Correlation Detection Patterns

#### Commit-based Correlation
```python
async def correlate_by_commit(self, build_item: ContextItem) -> List[ContextRelationship]:
    commit_sha = build_item.source_data.get("head_commit", {}).get("id")
    if not commit_sha:
        return []

    # Find related code changes
    code_items = await self.database.query_context_items(
        source_type="git",
        entity_type="commit",
        filters={"commit_sha": commit_sha}
    )

    relationships = []
    for code_item in code_items:
        relationships.append(ContextRelationship(
            source_id=build_item.id,
            target_id=code_item.id,
            relationship_type="builds_commit",
            confidence=1.0,
            metadata={"commit_sha": commit_sha}
        ))

    return relationships
```

#### Temporal Correlation
```python
async def correlate_by_timing(self, deploy_item: ContextItem) -> List[ContextRelationship]:
    # Find conversations about deployment around same time
    time_window = timedelta(hours=2)

    chat_items = await self.database.query_context_items(
        source_type="chat",
        timestamp_range=(
            deploy_item.timestamp - time_window,
            deploy_item.timestamp + time_window
        ),
        content_search="deploy OR deployment OR release"
    )

    relationships = []
    for chat_item in chat_items:
        confidence = self.calculate_temporal_confidence(
            deploy_item.timestamp, chat_item.timestamp
        )

        if confidence > 0.5:
            relationships.append(ContextRelationship(
                source_id=deploy_item.id,
                target_id=chat_item.id,
                relationship_type="discussed_during_deployment",
                confidence=confidence,
                temporal_context="concurrent"
            ))

    return relationships
```

## Performance and Scalability Patterns

### Webhook Processing at Scale
```python
class ScalableWebhookProcessor:
    def __init__(self):
        self.event_queue = asyncio.Queue(maxsize=10000)
        self.worker_pool = []

    async def start_workers(self, num_workers: int = 10):
        for i in range(num_workers):
            worker = asyncio.create_task(self.worker_loop(f"worker-{i}"))
            self.worker_pool.append(worker)

    async def worker_loop(self, worker_id: str):
        while True:
            try:
                event = await self.event_queue.get()
                await self.process_single_event(event)
                self.event_queue.task_done()
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
```

### Rate Limiting and Circuit Breaker
```python
class APIRateLimiter:
    def __init__(self, requests_per_minute: int = 100):
        self.rate_limit = requests_per_minute
        self.requests = deque()

    async def acquire(self):
        now = time.time()

        # Remove requests older than 1 minute
        while self.requests and now - self.requests[0] > 60:
            self.requests.popleft()

        if len(self.requests) >= self.rate_limit:
            sleep_time = 60 - (now - self.requests[0])
            await asyncio.sleep(sleep_time)

        self.requests.append(now)
```

## Error Handling and Resilience

### Retry Mechanisms
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
)
async def webhook_delivery_with_retry(self, url: str, payload: dict):
    async with self.session.post(url, json=payload) as response:
        response.raise_for_status()
        return await response.json()
```

### Dead Letter Queue
```python
class DeadLetterHandler:
    async def handle_failed_event(self, event: dict, error: Exception):
        # Store failed event for manual inspection
        await self.database.store_failed_event({
            "event": event,
            "error": str(error),
            "timestamp": datetime.utcnow(),
            "retry_count": event.get("retry_count", 0)
        })

        # Alert on persistent failures
        if event.get("retry_count", 0) > 5:
            await self.send_alert(f"Event processing failed: {error}")
```

## Monitoring and Observability

### Metrics Collection
```python
class CICDMetricsCollector:
    def __init__(self):
        self.metrics = {
            "webhooks_received": 0,
            "webhooks_processed": 0,
            "webhooks_failed": 0,
            "api_calls_made": 0,
            "correlations_detected": 0,
            "processing_latency_ms": deque(maxlen=1000)
        }

    async def record_webhook_processing(self, duration_ms: float):
        self.metrics["webhooks_processed"] += 1
        self.metrics["processing_latency_ms"].append(duration_ms)

    def get_health_summary(self) -> dict:
        return {
            "total_processed": self.metrics["webhooks_processed"],
            "success_rate": self.calculate_success_rate(),
            "avg_latency_ms": statistics.mean(self.metrics["processing_latency_ms"]),
            "p95_latency_ms": statistics.quantiles(
                self.metrics["processing_latency_ms"], n=20
            )[18] if self.metrics["processing_latency_ms"] else 0
        }
```

## Implementation Strategy

### Phase 1: Core Webhook Infrastructure
1. **Webhook Receiver**: Basic HTTP endpoint for all platforms
2. **Authentication**: Platform-specific signature validation
3. **Event Routing**: Route events to appropriate handlers
4. **Basic Storage**: Store raw webhooks in database

### Phase 2: Platform Adapters
1. **GitHub Actions Adapter**: Complete workflow/job tracking
2. **Jenkins Adapter**: Build and pipeline integration
3. **GitLab CI Adapter**: Pipeline and deployment tracking
4. **Azure DevOps Adapter**: Build and release pipelines

### Phase 3: Correlation Engine
1. **Commit Correlation**: Link builds to code changes
2. **Temporal Correlation**: Connect deployments to conversations
3. **Pattern Learning**: ML-based relationship detection
4. **Historical Analysis**: Batch processing of past data

### Phase 4: Advanced Features
1. **Performance Analytics**: Build success rates, deployment frequency
2. **Predictive Insights**: Failure prediction based on patterns
3. **Dashboard Integration**: Real-time CI/CD status visualization
4. **Alert System**: Failure notifications with context

This comprehensive integration strategy provides robust CI/CD pipeline tracking while maintaining high performance and reliability at scale.
