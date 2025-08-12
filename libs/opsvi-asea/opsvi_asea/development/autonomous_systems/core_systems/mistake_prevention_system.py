#!/usr/bin/env python3
"""
Mistake Prevention & Knowledge Application System
Ensures stored operational knowledge is applied to prevent repeated mistakes
"""

import json
from typing import Dict, List, Any, Optional
import re
import functools


def require_params(*required_params):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            missing = [
                p
                for p in required_params
                if p not in kwargs or kwargs[p] in [None, "", {}]
            ]
            if missing:
                raise ValueError(
                    f"Missing required parameter(s): {', '.join(missing)} for tool {func.__name__}"
                )
            return func(*args, **kwargs)

        wrapper._required_params = required_params
        return wrapper

    return decorator


class MistakePreventionSystem:
    """System to prevent repeated operational mistakes by applying stored knowledge"""

    def validate_tool_call_params(self, tool_func, **params):
        required = getattr(tool_func, "_required_params", [])
        missing = [
            p for p in required if p not in params or params[p] in [None, "", {}]
        ]
        if missing:
            raise ValueError(
                f"Tool call blocked: missing required parameter(s): {', '.join(missing)} for {tool_func.__name__}"
            )
        return tool_func(**params)

    def __init__(self):
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

    def validate_aql_query(self, query: str) -> Dict[str, Any]:
        """Basic AQL syntax validation"""
        # A simple regex to check for the basic structure of a read query
        # This is a basic check and not a full parser
        pattern = re.compile(
            r"^\s*FOR\s+\w+\s+IN\s+\w+.*\s+RETURN\s+\w+", re.IGNORECASE | re.DOTALL
        )

        if pattern.match(query):
            return {"valid": True, "errors": []}
        else:
            return {
                "valid": False,
                "errors": [
                    "Invalid AQL syntax. Basic check requires 'FOR ... IN ... RETURN ...' structure."
                ],
            }

    def validate_tool_result(self, tool_result: Any) -> Dict[str, Any]:
        """Validate tool result for common failure patterns"""

        validation_result = {"success": True, "errors": [], "failure_type": None}

        # Convert result to string for analysis
        result_str = str(tool_result)

        # Check for common failure patterns
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

        return validation_result

    def get_operational_knowledge_summary(self) -> Dict[str, Any]:
        """Get summary of key operational knowledge to apply"""

        return {
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


if __name__ == "__main__":
    # Test the system
    system = MistakePreventionSystem()

    # Test AQL validation with INCORRECT query (RETURN before SORT)
    bad_query = "FOR doc IN collection RETURN doc SORT doc.created DESC"
    result = system.validate_aql_query(bad_query)
    print("AQL Validation Test (Bad Query):")
    print(json.dumps(result, indent=2))

    # Test AQL validation with CORRECT query (SORT before RETURN)
    good_query = "FOR doc IN collection SORT doc.created DESC RETURN doc"
    result = system.validate_aql_query(good_query)
    print("\nAQL Validation Test (Good Query):")
    print(json.dumps(result, indent=2))

    # Test tool result validation
    failed_result = {"error": "Rate limit exceeded", "content": None}
    result = system.validate_tool_result(failed_result)
    print("\nTool Result Validation Test:")
    print(json.dumps(result, indent=2))

    # Show operational knowledge
    print("\nOperational Knowledge Summary:")
    print(json.dumps(system.get_operational_knowledge_summary(), indent=2))
