#!/usr/bin/env python3
"""
Resource Discovery System - Helps agents find and use existing shared resources
Prevents wheel reinvention by showing what's available in libs/
"""

import os
import json
import ast
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
import importlib.util

@dataclass
class SharedResource:
    """Represents a shared resource available in libs/"""
    package_name: str  # e.g., "opsvi-llm"
    module_name: str   # e.g., "opsvi_llm"
    category: str      # e.g., "llm", "database", "auth"
    description: str
    key_features: List[str]
    main_classes: List[str]
    main_functions: List[str]
    dependencies: List[str]
    import_example: str
    usage_example: str
    path: str

class ResourceDiscovery:
    """Discover and catalog shared resources in the monorepo."""
    
    # Category mappings based on package names
    CATEGORY_PATTERNS = {
        "llm": ["llm", "ai", "gpt", "claude", "anthropic", "openai"],
        "database": ["data", "db", "database", "sql", "mongo", "redis"],
        "auth": ["auth", "security", "jwt", "oauth"],
        "api": ["api", "http", "rest", "graphql", "gateway"],
        "messaging": ["comm", "message", "queue", "pubsub", "event"],
        "orchestration": ["orch", "workflow", "pipeline", "coord"],
        "monitoring": ["monitor", "log", "trace", "metric", "observ"],
        "deployment": ["deploy", "docker", "k8s", "kubernetes"],
        "filesystem": ["fs", "file", "storage"],
        "mcp": ["mcp", "tool", "server"],
        "core": ["core", "foundation", "base", "common", "shared"],
        "testing": ["test", "mock", "fixture"],
        "documentation": ["doc", "docs", "markdown"],
        "memory": ["memory", "cache", "session", "state"],
        "agents": ["agent", "assistant", "bot"],
        "rag": ["rag", "retrieval", "embedding", "vector"],
    }
    
    def __init__(self, workspace_root: str = "/home/opsvi/master_root"):
        self.workspace = Path(workspace_root)
        self.libs_dir = self.workspace / "libs"
        self.resources: List[SharedResource] = []
        self.resource_index: Dict[str, List[SharedResource]] = {}
        
    def discover_all_resources(self) -> Dict[str, Any]:
        """Discover all shared resources in libs/"""
        
        if not self.libs_dir.exists():
            return {
                "status": "error",
                "message": f"libs directory not found at {self.libs_dir}"
            }
        
        # Find all opsvi-* packages
        for package_dir in self.libs_dir.glob("opsvi-*"):
            if package_dir.is_dir():
                self._analyze_package(package_dir)
        
        # Build category index
        self._build_category_index()
        
        return {
            "status": "success",
            "total_resources": len(self.resources),
            "categories": list(self.resource_index.keys()),
            "resources": [asdict(r) for r in self.resources]
        }
    
    def _analyze_package(self, package_dir: Path):
        """Analyze a single package to extract resource information."""
        
        package_name = package_dir.name
        module_name = package_name.replace("-", "_")
        module_dir = package_dir / module_name
        
        if not module_dir.exists():
            return
        
        # Determine category
        category = self._determine_category(package_name)
        
        # Extract package info
        description = self._get_package_description(package_dir)
        main_classes = []
        main_functions = []
        key_features = []
        
        # Analyze Python files
        for py_file in module_dir.rglob("*.py"):
            if "__pycache__" not in str(py_file):
                classes, functions, features = self._analyze_python_file(py_file)
                main_classes.extend(classes)
                main_functions.extend(functions)
                key_features.extend(features)
        
        # Remove duplicates
        main_classes = list(set(main_classes))[:10]  # Top 10
        main_functions = list(set(main_functions))[:10]  # Top 10
        key_features = list(set(key_features))[:5]  # Top 5
        
        # Get dependencies
        dependencies = self._get_dependencies(package_dir)
        
        # Create import and usage examples
        import_example = self._generate_import_example(module_name, main_classes, main_functions)
        usage_example = self._generate_usage_example(module_name, main_classes, main_functions, category)
        
        # Create resource
        resource = SharedResource(
            package_name=package_name,
            module_name=module_name,
            category=category,
            description=description,
            key_features=key_features if key_features else ["General utilities"],
            main_classes=main_classes,
            main_functions=main_functions,
            dependencies=dependencies,
            import_example=import_example,
            usage_example=usage_example,
            path=str(package_dir.relative_to(self.workspace))
        )
        
        self.resources.append(resource)
    
    def _determine_category(self, package_name: str) -> str:
        """Determine the category of a package based on its name."""
        
        name_lower = package_name.lower()
        
        for category, patterns in self.CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if pattern in name_lower:
                    return category
        
        return "utility"  # Default category
    
    def _get_package_description(self, package_dir: Path) -> str:
        """Extract package description from README or pyproject.toml."""
        
        # Try README first
        for readme_name in ["README.md", "README.rst", "README.txt"]:
            readme_path = package_dir / readme_name
            if readme_path.exists():
                content = readme_path.read_text()
                lines = content.split("\n")
                # Get first non-empty, non-header line
                for line in lines:
                    if line and not line.startswith("#") and not line.startswith("="):
                        return line.strip()[:200]  # First 200 chars
        
        # Try pyproject.toml
        pyproject_path = package_dir / "pyproject.toml"
        if pyproject_path.exists():
            content = pyproject_path.read_text()
            for line in content.split("\n"):
                if "description" in line and "=" in line:
                    desc = line.split("=", 1)[1].strip().strip('"')
                    return desc[:200]
        
        return f"Shared library for {package_dir.name}"
    
    def _analyze_python_file(self, py_file: Path) -> tuple:
        """Analyze a Python file to extract classes and functions."""
        
        classes = []
        functions = []
        features = []
        
        try:
            content = py_file.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Extract classes
                if isinstance(node, ast.ClassDef):
                    if not node.name.startswith("_"):
                        classes.append(node.name)
                        
                        # Check for special base classes
                        for base in node.bases:
                            if isinstance(base, ast.Name):
                                if "LLM" in base.id:
                                    features.append("LLM integration")
                                elif "Base" in base.id:
                                    features.append("Extensible base classes")
                                elif "Client" in base.id:
                                    features.append("Client implementations")
                
                # Extract functions
                elif isinstance(node, ast.FunctionDef):
                    if not node.name.startswith("_"):
                        functions.append(node.name)
                        
                        # Look for feature indicators in function names
                        name_lower = node.name.lower()
                        if "async" in name_lower or node.decorator_list:
                            for dec in node.decorator_list:
                                if isinstance(dec, ast.Name) and "async" in dec.id:
                                    features.append("Async support")
                        if "validate" in name_lower:
                            features.append("Input validation")
                        if "auth" in name_lower:
                            features.append("Authentication")
                        if "cache" in name_lower:
                            features.append("Caching")
        except:
            pass  # Ignore files that can't be parsed
        
        return classes, functions, features
    
    def _get_dependencies(self, package_dir: Path) -> List[str]:
        """Extract dependencies from pyproject.toml."""
        
        dependencies = []
        pyproject_path = package_dir / "pyproject.toml"
        
        if pyproject_path.exists():
            content = pyproject_path.read_text()
            in_deps = False
            
            for line in content.split("\n"):
                if "dependencies" in line and "=" in line and "[" in line:
                    in_deps = True
                    continue
                elif in_deps:
                    if "]" in line:
                        in_deps = False
                    elif line.strip() and not line.strip().startswith("#"):
                        dep = line.strip().strip('",')
                        if dep:
                            # Extract package name without version
                            dep_name = dep.split("[")[0].split(">")[0].split("<")[0].split("=")[0]
                            dependencies.append(dep_name)
        
        return dependencies[:10]  # Top 10 dependencies
    
    def _generate_import_example(
        self, 
        module_name: str, 
        classes: List[str], 
        functions: List[str]
    ) -> str:
        """Generate import example for the module."""
        
        examples = []
        
        if classes:
            examples.append(f"from {module_name} import {', '.join(classes[:3])}")
        
        if functions:
            examples.append(f"from {module_name} import {', '.join(functions[:3])}")
        
        if not examples:
            examples.append(f"import {module_name}")
        
        return "\n".join(examples)
    
    def _generate_usage_example(
        self,
        module_name: str,
        classes: List[str],
        functions: List[str],
        category: str
    ) -> str:
        """Generate usage example based on category and available items."""
        
        examples = {
            "llm": f"""
from {module_name} import LLMClient

client = LLMClient()
response = await client.generate("Your prompt here")
""",
            "database": f"""
from {module_name} import DatabaseClient

db = DatabaseClient(connection_string)
result = await db.query("SELECT * FROM table")
""",
            "auth": f"""
from {module_name} import AuthManager

auth = AuthManager()
token = auth.create_token(user_id)
valid = auth.verify_token(token)
""",
            "api": f"""
from {module_name} import APIClient

api = APIClient(base_url)
response = await api.get("/endpoint")
""",
            "mcp": f"""
from {module_name}.tools import ToolName

tool = ToolName()
result = tool.execute(params)
""",
            "filesystem": f"""
from {module_name} import FileManager

fm = FileManager()
content = fm.read_file(path)
fm.write_file(path, content)
""",
        }
        
        # Return category-specific example or generic
        if category in examples:
            return examples[category].strip()
        
        # Generic example
        if classes:
            class_name = classes[0]
            return f"""
from {module_name} import {class_name}

instance = {class_name}()
# Use instance methods as needed
"""
        elif functions:
            func_name = functions[0]
            return f"""
from {module_name} import {func_name}

result = {func_name}(params)
"""
        
        return f"import {module_name}"
    
    def _build_category_index(self):
        """Build an index of resources by category."""
        
        self.resource_index = {}
        
        for resource in self.resources:
            if resource.category not in self.resource_index:
                self.resource_index[resource.category] = []
            self.resource_index[resource.category].append(resource)
    
    def find_resources_for_need(self, need: str) -> Dict[str, Any]:
        """Find resources that match a specific need."""
        
        need_lower = need.lower()
        matches = []
        
        # Search in multiple places
        for resource in self.resources:
            score = 0
            
            # Check category match
            if resource.category in need_lower or need_lower in resource.category:
                score += 3
            
            # Check package name
            if need_lower in resource.package_name.lower():
                score += 2
            
            # Check description
            if need_lower in resource.description.lower():
                score += 2
            
            # Check features
            for feature in resource.key_features:
                if need_lower in feature.lower():
                    score += 1
            
            # Check class names
            for class_name in resource.main_classes:
                if need_lower in class_name.lower():
                    score += 1
            
            if score > 0:
                matches.append((score, resource))
        
        # Sort by score
        matches.sort(key=lambda x: x[0], reverse=True)
        
        return {
            "status": "success",
            "query": need,
            "matches": [asdict(r) for _, r in matches[:5]],  # Top 5 matches
            "recommendation": self._generate_recommendation(need, matches)
        }
    
    def _generate_recommendation(self, need: str, matches: List[tuple]) -> str:
        """Generate recommendation based on search results."""
        
        if not matches:
            return f"No existing resources found for '{need}'. Consider creating a new shared library in libs/opsvi-{need}/"
        
        top_match = matches[0][1]
        
        if matches[0][0] >= 3:  # High confidence match
            return f"Use existing library '{top_match.package_name}' which provides {top_match.description}"
        else:
            return f"Consider using '{top_match.package_name}' or create a new specialized library if it doesn't meet your needs"
    
    def check_before_building(self, functionality: str) -> Dict[str, Any]:
        """Check if functionality exists before building new code."""
        
        # Search for existing resources
        search_result = self.find_resources_for_need(functionality)
        
        response = {
            "status": "success",
            "functionality": functionality,
            "should_create_new": False,
            "existing_resources": search_result["matches"],
            "recommendation": search_result["recommendation"]
        }
        
        # Determine if new library should be created
        if not search_result["matches"]:
            response["should_create_new"] = True
            response["suggested_location"] = f"libs/opsvi-{functionality.lower().replace(' ', '-')}"
            response["action"] = "CREATE_NEW_LIBRARY"
        else:
            response["action"] = "USE_EXISTING"
            response["import_examples"] = [
                match["import_example"] for match in search_result["matches"][:3]
            ]
        
        return response
    
    def generate_resource_catalog(self) -> str:
        """Generate a markdown catalog of all available resources."""
        
        if not self.resources:
            self.discover_all_resources()
        
        catalog = ["# Available Shared Resources\n"]
        catalog.append("## Quick Reference\n")
        
        # Group by category
        for category in sorted(self.resource_index.keys()):
            resources = self.resource_index[category]
            catalog.append(f"\n### {category.title()}\n")
            
            for resource in resources:
                catalog.append(f"#### `{resource.package_name}`\n")
                catalog.append(f"**Module**: `{resource.module_name}`\n")
                catalog.append(f"**Description**: {resource.description}\n")
                
                if resource.key_features:
                    catalog.append(f"**Features**: {', '.join(resource.key_features)}\n")
                
                if resource.main_classes:
                    catalog.append(f"**Main Classes**: `{', '.join(resource.main_classes[:5])}`\n")
                
                catalog.append(f"\n**Import**:\n```python\n{resource.import_example}\n```\n")
                
                if resource.usage_example:
                    catalog.append(f"\n**Usage**:\n```python\n{resource.usage_example}\n```\n")
                
                catalog.append("\n---\n")
        
        return "\n".join(catalog)


# MCP Tool Interface
def resource_discovery_tool(action: str, **kwargs) -> Dict[str, Any]:
    """MCP tool for resource discovery."""
    
    discovery = ResourceDiscovery()
    
    actions = {
        "discover_all": discovery.discover_all_resources,
        "find_for_need": lambda need: discovery.find_resources_for_need(need),
        "check_before_building": lambda functionality: discovery.check_before_building(functionality),
        "generate_catalog": lambda: {
            "status": "success",
            "catalog": discovery.generate_resource_catalog()
        }
    }
    
    if action not in actions:
        return {
            "status": "error",
            "message": f"Unknown action: {action}",
            "available_actions": list(actions.keys())
        }
    
    try:
        if action == "find_for_need":
            return actions[action](kwargs.get("need", ""))
        elif action == "check_before_building":
            return actions[action](kwargs.get("functionality", ""))
        else:
            return actions[action]()
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error executing {action}: {str(e)}"
        }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Resource Discovery System")
        print("=" * 50)
        print("Usage: resource_discovery.py <action> [args...]")
        print("\nActions:")
        print("  discover_all - Discover all shared resources")
        print("  find_for_need <need> - Find resources for a specific need")
        print("  check_before_building <functionality> - Check before building new code")
        print("  generate_catalog - Generate markdown catalog")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "find_for_need" and len(sys.argv) > 2:
        result = resource_discovery_tool(action, need=" ".join(sys.argv[2:]))
    elif action == "check_before_building" and len(sys.argv) > 2:
        result = resource_discovery_tool(action, functionality=" ".join(sys.argv[2:]))
    else:
        result = resource_discovery_tool(action)
    
    print(json.dumps(result, indent=2))