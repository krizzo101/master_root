#!/usr/bin/env python3
"""
Project Intelligence Wrapper for Claude/Agents

This module provides a simplified, unified interface to the project intelligence
system, making it trivial for agents to access and use the indexed knowledge.

Usage:
    from proj_intel_wrapper import intel
    
    # Find files
    files = intel.find("ConsultAgent")
    
    # Get architecture info
    arch = intel.architecture("agents")
    
    # Check dependencies
    deps = intel.dependencies("src/accf/agents/consult_agent.py")
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

# Add ACCF tools to path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "ACCF" / "src"))

try:
    from accf.tools.gatekeeper_data_tools import (
        ProjectIntelligenceQuerier,
        DataPackager,
        RelevanceScorer,
        FileContext,
    )
    from accf.tools.gatekeeper_query_templates import generate_query_template

    GATEKEEPER_AVAILABLE = True
except ImportError:
    GATEKEEPER_AVAILABLE = False
    print("Warning: Gatekeeper tools not available, using fallback methods")


@dataclass
class IntelResult:
    """Unified result format for intelligence queries"""

    query_type: str
    results: List[Any]
    count: int
    relevance_scores: Optional[List[float]] = None
    suggestions: Optional[List[str]] = None


class ProjectIntelligenceWrapper:
    """Simplified interface to project intelligence"""

    def __init__(self, intel_dir: str = ".proj-intel"):
        self.intel_dir = Path(intel_dir)

        # Check if intelligence directory exists
        if not self.intel_dir.exists():
            raise FileNotFoundError(
                f"Project intelligence not found at {self.intel_dir}\n"
                "Run 'project-intelligence full-package' to generate it."
            )

        self.active_dir = self.intel_dir

        # Initialize Gatekeeper if available
        if GATEKEEPER_AVAILABLE:
            self.querier = ProjectIntelligenceQuerier(str(self.active_dir))
            self.packager = DataPackager(self.querier)
            self.scorer = RelevanceScorer(self.querier)
        else:
            self.querier = None

        # Load indices for fallback
        self._load_fallback_indices()

    def _load_fallback_indices(self):
        """Load basic indices for fallback operations"""
        try:
            with open(self.active_dir / "symbol_index.json") as f:
                self.symbol_index = json.load(f)
        except:
            self.symbol_index = {}

        try:
            with open(self.active_dir / "reverse_index.json") as f:
                self.reverse_index = json.load(f)
        except:
            self.reverse_index = {}

    def find(self, query: str, max_results: int = 10) -> IntelResult:
        """Find files, symbols, or patterns"""
        results = []

        # Try symbol search first
        if query in self.symbol_index:
            symbol_hits = self.symbol_index[query]
            results.extend([{"type": "symbol", "data": hit} for hit in symbol_hits])

        # Then file pattern search
        if GATEKEEPER_AVAILABLE and self.querier:
            files = self.querier.find_files_by_pattern([query])
            for file_path in files[:max_results]:
                context = self.querier.get_file_context(file_path)
                if context:
                    results.append({"type": "file", "data": context})
        else:
            # Fallback: simple pattern matching
            with open(self.active_dir / "file_elements.min.jsonl") as f:
                for line in f:
                    data = json.loads(line)
                    if query.lower() in data["path"].lower():
                        results.append({"type": "file", "data": data})
                        if len(results) >= max_results:
                            break

        return IntelResult(
            query_type="find",
            results=results,
            count=len(results),
            suggestions=[f"Found {len(results)} matches for '{query}'"],
        )

    def architecture(self, component: str = None) -> IntelResult:
        """Get architectural information"""
        results = []

        with open(self.active_dir / "agent_architecture.jsonl") as f:
            for line in f:
                data = json.loads(line)
                if component:
                    if (
                        component.lower()
                        in data.get("data", {}).get("file_path", "").lower()
                    ):
                        results.append(data["data"])
                else:
                    results.append(data["data"])

                if len(results) >= 50:  # Limit for performance
                    break

        return IntelResult(
            query_type="architecture",
            results=results,
            count=len(results),
            suggestions=[f"Found {len(results)} architectural components"],
        )

    def dependencies(self, file_path: str) -> IntelResult:
        """Get file dependencies and relationships"""
        results = []

        if GATEKEEPER_AVAILABLE and self.querier:
            related = self.querier.find_related_files(file_path)
            results = [{"file": f, "relationship": "related"} for f in related]
        elif file_path in self.reverse_index:
            # Use reverse index for basic dependency info
            entries = self.reverse_index[file_path]
            results = [{"type": "index_entry", "data": e} for e in entries[:10]]

        return IntelResult(
            query_type="dependencies",
            results=results,
            count=len(results),
            suggestions=[f"Found {len(results)} related files"],
        )

    def stats(self, file_path: str = None) -> IntelResult:
        """Get statistics about files or the project"""
        if file_path:
            # Single file stats
            with open(self.active_dir / "file_elements.min.jsonl") as f:
                for line in f:
                    data = json.loads(line)
                    if data["path"] == file_path:
                        return IntelResult(query_type="stats", results=[data], count=1)
        else:
            # Project-wide stats
            total_files = 0
            total_functions = 0
            total_classes = 0

            with open(self.active_dir / "file_elements.min.jsonl") as f:
                for line in f:
                    data = json.loads(line)
                    total_files += 1
                    total_functions += data.get("fn_count", 0)
                    total_classes += data.get("class_count", 0)

            return IntelResult(
                query_type="stats",
                results=[
                    {
                        "total_files": total_files,
                        "total_functions": total_functions,
                        "total_classes": total_classes,
                        "avg_functions_per_file": total_functions / max(total_files, 1),
                        "avg_classes_per_file": total_classes / max(total_files, 1),
                    }
                ],
                count=1,
            )

        return IntelResult(query_type="stats", results=[], count=0)

    def suggest_context(
        self, task_description: str, max_files: int = 20
    ) -> IntelResult:
        """Suggest relevant files for a task"""
        if GATEKEEPER_AVAILABLE:
            # Use Gatekeeper's intelligent selection
            template = generate_query_template(
                "architecture_question", keywords=task_description.split()[:5]
            )
            package = self.packager.create_package(template)

            results = [
                {
                    "path": f.path,
                    "relevance": f.relevance_score,
                    "reason": f.inclusion_reason,
                }
                for f in package.files[:max_files]
            ]

            return IntelResult(
                query_type="context_suggestion",
                results=results,
                count=len(results),
                relevance_scores=[f.relevance_score for f in package.files[:max_files]],
                suggestions=["Files ranked by relevance to task"],
            )
        else:
            # Fallback: keyword matching
            keywords = task_description.lower().split()[:5]
            matches = []

            with open(self.active_dir / "file_elements.min.jsonl") as f:
                for line in f:
                    data = json.loads(line)
                    path_lower = data["path"].lower()
                    score = sum(1 for kw in keywords if kw in path_lower)
                    if score > 0:
                        matches.append((data["path"], score))

            matches.sort(key=lambda x: x[1], reverse=True)
            results = [
                {"path": p, "keyword_matches": s} for p, s in matches[:max_files]
            ]

            return IntelResult(
                query_type="context_suggestion",
                results=results,
                count=len(results),
                suggestions=["Files matched by keywords"],
            )

    def refresh_check(self) -> Dict[str, Any]:
        """Check if intelligence data needs refresh"""
        try:
            with open(self.active_dir / "proj_intel_manifest.json") as f:
                manifest = json.load(f)
        except FileNotFoundError:
            return {
                "error": "Manifest not found",
                "needs_refresh": True,
                "command": "project-intelligence full-package",
            }

        from datetime import datetime, timezone

        generated = datetime.fromisoformat(
            manifest["generated_at"].replace("Z", "+00:00")
        )
        now = datetime.now(timezone.utc)
        age_hours = (now - generated).total_seconds() / 3600

        return {
            "generated_at": manifest["generated_at"],
            "age_hours": round(age_hours, 1),
            "needs_refresh": age_hours > 24,
            "command": "project-intelligence full-package" if age_hours > 24 else None,
        }


# Global singleton for easy access
intel = ProjectIntelligenceWrapper()


# CLI interface for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python proj_intel_wrapper.py <command> [args]")
        print("Commands:")
        print("  find <query>         - Find files/symbols")
        print("  arch [component]     - Show architecture")
        print("  deps <file>          - Show dependencies")
        print("  stats [file]         - Show statistics")
        print("  suggest <task>       - Suggest files for task")
        print("  check                - Check freshness")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "find" and len(sys.argv) > 2:
        result = intel.find(sys.argv[2])
        print(f"Found {result.count} results:")
        for r in result.results[:10]:
            print(f"  - {r}")

    elif cmd == "arch":
        component = sys.argv[2] if len(sys.argv) > 2 else None
        result = intel.architecture(component)
        print(f"Architecture components: {result.count}")
        for r in result.results[:5]:
            print(f"  - {r.get('name', 'Unknown')} in {r.get('file_path', 'Unknown')}")

    elif cmd == "deps" and len(sys.argv) > 2:
        result = intel.dependencies(sys.argv[2])
        print(f"Dependencies: {result.count}")
        for r in result.results:
            print(f"  - {r}")

    elif cmd == "stats":
        file_path = sys.argv[2] if len(sys.argv) > 2 else None
        result = intel.stats(file_path)
        for r in result.results:
            print(json.dumps(r, indent=2))

    elif cmd == "suggest" and len(sys.argv) > 2:
        task = " ".join(sys.argv[2:])
        result = intel.suggest_context(task)
        print(f"Suggested files for '{task}':")
        for r in result.results:
            print(f"  - {r}")

    elif cmd == "check":
        status = intel.refresh_check()
        print(json.dumps(status, indent=2))

    else:
        print(f"Unknown command: {cmd}")
