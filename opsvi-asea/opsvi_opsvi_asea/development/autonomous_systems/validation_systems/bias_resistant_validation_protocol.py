#!/usr/bin/env python3
"""
Bias-Resistant Validation Protocol

Addresses confirmation bias and validation gaps identified in fresh agent testing.
Implements systematic cross-reference validation with skeptical defaults.
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime


class BiasResistantValidator:
    """Validation system designed to resist confirmation bias and validation gaps"""

    def __init__(self):
        self.skeptical_default = True
        self.validation_errors = []
        self.bias_flags = []

    def validate_capability_claims(
        self, claims: Dict[str, Any], evidence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate capability claims with bias resistance"""

        validation = {
            "timestamp": datetime.now().isoformat(),
            "claims_analyzed": claims,
            "evidence_analyzed": evidence,
            "systematic_cross_reference": self._systematic_cross_reference(
                claims, evidence
            ),
            "bias_detection": self._detect_validation_bias(claims, evidence),
            "skeptical_assessment": self._apply_skeptical_assessment(claims, evidence),
            "validation_gaps": self._identify_validation_gaps(claims, evidence),
            "corrected_authenticity_score": 0,
            "reliability_assessment": "",
        }

        # Calculate bias-resistant authenticity score
        validation[
            "corrected_authenticity_score"
        ] = self._calculate_bias_resistant_score(validation)

        # Assess overall reliability
        validation["reliability_assessment"] = self._assess_reliability(validation)

        return validation

    def _systematic_cross_reference(
        self, claims: Dict[str, Any], evidence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Systematically cross-reference every claim against every piece of evidence"""

        cross_reference = {
            "total_claims": 0,
            "claims_with_evidence": 0,
            "claims_without_evidence": 0,
            "evidence_without_claims": 0,
            "detailed_mapping": {},
        }

        # Extract all claims
        all_claims = []
        if "claimed_actions" in claims:
            all_claims.extend(claims["claimed_actions"])
        if "claimed_tool_usage" in claims:
            all_claims.extend(claims["claimed_tool_usage"])
        if "claimed_results" in claims:
            all_claims.extend(claims["claimed_results"])
        if "claimed_metrics" in claims:
            all_claims.extend(claims["claimed_metrics"])

        cross_reference["total_claims"] = len(all_claims)

        # Cross-reference each claim
        for claim in all_claims:
            claim_evidence = self._find_evidence_for_claim(claim, evidence)
            cross_reference["detailed_mapping"][claim] = {
                "evidence_found": len(claim_evidence) > 0,
                "evidence_details": claim_evidence,
                "evidence_strength": self._assess_evidence_strength(claim_evidence),
            }

            if len(claim_evidence) > 0:
                cross_reference["claims_with_evidence"] += 1
            else:
                cross_reference["claims_without_evidence"] += 1

        # Identify evidence not connected to claims
        all_evidence_items = []
        if "actual_tool_executions" in evidence:
            for tool, executions in evidence["actual_tool_executions"].items():
                all_evidence_items.extend(executions)

        cross_reference["evidence_without_claims"] = len(
            [
                item
                for item in all_evidence_items
                if not self._evidence_supports_any_claim(item, all_claims)
            ]
        )

        return cross_reference

    def _find_evidence_for_claim(
        self, claim: str, evidence: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find evidence that supports a specific claim"""

        supporting_evidence = []
        claim_lower = claim.lower()

        if "actual_tool_executions" in evidence:
            for tool_name, executions in evidence["actual_tool_executions"].items():
                for execution in executions:
                    # Check if this execution supports the claim
                    if self._execution_supports_claim(
                        execution, claim_lower, tool_name
                    ):
                        supporting_evidence.append(
                            {
                                "tool": tool_name,
                                "execution": execution,
                                "support_type": self._classify_support_type(
                                    execution, claim_lower
                                ),
                            }
                        )

        return supporting_evidence

    def _execution_supports_claim(
        self, execution: Dict[str, Any], claim_lower: str, tool_name: str
    ) -> bool:
        """Check if an execution supports a claim"""

        # Direct tool name match
        if tool_name.replace("_", " ") in claim_lower or tool_name in claim_lower:
            return True

        # Method name match
        if "method" in execution and execution["method"] in claim_lower:
            return True

        # Output content match
        if "data" in execution and "output" in execution["data"]:
            output = execution["data"]["output"]
            if isinstance(output, dict):
                for key in output.keys():
                    if key.replace("_", " ") in claim_lower:
                        return True

        return False

    def _classify_support_type(
        self, execution: Dict[str, Any], claim_lower: str
    ) -> str:
        """Classify the type of support evidence provides"""

        if "method" in execution and execution["method"] in claim_lower:
            return "direct_method_match"
        elif "data" in execution and "output" in execution["data"]:
            return "output_content_match"
        else:
            return "indirect_support"

    def _assess_evidence_strength(self, evidence_list: List[Dict[str, Any]]) -> str:
        """Assess the strength of evidence for a claim"""

        if len(evidence_list) == 0:
            return "no_evidence"
        elif len(evidence_list) == 1:
            support_type = evidence_list[0].get("support_type", "")
            if support_type == "direct_method_match":
                return "strong_evidence"
            else:
                return "weak_evidence"
        else:
            return "multiple_evidence"

    def _evidence_supports_any_claim(
        self, evidence_item: Dict[str, Any], claims: List[str]
    ) -> bool:
        """Check if evidence item supports any claim"""

        for claim in claims:
            if self._execution_supports_claim(evidence_item, claim.lower(), ""):
                return True
        return False

    def _detect_validation_bias(
        self, claims: Dict[str, Any], evidence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect potential validation bias patterns"""

        bias_detection = {
            "confirmation_bias_indicators": [],
            "overgeneralization_indicators": [],
            "cherry_picking_indicators": [],
            "overall_bias_risk": "low",
        }

        # Check for confirmation bias
        total_claims = (
            len(claims.get("claimed_actions", []))
            + len(claims.get("claimed_tool_usage", []))
            + len(claims.get("claimed_results", []))
            + len(claims.get("claimed_metrics", []))
        )

        if "actual_tool_executions" in evidence:
            total_executions = sum(
                len(executions)
                for executions in evidence["actual_tool_executions"].values()
            )

            # If claims significantly exceed evidence
            if total_claims > total_executions * 2:
                bias_detection["confirmation_bias_indicators"].append(
                    "Claims significantly exceed evidence"
                )

            # Check for overgeneralization
            tools_with_evidence = len(
                [
                    tool
                    for tool, executions in evidence["actual_tool_executions"].items()
                    if executions
                ]
            )
            total_tools_referenced = len(set(claims.get("claimed_tool_usage", [])))

            if total_tools_referenced > tools_with_evidence:
                bias_detection["overgeneralization_indicators"].append(
                    "Claims reference more tools than have evidence"
                )

        # Assess overall bias risk
        total_indicators = (
            len(bias_detection["confirmation_bias_indicators"])
            + len(bias_detection["overgeneralization_indicators"])
            + len(bias_detection["cherry_picking_indicators"])
        )

        if total_indicators > 2:
            bias_detection["overall_bias_risk"] = "high"
        elif total_indicators > 0:
            bias_detection["overall_bias_risk"] = "medium"

        return bias_detection

    def _apply_skeptical_assessment(
        self, claims: Dict[str, Any], evidence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply skeptical assessment with high burden of proof"""

        skeptical_assessment = {
            "burden_of_proof_standard": "high",
            "claims_meeting_standard": [],
            "claims_failing_standard": [],
            "evidence_quality_assessment": {},
            "skeptical_score": 0,
        }

        # High burden of proof for each claim
        all_claims = (
            claims.get("claimed_actions", [])
            + claims.get("claimed_tool_usage", [])
            + claims.get("claimed_results", [])
            + claims.get("claimed_metrics", [])
        )

        for claim in all_claims:
            evidence_for_claim = self._find_evidence_for_claim(claim, evidence)
            evidence_strength = self._assess_evidence_strength(evidence_for_claim)

            if evidence_strength in ["strong_evidence", "multiple_evidence"]:
                skeptical_assessment["claims_meeting_standard"].append(
                    {
                        "claim": claim,
                        "evidence_strength": evidence_strength,
                        "evidence_count": len(evidence_for_claim),
                    }
                )
            else:
                skeptical_assessment["claims_failing_standard"].append(
                    {
                        "claim": claim,
                        "evidence_strength": evidence_strength,
                        "reason": "Insufficient evidence to meet high burden of proof",
                    }
                )

        # Calculate skeptical score
        total_claims = len(all_claims)
        claims_meeting_standard = len(skeptical_assessment["claims_meeting_standard"])

        if total_claims > 0:
            skeptical_assessment["skeptical_score"] = (
                claims_meeting_standard / total_claims
            ) * 100

        return skeptical_assessment

    def _identify_validation_gaps(
        self, claims: Dict[str, Any], evidence: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify specific validation gaps"""

        gaps = []

        # Gap 1: Claims without evidence
        all_claims = (
            claims.get("claimed_actions", [])
            + claims.get("claimed_tool_usage", [])
            + claims.get("claimed_results", [])
            + claims.get("claimed_metrics", [])
        )

        for claim in all_claims:
            evidence_for_claim = self._find_evidence_for_claim(claim, evidence)
            if len(evidence_for_claim) == 0:
                gaps.append(
                    {
                        "gap_type": "claim_without_evidence",
                        "description": f"Claim '{claim}' has no supporting evidence",
                        "severity": "high",
                    }
                )

        # Gap 2: Evidence without claims
        if "actual_tool_executions" in evidence:
            for tool_name, executions in evidence["actual_tool_executions"].items():
                for execution in executions:
                    if not self._evidence_supports_any_claim(execution, all_claims):
                        gaps.append(
                            {
                                "gap_type": "evidence_without_claims",
                                "description": f"Tool execution {tool_name} not reflected in claims",
                                "severity": "medium",
                            }
                        )

        # Gap 3: Inconsistent tool usage claims
        claimed_tools = set(claims.get("claimed_tool_usage", []))
        actual_tools = set()
        if "actual_tool_executions" in evidence:
            actual_tools = set(
                tool
                for tool, executions in evidence["actual_tool_executions"].items()
                if executions
            )

        for claimed_tool in claimed_tools:
            if not any(
                claimed_tool in actual_tool or actual_tool in claimed_tool
                for actual_tool in actual_tools
            ):
                gaps.append(
                    {
                        "gap_type": "inconsistent_tool_claims",
                        "description": f"Claimed tool '{claimed_tool}' not found in actual executions",
                        "severity": "high",
                    }
                )

        return gaps

    def _calculate_bias_resistant_score(self, validation: Dict[str, Any]) -> float:
        """Calculate authenticity score with bias resistance"""

        score = 0.0

        # Base score from skeptical assessment
        skeptical_score = validation["skeptical_assessment"]["skeptical_score"]
        score += skeptical_score * 0.6  # 60% weight to skeptical assessment

        # Penalty for validation gaps
        gaps = validation["validation_gaps"]
        high_severity_gaps = len([gap for gap in gaps if gap["severity"] == "high"])
        medium_severity_gaps = len([gap for gap in gaps if gap["severity"] == "medium"])

        gap_penalty = (high_severity_gaps * 15) + (medium_severity_gaps * 5)
        score -= gap_penalty

        # Penalty for bias indicators
        bias_detection = validation["bias_detection"]
        if bias_detection["overall_bias_risk"] == "high":
            score -= 20
        elif bias_detection["overall_bias_risk"] == "medium":
            score -= 10

        # Cross-reference quality bonus
        cross_ref = validation["systematic_cross_reference"]
        if cross_ref["total_claims"] > 0:
            evidence_ratio = (
                cross_ref["claims_with_evidence"] / cross_ref["total_claims"]
            )
            score += evidence_ratio * 40  # Up to 40 points for complete evidence

        return max(0.0, min(100.0, score))

    def _assess_reliability(self, validation: Dict[str, Any]) -> str:
        """Assess overall reliability of validation"""

        score = validation["corrected_authenticity_score"]
        gaps = len(validation["validation_gaps"])
        bias_risk = validation["bias_detection"]["overall_bias_risk"]

        if score >= 80 and gaps == 0 and bias_risk == "low":
            return "high_reliability"
        elif score >= 60 and gaps <= 2 and bias_risk != "high":
            return "moderate_reliability"
        elif score >= 40:
            return "low_reliability"
        else:
            return "unreliable"


def main():
    """Test the bias-resistant validation protocol"""

    # Example usage with the fresh agent test data
    validator = BiasResistantValidator()

    # Mock claims and evidence for testing
    test_claims = {
        "claimed_actions": [
            "I used parallel research on optimization + meta-cognition"
        ],
        "claimed_tool_usage": ["meta-cognitive", "framework", "assessment"],
        "claimed_results": [],
        "claimed_metrics": [],
    }

    test_evidence = {
        "actual_tool_executions": {
            "cognitive_analysis": [
                {
                    "method": "capture_reasoning_sequence",
                    "data": {"output": {"efficiency": 0.67}},
                }
            ],
            "decision_system": [
                {
                    "method": "assess_decision_quality",
                    "data": {"output": {"autonomous_score": 50}},
                }
            ],
            "meta_cognitive": [],
        }
    }

    validation_result = validator.validate_capability_claims(test_claims, test_evidence)
    print(json.dumps(validation_result, indent=2))


if __name__ == "__main__":
    main()
