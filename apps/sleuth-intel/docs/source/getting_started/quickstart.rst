==========
Quickstart
==========

Get up and running with Sleuth Intel in 5 minutes. This guide covers the essentials to start your first investigation.

Installation
============

.. code-block:: bash

   # Install via pip
   pip install sleuth-intel

   # Or install with all features
   pip install sleuth-intel[all]

Basic Configuration
===================

Create a configuration file:

.. code-block:: python

   # config.py
   SLEUTH_CONFIG = {
       "api_keys": {
           "enformion": "your-api-key-here",
           "other_provider": "another-api-key"
       },
       "rate_limits": {
           "requests_per_second": 10,
           "requests_per_minute": 100
       },
       "cache": {
           "enabled": True,
           "ttl_seconds": 3600
       }
   }

Your First Investigation
========================

Simple Person Search
--------------------

.. code-block:: python

   from sleuth_intel import QuickSearch

   # Initialize quick search
   searcher = QuickSearch()

   # Search for a person
   results = searcher.find_person(
       name="John Doe",
       location="New York, NY"
   )

   # Display results
   print(f"Found {len(results)} matches")
   for person in results:
       print(f"- {person['name']}, Age: {person.get('age', 'Unknown')}")
       print(f"  Location: {person.get('address', 'Unknown')}")

Phone Number Lookup
-------------------

.. code-block:: python

   from sleuth_intel import PhoneLookup

   # Lookup phone number
   phone_info = PhoneLookup.search("555-123-4567")

   print(f"Owner: {phone_info['owner_name']}")
   print(f"Carrier: {phone_info['carrier']}")
   print(f"Type: {phone_info['line_type']}")
   print(f"Location: {phone_info['location']}")

Email Verification
------------------

.. code-block:: python

   from sleuth_intel import EmailVerifier

   # Verify email
   email_data = EmailVerifier.verify("john.doe@example.com")

   print(f"Valid: {email_data['is_valid']}")
   print(f"Deliverable: {email_data['is_deliverable']}")
   print(f"Risk Score: {email_data['risk_score']}")

Using Agents
============

Person Investigation Agent
--------------------------

.. code-block:: python

   from sleuth_intel.agents import PersonSearchAgent

   # Create agent
   agent = PersonSearchAgent(
       name="person_investigator",
       config={"max_results": 10}
   )

   # Run investigation
   investigation = agent.investigate({
       "first_name": "John",
       "last_name": "Doe",
       "city": "New York",
       "state": "NY"
   })

   # Access results
   print(f"Investigation ID: {investigation.id}")
   print(f"Status: {investigation.status}")
   print(f"Results: {investigation.results}")

Business Search Agent
---------------------

.. code-block:: python

   from sleuth_intel.agents import BusinessSearchAgent

   # Create business agent
   business_agent = BusinessSearchAgent()

   # Search for business
   business_results = business_agent.search({
       "company_name": "Acme Corporation",
       "state": "CA"
   })

   for business in business_results:
       print(f"Company: {business['name']}")
       print(f"Address: {business['address']}")
       print(f"Revenue: ${business.get('revenue', 'N/A')}")

Creating Workflows
==================

Simple Sequential Workflow
--------------------------

.. code-block:: python

   from sleuth_intel import WorkflowBuilder

   # Build workflow
   workflow = WorkflowBuilder.create("background_check")

   # Add steps
   workflow.add_step("person_search", PersonSearchAgent())
   workflow.add_step("phone_verify", PhoneSearchAgent())
   workflow.add_step("email_verify", EmailSearchAgent())

   # Execute workflow
   results = workflow.run({
       "name": "John Doe",
       "phone": "555-123-4567",
       "email": "john@example.com"
   })

   # Get comprehensive report
   report = results.get_report()
   print(report)

Parallel Workflow
-----------------

.. code-block:: python

   from sleuth_intel import ParallelWorkflow

   # Create parallel workflow
   parallel = ParallelWorkflow("comprehensive_search")

   # Add parallel tasks
   parallel.add_tasks([
       ("person", PersonSearchAgent(), {"name": "John Doe"}),
       ("business", BusinessSearchAgent(), {"company": "Acme Corp"}),
       ("address", AddressSearchAgent(), {"address": "123 Main St"})
   ])

   # Execute all tasks simultaneously
   results = parallel.execute()

   # Combine results
   combined_report = parallel.combine_results(results)

Working with Results
====================

Accessing Data
--------------

.. code-block:: python

   # Get structured data
   person_data = results.get("person_search")

   # Access nested fields safely
   phone_numbers = person_data.get("phone_numbers", [])
   primary_phone = phone_numbers[0] if phone_numbers else None

   # Get metadata
   metadata = results.metadata
   print(f"Execution time: {metadata['duration_ms']}ms")
   print(f"API calls made: {metadata['api_calls']}")

Exporting Results
-----------------

.. code-block:: python

   from sleuth_intel import ResultExporter

   # Export to different formats
   exporter = ResultExporter(results)

   # JSON export
   exporter.to_json("investigation_results.json")

   # CSV export
   exporter.to_csv("investigation_results.csv")

   # PDF report
   exporter.to_pdf("investigation_report.pdf", include_metadata=True)

   # Excel with multiple sheets
   exporter.to_excel("investigation.xlsx", {
       "Summary": results.summary,
       "Person Data": results.person_data,
       "Phone Data": results.phone_data
   })

Error Handling
==============

Basic Error Handling
--------------------

.. code-block:: python

   from sleuth_intel import SleuthIntelError

   try:
       results = searcher.find_person(name="John Doe")
   except SleuthIntelError as e:
       print(f"Investigation failed: {e}")
       print(f"Error code: {e.code}")
       print(f"Details: {e.details}")

Handling Rate Limits
--------------------

.. code-block:: python

   from sleuth_intel.exceptions import RateLimitError
   import time

   def search_with_retry(query, max_retries=3):
       for attempt in range(max_retries):
           try:
               return searcher.search(query)
           except RateLimitError as e:
               wait_time = e.retry_after or (2 ** attempt)
               print(f"Rate limited. Waiting {wait_time} seconds...")
               time.sleep(wait_time)
       raise Exception("Max retries exceeded")

Async Operations
================

Async Person Search
-------------------

.. code-block:: python

   import asyncio
   from sleuth_intel.async_api import AsyncSearcher

   async def async_investigation():
       searcher = AsyncSearcher()

       # Concurrent searches
       tasks = [
           searcher.find_person("John Doe"),
           searcher.find_person("Jane Smith"),
           searcher.find_person("Bob Johnson")
       ]

       results = await asyncio.gather(*tasks)
       return results

   # Run async investigation
   results = asyncio.run(async_investigation())

Streaming Results
-----------------

.. code-block:: python

   async def stream_investigation():
       async with AsyncSearcher() as searcher:
           async for result in searcher.stream_search(queries):
               print(f"Found: {result['name']}")
               # Process each result as it arrives
               await process_result(result)

Common Use Cases
================

Background Check
----------------

.. code-block:: python

   from sleuth_intel import BackgroundCheck

   # Comprehensive background check
   checker = BackgroundCheck()

   report = checker.run_check(
       name="John Doe",
       ssn_last_four="1234",
       date_of_birth="1980-01-01"
   )

   print(f"Criminal Records: {report['criminal_records']}")
   print(f"Court Cases: {report['court_cases']}")
   print(f"Bankruptcies: {report['bankruptcies']}")

Fraud Detection
---------------

.. code-block:: python

   from sleuth_intel import FraudDetector

   # Check for fraud indicators
   detector = FraudDetector()

   risk_assessment = detector.assess(
       email="suspicious@example.com",
       phone="555-fake-number",
       name="John Doe",
       address="123 Fake St"
   )

   print(f"Risk Score: {risk_assessment['risk_score']}/10")
   print(f"Red Flags: {risk_assessment['red_flags']}")
   print(f"Recommendation: {risk_assessment['recommendation']}")

Business Verification
---------------------

.. code-block:: python

   from sleuth_intel import BusinessVerifier

   # Verify business
   verifier = BusinessVerifier()

   verification = verifier.verify(
       company_name="Acme Corporation",
       ein="12-3456789",
       address="123 Business Ave"
   )

   print(f"Verified: {verification['is_verified']}")
   print(f"Status: {verification['business_status']}")
   print(f"Established: {verification['established_date']}")

Quick Tips
==========

1. **Enable Caching**: Reduce API calls and improve performance
2. **Use Bulk Operations**: Process multiple queries efficiently
3. **Set Appropriate Timeouts**: Prevent hanging requests
4. **Monitor Rate Limits**: Stay within API limits
5. **Handle Errors Gracefully**: Implement proper error handling
6. **Use Async When Possible**: Improve performance with async operations
7. **Export Results**: Save investigations for later analysis
8. **Configure Logging**: Enable logging for debugging
9. **Validate Input**: Check data before sending to APIs
10. **Review Documentation**: Check API docs for advanced features

Next Steps
==========

* Explore :doc:`/guides/workflow_design` for complex investigations
* Learn about :doc:`/technical/architecture` for system understanding
* Review :doc:`/api/agents` for detailed API reference
* Check :doc:`/examples/person_investigation` for real-world examples

Getting Help
============

If you encounter issues:

.. code-block:: python

   from sleuth_intel import diagnostic

   # Run diagnostic check
   diagnostic.check_configuration()
   diagnostic.test_connectivity()
   diagnostic.verify_credentials()

   # Get system info
   print(diagnostic.get_system_info())

For additional support:

* Documentation: https://sleuth-intel.readthedocs.io
* GitHub Issues: https://github.com/yourusername/sleuth-intel/issues
* Community Forum: https://forum.sleuth-intel.org
