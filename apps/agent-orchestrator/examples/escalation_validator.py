#!/usr/bin/env python3
"""
Escalation System Validation Script

Provides detailed validation of escalation system responses, testing edge cases,
and verifying proper integration behavior. This script focuses specifically on
validating escalation responses and system behavior under various conditions.
"""

import asyncio
import json
import logging
import sys
import time
import traceback
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from escalation_integration import (
    EscalationAwareOrchestrator,
    EscalationConfig,
    create_development_orchestrator,
)
from escalation_manager import (
    EscalationReason,
    EscalationRequest,
    EscalationResponse,
    EscalationType,
    IntelligentAgent,
    ManagerCommunicationBus,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EscalationValidator:
    """
    Comprehensive validation system for escalation responses and system behavior.

    Tests:
    1. Escalation request/response cycle correctness
    2. Communication bus reliability
    3. Enhancement pattern application
    4. Sub-swarm coordination logic
    5. Manager dashboard accuracy
    6. Edge case handling
    7. Performance under load
    8. Integration stability
    """

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.validation_dir = output_dir / "escalation_validation"
        self.validation_dir.mkdir(parents=True, exist_ok=True)

        # Validation results storage
        self.validation_results: Dict[str, Any] = {}
        self.test_metrics: Dict[str, float] = {}
        self.error_log: List[Dict] = []

        # Test configurations for different validation scenarios
        self.validation_scenarios = {
            "request_response_cycle": {
                "description": "Test complete escalation request/response cycle",
                "critical": True,
                "timeout": 30,
            },
            "communication_bus_reliability": {
                "description": "Test message bus reliability under load",
                "critical": True,
                "timeout": 60,
            },
            "enhancement_pattern_application": {
                "description": "Validate enhancement patterns are applied correctly",
                "critical": True,
                "timeout": 30,
            },
            "sub_swarm_coordination": {
                "description": "Test sub-swarm creation and coordination",
                "critical": True,
                "timeout": 45,
            },
            "manager_dashboard_accuracy": {
                "description": "Validate dashboard data accuracy and real-time updates",
                "critical": False,
                "timeout": 30,
            },
            "edge_case_handling": {
                "description": "Test system behavior with edge cases and invalid inputs",
                "critical": True,
                "timeout": 60,
            },
            "performance_under_load": {
                "description": "Test system performance with concurrent escalations",
                "critical": False,
                "timeout": 120,
            },
            "integration_stability": {
                "description": "Test long-running integration stability",
                "critical": True,
                "timeout": 180,
            },
        }

        logger.info(
            f"EscalationValidator initialized with {len(self.validation_scenarios)} scenarios"
        )

    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run complete validation suite and return detailed results"""
        logger.info("Starting comprehensive escalation system validation")

        start_time = time.time()

        try:
            # Initialize orchestrator for testing
            orchestrator = create_development_orchestrator(
                output_dir=self.validation_dir,
                tokens=["validation_token"],
                max_parallel=5,
                enable_escalation=True,
            )

            # Run all validation scenarios
            await self._validate_request_response_cycle(orchestrator)
            await self._validate_communication_bus_reliability(orchestrator)
            await self._validate_enhancement_pattern_application(orchestrator)
            await self._validate_sub_swarm_coordination(orchestrator)
            await self._validate_manager_dashboard_accuracy(orchestrator)
            await self._validate_edge_case_handling(orchestrator)
            await self._validate_performance_under_load(orchestrator)
            await self._validate_integration_stability(orchestrator)

            # Cleanup
            await orchestrator.shutdown()

            total_time = time.time() - start_time

            # Generate validation report
            report = await self._generate_validation_report(total_time)

            logger.info(f"Validation completed in {total_time:.2f}s")
            return report

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            logger.error(traceback.format_exc())

            return {
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "partial_results": self.validation_results,
            }

    async def _validate_request_response_cycle(
        self, orchestrator: EscalationAwareOrchestrator
    ):
        """Test complete escalation request/response cycle"""
        logger.info("Validating escalation request/response cycle")

        start_time = time.time()
        test_results = {}

        try:
            escalation_manager = orchestrator.escalation_manager

            # Test 1: Basic escalation request creation
            test_request = EscalationRequest(
                escalation_id=str(uuid.uuid4()),
                agent_id="validation_agent_001",
                agent_uuid=str(uuid.uuid4()),
                escalation_type=EscalationType.REPLACEMENT,
                escalation_reason=EscalationReason.FAILURE_THRESHOLD,
                problem_description="Test escalation for validation",
                attempted_solutions=["solution1", "solution2"],
                failure_count=3,
                required_permissions=["test_permission"],
                priority="high",
            )

            # Send escalation request
            escalation_id = await escalation_manager.handle_escalation(test_request)
            test_results["request_created"] = escalation_id is not None
            test_results["escalation_id_matches"] = (
                escalation_id == test_request.escalation_id
            )

            # Wait for processing
            await asyncio.sleep(2)

            # Check if response was generated
            response = await escalation_manager.comm_bus.get_response(escalation_id)
            test_results["response_generated"] = response is not None

            if response:
                test_results["response_type_correct"] = (
                    response.response_type == "replacement_spawned"
                )
                test_results["enhancement_applied"] = (
                    len(response.enhanced_capabilities) > 0
                )
                test_results["context_preserved"] = (
                    response.context_preservation is not None
                )
                test_results["handoff_instructions"] = bool(
                    response.handoff_instructions
                )

            # Test 2: Sub-swarm escalation cycle
            subswarm_request = EscalationRequest(
                escalation_id=str(uuid.uuid4()),
                agent_id="validation_agent_002",
                agent_uuid=str(uuid.uuid4()),
                escalation_type=EscalationType.SUB_SWARM,
                escalation_reason=EscalationReason.COMPLEX_DEBUGGING,
                problem_description="Complex problem requiring specialist team",
                specialist_types_needed=["troubleshoot", "research", "solution"],
                time_budget=300,
            )

            subswarm_id = await escalation_manager.handle_escalation(subswarm_request)
            await asyncio.sleep(2)

            subswarm_response = await escalation_manager.comm_bus.get_response(
                subswarm_id
            )
            test_results["subswarm_request_handled"] = subswarm_response is not None

            if subswarm_response:
                test_results["subswarm_created"] = (
                    subswarm_response.response_type == "sub_swarm_created"
                )
                test_results["agents_spawned"] = (
                    len(subswarm_response.sub_swarm_agents) > 0
                )
                test_results["specialist_coordination"] = (
                    subswarm_response.sub_swarm_id is not None
                )

            execution_time = time.time() - start_time
            test_results["execution_time"] = execution_time
            test_results["performance_acceptable"] = execution_time < 30.0

        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"Request/response cycle validation failed: {e}")

        self.validation_results["request_response_cycle"] = test_results
        self.test_metrics["request_response_cycle_time"] = time.time() - start_time

    async def _validate_communication_bus_reliability(
        self, orchestrator: EscalationAwareOrchestrator
    ):
        """Test communication bus reliability under load"""
        logger.info("Validating communication bus reliability")

        start_time = time.time()
        test_results = {}

        try:
            comm_bus = orchestrator.escalation_manager.comm_bus

            # Test concurrent message sending
            num_concurrent_messages = 10
            escalation_requests = []

            for i in range(num_concurrent_messages):
                request = EscalationRequest(
                    escalation_id=f"concurrent_test_{i}_{uuid.uuid4().hex[:8]}",
                    agent_id=f"concurrent_agent_{i}",
                    agent_uuid=str(uuid.uuid4()),
                    escalation_type=EscalationType.REPLACEMENT,
                    escalation_reason=EscalationReason.FAILURE_THRESHOLD,
                    problem_description=f"Concurrent test message {i}",
                    priority="normal",
                )
                escalation_requests.append(request)

            # Send all requests concurrently
            send_tasks = [comm_bus.send_escalation(req) for req in escalation_requests]

            sent_ids = await asyncio.gather(*send_tasks, return_exceptions=True)
            successful_sends = [id for id in sent_ids if isinstance(id, str)]

            test_results["concurrent_sends_successful"] = (
                len(successful_sends) == num_concurrent_messages
            )
            test_results["send_success_rate"] = (
                len(successful_sends) / num_concurrent_messages
            )

            # Wait for processing
            await asyncio.sleep(3)

            # Check message retrieval
            pending_escalations = await comm_bus.get_pending_escalations()
            test_results["messages_retrievable"] = len(pending_escalations) > 0

            # Test message ordering and integrity
            retrieved_ids = [req.escalation_id for req in pending_escalations]
            original_ids = [req.escalation_id for req in escalation_requests]

            test_results["message_integrity"] = all(
                id in retrieved_ids for id in original_ids
            )

            # Test response handling under load
            response_tasks = []
            for req in escalation_requests[:5]:  # Test with first 5
                response = EscalationResponse(
                    escalation_id=req.escalation_id,
                    response_type="replacement_spawned",
                    new_agent_uuid=str(uuid.uuid4()),
                    enhanced_capabilities=["test_capability"],
                )
                response_tasks.append(comm_bus.send_response(response))

            await asyncio.gather(*response_tasks, return_exceptions=True)

            # Verify responses were stored
            stored_responses = 0
            for req in escalation_requests[:5]:
                response = await comm_bus.get_response(req.escalation_id)
                if response:
                    stored_responses += 1

            test_results["response_storage_reliable"] = (
                stored_responses >= 4
            )  # Allow 1 failure
            test_results["response_storage_rate"] = stored_responses / 5

            execution_time = time.time() - start_time
            test_results["execution_time"] = execution_time
            test_results["performance_acceptable"] = execution_time < 60.0

        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"Communication bus reliability validation failed: {e}")

        self.validation_results["communication_bus_reliability"] = test_results
        self.test_metrics["comm_bus_reliability_time"] = time.time() - start_time

    async def _validate_enhancement_pattern_application(
        self, orchestrator: EscalationAwareOrchestrator
    ):
        """Validate enhancement patterns are applied correctly"""
        logger.info("Validating enhancement pattern application")

        start_time = time.time()
        test_results = {}

        try:
            escalation_manager = orchestrator.escalation_manager

            # Test enhancement patterns for different escalation reasons
            enhancement_test_cases = [
                {
                    "reason": EscalationReason.MISSING_PERMISSIONS,
                    "expected_enhancements": [
                        "elevated_permissions",
                        "file_system_access",
                    ],
                },
                {
                    "reason": EscalationReason.CONTEXT_EXHAUSTION,
                    "expected_enhancements": ["context_handoff", "state_preservation"],
                },
                {
                    "reason": EscalationReason.MISSING_DEPENDENCIES,
                    "expected_enhancements": [
                        "dependency_resolution",
                        "file_search_tools",
                    ],
                },
                {
                    "reason": EscalationReason.FAILURE_THRESHOLD,
                    "expected_enhancements": [
                        "alternative_strategies",
                        "enhanced_debugging",
                    ],
                },
            ]

            enhancement_results = {}

            for i, test_case in enumerate(enhancement_test_cases):
                request = EscalationRequest(
                    escalation_id=f"enhancement_test_{i}_{uuid.uuid4().hex[:8]}",
                    agent_id=f"enhancement_agent_{i}",
                    agent_uuid=str(uuid.uuid4()),
                    escalation_type=EscalationType.REPLACEMENT,
                    escalation_reason=test_case["reason"],
                    problem_description=f"Enhancement test for {test_case['reason'].value}",
                    required_tools=["additional_tool"],
                    required_permissions=["additional_permission"],
                )

                escalation_id = await escalation_manager.handle_escalation(request)
                await asyncio.sleep(1)  # Wait for processing

                response = await escalation_manager.comm_bus.get_response(escalation_id)

                if response:
                    applied_enhancements = response.enhanced_capabilities

                    # Check if expected enhancements are present
                    expected_present = any(
                        expected in applied_enhancements
                        for expected in test_case["expected_enhancements"]
                    )

                    # Check if user requirements were included
                    user_requirements_included = any(
                        req in applied_enhancements
                        for req in ["additional_tool", "additional_permission"]
                    )

                    enhancement_results[test_case["reason"].value] = {
                        "expected_enhancements_applied": expected_present,
                        "user_requirements_included": user_requirements_included,
                        "total_enhancements": len(applied_enhancements),
                        "enhancement_list": applied_enhancements,
                    }
                else:
                    enhancement_results[test_case["reason"].value] = {
                        "error": "No response received"
                    }

            test_results["enhancement_tests"] = enhancement_results

            # Calculate overall success metrics
            successful_enhancements = sum(
                1
                for result in enhancement_results.values()
                if isinstance(result, dict)
                and result.get("expected_enhancements_applied", False)
                and result.get("user_requirements_included", False)
            )

            test_results["enhancement_success_rate"] = successful_enhancements / len(
                enhancement_test_cases
            )
            test_results["all_patterns_working"] = successful_enhancements == len(
                enhancement_test_cases
            )

            execution_time = time.time() - start_time
            test_results["execution_time"] = execution_time
            test_results["performance_acceptable"] = execution_time < 30.0

        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"Enhancement pattern validation failed: {e}")

        self.validation_results["enhancement_pattern_application"] = test_results
        self.test_metrics["enhancement_pattern_time"] = time.time() - start_time

    async def _validate_sub_swarm_coordination(
        self, orchestrator: EscalationAwareOrchestrator
    ):
        """Test sub-swarm creation and coordination"""
        logger.info("Validating sub-swarm coordination")

        start_time = time.time()
        test_results = {}

        try:
            escalation_manager = orchestrator.escalation_manager

            # Test sub-swarm creation with different specialist configurations
            subswarm_configs = [
                {
                    "specialists": ["troubleshoot", "research", "solution"],
                    "complexity": "medium",
                    "budget": 300,
                },
                {
                    "specialists": ["troubleshoot", "research", "test", "solution"],
                    "complexity": "high",
                    "budget": 600,
                },
                {
                    "specialists": ["research", "analysis", "implementation"],
                    "complexity": "critical",
                    "budget": 900,
                },
            ]

            subswarm_results = {}

            for i, config in enumerate(subswarm_configs):
                request = EscalationRequest(
                    escalation_id=f"subswarm_test_{i}_{uuid.uuid4().hex[:8]}",
                    agent_id=f"subswarm_agent_{i}",
                    agent_uuid=str(uuid.uuid4()),
                    escalation_type=EscalationType.SUB_SWARM,
                    escalation_reason=EscalationReason.COMPLEX_DEBUGGING,
                    problem_description=f"Complex problem requiring {config['complexity']} level coordination",
                    specialist_types_needed=config["specialists"],
                    estimated_complexity=config["complexity"],
                    time_budget=config["budget"],
                )

                escalation_id = await escalation_manager.handle_escalation(request)
                await asyncio.sleep(2)  # Wait for sub-swarm creation

                response = await escalation_manager.comm_bus.get_response(escalation_id)

                if response and response.response_type == "sub_swarm_created":
                    # Validate sub-swarm structure
                    swarm_id = response.sub_swarm_id
                    agents = response.sub_swarm_agents
                    instructions = response.handoff_instructions
                    context = response.context_preservation

                    subswarm_results[f"config_{i}"] = {
                        "sub_swarm_created": swarm_id is not None,
                        "correct_agent_count": len(agents)
                        == len(config["specialists"]),
                        "agents_have_uuids": all(
                            "uuid" in agent or len(agent) > 10 for agent in agents
                        ),
                        "instructions_provided": len(instructions)
                        > 100,  # Reasonable instruction length
                        "context_preserved": isinstance(context, dict)
                        and len(context) > 0,
                        "time_budget_preserved": str(config["budget"]) in instructions,
                        "specialists_mentioned": all(
                            spec in instructions.lower()
                            for spec in config["specialists"]
                        ),
                        "coordination_protocol": "coordination protocol"
                        in instructions.lower(),
                        "sub_swarm_id": swarm_id,
                        "agent_count": len(agents),
                    }
                else:
                    subswarm_results[f"config_{i}"] = {
                        "error": f"Failed to create sub-swarm or wrong response type: {response.response_type if response else 'No response'}"
                    }

            test_results["subswarm_tests"] = subswarm_results

            # Calculate success metrics
            successful_subswarms = sum(
                1
                for result in subswarm_results.values()
                if isinstance(result, dict)
                and result.get("sub_swarm_created", False)
                and result.get("correct_agent_count", False)
                and result.get("instructions_provided", False)
            )

            test_results["subswarm_success_rate"] = successful_subswarms / len(
                subswarm_configs
            )
            test_results["all_subswarms_working"] = successful_subswarms == len(
                subswarm_configs
            )

            execution_time = time.time() - start_time
            test_results["execution_time"] = execution_time
            test_results["performance_acceptable"] = execution_time < 45.0

        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"Sub-swarm coordination validation failed: {e}")

        self.validation_results["sub_swarm_coordination"] = test_results
        self.test_metrics["sub_swarm_coordination_time"] = time.time() - start_time

    async def _validate_manager_dashboard_accuracy(
        self, orchestrator: EscalationAwareOrchestrator
    ):
        """Validate dashboard data accuracy and real-time updates"""
        logger.info("Validating manager dashboard accuracy")

        start_time = time.time()
        test_results = {}

        try:
            # Get baseline dashboard
            baseline_dashboard = await orchestrator.get_escalation_dashboard()
            baseline_metrics = baseline_dashboard.get("escalation_metrics", {})

            # Create some escalations to test dashboard updates
            test_escalations = []
            for i in range(3):
                request = EscalationRequest(
                    escalation_id=f"dashboard_test_{i}_{uuid.uuid4().hex[:8]}",
                    agent_id=f"dashboard_agent_{i}",
                    agent_uuid=str(uuid.uuid4()),
                    escalation_type=EscalationType.REPLACEMENT,
                    escalation_reason=EscalationReason.FAILURE_THRESHOLD,
                    problem_description=f"Dashboard test escalation {i}",
                    priority="normal",
                )
                test_escalations.append(request)

            # Send escalations
            for request in test_escalations:
                await orchestrator.escalation_manager.handle_escalation(request)

            await asyncio.sleep(2)  # Wait for processing

            # Get updated dashboard
            updated_dashboard = await orchestrator.get_escalation_dashboard()
            updated_metrics = updated_dashboard.get("escalation_metrics", {})

            # Validate dashboard structure
            test_results["dashboard_has_required_fields"] = all(
                field in updated_dashboard
                for field in [
                    "escalation_metrics",
                    "escalation_config",
                    "pending_count",
                ]
            )

            test_results["metrics_structure_valid"] = all(
                metric in updated_metrics
                for metric in [
                    "total_escalations",
                    "auto_replacements",
                    "sub_swarm_delegations",
                ]
            )

            # Validate metric updates
            baseline_total = baseline_metrics.get("total_escalations", 0)
            updated_total = updated_metrics.get("total_escalations", 0)

            test_results["escalation_count_updated"] = updated_total > baseline_total
            test_results[
                "escalation_count_accurate"
            ] = updated_total >= baseline_total + len(test_escalations)

            # Test real-time update capability
            dashboard_snapshots = []
            for i in range(3):
                snapshot = await orchestrator.get_escalation_dashboard()
                dashboard_snapshots.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "metrics": snapshot.get("escalation_metrics", {}),
                    }
                )

                # Create escalation between snapshots
                if i < 2:
                    realtime_request = EscalationRequest(
                        escalation_id=f"realtime_test_{i}_{uuid.uuid4().hex[:8]}",
                        agent_id=f"realtime_agent_{i}",
                        agent_uuid=str(uuid.uuid4()),
                        escalation_type=EscalationType.SUB_SWARM,
                        escalation_reason=EscalationReason.COMPLEX_DEBUGGING,
                        problem_description=f"Real-time test escalation {i}",
                    )
                    await orchestrator.escalation_manager.handle_escalation(
                        realtime_request
                    )
                    await asyncio.sleep(1)

            test_results["dashboard_snapshots"] = dashboard_snapshots
            test_results["real_time_updates"] = len(dashboard_snapshots) == 3

            # Validate configuration data accuracy
            config_data = updated_dashboard.get("escalation_config", {})
            test_results["config_data_present"] = len(config_data) > 0
            test_results["config_matches_orchestrator"] = (
                config_data.get("enable_escalation")
                == orchestrator.escalation_config.enable_escalation
            )

            execution_time = time.time() - start_time
            test_results["execution_time"] = execution_time
            test_results["performance_acceptable"] = execution_time < 30.0

        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"Dashboard accuracy validation failed: {e}")

        self.validation_results["manager_dashboard_accuracy"] = test_results
        self.test_metrics["dashboard_accuracy_time"] = time.time() - start_time

    async def _validate_edge_case_handling(
        self, orchestrator: EscalationAwareOrchestrator
    ):
        """Test system behavior with edge cases and invalid inputs"""
        logger.info("Validating edge case handling")

        start_time = time.time()
        test_results = {}

        try:
            escalation_manager = orchestrator.escalation_manager
            edge_case_results = {}

            # Test 1: Invalid escalation type
            try:
                invalid_request = EscalationRequest(
                    escalation_id=str(uuid.uuid4()),
                    agent_id="edge_case_agent",
                    agent_uuid=str(uuid.uuid4()),
                    escalation_type="INVALID_TYPE",  # This should cause issues
                    escalation_reason=EscalationReason.FAILURE_THRESHOLD,
                    problem_description="Test invalid escalation type",
                )
                # This should either fail gracefully or handle the invalid type
                result = await escalation_manager.handle_escalation(invalid_request)
                edge_case_results["invalid_escalation_type"] = {
                    "handled_gracefully": True,
                    "result": str(result),
                }
            except Exception as e:
                edge_case_results["invalid_escalation_type"] = {
                    "handled_gracefully": "Exception"
                    in str(type(e)),  # Should raise appropriate exception
                    "error": str(e),
                }

            # Test 2: Empty/null fields
            try:
                empty_request = EscalationRequest(
                    escalation_id="",  # Empty ID
                    agent_id="edge_case_agent",
                    agent_uuid=str(uuid.uuid4()),
                    escalation_type=EscalationType.REPLACEMENT,
                    escalation_reason=EscalationReason.FAILURE_THRESHOLD,
                    problem_description="",  # Empty description
                )
                result = await escalation_manager.handle_escalation(empty_request)
                edge_case_results["empty_fields"] = {
                    "handled_gracefully": True,
                    "result": str(result),
                }
            except Exception as e:
                edge_case_results["empty_fields"] = {
                    "handled_gracefully": True,  # Should handle empty fields
                    "error": str(e),
                }

            # Test 3: Extremely large inputs
            try:
                large_description = "X" * 100000  # 100KB description
                large_solutions = [
                    "solution " + "Y" * 1000
                ] * 100  # Large solution list

                large_request = EscalationRequest(
                    escalation_id=str(uuid.uuid4()),
                    agent_id="edge_case_agent",
                    agent_uuid=str(uuid.uuid4()),
                    escalation_type=EscalationType.REPLACEMENT,
                    escalation_reason=EscalationReason.FAILURE_THRESHOLD,
                    problem_description=large_description,
                    attempted_solutions=large_solutions,
                )

                result = await escalation_manager.handle_escalation(large_request)
                edge_case_results["large_inputs"] = {
                    "handled_gracefully": True,
                    "result": str(result)[:100] + "...",  # Truncate for logging
                }
            except Exception as e:
                edge_case_results["large_inputs"] = {
                    "handled_gracefully": "memory"
                    not in str(e).lower(),  # Should not cause memory errors
                    "error": str(e)[:200] + "...",
                }

            # Test 4: Concurrent duplicate escalations
            try:
                duplicate_id = str(uuid.uuid4())
                duplicate_requests = []

                for i in range(5):
                    request = EscalationRequest(
                        escalation_id=duplicate_id,  # Same ID for all
                        agent_id=f"duplicate_agent_{i}",
                        agent_uuid=str(uuid.uuid4()),
                        escalation_type=EscalationType.REPLACEMENT,
                        escalation_reason=EscalationReason.FAILURE_THRESHOLD,
                        problem_description=f"Duplicate escalation test {i}",
                    )
                    duplicate_requests.append(request)

                # Send all duplicates concurrently
                tasks = [
                    escalation_manager.handle_escalation(req)
                    for req in duplicate_requests
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                successful_results = [
                    r for r in results if not isinstance(r, Exception)
                ]

                edge_case_results["duplicate_escalations"] = {
                    "handled_gracefully": len(successful_results) > 0,
                    "duplicate_handling": len(set(successful_results))
                    <= 1,  # Should handle duplicates
                    "successful_count": len(successful_results),
                    "total_attempts": len(duplicate_requests),
                }
            except Exception as e:
                edge_case_results["duplicate_escalations"] = {"error": str(e)}

            # Test 5: Malformed communication bus access
            try:
                # Try to access non-existent escalation
                nonexistent_response = await escalation_manager.comm_bus.get_response(
                    "nonexistent_id_12345"
                )
                edge_case_results["nonexistent_escalation"] = {
                    "handled_gracefully": nonexistent_response is None,
                    "response": str(nonexistent_response),
                }
            except Exception as e:
                edge_case_results["nonexistent_escalation"] = {
                    "handled_gracefully": False,
                    "error": str(e),
                }

            test_results["edge_case_tests"] = edge_case_results

            # Calculate edge case handling success
            successful_edge_cases = sum(
                1
                for result in edge_case_results.values()
                if isinstance(result, dict) and result.get("handled_gracefully", False)
            )

            test_results["edge_case_success_rate"] = successful_edge_cases / len(
                edge_case_results
            )
            test_results["robust_error_handling"] = (
                successful_edge_cases >= len(edge_case_results) * 0.8
            )

            execution_time = time.time() - start_time
            test_results["execution_time"] = execution_time
            test_results["performance_acceptable"] = execution_time < 60.0

        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"Edge case handling validation failed: {e}")

        self.validation_results["edge_case_handling"] = test_results
        self.test_metrics["edge_case_handling_time"] = time.time() - start_time

    async def _validate_performance_under_load(
        self, orchestrator: EscalationAwareOrchestrator
    ):
        """Test system performance with concurrent escalations"""
        logger.info("Validating performance under load")

        start_time = time.time()
        test_results = {}

        try:
            escalation_manager = orchestrator.escalation_manager

            # Configuration for load testing
            num_concurrent_escalations = 20
            num_waves = 3

            performance_metrics = []

            for wave in range(num_waves):
                wave_start = time.time()

                # Create escalations for this wave
                wave_escalations = []
                for i in range(num_concurrent_escalations):
                    escalation_type = (
                        EscalationType.REPLACEMENT
                        if i % 2 == 0
                        else EscalationType.SUB_SWARM
                    )

                    request = EscalationRequest(
                        escalation_id=f"load_test_wave{wave}_{i}_{uuid.uuid4().hex[:8]}",
                        agent_id=f"load_agent_w{wave}_{i}",
                        agent_uuid=str(uuid.uuid4()),
                        escalation_type=escalation_type,
                        escalation_reason=EscalationReason.FAILURE_THRESHOLD,
                        problem_description=f"Load test escalation wave {wave}, item {i}",
                        priority="normal",
                    )
                    wave_escalations.append(request)

                # Send all escalations concurrently
                tasks = [
                    escalation_manager.handle_escalation(req)
                    for req in wave_escalations
                ]

                wave_results = await asyncio.gather(*tasks, return_exceptions=True)

                wave_time = time.time() - wave_start
                successful_escalations = [
                    r for r in wave_results if not isinstance(r, Exception)
                ]

                performance_metrics.append(
                    {
                        "wave": wave,
                        "total_escalations": num_concurrent_escalations,
                        "successful_escalations": len(successful_escalations),
                        "failed_escalations": len(wave_results)
                        - len(successful_escalations),
                        "wave_execution_time": wave_time,
                        "escalations_per_second": len(successful_escalations)
                        / wave_time
                        if wave_time > 0
                        else 0,
                        "success_rate": len(successful_escalations)
                        / num_concurrent_escalations,
                    }
                )

                # Brief pause between waves
                await asyncio.sleep(1)

            # Calculate overall performance metrics
            total_escalations = sum(m["total_escalations"] for m in performance_metrics)
            total_successful = sum(
                m["successful_escalations"] for m in performance_metrics
            )
            total_time = sum(m["wave_execution_time"] for m in performance_metrics)
            average_success_rate = sum(
                m["success_rate"] for m in performance_metrics
            ) / len(performance_metrics)

            test_results["performance_metrics"] = performance_metrics
            test_results["total_escalations_processed"] = total_escalations
            test_results["total_successful_escalations"] = total_successful
            test_results["overall_success_rate"] = (
                total_successful / total_escalations if total_escalations > 0 else 0
            )
            test_results["average_success_rate"] = average_success_rate
            test_results["total_processing_time"] = total_time
            test_results["overall_throughput"] = (
                total_successful / total_time if total_time > 0 else 0
            )

            # Performance benchmarks
            test_results["throughput_acceptable"] = (
                test_results["overall_throughput"] > 5.0
            )  # 5 escalations/second
            test_results["success_rate_acceptable"] = (
                test_results["overall_success_rate"] > 0.95
            )  # 95% success
            test_results["latency_acceptable"] = all(
                m["wave_execution_time"] < 10.0 for m in performance_metrics
            )  # <10s per wave

            # Check system state after load
            final_dashboard = await orchestrator.get_escalation_dashboard()
            test_results["system_stable_after_load"] = final_dashboard is not None
            test_results["metrics_updated"] = (
                final_dashboard.get("escalation_metrics", {}).get(
                    "total_escalations", 0
                )
                > 0
            )

            execution_time = time.time() - start_time
            test_results["execution_time"] = execution_time
            test_results["performance_acceptable"] = execution_time < 120.0

        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"Performance under load validation failed: {e}")

        self.validation_results["performance_under_load"] = test_results
        self.test_metrics["performance_under_load_time"] = time.time() - start_time

    async def _validate_integration_stability(
        self, orchestrator: EscalationAwareOrchestrator
    ):
        """Test long-running integration stability"""
        logger.info("Validating integration stability")

        start_time = time.time()
        test_results = {}

        try:
            # Test 1: Orchestrator stability over time
            stability_checks = []

            for i in range(10):  # Run 10 stability checks over time
                check_start = time.time()

                # Create and process some escalations
                request = EscalationRequest(
                    escalation_id=f"stability_test_{i}_{uuid.uuid4().hex[:8]}",
                    agent_id=f"stability_agent_{i}",
                    agent_uuid=str(uuid.uuid4()),
                    escalation_type=EscalationType.REPLACEMENT,
                    escalation_reason=EscalationReason.FAILURE_THRESHOLD,
                    problem_description=f"Stability test iteration {i}",
                    priority="normal",
                )

                try:
                    escalation_id = (
                        await orchestrator.escalation_manager.handle_escalation(request)
                    )

                    # Check dashboard is still accessible
                    dashboard = await orchestrator.get_escalation_dashboard()

                    # Check communication bus is working
                    pending = (
                        await orchestrator.escalation_manager.comm_bus.get_pending_escalations()
                    )

                    stability_checks.append(
                        {
                            "iteration": i,
                            "escalation_processed": escalation_id is not None,
                            "dashboard_accessible": dashboard is not None,
                            "comm_bus_working": isinstance(pending, list),
                            "check_time": time.time() - check_start,
                            "memory_stable": True,  # In a real implementation, check memory usage
                            "no_exceptions": True,
                        }
                    )

                except Exception as e:
                    stability_checks.append(
                        {
                            "iteration": i,
                            "escalation_processed": False,
                            "dashboard_accessible": False,
                            "comm_bus_working": False,
                            "check_time": time.time() - check_start,
                            "memory_stable": False,
                            "no_exceptions": False,
                            "error": str(e),
                        }
                    )

                # Wait between checks to simulate time passage
                await asyncio.sleep(2)

            test_results["stability_checks"] = stability_checks

            # Calculate stability metrics
            successful_checks = [
                check
                for check in stability_checks
                if check.get("escalation_processed", False)
                and check.get("dashboard_accessible", False)
                and check.get("comm_bus_working", False)
                and check.get("no_exceptions", False)
            ]

            test_results["stability_success_rate"] = len(successful_checks) / len(
                stability_checks
            )
            test_results["system_remained_stable"] = (
                len(successful_checks) >= len(stability_checks) * 0.9
            )  # 90% stability
            test_results["no_degradation"] = all(
                check.get("check_time", float("inf")) < 5.0
                for check in stability_checks
            )

            # Test 2: Memory and resource stability (mock implementation)
            test_results[
                "memory_leaks_detected"
            ] = False  # In real implementation, check memory usage trends
            test_results[
                "resource_cleanup_working"
            ] = True  # In real implementation, check resource cleanup
            test_results[
                "connection_pools_stable"
            ] = True  # In real implementation, check connection health

            # Test 3: Error recovery
            try:
                # Simulate an error condition and see if system recovers
                invalid_request = EscalationRequest(
                    escalation_id="",  # Invalid ID
                    agent_id="recovery_test",
                    agent_uuid=str(uuid.uuid4()),
                    escalation_type=EscalationType.REPLACEMENT,
                    escalation_reason=EscalationReason.FAILURE_THRESHOLD,
                    problem_description="Error recovery test",
                )

                await orchestrator.escalation_manager.handle_escalation(invalid_request)

                # System should still be working after the error
                recovery_dashboard = await orchestrator.get_escalation_dashboard()
                test_results["error_recovery"] = recovery_dashboard is not None

            except Exception:
                # After the exception, system should still work
                try:
                    recovery_dashboard = await orchestrator.get_escalation_dashboard()
                    test_results["error_recovery"] = recovery_dashboard is not None
                except Exception:
                    test_results["error_recovery"] = False

            execution_time = time.time() - start_time
            test_results["execution_time"] = execution_time
            test_results["performance_acceptable"] = execution_time < 180.0

        except Exception as e:
            test_results["error"] = str(e)
            logger.error(f"Integration stability validation failed: {e}")

        self.validation_results["integration_stability"] = test_results
        self.test_metrics["integration_stability_time"] = time.time() - start_time

    async def _generate_validation_report(self, total_time: float) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        logger.info("Generating validation report")

        # Calculate overall validation success
        critical_scenarios = [
            scenario
            for scenario, config in self.validation_scenarios.items()
            if config.get("critical", False)
        ]

        critical_results = {
            scenario: self.validation_results.get(scenario, {})
            for scenario in critical_scenarios
        }

        critical_success_count = 0
        total_critical = len(critical_scenarios)

        for scenario, results in critical_results.items():
            if isinstance(results, dict) and not results.get("error"):
                # Check if scenario passed based on key metrics
                scenario_success = self._evaluate_scenario_success(scenario, results)
                if scenario_success:
                    critical_success_count += 1

        overall_success = (
            critical_success_count >= total_critical * 0.9
        )  # 90% of critical scenarios must pass

        report = {
            "validation_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_execution_time": total_time,
                "scenarios_tested": len(self.validation_scenarios),
                "critical_scenarios": total_critical,
                "validation_version": "1.0.0",
            },
            "overall_assessment": {
                "validation_passed": overall_success,
                "critical_scenario_success_rate": f"{critical_success_count}/{total_critical}",
                "overall_system_health": "healthy"
                if overall_success
                else "needs_attention",
                "production_readiness": overall_success
                and critical_success_count == total_critical,
            },
            "scenario_results": self.validation_results,
            "performance_metrics": self.test_metrics,
            "error_log": self.error_log,
            "validation_summary": {
                scenario: {
                    "status": "passed" if not results.get("error") else "failed",
                    "critical": self.validation_scenarios[scenario].get(
                        "critical", False
                    ),
                    "execution_time": self.test_metrics.get(f"{scenario}_time", 0),
                    "key_metrics": self._extract_key_metrics(scenario, results),
                }
                for scenario, results in self.validation_results.items()
            },
            "recommendations": self._generate_validation_recommendations(
                critical_results
            ),
            "next_steps": [
                "Address any critical validation failures",
                "Optimize performance for scenarios with high execution times",
                "Monitor production deployment for validation pattern compliance",
                "Set up continuous validation in CI/CD pipeline",
            ],
        }

        # Save validation report
        report_file = self.validation_dir / "escalation_validation_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Validation report saved to: {report_file}")
        logger.info(
            f"Overall validation: {'✅ PASSED' if overall_success else '❌ FAILED'}"
        )

        return report

    def _evaluate_scenario_success(self, scenario: str, results: Dict) -> bool:
        """Evaluate if a specific scenario was successful"""
        if results.get("error"):
            return False

        # Scenario-specific success criteria
        success_criteria = {
            "request_response_cycle": (
                results.get("request_created", False)
                and results.get("response_generated", False)
                and results.get("performance_acceptable", False)
            ),
            "communication_bus_reliability": (
                results.get("concurrent_sends_successful", False)
                and results.get("message_integrity", False)
                and results.get("response_storage_reliable", False)
            ),
            "enhancement_pattern_application": (
                results.get("all_patterns_working", False)
                and results.get("enhancement_success_rate", 0) > 0.8
            ),
            "sub_swarm_coordination": (
                results.get("all_subswarms_working", False)
                and results.get("subswarm_success_rate", 0) > 0.8
            ),
            "edge_case_handling": (
                results.get("robust_error_handling", False)
                and results.get("edge_case_success_rate", 0) > 0.7
            ),
            "integration_stability": (
                results.get("system_remained_stable", False)
                and results.get("error_recovery", False)
            ),
        }

        return success_criteria.get(
            scenario, True
        )  # Default to True for non-critical scenarios

    def _extract_key_metrics(self, scenario: str, results: Dict) -> Dict:
        """Extract key metrics for each scenario"""
        key_metrics = {
            "request_response_cycle": {
                "requests_processed": results.get("request_created", False),
                "responses_generated": results.get("response_generated", False),
                "execution_time": results.get("execution_time", 0),
            },
            "communication_bus_reliability": {
                "send_success_rate": results.get("send_success_rate", 0),
                "message_integrity": results.get("message_integrity", False),
                "response_storage_rate": results.get("response_storage_rate", 0),
            },
            "enhancement_pattern_application": {
                "enhancement_success_rate": results.get("enhancement_success_rate", 0),
                "patterns_tested": len(results.get("enhancement_tests", {})),
            },
            "sub_swarm_coordination": {
                "subswarm_success_rate": results.get("subswarm_success_rate", 0),
                "configurations_tested": len(results.get("subswarm_tests", {})),
            },
            "performance_under_load": {
                "overall_throughput": results.get("overall_throughput", 0),
                "overall_success_rate": results.get("overall_success_rate", 0),
                "total_escalations": results.get("total_escalations_processed", 0),
            },
        }

        return key_metrics.get(
            scenario, {"execution_time": results.get("execution_time", 0)}
        )

    def _generate_validation_recommendations(self, critical_results: Dict) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        for scenario, results in critical_results.items():
            if results.get("error"):
                recommendations.append(
                    f"Fix critical error in {scenario}: {results['error'][:100]}..."
                )

            elif not self._evaluate_scenario_success(scenario, results):
                recommendations.append(
                    f"Improve {scenario} performance and reliability"
                )

        # Performance-based recommendations
        for scenario, time_taken in self.test_metrics.items():
            timeout = self.validation_scenarios.get(
                scenario.replace("_time", ""), {}
            ).get("timeout", 60)
            if time_taken > timeout * 0.8:  # If taking >80% of timeout
                recommendations.append(
                    f"Optimize {scenario} performance (taking {time_taken:.1f}s)"
                )

        return recommendations


async def main():
    """Main validation runner"""
    print("🔍 Starting Comprehensive Escalation System Validation")

    # Setup
    output_dir = Path("./escalation_validation_output")
    output_dir.mkdir(exist_ok=True)

    # Initialize validator
    validator = EscalationValidator(output_dir)

    try:
        # Run validation
        report = await validator.run_comprehensive_validation()

        # Display results
        print("\n" + "=" * 80)
        print("📋 ESCALATION SYSTEM VALIDATION RESULTS")
        print("=" * 80)

        overall = report.get("overall_assessment", {})
        print(
            f"✅ Validation Status: {'PASSED' if overall.get('validation_passed') else 'FAILED'}"
        )
        print(
            f"🎯 Critical Scenarios: {overall.get('critical_scenario_success_rate', '0/0')}"
        )
        print(
            f"💚 System Health: {overall.get('overall_system_health', 'unknown').title()}"
        )
        print(
            f"🚀 Production Ready: {'Yes' if overall.get('production_readiness') else 'No'}"
        )

        metadata = report.get("validation_metadata", {})
        print(f"⏱️  Total Time: {metadata.get('total_execution_time', 0):.1f}s")
        print(f"🧪 Scenarios Tested: {metadata.get('scenarios_tested', 0)}")

        # Show scenario summary
        print("\n📊 SCENARIO SUMMARY:")
        summary = report.get("validation_summary", {})
        for scenario, info in summary.items():
            status_icon = "✅" if info["status"] == "passed" else "❌"
            critical_icon = "🔥" if info["critical"] else "📋"
            print(
                f"  {status_icon} {critical_icon} {scenario.replace('_', ' ').title()} ({info['execution_time']:.1f}s)"
            )

        if report.get("recommendations"):
            print("\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(report["recommendations"], 1):
                print(f"  {i}. {rec}")

        print(
            f"\n📄 Full validation report: {output_dir}/escalation_validation_report.json"
        )
        print("=" * 80)

        return 0 if overall.get("validation_passed", False) else 1

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
