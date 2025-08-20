"""
TODO Discovery & Classification Engine

Discovers, analyzes, and prioritizes TODO items across the codebase
using intelligent parsing and dependency analysis.
"""

import ast
import hashlib
import json
import logging
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class TodoItem:
    """Represents a discovered TODO item"""

    id: str
    file_path: str
    line_number: int
    content: str
    category: str  # TODO, FIXME, HACK, BUG, OPTIMIZE, REFACTOR
    priority: int  # 1-5, 5 being highest
    context: Dict[str, Any]
    dependencies: List[str]
    estimated_complexity: str  # simple, medium, complex
    suggested_agent: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TodoDiscoveryEngine:
    """Discovers and classifies TODO items in the codebase"""

    TODO_PATTERNS = {
        "TODO": r"#\s*TODO[\s:]+(.+)",
        "FIXME": r"#\s*FIXME[\s:]+(.+)",
        "HACK": r"#\s*HACK[\s:]+(.+)",
        "BUG": r"#\s*BUG[\s:]+(.+)",
        "OPTIMIZE": r"#\s*OPTIMIZE[\s:]+(.+)",
        "REFACTOR": r"#\s*REFACTOR[\s:]+(.+)",
        "XXX": r"#\s*XXX[\s:]+(.+)",
    }

    COMPLEXITY_INDICATORS = {
        "simple": ["typo", "rename", "comment", "import", "constant"],
        "medium": ["implement", "add", "update", "modify", "enhance"],
        "complex": ["refactor", "redesign", "optimize", "architect", "integrate"],
    }

    AGENT_MAPPING = {
        "TODO": "sdlc-development",
        "FIXME": "sdlc-testing",
        "BUG": "test-remediation-specialist",
        "HACK": "refactoring-master",
        "OPTIMIZE": "excellence-optimizer",
        "REFACTOR": "refactoring-master",
        "XXX": "code-analyzer",
    }

    def __init__(self, project_root: str = "/home/opsvi/master_root"):
        self.project_root = Path(project_root)
        self.todos: List[TodoItem] = []
        self.dependency_graph: Dict[str, List[str]] = defaultdict(list)
        self.file_cache: Dict[str, str] = {}

    def discover_todos(
        self, paths: Optional[List[str]] = None, exclude_patterns: List[str] = None
    ) -> List[TodoItem]:
        """Discover all TODO items in the codebase"""

        if paths is None:
            paths = ["libs", "apps", "scripts", "tests"]

        if exclude_patterns is None:
            exclude_patterns = ["__pycache__", ".git", "node_modules", ".venv"]

        self.todos.clear()

        for base_path in paths:
            full_path = self.project_root / base_path
            if full_path.exists():
                self._scan_directory(full_path, exclude_patterns)

        # Analyze dependencies and set priorities
        self._analyze_dependencies()
        self._calculate_priorities()

        return self.todos

    def _scan_directory(self, directory: Path, exclude_patterns: List[str]):
        """Recursively scan directory for TODO items"""

        for item in directory.rglob("*.py"):
            # Skip excluded patterns
            if any(pattern in str(item) for pattern in exclude_patterns):
                continue

            self._scan_file(item)

    def _scan_file(self, file_path: Path):
        """Scan a single file for TODO items"""

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.file_cache[str(file_path)] = content

            lines = content.split("\n")

            for line_num, line in enumerate(lines, 1):
                for category, pattern in self.TODO_PATTERNS.items():
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        todo_content = match.group(1).strip()
                        context = self._extract_context(file_path, line_num, lines)

                        todo_item = TodoItem(
                            id=self._generate_id(file_path, line_num, todo_content),
                            file_path=str(file_path),
                            line_number=line_num,
                            content=todo_content,
                            category=category,
                            priority=3,  # Default, will be updated
                            context=context,
                            dependencies=[],
                            estimated_complexity=self._estimate_complexity(
                                todo_content
                            ),
                            suggested_agent=self.AGENT_MAPPING.get(
                                category, "sdlc-development"
                            ),
                            created_at=datetime.now().isoformat(),
                        )

                        self.todos.append(todo_item)

        except Exception as e:
            logger.error(f"Error scanning file {file_path}: {e}")

    def _extract_context(
        self, file_path: Path, line_num: int, lines: List[str]
    ) -> Dict[str, Any]:
        """Extract context around the TODO item"""

        context = {
            "function": None,
            "class": None,
            "imports": [],
            "surrounding_code": [],
            "file_type": self._determine_file_type(file_path),
        }

        # Get surrounding lines
        start = max(0, line_num - 6)
        end = min(len(lines), line_num + 5)
        context["surrounding_code"] = lines[start:end]

        # Try to parse AST to get function/class context
        try:
            tree = ast.parse(self.file_cache[str(file_path)])
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if hasattr(node, "lineno") and node.lineno <= line_num:
                        if hasattr(node, "end_lineno") and node.end_lineno >= line_num:
                            context["function"] = node.name

                elif isinstance(node, ast.ClassDef):
                    if hasattr(node, "lineno") and node.lineno <= line_num:
                        if hasattr(node, "end_lineno") and node.end_lineno >= line_num:
                            context["class"] = node.name

                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        context["imports"].append(alias.name)

                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        context["imports"].append(f"{module}.{alias.name}")

        except Exception:
            pass  # AST parsing failed, continue without it

        return context

    def _determine_file_type(self, file_path: Path) -> str:
        """Determine the type of file based on path and name"""

        path_str = str(file_path).lower()

        if "test" in path_str:
            return "test"
        elif "agent" in path_str:
            return "agent"
        elif "api" in path_str or "route" in path_str:
            return "api"
        elif "model" in path_str or "schema" in path_str:
            return "model"
        elif "util" in path_str or "helper" in path_str:
            return "utility"
        elif "config" in path_str or "setting" in path_str:
            return "config"
        else:
            return "general"

    def _estimate_complexity(self, content: str) -> str:
        """Estimate the complexity of implementing the TODO"""

        content_lower = content.lower()

        for complexity, indicators in self.COMPLEXITY_INDICATORS.items():
            if any(indicator in content_lower for indicator in indicators):
                return complexity

        return "medium"  # Default

    def _generate_id(self, file_path: Path, line_num: int, content: str) -> str:
        """Generate unique ID for TODO item"""

        data = f"{file_path}:{line_num}:{content}"
        return hashlib.sha256(data.encode()).hexdigest()[:12]

    def _analyze_dependencies(self):
        """Analyze dependencies between TODO items"""

        # Group TODOs by file
        todos_by_file = defaultdict(list)
        for todo in self.todos:
            todos_by_file[todo.file_path].append(todo)

        # Analyze import dependencies
        for file_path, file_todos in todos_by_file.items():
            if file_path in self.file_cache:
                try:
                    tree = ast.parse(self.file_cache[file_path])
                    imports = []

                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imports.append(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                imports.append(node.module)

                    # Check if imported modules have TODOs
                    for import_name in imports:
                        for other_file, other_todos in todos_by_file.items():
                            if import_name in other_file:
                                for todo in file_todos:
                                    for other_todo in other_todos:
                                        if other_todo.id != todo.id:
                                            todo.dependencies.append(other_todo.id)

                except Exception:
                    pass  # AST parsing failed

    def _calculate_priorities(self):
        """Calculate priority scores for TODO items"""

        for todo in self.todos:
            priority = 3  # Base priority

            # Adjust based on category
            if todo.category in ["BUG", "FIXME"]:
                priority += 2
            elif todo.category in ["HACK", "XXX"]:
                priority += 1
            elif todo.category == "OPTIMIZE":
                priority -= 1

            # Adjust based on file type
            if todo.context["file_type"] == "test":
                priority += 1
            elif todo.context["file_type"] == "api":
                priority += 1

            # Adjust based on dependencies
            if len(todo.dependencies) > 3:
                priority += 1
            elif len(todo.dependencies) == 0:
                priority -= 1

            # Adjust based on complexity
            if todo.estimated_complexity == "simple":
                priority += 1
            elif todo.estimated_complexity == "complex":
                priority -= 1

            # Clamp to 1-5 range
            todo.priority = max(1, min(5, priority))

    def classify_todos(self) -> Dict[str, List[TodoItem]]:
        """Classify TODOs by various criteria"""

        classifications = {
            "by_category": defaultdict(list),
            "by_complexity": defaultdict(list),
            "by_priority": defaultdict(list),
            "by_agent": defaultdict(list),
            "by_file_type": defaultdict(list),
        }

        for todo in self.todos:
            classifications["by_category"][todo.category].append(todo)
            classifications["by_complexity"][todo.estimated_complexity].append(todo)
            classifications["by_priority"][todo.priority].append(todo)
            classifications["by_agent"][todo.suggested_agent].append(todo)
            classifications["by_file_type"][todo.context["file_type"]].append(todo)

        return classifications

    def export_to_json(self, output_path: str):
        """Export discovered TODOs to JSON file"""

        data = {
            "metadata": {
                "total_todos": len(self.todos),
                "discovered_at": datetime.now().isoformat(),
                "project_root": str(self.project_root),
            },
            "todos": [todo.to_dict() for todo in self.todos],
            "classifications": self.classify_todos(),
        }

        # Convert defaultdicts to regular dicts for JSON serialization
        for key in data["classifications"]:
            data["classifications"][key] = {
                k: [t.to_dict() for t in v]
                for k, v in data["classifications"][key].items()
            }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Exported {len(self.todos)} TODOs to {output_path}")

    def get_implementation_queue(
        self, max_items: int = 10, complexity_filter: Optional[str] = None
    ) -> List[TodoItem]:
        """Get prioritized queue of TODOs for implementation"""

        filtered_todos = self.todos

        if complexity_filter:
            filtered_todos = [
                t for t in filtered_todos if t.estimated_complexity == complexity_filter
            ]

        # Sort by priority (descending) and complexity (ascending)
        complexity_order = {"simple": 1, "medium": 2, "complex": 3}
        sorted_todos = sorted(
            filtered_todos,
            key=lambda t: (
                -t.priority,
                complexity_order.get(t.estimated_complexity, 2),
            ),
        )

        return sorted_todos[:max_items]
