#!/usr/bin/env python3
"""
Meta-Cognitive Validation Logger - Tool Result Logging System

This system logs all autonomous system tool calls and results for validation analysis.
Critical for understanding what guidance agents actually receive vs. what they claim.

Usage:
    python3 meta_cognitive_validation_logger.py analyze_session "session_log.json"
    python3 meta_cognitive_validation_logger.py validate_claims "agent_response.txt" "tool_log.json"
"""

import json
import sys
from datetime import datetime
from typing import Dict, List, Any
import re


class MetaCognitiveValidationLogger:
    """Logger for validating meta-cognitive system usage and claims"""

    def __init__(self):
        self.session_logs = []
        self.validation_results = []

    def log_tool_execution(
        self, tool_name: str, parameters: Dict, result: Any, timestamp: str = None
    ) -> Dict[str, Any]:
        """Log a tool execution with parameters and results"""

        if timestamp is None:
            timestamp = datetime.now().isoformat()

        log_entry = {
            "timestamp": timestamp,
            "tool_name": tool_name,
            "parameters": parameters,
            "result": result,
            "success": self._determine_success(result),
            "error_indicators": self._extract_error_indicators(result),
            "guidance_provided": self._extract_guidance(tool_name, result),
        }

        self.session_logs.append(log_entry)
        return log_entry

    def _determine_success(self, result: Any) -> bool:
        """Determine if tool execution was successful"""

        if isinstance(result, dict):
            if "error" in result or "Error" in str(result):
                return False
            if "_id" in result:  # Database operations
                return True

        if isinstance(result, str):
            if "error" in result.lower() or "failed" in result.lower():
                return False

        return True

    def _extract_error_indicators(self, result: Any) -> List[str]:
        """Extract error indicators from tool results"""

        errors = []
        result_str = str(result).lower()

        if "error" in result_str:
            errors.append("error_in_result")
        if "failed" in result_str:
            errors.append("execution_failed")
        if "timeout" in result_str:
            errors.append("timeout_occurred")
        if "rate limit" in result_str:
            errors.append("rate_limited")
        if "not found" in result_str:
            errors.append("resource_not_found")

        return errors

    def _extract_guidance(self, tool_name: str, result: Any) -> Dict[str, Any]:
        """Extract actual guidance provided by tool"""

        guidance = {
            "tool_type": self._categorize_tool(tool_name),
            "guidance_content": None,
            "recommendations": [],
            "metrics": {},
            "insights": [],
        }

        if isinstance(result, dict):
            # Extract recommendations
            if "recommendations" in result:
                guidance["recommendations"] = result["recommendations"]
            if "insights" in result:
                guidance["insights"] = result["insights"]
            if "optimization_opportunities" in result:
                guidance["recommendations"].extend(result["optimization_opportunities"])

            # Extract metrics
            for key, value in result.items():
                if (
                    "efficiency" in key.lower()
                    or "score" in key.lower()
                    or "potential" in key.lower()
                ):
                    if isinstance(value, (int, float)):
                        guidance["metrics"][key] = value
                    elif isinstance(value, dict):
                        guidance["metrics"].update(value)

        guidance["guidance_content"] = result
        return guidance

    def _categorize_tool(self, tool_name: str) -> str:
        """Categorize tool type for analysis"""

        if "cognitive" in tool_name.lower():
            return "cognitive_analysis"
        elif "learning" in tool_name.lower():
            return "meta_learning"
        elif "decision" in tool_name.lower():
            return "decision_enhancement"
        elif "research" in tool_name.lower():
            return "research_system"
        elif "validation" in tool_name.lower():
            return "validation_system"
        else:
            return "unknown"

    def validate_agent_claims(
        self, agent_response: str, claimed_improvements: List[str] = None
    ) -> Dict[str, Any]:
        """Validate agent claims against actual tool results"""

        if not self.session_logs:
            return {"error": "No tool logs available for validation"}

        validation = {
            "timestamp": datetime.now().isoformat(),
            "agent_response_analysis": self._analyze_agent_response(agent_response),
            "tool_usage_validation": self._validate_tool_usage(),
            "claim_verification": self._verify_claims(
                agent_response, claimed_improvements
            ),
            "discrepancy_analysis": self._identify_discrepancies(agent_response),
            "authenticity_assessment": self._assess_authenticity(),
        }

        self.validation_results.append(validation)
        return validation

    def _analyze_agent_response(self, response: str) -> Dict[str, Any]:
        """Analyze agent response for claimed capabilities"""

        analysis = {
            "claimed_tool_usage": [],
            "claimed_metrics": {},
            "claimed_improvements": [],
            "claimed_compound_effects": [],
            "confidence_indicators": [],
        }

        # Extract claimed tool usage
        tool_mentions = re.findall(
            r"(cognitive|learning|decision|research|validation)\s+(analysis|system|tool|framework)",
            response.lower(),
        )
        analysis["claimed_tool_usage"] = list(set(tool_mentions))

        # Extract claimed metrics
        metrics = re.findall(
            r"(\d+\.?\d*)\s*[x×]\s*(amplification|multiplication|improvement|gain)",
            response.lower(),
        )
        for metric in metrics:
            analysis["claimed_metrics"][f"{metric[1]}_factor"] = float(metric[0])

        percentage_metrics = re.findall(
            r"(\d+\.?\d*)%\s*(improvement|efficiency|gain|increase)", response.lower()
        )
        for metric in percentage_metrics:
            analysis["claimed_metrics"][f"{metric[1]}_percentage"] = float(metric[0])

        # Extract improvement claims
        improvements = re.findall(
            r"(improved|enhanced|optimized|increased|amplified)\s+([a-zA-Z\s]+)",
            response.lower(),
        )
        analysis["claimed_improvements"] = [imp[1].strip() for imp in improvements]

        # Extract compound effect claims
        compound_indicators = re.findall(
            r"(compound|multiplicative|emergent|synerg\w+|amplif\w+)", response.lower()
        )
        analysis["claimed_compound_effects"] = list(set(compound_indicators))

        # Confidence indicators
        confidence_words = re.findall(
            r"(successfully|achieved|demonstrated|validated|proven|breakthrough)",
            response.lower(),
        )
        analysis["confidence_indicators"] = list(set(confidence_words))

        return analysis

    def _validate_tool_usage(self) -> Dict[str, Any]:
        """Validate actual tool usage against claims"""

        validation = {
            "tools_actually_used": [],
            "successful_executions": 0,
            "failed_executions": 0,
            "actual_guidance_received": {},
            "tool_categories_used": set(),
        }

        for log_entry in self.session_logs:
            validation["tools_actually_used"].append(log_entry["tool_name"])
            validation["tool_categories_used"].add(
                log_entry["guidance_provided"]["tool_type"]
            )

            if log_entry["success"]:
                validation["successful_executions"] += 1
            else:
                validation["failed_executions"] += 1

            # Collect actual guidance
            guidance = log_entry["guidance_provided"]
            if guidance["recommendations"]:
                validation["actual_guidance_received"]["recommendations"] = guidance[
                    "recommendations"
                ]
            if guidance["metrics"]:
                validation["actual_guidance_received"]["metrics"] = guidance["metrics"]

        validation["tool_categories_used"] = list(validation["tool_categories_used"])
        validation["success_rate"] = (
            validation["successful_executions"] / len(self.session_logs)
            if self.session_logs
            else 0
        )

        return validation

    def _verify_claims(
        self, response: str, claimed_improvements: List[str] = None
    ) -> Dict[str, Any]:
        """Verify specific claims against tool results"""

        response_analysis = self._analyze_agent_response(response)
        tool_validation = self._validate_tool_usage()

        verification = {
            "metric_claims_verified": {},
            "tool_usage_claims_verified": {},
            "improvement_claims_verified": {},
            "overall_authenticity_score": 0.0,
        }

        # Verify metric claims
        claimed_metrics = response_analysis["claimed_metrics"]
        actual_metrics = tool_validation["actual_guidance_received"].get("metrics", {})

        for claimed_metric, claimed_value in claimed_metrics.items():
            verification["metric_claims_verified"][claimed_metric] = {
                "claimed": claimed_value,
                "actual_evidence": self._find_metric_evidence(
                    claimed_metric, actual_metrics
                ),
                "verified": False,
            }

        # Verify tool usage claims
        claimed_tools = response_analysis["claimed_tool_usage"]
        actual_tools = tool_validation["tool_categories_used"]

        for claimed_tool in claimed_tools:
            tool_type = (
                claimed_tool[1]
                if isinstance(claimed_tool, tuple)
                else str(claimed_tool)
            )
            verification["tool_usage_claims_verified"][tool_type] = tool_type in [
                t.replace("_", " ") for t in actual_tools
            ]

        # Calculate authenticity score
        total_claims = len(claimed_metrics) + len(claimed_tools)
        verified_claims = sum(
            1 for v in verification["metric_claims_verified"].values() if v["verified"]
        )
        verified_claims += sum(
            1 for v in verification["tool_usage_claims_verified"].values() if v
        )

        verification["overall_authenticity_score"] = (
            verified_claims / total_claims if total_claims > 0 else 0.0
        )

        return verification

    def _find_metric_evidence(self, claimed_metric: str, actual_metrics: Dict) -> Any:
        """Find evidence for claimed metrics in actual tool results"""

        # Look for similar metric names
        for actual_metric, actual_value in actual_metrics.items():
            if any(
                word in actual_metric.lower()
                for word in claimed_metric.lower().split("_")
            ):
                return actual_value

        return None

    def _identify_discrepancies(self, response: str) -> List[Dict[str, Any]]:
        """Identify discrepancies between claims and evidence"""

        discrepancies = []
        response_analysis = self._analyze_agent_response(response)

        # Check for dramatic claims without evidence
        high_multipliers = [
            m
            for m in response_analysis["claimed_metrics"].values()
            if isinstance(m, (int, float)) and m > 2.0
        ]
        if high_multipliers and not self._has_supporting_evidence():
            discrepancies.append(
                {
                    "type": "unsupported_dramatic_claims",
                    "description": f"Claims multipliers of {high_multipliers} without supporting tool evidence",
                    "severity": "high",
                }
            )

        # Check for tool usage claims without actual usage
        claimed_categories = set(
            t[0] if isinstance(t, tuple) else str(t)
            for t in response_analysis["claimed_tool_usage"]
        )
        actual_categories = set(
            log["guidance_provided"]["tool_type"] for log in self.session_logs
        )

        unclaimed_usage = actual_categories - claimed_categories
        if unclaimed_usage:
            discrepancies.append(
                {
                    "type": "unreported_tool_usage",
                    "description": f"Used tools {unclaimed_usage} but didn't mention them",
                    "severity": "medium",
                }
            )

        # Check for confidence without validation
        confidence_indicators = response_analysis["confidence_indicators"]
        failed_executions = sum(1 for log in self.session_logs if not log["success"])

        if confidence_indicators and failed_executions > 0:
            discrepancies.append(
                {
                    "type": "confidence_despite_failures",
                    "description": f"High confidence claims despite {failed_executions} tool failures",
                    "severity": "high",
                }
            )

        return discrepancies

    def _has_supporting_evidence(self) -> bool:
        """Check if there's supporting evidence for dramatic claims"""

        for log in self.session_logs:
            guidance = log["guidance_provided"]
            if guidance["metrics"]:
                # Look for actual multiplicative effects in tool results
                for metric_name, metric_value in guidance["metrics"].items():
                    if isinstance(metric_value, (int, float)) and metric_value > 1.5:
                        return True

        return False

    def _assess_authenticity(self) -> Dict[str, Any]:
        """Assess overall authenticity of agent's meta-cognitive claims"""

        assessment = {
            "tool_usage_authenticity": 0.0,
            "metric_authenticity": 0.0,
            "improvement_authenticity": 0.0,
            "overall_authenticity": 0.0,
            "red_flags": [],
            "green_flags": [],
        }

        # Tool usage authenticity
        if self.session_logs:
            successful_tools = sum(1 for log in self.session_logs if log["success"])
            assessment["tool_usage_authenticity"] = successful_tools / len(
                self.session_logs
            )

        # Check for red flags
        failed_executions = sum(1 for log in self.session_logs if not log["success"])
        if failed_executions > len(self.session_logs) * 0.3:
            assessment["red_flags"].append("high_tool_failure_rate")

        # Check for green flags
        if any(
            log["guidance_provided"]["recommendations"] for log in self.session_logs
        ):
            assessment["green_flags"].append("actual_guidance_received")

        if (
            len(set(log["guidance_provided"]["tool_type"] for log in self.session_logs))
            > 2
        ):
            assessment["green_flags"].append("diverse_tool_usage")

        # Overall authenticity
        assessment["overall_authenticity"] = (
            assessment["tool_usage_authenticity"]
            + len(assessment["green_flags"]) * 0.2
            - len(assessment["red_flags"]) * 0.3
        )
        assessment["overall_authenticity"] = max(
            0.0, min(1.0, assessment["overall_authenticity"])
        )

        return assessment

    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""

        if not self.validation_results:
            return {"error": "No validation results available"}

        latest_validation = self.validation_results[-1]

        report = {
            "validation_timestamp": datetime.now().isoformat(),
            "session_summary": {
                "total_tool_executions": len(self.session_logs),
                "successful_executions": sum(
                    1 for log in self.session_logs if log["success"]
                ),
                "failed_executions": sum(
                    1 for log in self.session_logs if not log["success"]
                ),
                "tool_categories_used": list(
                    set(
                        log["guidance_provided"]["tool_type"]
                        for log in self.session_logs
                    )
                ),
            },
            "authenticity_assessment": latest_validation["authenticity_assessment"],
            "claim_verification": latest_validation["claim_verification"],
            "discrepancies": latest_validation["discrepancy_analysis"],
            "recommendations": self._generate_validation_recommendations(
                latest_validation
            ),
        }

        return report

    def _generate_validation_recommendations(self, validation: Dict) -> List[str]:
        """Generate recommendations based on validation results"""

        recommendations = []

        authenticity_score = validation["authenticity_assessment"][
            "overall_authenticity"
        ]

        if authenticity_score < 0.5:
            recommendations.append(
                "CRITICAL: Low authenticity score - verify meta-cognitive system functionality"
            )

        if validation["discrepancy_analysis"]:
            high_severity = [
                d for d in validation["discrepancy_analysis"] if d["severity"] == "high"
            ]
            if high_severity:
                recommendations.append(
                    "HIGH PRIORITY: Address high-severity discrepancies in claims vs. evidence"
                )

        success_rate = validation["tool_usage_validation"]["success_rate"]
        if success_rate < 0.7:
            recommendations.append(
                "MODERATE: Improve tool execution success rate for reliable meta-cognitive analysis"
            )

        if not validation["tool_usage_validation"]["actual_guidance_received"]:
            recommendations.append(
                "CRITICAL: No actual guidance received from tools - system may not be functional"
            )

        return recommendations


def main():
    """Main execution function"""
    if len(sys.argv) < 2:
        print("Usage: python3 meta_cognitive_validation_logger.py <command> [args]")
        print("Commands:")
        print("  log_session - Start logging session")
        print("  validate_claims <agent_response_file> - Validate agent claims")
        print("  generate_report - Generate validation report")
        return

    logger = MetaCognitiveValidationLogger()
    command = sys.argv[1]

    if command == "log_session":
        print("Session logging started. Use log_tool_execution() to log tool calls.")

    elif command == "validate_claims":
        if len(sys.argv) < 3:
            print("Error: agent_response_file required")
            return

        try:
            with open(sys.argv[2], "r") as f:
                agent_response = f.read()

            # For demonstration, add some sample tool logs
            sample_logs = [
                {
                    "tool_name": "cognitive_process_analysis_system",
                    "parameters": {"reasoning_text": "sample reasoning"},
                    "result": {
                        "reasoning_efficiency": {"overall_efficiency": 0.65},
                        "optimization_opportunities": [],
                    },
                    "timestamp": datetime.now().isoformat(),
                }
            ]

            for log in sample_logs:
                logger.log_tool_execution(
                    log["tool_name"], log["parameters"], log["result"], log["timestamp"]
                )

            validation = logger.validate_agent_claims(agent_response)
            print(json.dumps(validation, indent=2))

        except FileNotFoundError:
            print(f"Error: File {sys.argv[2]} not found")
        except Exception as e:
            print(f"Error: {str(e)}")

    elif command == "generate_report":
        report = logger.generate_validation_report()
        print(json.dumps(report, indent=2))

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
