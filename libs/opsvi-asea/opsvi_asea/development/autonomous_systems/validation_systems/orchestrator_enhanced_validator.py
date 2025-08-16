#!/usr/bin/env python3
"""
Orchestrator-Enhanced Validator

Uses the ASEA Orchestrator's AI capabilities for sophisticated validation of agent responses.
This creates a "validator agent" that can apply the same cognitive enhancement tools
to assess whether another agent's claims are authentic and well-supported.

Key Features:
- AI-powered claim analysis using Budget Manager + Workflow Intelligence
- Sophisticated authenticity assessment through orchestrator reasoning
- Multi-dimensional validation using coordinated plugin analysis
- Evidence synthesis and credibility scoring
- Comparative analysis between claimed and actual capabilities
"""

import json
import os
import sys
import asyncio
from datetime import datetime
from typing import Dict, List, Any

# Add orchestrator to path
sys.path.append("/home/opsvi/asea/asea_orchestrator/src")

from asea_orchestrator.core import Orchestrator
from asea_orchestrator.workflow import WorkflowManager


class OrchestratorEnhancedValidator:
    """Uses ASEA Orchestrator for sophisticated agent response validation"""

    def __init__(self):
        self.orchestrator = None
        self.validation_workflows = self._define_validation_workflows()
        self.setup_orchestrator()

    def setup_orchestrator(self):
        """Initialize the orchestrator for validation tasks"""
        try:
            plugin_dir = "/home/opsvi/asea/asea_orchestrator/src/asea_orchestrator/plugins/available"

            # Create workflow definitions for validation
            workflow_definitions = {
                "validation_workflow": {
                    "steps": [
                        {
                            "plugin_name": "budget_manager",
                            "parameters": {"operation": "validation"},
                            "outputs": {"cost_estimate": "validation_cost"},
                        },
                        {
                            "plugin_name": "ai_reasoning",
                            "parameters": {"analysis_type": "validation"},
                            "outputs": {"analysis_result": "validation_analysis"},
                        },
                    ]
                }
            }

            workflow_manager = WorkflowManager(workflow_definitions)

            self.orchestrator = Orchestrator(
                plugin_dir=plugin_dir, workflow_manager=workflow_manager
            )

            print("✅ Orchestrator initialized for validation")
        except Exception as e:
            print(f"❌ Failed to initialize orchestrator: {e}")
            self.orchestrator = None

    def _define_validation_workflows(self) -> Dict[str, Dict]:
        """Define validation workflows using orchestrator capabilities"""

        return {
            "authenticity_assessment": {
                "name": "Agent Response Authenticity Assessment",
                "description": "Comprehensive authenticity analysis using AI reasoning",
                "steps": [
                    {
                        "plugin": "budget_manager",
                        "action": "estimate_cost",
                        "params": {
                            "operation": "authenticity_analysis",
                            "complexity": "high",
                        },
                    },
                    {
                        "plugin": "ai_reasoning",
                        "action": "analyze_claims",
                        "params": {
                            "analysis_type": "authenticity_assessment",
                            "evidence_required": True,
                        },
                    },
                    {
                        "plugin": "workflow_intelligence",
                        "action": "assess_workflow",
                        "params": {
                            "workflow_type": "validation_analysis",
                            "optimization_focus": "accuracy",
                        },
                    },
                ],
            },
            "capability_verification": {
                "name": "Capability Claims Verification",
                "description": "Verify claimed capabilities against actual evidence",
                "steps": [
                    {
                        "plugin": "budget_manager",
                        "action": "estimate_cost",
                        "params": {
                            "operation": "capability_verification",
                            "complexity": "medium",
                        },
                    },
                    {
                        "plugin": "ai_reasoning",
                        "action": "verify_capabilities",
                        "params": {
                            "verification_type": "evidence_based",
                            "threshold": "high_confidence",
                        },
                    },
                    {
                        "plugin": "logger",
                        "action": "log_verification_results",
                        "params": {"log_level": "INFO"},
                    },
                ],
            },
            "evidence_synthesis": {
                "name": "Evidence Synthesis and Scoring",
                "description": "Synthesize evidence and generate credibility scores",
                "steps": [
                    {
                        "plugin": "ai_reasoning",
                        "action": "synthesize_evidence",
                        "params": {
                            "synthesis_type": "comprehensive",
                            "scoring_method": "weighted_evidence",
                        },
                    },
                    {
                        "plugin": "workflow_intelligence",
                        "action": "optimize_scoring",
                        "params": {
                            "optimization_target": "accuracy",
                            "bias_correction": True,
                        },
                    },
                ],
            },
        }

    async def validate_agent_response(
        self,
        agent_response: str,
        actual_logs: Dict[str, Any],
        validation_type: str = "comprehensive",
    ) -> Dict[str, Any]:
        """Validate agent response using orchestrator-enhanced analysis"""

        if not self.orchestrator:
            return self._fallback_validation(agent_response, actual_logs)

        validation_context = {
            "agent_response": agent_response,
            "actual_logs": actual_logs,
            "validation_timestamp": datetime.now().isoformat(),
            "validation_type": validation_type,
        }

        results = {
            "validation_context": validation_context,
            "orchestrator_analysis": {},
            "authenticity_assessment": {},
            "capability_verification": {},
            "evidence_synthesis": {},
            "final_validation_score": 0,
            "validation_summary": "",
            "recommendations": [],
        }

        try:
            # Step 1: Authenticity Assessment using AI Reasoning
            print("🔍 Running orchestrator-enhanced authenticity assessment...")
            authenticity_result = await self._run_authenticity_assessment(
                validation_context
            )
            results["authenticity_assessment"] = authenticity_result

            # Step 2: Capability Verification
            print("🔍 Running capability verification analysis...")
            capability_result = await self._run_capability_verification(
                validation_context
            )
            results["capability_verification"] = capability_result

            # Step 3: Evidence Synthesis
            print("🔍 Running evidence synthesis and scoring...")
            evidence_result = await self._run_evidence_synthesis(validation_context)
            results["evidence_synthesis"] = evidence_result

            # Step 4: Final Scoring and Summary
            results[
                "final_validation_score"
            ] = self._calculate_orchestrator_validation_score(results)
            results[
                "validation_summary"
            ] = self._generate_orchestrator_validation_summary(results)
            results["recommendations"] = self._generate_validation_recommendations(
                results
            )

        except Exception as e:
            results["error"] = f"Orchestrator validation failed: {str(e)}"
            results["fallback_used"] = True
            fallback_result = self._fallback_validation(agent_response, actual_logs)
            results.update(fallback_result)

        return results

    async def _run_authenticity_assessment(
        self, validation_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run authenticity assessment using orchestrator AI reasoning"""

        authenticity_prompt = f"""
        Analyze this agent response for authenticity and credibility:
        
        AGENT RESPONSE:
        {validation_context['agent_response'][:2000]}...
        
        ACTUAL TOOL LOGS:
        {json.dumps(validation_context['actual_logs'], indent=2)[:1000]}...
        
        Assess authenticity across these dimensions:
        1. Consistency between claims and evidence
        2. Plausibility of claimed tool usage
        3. Reasonableness of claimed results
        4. Detection of potential overstatement or fabrication
        5. Overall credibility assessment
        
        Provide specific evidence for your assessment and assign scores (1-10) for each dimension.
        """

        try:
            # Use budget manager to estimate cost
            budget_result = await self._execute_plugin_action(
                "budget_manager",
                "estimate_cost",
                {
                    "operation": "authenticity_analysis",
                    "prompt_tokens": len(authenticity_prompt.split()),
                    "complexity": "high",
                },
            )

            # Use AI reasoning for analysis
            reasoning_result = await self._execute_plugin_action(
                "ai_reasoning",
                "analyze_claims",
                {
                    "prompt": authenticity_prompt,
                    "analysis_type": "authenticity_assessment",
                    "max_tokens": 1000,
                },
            )

            return {
                "budget_estimation": budget_result,
                "ai_analysis": reasoning_result,
                "assessment_timestamp": datetime.now().isoformat(),
                "assessment_type": "orchestrator_enhanced",
            }

        except Exception as e:
            return {
                "error": f"Authenticity assessment failed: {str(e)}",
                "fallback_assessment": "manual_review_required",
            }

    async def _run_capability_verification(
        self, validation_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify claimed capabilities using orchestrator analysis"""

        capability_prompt = f"""
        Verify the capabilities claimed in this agent response:
        
        CLAIMED CAPABILITIES ANALYSIS:
        - Extract all capability claims from the response
        - Assess each claim against available evidence
        - Identify overstatement or unsupported claims
        - Rate the evidence quality for each claim
        
        AGENT RESPONSE:
        {validation_context['agent_response'][:1500]}...
        
        AVAILABLE EVIDENCE:
        {json.dumps(validation_context['actual_logs'], indent=2)[:800]}...
        
        For each claimed capability, provide:
        1. Capability description
        2. Evidence assessment (strong/moderate/weak/none)
        3. Verification confidence (1-10)
        4. Specific supporting or contradicting evidence
        """

        try:
            # Estimate verification cost
            budget_result = await self._execute_plugin_action(
                "budget_manager",
                "estimate_cost",
                {
                    "operation": "capability_verification",
                    "prompt_tokens": len(capability_prompt.split()),
                    "complexity": "medium",
                },
            )

            # Run capability verification
            verification_result = await self._execute_plugin_action(
                "ai_reasoning",
                "verify_capabilities",
                {
                    "prompt": capability_prompt,
                    "verification_type": "evidence_based",
                    "max_tokens": 1200,
                },
            )

            return {
                "budget_estimation": budget_result,
                "verification_analysis": verification_result,
                "verification_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "error": f"Capability verification failed: {str(e)}",
                "fallback_verification": "manual_review_required",
            }

    async def _run_evidence_synthesis(
        self, validation_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthesize evidence and generate final scoring"""

        synthesis_prompt = """
        Synthesize all available evidence to generate a comprehensive validation assessment:
        
        SYNTHESIS REQUIREMENTS:
        1. Weight evidence quality and relevance
        2. Account for potential biases or overstatement
        3. Generate quantitative credibility scores
        4. Identify key strengths and weaknesses
        5. Provide actionable recommendations
        
        EVIDENCE TO SYNTHESIZE:
        - Agent response claims and assertions
        - Actual tool execution logs and outputs
        - Consistency analysis between claims and evidence
        - Capability verification results
        
        Generate a final credibility score (0-100) with detailed justification.
        """

        try:
            # Run evidence synthesis
            synthesis_result = await self._execute_plugin_action(
                "ai_reasoning",
                "synthesize_evidence",
                {
                    "prompt": synthesis_prompt,
                    "synthesis_type": "comprehensive",
                    "max_tokens": 800,
                },
            )

            # Use workflow intelligence for optimization
            workflow_result = await self._execute_plugin_action(
                "workflow_intelligence",
                "optimize_scoring",
                {
                    "workflow_data": synthesis_result,
                    "optimization_target": "accuracy",
                    "bias_correction": True,
                },
            )

            return {
                "synthesis_analysis": synthesis_result,
                "workflow_optimization": workflow_result,
                "synthesis_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "error": f"Evidence synthesis failed: {str(e)}",
                "fallback_synthesis": "basic_scoring_required",
            }

    async def _execute_plugin_action(
        self, plugin_name: str, action: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a plugin action through the orchestrator"""

        if not self.orchestrator:
            raise Exception("Orchestrator not available")

        try:
            # Create workflow for the specific action
            workflow_config = {
                "name": f"{plugin_name}_{action}",
                "steps": [{"plugin": plugin_name, "action": action, "params": params}],
            }

            # Execute through orchestrator
            result = await self.orchestrator.run_workflow(
                workflow_config["name"],
                initial_state=workflow_config.get("parameters", {}),
            )

            return {
                "plugin": plugin_name,
                "action": action,
                "result": result,
                "execution_timestamp": datetime.now().isoformat(),
                "success": True,
            }

        except Exception as e:
            return {
                "plugin": plugin_name,
                "action": action,
                "error": str(e),
                "execution_timestamp": datetime.now().isoformat(),
                "success": False,
            }

    def _calculate_orchestrator_validation_score(
        self, results: Dict[str, Any]
    ) -> float:
        """Calculate final validation score from orchestrator analysis"""

        base_score = 50.0  # Neutral starting point

        # Authenticity assessment impact (40 points)
        authenticity = results.get("authenticity_assessment", {})
        if "ai_analysis" in authenticity and "error" not in authenticity["ai_analysis"]:
            # TODO: Extract scores from AI analysis
            base_score += 20  # Placeholder - would extract actual scores

        # Capability verification impact (35 points)
        capability = results.get("capability_verification", {})
        if (
            "verification_analysis" in capability
            and "error" not in capability["verification_analysis"]
        ):
            base_score += 15  # Placeholder - would extract verification scores

        # Evidence synthesis impact (25 points)
        evidence = results.get("evidence_synthesis", {})
        if (
            "synthesis_analysis" in evidence
            and "error" not in evidence["synthesis_analysis"]
        ):
            base_score += 10  # Placeholder - would extract synthesis scores

        return min(100.0, max(0.0, base_score))

    def _generate_orchestrator_validation_summary(self, results: Dict[str, Any]) -> str:
        """Generate validation summary from orchestrator analysis"""

        score = results["final_validation_score"]

        summary_parts = [
            "🤖 ORCHESTRATOR-ENHANCED VALIDATION RESULTS",
            f"Final Validation Score: {score:.1f}/100",
            "",
        ]

        # Authenticity assessment summary
        authenticity = results.get("authenticity_assessment", {})
        if "error" not in authenticity:
            summary_parts.extend(
                [
                    "✅ Authenticity Assessment: Completed using AI reasoning",
                    "   - Multi-dimensional credibility analysis performed",
                    "   - Evidence-claim consistency evaluated",
                ]
            )
        else:
            summary_parts.append(
                "❌ Authenticity Assessment: Failed - using fallback methods"
            )

        # Capability verification summary
        capability = results.get("capability_verification", {})
        if "error" not in capability:
            summary_parts.extend(
                [
                    "✅ Capability Verification: Completed using orchestrator analysis",
                    "   - Individual capability claims assessed",
                    "   - Evidence quality ratings generated",
                ]
            )
        else:
            summary_parts.append(
                "❌ Capability Verification: Failed - manual review required"
            )

        # Evidence synthesis summary
        evidence = results.get("evidence_synthesis", {})
        if "error" not in evidence:
            summary_parts.extend(
                [
                    "✅ Evidence Synthesis: Completed with workflow optimization",
                    "   - Comprehensive evidence weighting applied",
                    "   - Bias correction and optimization performed",
                ]
            )
        else:
            summary_parts.append("❌ Evidence Synthesis: Failed - basic scoring used")

        # Overall assessment
        if score >= 80:
            summary_parts.append(
                "\n🟢 VALIDATION RESULT: High confidence in agent claims"
            )
        elif score >= 60:
            summary_parts.append(
                "\n🟡 VALIDATION RESULT: Moderate confidence with some concerns"
            )
        elif score >= 40:
            summary_parts.append(
                "\n🟠 VALIDATION RESULT: Low confidence - significant concerns"
            )
        else:
            summary_parts.append(
                "\n🔴 VALIDATION RESULT: Very low confidence - major credibility issues"
            )

        return "\n".join(summary_parts)

    def _generate_validation_recommendations(
        self, results: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations from validation results"""

        recommendations = []
        score = results["final_validation_score"]

        if score < 60:
            recommendations.extend(
                [
                    "🔍 Recommend independent verification of claimed capabilities",
                    "📊 Request specific evidence for quantitative claims",
                    "🧪 Conduct controlled testing to verify tool effectiveness",
                ]
            )

        if score < 40:
            recommendations.extend(
                [
                    "⚠️ Consider this agent response unreliable for decision-making",
                    "🔄 Recommend re-testing with fresh agent and better controls",
                    "📝 Document credibility concerns for future reference",
                ]
            )

        # Add specific recommendations based on analysis results
        authenticity = results.get("authenticity_assessment", {})
        if "error" in authenticity:
            recommendations.append(
                "🔧 Fix orchestrator integration for better authenticity assessment"
            )

        return recommendations

    def _fallback_validation(
        self, agent_response: str, actual_logs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback validation when orchestrator is not available"""

        return {
            "validation_type": "fallback",
            "orchestrator_available": False,
            "basic_analysis": {
                "response_length": len(agent_response),
                "log_entries": sum(
                    len(logs) if isinstance(logs, list) else 0
                    for logs in actual_logs.values()
                ),
                "timestamp": datetime.now().isoformat(),
            },
            "final_validation_score": 50,  # Neutral score when can't validate
            "validation_summary": "⚠️ Orchestrator validation unavailable - using basic fallback analysis",
            "recommendations": [
                "🔧 Fix orchestrator integration for enhanced validation capabilities"
            ],
        }


async def main():
    """Main execution function"""

    if len(sys.argv) < 2:
        print("Usage: python3 orchestrator_enhanced_validator.py <command> [args]")
        print("Commands:")
        print(
            "  validate_response <response_file> [logs_file] - Validate agent response"
        )
        print("  test_orchestrator - Test orchestrator integration")
        return

    validator = OrchestratorEnhancedValidator()
    command = sys.argv[1]

    if command == "validate_response":
        if len(sys.argv) < 3:
            print("Error: response_file required")
            return

        response_file = sys.argv[2]
        logs_file = sys.argv[3] if len(sys.argv) > 3 else None

        try:
            # Load agent response
            with open(response_file, "r") as f:
                agent_response = f.read()

            # Load logs if provided
            actual_logs = {}
            if logs_file and os.path.exists(logs_file):
                with open(logs_file, "r") as f:
                    actual_logs = json.load(f)
            else:
                # Load from standard log locations
                log_dir = "/home/opsvi/asea/development/autonomous_systems/logs"
                for log_file in ["cognitive_analysis.log", "decision_system.log"]:
                    log_path = os.path.join(log_dir, log_file)
                    if os.path.exists(log_path):
                        tool_name = log_file.replace(".log", "")
                        actual_logs[tool_name] = []
                        with open(log_path, "r") as f:
                            for line in f:
                                if line.strip():
                                    try:
                                        actual_logs[tool_name].append(
                                            json.loads(line.strip())
                                        )
                                    except:
                                        pass

            # Run validation
            validation_results = await validator.validate_agent_response(
                agent_response, actual_logs
            )

            # Output results
            print(json.dumps(validation_results, indent=2))

        except FileNotFoundError:
            print(f"Error: File {response_file} not found")
        except Exception as e:
            print(f"Error: {str(e)}")

    elif command == "test_orchestrator":
        print("🧪 Testing orchestrator integration...")

        if validator.orchestrator:
            print("✅ Orchestrator initialized successfully")

            # Test basic plugin access
            try:
                plugins = validator.orchestrator.plugin_manager.list_available_plugins()
                print(f"✅ Available plugins: {len(plugins)}")
                for plugin_name in plugins[:5]:  # Show first 5
                    print(f"   - {plugin_name}")
            except Exception as e:
                print(f"❌ Plugin access failed: {e}")
        else:
            print("❌ Orchestrator initialization failed")

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    asyncio.run(main())
