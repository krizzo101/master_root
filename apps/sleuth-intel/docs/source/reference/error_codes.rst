===========
Error Codes
===========

This reference provides a comprehensive list of error codes, their meanings, and resolution strategies.

Error Code Categories
=====================

Sleuth Intel uses a structured error code system:

* **1xxx**: Authentication and Authorization Errors
* **2xxx**: Validation Errors
* **3xxx**: API and Provider Errors
* **4xxx**: Rate Limiting and Quota Errors
* **5xxx**: System and Infrastructure Errors
* **6xxx**: Data Processing Errors
* **7xxx**: Workflow and Orchestration Errors

Authentication Errors (1xxx)
=============================

.. list-table:: Authentication Error Codes
   :header-rows: 1
   :widths: 15 25 60

   * - Code
     - Error
     - Description and Resolution
   * - 1001
     - INVALID_API_KEY
     - The provided API key is invalid or malformed. Check your configuration.
   * - 1002
     - EXPIRED_API_KEY
     - API key has expired. Renew or rotate your credentials.
   * - 1003
     - INSUFFICIENT_PERMISSIONS
     - API key lacks required permissions for this operation.
   * - 1004
     - AUTHENTICATION_REQUIRED
     - No authentication credentials provided.
   * - 1005
     - TOKEN_REFRESH_FAILED
     - Failed to refresh authentication token. Re-authenticate.

Validation Errors (2xxx)
=========================

.. list-table:: Validation Error Codes
   :header-rows: 1
   :widths: 15 25 60

   * - Code
     - Error
     - Description and Resolution
   * - 2001
     - INVALID_INPUT_FORMAT
     - Input data format is invalid. Check data structure.
   * - 2002
     - MISSING_REQUIRED_FIELD
     - Required field is missing from input.
   * - 2003
     - INVALID_EMAIL_FORMAT
     - Email address format is invalid.
   * - 2004
     - INVALID_PHONE_FORMAT
     - Phone number format is invalid or unsupported.
   * - 2005
     - INVALID_SSN_FORMAT
     - SSN format is invalid (should be XXX-XX-XXXX or last 4).
   * - 2006
     - INVALID_DATE_FORMAT
     - Date format is invalid. Use YYYY-MM-DD.
   * - 2007
     - VALUE_OUT_OF_RANGE
     - Numeric value is outside acceptable range.
   * - 2008
     - INVALID_STATE_CODE
     - State code is invalid. Use 2-letter codes.

API/Provider Errors (3xxx)
===========================

.. list-table:: API Error Codes
   :header-rows: 1
   :widths: 15 25 60

   * - Code
     - Error
     - Description and Resolution
   * - 3001
     - PROVIDER_UNAVAILABLE
     - Data provider is temporarily unavailable. Retry later.
   * - 3002
     - PROVIDER_TIMEOUT
     - Request to provider timed out. Increase timeout or retry.
   * - 3003
     - INVALID_PROVIDER_RESPONSE
     - Provider returned malformed response. Contact support.
   * - 3004
     - PROVIDER_ERROR
     - Provider returned an error. Check provider status.
   * - 3005
     - NO_DATA_FOUND
     - No data found for the given query.
   * - 3006
     - PARTIAL_DATA_AVAILABLE
     - Only partial data available. Some sources failed.

Rate Limiting Errors (4xxx)
============================

.. list-table:: Rate Limit Error Codes
   :header-rows: 1
   :widths: 15 25 60

   * - Code
     - Error
     - Description and Resolution
   * - 4001
     - RATE_LIMIT_EXCEEDED
     - API rate limit exceeded. Wait before retrying.
   * - 4002
     - DAILY_QUOTA_EXCEEDED
     - Daily API quota exhausted. Resets at midnight UTC.
   * - 4003
     - CONCURRENT_LIMIT_REACHED
     - Maximum concurrent requests reached. Queue requests.
   * - 4004
     - BURST_LIMIT_EXCEEDED
     - Burst rate limit hit. Implement exponential backoff.

System Errors (5xxx)
====================

.. list-table:: System Error Codes
   :header-rows: 1
   :widths: 15 25 60

   * - Code
     - Error
     - Description and Resolution
   * - 5001
     - INTERNAL_SERVER_ERROR
     - Unexpected server error. Retry or contact support.
   * - 5002
     - DATABASE_CONNECTION_FAILED
     - Cannot connect to database. Check configuration.
   * - 5003
     - CACHE_UNAVAILABLE
     - Cache service unavailable. Operating without cache.
   * - 5004
     - RESOURCE_EXHAUSTED
     - System resources exhausted. Scale or wait.
   * - 5005
     - CONFIGURATION_ERROR
     - Invalid system configuration. Check settings.

Data Processing Errors (6xxx)
==============================

.. list-table:: Processing Error Codes
   :header-rows: 1
   :widths: 15 25 60

   * - Code
     - Error
     - Description and Resolution
   * - 6001
     - DATA_PARSING_ERROR
     - Failed to parse data. Check format compatibility.
   * - 6002
     - DATA_VALIDATION_FAILED
     - Data validation failed. Review data quality.
   * - 6003
     - TRANSFORMATION_ERROR
     - Data transformation failed. Check mapping rules.
   * - 6004
     - AGGREGATION_ERROR
     - Failed to aggregate results. Check data consistency.
   * - 6005
     - ENCODING_ERROR
     - Character encoding error. Ensure UTF-8 encoding.

Workflow Errors (7xxx)
======================

.. list-table:: Workflow Error Codes
   :header-rows: 1
   :widths: 15 25 60

   * - Code
     - Error
     - Description and Resolution
   * - 7001
     - WORKFLOW_NOT_FOUND
     - Specified workflow doesn't exist.
   * - 7002
     - TASK_DEPENDENCY_FAILED
     - Dependent task failed. Check task chain.
   * - 7003
     - WORKFLOW_TIMEOUT
     - Workflow execution timed out.
   * - 7004
     - INVALID_WORKFLOW_STATE
     - Workflow in invalid state for operation.
   * - 7005
     - AGENT_NOT_AVAILABLE
     - Required agent not available or not registered.

Error Response Format
=====================

All errors follow a consistent JSON format:

.. code-block:: json

   {
     "error": {
       "code": 4001,
       "type": "RATE_LIMIT_EXCEEDED",
       "message": "API rate limit exceeded",
       "details": {
         "limit": 100,
         "window": "1m",
         "retry_after": 45
       },
       "timestamp": "2024-01-15T10:30:45Z",
       "request_id": "req_abc123xyz"
     }
   }

Error Handling Examples
=======================

Python Error Handling
---------------------

.. code-block:: python

   from sleuth_intel.exceptions import (
       SleuthIntelError,
       RateLimitError,
       ValidationError,
       APIError
   )
   import time

   def handle_investigation_errors():
       try:
           result = agent.investigate(query)
       except RateLimitError as e:
           # Handle rate limiting with exponential backoff
           wait_time = e.retry_after or 60
           print(f"Rate limited. Waiting {wait_time} seconds...")
           time.sleep(wait_time)
           return handle_investigation_errors()  # Retry

       except ValidationError as e:
           # Handle validation errors
           print(f"Invalid input: {e.message}")
           print(f"Field: {e.field}")
           print(f"Value: {e.value}")
           raise

       except APIError as e:
           # Handle API errors
           if e.code == 3005:  # NO_DATA_FOUND
               return {"status": "no_results", "data": []}
           else:
               print(f"API Error {e.code}: {e.message}")
               raise

       except SleuthIntelError as e:
           # Handle general errors
           print(f"Error {e.code}: {e.message}")
           if e.is_retryable:
               time.sleep(5)
               return handle_investigation_errors()
           raise

Async Error Handling
--------------------

.. code-block:: python

   import asyncio
   from sleuth_intel.async_api import AsyncAgent

   async def resilient_investigation(query, max_retries=3):
       agent = AsyncAgent()

       for attempt in range(max_retries):
           try:
               return await agent.investigate(query)

           except RateLimitError as e:
               if attempt < max_retries - 1:
                   await asyncio.sleep(e.retry_after or (2 ** attempt))
               else:
                   raise

           except APIError as e:
               if e.is_transient and attempt < max_retries - 1:
                   await asyncio.sleep(2 ** attempt)
               else:
                   raise

Error Recovery Strategies
=========================

Automatic Retry
---------------

.. code-block:: python

   from sleuth_intel.retry import RetryStrategy

   # Configure retry strategy
   retry_strategy = RetryStrategy(
       max_attempts=3,
       backoff_factor=2.0,
       max_backoff=120,
       retryable_errors=[4001, 5001, 3001]
   )

   # Apply to agent
   agent = PersonSearchAgent(retry_strategy=retry_strategy)

Circuit Breaker
---------------

.. code-block:: python

   from sleuth_intel.resilience import CircuitBreaker

   # Configure circuit breaker
   circuit_breaker = CircuitBreaker(
       failure_threshold=5,
       recovery_timeout=60,
       expected_errors=[APIError, TimeoutError]
   )

   # Wrap agent calls
   @circuit_breaker
   def safe_investigate(query):
       return agent.investigate(query)

Fallback Providers
------------------

.. code-block:: python

   from sleuth_intel.providers import FallbackProvider

   # Configure fallback chain
   provider = FallbackProvider([
       PrimaryProvider(),
       SecondaryProvider(),
       TertiaryProvider()
   ])

   # Automatic fallback on errors
   result = provider.search(query)

Common Error Scenarios
======================

Scenario: Rate Limit Handling
------------------------------

**Problem**: Hitting rate limits during bulk processing

**Solution**:

.. code-block:: python

   from sleuth_intel.utils import RateLimitedProcessor

   processor = RateLimitedProcessor(
       requests_per_second=10,
       burst_size=20
   )

   # Process with automatic rate limiting
   results = processor.process_batch(items)

Scenario: Incomplete Data
--------------------------

**Problem**: Provider returns partial data

**Solution**:

.. code-block:: python

   def handle_partial_data(result):
       if result.get("_partial"):
           # Log missing fields
           missing = result.get("_missing_fields", [])
           logger.warning(f"Partial data: missing {missing}")

           # Attempt to fill from cache or other sources
           result = enrich_from_cache(result)

           # Mark as incomplete if still missing critical data
           if missing_critical_fields(result):
               result["_quality"] = "incomplete"

       return result

Debugging Error Codes
=====================

Enable Debug Logging
--------------------

.. code-block:: python

   import logging

   # Enable debug logging
   logging.basicConfig(level=logging.DEBUG)

   # Or for specific module
   logging.getLogger('sleuth_intel.api').setLevel(logging.DEBUG)

Error Diagnostics
-----------------

.. code-block:: python

   from sleuth_intel.diagnostics import ErrorDiagnostics

   # Run diagnostics
   diagnostics = ErrorDiagnostics()

   # Check specific error
   diagnosis = diagnostics.diagnose_error(error_code=4001)
   print(diagnosis.explanation)
   print(diagnosis.resolution_steps)

   # Get error statistics
   stats = diagnostics.get_error_stats()
   print(f"Most common errors: {stats.top_errors}")

Support Resources
=================

When encountering persistent errors:

1. **Check Status Page**: https://status.sleuth-intel.com
2. **Review Documentation**: Ensure correct API usage
3. **Enable Debug Logging**: Capture detailed error information
4. **Contact Support**: Include error code and request ID
5. **Community Forum**: https://forum.sleuth-intel.org/errors
