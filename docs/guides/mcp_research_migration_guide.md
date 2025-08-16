# MCP Research Engine Migration Guide

## Overview

This guide provides step-by-step instructions for migrating from the static research engine to the new MCP-enhanced research engine in the autonomous coder.

## Migration Benefits

### Before (Static Research Engine)
- ❌ Hardcoded version numbers that become outdated
- ❌ Manual updates required for new releases
- ❌ Limited to predefined technology list
- ❌ No real-time validation
- ❌ Static best practices

### After (MCP Research Engine)
- ✅ Real-time version discovery from multiple sources
- ✅ Automatic updates from official sources
- ✅ Support for any technology/package
- ✅ Cross-validation from multiple sources
- ✅ Dynamic best practices based on current trends
- ✅ Intelligent caching for performance
- ✅ Fallback to static data for reliability

## Migration Steps

### Step 1: Install Dependencies

```bash
# Ensure MCP servers are available
pip install mcp-server-brave-search
pip install mcp-server-firecrawl
pip install mcp-server-context7

# Verify installation
python -c "import mcp__mcp_web_search; print('Brave Search: OK')"
python -c "import mcp__firecrawl; print('Firecrawl: OK')"
python -c "import mcp__tech_docs; print('Context7: OK')"
```

### Step 2: Parallel Testing

Run both engines in parallel to validate results:

```python
# In your code
from modules.research_engine import ResearchEngine  # Original
from modules.mcp_research_engine import MCPResearchEngine  # New

async def compare_engines(package_name):
    """Compare results from both engines."""
    
    # Get results from both
    static_engine = ResearchEngine()
    mcp_engine = MCPResearchEngine()
    
    static_result = await static_engine.research_technology(package_name)
    mcp_result = await mcp_engine.research_technology(package_name)
    
    # Compare versions
    print(f"Package: {package_name}")
    print(f"  Static Version: {static_result.version}")
    print(f"  MCP Version: {mcp_result.version}")
    
    # Log if different
    if static_result.version != mcp_result.version:
        print(f"  ⚠️ Version mismatch - MCP found newer version")
    
    return mcp_result  # Use MCP result
```

### Step 3: Update Import Statements

Replace imports throughout the codebase:

```python
# Before
from modules.research_engine import ResearchEngine

# After
from modules.mcp_research_engine import MCPResearchEngine as ResearchEngine
```

### Step 4: Configure Caching

Set up appropriate cache settings:

```python
# config.yaml or environment variables
research_cache:
  memory_size: 100  # Number of items in memory
  disk_cache_dir: ".cache"
  ttl_seconds: 3600  # 1 hour
  
mcp_timeouts:
  search: 10  # seconds
  scrape: 30  # seconds
  docs: 20    # seconds
```

### Step 5: Monitor Performance

Add logging to track MCP performance:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# In your code
engine = MCPResearchEngine()

# Get summary statistics
summary = engine.get_research_summary()
logging.info(f"Research Engine Status: {summary}")
```

### Step 6: Implement Gradual Rollout

Use feature flags for controlled rollout:

```python
class AdaptiveResearchEngine(BaseModule):
    """Adaptive engine with gradual MCP rollout."""
    
    def __init__(self, mcp_percentage: float = 0.1):
        """Start with 10% MCP usage."""
        self.mcp_percentage = mcp_percentage
        self.static_engine = ResearchEngine()
        self.mcp_engine = MCPResearchEngine()
    
    async def research_technology(self, name: str) -> TechInfo:
        """Use MCP for configured percentage of requests."""
        import random
        
        if random.random() < self.mcp_percentage:
            # Use MCP engine
            self.log(f"Using MCP engine for {name}")
            try:
                return await self.mcp_engine.research_technology(name)
            except Exception as e:
                self.log(f"MCP failed, falling back: {e}")
                return await self.static_engine.research_technology(name)
        else:
            # Use static engine
            return await self.static_engine.research_technology(name)
    
    def increase_mcp_usage(self, increment: float = 0.1):
        """Gradually increase MCP usage."""
        self.mcp_percentage = min(1.0, self.mcp_percentage + increment)
        self.log(f"MCP usage increased to {self.mcp_percentage * 100}%")
```

## Configuration Options

### Environment Variables

```bash
# MCP Service Configuration
export MCP_BRAVE_TIMEOUT=10
export MCP_FIRECRAWL_TIMEOUT=30
export MCP_CONTEXT7_TIMEOUT=20

# Cache Configuration
export RESEARCH_CACHE_TTL=3600
export RESEARCH_CACHE_SIZE=100

# Fallback Configuration
export USE_FALLBACK_ON_ERROR=true
export FALLBACK_CONFIDENCE_THRESHOLD=0.5

# Rate Limiting
export MCP_REQUESTS_PER_MINUTE=60
export MCP_BURST_SIZE=10
```

### Configuration File (research_config.yaml)

```yaml
mcp_services:
  brave_search:
    enabled: true
    timeout: 10
    max_retries: 3
    freshness_default: "pw"  # past week
    
  firecrawl:
    enabled: true
    timeout: 30
    max_retries: 2
    formats: ["markdown"]
    only_main_content: true
    
  context7:
    enabled: true
    timeout: 20
    max_retries: 3
    default_tokens: 2000
    
cache:
  memory:
    size: 100
    ttl: 300  # 5 minutes
  disk:
    enabled: true
    path: ".cache"
    ttl: 3600  # 1 hour
    max_size_mb: 100
    
fallback:
  enabled: true
  update_from_mcp: true  # Update static data from successful MCP calls
  confidence_threshold: 0.7
  
monitoring:
  log_level: "INFO"
  metrics_enabled: true
  slow_query_threshold_ms: 5000
```

## Testing Strategy

### Unit Tests

```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.asyncio
async def test_mcp_research_with_mock():
    """Test MCP research with mocked services."""
    
    with patch('mcp__mcp_web_search.brave_web_search') as mock_brave:
        # Mock successful response
        mock_brave.return_value = [
            {
                "Title": "React 19.1.1 Released",
                "URL": "https://react.dev/blog",
                "Description": "Latest version 19.1.1 with new features"
            }
        ]
        
        engine = MCPResearchEngine()
        result = await engine.research_technology("react")
        
        assert result.version == "19.1.1"
        assert result.name == "react"
        mock_brave.assert_called_once()
```

### Integration Tests

```python
@pytest.mark.integration
async def test_real_mcp_services():
    """Test with real MCP services (rate limited)."""
    
    engine = MCPResearchEngine()
    
    # Test a known package
    result = await engine.research_technology("react")
    
    # Verify reasonable version format
    assert re.match(r'\d+\.\d+\.\d+', result.version)
    
    # Verify caching works
    start = time.time()
    cached_result = await engine.research_technology("react")
    cache_time = time.time() - start
    
    assert cache_time < 0.1  # Should be instant from cache
    assert cached_result.version == result.version
```

### Performance Tests

```python
@pytest.mark.performance
async def test_parallel_performance():
    """Test parallel execution performance."""
    
    engine = MCPResearchEngine()
    packages = ["react", "vue", "angular", "svelte", "solid"]
    
    start = time.time()
    results = await engine.get_current_versions(packages)
    elapsed = time.time() - start
    
    # Should complete in reasonable time
    assert elapsed < 10  # seconds
    
    # Should return all results
    assert len(results) == len(packages)
    
    # Calculate average time per package
    avg_time = elapsed / len(packages)
    assert avg_time < 2  # Should be faster due to parallelization
```

## Monitoring and Observability

### Metrics to Track

```python
class ResearchMetrics:
    """Track research engine metrics."""
    
    def __init__(self):
        self.metrics = {
            "mcp_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "fallback_uses": 0,
            "errors": 0,
            "total_latency_ms": 0
        }
    
    def record_mcp_call(self, service: str, latency_ms: float, success: bool):
        """Record MCP service call metrics."""
        self.metrics["mcp_calls"] += 1
        self.metrics["total_latency_ms"] += latency_ms
        
        if not success:
            self.metrics["errors"] += 1
    
    def get_summary(self) -> Dict:
        """Get metrics summary."""
        total_calls = self.metrics["mcp_calls"]
        
        return {
            "total_calls": total_calls,
            "success_rate": 1 - (self.metrics["errors"] / max(total_calls, 1)),
            "cache_hit_rate": self.metrics["cache_hits"] / 
                            max(self.metrics["cache_hits"] + self.metrics["cache_misses"], 1),
            "avg_latency_ms": self.metrics["total_latency_ms"] / max(total_calls, 1),
            "fallback_rate": self.metrics["fallback_uses"] / max(total_calls, 1)
        }
```

### Logging Best Practices

```python
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()

# In your code
logger.info("research_started", 
           package=package_name,
           strategy="mcp",
           services=["brave", "context7"])

logger.error("mcp_service_failed",
            service="brave_search",
            error=str(e),
            fallback_used=True)
```

## Rollback Plan

If issues arise, follow this rollback procedure:

1. **Immediate Rollback** (< 1 minute):
   ```python
   # In config
   USE_MCP_RESEARCH = False  # Disables MCP, uses static only
   ```

2. **Partial Rollback** (< 5 minutes):
   ```python
   # Reduce MCP usage percentage
   engine.mcp_percentage = 0.0  # 0% MCP usage
   ```

3. **Full Rollback** (< 10 minutes):
   ```bash
   # Revert to previous version
   git checkout main
   git revert [commit-hash]
   
   # Or use previous module
   mv modules/research_engine.py.backup modules/research_engine.py
   ```

## Troubleshooting

### Common Issues and Solutions

1. **MCP Service Timeout**
   - Increase timeout values in config
   - Check network connectivity
   - Verify MCP server is running

2. **Cache Corruption**
   - Clear cache directory: `rm -rf .cache/*`
   - Restart application

3. **Version Parsing Errors**
   - Check regex patterns in `_extract_version_pattern()`
   - Add debug logging for unparsed versions
   - Update patterns for new version formats

4. **Circuit Breaker Open**
   - Check service health
   - Review error logs
   - Wait for timeout period or manually reset

5. **High Latency**
   - Enable caching if disabled
   - Reduce parallel request count
   - Use more selective queries

## Success Criteria

Migration is considered successful when:

- [ ] All tests pass with MCP engine
- [ ] Cache hit rate > 50% after warm-up
- [ ] Average response time < 2 seconds
- [ ] Error rate < 5%
- [ ] Fallback usage < 10%
- [ ] Version accuracy validated for top 20 packages
- [ ] No increase in application errors
- [ ] Memory usage stable (no leaks)

## Conclusion

The MCP research engine provides significant improvements over the static version while maintaining reliability through fallback mechanisms. Follow this guide for a smooth migration and monitor metrics to ensure optimal performance.