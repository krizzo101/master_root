#!/usr/bin/env python3
"""
Comprehensive analysis tool for answer_review.py hook
Performs static analysis, complexity metrics, and identifies optimization opportunities
"""

import ast
import os
import re
import sys
from collections import defaultdict
from pathlib import Path


def analyze_complexity(code):
    """Calculate cyclomatic complexity and other metrics."""
    tree = ast.parse(code)

    class ComplexityVisitor(ast.NodeVisitor):
        def __init__(self):
            self.functions = {}
            self.current_function = None
            self.complexity = defaultdict(int)

        def visit_FunctionDef(self, node):
            self.current_function = node.name
            self.functions[node.name] = {
                "lines": node.end_lineno - node.lineno + 1
                if hasattr(node, "end_lineno")
                else 0,
                "complexity": 1,  # Base complexity
                "args": len(node.args.args),
                "returns": 0,
                "branches": 0,
                "loops": 0,
            }
            self.generic_visit(node)
            self.current_function = None

        def visit_If(self, node):
            if self.current_function:
                self.functions[self.current_function]["complexity"] += 1
                self.functions[self.current_function]["branches"] += 1
            self.generic_visit(node)

        def visit_For(self, node):
            if self.current_function:
                self.functions[self.current_function]["complexity"] += 1
                self.functions[self.current_function]["loops"] += 1
            self.generic_visit(node)

        def visit_While(self, node):
            if self.current_function:
                self.functions[self.current_function]["complexity"] += 1
                self.functions[self.current_function]["loops"] += 1
            self.generic_visit(node)

        def visit_Return(self, node):
            if self.current_function:
                self.functions[self.current_function]["returns"] += 1
            self.generic_visit(node)

        def visit_Try(self, node):
            if self.current_function:
                self.functions[self.current_function]["complexity"] += len(
                    node.handlers
                )
            self.generic_visit(node)

    visitor = ComplexityVisitor()
    visitor.visit(tree)
    return visitor.functions


def analyze_patterns(code):
    """Identify code patterns and potential issues."""
    issues = []

    # Check for synchronous I/O in async context
    if "asyncio.run(" in code:
        sync_io_patterns = [
            (r"open\([^)]+\)", "Synchronous file I/O in async context"),
            (r"json\.load\(sys\.stdin\)", "Synchronous stdin read"),
            (r"print\(", "Synchronous stdout write (consider async logging)"),
        ]
        for pattern, message in sync_io_patterns:
            if re.search(pattern, code):
                issues.append(("PERFORMANCE", message))

    # Check for hardcoded values
    hardcoded = [
        (r"timeout=\d+", "Hardcoded timeout values"),
        (r"max_attempts\s*=\s*\d+", "Hardcoded retry limits"),
        (r"temperature\s*=\s*[\d.]+", "Hardcoded model parameters"),
    ]
    for pattern, message in hardcoded:
        if re.search(pattern, code, re.IGNORECASE):
            issues.append(("MAINTAINABILITY", message))

    # Check error handling
    if "except Exception:" in code:
        issues.append(
            ("ERROR_HANDLING", "Broad exception catching without specific handling")
        )

    # Check for missing type hints
    func_pattern = r"def\s+(\w+)\s*\([^)]*\)\s*:"
    funcs = re.findall(func_pattern, code)
    for func in funcs:
        if (
            f"def {func}(" in code
            and "->" not in code.split(f"def {func}(")[1].split(":")[0]
        ):
            issues.append(("TYPE_SAFETY", f"Missing return type hint for {func}()"))

    # Check for inefficient patterns
    if "for" in code and "append" in code:
        issues.append(
            ("PERFORMANCE", "Consider list comprehension instead of loop+append")
        )

    if re.search(r"json\.loads.*json\.dumps", code):
        issues.append(("PERFORMANCE", "Redundant JSON serialization/deserialization"))

    return issues


def analyze_dependencies(code):
    """Analyze import statements and dependencies."""
    imports = []
    tree = ast.parse(code)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(f"{module}.{alias.name}" if module else alias.name)

    # Categorize imports
    stdlib = []
    external = []
    local = []

    stdlib_modules = {
        "asyncio",
        "json",
        "os",
        "pathlib",
        "re",
        "sys",
        "time",
        "traceback",
        "typing",
    }

    for imp in imports:
        base = imp.split(".")[0]
        if base in stdlib_modules:
            stdlib.append(imp)
        elif imp.startswith("review_logging") or imp.startswith("."):
            local.append(imp)
        else:
            external.append(imp)

    return {"stdlib": stdlib, "external": external, "local": local}


def generate_report(file_path):
    """Generate comprehensive analysis report."""
    with open(file_path, "r") as f:
        code = f.read()

    print("# Code Analysis Report: answer_review.py\n")

    # File metrics
    lines = code.count("\n")
    non_empty = len([l for l in code.split("\n") if l.strip()])
    comments = len([l for l in code.split("\n") if l.strip().startswith("#")])

    print("## File Metrics")
    print(f"- Total lines: {lines}")
    print(f"- Non-empty lines: {non_empty}")
    print(f"- Comment lines: {comments}")
    print(f"- Code density: {(non_empty - comments) / non_empty * 100:.1f}%\n")

    # Complexity analysis
    print("## Complexity Analysis")
    functions = analyze_complexity(code)

    # Sort by complexity
    sorted_funcs = sorted(
        functions.items(), key=lambda x: x[1]["complexity"], reverse=True
    )

    print("| Function | Lines | Complexity | Branches | Loops |")
    print("|----------|-------|------------|----------|-------|")
    for name, metrics in sorted_funcs[:10]:
        print(
            f"| {name} | {metrics['lines']} | {metrics['complexity']} | {metrics['branches']} | {metrics['loops']} |"
        )

    # High complexity warnings
    high_complexity = [f for f, m in functions.items() if m["complexity"] > 10]
    if high_complexity:
        print(f"\n⚠️ **High complexity functions (>10):** {', '.join(high_complexity)}")

    large_functions = [f for f, m in functions.items() if m["lines"] > 50]
    if large_functions:
        print(f"⚠️ **Large functions (>50 lines):** {', '.join(large_functions)}")

    # Pattern analysis
    print("\n## Code Pattern Issues")
    issues = analyze_patterns(code)

    if issues:
        by_category = defaultdict(list)
        for category, issue in issues:
            by_category[category].append(issue)

        for category, items in sorted(by_category.items()):
            print(f"\n### {category}")
            for item in items:
                print(f"- {item}")
    else:
        print("✓ No significant issues found")

    # Dependency analysis
    print("\n## Dependencies")
    deps = analyze_dependencies(code)
    print(f"- Standard library: {len(deps['stdlib'])} modules")
    print(f"- External: {len(deps['external'])} packages")
    print(f"- Local: {len(deps['local'])} modules")

    if deps["external"]:
        print(
            f"\nExternal dependencies: {', '.join(set(d.split('.')[0] for d in deps['external']))}"
        )

    # Performance considerations
    print("\n## Performance Considerations")
    perf_issues = []

    if "asyncio.run" in code:
        count = code.count("asyncio.run")
        perf_issues.append(
            f"- {count} synchronous asyncio.run() calls (consider async context manager)"
        )

    if "time.sleep" in code:
        perf_issues.append("- Blocking sleep() calls found")

    if re.search(r"for .+ in .+:\s+.+\.append\(", code):
        perf_issues.append("- Loop+append pattern (consider list comprehension)")

    if not perf_issues:
        print("✓ No obvious performance issues")
    else:
        for issue in perf_issues:
            print(issue)

    # Security considerations
    print("\n## Security Considerations")
    sec_issues = []

    if "eval(" in code or "exec(" in code:
        sec_issues.append("- ⚠️ Dynamic code execution found")

    if re.search(r"os\.system\(|subprocess\.call\(", code):
        sec_issues.append("- Shell command execution")

    if "pickle" in code:
        sec_issues.append("- Pickle usage (potential deserialization vulnerability)")

    if not sec_issues:
        print("✓ No obvious security issues")
    else:
        for issue in sec_issues:
            print(issue)


if __name__ == "__main__":
    file_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "/home/opsvi/master_root/.claude/hooks/answer_review.py"
    )
    generate_report(file_path)
