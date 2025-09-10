# Sleuth Intel - Multi-Agent System Architecture

## 🏗️ System Overview

Sleuth Intel implements a sophisticated multi-agent architecture using the proven GenericOrchestrator pattern for intelligence gathering, data enrichment, and investigation workflows.

## 🧠 Agent Specifications

### Core Intelligence Agents

#### 1. PersonSearchAgent
**Role**: Individual identity lookup and verification
**Capabilities**:
- Name-based person search with fuzzy matching
- Age range filtering and demographic analysis
- Address history compilation
- Associate and relative discovery
- Identity confidence scoring

**EnformionGO Integration**: `/person-search` endpoint
**Credit Cost**: 1 credit per search

#### 2. PhoneSearchAgent
**Role**: Phone number intelligence specialist
**Capabilities**:
- Reverse phone number lookup
- Carrier identification and line type detection
- Owner verification and contact validation
- Phone number history and portability tracking
- Spam/fraud risk assessment

**EnformionGO Integration**: `/phone-search` endpoint
**Credit Cost**: 1-2 credits based on detail level

#### 3. EmailSearchAgent
**Role**: Email address validation and reverse lookup
**Capabilities**:
- Email address validation and deliverability testing
- Associated person profile discovery
- Social media profile correlation
- Domain analysis and business affiliation
- Email breach and compromise detection

**EnformionGO Integration**: `/email-search` endpoint
**Credit Cost**: 1-2 credits

#### 4. AddressSearchAgent
**Role**: Location-based intelligence gathering
**Capabilities**:
- Current and historical resident identification
- Property ownership and value analysis
- Neighborhood demographic profiling
- Move pattern analysis
- Address validation and standardization

**EnformionGO Integration**: `/address-search` endpoint
**Credit Cost**: 1 credit

#### 5. BusinessSearchAgent
**Role**: Corporate and business intelligence
**Capabilities**:
- Business entity verification and details
- Principal and executive identification
- Corporate filing and registration analysis
- Business relationship mapping
- Industry classification and analysis

**EnformionGO Integration**: `/business-search` endpoint
**Credit Cost**: 2-3 credits

#### 6. DataEnrichmentAgent
**Role**: Contact data enhancement and validation
**Capabilities**:
- Multi-source data consolidation
- Contact information verification
- Data quality scoring and confidence assessment
- Missing data inference and completion
- Duplicate detection and deduplication

**Integration**: Cross-endpoint aggregation and validation
**Credit Cost**: Variable based on operations

### Specialized Analysis Agents

#### 7. AnalysisAgent
**Role**: Results aggregation and intelligence synthesis
**Capabilities**:
- Multi-source data correlation
- Pattern recognition and anomaly detection
- Confidence scoring and reliability assessment
- Report generation and visualization
- Risk assessment and flagging

#### 8. ValidationAgent
**Role**: Data quality assurance and verification
**Capabilities**:
- Cross-reference validation across multiple sources
- Data consistency checking
- Accuracy scoring and confidence metrics
- Error detection and data cleaning
- Compliance verification (FCRA, privacy)

## 🎯 Orchestrator Design

### Generic Orchestrator Integration

```python
# Core orchestrator configuration
orchestrator = GenericOrchestrator(
    output_dir=Path("sleuth_intel_operations"),
    max_parallel=3,  # Optimal for API rate limits
    use_optimizations=True,
    token_pool_size=19+  # Leverage existing token pool
)
```

### Task Routing Logic

**Single-Source Lookup Pattern**:
```
input_validation → specific_agent → result_validation → report
```

**Multi-Source Enrichment Pattern**:
```
                  ┌→ person_search ┐
input_validation → phone_search   → data_enrichment → analysis → report
                  └→ email_search ┘
```

**Investigation Workflow Pattern**:
```
initial_search → lead_discovery → deep_analysis → correlation → final_report
```

**Bulk Processing Pattern**:
```
batch_validation → [parallel_agents] → result_aggregation → bulk_report
```

## ⚡ Execution Patterns

### 1. Direct Lookup Execution

**Use Case**: Single data point verification
**Pattern**: `setup → agent_execution → validation → report`
**Example**: Phone number owner identification

```python
def generate_phone_lookup_tasks(phone_number):
    return [
        AgentTask(
            task_id="validate_input",
            task_type="validation",
            prompt=f"Validate phone number format: {phone_number}",
            dependencies=[]
        ),
        AgentTask(
            task_id="phone_search",
            task_type="intelligence",
            prompt=f"Perform comprehensive phone lookup for {phone_number}",
            dependencies=["validate_input"]
        ),
        AgentTask(
            task_id="generate_report",
            task_type="reporting",
            prompt="Generate phone lookup report with findings",
            dependencies=["phone_search"]
        )
    ]
```

### 2. Multi-Source Intelligence Gathering

**Use Case**: Comprehensive person investigation
**Pattern**: `setup → [parallel_agents] → correlation → analysis → report`

```python
def generate_person_investigation_tasks(person_name, location=None):
    return [
        AgentTask(
            task_id="setup_investigation",
            task_type="setup",
            prompt=f"Initialize investigation for {person_name}",
            dependencies=[]
        ),
        AgentTask(
            task_id="person_search",
            task_type="intelligence",
            prompt=f"PersonSearchAgent: Find all records for {person_name}",
            dependencies=["setup_investigation"]
        ),
        AgentTask(
            task_id="phone_discovery",
            task_type="intelligence",
            prompt="PhoneSearchAgent: Investigate all discovered phone numbers",
            dependencies=["person_search"]
        ),
        AgentTask(
            task_id="email_discovery",
            task_type="intelligence",
            prompt="EmailSearchAgent: Investigate all discovered email addresses",
            dependencies=["person_search"]
        ),
        AgentTask(
            task_id="address_history",
            task_type="intelligence",
            prompt="AddressSearchAgent: Analyze address history and associations",
            dependencies=["person_search"]
        ),
        AgentTask(
            task_id="data_correlation",
            task_type="analysis",
            prompt="AnalysisAgent: Correlate all intelligence findings",
            dependencies=["phone_discovery", "email_discovery", "address_history"]
        ),
        AgentTask(
            task_id="final_report",
            task_type="reporting",
            prompt="Generate comprehensive investigation report",
            dependencies=["data_correlation"]
        )
    ]
```

### 3. Business Intelligence Workflow

**Use Case**: Corporate due diligence
**Pattern**: `business_search → principal_analysis → relationship_mapping → risk_assessment`

```python
def generate_business_intelligence_tasks(business_name):
    return [
        AgentTask(
            task_id="business_search",
            task_type="intelligence",
            prompt=f"BusinessSearchAgent: Complete analysis of {business_name}",
            dependencies=[]
        ),
        AgentTask(
            task_id="principal_investigation",
            task_type="intelligence",
            prompt="PersonSearchAgent: Investigate all identified principals",
            dependencies=["business_search"]
        ),
        AgentTask(
            task_id="relationship_mapping",
            task_type="analysis",
            prompt="AnalysisAgent: Map business relationships and connections",
            dependencies=["principal_investigation"]
        ),
        AgentTask(
            task_id="risk_assessment",
            task_type="analysis",
            prompt="ValidationAgent: Assess business and principal risks",
            dependencies=["relationship_mapping"]
        ),
        AgentTask(
            task_id="due_diligence_report",
            task_type="reporting",
            prompt="Generate comprehensive due diligence report",
            dependencies=["risk_assessment"]
        )
    ]
```

## 🔧 Integration Architecture

### Secure Credential Management

```python
# Integration with existing SecureAPILocker
from src.core.secure_api_locker import api_locker_manager

class SleuthIntelAgent:
    def __init__(self):
        self.credentials = api_locker_manager.get_credential("enformion")
        self.rate_limiter = RateLimiter(self.credentials.rate_limit)

    async def execute_search(self, endpoint, parameters):
        # Rate limit management
        await self.rate_limiter.acquire()

        # API call with secure credentials
        result = await self.api_client.request(endpoint, parameters)

        # Credit usage tracking
        self.track_credit_usage(result.credits_used)

        return result
```

### Rate Limit Management

```python
class DistributedRateLimiter:
    """Manages rate limits across multiple agents"""

    def __init__(self, max_requests_per_minute=100):
        self.semaphore = asyncio.Semaphore(max_requests_per_minute)
        self.request_times = deque()

    async def acquire(self):
        # Remove requests older than 1 minute
        current_time = time.time()
        while self.request_times and current_time - self.request_times[0] > 60:
            self.request_times.popleft()

        # Wait if at limit
        if len(self.request_times) >= self.max_requests:
            sleep_time = 60 - (current_time - self.request_times[0])
            await asyncio.sleep(sleep_time)

        self.request_times.append(current_time)
        await self.semaphore.acquire()
```

### Error Handling and Recovery

```python
class ResilientAgent:
    """Base agent with comprehensive error handling"""

    async def execute_with_retry(self, operation, max_retries=3):
        for attempt in range(max_retries):
            try:
                return await operation()
            except RateLimitError:
                # Exponential backoff for rate limits
                await asyncio.sleep(2 ** attempt)
            except AuthenticationError:
                # Refresh credentials and retry
                await self.refresh_credentials()
            except APIError as e:
                if e.is_retryable():
                    await asyncio.sleep(1)  # Brief pause for transient errors
                else:
                    raise  # Don't retry non-retryable errors

        raise MaxRetriesExceededError()
```

## 📊 Performance Optimization

### Credit Usage Optimization

**Strategy 1: Smart Query Planning**
- Analyze query to determine minimum required endpoints
- Use cached results when available
- Prioritize high-confidence, low-cost searches

**Strategy 2: Batch Processing**
- Group similar queries for bulk processing
- Implement request deduplication
- Use parallel processing within rate limits

**Strategy 3: Result Caching**
- Cache results by query parameters
- Implement TTL-based cache expiration
- Share cache across agent instances

### Parallel Processing Configuration

```python
# Optimal parallel configuration based on API limits
PARALLEL_CONFIG = {
    "starter_plan": {
        "max_parallel": 2,
        "rate_limit": "10/minute",
        "monthly_limit": 1000
    },
    "pro_plan": {
        "max_parallel": 5,
        "rate_limit": "100/minute",
        "monthly_limit": 10000
    },
    "enterprise_plan": {
        "max_parallel": 10,
        "rate_limit": "custom",
        "monthly_limit": "unlimited"
    }
}
```

## 🔍 Agent Communication Patterns

### Message Bus Architecture

```python
class AgentMessageBus:
    """Facilitates communication between agents"""

    def __init__(self):
        self.channels = defaultdict(list)
        self.subscribers = defaultdict(set)

    async def publish(self, channel, message):
        """Publish message to channel"""
        for subscriber in self.subscribers[channel]:
            await subscriber.handle_message(message)

    async def subscribe(self, agent, channel):
        """Subscribe agent to channel"""
        self.subscribers[channel].add(agent)
```

### Data Sharing Protocol

```python
class SharedIntelligence:
    """Shared data store for agent collaboration"""

    def __init__(self):
        self.cache = {}
        self.confidence_scores = {}
        self.source_tracking = {}

    def store_result(self, query_key, result, source_agent, confidence):
        """Store result with metadata"""
        self.cache[query_key] = result
        self.confidence_scores[query_key] = confidence
        self.source_tracking[query_key] = source_agent

    def get_best_result(self, query_key):
        """Get highest confidence result"""
        if query_key in self.cache:
            return {
                "result": self.cache[query_key],
                "confidence": self.confidence_scores[query_key],
                "source": self.source_tracking[query_key]
            }
        return None
```

## 🎯 Quality Assurance

### Result Validation Pipeline

1. **Data Consistency Check** - Verify data across sources
2. **Confidence Scoring** - Assign reliability scores
3. **Anomaly Detection** - Flag unusual patterns
4. **Completeness Assessment** - Identify missing data
5. **Compliance Verification** - Ensure regulatory compliance

### Monitoring and Analytics

```python
class OperationalMetrics:
    """Track system performance and usage"""

    def __init__(self):
        self.metrics = {
            "api_calls_made": 0,
            "credits_consumed": 0,
            "success_rate": 0.0,
            "average_response_time": 0.0,
            "error_rate": 0.0
        }

    def record_operation(self, agent_name, duration, credits_used, success):
        """Record individual operation metrics"""
        self.metrics["api_calls_made"] += 1
        self.metrics["credits_consumed"] += credits_used
        # Update running averages...
```

This architecture provides a robust, scalable foundation for comprehensive intelligence gathering operations while maintaining optimal performance and cost efficiency.
