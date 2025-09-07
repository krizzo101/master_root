============
Installation
============

This guide will help you install Sleuth Intel and its dependencies.

Requirements
============

* Python 3.9 or higher
* pip package manager
* Virtual environment (recommended)

Basic Installation
==================

Using pip
---------

The simplest way to install Sleuth Intel:

.. code-block:: bash

   pip install sleuth-intel

From Source
-----------

For the latest development version:

.. code-block:: bash

   git clone https://github.com/yourusername/sleuth-intel.git
   cd sleuth-intel
   pip install -e .

With Optional Dependencies
--------------------------

Install with all optional dependencies:

.. code-block:: bash

   pip install sleuth-intel[all]

Or specific extras:

.. code-block:: bash

   # For PDF generation
   pip install sleuth-intel[pdf]

   # For database support
   pip install sleuth-intel[database]

   # For webhook support
   pip install sleuth-intel[webhooks]

Development Installation
========================

For contributors and developers:

.. code-block:: bash

   git clone https://github.com/yourusername/sleuth-intel.git
   cd sleuth-intel

   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install in development mode with dev dependencies
   pip install -e ".[dev]"

   # Install pre-commit hooks
   pre-commit install

Docker Installation
===================

Using Docker:

.. code-block:: bash

   docker pull sleuth-intel:latest

   # Run container
   docker run -it sleuth-intel:latest

Using Docker Compose:

.. code-block:: yaml

   version: '3.8'
   services:
     sleuth-intel:
       image: sleuth-intel:latest
       environment:
         - SLEUTH_API_KEY=${SLEUTH_API_KEY}
       volumes:
         - ./data:/app/data
         - ./configs:/app/configs

Verify Installation
===================

After installation, verify everything is working:

.. code-block:: python

   import sleuth_intel
   print(sleuth_intel.__version__)

   # Test basic functionality
   from sleuth_intel.agents import BaseAgent
   agent = BaseAgent(name="test")
   print(f"Agent created: {agent.name}")

Configuration
=============

After installation, configure your API keys and settings:

.. code-block:: bash

   # Create configuration directory
   mkdir ~/.sleuth_intel

   # Copy example configuration
   cp config.example.yml ~/.sleuth_intel/config.yml

   # Edit with your API keys
   nano ~/.sleuth_intel/config.yml

Environment Variables
---------------------

You can also use environment variables:

.. code-block:: bash

   export SLEUTH_INTEL_API_KEY="your-api-key"
   export SLEUTH_INTEL_RATE_LIMIT=100
   export SLEUTH_INTEL_TIMEOUT=30

Troubleshooting
===============

Common Installation Issues
--------------------------

**Import Error**: If you get import errors:

.. code-block:: bash

   # Ensure you're in the correct virtual environment
   which python

   # Reinstall dependencies
   pip install --upgrade --force-reinstall sleuth-intel

**Permission Denied**: On Linux/Mac:

.. code-block:: bash

   # Use user installation
   pip install --user sleuth-intel

   # Or with sudo (not recommended)
   sudo pip install sleuth-intel

**SSL Certificate Error**: Behind corporate proxy:

.. code-block:: bash

   # Temporarily disable SSL verification (not recommended for production)
   pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org sleuth-intel

Next Steps
==========

Once installed, proceed to:

* :doc:`quickstart` - Get up and running quickly
* :doc:`configuration` - Configure your settings
* :doc:`first_investigation` - Run your first investigation
