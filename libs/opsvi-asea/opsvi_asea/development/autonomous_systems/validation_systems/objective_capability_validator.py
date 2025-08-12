#!/usr/bin/env python3
"""
Objective Capability Validator

Removes subjective assessment from validation chain through:
1. Purely quantitative evidence measurement
2. External validation requirements  
3. Falsifiable capability claims
4. Independent verification protocols

No interpretation, no extrapolation, no subjective scoring.
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional


class ObjectiveCapabilityValidator:
    """Objective validation system that eliminates subjective interpretation"""

    def __init__(self):
        self.validation_standards = self._load_objective_standards()

    def _load_objective_standards(self) -> Dict[str, Any]:
        """Load purely objective validation standards"""

        return {
            "tool_execution_validation": {
                "requirement": "Claimed tool usage must have corresponding log entries",
                "measurement": "count_matching_log_entries",
                "threshold": "1:1 correspondence required",
                "failure_condition": "any_claim_without_log_entry",
            },
            "temporal_consistency": {
                "requirement": "Tool execution timestamps must be within claimed timeframe",
                "measurement": "timestamp_analysis",
                "threshold": "execution_within_session_window",
                "failure_condition": "execution_outside_timeframe",
            },
            "output_verification": {
                "requirement": "Claimed results must match actual tool outputs",
                "measurement": "direct_output_comparison",
                "threshold": "exact_match_or_derivable",
                "failure_condition": "claimed_results_not_in_outputs",
            },
            "capability_scope_validation": {
                "requirement": "Claims cannot exceed demonstrated tool capabilities",
                "measurement": "capability_boundary_analysis",
                "threshold": "claims_within_tool_scope",
                "failure_condition": "claims_exceed_tool_capabilities",
            },
        }

    def validate_capability_claim(
        self,
        capability_name: str,
        claimed_evidence: Dict[str, Any],
        actual_logs: Dict[str, Any],
        validation_window_minutes: int = 30,
    ) -> Dict[str, Any]:
        """Validate a specific capability claim objectively"""

        validation_result = {
            "capability_name": capability_name,
            "timestamp": datetime.now().isoformat(),
            "validation_window_minutes": validation_window_minutes,
            "objective_measurements": {},
            "pass_fail_results": {},
            "overall_validation": "FAIL",  # Default to fail
            "failure_reasons": [],
            "quantitative_evidence": {},
        }

        # Apply each objective standard
        for standard_name, standard_config in self.validation_standards.items():
            measurement_result = self._apply_objective_measurement(
                standard_name, standard_config, claimed_evidence, actual_logs
            )

            validation_result["objective_measurements"][
                standard_name
            ] = measurement_result
            validation_result["pass_fail_results"][standard_name] = measurement_result[
                "passes_threshold"
            ]

            if not measurement_result["passes_threshold"]:
                validation_result["failure_reasons"].append(
                    measurement_result["failure_reason"]
                )

        # Overall validation passes only if ALL standards pass
        all_pass = all(validation_result["pass_fail_results"].values())
        validation_result["overall_validation"] = "PASS" if all_pass else "FAIL"

        # Quantitative evidence summary
        validation_result[
            "quantitative_evidence"
        ] = self._extract_quantitative_evidence(actual_logs)

        return validation_result

    def _apply_objective_measurement(
        self,
        standard_name: str,
        standard_config: Dict[str, Any],
        claimed_evidence: Dict[str, Any],
        actual_logs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Apply a single objective measurement standard"""

        measurement_result = {
            "standard_name": standard_name,
            "measurement_type": standard_config["measurement"],
            "passes_threshold": False,
            "measurement_value": None,
            "threshold_value": standard_config["threshold"],
            "failure_reason": "",
        }

        if standard_name == "tool_execution_validation":
            measurement_result = self._measure_tool_execution_correspondence(
                claimed_evidence, actual_logs
            )

        elif standard_name == "temporal_consistency":
            measurement_result = self._measure_temporal_consistency(
                claimed_evidence, actual_logs
            )

        elif standard_name == "output_verification":
            measurement_result = self._measure_output_verification(
                claimed_evidence, actual_logs
            )

        elif standard_name == "capability_scope_validation":
            measurement_result = self._measure_capability_scope(
                claimed_evidence, actual_logs
            )

        return measurement_result

    def _measure_tool_execution_correspondence(
        self, claimed_evidence: Dict[str, Any], actual_logs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Measure 1:1 correspondence between claimed tool usage and actual executions"""

        result = {
            "standard_name": "tool_execution_validation",
            "measurement_type": "count_matching_log_entries",
            "passes_threshold": False,
            "measurement_value": {},
            "threshold_value": "1:1 correspondence required",
            "failure_reason": "",
        }

        # Extract claimed tools
        claimed_tools = set()
        if "claimed_tool_usage" in claimed_evidence:
            for tool in claimed_evidence["claimed_tool_usage"]:
                # Normalize tool names
                normalized_tool = tool.lower().replace("-", "_").replace(" ", "_")
                claimed_tools.add(normalized_tool)

        # Extract actual tool executions
        actual_tools = set()
        total_executions = 0
        if "actual_tool_executions" in actual_logs:
            for tool_name, executions in actual_logs["actual_tool_executions"].items():
                if executions:  # Only count tools that were actually executed
                    actual_tools.add(tool_name)
                    total_executions += len(executions)

        # Measure correspondence
        claimed_tools_with_evidence = set()
        for claimed_tool in claimed_tools:
            for actual_tool in actual_tools:
                if claimed_tool in actual_tool or actual_tool in claimed_tool:
                    claimed_tools_with_evidence.add(claimed_tool)
                    break

        correspondence_ratio = (
            len(claimed_tools_with_evidence) / len(claimed_tools)
            if claimed_tools
            else 0
        )

        result["measurement_value"] = {
            "claimed_tools": list(claimed_tools),
            "actual_tools": list(actual_tools),
            "claimed_tools_with_evidence": list(claimed_tools_with_evidence),
            "correspondence_ratio": correspondence_ratio,
            "total_actual_executions": total_executions,
        }

        # Pass threshold: ALL claimed tools must have evidence
        result["passes_threshold"] = (
            correspondence_ratio == 1.0 and len(claimed_tools) > 0
        )

        if not result["passes_threshold"]:
            unsupported_tools = claimed_tools - claimed_tools_with_evidence
            if unsupported_tools:
                result[
                    "failure_reason"
                ] = f"Claimed tools without evidence: {list(unsupported_tools)}"
            elif len(claimed_tools) == 0:
                result["failure_reason"] = "No tool usage claims to validate"

        return result

    def _measure_temporal_consistency(
        self, claimed_evidence: Dict[str, Any], actual_logs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Measure temporal consistency of tool executions"""

        result = {
            "standard_name": "temporal_consistency",
            "measurement_type": "timestamp_analysis",
            "passes_threshold": False,
            "measurement_value": {},
            "threshold_value": "execution_within_session_window",
            "failure_reason": "",
        }

        # Extract execution timestamps
        execution_timestamps = []
        if "actual_tool_executions" in actual_logs:
            for tool_name, executions in actual_logs["actual_tool_executions"].items():
                for execution in executions:
                    if "timestamp" in execution:
                        execution_timestamps.append(execution["timestamp"])

        if execution_timestamps:
            # Convert to datetime objects for analysis
            try:
                timestamps = [datetime.fromisoformat(ts) for ts in execution_timestamps]
                timestamps.sort()

                # Measure time span
                time_span_minutes = (
                    timestamps[-1] - timestamps[0]
                ).total_seconds() / 60

                result["measurement_value"] = {
                    "execution_count": len(timestamps),
                    "first_execution": timestamps[0].isoformat(),
                    "last_execution": timestamps[-1].isoformat(),
                    "time_span_minutes": time_span_minutes,
                }

                # Pass threshold: reasonable time span for claimed complexity
                result["passes_threshold"] = (
                    0.1 <= time_span_minutes <= 60
                )  # Between 6 seconds and 1 hour

                if not result["passes_threshold"]:
                    if time_span_minutes < 0.1:
                        result[
                            "failure_reason"
                        ] = f"Executions too rapid ({time_span_minutes:.3f} minutes) for claimed complexity"
                    else:
                        result[
                            "failure_reason"
                        ] = f"Execution span too long ({time_span_minutes:.1f} minutes)"

            except Exception as e:
                result["failure_reason"] = f"Timestamp parsing error: {str(e)}"
        else:
            result["failure_reason"] = "No execution timestamps found"

        return result

    def _measure_output_verification(
        self, claimed_evidence: Dict[str, Any], actual_logs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Measure whether claimed results match actual tool outputs"""

        result = {
            "standard_name": "output_verification",
            "measurement_type": "direct_output_comparison",
            "passes_threshold": False,
            "measurement_value": {},
            "threshold_value": "exact_match_or_derivable",
            "failure_reason": "",
        }

        # Extract claimed results
        claimed_results = claimed_evidence.get("claimed_results", [])
        claimed_metrics = claimed_evidence.get("claimed_metrics", [])

        # Extract actual outputs
        actual_outputs = []
        if "actual_tool_executions" in actual_logs:
            for tool_name, executions in actual_logs["actual_tool_executions"].items():
                for execution in executions:
                    if "data" in execution and "output" in execution["data"]:
                        actual_outputs.append(
                            {"tool": tool_name, "output": execution["data"]["output"]}
                        )

        # Measure verification
        verified_claims = 0
        total_claims = len(claimed_results) + len(claimed_metrics)

        verification_details = {
            "claimed_results": claimed_results,
            "claimed_metrics": claimed_metrics,
            "actual_outputs": actual_outputs,
            "verified_claims": verified_claims,
            "total_claims": total_claims,
        }

        # For this validation, we require specific result claims to verify
        # If no specific results/metrics claimed, we pass (nothing to verify)
        if total_claims == 0:
            result["passes_threshold"] = True
            verification_details[
                "verification_note"
            ] = "No specific results/metrics claimed - nothing to verify"
        else:
            # TODO: Implement specific result verification logic
            result["passes_threshold"] = False
            result["failure_reason"] = "Result verification not yet implemented"

        result["measurement_value"] = verification_details

        return result

    def _measure_capability_scope(
        self, claimed_evidence: Dict[str, Any], actual_logs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Measure whether claims exceed demonstrated tool capabilities"""

        result = {
            "standard_name": "capability_scope_validation",
            "measurement_type": "capability_boundary_analysis",
            "passes_threshold": False,
            "measurement_value": {},
            "threshold_value": "claims_within_tool_scope",
            "failure_reason": "",
        }

        # Define known tool capabilities
        known_capabilities = {
            "cognitive_analysis": [
                "reasoning pattern analysis",
                "efficiency calculation",
                "decision point extraction",
                "cognitive load assessment",
            ],
            "decision_system": [
                "decision quality assessment",
                "autonomous scoring",
                "framework application",
                "evidence evaluation",
            ],
            "meta_cognitive": [
                "integrated analysis",
                "compound effect detection",
                "meta-cognitive optimization",
            ],
        }

        # Extract capability claims
        claimed_actions = claimed_evidence.get("claimed_actions", [])

        # Check if claims exceed known capabilities
        scope_violations = []
        for claim in claimed_actions:
            claim_lower = claim.lower()

            # Check for overstated capabilities
            overstated_indicators = [
                "breakthrough",
                "revolutionary",
                "unprecedented",
                "unlimited",
                "infinite",
                "perfect",
                "complete mastery",
            ]

            for indicator in overstated_indicators:
                if indicator in claim_lower:
                    scope_violations.append(
                        {
                            "claim": claim,
                            "violation_type": "overstated_capability",
                            "indicator": indicator,
                        }
                    )

        result["measurement_value"] = {
            "known_capabilities": known_capabilities,
            "claimed_actions": claimed_actions,
            "scope_violations": scope_violations,
        }

        # Pass if no scope violations
        result["passes_threshold"] = len(scope_violations) == 0

        if scope_violations:
            result[
                "failure_reason"
            ] = f"Capability scope violations: {[v['violation_type'] for v in scope_violations]}"

        return result

    def _extract_quantitative_evidence(
        self, actual_logs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract purely quantitative evidence from logs"""

        quantitative_evidence = {
            "total_tool_executions": 0,
            "tools_executed": [],
            "execution_timestamps": [],
            "numeric_outputs": {},
            "structured_data_count": 0,
        }

        if "actual_tool_executions" in actual_logs:
            for tool_name, executions in actual_logs["actual_tool_executions"].items():
                if executions:
                    quantitative_evidence["tools_executed"].append(tool_name)
                    quantitative_evidence["total_tool_executions"] += len(executions)

                    for execution in executions:
                        if "timestamp" in execution:
                            quantitative_evidence["execution_timestamps"].append(
                                execution["timestamp"]
                            )

                        if "data" in execution and "output" in execution["data"]:
                            output = execution["data"]["output"]
                            if isinstance(output, dict):
                                quantitative_evidence["structured_data_count"] += 1

                                # Extract numeric values
                                numeric_values = self._extract_numeric_values(output)
                                if numeric_values:
                                    quantitative_evidence["numeric_outputs"][
                                        tool_name
                                    ] = numeric_values

        return quantitative_evidence

    def _extract_numeric_values(self, data: Any, path: str = "") -> Dict[str, float]:
        """Recursively extract numeric values from data structure"""

        numeric_values = {}

        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                if isinstance(value, (int, float)):
                    numeric_values[current_path] = float(value)
                elif isinstance(value, dict):
                    nested_values = self._extract_numeric_values(value, current_path)
                    numeric_values.update(nested_values)
        elif isinstance(data, (int, float)):
            numeric_values[path] = float(data)

        return numeric_values

    def generate_objective_report(self, validation_result: Dict[str, Any]) -> str:
        """Generate objective validation report with no interpretation"""

        report_lines = [
            f"OBJECTIVE CAPABILITY VALIDATION REPORT",
            f"Capability: {validation_result['capability_name']}",
            f"Timestamp: {validation_result['timestamp']}",
            f"Overall Result: {validation_result['overall_validation']}",
            f"",
            f"QUANTITATIVE EVIDENCE:",
            f"- Total tool executions: {validation_result['quantitative_evidence']['total_tool_executions']}",
            f"- Tools executed: {validation_result['quantitative_evidence']['tools_executed']}",
            f"- Structured data outputs: {validation_result['quantitative_evidence']['structured_data_count']}",
            f"",
            f"OBJECTIVE MEASUREMENTS:",
        ]

        for standard_name, measurement in validation_result[
            "objective_measurements"
        ].items():
            status = "PASS" if measurement["passes_threshold"] else "FAIL"
            report_lines.append(f"- {standard_name}: {status}")
            if not measurement["passes_threshold"]:
                report_lines.append(
                    f"  Failure reason: {measurement['failure_reason']}"
                )

        if validation_result["failure_reasons"]:
            report_lines.extend(
                [
                    f"",
                    f"FAILURE REASONS:",
                    *[f"- {reason}" for reason in validation_result["failure_reasons"]],
                ]
            )

        return "\\n".join(report_lines)


def main():
    """Test objective capability validation"""

    if len(sys.argv) < 2:
        print("Usage: python3 objective_capability_validator.py <capability_name>")
        print(
            "Example: python3 objective_capability_validator.py meta_cognitive_intelligence"
        )
        return

    capability_name = sys.argv[1]

    validator = ObjectiveCapabilityValidator()

    # Load fresh agent test data
    try:
        with open(
            "/home/opsvi/asea/development/autonomous_systems/validation_systems/fresh_agent_response.txt",
            "r",
        ) as f:
            agent_response = f.read()

        # Extract claimed evidence
        claimed_evidence = {
            "claimed_actions": [
                "I used parallel research on optimization + meta-cognition"
            ],
            "claimed_tool_usage": ["meta-cognitive", "framework", "assessment"],
            "claimed_results": [],
            "claimed_metrics": [],
        }

        # Load actual logs
        actual_logs = {
            "actual_tool_executions": {
                "cognitive_analysis": [],
                "decision_system": [],
                "meta_cognitive": [],
            }
        }

        # Load log files
        log_files = {
            "cognitive_analysis": "/home/opsvi/asea/development/autonomous_systems/logs/cognitive_analysis.log",
            "decision_system": "/home/opsvi/asea/development/autonomous_systems/logs/decision_system.log",
            "meta_cognitive": "/home/opsvi/asea/development/autonomous_systems/logs/meta_cognitive.log",
        }

        for tool_name, log_file in log_files.items():
            if os.path.exists(log_file):
                with open(log_file, "r") as f:
                    for line in f:
                        if line.strip():
                            log_entry = json.loads(line.strip())
                            actual_logs["actual_tool_executions"][tool_name].append(
                                log_entry
                            )

        # Validate capability
        validation_result = validator.validate_capability_claim(
            capability_name, claimed_evidence, actual_logs
        )

        # Generate report
        report = validator.generate_objective_report(validation_result)
        print(report)

        # Also output JSON for processing
        print("\\n" + "=" * 60)
        print("JSON OUTPUT:")
        print(json.dumps(validation_result, indent=2))

    except Exception as e:
        print(f"Validation error: {str(e)}")


if __name__ == "__main__":
    main()
