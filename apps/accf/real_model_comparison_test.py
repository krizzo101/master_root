"""
Real Model Comparison Test for o3_agent Tool

This script actually calls the o3_agent tool for each approved model to compare
their responses to the same prompt.
"""

import asyncio
import json
import time
from typing import Dict, List, Any
from datetime import datetime

# Test prompt designed to evaluate different model capabilities
TEST_PROMPT = """
You are a senior software architect tasked with designing a scalable microservices architecture for a new e-commerce platform. The platform needs to handle:

1. 100,000+ concurrent users
2. Real-time inventory management
3. Payment processing with multiple providers
4. Order fulfillment and shipping
5. Customer analytics and personalization
6. Multi-tenant support for different storefronts

Requirements:
- 99.9% uptime SLA
- Sub-second response times for critical operations
- GDPR compliance for EU customers
- PCI DSS compliance for payment processing
- Horizontal scalability for peak shopping seasons

Please provide:
1. A high-level architecture diagram description
2. Service decomposition with clear boundaries
3. Data flow patterns for key operations
4. Technology stack recommendations
5. Security considerations and implementation
6. Monitoring and observability strategy
7. Deployment and scaling approach
8. Potential challenges and mitigation strategies

Focus on practical, production-ready solutions with specific implementation details.
"""

APPROVED_MODELS = ["o4-mini", "o3", "gpt-4.1-mini", "gpt-4.1", "gpt-4.1-nano"]


class RealModelComparisonTester:
    """Test and compare different models using the actual o3_agent tool."""

    def __init__(self):
        self.results = {}

    async def test_model_with_o3_agent(self, model: str) -> Dict[str, Any]:
        """Test a single model using the actual o3_agent tool."""
        print(f"\n{'='*60}")
        print(f"Testing model: {model}")
        print(f"{'='*60}")

        start_time = time.time()

        try:
            # Import and use the actual o3_agent tool
            # This would be the real MCP tool call
            from mcp_agent_server import ConsultAgentTool

            # Create the tool instance
            tool = ConsultAgentTool()

            # Call the tool with the test prompt
            result = await tool.execute(
                {
                    "prompt": TEST_PROMPT,
                    "model": model,
                    "iterate": 1,  # No iterations as requested
                    "critic_enabled": False,  # No critic as requested
                    "artifact_type": "design",  # Use design artifact type for architecture
                }
            )

            # Extract text from TextContent objects
            response_text = ""
            if result and len(result) > 0:
                response_text = result[0].text

            end_time = time.time()
            execution_time = end_time - start_time

            response_data = {
                "model": model,
                "prompt": TEST_PROMPT,
                "response": response_text,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
                "tool_response": result,
                "metrics": self._analyze_response(response_text),
            }

            self.results[model] = response_data

            print(f"✅ Successfully tested {model}")
            print(f"   Execution time: {execution_time:.2f}s")
            print(f"   Response length: {len(response_text)} characters")

            return response_data

        except Exception as e:
            print(f"❌ Error testing {model}: {e}")
            error_data = {
                "model": model,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat(),
            }
            self.results[model] = error_data
            return error_data

    def _analyze_response(self, response: str) -> Dict[str, Any]:
        """Analyze response characteristics and quality metrics."""
        if not response:
            return {
                "word_count": 0,
                "character_count": 0,
                "section_count": 0,
                "code_block_count": 0,
                "bullet_point_count": 0,
                "numbered_list_count": 0,
                "technical_depth_score": 0.0,
                "structure_score": 0.0,
                "completeness_score": 0.0,
            }

        metrics = {
            "word_count": len(response.split()),
            "character_count": len(response),
            "section_count": response.count("##"),
            "code_block_count": response.count("```"),
            "bullet_point_count": response.count("- "),
            "numbered_list_count": response.count("1.")
            + response.count("2.")
            + response.count("3."),
            "technical_depth_score": self._calculate_technical_depth(response),
            "structure_score": self._calculate_structure_score(response),
            "completeness_score": self._calculate_completeness_score(response),
        }

        return metrics

    def _calculate_technical_depth(self, response: str) -> float:
        """Calculate technical depth score (0-10)."""
        technical_terms = [
            "microservices",
            "kubernetes",
            "docker",
            "api gateway",
            "load balancer",
            "database",
            "cache",
            "message queue",
            "monitoring",
            "logging",
            "security",
            "authentication",
            "authorization",
            "encryption",
            "ssl",
            "scalability",
            "availability",
            "performance",
            "latency",
            "throughput",
        ]

        found_terms = sum(
            1 for term in technical_terms if term.lower() in response.lower()
        )
        return min(10.0, (found_terms / len(technical_terms)) * 10)

    def _calculate_structure_score(self, response: str) -> float:
        """Calculate structure and organization score (0-10)."""
        structure_indicators = [
            response.count("##"),  # Headers
            response.count("###"),  # Sub-headers
            response.count("- "),  # Bullet points
            response.count("1."),  # Numbered lists
            response.count("```"),  # Code blocks
        ]

        total_indicators = sum(structure_indicators)
        return min(10.0, (total_indicators / 20) * 10)  # Normalize to 0-10

    def _calculate_completeness_score(self, response: str) -> float:
        """Calculate completeness score based on required sections (0-10)."""
        required_sections = [
            "architecture",
            "service",
            "data flow",
            "technology",
            "security",
            "monitoring",
            "deployment",
            "challenges",
        ]

        found_sections = sum(
            1 for section in required_sections if section.lower() in response.lower()
        )
        return min(10.0, (found_sections / len(required_sections)) * 10)

    async def run_comparison(self) -> Dict[str, Any]:
        """Run comparison tests for all models."""
        print("🚀 Starting Real Model Comparison Test")
        print(f"Testing {len(APPROVED_MODELS)} models: {', '.join(APPROVED_MODELS)}")
        print(f"Test prompt length: {len(TEST_PROMPT)} characters")
        print(f"Test prompt preview: {TEST_PROMPT[:100]}...")

        start_time = time.time()

        # Test each model
        for model in APPROVED_MODELS:
            try:
                await self.test_model_with_o3_agent(model)
                await asyncio.sleep(2)  # Brief pause between tests
            except Exception as e:
                print(f"❌ Error testing model {model}: {e}")
                self.results[model] = {"error": str(e)}

        total_time = time.time() - start_time

        # Generate comparison report
        comparison_report = self._generate_comparison_report(total_time)

        return comparison_report

    def _generate_comparison_report(self, total_time: float) -> Dict[str, Any]:
        """Generate comprehensive comparison report."""
        print(f"\n{'='*80}")
        print("📊 MODEL COMPARISON REPORT")
        print(f"{'='*80}")

        report = {
            "test_summary": {
                "total_models_tested": len(APPROVED_MODELS),
                "models_tested": APPROVED_MODELS,
                "total_execution_time": total_time,
                "test_prompt_length": len(TEST_PROMPT),
                "timestamp": datetime.now().isoformat(),
            },
            "model_results": {},
            "comparison_analysis": {},
            "recommendations": {},
        }

        # Analyze each model's results
        successful_models = []
        for model in APPROVED_MODELS:
            if model in self.results and "error" not in self.results[model]:
                result = self.results[model]
                metrics = result["metrics"]
                successful_models.append(model)

                print(f"\n📈 {model.upper()} RESULTS:")
                print(f"  ⏱️  Execution Time: {result['execution_time']:.2f}s")
                print(f"  📝 Word Count: {metrics['word_count']}")
                print(
                    f"  🔧 Technical Depth: {metrics['technical_depth_score']:.1f}/10"
                )
                print(f"  📋 Structure Score: {metrics['structure_score']:.1f}/10")
                print(f"  ✅ Completeness: {metrics['completeness_score']:.1f}/10")

                report["model_results"][model] = {
                    "execution_time": result["execution_time"],
                    "metrics": metrics,
                    "response_preview": (
                        result["response"][:300] + "..."
                        if len(result["response"]) > 300
                        else result["response"]
                    ),
                    "full_response": result["response"],
                }
            else:
                print(f"\n❌ {model.upper()}: FAILED")
                if model in self.results:
                    print(
                        f"  Error: {self.results[model].get('error', 'Unknown error')}"
                    )

        # Generate comparison analysis
        if successful_models:
            self._analyze_model_differences(report, successful_models)
            self._generate_recommendations(report, successful_models)
        else:
            print("\n❌ No successful model tests to analyze")

        return report

    def _analyze_model_differences(
        self, report: Dict[str, Any], successful_models: List[str]
    ):
        """Analyze differences between models."""
        print(f"\n{'='*60}")
        print("🔍 MODEL DIFFERENCES ANALYSIS")
        print(f"{'='*60}")

        analysis = {}

        # Compare execution times
        execution_times = {
            model: report["model_results"][model]["execution_time"]
            for model in successful_models
        }
        fastest_model = min(execution_times, key=execution_times.get)
        slowest_model = max(execution_times, key=execution_times.get)

        analysis["performance"] = {
            "fastest_model": fastest_model,
            "slowest_model": slowest_model,
            "time_range": f"{execution_times[fastest_model]:.2f}s - {execution_times[slowest_model]:.2f}s",
        }

        # Compare technical depth
        technical_scores = {
            model: report["model_results"][model]["metrics"]["technical_depth_score"]
            for model in successful_models
        }
        highest_tech = max(technical_scores, key=technical_scores.get)
        lowest_tech = min(technical_scores, key=technical_scores.get)

        analysis["technical_depth"] = {
            "highest": highest_tech,
            "lowest": lowest_tech,
            "score_range": f"{technical_scores[lowest_tech]:.1f} - {technical_scores[highest_tech]:.1f}/10",
        }

        # Compare structure quality
        structure_scores = {
            model: report["model_results"][model]["metrics"]["structure_score"]
            for model in successful_models
        }
        best_structured = max(structure_scores, key=structure_scores.get)
        worst_structured = min(structure_scores, key=structure_scores.get)

        analysis["structure_quality"] = {
            "best_structured": best_structured,
            "worst_structured": worst_structured,
            "score_range": f"{structure_scores[worst_structured]:.1f} - {structure_scores[best_structured]:.1f}/10",
        }

        report["comparison_analysis"] = analysis

        print(
            f"⚡ Performance: {fastest_model} is fastest ({execution_times[fastest_model]:.2f}s)"
        )
        print(
            f"🔧 Technical Depth: {highest_tech} has highest score ({technical_scores[highest_tech]:.1f}/10)"
        )
        print(
            f"📋 Structure Quality: {best_structured} has best structure ({structure_scores[best_structured]:.1f}/10)"
        )

    def _generate_recommendations(
        self, report: Dict[str, Any], successful_models: List[str]
    ):
        """Generate recommendations based on model characteristics."""
        print(f"\n{'='*60}")
        print("💡 RECOMMENDATIONS")
        print(f"{'='*60}")

        recommendations = {
            "use_cases": {},
            "prompt_optimization": {},
            "model_selection": {},
        }

        # Model-specific recommendations based on actual test results
        for model in successful_models:
            metrics = report["model_results"][model]["metrics"]
            execution_time = report["model_results"][model]["execution_time"]

            # Generate recommendations based on actual performance
            if execution_time < 5.0:
                speed_characteristic = "Very fast"
            elif execution_time < 10.0:
                speed_characteristic = "Fast"
            else:
                speed_characteristic = "Slower"

            if metrics["technical_depth_score"] > 8.0:
                depth_characteristic = "High technical depth"
            elif metrics["technical_depth_score"] > 6.0:
                depth_characteristic = "Good technical depth"
            else:
                depth_characteristic = "Basic technical depth"

            recommendations["use_cases"][
                model
            ] = f"{speed_characteristic} with {depth_characteristic}. Best for {'quick overviews' if execution_time < 5.0 else 'detailed analysis' if metrics['technical_depth_score'] > 7.0 else 'general guidance'}."

        # Prompt optimization recommendations
        recommendations["prompt_optimization"] = {
            "o4-mini": "Use concise, direct prompts. Focus on key requirements.",
            "o3": "Use detailed, context-rich prompts. Include reasoning requirements.",
            "gpt-4.1-mini": "Use structured prompts with clear sections.",
            "gpt-4.1": "Use comprehensive prompts with detailed requirements.",
            "gpt-4.1-nano": "Use simple, focused prompts with essential information only.",
        }

        # Model selection guidance
        if successful_models:
            fastest = min(
                successful_models,
                key=lambda m: report["model_results"][m]["execution_time"],
            )
            highest_quality = max(
                successful_models,
                key=lambda m: report["model_results"][m]["metrics"][
                    "technical_depth_score"
                ],
            )

            recommendations["model_selection"] = {
                "speed_priority": fastest,
                "quality_priority": highest_quality,
                "reasoning_priority": "o3",  # Based on known characteristics
                "cost_priority": "gpt-4.1-nano",  # Based on known characteristics
                "balanced_choice": "gpt-4.1-mini",  # Based on known characteristics
            }

        report["recommendations"] = recommendations

        print("🎯 Model Selection Guide:")
        if successful_models:
            fastest = min(
                successful_models,
                key=lambda m: report["model_results"][m]["execution_time"],
            )
            highest_quality = max(
                successful_models,
                key=lambda m: report["model_results"][m]["metrics"][
                    "technical_depth_score"
                ],
            )
            print(f"- ⚡ Speed Priority: {fastest}")
            print(f"- 🏆 Quality Priority: {highest_quality}")
            print("- 🧠 Reasoning Priority: o3")
            print("- 💰 Cost Priority: gpt-4.1-nano")
            print("- ⚖️  Balanced Choice: gpt-4.1-mini")

    def save_report(
        self,
        report: Dict[str, Any],
        filename: str = "real_model_comparison_report.json",
    ):
        """Save the comparison report to a JSON file."""
        with open(filename, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n💾 Report saved to: {filename}")

    def save_responses(self, filename: str = "model_responses.md"):
        """Save individual model responses to a markdown file for easy comparison."""
        with open(filename, "w") as f:
            f.write("# Model Comparison Responses\n\n")
            f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Test Prompt:\n```\n{TEST_PROMPT}\n```\n\n")

            for model in APPROVED_MODELS:
                if model in self.results and "error" not in self.results[model]:
                    result = self.results[model]
                    f.write(f"## {model.upper()}\n\n")
                    f.write(f"**Execution Time**: {result['execution_time']:.2f}s\n\n")
                    f.write(f"**Metrics**:\n")
                    f.write(f"- Word Count: {result['metrics']['word_count']}\n")
                    f.write(
                        f"- Technical Depth: {result['metrics']['technical_depth_score']:.1f}/10\n"
                    )
                    f.write(
                        f"- Structure Score: {result['metrics']['structure_score']:.1f}/10\n"
                    )
                    f.write(
                        f"- Completeness: {result['metrics']['completeness_score']:.1f}/10\n\n"
                    )
                    f.write(f"**Response**:\n\n{result['response']}\n\n")
                    f.write("---\n\n")
                else:
                    f.write(f"## {model.upper()}\n\n")
                    f.write(f"**Status**: FAILED\n")
                    if model in self.results:
                        f.write(
                            f"**Error**: {self.results[model].get('error', 'Unknown error')}\n"
                        )
                    f.write("\n---\n\n")

        print(f"📄 Individual responses saved to: {filename}")


async def main():
    """Main function to run the real model comparison test."""
    tester = RealModelComparisonTester()

    try:
        print("🔧 Starting Real Model Comparison Test")
        print("This will test all approved models using the actual o3_agent tool")
        print("Make sure the MCP server is running and accessible")

        report = await tester.run_comparison()
        tester.save_report(report)
        tester.save_responses()

        print(f"\n{'='*80}")
        print("✅ TEST COMPLETED SUCCESSFULLY")
        print(f"{'='*80}")
        print("📋 Generated files:")
        print("1. real_model_comparison_report.json - Detailed metrics and analysis")
        print("2. model_responses.md - Individual model responses for comparison")
        print("\n🎯 Next steps:")
        print("1. Review the detailed report and individual responses")
        print("2. Analyze model-specific characteristics and differences")
        print("3. Consider implementing model-specific prompt optimizations")
        print("4. Update o3_agent tool with model-specific prompting strategies")

    except Exception as e:
        print(f"❌ Error during model comparison: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
