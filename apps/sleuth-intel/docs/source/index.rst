.. Sleuth Intel documentation master file

===========================================
Sleuth Intel - Advanced OSINT Framework
===========================================

.. image:: https://img.shields.io/badge/Python-3.9%2B-blue
   :alt: Python Version

.. image:: https://img.shields.io/badge/License-MIT-green
   :alt: License

**Sleuth Intel** is a comprehensive Open Source Intelligence (OSINT) investigation framework that provides automated data gathering, analysis, and reporting capabilities through a modular agent-based architecture.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   getting_started/installation
   getting_started/quickstart
   getting_started/configuration
   getting_started/first_investigation

.. toctree::
   :maxdepth: 2
   :caption: User Guides

   guides/basic_usage
   guides/workflow_design
   guides/data_providers
   guides/output_formats
   guides/best_practices

.. toctree::
   :maxdepth: 2
   :caption: Technical Documentation

   technical/architecture
   technical/agent_system
   technical/orchestration
   technical/performance
   technical/security

.. toctree::
   :maxdepth: 2
   :caption: Integration Guides

   integration/orchestrator
   integration/custom_agents
   integration/webhooks
   integration/databases
   integration/api_clients

.. toctree::
   :maxdepth: 3
   :caption: API Reference

   api/agents
   api/core
   api/models
   api/orchestration
   api/providers
   api/utils

.. toctree::
   :maxdepth: 2
   :caption: Advanced Topics

   advanced/rate_limiting
   advanced/error_handling
   advanced/caching
   advanced/parallel_processing
   advanced/custom_providers

.. toctree::
   :maxdepth: 2
   :caption: Examples

   examples/person_investigation
   examples/business_research
   examples/fraud_detection
   examples/bulk_processing
   examples/real_time_monitoring

.. toctree::
   :maxdepth: 2
   :caption: Reference

   reference/error_codes
   reference/configuration_options
   reference/performance_metrics
   reference/troubleshooting
   reference/faq

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Key Features
============

* **Modular Agent Architecture**: Specialized agents for different investigation tasks
* **Multiple Data Providers**: Integration with various OSINT data sources
* **Workflow Orchestration**: Chain multiple investigations into complex workflows
* **Real-time Processing**: Stream processing capabilities for continuous monitoring
* **Comprehensive Reporting**: Multiple output formats including JSON, CSV, and PDF
* **Rate Limiting**: Built-in rate limiting and retry mechanisms
* **Error Recovery**: Robust error handling and automatic recovery
* **Extensible Design**: Easy to add custom agents and providers

Quick Example
=============

.. code-block:: python

   from sleuth_intel import InvestigationOrchestrator
   from sleuth_intel.agents import PersonSearchAgent

   # Initialize orchestrator
   orchestrator = InvestigationOrchestrator()

   # Create and configure agent
   agent = PersonSearchAgent(
       name="person_investigator",
       config={"max_depth": 3}
   )

   # Run investigation
   results = orchestrator.investigate(
       agent=agent,
       query={"name": "John Doe", "location": "New York"}
   )

   # Process results
   print(results.summary)

Support
=======

* **Documentation**: https://sleuth-intel.readthedocs.io
* **GitHub**: https://github.com/yourusername/sleuth-intel
* **Issues**: https://github.com/yourusername/sleuth-intel/issues
* **Discussions**: https://github.com/yourusername/sleuth-intel/discussions
