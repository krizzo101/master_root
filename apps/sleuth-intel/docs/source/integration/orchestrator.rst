=======================
Orchestrator Integration
=======================

This guide covers integrating Sleuth Intel with the Agent Orchestrator system for coordinated multi-agent investigations.

Overview
========

The Orchestrator integration enables:

* **Coordinated Execution**: Multiple agents working together
* **Resource Management**: Optimal resource allocation
* **State Management**: Persistent workflow state
* **Event Streaming**: Real-time progress updates
* **Error Recovery**: Automatic failure handling

Basic Integration
=================

Setting Up the Orchestrator
----------------------------

.. code-block:: python

   from sleuth_intel.orchestration import SleuthOrchestrator
   from agent_orchestrator import AgentOrchestrator

   # Initialize orchestrators
   agent_orchestrator = AgentOrchestrator(
       workspace="investigation_workspace",
       max_agents=10
   )

   sleuth_orchestrator = SleuthOrchestrator(
       agent_orchestrator=agent_orchestrator,
       config={
           "max_concurrent_investigations": 5,
           "timeout_seconds": 300,
           "enable_caching": True
       }
   )

Registering Agents
------------------

.. code-block:: python

   from sleuth_intel.agents import PersonSearchAgent, PhoneSearchAgent

   # Register Sleuth Intel agents with orchestrator
   sleuth_orchestrator.register_agent(
       PersonSearchAgent(name="person_investigator"),
       capabilities=["person_search", "identity_verification"],
       resource_requirements={"memory": "512MB", "cpu": 0.5}
   )

   sleuth_orchestrator.register_agent(
       PhoneSearchAgent(name="phone_investigator"),
       capabilities=["phone_lookup", "carrier_info"],
       resource_requirements={"memory": "256MB", "cpu": 0.25}
   )

Creating Investigation Workflows
================================

Sequential Investigation
------------------------

.. code-block:: python

   # Define investigation workflow
   investigation = sleuth_orchestrator.create_investigation(
       name="comprehensive_person_search",
       description="Full background investigation"
   )

   # Add investigation phases
   investigation.add_phase("identity", [
       {
           "agent": "person_investigator",
           "task": "search_person",
           "input": {"name": "John Doe", "location": "New York"}
       }
   ])

   investigation.add_phase("contact_verification", [
       {
           "agent": "phone_investigator",
           "task": "verify_phone",
           "input": {"phone": "${identity.phone_number}"}
       }
   ])

   # Execute investigation
   results = await investigation.execute()

Parallel Investigation
----------------------

.. code-block:: python

   # Create parallel investigation workflow
   parallel_investigation = sleuth_orchestrator.create_parallel_investigation(
       name="multi_source_search"
   )

   # Add parallel tasks
   tasks = [
       ("person_investigator", {"name": "John Doe"}),
       ("business_investigator", {"company": "Acme Corp"}),
       ("address_investigator", {"address": "123 Main St"})
   ]

   for agent_name, input_data in tasks:
       parallel_investigation.add_task(
           agent=agent_name,
           input=input_data,
           timeout=60
       )

   # Execute all tasks in parallel
   results = await parallel_investigation.execute_parallel()

Advanced Integration Features
=============================

Message Bus Integration
-----------------------

.. code-block:: python

   from sleuth_intel.orchestration import MessageBusIntegration

   # Configure message bus
   message_bus = MessageBusIntegration(
       broker_url="redis://localhost:6379",
       topic="investigations"
   )

   # Subscribe to investigation events
   @message_bus.on("investigation.started")
   async def on_investigation_start(event):
       print(f"Investigation {event.id} started")

   @message_bus.on("investigation.completed")
   async def on_investigation_complete(event):
       print(f"Investigation {event.id} completed with {len(event.results)} results")

   # Connect message bus to orchestrator
   sleuth_orchestrator.connect_message_bus(message_bus)

State Persistence
-----------------

.. code-block:: python

   from sleuth_intel.orchestration import StatePersistence

   # Configure state persistence
   state_manager = StatePersistence(
       backend="postgresql",
       connection_string="postgresql://user:pass@localhost/sleuth_db"
   )

   # Enable checkpointing
   sleuth_orchestrator.enable_checkpointing(
       state_manager=state_manager,
       checkpoint_interval=10,  # Checkpoint every 10 tasks
       recovery_mode="continue"  # Continue from last checkpoint on failure
   )

Resource Allocation
-------------------

.. code-block:: python

   from sleuth_intel.orchestration import ResourceManager

   # Configure resource limits
   resource_manager = ResourceManager(
       max_memory="4GB",
       max_cpu_cores=8,
       max_concurrent_agents=20
   )

   # Set resource policies
   resource_manager.set_policy(
       agent_type="PersonSearchAgent",
       max_instances=5,
       memory_limit="512MB",
       cpu_limit=1.0
   )

   # Attach to orchestrator
   sleuth_orchestrator.set_resource_manager(resource_manager)

Quality Gates Integration
=========================

Defining Quality Gates
----------------------

.. code-block:: python

   from sleuth_intel.orchestration import QualityGate

   # Define quality gate for data validation
   data_quality_gate = QualityGate(
       name="data_validation",
       description="Validate investigation data quality"
   )

   # Add validation rules
   data_quality_gate.add_rule(
       name="completeness_check",
       condition=lambda result: result.get("completeness_score", 0) > 0.8,
       error_message="Data completeness below threshold"
   )

   data_quality_gate.add_rule(
       name="accuracy_check",
       condition=lambda result: result.get("confidence_score", 0) > 0.7,
       error_message="Confidence score too low"
   )

   # Apply to investigation
   investigation.add_quality_gate(data_quality_gate)

Performance Gates
-----------------

.. code-block:: python

   # Define performance quality gate
   performance_gate = QualityGate(
       name="performance_check",
       description="Ensure performance requirements"
   )

   performance_gate.add_rule(
       name="response_time",
       condition=lambda metrics: metrics["response_time_ms"] < 5000,
       error_message="Response time exceeded 5 seconds"
   )

   performance_gate.add_rule(
       name="api_calls",
       condition=lambda metrics: metrics["api_calls"] < 100,
       error_message="Too many API calls"
   )

Custom Orchestrator Agents
==========================

Creating Custom Agents
----------------------

.. code-block:: python

   from sleuth_intel.orchestration import OrchestratorAgent
   from sleuth_intel.agents import BaseAgent

   class CustomInvestigationAgent(BaseAgent, OrchestratorAgent):
       """Custom agent with orchestrator integration"""

       def __init__(self, name, orchestrator):
           super().__init__(name=name)
           self.orchestrator = orchestrator

       async def execute(self, input_data):
           # Report progress to orchestrator
           await self.report_progress(0, "Starting investigation")

           # Perform investigation
           results = await self._investigate(input_data)

           # Check with orchestrator for next steps
           next_tasks = await self.orchestrator.get_next_tasks(results)

           if next_tasks:
               # Delegate to other agents
               delegated_results = await self.delegate_tasks(next_tasks)
               results.update(delegated_results)

           # Report completion
           await self.report_progress(100, "Investigation complete")
           return results

Agent Communication
-------------------

.. code-block:: python

   # Enable inter-agent communication
   sleuth_orchestrator.enable_agent_communication()

   class CollaborativeAgent(BaseAgent):
       async def execute(self, input_data):
           # Request data from another agent
           person_data = await self.request_from_agent(
               agent_name="person_investigator",
               request={"name": input_data["subject"]}
           )

           # Share results with other agents
           await self.broadcast_to_agents(
               event="data_available",
               data={"person_id": person_data["id"]}
           )

           return self.process_with_shared_data(person_data)

Event-Driven Orchestration
===========================

Event Handlers
--------------

.. code-block:: python

   # Define event-driven workflow
   event_workflow = sleuth_orchestrator.create_event_workflow(
       name="reactive_investigation"
   )

   # Register event handlers
   @event_workflow.on("new_person_detected")
   async def handle_new_person(event):
       # Trigger person investigation
       return await sleuth_orchestrator.trigger_investigation(
           agent="person_investigator",
           input={"person_id": event.data["person_id"]}
       )

   @event_workflow.on("risk_threshold_exceeded")
   async def handle_high_risk(event):
       # Trigger deep investigation
       return await sleuth_orchestrator.trigger_deep_investigation(
           subject=event.data["subject"],
           depth=5
       )

Stream Processing
-----------------

.. code-block:: python

   # Set up stream processing
   stream_processor = sleuth_orchestrator.create_stream_processor(
       source="kafka://localhost:9092/investigations"
   )

   @stream_processor.process
   async def process_investigation_stream(record):
       # Process each record
       result = await sleuth_orchestrator.quick_investigate(record)

       # Filter and route
       if result["risk_score"] > 7:
           await stream_processor.route_to("high_risk_queue", result)
       else:
           await stream_processor.route_to("standard_queue", result)

Monitoring and Metrics
======================

Orchestrator Metrics
--------------------

.. code-block:: python

   # Enable metrics collection
   sleuth_orchestrator.enable_metrics(
       backend="prometheus",
       endpoint="http://localhost:9090"
   )

   # Custom metrics
   sleuth_orchestrator.register_metric(
       name="investigation_duration",
       type="histogram",
       description="Investigation completion time",
       buckets=[1, 5, 10, 30, 60, 120, 300]
   )

   # Track custom events
   with sleuth_orchestrator.track_metric("investigation_duration"):
       results = await investigation.execute()

Dashboard Integration
---------------------

.. code-block:: python

   # Configure dashboard
   dashboard = sleuth_orchestrator.create_dashboard(
       title="Investigation Monitor",
       refresh_interval=5
   )

   # Add widgets
   dashboard.add_widget(
       type="gauge",
       title="Active Investigations",
       metric="active_investigations_count"
   )

   dashboard.add_widget(
       type="line_chart",
       title="Investigation Rate",
       metric="investigations_per_minute",
       time_range="1h"
   )

Best Practices
==============

1. **Use Checkpointing**: Enable checkpointing for long-running investigations
2. **Set Resource Limits**: Define appropriate resource limits for each agent
3. **Implement Circuit Breakers**: Prevent cascade failures
4. **Monitor Performance**: Track key metrics and set up alerts
5. **Version Workflows**: Version your investigation workflows
6. **Test Failover**: Regularly test failure recovery mechanisms
7. **Document Dependencies**: Clearly document agent dependencies
8. **Use Caching**: Leverage orchestrator's distributed cache
9. **Implement Retry Logic**: Configure appropriate retry strategies
10. **Log Comprehensively**: Enable detailed logging for debugging

Example: Complete Integration
=============================

.. code-block:: python

   async def setup_complete_orchestration():
       """Complete orchestrator integration example"""

       # Initialize components
       orchestrator = AgentOrchestrator(workspace="investigations")
       sleuth = SleuthOrchestrator(orchestrator)

       # Register all agents
       agents = [
           PersonSearchAgent("person_agent"),
           BusinessSearchAgent("business_agent"),
           FinancialAgent("financial_agent"),
           RiskAnalysisAgent("risk_agent")
       ]

       for agent in agents:
           sleuth.register_agent(agent)

       # Create comprehensive workflow
       workflow = sleuth.create_workflow("comprehensive_investigation")

       # Add phases with dependencies
       workflow.add_phase("data_gathering", parallel=True)
       workflow.add_phase("analysis", depends_on=["data_gathering"])
       workflow.add_phase("risk_assessment", depends_on=["analysis"])
       workflow.add_phase("reporting", depends_on=["risk_assessment"])

       # Configure quality gates
       workflow.add_quality_gate(
           phase="analysis",
           gate=QualityGate("data_quality", min_score=0.8)
       )

       # Set up monitoring
       workflow.enable_monitoring(
           metrics=True,
           tracing=True,
           logging=True
       )

       # Execute with error handling
       try:
           results = await workflow.execute(
               input_data={"subject": "John Doe"},
               timeout=300
           )
           return results
       except Exception as e:
           await workflow.rollback()
           raise
