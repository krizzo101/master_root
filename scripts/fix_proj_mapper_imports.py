#!/usr/bin/env python3
"""
Fix proj-mapper imports to work with actual opsvi library structure
"""

import os
import sys

sys.path.insert(0, "/home/opsvi/master_root/libs")

import re
from pathlib import Path


class ImportFixer:
    """Fixes imports to match actual library structure"""

    def __init__(self):
        self.project_root = Path("/home/opsvi/master_root")
        self.app_path = self.project_root / "apps" / "proj-mapper"
        self.libs_path = self.project_root / "libs"

    def analyze_library_structure(self):
        """Analyze actual structure of opsvi libraries"""
        print("📊 Analyzing library structure...")

        lib_structure = {}

        # Check each opsvi library
        for lib_dir in self.libs_path.glob("opsvi-*"):
            if lib_dir.is_dir():
                lib_name = lib_dir.name

                # Find the actual module directory
                # It could be opsvi_xxx or the same as lib name
                possible_modules = [
                    lib_dir / lib_name.replace("-", "_"),
                    lib_dir / lib_name,
                    lib_dir / "src" / lib_name.replace("-", "_"),
                ]

                for module_path in possible_modules:
                    if module_path.exists() and (module_path / "__init__.py").exists():
                        lib_structure[lib_name] = {
                            "module_name": module_path.name,
                            "path": str(module_path),
                            "has_init": True,
                        }
                        break
                else:
                    # Check if there's any Python module
                    for py_dir in lib_dir.glob("*/"):
                        if py_dir.is_dir() and (py_dir / "__init__.py").exists():
                            lib_structure[lib_name] = {
                                "module_name": py_dir.name,
                                "path": str(py_dir),
                                "has_init": True,
                            }
                            break

        return lib_structure

    def create_import_mappings(self, lib_structure):
        """Create correct import mappings based on actual structure"""

        mappings = {}

        # Map proj_mapper components to actual opsvi modules
        component_mapping = {
            "proj_mapper.core": "opsvi_core",
            "proj_mapper.models": "opsvi_data.models",  # Use opsvi-data for models
            "proj_mapper.storage": "opsvi_data.storage",
            "proj_mapper.utils": "opsvi_core.utils",  # Use opsvi-core utils
            "proj_mapper.pipeline": "opsvi_pipeline",
            "proj_mapper.output": "opsvi_visualization.generators",
            "proj_mapper.analyzers": "proj_mapper.claude_code_adapter",  # Use our adapter
            "proj_mapper.interfaces": "opsvi_core.interfaces",  # Use opsvi-core interfaces
        }

        # Build regex patterns for replacement
        for old_import, new_import in component_mapping.items():
            # Handle different import styles
            mappings[f"from {old_import}"] = f"from {new_import}"
            mappings[f"import {old_import}"] = f"import {new_import}"

        return mappings

    def fix_file_imports(self, file_path: Path, mappings: dict):
        """Fix imports in a single file"""

        try:
            content = file_path.read_text()
            original_content = content

            # First, revert the broken changes from previous migration
            broken_mappings = {
                "from opsvi_core": "from proj_mapper.core",
                "from opsvi_models": "from proj_mapper.models",
                "from opsvi_data.storage": "from proj_mapper.storage",
                "from opsvi_utils": "from proj_mapper.utils",
                "from opsvi_pipeline": "from proj_mapper.pipeline",
                "from opsvi_visualization.generators": "from proj_mapper.output",
            }

            for broken, original in broken_mappings.items():
                content = content.replace(broken, original)

            # Now apply selective fixes for components we can actually replace

            # Only replace storage with opsvi_data if it exists
            if "from proj_mapper.storage" in content:
                # Keep original for now until we properly implement storage adapter
                pass

            # Replace analyzers with claude_code_adapter where appropriate
            if "from proj_mapper.analyzers" in content:
                # Check if it's importing specific analyzers
                analyzer_imports = re.findall(
                    r"from proj_mapper\.analyzers\.(\w+) import (\w+)", content
                )
                for module, name in analyzer_imports:
                    # Replace with our adapter
                    old_line = f"from proj_mapper.analyzers.{module} import {name}"
                    new_line = f"from proj_mapper.claude_code_adapter import {name}"
                    content = content.replace(old_line, new_line)

            # Add sys.path setup at the beginning of main files
            if (
                file_path.name in ["__main__.py", "main.py", "cli.py"]
                and "sys.path.insert" not in content
            ):
                path_setup = """import sys
import os
sys.path.insert(0, '/home/opsvi/master_root/libs')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
                # Find where to insert (after shebang and docstring)
                lines = content.split("\n")
                insert_at = 0

                for i, line in enumerate(lines):
                    if line.startswith("#!"):
                        insert_at = i + 1
                    elif line.startswith('"""') and i > 0:
                        # Find end of docstring
                        for j in range(i + 1, len(lines)):
                            if '"""' in lines[j]:
                                insert_at = j + 1
                                break
                        break
                    elif line and not line.startswith("#"):
                        insert_at = i
                        break

                lines.insert(insert_at, path_setup)
                content = "\n".join(lines)

            if content != original_content:
                file_path.write_text(content)
                return True

        except Exception as e:
            print(f"  ❌ Error fixing {file_path}: {e}")

        return False

    def add_path_setup_script(self):
        """Create a setup script for proj-mapper"""

        setup_script = '''#!/usr/bin/env python3
"""
Setup script to configure proj-mapper to work with master_root libraries
Run this before using proj-mapper
"""

import sys
import os
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
'''

        setup_path = self.app_path / "setup_paths.py"
        setup_path.write_text(setup_script)

        print(f"✅ Created setup script: {setup_path}")

        return setup_path

    def create_compatibility_layer(self):
        """Create compatibility layer for gradual migration"""

        compat_content = '''"""
Compatibility layer for proj-mapper migration
Provides adapters between proj-mapper and opsvi libraries
"""

from typing import Any, Dict, List, Optional
from pathlib import Path


class StorageAdapter:
    """Adapter for storage operations"""

    def __init__(self):
        # Will eventually use opsvi_data
        from proj_mapper.storage import FileStorage as OriginalStorage
        self.storage = OriginalStorage()

    def save(self, data: Any, path: Path):
        return self.storage.save(data, path)

    def load(self, path: Path):
        return self.storage.load(path)


class ModelAdapter:
    """Adapter for model operations"""

    @staticmethod
    def create_project_map(**kwargs):
        from proj_mapper.models import ProjectMap
        return ProjectMap(**kwargs)

    @staticmethod
    def create_file_info(**kwargs):
        from proj_mapper.models import FileInfo
        return FileInfo(**kwargs)


class PipelineAdapter:
    """Adapter for pipeline operations"""

    def __init__(self):
        from proj_mapper.pipeline import Pipeline as OriginalPipeline
        self.pipeline = OriginalPipeline()

    def run(self, stages: List[Any], data: Any):
        return self.pipeline.run(stages, data)


# Export adapters as if they were the original classes
FileStorage = StorageAdapter
ProjectMap = ModelAdapter.create_project_map
FileInfo = ModelAdapter.create_file_info
Pipeline = PipelineAdapter
'''

        compat_path = self.app_path / "src" / "proj_mapper" / "compatibility.py"
        compat_path.write_text(compat_content)

        print(f"✅ Created compatibility layer: {compat_path}")

        return compat_path

    def run_fix(self):
        """Execute the import fixes"""

        print("=" * 60)
        print("FIXING PROJ-MAPPER IMPORTS")
        print("=" * 60)

        # Analyze library structure
        lib_structure = self.analyze_library_structure()
        print(f"\n📚 Found {len(lib_structure)} opsvi libraries")

        # Create import mappings
        mappings = self.create_import_mappings(lib_structure)

        # Fix Python files
        print("\n🔧 Fixing imports...")
        python_files = list(self.app_path.glob("**/*.py"))

        fixed_count = 0
        for py_file in python_files:
            if ".venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            if self.fix_file_imports(py_file, mappings):
                fixed_count += 1
                print(f"  ✏️ Fixed: {py_file.name}")

        print(f"\n✅ Fixed {fixed_count} files")

        # Create setup script
        setup_path = self.add_path_setup_script()

        # Create compatibility layer
        compat_path = self.create_compatibility_layer()

        print("\n" + "=" * 60)
        print("IMPORT FIXES COMPLETE")
        print("=" * 60)
        print("\nNext steps:")
        print(f"1. Run: python {setup_path}")
        print("2. Test: python -m proj_mapper.cli analyze <project>")

        return True


def main():
    """Main execution"""

    fixer = ImportFixer()
    success = fixer.run_fix()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
