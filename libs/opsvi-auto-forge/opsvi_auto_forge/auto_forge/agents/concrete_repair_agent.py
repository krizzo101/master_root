"""Concrete implementation of BaseRepairAgent with actual repair logic."""

import logging
import re
from typing import List

from .base_repair_agent import BaseRepairAgent, RepairRequest, RepairResult, Artifact

logger = logging.getLogger(__name__)


class ConcreteRepairAgent(BaseRepairAgent):
    """Concrete implementation of repair agent with actual repair capabilities."""

    def __init__(
        self,
        name: str = "ConcreteRepairAgent",
        description: str = "Concrete repair agent with multiple repair capabilities",
        repair_capabilities: List[str] = None,
        neo4j_client=None,
        model: str = "gpt-4.1-mini",
        temperature: float = 0.1,
        max_tokens: int = 4000,
    ):
        if repair_capabilities is None:
            repair_capabilities = [
                "syntax_error",
                "security_vulnerability",
                "performance_issue",
                "code_style",
                "missing_import",
                "type_error",
            ]

        super().__init__(
            name=name,
            description=description,
            repair_capabilities=repair_capabilities,
            neo4j_client=neo4j_client,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def _perform_repair(self, request: RepairRequest) -> RepairResult:
        """Perform the actual repair operation."""
        try:
            issue_type = request.issue_type
            artifact = request.artifact
            content = artifact.metadata.get("content", "")

            if not content:
                return RepairResult(
                    success=False,
                    original_artifact=artifact,
                    repair_type=issue_type,
                    confidence=0.0,
                    error_message="No content found in artifact",
                )

            # Route to specific repair method based on issue type
            if issue_type == "syntax_error":
                return await self._repair_syntax_error(request)
            elif issue_type == "security_vulnerability":
                return await self._repair_security_vulnerability(request)
            elif issue_type == "performance_issue":
                return await self._repair_performance_issue(request)
            elif issue_type == "code_style":
                return await self._repair_code_style(request)
            elif issue_type == "missing_import":
                return await self._repair_missing_import(request)
            elif issue_type == "type_error":
                return await self._repair_type_error(request)
            else:
                return await self._repair_generic(request)

        except Exception as e:
            logger.error(f"Repair operation failed: {e}", exc_info=True)
            return RepairResult(
                success=False,
                original_artifact=request.artifact,
                repair_type=request.issue_type,
                confidence=0.0,
                error_message=f"Repair operation failed: {str(e)}",
            )

    async def _repair_syntax_error(self, request: RepairRequest) -> RepairResult:
        """Repair syntax errors in code."""
        content = request.artifact.metadata.get("content", "")
        changes_made = []

        # Simple syntax error repairs
        fixed_content = content

        # Fix common Python syntax errors
        # Remove trailing whitespace
        fixed_content = re.sub(r"[ \t]+$", "", fixed_content, flags=re.MULTILINE)

        # Fix common indentation issues
        lines = fixed_content.split("\n")
        fixed_lines = []
        for line in lines:
            # Ensure consistent indentation
            if line.strip() and not line.startswith("#"):
                # Count leading spaces
                leading_spaces = len(line) - len(line.lstrip())
                if leading_spaces % 4 != 0:
                    # Fix to nearest 4-space boundary
                    fixed_spaces = (leading_spaces // 4) * 4
                    line = " " * fixed_spaces + line.lstrip()
            fixed_lines.append(line)

        fixed_content = "\n".join(fixed_lines)

        if fixed_content != content:
            changes_made.append("Fixed indentation and whitespace issues")

        # Create fixed artifact
        fixed_artifact = Artifact(
            id=request.artifact.id,
            type=request.artifact.type,
            metadata={
                **request.artifact.metadata,
                "content": fixed_content,
                "repaired": True,
                "repair_type": "syntax_error",
            },
        )

        return RepairResult(
            success=True,
            fixed_artifact=fixed_artifact,
            original_artifact=request.artifact,
            repair_type="syntax_error",
            changes_made=changes_made,
            confidence=0.8 if changes_made else 0.5,
        )

    async def _repair_security_vulnerability(
        self, request: RepairRequest
    ) -> RepairResult:
        """Repair security vulnerabilities."""
        content = request.artifact.metadata.get("content", "")
        changes_made = []

        fixed_content = content

        # Fix common security issues
        # Replace hardcoded passwords with environment variables
        password_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
        ]

        for pattern in password_patterns:
            matches = re.findall(pattern, fixed_content, re.IGNORECASE)
            for match in matches:
                if "password" in match.lower():
                    replacement = 'password = os.getenv("PASSWORD")'
                elif "api_key" in match.lower():
                    replacement = 'api_key = os.getenv("API_KEY")'
                elif "secret" in match.lower():
                    replacement = 'secret = os.getenv("SECRET")'
                else:
                    replacement = 'value = os.getenv("SECURE_VALUE")'

                fixed_content = fixed_content.replace(match, replacement)
                changes_made.append(
                    "Replaced hardcoded credential with environment variable"
                )

        # Add import os if needed
        if "os.getenv(" in fixed_content and "import os" not in fixed_content:
            # Add import at the top
            lines = fixed_content.split("\n")
            import_lines = [
                line for line in lines if line.strip().startswith("import ")
            ]
            if not any("import os" in line for line in import_lines):
                lines.insert(0, "import os")
                fixed_content = "\n".join(lines)
                changes_made.append("Added missing os import")

        if fixed_content != content:
            fixed_artifact = Artifact(
                id=request.artifact.id,
                type=request.artifact.type,
                metadata={
                    **request.artifact.metadata,
                    "content": fixed_content,
                    "repaired": True,
                    "repair_type": "security_vulnerability",
                },
            )

            return RepairResult(
                success=True,
                fixed_artifact=fixed_artifact,
                original_artifact=request.artifact,
                repair_type="security_vulnerability",
                changes_made=changes_made,
                confidence=0.9 if changes_made else 0.3,
            )
        else:
            return RepairResult(
                success=False,
                original_artifact=request.artifact,
                repair_type="security_vulnerability",
                confidence=0.3,
                error_message="No security vulnerabilities found to repair",
            )

    async def _repair_performance_issue(self, request: RepairRequest) -> RepairResult:
        """Repair performance issues."""
        content = request.artifact.metadata.get("content", "")
        changes_made = []

        fixed_content = content

        # Simple performance optimizations
        # Replace list comprehensions with generator expressions where appropriate
        fixed_content = re.sub(
            r"\[([^]]+)\s+for\s+([^]]+)\s+in\s+([^]]+)\s+if\s+([^]]+)\]",
            r"(\1 for \2 in \3 if \4)",
            fixed_content,
        )

        # Add caching decorators for expensive functions
        expensive_patterns = [
            r"def\s+(\w+)\s*\([^)]*\):\s*\n\s*#\s*expensive",
            r"def\s+(\w+)\s*\([^)]*\):\s*\n\s*#\s*slow",
        ]

        for pattern in expensive_patterns:
            matches = re.findall(pattern, fixed_content)
            for func_name in matches:
                # Add @lru_cache decorator
                fixed_content = re.sub(
                    rf"def\s+{func_name}\s*\(",
                    f"@lru_cache(maxsize=128)\ndef {func_name}(",
                    fixed_content,
                )
                changes_made.append(f"Added caching to function {func_name}")

        if fixed_content != content:
            fixed_artifact = Artifact(
                id=request.artifact.id,
                type=request.artifact.type,
                metadata={
                    **request.artifact.metadata,
                    "content": fixed_content,
                    "repaired": True,
                    "repair_type": "performance_issue",
                },
            )

            return RepairResult(
                success=True,
                fixed_artifact=fixed_artifact,
                original_artifact=request.artifact,
                repair_type="performance_issue",
                changes_made=changes_made,
                confidence=0.7 if changes_made else 0.4,
            )
        else:
            return RepairResult(
                success=False,
                original_artifact=request.artifact,
                repair_type="performance_issue",
                confidence=0.4,
                error_message="No performance issues found to repair",
            )

    async def _repair_code_style(self, request: RepairRequest) -> RepairResult:
        """Repair code style issues."""
        content = request.artifact.metadata.get("content", "")
        changes_made = []

        fixed_content = content

        # Fix common style issues
        # Remove trailing whitespace
        fixed_content = re.sub(r"[ \t]+$", "", fixed_content, flags=re.MULTILINE)

        # Fix line length (simple approach)
        lines = fixed_content.split("\n")
        fixed_lines = []
        for line in lines:
            if len(line) > 88:  # Black's default line length
                # Simple line breaking (this is a basic implementation)
                if "=" in line and len(line) > 88:
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        var_name = parts[0].strip()
                        value = parts[1].strip()
                        if len(var_name) + len(value) + 3 > 88:
                            # Break the line
                            line = f"{var_name} = \\\n    {value}"
                            changes_made.append("Broke long line")
            fixed_lines.append(line)

        fixed_content = "\n".join(fixed_lines)

        if fixed_content != content:
            fixed_artifact = Artifact(
                id=request.artifact.id,
                type=request.artifact.type,
                metadata={
                    **request.artifact.metadata,
                    "content": fixed_content,
                    "repaired": True,
                    "repair_type": "code_style",
                },
            )

            return RepairResult(
                success=True,
                fixed_artifact=fixed_artifact,
                original_artifact=request.artifact,
                repair_type="code_style",
                changes_made=changes_made,
                confidence=0.8 if changes_made else 0.6,
            )
        else:
            return RepairResult(
                success=False,
                original_artifact=request.artifact,
                repair_type="code_style",
                confidence=0.6,
                error_message="No code style issues found to repair",
            )

    async def _repair_missing_import(self, request: RepairRequest) -> RepairResult:
        """Repair missing imports."""
        content = request.artifact.metadata.get("content", "")
        changes_made = []

        fixed_content = content

        # Detect common missing imports
        missing_imports = []

        if "json." in content and "import json" not in content:
            missing_imports.append("import json")

        if "datetime." in content and "import datetime" not in content:
            missing_imports.append("import datetime")

        if "re." in content and "import re" not in content:
            missing_imports.append("import re")

        if "os." in content and "import os" not in content:
            missing_imports.append("import os")

        if "sys." in content and "import sys" not in content:
            missing_imports.append("import sys")

        if missing_imports:
            # Add imports at the top
            lines = fixed_content.split("\n")
            import_section = []
            other_lines = []

            for line in lines:
                if line.strip().startswith("import ") or line.strip().startswith(
                    "from "
                ):
                    import_section.append(line)
                else:
                    other_lines.append(line)

            # Add missing imports
            for imp in missing_imports:
                if imp not in import_section:
                    import_section.append(imp)
                    changes_made.append(f"Added missing import: {imp}")

            # Reconstruct content
            fixed_content = "\n".join(import_section + [""] + other_lines)

        if fixed_content != content:
            fixed_artifact = Artifact(
                id=request.artifact.id,
                type=request.artifact.type,
                metadata={
                    **request.artifact.metadata,
                    "content": fixed_content,
                    "repaired": True,
                    "repair_type": "missing_import",
                },
            )

            return RepairResult(
                success=True,
                fixed_artifact=fixed_artifact,
                original_artifact=request.artifact,
                repair_type="missing_import",
                changes_made=changes_made,
                confidence=0.9 if changes_made else 0.5,
            )
        else:
            return RepairResult(
                success=False,
                original_artifact=request.artifact,
                repair_type="missing_import",
                confidence=0.5,
                error_message="No missing imports found to repair",
            )

    async def _repair_type_error(self, request: RepairRequest) -> RepairResult:
        """Repair type errors."""
        content = request.artifact.metadata.get("content", "")
        changes_made = []

        fixed_content = content

        # Simple type error repairs
        # Add type hints where missing
        function_pattern = r"def\s+(\w+)\s*\(([^)]*)\):"
        matches = re.finditer(function_pattern, fixed_content)

        for match in matches:
            func_name = match.group(1)
            params = match.group(2)

            # Add return type hints for common patterns
            if func_name.startswith("get_") or func_name.startswith("is_"):
                # Add -> bool or -> str based on function name
                if func_name.startswith("is_"):
                    return_type = " -> bool"
                elif func_name.startswith("get_"):
                    return_type = " -> str"
                else:
                    return_type = " -> Any"

                # Add return type hint
                func_def = match.group(0)
                if " -> " not in func_def:
                    new_func_def = func_def.replace("):", f"){return_type}:")
                    fixed_content = fixed_content.replace(func_def, new_func_def)
                    changes_made.append(f"Added return type hint to {func_name}")

        if fixed_content != content:
            fixed_artifact = Artifact(
                id=request.artifact.id,
                type=request.artifact.type,
                metadata={
                    **request.artifact.metadata,
                    "content": fixed_content,
                    "repaired": True,
                    "repair_type": "type_error",
                },
            )

            return RepairResult(
                success=True,
                fixed_artifact=fixed_artifact,
                original_artifact=request.artifact,
                repair_type="type_error",
                changes_made=changes_made,
                confidence=0.7 if changes_made else 0.4,
            )
        else:
            return RepairResult(
                success=False,
                original_artifact=request.artifact,
                repair_type="type_error",
                confidence=0.4,
                error_message="No type errors found to repair",
            )

    async def _repair_generic(self, request: RepairRequest) -> RepairResult:
        """Generic repair for unknown issue types."""
        # For unknown issue types, try to apply basic fixes
        content = request.artifact.metadata.get("content", "")

        # Apply basic formatting
        fixed_content = content.strip()

        if fixed_content != content:
            fixed_artifact = Artifact(
                id=request.artifact.id,
                type=request.artifact.type,
                metadata={
                    **request.artifact.metadata,
                    "content": fixed_content,
                    "repaired": True,
                    "repair_type": "generic",
                },
            )

            return RepairResult(
                success=True,
                fixed_artifact=fixed_artifact,
                original_artifact=request.artifact,
                repair_type="generic",
                changes_made=["Applied basic formatting"],
                confidence=0.5,
            )
        else:
            return RepairResult(
                success=False,
                original_artifact=request.artifact,
                repair_type=request.issue_type,
                confidence=0.3,
                error_message=f"Unknown repair type: {request.issue_type}",
            )
