#!/usr/bin/env python3
"""
OAMAT Smart Decomposition - Module Entry Point

Enables running with: python -m src.applications.oamat_sd
"""

import asyncio
from pathlib import Path
import sys

# Add project root to path for absolute imports
project_root = Path(__file__).parents[3]
sys.path.insert(0, str(project_root))

from src.applications.oamat_sd.main import main

if __name__ == "__main__":
    asyncio.run(main())
