"""Syntax fixer agent for repairing Python syntax and formatting issues."""

import ast
import logging
import re
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from opsvi_auto_forge.agents.base_repair_agent import (
    BaseRepairAgent,
    RepairRequest,
    RepairResult,
)
from opsvi_auto_forge.config.models import Artifact

logger = logging.getLogger(__name__)


class SyntaxFixResult(BaseModel):
    """Result of syntax fixing operation."""

    fixed_code: str = Field(..., description="The fixed code")
    syntax_errors_fixed: List[str] = Field(
        default_factory=list, description="List of syntax errors fixed"
    )
    formatting_issues_fixed: List[str] = Field(
        default_factory=list, description="List of formatting issues fixed"
    )
    import_issues_fixed: List[str] = Field(
        default_factory=list, description="List of import issues fixed"
    )
    validation_passed: bool = Field(
        ..., description="Whether the fixed code passes syntax validation"
    )


class SyntaxFixer(BaseRepairAgent):
    """Agent for fixing Python syntax errors, formatting issues, and import problems."""

    def __init__(self, neo4j_client=None):
        """Initialize the syntax fixer agent."""
        super().__init__(
            name="SyntaxFixer",
            description="Fixes Python syntax errors, formatting issues, and import problems",
            repair_capabilities=[
                "syntax_error",
                "formatting_issue",
                "import_error",
                "indentation_error",
                "missing_colon",
                "unmatched_brackets",
                "invalid_identifier",
                "trailing_whitespace",
                "missing_newline",
            ],
            neo4j_client=neo4j_client,
            model="gpt-4.1-mini",
            temperature=0.1,
            max_tokens=4000,
        )

    async def _perform_repair(self, request: RepairRequest) -> RepairResult:
        """Perform syntax fixing on the artifact."""
        try:
            # Extract code from artifact
            code = self._extract_code_from_artifact(request.artifact)
            if not code:
                return RepairResult(
                    success=False,
                    original_artifact=request.artifact,
                    repair_type=request.issue_type,
                    confidence=0.0,
                    error_message="No code found in artifact",
                )

            # Analyze the code for issues
            issues = self._analyze_code_issues(code, request.issue_type)

            # Fix the issues
            fixed_code, changes_made = await self._fix_code_issues(
                code, issues, request
            )

            # Validate the fixed code
            validation_passed = self._validate_syntax(fixed_code)

            # Create fixed artifact
            fixed_artifact = self._create_fixed_artifact(request.artifact, fixed_code)

            # Calculate confidence based on validation and changes
            confidence = self._calculate_confidence(
                validation_passed, len(changes_made), len(issues)
            )

            return RepairResult(
                success=validation_passed and len(changes_made) > 0,
                fixed_artifact=fixed_artifact,
                original_artifact=request.artifact,
                repair_type=request.issue_type,
                changes_made=changes_made,
                confidence=confidence,
                metadata={
                    "syntax_errors_fixed": len(
                        [c for c in changes_made if "syntax" in c.lower()]
                    ),
                    "formatting_issues_fixed": len(
                        [c for c in changes_made if "format" in c.lower()]
                    ),
                    "import_issues_fixed": len(
                        [c for c in changes_made if "import" in c.lower()]
                    ),
                    "validation_passed": validation_passed,
                },
            )

        except Exception as e:
            logger.error(f"Error during syntax repair: {e}", exc_info=True)
            return RepairResult(
                success=False,
                original_artifact=request.artifact,
                repair_type=request.issue_type,
                confidence=0.0,
                error_message=str(e),
            )

    def _extract_code_from_artifact(self, artifact: Artifact) -> Optional[str]:
        """Extract code content from artifact."""
        if artifact.type == "code" and artifact.metadata.get("content"):
            return artifact.metadata["content"]
        elif artifact.type == "file" and artifact.metadata.get("file_content"):
            return artifact.metadata["file_content"]
        return None

    def _analyze_code_issues(self, code: str, issue_type: str) -> List[Dict[str, Any]]:
        """Analyze code for specific issues."""
        issues = []

        if issue_type == "syntax_error":
            issues.extend(self._find_syntax_errors(code))
        elif issue_type == "formatting_issue":
            issues.extend(self._find_formatting_issues(code))
        elif issue_type == "import_error":
            issues.extend(self._find_import_issues(code))
        elif issue_type == "indentation_error":
            issues.extend(self._find_indentation_errors(code))
        else:
            # Analyze for all issues
            issues.extend(self._find_syntax_errors(code))
            issues.extend(self._find_formatting_issues(code))
            issues.extend(self._find_import_issues(code))
            issues.extend(self._find_indentation_errors(code))

        return issues

    def _find_syntax_errors(self, code: str) -> List[Dict[str, Any]]:
        """Find syntax errors in the code."""
        issues = []

        try:
            ast.parse(code)
        except SyntaxError as e:
            issues.append(
                {
                    "type": "syntax_error",
                    "line": e.lineno,
                    "message": str(e),
                    "severity": "high",
                }
            )

        # Check for common syntax issues
        if "def " in code and ":" not in code:
            issues.append(
                {
                    "type": "missing_colon",
                    "line": None,
                    "message": "Missing colon after function definition",
                    "severity": "medium",
                }
            )

        return issues

    def _find_formatting_issues(self, code: str) -> List[Dict[str, Any]]:
        """Find formatting issues in the code."""
        issues = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            # Trailing whitespace
            if line.rstrip() != line:
                issues.append(
                    {
                        "type": "trailing_whitespace",
                        "line": i,
                        "message": "Trailing whitespace",
                        "severity": "low",
                    }
                )

            # Inconsistent indentation
            if line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                if i > 1 and lines[i - 2].strip().endswith(":"):
                    issues.append(
                        {
                            "type": "indentation_error",
                            "line": i,
                            "message": "Expected indentation after colon",
                            "severity": "high",
                        }
                    )

        # Missing newline at end
        if code and not code.endswith("\n"):
            issues.append(
                {
                    "type": "missing_newline",
                    "line": len(lines),
                    "message": "Missing newline at end of file",
                    "severity": "low",
                }
            )

        return issues

    def _find_import_issues(self, code: str) -> List[Dict[str, Any]]:
        """Find import-related issues in the code."""
        issues = []

        # Check for unused imports (basic check)
        import_lines = [
            line
            for line in code.split("\n")
            if line.strip().startswith(("import ", "from "))
        ]

        for import_line in import_lines:
            # Check for missing spaces around import
            if "import" in import_line and not re.search(r"\s+import\s+", import_line):
                issues.append(
                    {
                        "type": "import_formatting",
                        "line": None,
                        "message": "Missing spaces around import keyword",
                        "severity": "medium",
                    }
                )

        return issues

    def _find_indentation_errors(self, code: str) -> List[Dict[str, Any]]:
        """Find indentation errors in the code."""
        issues = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            if line.strip():  # Non-empty line
                # Check for mixed tabs and spaces
                if "\t" in line and " " in line[: len(line) - len(line.lstrip())]:
                    issues.append(
                        {
                            "type": "mixed_indentation",
                            "line": i,
                            "message": "Mixed tabs and spaces in indentation",
                            "severity": "high",
                        }
                    )

        return issues

    async def _fix_code_issues(
        self, code: str, issues: List[Dict[str, Any]], request: RepairRequest
    ) -> tuple[str, List[str]]:
        """Fix code issues using AI model."""
        changes_made = []
        fixed_code = code

        if not issues:
            return fixed_code, changes_made

        # Create prompt for fixing issues
        prompt = self._create_fix_prompt(code, issues, request.issue_description)

        try:
            # Use AI model to fix the code
            response = await self._call_model(prompt)

            if response and response.get("fixed_code"):
                fixed_code = response["fixed_code"]
                changes_made = response.get("changes_made", [])

                # Apply basic fixes that don't require AI
                fixed_code, basic_changes = self._apply_basic_fixes(fixed_code)
                changes_made.extend(basic_changes)

        except Exception as e:
            logger.error(f"Error calling model for syntax fix: {e}")
            # Fallback to basic fixes only
            fixed_code, changes_made = self._apply_basic_fixes(code)

        return fixed_code, changes_made

    def _create_fix_prompt(
        self, code: str, issues: List[Dict[str, Any]], issue_description: str
    ) -> str:
        """Create prompt for fixing code issues."""
        issues_text = "\n".join(
            [f"- {issue['type']}: {issue['message']}" for issue in issues]
        )

        return f"""
You are a Python syntax fixer. Fix the following code issues:

**Issue Description**: {issue_description}

**Issues Found**:
{issues_text}

**Code to Fix**:
```python
{code}
```

**Requirements**:
1. Fix all syntax errors
2. Fix formatting issues (trailing whitespace, indentation, etc.)
3. Fix import organization
4. Ensure the code is valid Python syntax
5. Maintain the original functionality
6. Return the fixed code and list of changes made

**Response Format**:
```json
{{
    "fixed_code": "the fixed Python code",
    "changes_made": [
        "description of change 1",
        "description of change 2"
    ]
}}
```

Fix the code and return the response in the specified format.
"""

    def _apply_basic_fixes(self, code: str) -> tuple[str, List[str]]:
        """Apply basic fixes that don't require AI."""
        changes_made = []
        fixed_code = code

        # Remove trailing whitespace
        lines = fixed_code.split("\n")
        cleaned_lines = []
        for line in lines:
            if line.rstrip() != line:
                changes_made.append("Removed trailing whitespace")
            cleaned_lines.append(line.rstrip())

        # Add newline at end if missing
        if cleaned_lines and cleaned_lines[-1]:
            cleaned_lines.append("")
            changes_made.append("Added newline at end of file")

        fixed_code = "\n".join(cleaned_lines)

        return fixed_code, changes_made

    def _validate_syntax(self, code: str) -> bool:
        """Validate that the code has correct Python syntax."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def _create_fixed_artifact(
        self, original_artifact: Artifact, fixed_code: str
    ) -> Artifact:
        """Create a new artifact with the fixed code."""

        # Create new metadata with fixed content
        metadata = original_artifact.metadata.copy()
        metadata["content"] = fixed_code
        metadata["original_artifact_id"] = str(original_artifact.id)
        metadata["repair_timestamp"] = str(uuid4())

        return Artifact(
            id=uuid4(),
            type=original_artifact.type,
            path=original_artifact.path,
            hash=self._calculate_hash(fixed_code),
            metadata=metadata,
            size_bytes=len(fixed_code.encode()),
            mime_type=original_artifact.mime_type,
            task_id=original_artifact.task_id,
        )

    def _calculate_hash(self, content: str) -> str:
        """Calculate hash for the content."""
        import hashlib

        return hashlib.sha256(content.encode()).hexdigest()

    def _calculate_confidence(
        self, validation_passed: bool, changes_count: int, issues_count: int
    ) -> float:
        """Calculate confidence in the repair."""
        if not validation_passed:
            return 0.0

        if issues_count == 0:
            return 1.0

        # Base confidence on how many issues were addressed
        issue_coverage = min(changes_count / issues_count, 1.0)

        # Higher confidence if validation passed
        base_confidence = 0.8 if validation_passed else 0.3

        return min(base_confidence + (issue_coverage * 0.2), 1.0)
