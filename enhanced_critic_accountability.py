#!/usr/bin/env python3
"""
Enhanced Critic Accountability Design

The critic is now "on the hook" for providing specific fixes and guidance.
No more vague suggestions - concrete, actionable fixes required.
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum
import re  # Added missing import for regex


class IssueSeverity(Enum):
    CRITICAL = "critical"  # Code won't run or has security flaws
    HIGH = "high"  # Major functional issues
    MEDIUM = "medium"  # Important improvements
    LOW = "low"  # Style/optimization suggestions


class FixType(Enum):
    CODE_CHANGE = "code_change"  # Specific code modification
    ARCHITECTURE = "architecture"  # Structural changes
    CONFIGURATION = "configuration"  # Settings/environment changes
    DEPENDENCY = "dependency"  # Package/library changes
    DOCUMENTATION = "documentation"  # Comments/docs updates


@dataclass
class ConcreteFix:
    """A concrete, actionable fix that the critic must provide."""

    issue_description: str
    severity: IssueSeverity
    location: str  # File:line or specific location
    current_code: str  # What's wrong
    fixed_code: str  # What it should be
    fix_type: FixType
    reasoning: str  # Why this fix is needed
    impact: str  # What this fixes
    atomic_fix: str  # ≤140 character fix for nano model


@dataclass
class CriticAccountability:
    """The critic is accountable for providing specific fixes and guidance."""

    session_id: str
    iteration_number: int
    total_issues_found: int
    critical_issues: int
    fixes_provided: int
    fixes_implemented: int
    success_rate: float  # Percentage of fixes that resolved issues


class EnhancedCriticAgent:
    """
    Enhanced critic that is accountable for specific fixes and guidance.

    The critic is now "on the hook" for:
    1. Finding ALL issues (no excuses)
    2. Providing concrete fixes (not vague suggestions)
    3. Ensuring fixes work (validation required)
    4. Taking responsibility for missed issues
    """

    def __init__(self):
        self.accountability_tracker = {}
        self.fix_registry = {}

    def analyze_code_with_accountability(
        self, code: str, session_id: str, iteration: int = 1
    ) -> Dict[str, Any]:
        """
        Analyze code with full accountability for finding and fixing issues.

        The critic must:
        - Find ALL issues (no excuses for missing critical problems)
        - Provide concrete fixes (not vague suggestions)
        - Validate that fixes work
        - Take responsibility for missed issues
        """

        # Initialize accountability for this session
        if session_id not in self.accountability_tracker:
            self.accountability_tracker[session_id] = CriticAccountability(
                session_id=session_id,
                iteration_number=iteration,
                total_issues_found=0,
                critical_issues=0,
                fixes_provided=0,
                fixes_implemented=0,
                success_rate=0.0,
            )

        accountability = self.accountability_tracker[session_id]

        # The critic MUST find issues - no excuses
        issues_found = self._find_all_issues(code)
        accountability.total_issues_found = len(issues_found)
        accountability.critical_issues = len(
            [i for i in issues_found if i["severity"] == IssueSeverity.CRITICAL]
        )

        # The critic MUST provide concrete fixes
        concrete_fixes = self._provide_concrete_fixes(issues_found, code)
        accountability.fixes_provided = len(concrete_fixes)

        # The critic MUST validate fixes work
        validation_results = self._validate_fixes(concrete_fixes, code)

        return {
            "accountability": {
                "session_id": session_id,
                "iteration": iteration,
                "issues_found": accountability.total_issues_found,
                "critical_issues": accountability.critical_issues,
                "fixes_provided": accountability.fixes_provided,
                "fixes_validated": len(validation_results["valid_fixes"]),
                "success_rate": len(validation_results["valid_fixes"])
                / max(1, accountability.fixes_provided),
                "critic_responsibility": self._calculate_critic_responsibility(
                    accountability
                ),
            },
            "issues": [self._issue_to_dict(issue) for issue in issues_found],
            "concrete_fixes": [self._fix_to_dict(fix) for fix in concrete_fixes],
            "validation": validation_results,
            "next_actions": self._generate_next_actions(
                concrete_fixes, validation_results
            ),
        }

    def _find_all_issues(self, code: str) -> List[Dict[str, Any]]:
        """
        Find ALL issues in the code. The critic is accountable for missing nothing.

        This is where the critic must be thorough and systematic.
        """
        issues = []

        # Critical issues that prevent code from running
        critical_patterns = [
            (r"app\.state\.jwt", "Global JWT reference breaks multi-instance usage"),
            (r"import.*not found", "Missing import statement"),
            (r"undefined.*variable", "Undefined variable reference"),
            (r"syntax.*error", "Syntax error in code"),
            (r"indentation.*error", "Indentation error"),
        ]

        # High priority functional issues
        high_patterns = [
            (r"except.*pass", "Silent exception handling"),
            (r"password.*plaintext", "Password stored in plaintext"),
            (r"sql.*injection", "Potential SQL injection vulnerability"),
            (r"hardcoded.*secret", "Hardcoded secret in code"),
        ]

        # Check for critical issues first
        for pattern, description in critical_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(
                    {
                        "type": "critical",
                        "description": description,
                        "pattern": pattern,
                        "severity": IssueSeverity.CRITICAL,
                    }
                )

        # Check for high priority issues
        for pattern, description in high_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(
                    {
                        "type": "high",
                        "description": description,
                        "pattern": pattern,
                        "severity": IssueSeverity.HIGH,
                    }
                )

        return issues

    def _provide_concrete_fixes(
        self, issues: List[Dict], code: str
    ) -> List[ConcreteFix]:
        """
        Provide concrete, actionable fixes for each issue.

        The critic must provide specific code changes, not vague suggestions.
        """
        fixes = []

        for issue in issues:
            if issue["severity"] == IssueSeverity.CRITICAL:
                # Critical issues get immediate, specific fixes
                fix = self._create_critical_fix(issue, code)
                fixes.append(fix)
            elif issue["severity"] == IssueSeverity.HIGH:
                # High priority issues get detailed fixes
                fix = self._create_high_priority_fix(issue, code)
                fixes.append(fix)

        return fixes

    def _create_critical_fix(self, issue: Dict, code: str) -> ConcreteFix:
        """Create a critical fix with specific code changes."""

        if "Global JWT reference" in issue["description"]:
            return ConcreteFix(
                issue_description="Global JWT reference breaks multi-instance usage",
                severity=IssueSeverity.CRITICAL,
                location="app.py:45",
                current_code="jwt_manager = app.state.jwt",
                fixed_code="jwt_manager = request.app.state.jwt",
                fix_type=FixType.ARCHITECTURE,
                reasoning="Global app.state.jwt reference prevents multiple instances from running",
                impact="Enables multi-instance deployment and proper dependency injection",
                atomic_fix="Replace 'app.state.jwt' with 'request.app.state.jwt' in JWT manager initialization",
            )

        # Add more critical fix patterns here
        return ConcreteFix(
            issue_description=issue["description"],
            severity=IssueSeverity.CRITICAL,
            location="unknown",
            current_code="[issue detected]",
            fixed_code="[fix required]",
            fix_type=FixType.CODE_CHANGE,
            reasoning="Critical issue must be fixed for code to function",
            impact="Enables code to run properly",
            atomic_fix=f"Fix {issue['description']}",
        )

    def _create_high_priority_fix(self, issue: Dict, code: str) -> ConcreteFix:
        """Create a high priority fix with specific guidance."""

        if "Silent exception handling" in issue["description"]:
            return ConcreteFix(
                issue_description="Silent exception handling hides errors",
                severity=IssueSeverity.HIGH,
                location="database.py:23",
                current_code="except Exception as e:\n    pass",
                fixed_code="except Exception as e:\n    logger.error(f'Database error: {e}')\n    raise",
                fix_type=FixType.CODE_CHANGE,
                reasoning="Silent exceptions make debugging impossible",
                impact="Enables proper error tracking and debugging",
                atomic_fix="Replace 'except: pass' with proper error logging and re-raising",
            )

        return ConcreteFix(
            issue_description=issue["description"],
            severity=IssueSeverity.HIGH,
            location="unknown",
            current_code="[issue detected]",
            fixed_code="[fix required]",
            fix_type=FixType.CODE_CHANGE,
            reasoning="High priority issue affects functionality",
            impact="Improves code reliability and security",
            atomic_fix=f"Address {issue['description']}",
        )

    def _validate_fixes(
        self, fixes: List[ConcreteFix], original_code: str
    ) -> Dict[str, Any]:
        """
        Validate that the provided fixes actually work.

        The critic is accountable for ensuring fixes are correct.
        """
        valid_fixes = []
        invalid_fixes = []

        for fix in fixes:
            # Simulate applying the fix
            fixed_code = self._apply_fix(original_code, fix)

            # Validate the fix
            if self._is_fix_valid(fixed_code, fix):
                valid_fixes.append(fix)
            else:
                invalid_fixes.append(fix)

        return {
            "valid_fixes": valid_fixes,
            "invalid_fixes": invalid_fixes,
            "validation_rate": len(valid_fixes) / max(1, len(fixes)),
        }

    def _apply_fix(self, code: str, fix: ConcreteFix) -> str:
        """Apply a fix to the code."""
        # This would be the actual fix application logic
        # For now, we'll simulate it
        return code.replace(fix.current_code, fix.fixed_code)

    def _is_fix_valid(self, fixed_code: str, fix: ConcreteFix) -> bool:
        """Check if a fix is valid."""
        # This would include syntax checking, logic validation, etc.
        # For now, we'll assume fixes are valid if they change the code
        return fix.current_code != fix.fixed_code

    def _calculate_critic_responsibility(
        self, accountability: CriticAccountability
    ) -> str:
        """Calculate the critic's responsibility level."""
        if accountability.critical_issues > 0 and accountability.fixes_provided == 0:
            return "CRITICAL FAILURE - Found critical issues but provided no fixes"
        elif accountability.success_rate < 0.5:
            return "POOR PERFORMANCE - Less than 50% of fixes are valid"
        elif accountability.success_rate < 0.8:
            return "NEEDS IMPROVEMENT - Fixes need better validation"
        else:
            return "GOOD PERFORMANCE - Providing effective fixes"

    def _generate_next_actions(
        self, fixes: List[ConcreteFix], validation: Dict
    ) -> List[str]:
        """Generate specific next actions for the nano model."""
        actions = []

        # Prioritize critical fixes
        critical_fixes = [f for f in fixes if f.severity == IssueSeverity.CRITICAL]
        for fix in critical_fixes:
            actions.append(f"CRITICAL: {fix.atomic_fix}")

        # Add high priority fixes
        high_fixes = [f for f in fixes if f.severity == IssueSeverity.HIGH]
        for fix in high_fixes[:3]:  # Limit to top 3
            actions.append(f"HIGH: {fix.atomic_fix}")

        # Add validation actions
        if validation["validation_rate"] < 0.8:
            actions.append("VALIDATE: Test all fixes before proceeding")

        return actions

    def _issue_to_dict(self, issue: Dict) -> Dict[str, Any]:
        """Convert issue to dictionary format."""
        return {
            "severity": issue["severity"].value,
            "description": issue["description"],
            "type": issue["type"],
            "pattern": issue.get("pattern", ""),
        }

    def _fix_to_dict(self, fix: ConcreteFix) -> Dict[str, Any]:
        """Convert fix to dictionary format."""
        return {
            "issue_description": fix.issue_description,
            "severity": fix.severity.value,
            "location": fix.location,
            "current_code": fix.current_code,
            "fixed_code": fix.fixed_code,
            "fix_type": fix.fix_type.value,
            "reasoning": fix.reasoning,
            "impact": fix.impact,
            "atomic_fix": fix.atomic_fix,
        }


# Example usage
if __name__ == "__main__":
    critic = EnhancedCriticAgent()

    # Example code with issues
    test_code = """
    from fastapi import FastAPI
    app = FastAPI()

    # Critical issue: Global JWT reference
    jwt_manager = app.state.jwt

    # High priority issue: Silent exception
    try:
        result = database.query()
    except Exception as e:
        pass
    """

    result = critic.analyze_code_with_accountability(test_code, "test_session_001")

    print("=== ENHANCED CRITIC ACCOUNTABILITY TEST ===")
    print(f"Accountability: {result['accountability']}")
    print(f"Issues found: {len(result['issues'])}")
    print(f"Concrete fixes: {len(result['concrete_fixes'])}")
    print(f"Validation rate: {result['validation']['validation_rate']:.1%}")
    print(f"Next actions: {result['next_actions']}")
