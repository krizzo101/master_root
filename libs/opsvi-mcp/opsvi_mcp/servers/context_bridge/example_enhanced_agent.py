"""
Example: Enhanced Research Agent with Context Bridge Integration

Demonstrates how to upgrade existing agents with IDE context awareness.
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from .client import EnhancedAgentBase, ContextBridgeClient
from .models import DiagnosticSeverity


class ContextAwareResearchAgent(EnhancedAgentBase):
    """
    Research agent that automatically uses IDE context

    Features:
    - Automatically searches in context of current file
    - Prioritizes results based on diagnostics
    - Understands selected code for focused research
    """

    def __init__(self):
        super().__init__("research_agent")
        self.search_history: List[Dict] = []

    async def execute_core(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        Execute research task with context enhancement

        Args:
            task: Research query/task
            **kwargs: Additional parameters

        Returns:
            Research results with context relevance
        """
        results = {
            "task": task,
            "timestamp": datetime.utcnow().isoformat(),
            "context_used": False,
            "findings": [],
        }

        # Check if we have context
        if self.current_context:
            results["context_used"] = True

            # 1. Focus on current file if relevant
            if self.current_context.active_file:
                results["focused_file"] = self.current_context.active_file
                file_results = await self._search_in_file(
                    task, self.current_context.active_file
                )
                results["findings"].extend(file_results)

            # 2. Consider diagnostics for problem-solving queries
            if "fix" in task.lower() or "error" in task.lower():
                diagnostic_insights = await self._analyze_diagnostics(task)
                results["diagnostic_insights"] = diagnostic_insights

            # 3. Use selection for precise context
            if self.current_context.selection:
                selection_analysis = await self._analyze_selection(
                    task, self.current_context.selection
                )
                results["selection_analysis"] = selection_analysis

        # 4. Perform broader search
        broad_results = await self._perform_broad_search(task)
        results["findings"].extend(broad_results)

        # 5. Rank results by relevance
        results["findings"] = self._rank_by_relevance(
            results["findings"], self.current_context
        )

        # Store in history
        self.search_history.append(results)

        return results

    async def _search_in_file(self, query: str, file_path: str) -> List[Dict]:
        """Search within specific file"""
        # Simplified example - would use actual search tools
        return [
            {
                "source": file_path,
                "relevance": 0.9,
                "snippet": f"Found '{query}' in current file",
                "line_numbers": [10, 25, 40],
            }
        ]

    async def _analyze_diagnostics(self, query: str) -> Dict:
        """Analyze diagnostics for insights"""
        if not self.current_context:
            return {}

        errors = [
            d
            for d in self.current_context.diagnostics
            if d.severity == DiagnosticSeverity.ERROR
        ]

        warnings = [
            d
            for d in self.current_context.diagnostics
            if d.severity == DiagnosticSeverity.WARNING
        ]

        return {
            "error_count": len(errors),
            "warning_count": len(warnings),
            "top_errors": [
                {
                    "message": e.message,
                    "line": e.line,
                    "suggestion": f"Consider fixing: {e.message}",
                }
                for e in errors[:3]
            ],
        }

    async def _analyze_selection(self, query: str, selection) -> Dict:
        """Analyze selected code"""
        return {
            "selected_lines": f"{selection.start_line}-{selection.end_line}",
            "code_preview": selection.selected_text[:200],
            "analysis": f"Selected code appears to be related to: {query}",
        }

    async def _perform_broad_search(self, query: str) -> List[Dict]:
        """Perform broader codebase search"""
        # Simplified - would use actual search
        return [
            {
                "source": "codebase_search",
                "relevance": 0.5,
                "snippet": f"General search result for '{query}'",
                "files": ["main.py", "utils.py", "test.py"],
            }
        ]

    def _rank_by_relevance(self, findings: List[Dict], context) -> List[Dict]:
        """Rank findings by relevance to current context"""
        if not context or not context.active_file:
            return findings

        # Boost relevance for current file
        for finding in findings:
            if finding.get("source") == context.active_file:
                finding["relevance"] *= 1.5

        # Sort by relevance
        return sorted(findings, key=lambda x: x.get("relevance", 0), reverse=True)


class ContextAwareCodeGenerator(EnhancedAgentBase):
    """
    Code generation agent with IDE awareness

    Features:
    - Generates code that fits current file style
    - Automatically fixes diagnostics
    - Respects project patterns
    """

    def __init__(self):
        super().__init__("code_generator")

    async def execute_core(self, task: str, **kwargs) -> str:
        """
        Generate code with context awareness

        Args:
            task: Code generation request
            **kwargs: Additional parameters

        Returns:
            Generated code
        """
        # Analyze current file for style
        style_hints = await self._analyze_file_style()

        # Check for relevant diagnostics
        fixes_needed = await self._identify_needed_fixes()

        # Generate code
        code = await self._generate_code(task, style_hints, fixes_needed)

        return code

    async def _analyze_file_style(self) -> Dict:
        """Analyze current file for coding style"""
        if not self.current_context or not self.current_context.active_file:
            return {}

        # Simplified analysis
        return {
            "indent": "    ",  # 4 spaces
            "quotes": "double",
            "line_length": 88,
            "docstring_style": "google",
        }

    async def _identify_needed_fixes(self) -> List[str]:
        """Identify fixes needed based on diagnostics"""
        if not self.current_context:
            return []

        fixes = []
        for diag in self.current_context.diagnostics:
            if diag.severity == DiagnosticSeverity.ERROR:
                fixes.append(f"Fix: {diag.message} at line {diag.line}")

        return fixes

    async def _generate_code(
        self, task: str, style_hints: Dict, fixes_needed: List[str]
    ) -> str:
        """Generate actual code"""
        # Simplified generation
        code_lines = [
            "# Generated by Context-Aware Code Generator",
            f"# Task: {task}",
            "",
        ]

        if fixes_needed:
            code_lines.append("# Addressing the following issues:")
            for fix in fixes_needed:
                code_lines.append(f"#  - {fix}")
            code_lines.append("")

        # Add actual code
        code_lines.extend(
            [
                "def generated_function():",
                '    """Function generated based on context"""',
                "    # Implementation based on current file style",
                "    pass",
            ]
        )

        return "\n".join(code_lines)


async def demo_enhanced_agents():
    """
    Demonstrate enhanced agents with context awareness
    """
    print("=== Context-Aware Agent Demo ===\n")

    # Initialize agents
    research_agent = ContextAwareResearchAgent()
    code_agent = ContextAwareCodeGenerator()

    # Simulate IDE context
    from .models import IDEContext, DiagnosticInfo, FileSelection

    mock_context = IDEContext(
        active_file="/home/opsvi/master_root/example.py",
        selection=FileSelection(
            file_path="/home/opsvi/master_root/example.py",
            start_line=15,
            start_column=0,
            end_line=20,
            end_column=0,
            selected_text="def process_data(data):\n    return data",
        ),
        diagnostics=[
            DiagnosticInfo(
                file_path="/home/opsvi/master_root/example.py",
                line=17,
                column=5,
                severity=DiagnosticSeverity.ERROR,
                message="'result' is not defined",
            )
        ],
        project_root="/home/opsvi/master_root",
        open_tabs=["/home/opsvi/master_root/example.py"],
    )

    # Mock context client
    research_agent.current_context = mock_context
    code_agent.current_context = mock_context

    # Example 1: Context-aware research
    print("1. Research with context:")
    research_results = await research_agent.execute_core(
        "Find all usages of process_data function"
    )
    print(f"   Context used: {research_results['context_used']}")
    print(f"   Focused file: {research_results.get('focused_file', 'None')}")
    print(f"   Findings: {len(research_results['findings'])} results")
    if research_results.get("diagnostic_insights"):
        print(
            f"   Errors found: {research_results['diagnostic_insights']['error_count']}"
        )
    print()

    # Example 2: Context-aware code generation
    print("2. Code generation with context:")
    generated_code = await code_agent.execute_core("Fix the undefined variable error")
    print("   Generated code:")
    for line in generated_code.split("\n")[:10]:
        print(f"   {line}")
    print()

    # Example 3: Working without context
    print("3. Working without context (fallback):")
    research_agent.current_context = None
    results_no_context = await research_agent.execute_core(
        "Search for authentication functions"
    )
    print(f"   Context used: {results_no_context['context_used']}")
    print(f"   Still found: {len(results_no_context['findings'])} results")


if __name__ == "__main__":
    # Run demonstration
    asyncio.run(demo_enhanced_agents())
