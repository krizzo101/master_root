====
Core
====

Core modules provide fundamental functionality for the Sleuth Intel framework.

Secure API Locker
=================

.. automodule:: src.core.secure_api_locker
   :members:
   :undoc-members:
   :show-inheritance:

APILockerManager
----------------

.. autoclass:: src.core.secure_api_locker.APILockerManager
   :members:
   :undoc-members:
   :show-inheritance:

   .. automethod:: __init__
   .. automethod:: add_credential
   .. automethod:: get_credential
   .. automethod:: rotate_credentials
   .. automethod:: encrypt_credential
   .. automethod:: decrypt_credential

APICredential
-------------

.. autoclass:: src.core.secure_api_locker.APICredential
   :members:
   :undoc-members:
   :show-inheritance:

Configuration Manager
=====================

.. automodule:: src.core.config_manager
   :members:
   :undoc-members:
   :show-inheritance:

ConfigManager
-------------

.. autoclass:: src.core.config_manager.ConfigManager
   :members:
   :undoc-members:
   :show-inheritance:

   .. automethod:: load_config
   .. automethod:: save_config
   .. automethod:: get
   .. automethod:: set
   .. automethod:: validate_config

Cache Manager
=============

.. automodule:: src.core.cache_manager
   :members:
   :undoc-members:
   :show-inheritance:

CacheManager
------------

.. autoclass:: src.core.cache_manager.CacheManager
   :members:
   :undoc-members:
   :show-inheritance:

   .. automethod:: get
   .. automethod:: set
   .. automethod:: delete
   .. automethod:: clear
   .. automethod:: get_stats

Logger Configuration
====================

.. automodule:: src.core.logger
   :members:
   :undoc-members:
   :show-inheritance:

LoggerConfig
------------

.. autoclass:: src.core.logger.LoggerConfig
   :members:
   :undoc-members:
   :show-inheritance:

   .. automethod:: setup_logging
   .. automethod:: get_logger
   .. automethod:: set_level
   .. automethod:: add_handler

Error Handling
==============

.. automodule:: src.core.exceptions
   :members:
   :undoc-members:
   :show-inheritance:

Exception Classes
-----------------

.. autoclass:: src.core.exceptions.SleuthIntelError
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.core.exceptions.APIError
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.core.exceptions.RateLimitError
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.core.exceptions.ValidationError
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.core.exceptions.AuthenticationError
   :members:
   :undoc-members:
   :show-inheritance:

Validators
==========

.. automodule:: src.core.validators
   :members:
   :undoc-members:
   :show-inheritance:

InputValidator
--------------

.. autoclass:: src.core.validators.InputValidator
   :members:
   :undoc-members:
   :show-inheritance:

   .. automethod:: validate_email
   .. automethod:: validate_phone
   .. automethod:: validate_ssn
   .. automethod:: validate_address

OutputValidator
---------------

.. autoclass:: src.core.validators.OutputValidator
   :members:
   :undoc-members:
   :show-inheritance:

   .. automethod:: validate_schema
   .. automethod:: validate_required_fields
   .. automethod:: sanitize_output

Rate Limiter
============

.. automodule:: src.core.rate_limiter
   :members:
   :undoc-members:
   :show-inheritance:

RateLimiter
-----------

.. autoclass:: src.core.rate_limiter.RateLimiter
   :members:
   :undoc-members:
   :show-inheritance:

   .. automethod:: acquire
   .. automethod:: release
   .. automethod:: wait_if_needed
   .. automethod:: get_current_rate

Retry Manager
=============

.. automodule:: src.core.retry_manager
   :members:
   :undoc-members:
   :show-inheritance:

RetryManager
------------

.. autoclass:: src.core.retry_manager.RetryManager
   :members:
   :undoc-members:
   :show-inheritance:

   .. automethod:: retry
   .. automethod:: exponential_backoff
   .. automethod:: should_retry

Session Manager
===============

.. automodule:: src.core.session_manager
   :members:
   :undoc-members:
   :show-inheritance:

SessionManager
--------------

.. autoclass:: src.core.session_manager.SessionManager
   :members:
   :undoc-members:
   :show-inheritance:

   .. automethod:: create_session
   .. automethod:: get_session
   .. automethod:: close_session
   .. automethod:: configure_session

Metrics Collector
=================

.. automodule:: src.core.metrics
   :members:
   :undoc-members:
   :show-inheritance:

MetricsCollector
----------------

.. autoclass:: src.core.metrics.MetricsCollector
   :members:
   :undoc-members:
   :show-inheritance:

   .. automethod:: record_request
   .. automethod:: record_error
   .. automethod:: get_metrics
   .. automethod:: reset_metrics
