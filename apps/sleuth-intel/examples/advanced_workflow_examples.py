"""
Advanced Workflow Examples

Demonstrates sophisticated workflow patterns including:
- Conditional execution based on results
- Dynamic workflow modification
- Multi-stage investigations
- Result correlation and analysis
- Performance optimization strategies
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.orchestration.sleuth_orchestrator import SleuthIntelOrchestrator
from src.orchestration.workflow_templates import (
    InvestigationDepth,
    WorkflowBudget,
    WorkflowCustomization,
    WorkflowTemplateManager,
)


class AdaptiveWorkflowManager:
    """Manages adaptive workflows that modify based on intermediate results"""

    def __init__(self, orchestrator: SleuthIntelOrchestrator):
        self.orchestrator = orchestrator
        self.manager = WorkflowTemplateManager(orchestrator)

    async def execute_adaptive_investigation(
        self,
        initial_data: Dict[str, Any],
        investigation_goals: List[str],
        budget: Optional[WorkflowBudget] = None,
    ) -> Dict[str, Any]:
        """Execute adaptive investigation that modifies based on findings"""

        stages = []
        current_budget = budget
        accumulated_results = {
            "stages": [],
            "total_cost": 0.0,
            "total_time": 0.0,
            "confidence_progression": [],
            "discovery_timeline": [],
        }

        # Stage 1: Initial reconnaissance
        print("Stage 1: Initial Reconnaissance")
        stage1_result = await self._execute_reconnaissance_stage(
            initial_data, current_budget
        )
        stages.append(stage1_result)
        accumulated_results["stages"].append(stage1_result)

        # Analyze Stage 1 results to determine next steps
        stage2_plan = self._analyze_results_for_next_stage(
            stage1_result, investigation_goals
        )

        if stage2_plan and current_budget:
            current_budget.max_cost_usd -= stage1_result["metadata"]["total_cost"]
            if current_budget.max_cost_usd <= 0:
                print("Budget exhausted after Stage 1")
                return accumulated_results

        # Stage 2: Targeted deep dive
        if stage2_plan:
            print(f"Stage 2: {stage2_plan['description']}")
            stage2_result = await self._execute_targeted_stage(
                stage2_plan, stage1_result, current_budget
            )
            stages.append(stage2_result)
            accumulated_results["stages"].append(stage2_result)

            # Stage 3: Correlation and validation
            correlation_result = await self._execute_correlation_stage(stages)
            accumulated_results["stages"].append(correlation_result)

        # Final analysis and reporting
        final_analysis = await self._generate_comprehensive_report(accumulated_results)
        accumulated_results["final_analysis"] = final_analysis

        return accumulated_results

    async def _execute_reconnaissance_stage(
        self, data: Dict[str, Any], budget: Optional[WorkflowBudget]
    ) -> Dict[str, Any]:
        """Execute initial reconnaissance to gather basic intelligence"""

        # Determine primary data type
        if "phone_number" in data:
            primary_workflow = "phone_investigation"
        elif "company_name" in data:
            primary_workflow = "business_due_diligence"
        elif "first_name" in data and "last_name" in data:
            primary_workflow = "person_investigation"
        elif "street_address" in data:
            primary_workflow = "address_analysis"
        else:
            raise ValueError("Unable to determine primary investigation type from data")

        # Execute basic investigation
        result = await self.manager.execute_workflow(
            template_type=primary_workflow,
            depth="basic",
            query_data=data,
            budget=budget,
        )

        result["stage_name"] = "reconnaissance"
        result["primary_workflow"] = primary_workflow

        return result

    def _analyze_results_for_next_stage(
        self, stage1_result: Dict[str, Any], goals: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Analyze Stage 1 results to determine optimal Stage 2 strategy"""

        success_rate = stage1_result["metadata"]["success_rate"]
        data_sources = stage1_result["results"]["data_sources"]
        correlations = stage1_result["results"]["correlations"]

        # If low success rate, try different providers
        if success_rate < 0.5:
            return {
                "type": "provider_diversification",
                "description": "Diversifying data providers due to low success rate",
                "strategy": "comprehensive",
                "focus": "alternative_sources",
            }

        # If good correlations, do deep dive
        if len(correlations) > 2:
            return {
                "type": "deep_correlation",
                "description": "Deep investigation based on strong correlations",
                "strategy": "deep",
                "focus": "correlation_expansion",
            }

        # If business focus detected
        if any("business" in goal.lower() for goal in goals):
            if "business" not in stage1_result["primary_workflow"]:
                return {
                    "type": "business_expansion",
                    "description": "Expanding investigation to business connections",
                    "strategy": "comprehensive",
                    "focus": "business_network",
                }

        # Default: comprehensive investigation
        return {
            "type": "comprehensive_expansion",
            "description": "Comprehensive multi-source investigation",
            "strategy": "comprehensive",
            "focus": "multi_source",
        }

    async def _execute_targeted_stage(
        self,
        plan: Dict[str, Any],
        previous_result: Dict[str, Any],
        budget: Optional[WorkflowBudget],
    ) -> Dict[str, Any]:
        """Execute targeted investigation based on Stage 1 findings"""

        # Extract data from previous stage for expansion
        expansion_data = self._extract_expansion_data(previous_result)

        if plan["type"] == "business_expansion":
            result = await self.manager.execute_workflow(
                template_type="business_due_diligence",
                depth=plan["strategy"],
                query_data=expansion_data,
                budget=budget,
            )
        elif plan["type"] == "deep_correlation":
            # Use the same workflow type but with deep investigation
            workflow_type = previous_result["primary_workflow"]
            result = await self.manager.execute_workflow(
                template_type=workflow_type,
                depth="deep",
                query_data=expansion_data,
                budget=budget,
            )
        else:
            # Comprehensive multi-source investigation
            workflow_type = previous_result["primary_workflow"]
            result = await self.manager.execute_workflow(
                template_type=workflow_type,
                depth="comprehensive",
                query_data=expansion_data,
                budget=budget,
            )

        result["stage_name"] = "targeted_investigation"
        result["plan_type"] = plan["type"]

        return result

    def _extract_expansion_data(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from previous results for investigation expansion"""
        expansion_data = {}

        # Extract data from successful results
        for detailed_result in result["results"]["detailed_results"]:
            if detailed_result["success"] and detailed_result["data"]:
                data = detailed_result["data"]

                # Extract common expansion fields
                expansion_fields = [
                    "first_name",
                    "last_name",
                    "company_name",
                    "phone_number",
                    "email_address",
                    "street_address",
                    "city",
                    "state",
                    "zip_code",
                ]

                for field in expansion_fields:
                    if field in data and data[field] and field not in expansion_data:
                        expansion_data[field] = data[field]

        return expansion_data

    async def _execute_correlation_stage(
        self, stages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute correlation analysis across all stages"""

        all_results = []
        for stage in stages:
            all_results.extend(stage["results"]["detailed_results"])

        # Advanced correlation analysis
        correlations = self._calculate_advanced_correlations(all_results)
        confidence_scores = self._calculate_confidence_scores(all_results)
        data_integrity = self._assess_data_integrity(all_results)

        return {
            "stage_name": "correlation_analysis",
            "advanced_correlations": correlations,
            "confidence_scores": confidence_scores,
            "data_integrity": data_integrity,
            "timestamp": datetime.now(),
        }

    def _calculate_advanced_correlations(
        self, results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate advanced correlations with statistical measures"""

        correlations = {
            "identity_confirmations": [],
            "data_conflicts": [],
            "confidence_clusters": [],
            "source_reliability": {},
        }

        # Group results by data type
        data_by_type = {}
        for result in results:
            agent_type = result.get("agent_type", "unknown")
            if agent_type not in data_by_type:
                data_by_type[agent_type] = []
            data_by_type[agent_type].append(result)

        # Identify identity confirmations
        for agent_type, agent_results in data_by_type.items():
            for result in agent_results:
                if result["success"] and result["data"]:
                    # Look for confirmations across different agents
                    confirmations = self._find_cross_agent_confirmations(
                        result, data_by_type, agent_type
                    )
                    if confirmations:
                        correlations["identity_confirmations"].append(
                            {
                                "source_agent": agent_type,
                                "confirmations": confirmations,
                                "confidence": len(confirmations) / len(data_by_type),
                            }
                        )

        return correlations

    def _find_cross_agent_confirmations(
        self,
        target_result: Dict[str, Any],
        all_data: Dict[str, List[Dict[str, Any]]],
        source_agent: str,
    ) -> List[Dict[str, Any]]:
        """Find confirmations of data across different agents"""

        confirmations = []
        target_data = target_result.get("data", {})

        for agent_type, results in all_data.items():
            if agent_type == source_agent:
                continue

            for result in results:
                if result["success"] and result["data"]:
                    matches = self._find_data_matches(target_data, result["data"])
                    if matches:
                        confirmations.append(
                            {
                                "confirming_agent": agent_type,
                                "matching_fields": matches,
                                "match_confidence": len(matches)
                                / max(len(target_data), len(result["data"])),
                            }
                        )

        return confirmations

    def _find_data_matches(
        self, data1: Dict[str, Any], data2: Dict[str, Any]
    ) -> List[str]:
        """Find matching data fields between two datasets"""
        matches = []

        for key, value in data1.items():
            if key in data2 and value and data2[key]:
                # Normalize values for comparison
                val1 = str(value).lower().strip()
                val2 = str(data2[key]).lower().strip()

                if val1 == val2:
                    matches.append(key)
                elif self._fuzzy_match(val1, val2):
                    matches.append(f"{key}_fuzzy")

        return matches

    def _fuzzy_match(self, val1: str, val2: str) -> bool:
        """Simple fuzzy matching for similar values"""
        # Basic similarity check
        shorter = min(len(val1), len(val2))
        longer = max(len(val1), len(val2))

        if shorter == 0:
            return False

        # Count common characters
        common = sum(1 for c1, c2 in zip(val1, val2) if c1 == c2)
        similarity = common / longer

        return similarity > 0.8

    def _calculate_confidence_scores(
        self, results: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate confidence scores for different data categories"""

        scores = {
            "identity_confidence": 0.0,
            "contact_confidence": 0.0,
            "business_confidence": 0.0,
            "address_confidence": 0.0,
            "overall_confidence": 0.0,
        }

        # Categorize results
        categories = {
            "identity": ["person_search_agent"],
            "contact": ["phone_search_agent", "email_search_agent"],
            "business": ["business_search_agent"],
            "address": ["address_search_agent"],
        }

        for category, agent_types in categories.items():
            relevant_results = [
                r
                for r in results
                if r.get("agent_type") in agent_types and r["success"]
            ]

            if relevant_results:
                avg_confidence = sum(
                    r.get("confidence", 0.5) for r in relevant_results
                ) / len(relevant_results)
                scores[f"{category}_confidence"] = avg_confidence

        # Calculate overall confidence
        confidence_values = [
            v for k, v in scores.items() if k != "overall_confidence" and v > 0
        ]
        scores["overall_confidence"] = (
            sum(confidence_values) / len(confidence_values)
            if confidence_values
            else 0.0
        )

        return scores

    def _assess_data_integrity(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess the integrity and reliability of collected data"""

        integrity = {
            "consistency_score": 0.0,
            "completeness_score": 0.0,
            "freshness_score": 0.0,
            "source_diversity_score": 0.0,
            "reliability_flags": [],
        }

        successful_results = [r for r in results if r["success"]]

        if not successful_results:
            return integrity

        # Consistency: How well do data points agree
        conflicts = 0
        comparisons = 0

        for i, result1 in enumerate(successful_results):
            for result2 in successful_results[i + 1 :]:
                common_fields = set(result1.get("data", {}).keys()) & set(
                    result2.get("data", {}).keys()
                )
                for field in common_fields:
                    comparisons += 1
                    val1 = result1["data"][field]
                    val2 = result2["data"][field]
                    if val1 and val2 and str(val1).lower() != str(val2).lower():
                        conflicts += 1

        integrity["consistency_score"] = (
            1.0 - (conflicts / comparisons) if comparisons > 0 else 1.0
        )

        # Completeness: How much expected data was found
        expected_fields = set(["name", "phone", "email", "address", "business"])
        found_fields = set()

        for result in successful_results:
            if result.get("data"):
                found_fields.update(result["data"].keys())

        integrity["completeness_score"] = len(found_fields & expected_fields) / len(
            expected_fields
        )

        # Source diversity: How many different sources were used
        sources = set()
        for result in successful_results:
            agent_type = result.get("agent_type")
            if agent_type:
                sources.add(agent_type)

        integrity["source_diversity_score"] = min(
            len(sources) / 5, 1.0
        )  # Normalize to max of 5 sources

        # Reliability flags
        if integrity["consistency_score"] < 0.7:
            integrity["reliability_flags"].append("low_consistency")

        if integrity["completeness_score"] < 0.5:
            integrity["reliability_flags"].append("low_completeness")

        if len(sources) < 2:
            integrity["reliability_flags"].append("limited_sources")

        return integrity

    async def _generate_comprehensive_report(
        self, accumulated_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""

        report = {
            "executive_summary": {},
            "investigation_timeline": [],
            "key_findings": [],
            "confidence_assessment": {},
            "recommendations": [],
            "data_quality_metrics": {},
            "cost_benefit_analysis": {},
        }

        # Executive summary
        total_cost = sum(
            stage.get("metadata", {}).get("total_cost", 0)
            for stage in accumulated_results["stages"]
        )
        total_time = sum(
            stage.get("metadata", {}).get("execution_time", 0)
            for stage in accumulated_results["stages"]
        )

        report["executive_summary"] = {
            "total_stages_executed": len(accumulated_results["stages"]),
            "total_investigation_cost": total_cost,
            "total_investigation_time_seconds": total_time,
            "overall_success_rate": self._calculate_overall_success_rate(
                accumulated_results
            ),
            "data_points_discovered": self._count_total_data_points(
                accumulated_results
            ),
            "high_confidence_findings": self._count_high_confidence_findings(
                accumulated_results
            ),
        }

        # Key findings extraction
        report["key_findings"] = self._extract_key_findings(accumulated_results)

        # Recommendations based on findings
        report["recommendations"] = self._generate_recommendations(accumulated_results)

        return report

    def _calculate_overall_success_rate(self, results: Dict[str, Any]) -> float:
        """Calculate overall success rate across all stages"""
        total_queries = 0
        successful_queries = 0

        for stage in results["stages"]:
            if "results" in stage and "summary" in stage["results"]:
                summary = stage["results"]["summary"]
                total_queries += summary.get("total_queries", 0)
                successful_queries += summary.get("successful_queries", 0)

        return successful_queries / total_queries if total_queries > 0 else 0.0

    def _count_total_data_points(self, results: Dict[str, Any]) -> int:
        """Count total unique data points across all stages"""
        unique_data_points = set()

        for stage in results["stages"]:
            if "results" in stage and "detailed_results" in stage["results"]:
                for result in stage["results"]["detailed_results"]:
                    if result["success"] and result["data"]:
                        for key, value in result["data"].items():
                            if value:
                                unique_data_points.add(f"{key}:{value}")

        return len(unique_data_points)

    def _count_high_confidence_findings(self, results: Dict[str, Any]) -> int:
        """Count findings with high confidence scores"""
        high_confidence_count = 0

        for stage in results["stages"]:
            if "results" in stage and "detailed_results" in stage["results"]:
                for result in stage["results"]["detailed_results"]:
                    confidence = result.get("confidence", 0.0)
                    if confidence > 0.8:
                        high_confidence_count += 1

        return high_confidence_count

    def _extract_key_findings(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract key findings from investigation results"""
        findings = []

        # Extract findings from each stage
        for stage in results["stages"]:
            if stage.get("stage_name") == "correlation_analysis":
                # Extract correlation findings
                if "advanced_correlations" in stage:
                    correlations = stage["advanced_correlations"]

                    for confirmation in correlations.get("identity_confirmations", []):
                        if confirmation["confidence"] > 0.7:
                            findings.append(
                                {
                                    "type": "identity_confirmation",
                                    "confidence": confirmation["confidence"],
                                    "description": f"Identity confirmed across {len(confirmation['confirmations'])} sources",
                                    "details": confirmation,
                                }
                            )

        return findings

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on investigation results"""
        recommendations = []

        overall_success = self._calculate_overall_success_rate(results)

        if overall_success < 0.5:
            recommendations.append(
                "Consider using additional data providers to improve success rate"
            )

        if len(results["stages"]) < 3:
            recommendations.append(
                "Consider additional investigation stages for more comprehensive results"
            )

        # Check for data quality issues
        correlation_stage = next(
            (
                stage
                for stage in results["stages"]
                if stage.get("stage_name") == "correlation_analysis"
            ),
            None,
        )

        if correlation_stage and "data_integrity" in correlation_stage:
            integrity = correlation_stage["data_integrity"]

            if integrity["consistency_score"] < 0.7:
                recommendations.append(
                    "Data consistency issues detected - verify conflicting information"
                )

            if integrity["completeness_score"] < 0.5:
                recommendations.append(
                    "Consider additional data sources to improve information completeness"
                )

        return recommendations


async def example_adaptive_fraud_investigation():
    """Example: Adaptive fraud investigation that modifies based on findings"""
    print("=== Adaptive Fraud Investigation Example ===\n")

    orchestrator = SleuthIntelOrchestrator()
    adaptive_manager = AdaptiveWorkflowManager(orchestrator)

    # Initial suspect data
    suspect_data = {
        "first_name": "John",
        "last_name": "Suspicious",
        "phone_number": "+1-555-FRAUD-01",
        "city": "Las Vegas",
        "state": "NV",
    }

    investigation_goals = [
        "verify_identity",
        "find_business_connections",
        "discover_assets",
        "check_criminal_history",
    ]

    budget = WorkflowBudget(max_cost_usd=25.00, max_time_minutes=30)

    print("Starting adaptive fraud investigation...")
    print(f"Initial data: {suspect_data}")
    print(f"Budget: ${budget.max_cost_usd:.2f}")

    try:
        results = await adaptive_manager.execute_adaptive_investigation(
            initial_data=suspect_data,
            investigation_goals=investigation_goals,
            budget=budget,
        )

        print(f"\nInvestigation completed!")
        print(f"Stages executed: {len(results['stages'])}")
        print(
            f"Total cost: ${results['final_analysis']['executive_summary']['total_investigation_cost']:.2f}"
        )
        print(
            f"Success rate: {results['final_analysis']['executive_summary']['overall_success_rate']:.1%}"
        )
        print(
            f"Data points discovered: {results['final_analysis']['executive_summary']['data_points_discovered']}"
        )

        # Print key findings
        key_findings = results["final_analysis"]["key_findings"]
        if key_findings:
            print(f"\nKey Findings:")
            for finding in key_findings:
                print(
                    f"  - {finding['description']} (Confidence: {finding['confidence']:.1%})"
                )

        # Print recommendations
        recommendations = results["final_analysis"]["recommendations"]
        if recommendations:
            print(f"\nRecommendations:")
            for rec in recommendations:
                print(f"  - {rec}")

        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"adaptive_fraud_investigation_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nDetailed results saved to: {filename}")

    except Exception as e:
        print(f"Investigation failed: {e}")


async def example_multi_target_investigation():
    """Example: Investigating multiple related targets simultaneously"""
    print("\n=== Multi-Target Investigation Example ===\n")

    # Network of related individuals/entities
    targets = [
        {
            "first_name": "Alice",
            "last_name": "Primary",
            "city": "New York",
            "state": "NY",
        },
        {
            "first_name": "Bob",
            "last_name": "Associate",
            "phone_number": "+1-555-123-4567",
        },
        {"company_name": "Suspicious Corp", "city": "Delaware", "state": "DE"},
        {"street_address": "123 Shell Company Ave", "city": "Offshore", "state": "DE"},
    ]

    orchestrator = SleuthIntelOrchestrator()
    manager = WorkflowTemplateManager(orchestrator)

    print(f"Investigating network of {len(targets)} related targets...")

    # Execute parallel investigations
    all_results = []

    for i, target in enumerate(targets):
        print(f"\nTarget {i+1}: {target}")

        # Determine workflow type
        if "company_name" in target:
            workflow_type = "business_due_diligence"
        elif "street_address" in target:
            workflow_type = "address_analysis"
        elif "phone_number" in target:
            workflow_type = "phone_investigation"
        else:
            workflow_type = "person_investigation"

        result = await manager.execute_workflow(
            template_type=workflow_type, depth="comprehensive", query_data=target
        )

        result["target_id"] = i
        result["target_data"] = target
        all_results.append(result)

        print(f"  Success rate: {result['metadata']['success_rate']:.1%}")
        print(f"  Cost: ${result['metadata']['total_cost']:.2f}")

    # Cross-reference results for network analysis
    network_analysis = await analyze_network_connections(all_results)

    print(f"\n=== Network Analysis ===")
    print(
        f"Total network cost: ${sum(r['metadata']['total_cost'] for r in all_results):.2f}"
    )
    print(f"Network connections found: {len(network_analysis['connections'])}")
    print(f"Correlation clusters: {len(network_analysis['clusters'])}")

    # Save network analysis
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"network_investigation_{timestamp}.json"
    with open(filename, "w") as f:
        json.dump(
            {"targets": all_results, "network_analysis": network_analysis},
            f,
            indent=2,
            default=str,
        )
    print(f"Network analysis saved to: {filename}")


async def analyze_network_connections(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze connections between investigation targets"""

    connections = []
    clusters = []

    # Find connections between results
    for i, result1 in enumerate(results):
        for j, result2 in enumerate(results[i + 1 :], i + 1):
            connection_strength = calculate_connection_strength(result1, result2)

            if connection_strength > 0.5:
                connections.append(
                    {
                        "target_1": i,
                        "target_2": j,
                        "strength": connection_strength,
                        "connection_type": determine_connection_type(result1, result2),
                    }
                )

    # Cluster highly connected targets
    if len(connections) > 2:
        clusters = identify_clusters(connections, len(results))

    return {
        "connections": connections,
        "clusters": clusters,
        "network_density": len(connections) / (len(results) * (len(results) - 1) / 2),
        "strongest_connection": max(connections, key=lambda x: x["strength"])
        if connections
        else None,
    }


def calculate_connection_strength(
    result1: Dict[str, Any], result2: Dict[str, Any]
) -> float:
    """Calculate connection strength between two investigation results"""

    # Extract all data from both results
    data1 = {}
    data2 = {}

    for detailed_result in result1["results"]["detailed_results"]:
        if detailed_result["success"] and detailed_result["data"]:
            data1.update(detailed_result["data"])

    for detailed_result in result2["results"]["detailed_results"]:
        if detailed_result["success"] and detailed_result["data"]:
            data2.update(detailed_result["data"])

    # Find common values
    common_values = 0
    total_values = 0

    for key1, value1 in data1.items():
        for key2, value2 in data2.items():
            total_values += 1
            if value1 and value2 and str(value1).lower() == str(value2).lower():
                common_values += 1

    return common_values / total_values if total_values > 0 else 0.0


def determine_connection_type(result1: Dict[str, Any], result2: Dict[str, Any]) -> str:
    """Determine the type of connection between two targets"""

    target1 = result1.get("target_data", {})
    target2 = result2.get("target_data", {})

    # Business connection
    if "company_name" in target1 or "company_name" in target2:
        return "business"

    # Address connection
    if "street_address" in target1 or "street_address" in target2:
        return "location"

    # Personal connection
    if "first_name" in target1 and "first_name" in target2:
        return "personal"

    return "unknown"


def identify_clusters(
    connections: List[Dict[str, Any]], num_targets: int
) -> List[List[int]]:
    """Identify clusters of highly connected targets"""

    # Simple clustering based on connection strength
    clusters = []
    used_targets = set()

    # Sort connections by strength
    sorted_connections = sorted(connections, key=lambda x: x["strength"], reverse=True)

    for connection in sorted_connections:
        target1 = connection["target_1"]
        target2 = connection["target_2"]

        if target1 not in used_targets and target2 not in used_targets:
            # Start new cluster
            clusters.append([target1, target2])
            used_targets.add(target1)
            used_targets.add(target2)
        elif target1 not in used_targets:
            # Add to existing cluster containing target2
            for cluster in clusters:
                if target2 in cluster:
                    cluster.append(target1)
                    used_targets.add(target1)
                    break
        elif target2 not in used_targets:
            # Add to existing cluster containing target1
            for cluster in clusters:
                if target1 in cluster:
                    cluster.append(target2)
                    used_targets.add(target2)
                    break

    return clusters


async def example_performance_optimization():
    """Example: Performance optimization strategies for large investigations"""
    print("\n=== Performance Optimization Example ===\n")

    # Simulate large dataset
    large_dataset = []
    for i in range(50):
        large_dataset.append(
            {
                "first_name": f"Person{i:02d}",
                "last_name": f"Subject{i:02d}",
                "city": ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"][
                    i % 5
                ],
                "state": ["NY", "CA", "IL", "TX", "AZ"][i % 5],
            }
        )

    orchestrator = SleuthIntelOrchestrator()
    manager = WorkflowTemplateManager(orchestrator)

    print(f"Optimizing processing for {len(large_dataset)} records...")

    # Strategy 1: Batch processing with cost optimization
    print("\nStrategy 1: Optimized Batch Processing")
    start_time = datetime.now()

    budget = WorkflowBudget(max_cost_usd=30.00, max_time_minutes=60)

    customization = WorkflowCustomization(
        custom_config={
            "max_parallel_agents": 15,  # High parallelization
            "enable_caching": True,
            "cache_ttl": 86400,  # Long cache for batch processing
            "cost_optimization": True,
        }
    )

    batch_result = await manager.execute_workflow(
        template_type="bulk_processing",
        depth="basic",
        query_data=large_dataset[:20],  # Process subset for demo
        budget=budget,
        customization=customization,
    )

    batch_time = (datetime.now() - start_time).total_seconds()

    print(f"  Processed: 20 records")
    print(f"  Time: {batch_time:.1f}s")
    print(f"  Cost: ${batch_result['metadata']['total_cost']:.2f}")
    print(f"  Cost per record: ${batch_result['metadata']['total_cost'] / 20:.3f}")
    print(f"  Success rate: {batch_result['metadata']['success_rate']:.1%}")

    # Strategy 2: Progressive depth investigation
    print("\nStrategy 2: Progressive Depth Investigation")
    progressive_results = []

    # Start with basic investigation on all
    basic_results = await manager.execute_workflow(
        template_type="person_investigation",
        depth="basic",
        query_data=large_dataset[:5],  # Small subset for demo
    )
    progressive_results.append(("basic", basic_results))

    # Identify high-value targets for deeper investigation
    high_value_targets = []
    for i, result in enumerate(basic_results["results"]["detailed_results"]):
        if result["success"] and result.get("confidence", 0) > 0.7:
            high_value_targets.append(large_dataset[i])

    if high_value_targets:
        deep_results = await manager.execute_workflow(
            template_type="person_investigation",
            depth="comprehensive",
            query_data=high_value_targets,
        )
        progressive_results.append(("comprehensive", deep_results))

    total_progressive_cost = sum(
        r[1]["metadata"]["total_cost"] for r in progressive_results
    )
    print(f"  Total progressive cost: ${total_progressive_cost:.2f}")
    print(f"  High-value targets identified: {len(high_value_targets)}")

    # Cost comparison
    print(f"\nCost Optimization Analysis:")
    basic_all_cost = len(large_dataset) * 1.00  # Estimated cost for all basic
    comprehensive_all_cost = (
        len(large_dataset) * 5.00
    )  # Estimated cost for all comprehensive

    print(f"  All Basic: ${basic_all_cost:.2f}")
    print(f"  All Comprehensive: ${comprehensive_all_cost:.2f}")
    print(
        f"  Progressive Strategy: ~${total_progressive_cost * (len(large_dataset) / 5):.2f}"
    )
    print(
        f"  Savings vs All Comprehensive: {(1 - (total_progressive_cost * (len(large_dataset) / 5)) / comprehensive_all_cost) * 100:.1f}%"
    )


if __name__ == "__main__":

    async def run_all_advanced_examples():
        await example_adaptive_fraud_investigation()
        await example_multi_target_investigation()
        await example_performance_optimization()

    asyncio.run(run_all_advanced_examples())
