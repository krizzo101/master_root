# Example 2: Parallel Test Scaffolding

## Scenario
Generate comprehensive test suites for 10 microservices in parallel using OpenAI Codex's sandbox capabilities, creating one PR per service.

## Implementation

### Orchestration Script
```python
#!/usr/bin/env python3
# parallel-test-generation.py

import asyncio
import json
from typing import List, Dict, Any
from opsvi_mcp.servers.multi_agent_orchestrator import (
    orchestrate_task,
    spawn_codex_sandbox
)

# Microservices to process
SERVICES = [
    {"name": "auth-service", "repo": "github.com/org/auth-service", "lang": "python"},
    {"name": "user-service", "repo": "github.com/org/user-service", "lang": "python"},
    {"name": "payment-service", "repo": "github.com/org/payment-service", "lang": "javascript"},
    {"name": "notification-service", "repo": "github.com/org/notification-service", "lang": "go"},
    {"name": "inventory-service", "repo": "github.com/org/inventory-service", "lang": "java"},
    {"name": "shipping-service", "repo": "github.com/org/shipping-service", "lang": "python"},
    {"name": "order-service", "repo": "github.com/org/order-service", "lang": "javascript"},
    {"name": "analytics-service", "repo": "github.com/org/analytics-service", "lang": "python"},
    {"name": "search-service", "repo": "github.com/org/search-service", "lang": "rust"},
    {"name": "recommendation-service", "repo": "github.com/org/recommendation-service", "lang": "python"}
]

async def generate_test_suite(service: Dict[str, str]) -> Dict[str, Any]:
    """Generate test suite for a single service using Codex sandbox"""
    
    # Craft language-specific test generation prompt
    prompts = {
        "python": "Generate comprehensive pytest test suite with fixtures, mocks, and 90% coverage",
        "javascript": "Generate Jest test suite with mocks, integration tests, and snapshot tests",
        "go": "Generate Go test suite with table-driven tests and benchmarks",
        "java": "Generate JUnit 5 test suite with Mockito mocks and integration tests",
        "rust": "Generate Rust test suite with unit tests and property-based tests"
    }
    
    task_prompt = f"""
    For the {service['name']} microservice:
    1. Analyze all source files to understand the codebase
    2. {prompts.get(service['lang'], 'Generate comprehensive test suite')}
    3. Include:
       - Unit tests for all public functions
       - Integration tests for API endpoints
       - Edge cases and error scenarios
       - Performance tests where applicable
    4. Ensure tests are idempotent and can run in CI
    5. Add test documentation in README
    6. Update CI configuration to run new tests
    """
    
    # Spawn Codex sandbox with preloaded repository
    result = await spawn_codex_sandbox(
        task=task_prompt,
        repository_url=service['repo'],
        branch="main",
        generate_pr=True
    )
    
    return {
        "service": service['name'],
        "language": service['lang'],
        "sandbox_id": result['sandbox_id'],
        "pr_url": result['pr_url'],
        "execution_time": result['duration_ms'],
        "test_stats": result.get('test_statistics', {})
    }

async def parallel_test_generation():
    """Orchestrate parallel test generation across all services"""
    
    print(f"Starting parallel test generation for {len(SERVICES)} services...")
    
    # Create tasks for parallel execution
    tasks = [generate_test_suite(service) for service in SERVICES]
    
    # Execute all tasks in parallel using Codex sandboxes
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    successful = []
    failed = []
    
    for result in results:
        if isinstance(result, Exception):
            failed.append(str(result))
        else:
            successful.append(result)
    
    # Generate summary report
    report = generate_test_report(successful, failed)
    
    # Save artifacts
    save_artifacts(report)
    
    return report

def generate_test_report(successful: List[Dict], failed: List[str]) -> Dict[str, Any]:
    """Generate comprehensive test generation report"""
    
    total_tests = sum(r.get('test_stats', {}).get('total_tests', 0) for r in successful)
    avg_coverage = sum(r.get('test_stats', {}).get('coverage', 0) for r in successful) / len(successful) if successful else 0
    
    return {
        "summary": {
            "total_services": len(SERVICES),
            "successful": len(successful),
            "failed": len(failed),
            "total_tests_generated": total_tests,
            "average_coverage": f"{avg_coverage:.1f}%",
            "total_execution_time": sum(r['execution_time'] for r in successful)
        },
        "services": successful,
        "failures": failed,
        "pull_requests": [
            {
                "service": r['service'],
                "pr_url": r['pr_url'],
                "tests_added": r.get('test_stats', {}).get('total_tests', 0)
            }
            for r in successful
        ]
    }

def save_artifacts(report: Dict[str, Any]):
    """Save execution artifacts and logs"""
    
    # Save main report
    with open('/tmp/test_generation_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    # Save individual service logs
    for service in report['services']:
        log_path = f"/tmp/logs/{service['service']}_test_generation.log"
        # Fetch and save sandbox logs
        fetch_sandbox_logs(service['sandbox_id'], log_path)
    
    print(f"Artifacts saved to /tmp/")
    print(f"Report: /tmp/test_generation_report.json")
    print(f"Logs: /tmp/logs/")

async def fetch_sandbox_logs(sandbox_id: str, output_path: str):
    """Fetch logs from Codex sandbox"""
    # Implementation would call Codex API to retrieve logs
    pass

if __name__ == "__main__":
    report = asyncio.run(parallel_test_generation())
    
    print("\n" + "="*60)
    print("TEST GENERATION COMPLETE")
    print("="*60)
    print(f"✅ Successful: {report['summary']['successful']}/{report['summary']['total_services']}")
    print(f"📊 Tests Generated: {report['summary']['total_tests_generated']}")
    print(f"📈 Average Coverage: {report['summary']['average_coverage']}")
    print(f"⏱️  Total Time: {report['summary']['total_execution_time']/1000:.1f}s")
    print("\nPull Requests Created:")
    for pr in report['pull_requests']:
        print(f"  - {pr['service']}: {pr['pr_url']} (+{pr['tests_added']} tests)")
```

### Expected Output

```json
{
  "summary": {
    "total_services": 10,
    "successful": 9,
    "failed": 1,
    "total_tests_generated": 847,
    "average_coverage": "88.3%",
    "total_execution_time": 125000
  },
  "services": [
    {
      "service": "auth-service",
      "language": "python",
      "sandbox_id": "sbx_123abc",
      "pr_url": "https://github.com/org/auth-service/pull/45",
      "execution_time": 12500,
      "test_stats": {
        "total_tests": 95,
        "unit_tests": 67,
        "integration_tests": 28,
        "coverage": 91.2,
        "files_created": [
          "tests/test_auth_manager.py",
          "tests/test_jwt_handler.py",
          "tests/fixtures/auth_fixtures.py",
          "tests/integration/test_auth_api.py"
        ]
      }
    }
  ],
  "pull_requests": [
    {
      "service": "auth-service",
      "pr_url": "https://github.com/org/auth-service/pull/45",
      "tests_added": 95
    }
  ]
}
```

### Monitoring Dashboard

```python
# monitor_test_generation.py

import time
from datetime import datetime

class TestGenerationMonitor:
    """Real-time monitoring of parallel test generation"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.sandbox_status = {}
        
    async def monitor_sandboxes(self, sandbox_ids: List[str]):
        """Monitor sandbox execution status"""
        
        while any(status != 'completed' for status in self.sandbox_status.values()):
            for sandbox_id in sandbox_ids:
                status = await check_sandbox_status(sandbox_id)
                self.sandbox_status[sandbox_id] = status['state']
                
                if status['state'] == 'running':
                    print(f"🔄 {sandbox_id}: {status['progress']}% complete")
                elif status['state'] == 'completed':
                    print(f"✅ {sandbox_id}: PR created - {status['pr_url']}")
                elif status['state'] == 'failed':
                    print(f"❌ {sandbox_id}: {status['error']}")
            
            time.sleep(5)  # Poll every 5 seconds
```

### CI Integration

```yaml
# .github/workflows/test-generation.yml

name: Weekly Test Generation

on:
  schedule:
    - cron: '0 0 * * 1'  # Every Monday
  workflow_dispatch:

jobs:
  generate-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install opsvi-mcp
          
      - name: Run parallel test generation
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python parallel-test-generation.py
          
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: test-generation-report
          path: /tmp/test_generation_report.json
          
      - name: Notify Slack
        if: always()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Test generation completed: ${{ job.status }}"
            }
```

### Validation Script

```python
async def validate_generated_tests():
    """Validate that generated tests actually work"""
    
    for pr in pull_requests:
        # 1. Check PR checks status
        checks = await get_pr_checks(pr['pr_url'])
        
        # 2. If checks pass, run additional validation
        if all(check.passing for check in checks):
            # Run tests in isolated sandbox
            validation_result = await spawn_codex_sandbox(
                task="Run full test suite and generate coverage report",
                repository_url=pr['pr_url'],
                generate_pr=False
            )
            
            # 3. Check coverage meets threshold
            if validation_result['coverage'] < 80:
                add_pr_comment(
                    pr['pr_url'],
                    f"⚠️ Coverage {validation_result['coverage']}% is below 80% threshold"
                )
```

---
*This example leverages OpenAI Codex's parallel sandbox execution for efficient test generation across multiple services.*