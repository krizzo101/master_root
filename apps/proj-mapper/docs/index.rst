====================
Project Mapper Docs
====================

Project Mapper is a Python tool designed to analyze projects and generate structured maps optimized for AI agent consumption. It helps AI development agents understand project structure, relationships, and documentation, making them more effective when interacting with unfamiliar codebases.

Features
========

* **Python Code Analysis**: Extracts structure and relationships from Python code
* **Markdown Documentation Analysis**: Processes documentation and finds connections to code
* **Relationship Detection**: Identifies and scores relationships between files
* **AI-Optimized Output**: Generates maps formatted for efficient AI consumption
* **Flexible Configuration**: Customize analysis and output through configuration
* **CLI and API Interfaces**: Use as a command-line tool or library

Documentation
============

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user/getting_started
   user/configuration
   user/cli_reference
   user/advanced_usage
   user/troubleshooting

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/index
   api/core/index
   api/analyzers/index
   api/relationship/index
   api/output/index
   api/interfaces/index
   api/models/index

.. toctree::
   :maxdepth: 2
   :caption: Developer Guide

   developer/index
   developer/architecture
   developer/extending
   developer/contributing
   
Installation
===========

Install Project Mapper using pip:

.. code-block:: bash

   pip install proj-mapper

For development installation:

.. code-block:: bash

   git clone https://github.com/yourusername/project_mapper.git
   cd project_mapper
   pip install -e .

Quick Start
==========

Basic usage:

.. code-block:: bash

   # Navigate to your project
   cd /path/to/your/project
   
   # Generate a project map
   proj-mapper generate-map

Python API:

.. code-block:: python

   from proj_mapper import ProjectMapper
   
   # Create a Project Mapper instance
   mapper = ProjectMapper(project_root="/path/to/project")
   
   # Generate a map
   result = mapper.generate_map()
   
   # Access the map data
   map_data = result.map_data

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search` 