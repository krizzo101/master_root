======
Agents
======

The agents module provides specialized intelligence gathering agents for various investigation tasks.

Base Agent
==========

.. automodule:: src.agents.base_agent
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

BaseAgent Class
---------------

.. autoclass:: src.agents.base_agent.BaseAgent
   :members:
   :undoc-members:
   :show-inheritance:

   .. automethod:: __init__
   .. automethod:: execute
   .. automethod:: validate_input
   .. automethod:: process_results
   .. automethod:: get_metrics

RateLimiter Class
-----------------

.. autoclass:: src.agents.base_agent.RateLimiter
   :members:
   :undoc-members:
   :show-inheritance:

Configuration Classes
---------------------

.. autoclass:: src.agents.base_agent.RateLimitConfig
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.agents.base_agent.RetryConfig
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.agents.base_agent.CacheConfig
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.agents.base_agent.MetricsData
   :members:
   :undoc-members:
   :show-inheritance:

Person Search Agent
===================

.. automodule:: src.agents.person_search_agent
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.agents.person_search_agent.PersonSearchAgent
   :members:
   :undoc-members:
   :show-inheritance:

   .. automethod:: search_person
   .. automethod:: enrich_person_data
   .. automethod:: analyze_social_presence
   .. automethod:: verify_identity

Phone Search Agent
==================

.. automodule:: src.agents.phone_search_agent
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.agents.phone_search_agent.PhoneSearchAgent
   :members:
   :undoc-members:
   :show-inheritance:

   .. automethod:: lookup_phone
   .. automethod:: validate_phone_number
   .. automethod:: get_carrier_info
   .. automethod:: check_reputation

Email Search Agent
==================

.. automodule:: src.agents.email_search_agent
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.agents.email_search_agent.EmailSearchAgent
   :members:
   :undoc-members:
   :show-inheritance:

   .. automethod:: search_email
   .. automethod:: validate_email
   .. automethod:: check_breach_data
   .. automethod:: analyze_domain

Address Search Agent
====================

.. automodule:: src.agents.address_search_agent
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.agents.address_search_agent.AddressSearchAgent
   :members:
   :undoc-members:
   :show-inheritance:

   .. automethod:: search_address
   .. automethod:: geocode_address
   .. automethod:: get_property_details
   .. automethod:: find_residents

Business Search Agent
=====================

.. automodule:: src.agents.business_search_agent
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.agents.business_search_agent.BusinessSearchAgent
   :members:
   :undoc-members:
   :show-inheritance:

   .. automethod:: search_business
   .. automethod:: get_company_details
   .. automethod:: analyze_reputation
   .. automethod:: find_key_personnel

Social Media Agent
==================

.. automodule:: src.agents.social_media_agent
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.agents.social_media_agent.SocialMediaAgent
   :members:
   :undoc-members:
   :show-inheritance:

   .. automethod:: search_profiles
   .. automethod:: analyze_activity
   .. automethod:: extract_connections
   .. automethod:: detect_fake_profiles

Vehicle Search Agent
====================

.. automodule:: src.agents.vehicle_search_agent
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.agents.vehicle_search_agent.VehicleSearchAgent
   :members:
   :undoc-members:
   :show-inheritance:

   .. automethod:: search_vehicle
   .. automethod:: lookup_vin
   .. automethod:: get_registration_history
   .. automethod:: check_recalls

Court Records Agent
===================

.. automodule:: src.agents.court_records_agent
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.agents.court_records_agent.CourtRecordsAgent
   :members:
   :undoc-members:
   :show-inheritance:

   .. automethod:: search_cases
   .. automethod:: get_case_details
   .. automethod:: find_criminal_records
   .. automethod:: search_civil_cases

Financial Agent
===============

.. automodule:: src.agents.financial_agent
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.agents.financial_agent.FinancialAgent
   :members:
   :undoc-members:
   :show-inheritance:

   .. automethod:: search_assets
   .. automethod:: find_bankruptcies
   .. automethod:: check_liens
   .. automethod:: analyze_financial_health

Agent Factory
=============

.. automodule:: src.agents.agent_factory
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.agents.agent_factory.AgentFactory
   :members:
   :undoc-members:
   :show-inheritance:

   .. automethod:: create_agent
   .. automethod:: register_agent
   .. automethod:: list_available_agents
