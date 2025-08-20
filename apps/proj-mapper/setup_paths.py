#!/usr/bin/env python3
"""
Setup script to configure proj-mapper to work with master_root libraries
Run this before using proj-mapper
"""

import os
import sys
from pathlib import Path

# Add master_root libs to path
master_root = Path(__file__).parent.parent.parent
libs_path = master_root / "libs"
sys.path.insert(0, str(libs_path))

# Add proj-mapper src to path
proj_mapper_src = Path(__file__).parent / "src"
sys.path.insert(0, str(proj_mapper_src))

print(f"✅ Path configured for proj-mapper")
print(f"   Master root libs: {libs_path}")
print(f"   Proj-mapper src: {proj_mapper_src}")

# Try importing to verify
try:
    import proj_mapper

    print(f"✅ proj-mapper imported successfully")
except ImportError as e:
    print(f"❌ Failed to import proj-mapper: {e}")
