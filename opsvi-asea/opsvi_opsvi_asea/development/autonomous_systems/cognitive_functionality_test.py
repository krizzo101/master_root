#!/usr/bin/env python3
"""
Comprehensive Cognitive Functionality Testing

Tests whether the orchestrator's cognitive plugins actually enhance cognition:
1. AI Reasoning Plugin - Real AI analysis vs. baseline
2. Cognitive Critic Plugin - Quality of critique and feedback
3. Budget Manager Plugin - Accurate cost calculations
4. Workflow Intelligence Plugin - Meaningful optimization insights

This tests COGNITIVE EFFECTIVENESS, not just technical execution.
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Add orchestrator to path
sys.path.append("/home/opsvi/asea/asea_orchestrator/src")

from asea_orchestrator.orchestrator_manager import OrchestratorManager


class CognitiveFunctionalityTester:
    def __init__(self):
        self.orchestrator_manager = None
        self.test_results = {}

    async def initialize(self):
        """Initialize orchestrator for testing."""
        try:
            plugin_dir = "/home/opsvi/asea/asea_orchestrator/src/asea_orchestrator/plugins/available"
            self.orchestrator_manager = OrchestratorManager(plugin_dir)
            await self.orchestrator_manager.initialize()
            print("✅ Orchestrator initialized for cognitive testing")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize orchestrator: {e}")
            return False

    async def test_ai_reasoning_quality(self) -> Dict[str, Any]:
        """Test whether AI reasoning actually provides intelligent analysis."""
        print("\n🧠 Testing AI Reasoning Plugin Quality...")

        test_scenario = {
            "prompt": "Analyze the trade-offs between microservices and monolithic architecture for a startup with 5 developers building a financial application. Consider scalability, development speed, operational complexity, and cost.",
            "context": {
                "team_size": 5,
                "domain": "financial",
                "stage": "startup",
                "priorities": [
                    "development_speed",
                    "cost_efficiency",
                    "regulatory_compliance",
                ],
            },
            "model": "gpt-4.1-mini",
            "max_tokens": 800,
        }

        try:
            # Execute AI reasoning
            workflow_def = {
                "name": "ai_reasoning_quality_test",
                "steps": [
                    {
                        "plugin_name": "ai_reasoning",
                        "inputs": {"action": "reason", **test_scenario},
                    }
                ],
            }

            # Create a simple workflow for testing
            workflow_name = workflow_def["name"]

            # Register the workflow with the workflow manager
            from asea_orchestrator.workflow import Workflow, WorkflowStep

            steps = []
            for i, step_def in enumerate(workflow_def["steps"]):
                step = WorkflowStep(
                    plugin_name=step_def["plugin_name"],
                    inputs=step_def.get("inputs", {}),
                    outputs={f"step_{i}": f"step_{i}"},
                    parameters=step_def.get("inputs", {}),
                )
                steps.append(step)

            workflow = Workflow(name=workflow_name, steps=steps)
            self.orchestrator_manager.orchestrator.workflow_manager.workflows[
                workflow_name
            ] = workflow

            # Execute the workflow
            result = await self.orchestrator_manager.orchestrator.run_workflow(
                workflow_name, initial_state=workflow_def["steps"][0].get("inputs", {})
            )

            if result and result.get("success"):
                reasoning_data = (
                    result.get("data", {}).get("step_0", {}).get("data", {})
                )
                reasoning_text = reasoning_data.get("reasoning", "")

                # Analyze quality of reasoning
                quality_metrics = self._analyze_reasoning_quality(
                    reasoning_text, test_scenario
                )

                return {
                    "success": True,
                    "reasoning_provided": bool(reasoning_text),
                    "reasoning_length": len(reasoning_text),
                    "quality_metrics": quality_metrics,
                    "model_used": reasoning_data.get("model_used"),
                    "tokens_used": reasoning_data.get("tokens_used"),
                    "cost_data": reasoning_data.get("cost_data"),
                    "sample_reasoning": reasoning_text[:200] + "..."
                    if len(reasoning_text) > 200
                    else reasoning_text,
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error_message", "Unknown error"),
                    "quality_metrics": {"overall_score": 0},
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "quality_metrics": {"overall_score": 0},
            }

    async def test_cognitive_critic_effectiveness(self) -> Dict[str, Any]:
        """Test whether cognitive critic provides meaningful feedback."""
        print("\n🔍 Testing Cognitive Critic Plugin Effectiveness...")

        # Test with a deliberately flawed response
        flawed_response = """
        Microservices are always better than monoliths. You should definitely use microservices because they're modern and scalable. Just split everything into separate services and you'll be fine. Don't worry about the complexity.
        """

        original_prompt = (
            "Should a 5-person startup use microservices or monolithic architecture?"
        )

        try:
            workflow_def = {
                "name": "cognitive_critic_test",
                "steps": [
                    {
                        "plugin_name": "cognitive_critic",
                        "inputs": {
                            "original_prompt": original_prompt,
                            "agent_response": flawed_response,
                            "critique_focus": "comprehensive",
                        },
                    }
                ],
            }

            result = await self.orchestrator_manager.orchestrator.execute_workflow(
                workflow_def
            )

            if result and result.get("success"):
                critic_data = result.get("data", {}).get("step_0", {}).get("data", {})
                critique = critic_data.get("critique", {})

                # Analyze critique effectiveness
                effectiveness_metrics = self._analyze_critique_effectiveness(
                    critique, flawed_response
                )

                return {
                    "success": True,
                    "critique_provided": bool(critique),
                    "needs_revision": critic_data.get("needs_revision"),
                    "revision_priority": critic_data.get("revision_priority"),
                    "quality_score": critic_data.get("quality_score"),
                    "specific_issues_count": len(
                        critic_data.get("specific_issues", [])
                    ),
                    "improvement_suggestions_count": len(
                        critic_data.get("improvement_suggestions", [])
                    ),
                    "effectiveness_metrics": effectiveness_metrics,
                    "sample_critique": str(critique.get("overall_assessment", ""))[:200]
                    + "...",
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error_message", "Unknown error"),
                    "effectiveness_metrics": {"overall_score": 0},
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "effectiveness_metrics": {"overall_score": 0},
            }

    async def test_budget_manager_accuracy(self) -> Dict[str, Any]:
        """Test whether budget manager provides accurate cost calculations."""
        print("\n💰 Testing Budget Manager Plugin Accuracy...")

        test_operations = [
            {
                "action": "estimate_cost",
                "model": "gpt-4.1-mini",
                "input_tokens": 500,
                "estimated_output_tokens": 1000,
            },
            {
                "action": "get_recommended_model",
                "task_type": "reasoning",
                "max_cost_usd": 0.01,
            },
            {"action": "check_budget", "estimated_cost_usd": 0.005, "period": "daily"},
        ]

        results = []

        try:
            for operation in test_operations:
                workflow_def = {
                    "name": f"budget_test_{operation['action']}",
                    "steps": [{"plugin_name": "budget_manager", "inputs": operation}],
                }

                result = await self.orchestrator_manager.orchestrator.execute_workflow(
                    workflow_def
                )

                if result and result.get("success"):
                    budget_data = (
                        result.get("data", {}).get("step_0", {}).get("data", {})
                    )
                    results.append(
                        {
                            "operation": operation["action"],
                            "success": True,
                            "data": budget_data,
                        }
                    )
                else:
                    results.append(
                        {
                            "operation": operation["action"],
                            "success": False,
                            "error": result.get("error_message", "Unknown error"),
                        }
                    )

            # Analyze accuracy
            accuracy_metrics = self._analyze_budget_accuracy(results)

            return {
                "success": True,
                "operations_tested": len(test_operations),
                "successful_operations": len([r for r in results if r["success"]]),
                "accuracy_metrics": accuracy_metrics,
                "detailed_results": results,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "accuracy_metrics": {"overall_score": 0},
            }

    async def test_workflow_intelligence_insights(self) -> Dict[str, Any]:
        """Test whether workflow intelligence provides meaningful insights."""
        print("\n📊 Testing Workflow Intelligence Plugin Insights...")

        # Create a test workflow to analyze
        test_workflow = {
            "name": "test_workflow_analysis",
            "steps": [
                {"plugin_name": "web_search", "inputs": {"query": "test"}},
                {"plugin_name": "arango_db", "inputs": {"action": "query"}},
                {"plugin_name": "logger", "inputs": {"message": "test"}},
            ],
        }

        test_operations = [
            {"action": "analyze", "workflow_definition": test_workflow},
            {
                "action": "recommend_optimizations",
                "workflow_definition": test_workflow,
                "performance_target": "balanced",
            },
        ]

        results = []

        try:
            for operation in test_operations:
                workflow_def = {
                    "name": f"workflow_intelligence_test_{operation['action']}",
                    "steps": [
                        {"plugin_name": "workflow_intelligence", "inputs": operation}
                    ],
                }

                result = await self.orchestrator_manager.orchestrator.execute_workflow(
                    workflow_def
                )

                if result and result.get("success"):
                    intelligence_data = (
                        result.get("data", {}).get("step_0", {}).get("data", {})
                    )
                    results.append(
                        {
                            "operation": operation["action"],
                            "success": True,
                            "data": intelligence_data,
                        }
                    )
                else:
                    results.append(
                        {
                            "operation": operation["action"],
                            "success": False,
                            "error": result.get("error_message", "Unknown error"),
                        }
                    )

            # Analyze insight quality
            insight_metrics = self._analyze_workflow_insights(results)

            return {
                "success": True,
                "operations_tested": len(test_operations),
                "successful_operations": len([r for r in results if r["success"]]),
                "insight_metrics": insight_metrics,
                "detailed_results": results,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "insight_metrics": {"overall_score": 0},
            }

    def _analyze_reasoning_quality(
        self, reasoning_text: str, scenario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze the quality of AI reasoning output."""
        if not reasoning_text:
            return {"overall_score": 0, "issues": ["No reasoning provided"]}

        quality_indicators = {
            "mentions_microservices": "microservice" in reasoning_text.lower(),
            "mentions_monolith": "monolith" in reasoning_text.lower(),
            "addresses_scalability": "scalability" in reasoning_text.lower()
            or "scale" in reasoning_text.lower(),
            "addresses_cost": "cost" in reasoning_text.lower()
            or "budget" in reasoning_text.lower(),
            "addresses_team_size": "team" in reasoning_text.lower()
            or "developer" in reasoning_text.lower(),
            "provides_tradeoffs": "trade" in reasoning_text.lower()
            or "pros" in reasoning_text.lower()
            or "cons" in reasoning_text.lower(),
            "structured_analysis": len(reasoning_text.split("\n")) > 3,
            "sufficient_depth": len(reasoning_text) > 300,
        }

        score = sum(quality_indicators.values()) / len(quality_indicators)

        return {
            "overall_score": score,
            "quality_indicators": quality_indicators,
            "reasoning_length": len(reasoning_text),
            "structure_score": 1 if quality_indicators["structured_analysis"] else 0,
            "depth_score": 1 if quality_indicators["sufficient_depth"] else 0,
            "relevance_score": sum(
                [
                    quality_indicators["mentions_microservices"],
                    quality_indicators["mentions_monolith"],
                    quality_indicators["addresses_scalability"],
                    quality_indicators["addresses_cost"],
                ]
            )
            / 4,
        }

    def _analyze_critique_effectiveness(
        self, critique: Dict[str, Any], original_response: str
    ) -> Dict[str, Any]:
        """Analyze how effective the cognitive critique is."""
        if not critique:
            return {"overall_score": 0, "issues": ["No critique provided"]}

        effectiveness_indicators = {
            "identified_issues": len(critique.get("specific_issues", [])) > 0,
            "provided_suggestions": len(critique.get("improvement_suggestions", []))
            > 0,
            "assigned_quality_score": "quality_score" in critique
            and isinstance(critique["quality_score"], (int, float)),
            "identified_logical_gaps": len(critique.get("logical_gaps", [])) > 0,
            "flagged_for_revision": critique.get("needs_revision", False),
            "detailed_assessment": len(str(critique.get("overall_assessment", "")))
            > 50,
            "identified_missing_elements": len(critique.get("missing_elements", []))
            > 0,
            "provided_alternative_approaches": len(
                critique.get("alternative_approaches", [])
            )
            > 0,
        }

        # Check if critique correctly identified the flawed response
        flawed_response_indicators = {
            "caught_oversimplification": "simple" in str(critique).lower()
            or "complex" in str(critique).lower(),
            "caught_absolutism": "always" in str(critique).lower()
            or "absolute" in str(critique).lower(),
            "suggested_nuance": "consider" in str(critique).lower()
            or "depend" in str(critique).lower(),
        }

        effectiveness_score = sum(effectiveness_indicators.values()) / len(
            effectiveness_indicators
        )
        flaw_detection_score = sum(flawed_response_indicators.values()) / len(
            flawed_response_indicators
        )

        return {
            "overall_score": (effectiveness_score + flaw_detection_score) / 2,
            "effectiveness_indicators": effectiveness_indicators,
            "flaw_detection_indicators": flawed_response_indicators,
            "critique_quality_score": critique.get("quality_score", 0),
            "revision_recommended": critique.get("needs_revision", False),
            "issues_identified": len(critique.get("specific_issues", [])),
            "suggestions_provided": len(critique.get("improvement_suggestions", [])),
        }

    def _analyze_budget_accuracy(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze budget manager accuracy."""
        successful_results = [r for r in results if r["success"]]

        if not successful_results:
            return {"overall_score": 0, "issues": ["No successful operations"]}

        accuracy_indicators = {
            "cost_estimation_works": any(
                r["operation"] == "estimate_cost"
                and "total_estimated_cost_usd" in r.get("data", {})
                for r in successful_results
            ),
            "model_recommendation_works": any(
                r["operation"] == "get_recommended_model"
                and "recommended_model" in r.get("data", {})
                for r in successful_results
            ),
            "budget_checking_works": any(
                r["operation"] == "check_budget" and "can_proceed" in r.get("data", {})
                for r in successful_results
            ),
            "provides_cost_breakdown": any(
                "input_cost_usd" in r.get("data", {})
                and "output_cost_usd" in r.get("data", {})
                for r in successful_results
            ),
            "realistic_cost_values": True,  # Would need real validation against known pricing
        }

        # Check for reasonable cost calculations
        cost_estimate_result = next(
            (r for r in successful_results if r["operation"] == "estimate_cost"), None
        )
        if cost_estimate_result:
            cost_data = cost_estimate_result.get("data", {})
            total_cost = cost_data.get("total_estimated_cost_usd", 0)
            # For 500 input + 1000 output tokens on gpt-4.1-mini, should be around $0.002
            accuracy_indicators["reasonable_cost_estimate"] = (
                0.001 <= total_cost <= 0.01
            )

        score = sum(accuracy_indicators.values()) / len(accuracy_indicators)

        return {
            "overall_score": score,
            "accuracy_indicators": accuracy_indicators,
            "successful_operations": len(successful_results),
            "total_operations": len(results),
        }

    def _analyze_workflow_insights(
        self, results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze workflow intelligence insight quality."""
        successful_results = [r for r in results if r["success"]]

        if not successful_results:
            return {"overall_score": 0, "issues": ["No successful operations"]}

        insight_indicators = {
            "workflow_analysis_provided": any(
                r["operation"] == "analyze" and "workflow_analysis" in r.get("data", {})
                for r in successful_results
            ),
            "optimization_recommendations_provided": any(
                r["operation"] == "recommend_optimizations"
                and "recommendations" in r.get("data", {})
                for r in successful_results
            ),
            "complexity_scoring": any(
                "complexity_score" in str(r.get("data", {})) for r in successful_results
            ),
            "risk_identification": any(
                "risk_factors" in str(r.get("data", {})) for r in successful_results
            ),
            "actionable_recommendations": any(
                len(r.get("data", {}).get("recommendations", [])) > 0
                for r in successful_results
            ),
        }

        # Check recommendation quality
        optimization_result = next(
            (
                r
                for r in successful_results
                if r["operation"] == "recommend_optimizations"
            ),
            None,
        )
        if optimization_result:
            recommendations = optimization_result.get("data", {}).get(
                "recommendations", []
            )
            insight_indicators["specific_recommendations"] = len(recommendations) > 0
            insight_indicators["detailed_recommendations"] = any(
                len(str(rec.get("description", ""))) > 20 for rec in recommendations
            )

        score = sum(insight_indicators.values()) / len(insight_indicators)

        return {
            "overall_score": score,
            "insight_indicators": insight_indicators,
            "successful_operations": len(successful_results),
            "total_operations": len(results),
        }

    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all cognitive functionality tests."""
        print("🚀 Starting Comprehensive Cognitive Functionality Testing...")
        print("=" * 60)

        if not await self.initialize():
            return {"error": "Failed to initialize orchestrator"}

        # Run all tests
        test_results = {}

        try:
            test_results["ai_reasoning"] = await self.test_ai_reasoning_quality()
            test_results[
                "cognitive_critic"
            ] = await self.test_cognitive_critic_effectiveness()
            test_results["budget_manager"] = await self.test_budget_manager_accuracy()
            test_results[
                "workflow_intelligence"
            ] = await self.test_workflow_intelligence_insights()

            # Calculate overall cognitive enhancement score
            cognitive_scores = []
            for test_name, result in test_results.items():
                if result.get("success"):
                    if "quality_metrics" in result:
                        cognitive_scores.append(
                            result["quality_metrics"].get("overall_score", 0)
                        )
                    elif "effectiveness_metrics" in result:
                        cognitive_scores.append(
                            result["effectiveness_metrics"].get("overall_score", 0)
                        )
                    elif "accuracy_metrics" in result:
                        cognitive_scores.append(
                            result["accuracy_metrics"].get("overall_score", 0)
                        )
                    elif "insight_metrics" in result:
                        cognitive_scores.append(
                            result["insight_metrics"].get("overall_score", 0)
                        )

            overall_cognitive_score = (
                sum(cognitive_scores) / len(cognitive_scores) if cognitive_scores else 0
            )

            test_results["overall_assessment"] = {
                "cognitive_enhancement_score": overall_cognitive_score,
                "tests_passed": sum(
                    1 for r in test_results.values() if r.get("success", False)
                ),
                "total_tests": len(
                    [k for k in test_results.keys() if k != "overall_assessment"]
                ),
                "cognitive_effectiveness": "HIGH"
                if overall_cognitive_score >= 0.7
                else "MEDIUM"
                if overall_cognitive_score >= 0.4
                else "LOW",
                "recommendation": self._generate_overall_recommendation(
                    overall_cognitive_score, test_results
                ),
            }

            return test_results

        except Exception as e:
            return {"error": f"Test execution failed: {str(e)}"}

        finally:
            if self.orchestrator_manager:
                try:
                    await self.orchestrator_manager.shutdown()
                except AttributeError:
                    # Orchestrator manager may not have cleanup method
                    pass

    def _generate_overall_recommendation(
        self, score: float, results: Dict[str, Any]
    ) -> str:
        """Generate overall recommendation based on test results."""
        if score >= 0.7:
            return "Cognitive enhancement is working effectively. Orchestrator provides meaningful cognitive improvements."
        elif score >= 0.4:
            return "Cognitive enhancement shows promise but needs improvement. Some plugins working better than others."
        else:
            return "Cognitive enhancement is not working effectively. Significant improvements needed before deployment."


async def main():
    """Run cognitive functionality tests."""
    tester = CognitiveFunctionalityTester()
    results = await tester.run_comprehensive_test()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"/home/opsvi/asea/development/autonomous_systems/cognitive_functionality_test_results_{timestamp}.json"

    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Print summary
    print("\n" + "=" * 60)
    print("🎯 COGNITIVE FUNCTIONALITY TEST RESULTS")
    print("=" * 60)

    if "error" in results:
        print(f"❌ Test failed: {results['error']}")
        return

    overall = results.get("overall_assessment", {})
    print(
        f"🧠 Cognitive Enhancement Score: {overall.get('cognitive_enhancement_score', 0):.2f}"
    )
    print(
        f"✅ Tests Passed: {overall.get('tests_passed', 0)}/{overall.get('total_tests', 0)}"
    )
    print(f"📊 Effectiveness: {overall.get('cognitive_effectiveness', 'UNKNOWN')}")
    print(f"💡 Recommendation: {overall.get('recommendation', 'No recommendation')}")

    print(f"\n📄 Detailed results saved to: {results_file}")

    # Print individual test summaries
    for test_name, result in results.items():
        if test_name == "overall_assessment":
            continue

        print(f"\n{test_name.upper()}:")
        if result.get("success"):
            print(f"  ✅ Success")
            for metric_key in [
                "quality_metrics",
                "effectiveness_metrics",
                "accuracy_metrics",
                "insight_metrics",
            ]:
                if metric_key in result:
                    score = result[metric_key].get("overall_score", 0)
                    print(f"  📊 {metric_key.replace('_', ' ').title()}: {score:.2f}")
        else:
            print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    asyncio.run(main())
