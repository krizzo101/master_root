===============
Workflow Design
===============

This guide covers designing and implementing investigation workflows using Sleuth Intel's orchestration system.

Understanding Workflows
=======================

A workflow in Sleuth Intel is a sequence of investigation tasks that are executed by specialized agents. Workflows can be:

* **Sequential**: Tasks execute one after another
* **Parallel**: Multiple tasks execute simultaneously
* **Conditional**: Tasks execute based on conditions
* **Iterative**: Tasks repeat based on results

Basic Workflow Structure
========================

Simple Sequential Workflow
--------------------------

.. code-block:: python

   from sleuth_intel import WorkflowOrchestrator
   from sleuth_intel.agents import PersonSearchAgent, PhoneSearchAgent

   # Create orchestrator
   orchestrator = WorkflowOrchestrator()

   # Define workflow
   workflow = orchestrator.create_workflow("person_investigation")

   # Add sequential tasks
   workflow.add_task(
       agent=PersonSearchAgent(),
       input_mapping={"name": "subject_name"},
       output_key="person_data"
   )

   workflow.add_task(
       agent=PhoneSearchAgent(),
       input_mapping={"phone": "person_data.phone_number"},
       output_key="phone_data"
   )

   # Execute workflow
   results = workflow.execute({"subject_name": "John Doe"})

Parallel Execution
------------------

.. code-block:: python

   from sleuth_intel import ParallelWorkflow

   workflow = ParallelWorkflow("comprehensive_search")

   # Add parallel tasks
   workflow.add_parallel_tasks([
       {
           "agent": PersonSearchAgent(),
           "input": {"name": "John Doe"},
           "output_key": "person_results"
       },
       {
           "agent": BusinessSearchAgent(),
           "input": {"company": "Acme Corp"},
           "output_key": "business_results"
       },
       {
           "agent": AddressSearchAgent(),
           "input": {"address": "123 Main St"},
           "output_key": "address_results"
       }
   ])

   # Execute all tasks in parallel
   results = workflow.execute()

Advanced Workflow Patterns
==========================

Conditional Branching
---------------------

.. code-block:: python

   from sleuth_intel import ConditionalWorkflow

   workflow = ConditionalWorkflow("risk_assessment")

   # Add initial task
   workflow.add_task(
       agent=PersonSearchAgent(),
       output_key="person_data"
   )

   # Add conditional branch
   workflow.add_condition(
       condition=lambda results: results["person_data"]["risk_score"] > 7,
       true_branch=[
           {"agent": CourtRecordsAgent(), "output_key": "court_records"},
           {"agent": FinancialAgent(), "output_key": "financial_data"}
       ],
       false_branch=[
           {"agent": SocialMediaAgent(), "output_key": "social_data"}
       ]
   )

Error Handling and Recovery
---------------------------

.. code-block:: python

   from sleuth_intel import ResilientWorkflow

   workflow = ResilientWorkflow("fault_tolerant_investigation")

   # Configure retry policy
   workflow.set_retry_policy(
       max_retries=3,
       backoff_factor=2.0,
       retry_on_errors=[TimeoutError, ConnectionError]
   )

   # Add fallback strategies
   workflow.add_task_with_fallback(
       primary_agent=EnformionAgent(),
       fallback_agent=PublicRecordsAgent(),
       output_key="subject_data"
   )

   # Add error handler
   workflow.on_error(lambda error, context: {
       "error_type": type(error).__name__,
       "task": context.current_task,
       "timestamp": datetime.now()
   })

Data Transformation
-------------------

.. code-block:: python

   from sleuth_intel import TransformWorkflow

   workflow = TransformWorkflow("data_enrichment")

   # Add task with data transformation
   workflow.add_task(
       agent=PersonSearchAgent(),
       output_key="raw_person_data"
   )

   # Transform data between tasks
   workflow.add_transformation(
       input_key="raw_person_data",
       output_key="formatted_person",
       transform=lambda data: {
           "full_name": f"{data['first_name']} {data['last_name']}",
           "age": calculate_age(data['dob']),
           "addresses": normalize_addresses(data['addresses'])
       }
   )

Workflow Composition
====================

Nested Workflows
----------------

.. code-block:: python

   # Create sub-workflows
   person_workflow = create_person_investigation_workflow()
   business_workflow = create_business_investigation_workflow()

   # Create main workflow
   main_workflow = WorkflowOrchestrator()

   # Compose workflows
   main_workflow.add_sub_workflow(
       workflow=person_workflow,
       input_mapping={"name": "subject_name"},
       output_key="person_investigation"
   )

   main_workflow.add_sub_workflow(
       workflow=business_workflow,
       input_mapping={"company": "person_investigation.employer"},
       output_key="business_investigation"
   )

Dynamic Workflow Generation
---------------------------

.. code-block:: python

   def create_dynamic_workflow(investigation_type, depth=3):
       """Dynamically generate workflow based on investigation type"""

       workflow = WorkflowOrchestrator()

       if investigation_type == "person":
           agents = [PersonSearchAgent(), PhoneSearchAgent(), EmailSearchAgent()]
       elif investigation_type == "business":
           agents = [BusinessSearchAgent(), FinancialAgent(), CourtRecordsAgent()]
       else:
           raise ValueError(f"Unknown investigation type: {investigation_type}")

       # Add agents based on depth
       for i, agent in enumerate(agents[:depth]):
           workflow.add_task(
               agent=agent,
               output_key=f"level_{i}_data"
           )

       return workflow

Real-time Monitoring
====================

Progress Tracking
-----------------

.. code-block:: python

   from sleuth_intel import MonitoredWorkflow

   workflow = MonitoredWorkflow("tracked_investigation")

   # Add progress callback
   workflow.on_progress(lambda progress: {
       print(f"Progress: {progress.completed}/{progress.total} tasks")
       print(f"Current task: {progress.current_task}")
       print(f"Elapsed time: {progress.elapsed_time}")
   })

   # Add task completion callback
   workflow.on_task_complete(lambda task, result: {
       logger.info(f"Task {task.name} completed with {len(result)} results")
   })

Streaming Results
-----------------

.. code-block:: python

   async def stream_investigation():
       """Stream results as they become available"""

       workflow = AsyncWorkflow("streaming_investigation")

       async for result in workflow.stream_execute(input_data):
           # Process results in real-time
           await process_result(result)

           # Send to webhook
           await send_webhook(result)

Best Practices
==============

1. **Design for Idempotency**: Ensure workflows can be safely re-run
2. **Use Caching**: Cache intermediate results to avoid redundant API calls
3. **Implement Circuit Breakers**: Prevent cascading failures
4. **Log Everything**: Comprehensive logging for debugging and audit
5. **Version Your Workflows**: Track workflow versions for reproducibility
6. **Test Incrementally**: Test each component before composing
7. **Monitor Performance**: Track execution time and resource usage
8. **Handle Rate Limits**: Respect API rate limits with proper throttling
9. **Validate Inputs**: Validate all inputs before workflow execution
10. **Document Dependencies**: Clearly document agent dependencies

Example: Fraud Detection Workflow
==================================

.. code-block:: python

   def create_fraud_detection_workflow():
       """Complete fraud detection workflow example"""

       workflow = WorkflowOrchestrator(
           name="fraud_detection",
           description="Comprehensive fraud risk assessment"
       )

       # Phase 1: Identity Verification
       workflow.add_phase("identity_verification", [
           {"agent": PersonSearchAgent(), "output": "person_data"},
           {"agent": PhoneSearchAgent(), "output": "phone_data"},
           {"agent": EmailSearchAgent(), "output": "email_data"}
       ])

       # Phase 2: Background Check
       workflow.add_phase("background_check", [
           {"agent": CourtRecordsAgent(), "output": "court_records"},
           {"agent": FinancialAgent(), "output": "financial_data"},
           {"agent": AddressSearchAgent(), "output": "address_history"}
       ])

       # Phase 3: Risk Analysis
       workflow.add_phase("risk_analysis", [
           {"agent": RiskScoringAgent(), "output": "risk_score"},
           {"agent": PatternAnalysisAgent(), "output": "patterns"},
           {"agent": AnomalyDetectionAgent(), "output": "anomalies"}
       ])

       # Phase 4: Report Generation
       workflow.add_phase("reporting", [
           {"agent": ReportGeneratorAgent(), "output": "final_report"}
       ])

       # Configure execution strategy
       workflow.configure(
           parallel_phases=False,
           parallel_tasks_within_phase=True,
           continue_on_error=True,
           timeout_seconds=300
       )

       return workflow

Performance Optimization
========================

Caching Strategy
----------------

.. code-block:: python

   workflow.configure_cache(
       enable=True,
       ttl_seconds=3600,
       cache_key_strategy="hash",
       shared_cache=True
   )

Resource Management
-------------------

.. code-block:: python

   workflow.configure_resources(
       max_concurrent_tasks=10,
       max_memory_mb=1024,
       cpu_limit=2.0,
       gpu_required=False
   )

Batch Processing
----------------

.. code-block:: python

   workflow.configure_batching(
       batch_size=100,
       batch_timeout_seconds=30,
       parallel_batches=4
   )
