============
Architecture
============

This document provides a comprehensive overview of the Sleuth Intel architecture, design patterns, and core components.

System Overview
===============

Sleuth Intel is built on a modular, agent-based architecture that enables:

* **Scalability**: Horizontal scaling through distributed agent execution
* **Extensibility**: Easy addition of new agents and providers
* **Reliability**: Fault tolerance and automatic recovery
* **Performance**: Asynchronous processing and intelligent caching
* **Security**: Encrypted credential storage and secure API communication

.. code-block:: text

   ┌─────────────────────────────────────────────────────────────┐
   │                      Client Application                      │
   └──────────────────────┬──────────────────────────────────────┘
                          │
   ┌──────────────────────▼──────────────────────────────────────┐
   │                 Orchestration Layer                          │
   │  ┌──────────────────────────────────────────────────────┐  │
   │  │           WorkflowOrchestrator                       │  │
   │  │  ┌────────────┐  ┌────────────┐  ┌────────────┐   │  │
   │  │  │  Scheduler │  │   Router   │  │  Executor  │   │  │
   │  │  └────────────┘  └────────────┘  └────────────┘   │  │
   │  └──────────────────────────────────────────────────────┘  │
   └──────────────────────┬──────────────────────────────────────┘
                          │
   ┌──────────────────────▼──────────────────────────────────────┐
   │                      Agent Layer                             │
   │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
   │  │  Person  │  │  Phone   │  │  Email   │  │ Business │  │
   │  │  Agent   │  │  Agent   │  │  Agent   │  │  Agent   │  │
   │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
   └──────────────────────┬──────────────────────────────────────┘
                          │
   ┌──────────────────────▼──────────────────────────────────────┐
   │                    Provider Layer                            │
   │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
   │  │Enformion │  │  Public  │  │  Social  │  │ Financial│  │
   │  │   API    │  │  Records │  │  Media   │  │   APIs   │  │
   │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
   └──────────────────────────────────────────────────────────────┘

Core Components
===============

Orchestration Layer
-------------------

The orchestration layer manages workflow execution and agent coordination:

**WorkflowOrchestrator**
  Central component that coordinates agent execution, manages dependencies, and handles result aggregation.

**TaskScheduler**
  Schedules tasks based on dependencies, priorities, and resource availability.

**ResultAggregator**
  Combines results from multiple agents into coherent investigation reports.

**StateManager**
  Maintains workflow state, handles checkpointing, and enables recovery.

Agent Layer
-----------

Agents are specialized components for specific investigation tasks:

**BaseAgent**
  Abstract base class providing common functionality:

  * Rate limiting and throttling
  * Retry logic with exponential backoff
  * Caching and memoization
  * Metrics collection
  * Error handling

**Specialized Agents**
  Each agent extends BaseAgent with domain-specific logic:

  * PersonSearchAgent: Personal information searches
  * BusinessSearchAgent: Company and business entity searches
  * PhoneSearchAgent: Phone number lookups and validation
  * EmailSearchAgent: Email address verification and analysis
  * AddressSearchAgent: Physical address and property searches
  * SocialMediaAgent: Social media profile discovery
  * FinancialAgent: Financial records and asset searches
  * CourtRecordsAgent: Legal and court record searches

Provider Layer
--------------

Providers interface with external data sources:

**APIProvider**
  Base class for API-based data providers with:

  * Authentication management
  * Request/response handling
  * Rate limit compliance
  * Error translation

**DataProviders**
  Specific implementations for each data source:

  * EnformionProvider: Enformion API integration
  * PublicRecordsProvider: Public records databases
  * SocialMediaProvider: Social media APIs
  * FinancialProvider: Financial data services

Design Patterns
===============

Agent Pattern
-------------

Each agent follows a consistent pattern:

.. code-block:: python

   class InvestigationAgent(BaseAgent):
       def __init__(self, config):
           super().__init__(config)
           self.provider = self._initialize_provider()

       def execute(self, input_data):
           # Validate input
           self.validate_input(input_data)

           # Check cache
           if cached := self.cache.get(input_data):
               return cached

           # Execute with rate limiting
           with self.rate_limiter:
               result = self._perform_search(input_data)

           # Cache and return
           self.cache.set(input_data, result)
           return result

Pipeline Pattern
----------------

Workflows use a pipeline pattern for data transformation:

.. code-block:: python

   pipeline = Pipeline()
   pipeline.add_stage(DataValidation())
   pipeline.add_stage(DataEnrichment())
   pipeline.add_stage(DataNormalization())
   pipeline.add_stage(ResultAggregation())

   result = pipeline.execute(input_data)

Observer Pattern
----------------

Event-driven architecture for monitoring:

.. code-block:: python

   orchestrator.on("task_complete", handle_completion)
   orchestrator.on("error", handle_error)
   orchestrator.on("progress", update_progress)

Data Flow
=========

Request Processing
------------------

1. **Input Reception**: Client submits investigation request
2. **Validation**: Input validated against schema
3. **Planning**: Orchestrator creates execution plan
4. **Distribution**: Tasks distributed to agents
5. **Execution**: Agents query providers
6. **Aggregation**: Results combined
7. **Output**: Final report delivered

Caching Strategy
----------------

Multi-level caching for optimal performance:

.. code-block:: text

   Level 1: In-Memory Cache (LRU, 5 min TTL)
      ↓ (miss)
   Level 2: Redis Cache (1 hour TTL)
      ↓ (miss)
   Level 3: Database Cache (24 hour TTL)
      ↓ (miss)
   External API Call

Error Handling
--------------

Comprehensive error handling strategy:

.. code-block:: text

   Try Operation
      ↓
   Transient Error? → Yes → Retry with Backoff
      ↓ No                    ↓ (max retries)
   Permanent Error          Log and Fallback
      ↓                       ↓
   Circuit Breaker         Alternative Provider
      ↓                       ↓
   Error Response          Degraded Result

Security Architecture
=====================

Credential Management
---------------------

**Secure Storage**
  * Encrypted credential vault
  * Key rotation support
  * Audit logging

**Access Control**
  * Role-based permissions
  * API key management
  * Token refresh handling

Data Protection
---------------

**Encryption**
  * TLS for all API communication
  * At-rest encryption for cached data
  * Sensitive field masking

**Privacy**
  * PII detection and handling
  * Data retention policies
  * GDPR compliance features

Scalability
===========

Horizontal Scaling
------------------

.. code-block:: yaml

   # Docker Compose scaling example
   services:
     agent:
       image: sleuth-intel-agent
       deploy:
         replicas: 10

     orchestrator:
       image: sleuth-intel-orchestrator
       deploy:
         replicas: 3

     cache:
       image: redis:alpine
       deploy:
         replicas: 2

Load Balancing
--------------

* Round-robin agent selection
* Least-connections routing
* Health check based routing
* Geographic distribution

Performance Optimization
========================

Async Processing
----------------

.. code-block:: python

   async def parallel_investigation():
       tasks = [
           agent1.execute_async(data1),
           agent2.execute_async(data2),
           agent3.execute_async(data3)
       ]
       results = await asyncio.gather(*tasks)
       return aggregate_results(results)

Connection Pooling
------------------

.. code-block:: python

   # HTTP connection pooling
   session = aiohttp.ClientSession(
       connector=aiohttp.TCPConnector(
           limit=100,
           limit_per_host=10
       )
   )

Resource Management
-------------------

* Memory-mapped file caching
* Lazy loading of large datasets
* Stream processing for bulk operations
* Resource pooling and recycling

Monitoring and Observability
============================

Metrics Collection
------------------

**Application Metrics**
  * Request rate and latency
  * Cache hit/miss ratios
  * Agent performance stats
  * Error rates and types

**System Metrics**
  * CPU and memory usage
  * Network I/O
  * Disk usage
  * Thread pool stats

Logging Strategy
----------------

.. code-block:: python

   # Structured logging
   logger.info("investigation_complete", extra={
       "investigation_id": investigation_id,
       "duration_ms": duration,
       "agent_count": len(agents),
       "result_count": len(results),
       "cache_hits": cache_hits
   })

Tracing
-------

Distributed tracing for request flow:

.. code-block:: python

   with tracer.start_span("investigation") as span:
       span.set_tag("investigation.type", "person")
       span.set_tag("investigation.depth", 3)

       with tracer.start_span("agent.execution", child_of=span):
           result = agent.execute(data)

Deployment Architecture
=======================

Container Architecture
----------------------

.. code-block:: dockerfile

   # Multi-stage build
   FROM python:3.9-slim as builder
   WORKDIR /build
   COPY requirements.txt .
   RUN pip install --user -r requirements.txt

   FROM python:3.9-slim
   WORKDIR /app
   COPY --from=builder /root/.local /root/.local
   COPY . .
   CMD ["python", "-m", "sleuth_intel"]

Kubernetes Deployment
---------------------

.. code-block:: yaml

   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: sleuth-intel
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: sleuth-intel
     template:
       metadata:
         labels:
           app: sleuth-intel
       spec:
         containers:
         - name: app
           image: sleuth-intel:latest
           resources:
             requests:
               memory: "256Mi"
               cpu: "250m"
             limits:
               memory: "512Mi"
               cpu: "500m"
