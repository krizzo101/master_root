# Sleuth Intel Workflow Templates

Comprehensive workflow templates for intelligence gathering investigations with pre-configured agent coordination, dependency chains, error handling, and result formatting.

## Overview

The workflow template system provides optimized, standardized workflows for common investigation scenarios. Each template includes:

- **Agent Coordination**: Automatic selection and coordination of appropriate agents
- **Dependency Management**: Proper execution order based on data dependencies
- **Cost Optimization**: Budget-aware execution with cost estimation
- **Progress Tracking**: Real-time progress monitoring and reporting
- **Result Correlation**: Advanced correlation analysis across data sources
- **Multiple Output Formats**: JSON, CSV, PDF, HTML export capabilities

## Quick Start

### Basic Usage

```python
from src.orchestration.workflow_templates import phone_investigation_workflow, InvestigationDepth

# Simple phone investigation
result = await phone_investigation_workflow(
    phone_number="+1-555-123-4567",
    depth=InvestigationDepth.BASIC
)

print(f"Cost: ${result['metadata']['total_cost']:.2f}")
print(f"Success Rate: {result['metadata']['success_rate']:.1%}")
```

### With Budget Constraints

```python
from src.orchestration.workflow_templates import WorkflowBudget, person_investigation_workflow

budget = WorkflowBudget(
    max_cost_usd=5.00,
    max_time_minutes=10
)

result = await person_investigation_workflow(
    first_name="John",
    last_name="Smith",
    city="Los Angeles",
    state="CA",
    depth=InvestigationDepth.COMPREHENSIVE,
    budget=budget
)
```

## Investigation Depths

### BASIC
- **Cost**: $0.25 - $2.00 per investigation
- **Time**: 1-5 minutes
- **Scope**: Single primary agent, basic data points
- **Use Case**: Quick verification, initial screening

### COMPREHENSIVE
- **Cost**: $2.50 - $8.00 per investigation
- **Time**: 5-15 minutes
- **Scope**: Multiple agents with cross-referencing
- **Use Case**: Standard investigations, due diligence

### DEEP
- **Cost**: $8.00 - $25.00 per investigation
- **Time**: 15-35 minutes
- **Scope**: Full agent network with correlation analysis
- **Use Case**: Complex investigations, fraud detection

### FORENSIC
- **Cost**: $25.00+ per investigation
- **Time**: 35+ minutes
- **Scope**: Maximum depth with network analysis
- **Use Case**: Legal proceedings, high-stakes investigations

## Available Workflows

### 1. Phone Investigation

Investigate phone numbers with carrier data, owner lookup, and network analysis.

```python
await phone_investigation_workflow(
    phone_number="+1-555-123-4567",
    depth=InvestigationDepth.COMPREHENSIVE
)
```

**Agents Used**:
- Basic: `phone_search_agent`
- Comprehensive: `phone_search_agent`, `person_search_agent`, `email_search_agent`
- Deep: All agents + `business_search_agent`, `address_search_agent`, `data_enrichment_agent`

### 2. Person Investigation

Comprehensive background investigation with multi-source verification.

```python
await person_investigation_workflow(
    first_name="John",
    last_name="Smith",
    city="Los Angeles",
    state="CA",
    depth=InvestigationDepth.DEEP
)
```

**Agents Used**:
- Basic: `person_search_agent`
- Comprehensive: `person_search_agent`, `phone_search_agent`, `email_search_agent`
- Deep: All agents + `business_search_agent`, `address_search_agent`, `analysis_agent`

### 3. Business Due Diligence

Business verification, executive research, and network analysis.

```python
await business_due_diligence_workflow(
    company_name="Acme Corporation",
    city="New York",
    state="NY",
    depth=InvestigationDepth.COMPREHENSIVE
)
```

**Agents Used**:
- Basic: `business_search_agent`
- Comprehensive: `business_search_agent`, `person_search_agent`, `address_search_agent`
- Deep: All agents + network analysis and correlation

### 4. Address Analysis

Property investigation with ownership history and resident analysis.

```python
await address_analysis_workflow(
    street_address="123 Main Street",
    city="Anytown",
    state="CA",
    depth=InvestigationDepth.BASIC
)
```

**Agents Used**:
- Basic: `address_search_agent`
- Comprehensive: `address_search_agent`, `person_search_agent`, `business_search_agent`
- Deep: All agents + historical data and network analysis

### 5. Bulk Processing

High-volume processing with optimized cost and performance.

```python
records = [
    {'first_name': 'John', 'last_name': 'Doe'},
    {'phone_number': '+1-555-123-4567'},
    {'company_name': 'Example Corp'}
]

await bulk_processing_workflow(
    records=records,
    depth=InvestigationDepth.BASIC
)
```

**Features**:
- Optimized parallelization (up to 15 concurrent agents)
- Extended caching (24 hours)
- Cost optimization algorithms
- Progress batching and reporting

## Advanced Features

### Custom Workflows

```python
from src.orchestration.workflow_templates import WorkflowTemplateManager, WorkflowCustomization

orchestrator = SleuthIntelOrchestrator()
manager = WorkflowTemplateManager(orchestrator)

customization = WorkflowCustomization(
    skip_agents=['email_search_agent'],
    additional_agents=['analysis_agent'],
    custom_config={
        'correlation_threshold': 0.95,
        'max_parallel_agents': 8
    }
)

result = await manager.execute_workflow(
    template_type='person_investigation',
    depth='deep',
    query_data={'first_name': 'Jane', 'last_name': 'Doe'},
    customization=customization
)
```

### Progress Tracking

```python
async def progress_callback(update):
    print(f"Progress: {update['progress']:.1%}")
    print(f"Status: {update['status']}")
    if update['errors']:
        print(f"Errors: {len(update['errors'])}")

result = await person_investigation_workflow(
    first_name="John",
    last_name="Smith",
    progress_callback=progress_callback
)
```

### Cost Estimation

```python
manager = WorkflowTemplateManager(orchestrator)

# Estimate before execution
estimate = manager.estimate_workflow_cost(
    template_type='business_due_diligence',
    depth='comprehensive',
    record_count=1
)

print(f"Estimated cost: ${estimate['total_estimated_cost']:.2f}")
```

### Result Correlation

All workflows automatically perform correlation analysis:

```python
result = await person_investigation_workflow(...)

# Access correlations
for correlation in result['results']['correlations']:
    print(f"Correlation: {correlation['correlation_score']:.2f}")
    print(f"Common fields: {correlation['common_fields']}")
```

## Budget Management

### Budget Constraints

```python
budget = WorkflowBudget(
    max_cost_usd=10.00,           # Maximum total cost
    max_time_minutes=15,          # Maximum execution time
    max_credits=100,              # Maximum API credits
    priority_allocation={         # Budget allocation by agent type
        'person_search_agent': 0.4,
        'business_search_agent': 0.3,
        'phone_search_agent': 0.2,
        'email_search_agent': 0.1
    }
)
```

### Cost Optimization

- **Provider Rotation**: Automatically uses most cost-effective providers
- **Caching**: Intelligent caching to avoid duplicate API calls
- **Progressive Depth**: Start basic, upgrade to comprehensive only if needed
- **Parallel Efficiency**: Optimal parallelization to reduce time costs

## Output Formats

### JSON (Default)
Complete structured data with metadata, correlations, and detailed results.

### CSV Summary
Key metrics and summary statistics for spreadsheet analysis.

### PDF Reports
Formatted investigation reports suitable for presentation.

### HTML Dashboard
Interactive web-based results with charts and visualizations.

## Error Handling

### Automatic Retry
- Failed queries automatically retried with exponential backoff
- Provider failover for API quota exhaustion
- Rate limit handling with intelligent queuing

### Partial Results
- Workflows continue even if some agents fail
- Partial success reporting with confidence scores
- Error aggregation and detailed logging

## Performance Optimization

### Caching Strategy
```python
# Long-term caching for bulk operations
customization = WorkflowCustomization(
    custom_config={
        'enable_caching': True,
        'cache_ttl': 86400,  # 24 hours
        'max_parallel_agents': 15
    }
)
```

### Rate Limit Management
- Intelligent rate limiting across all providers
- Queue management for burst requests
- Provider selection based on current limits

### Resource Optimization
- Memory-efficient result streaming
- Configurable parallelization levels
- Dynamic agent pool management

## Example Scripts

### Quick Demos
- `simple_workflow_demo.py` - Basic usage examples
- `workflow_usage_examples.py` - Comprehensive examples with interactive mode

### Advanced Usage
- `advanced_workflow_examples.py` - Adaptive workflows, network analysis, optimization

### Interactive Mode
```bash
python examples/workflow_usage_examples.py interactive
```

## Configuration

### Workflow Templates
Templates are pre-configured but customizable:

```python
# View available templates
manager = WorkflowTemplateManager(orchestrator)
templates = manager.get_available_templates()

for template_type, depths in templates.items():
    print(f"{template_type}:")
    for depth, config in depths.items():
        print(f"  {depth}: {config['description']}")
```

### Environment Setup
Ensure the following are configured:
- API credentials in `SecureAPILocker`
- Required agents are initialized
- Database connections for caching

## Best Practices

### 1. Start Simple
Begin with BASIC depth investigations and upgrade as needed.

### 2. Use Budget Constraints
Always set reasonable budget limits to control costs.

### 3. Monitor Progress
Use progress callbacks for long-running investigations.

### 4. Cache Intelligently
Enable caching for similar investigations, especially bulk processing.

### 5. Handle Errors Gracefully
Check success rates and error logs to improve investigation quality.

### 6. Correlate Results
Review correlation analysis for data verification and discovery.

## Troubleshooting

### Common Issues

**Low Success Rates**
- Check API credentials and quotas
- Verify network connectivity
- Try different data providers

**High Costs**
- Use budget constraints
- Start with BASIC depth
- Enable caching for repeated investigations

**Slow Performance**
- Increase parallelization
- Use appropriate investigation depth
- Check rate limits

**Data Quality Issues**
- Review correlation analysis
- Check data integrity scores
- Use multiple data providers for verification

### Debug Mode
```python
import logging
logging.getLogger('src.orchestration').setLevel(logging.DEBUG)
```

## API Reference

See the docstrings in `workflow_templates.py` for complete API documentation.

Key classes:
- `WorkflowTemplateManager`: Main interface
- `WorkflowBudget`: Budget configuration
- `WorkflowCustomization`: Template customization
- `InvestigationDepth`: Investigation depth levels

Key functions:
- `phone_investigation_workflow()`
- `person_investigation_workflow()`
- `business_due_diligence_workflow()`
- `address_analysis_workflow()`
- `bulk_processing_workflow()`
