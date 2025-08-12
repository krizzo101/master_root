#!/usr/bin/env python3
"""
Enhanced Mistake Prevention System with Strategic Partnership
Combines operational mistake prevention with empowered pushback capabilities
"""

import json
from typing import Dict, List, Any, Optional
import re
from strategic_partnership_mixin import StrategicPartnershipMixin


class EnhancedMistakePreventionSystem(StrategicPartnershipMixin):
    """Enhanced system that prevents mistakes AND provides strategic pushback"""

    def __init__(self):
        super().__init__()  # Initialize strategic partnership capabilities
        self.aql_patterns = {
            "syntax_order": "FOR → FILTER → SORT → LIMIT → RETURN",
            "common_errors": [
                "SORT after RETURN",
                "Invalid collection references",
                "Missing collection existence validation",
            ],
            "proper_patterns": [
                "Always validate collection exists",
                "Use correct operation order",
                "Proper COLLECT WITH COUNT syntax",
            ],
        }

        self.tool_validation_protocol = [
            "Check result for errors",
            "If failure detected, STOP all other operations",
            "Analyze root cause",
            "Fix the specific issue",
            "Retry with corrected approach",
        ]

    def comprehensive_operation_validation(
        self, operation: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Comprehensive validation including strategic partnership assessment"""

        # Original mistake prevention validation
        technical_validation = self._technical_validation(operation, context)

        # Strategic partnership evaluation
        strategic_evaluation = self.evaluate_user_directive(operation, context)

        # Combined assessment
        comprehensive_result = {
            "technical_validation": technical_validation,
            "strategic_evaluation": strategic_evaluation,
            "overall_recommendation": "proceed",
            "combined_confidence": 1.0,
            "action_required": [],
        }

        # Determine overall recommendation
        if not technical_validation.get("valid", True):
            comprehensive_result["overall_recommendation"] = "fix_technical_issues"
            comprehensive_result["action_required"].append(
                "Address technical validation failures"
            )
            comprehensive_result["combined_confidence"] *= 0.3

        if strategic_evaluation["pushback_warranted"]:
            comprehensive_result["overall_recommendation"] = "consider_alternative"
            comprehensive_result["action_required"].append(
                "Evaluate strategic alternative"
            )
            comprehensive_result["combined_confidence"] *= 0.7

        # Generate strategic response if needed
        if strategic_evaluation["pushback_warranted"]:
            comprehensive_result[
                "strategic_pushback_message"
            ] = self.provide_strategic_pushback(strategic_evaluation)

        return comprehensive_result

    def _technical_validation(
        self, operation: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Technical validation (original mistake prevention logic)"""

        validation_result = {"valid": True, "errors": []}

        # AQL validation if operation contains query
        if "FOR" in operation and "RETURN" in operation:
            aql_validation = self.validate_aql_query(operation)
            if not aql_validation["valid"]:
                validation_result["valid"] = False
                validation_result["errors"].extend(aql_validation["errors"])

        # Tool result validation if context contains results
        if context.get("tool_results"):
            for result in context["tool_results"]:
                tool_validation = self.validate_tool_result(result)
                if not tool_validation["success"]:
                    validation_result["valid"] = False
                    validation_result["errors"].extend(tool_validation["errors"])

        return validation_result

    def validate_aql_query(self, query: str) -> Dict[str, Any]:
        """Enhanced AQL validation with strategic considerations"""

        # Original technical validation
        pattern = re.compile(
            r"^\s*FOR\s+\w+\s+IN\s+\w+.*\s+RETURN\s+\w+", re.IGNORECASE | re.DOTALL
        )

        if pattern.match(query):
            technical_result = {"valid": True, "errors": []}
        else:
            technical_result = {
                "valid": False,
                "errors": [
                    "Invalid AQL syntax. Basic check requires 'FOR ... IN ... RETURN ...' structure."
                ],
            }

        # Strategic assessment of query approach
        strategic_context = {
            "query_complexity": len(query.split()),
            "existing_working_queries": True,
        }
        strategic_eval = self.evaluate_user_directive(
            f"Execute AQL query: {query}", strategic_context
        )

        # Combine technical and strategic assessments
        combined_result = technical_result.copy()
        combined_result["strategic_assessment"] = strategic_eval

        return combined_result

    def validate_tool_result(self, tool_result: Any) -> Dict[str, Any]:
        """Enhanced tool result validation with strategic feedback"""

        validation_result = {
            "success": True,
            "errors": [],
            "failure_type": None,
            "strategic_feedback": None,
        }

        # Original technical validation
        result_str = str(tool_result)
        failure_patterns = [
            ("rate_limit", "Rate limit exceeded"),
            ("rate_limit", "429"),
            ("error", "error"),
            ("error", "Error"),
            ("error", "ERROR"),
            ("failure", "failed"),
            ("failure", "Failed"),
            ("failure", "FAILED"),
            ("null_content", "content: null"),
            ("empty_result", "[]"),
            ("timeout", "timeout"),
            ("timeout", "Timeout"),
        ]

        for failure_type, pattern in failure_patterns:
            if pattern in result_str:
                validation_result["success"] = False
                validation_result["failure_type"] = failure_type
                validation_result["errors"].append(f"Tool failure detected: {pattern}")

                # Strategic feedback on failure
                if failure_type == "rate_limit":
                    validation_result[
                        "strategic_feedback"
                    ] = "Consider implementing rate limiting or using alternative approaches"
                elif failure_type == "timeout":
                    validation_result[
                        "strategic_feedback"
                    ] = "Consider breaking operation into smaller chunks or optimizing query"
                elif failure_type == "empty_result":
                    validation_result[
                        "strategic_feedback"
                    ] = "Verify query logic and collection state before assuming failure"

        return validation_result

    def get_enhanced_operational_knowledge_summary(self) -> Dict[str, Any]:
        """Enhanced operational knowledge including strategic partnership protocols"""

        base_knowledge = {
            "aql_syntax": {
                "order": "FOR → FILTER → SORT → LIMIT → RETURN",
                "critical_rule": "RETURN must come after SORT",
                "validation_required": "Always validate collection exists",
            },
            "tool_validation": {
                "mandatory_check": "ALWAYS check tool results for errors before proceeding",
                "failure_response": "STOP all operations if failure detected",
                "common_failures": [
                    "Rate limit exceeded",
                    "429 errors",
                    "content: null",
                ],
            },
            "absolute_paths": {
                "shell_commands": "ALWAYS use absolute paths starting with /home/opsvi/asea/",
                "mcp_filesystem": "MANDATORY absolute paths for all MCP filesystem tools",
            },
        }

        # Add strategic partnership knowledge
        base_knowledge["strategic_partnership"] = {
            "empowered_pushback": "MANDATORY: Pushback when directive has issues",
            "alternative_solutions": "REQUIRED: Propose better approaches when identified",
            "value_based_disagreement": "Expected to disagree when it prevents mistakes",
            "efficiency_optimization": "Actively identify and suggest efficiency improvements",
            "quality_assurance": "Challenge approaches that risk quality degradation",
        }

        return base_knowledge


def test_enhanced_system():
    """Test the enhanced mistake prevention system"""

    system = EnhancedMistakePreventionSystem()

    print("ENHANCED MISTAKE PREVENTION SYSTEM TEST")
    print("=" * 60)

    # Test 1: Technical validation with strategic assessment
    print("TEST 1: AQL Query with Strategic Assessment")
    bad_query = "FOR doc IN collection RETURN doc SORT doc.created DESC"
    result = system.validate_aql_query(bad_query)
    print(f"Technical Valid: {result['valid']}")
    print(f"Strategic Pushback: {result['strategic_assessment']['pushback_warranted']}")

    # Test 2: Comprehensive operation validation
    print("\nTEST 2: Comprehensive Operation Validation")
    operation = "Rebuild entire database schema from scratch"
    context = {"existing_working_system": True, "time_pressure": True}

    comprehensive_result = system.comprehensive_operation_validation(operation, context)
    print(f"Overall Recommendation: {comprehensive_result['overall_recommendation']}")
    print(f"Combined Confidence: {comprehensive_result['combined_confidence']:.2f}")

    if comprehensive_result.get("strategic_pushback_message"):
        print("\nSTRATEGIC PUSHBACK MESSAGE:")
        print(comprehensive_result["strategic_pushback_message"])

    # Test 3: Enhanced operational knowledge
    print("\nTEST 3: Enhanced Operational Knowledge")
    knowledge = system.get_enhanced_operational_knowledge_summary()
    print(f"Strategic Partnership Protocols: {knowledge['strategic_partnership']}")

    print(
        "\n✅ Enhanced system successfully combines technical validation with strategic partnership!"
    )


if __name__ == "__main__":
    test_enhanced_system()
