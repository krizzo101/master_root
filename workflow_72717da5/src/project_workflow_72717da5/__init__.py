"""
project_workflow_72717da5 package

This package provides a small, stable public API for running lightweight workflows
using utilities provided in the companion utils module.

Public API:
- __version__: package version string
- get_version(): return package version
- run_workflow(*args, **kwargs): validate and normalize inputs, delegate to utils,
  and return a deterministic dict result with keys: status, result, error
- Any explicit re-exports from utils (see __all__)

Basic usage examples:

>>> from project_workflow_72717da5 import get_version, run_workflow
>>> get_version()
'0.0.0'
>>> run_workflow('item')
{'status': 'success', 'result': {'original': 'item', 'processed': ['item']}, 'error': None}

Note: run_workflow will not perform network or file I/O by itself. If the
underlying utils contains functions that perform such actions, they will only
be invoked if explicitly delegated to and with provided arguments.
"""

import logging
from typing import Any, Dict, Optional, Sequence
