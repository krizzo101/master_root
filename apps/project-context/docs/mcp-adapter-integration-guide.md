# MCP Adapter Integration Guide

This guide explains the integration between the chat and code adapters with the MCP (Model Context Protocol) tools framework, enabling unified pipeline orchestration and cross-adapter data validation.

## Overview

The MCP Adapter Integration provides a bridge between the ingestion pipeline components and the MCP server tools, allowing:

- **Unified Pipeline Control**: Start, stop, and monitor the ingestion pipeline through MCP tools
- **Cross-Adapter Validation**: Validate integration and data flow between chat and code adapters
- **Real-time Monitoring**: Get comprehensive health reports and system status
- **End-to-End Testing**: Run complete system validation tests

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCP Server    │    │  Integration     │    │   Ingestion     │
│                 │◄──►│     Layer        │◄──►│   Pipeline      │
│  - Tools Reg.   │    │                  │    │                 │
│  - FastMCP      │    │  - Orchestrator  │    │  - Chat Adapter │
└─────────────────┘    │  - Validation    │    │  - Code Adapter │
                       │  - Monitoring    │    │  - Git Adapter  │
                       └──────────────────┘    │  - Error Adapter│
                                               └─────────────────┘
```

## Integration Components

### 1. IngestionToolsManager

The central manager that coordinates between MCP tools and the ingestion pipeline:

```python
from project_context.tools.ingestion_tools import _tools_manager

# Initialize the integration
result = await _tools_manager.initialize()
print(f"Status: {result['status']}")
```

### 2. MCP Tools

Seven key tools are registered with the MCP server:

#### Pipeline Control Tools

- **`start_ingestion_pipeline_tool`**: Start the ingestion pipeline
- **`stop_ingestion_pipeline_tool`**: Stop the running pipeline
- **`get_pipeline_status_tool`**: Get current pipeline status and metrics

#### Validation and Testing Tools

- **`validate_adapter_integration_tool`**: Validate individual adapter integration
- **`analyze_cross_adapter_relationships_tool`**: Analyze data relationships between adapters
- **`test_end_to_end_pipeline_tool`**: Run comprehensive system tests
- **`get_integration_health_report_tool`**: Generate system health reports

## Usage Examples

### Starting the Pipeline

```python
# Start all adapters
result = await start_ingestion_pipeline_tool()

# Start specific adapters for 60 seconds
result = await start_ingestion_pipeline_tool(
    adapter_ids=["chat", "code"],
    duration_seconds=60
)
```

### Validating Adapters

```python
# Validate chat adapter integration
result = await validate_adapter_integration_tool("chat")

# Check validation results
if result["summary"]["overall_status"] == "pass":
    print("✅ Chat adapter validation passed")
    print(f"Success rate: {result['summary']['success_rate']}")
```

### Monitoring System Health

```python
# Get comprehensive health report
health = await get_integration_health_report_tool()

print(f"Health Score: {health['overall_health_score']}/100")
print(f"Active Adapters: {health['system_overview']['active_adapters']}")

# Check recommendations
for rec in health["recommendations"]:
    print(f"- {rec['recommendation']} (Priority: {rec['priority']})")
```

### Cross-Adapter Analysis

```python
# Analyze relationships between adapters
analysis = await analyze_cross_adapter_relationships_tool(time_window_hours=24)

# Check data flow patterns
for pattern_name, pattern_info in analysis["data_flow_analysis"].items():
    print(f"{pattern_name}: {pattern_info['pattern_strength']} strength")
```

## Configuration

### Pipeline Configuration

The integration uses the standard pipeline configuration file:

```yaml
# config/ingestion_pipeline.yaml
pipeline:
  max_concurrent_adapters: 10
  batch_commit_size: 1000
  health_check_interval: 60

adapters:
  chat:
    enabled: true
    batch_mode: "streaming"
    batch_size: 50
    generate_embeddings: true
    extract_relationships: true

  code:
    enabled: true
    batch_mode: "batch"
    batch_size: 200
    generate_embeddings: true
    generate_summaries: true
```

### Database Configuration

Ensure your database connection is properly configured:

```yaml
database:
  postgresql:
    host: "localhost"
    port: 5432
    database: "unified_context"
    username: "postgres"
    password: "${POSTGRES_PASSWORD}"
    pool_size: 20
```

## Validation and Testing

### Running Integration Validation

Use the provided validation script to test the complete integration:

```bash
# Run full validation suite
python validate_mcp_integration.py

# Check validation report
cat mcp_integration_validation_report.json
```

### Validation Test Coverage

The validation script tests:

1. **Tools Manager Initialization**: Verify MCP integration layer starts correctly
2. **Individual Adapter Validation**: Test each adapter's integration functionality
3. **Pipeline Integration**: Test pipeline startup, operation, and shutdown
4. **Cross-Adapter Relationships**: Validate relationship detection between adapters
5. **End-to-End Pipeline**: Complete system functionality test
6. **Health Reporting**: Verify monitoring and health check systems
7. **MCP Server Integration**: Confirm all tools are properly registered

### Expected Validation Results

A successful integration should achieve:
- ✅ 90%+ success rate on all validation tests
- ✅ All adapters passing basic integration tests
- ✅ Pipeline startup and data processing working
- ✅ Cross-adapter relationship detection functional
- ✅ Health reporting providing accurate metrics

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors

```python
# Error: Database connection failed
# Solution: Check database configuration and ensure PostgreSQL is running
await _tools_manager.initialize()  # Should show database status
```

#### 2. Adapter Initialization Failures

```python
# Error: Adapter not found in registry
# Solution: Check adapter configuration and registration
result = await validate_adapter_integration_tool("chat")
# Review result["tests"]["initialization"] for details
```

#### 3. Pipeline Startup Issues

```python
# Error: Pipeline startup failed
# Solution: Check adapter configurations and dependencies
status = await get_pipeline_status_tool()
# Review status["pipeline"] and status["adapters"] for issues
```

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
import structlog

# Configure debug logging
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)
```

### Health Check Commands

Quick health check commands:

```bash
# Check MCP server is running
curl -X GET http://localhost:8000/health

# Validate database connectivity
psql -h localhost -U postgres -d unified_context -c "SELECT 1;"

# Check adapter configurations
python -c "from project_context.tools.ingestion_tools import get_integration_health_report; import asyncio; print(asyncio.run(get_integration_health_report()))"
```

## Performance Optimization

### Recommended Settings

For optimal performance:

```yaml
# High-throughput configuration
pipeline:
  max_concurrent_adapters: 20
  batch_commit_size: 2000

adapters:
  chat:
    batch_size: 100
    max_items_per_second: 1000

  code:
    batch_size: 500
    max_items_per_second: 500
```

### Memory Management

Monitor memory usage during operation:

```python
health = await get_integration_health_report_tool()
memory_metrics = health["performance_metrics"]
print(f"Memory usage within limits: {memory_metrics.get('memory_ok', True)}")
```

## Production Deployment

### Pre-deployment Checklist

- [ ] Full validation suite passes (90%+ success rate)
- [ ] Database connectivity confirmed
- [ ] All adapters configured and tested
- [ ] Monitoring and alerting configured
- [ ] Resource limits appropriate for workload
- [ ] Backup and recovery procedures in place

### Monitoring in Production

Set up continuous monitoring:

```python
# Schedule regular health checks
import asyncio

async def monitor_health():
    while True:
        health = await get_integration_health_report_tool()
        if health["overall_health_score"] < 80:
            # Alert administrators
            print(f"⚠️ Health score dropped to {health['overall_health_score']}")

        await asyncio.sleep(300)  # Check every 5 minutes
```

## API Reference

### Tool Functions

#### start_ingestion_pipeline

```python
async def start_ingestion_pipeline(
    adapter_ids: Optional[List[str]] = None,
    config_path: Optional[str] = None,
    duration_seconds: Optional[int] = None
) -> Dict[str, Any]
```

**Parameters:**
- `adapter_ids`: List of adapter IDs to start (default: all)
- `config_path`: Path to pipeline configuration file
- `duration_seconds`: How long to run pipeline (default: run until stopped)

**Returns:** Pipeline startup status and metrics

#### validate_adapter_integration

```python
async def validate_adapter_integration(
    adapter_id: str,
    test_items_count: int = 10
) -> Dict[str, Any]
```

**Parameters:**
- `adapter_id`: ID of adapter to validate
- `test_items_count`: Number of test items to process

**Returns:** Comprehensive validation results including test status and performance metrics

#### get_integration_health_report

```python
async def get_integration_health_report() -> Dict[str, Any]
```

**Returns:** Comprehensive health report including:
- System overview and status
- Adapter health assessments
- Performance metrics
- Recommendations for improvements

## Support

For additional support:

1. Check the validation report: `mcp_integration_validation_report.json`
2. Review adapter logs in the pipeline monitoring system
3. Consult the troubleshooting section above
4. Verify database and system resource availability
