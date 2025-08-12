#!/usr/bin/env python3
"""
Reality Check Tests - Verify systems actually work as intended
Test against real problems I was trying to solve
"""

import sys

sys.path.append("/home/opsvi/asea/development/temp")

from mistake_prevention_system import MistakePreventionSystem
from session_continuity_system import SessionContinuitySystem
from autonomous_decision_system import AutonomousDecisionSystem


def test_mistake_prevention_real_scenarios():
    """Test if mistake prevention catches actual errors I make"""

    print("=== TESTING MISTAKE PREVENTION AGAINST REAL SCENARIOS ===")

    system = MistakePreventionSystem()

    # Test 1: AQL query with SORT after RETURN (common error I make)
    bad_aql = "FOR doc IN core_memory RETURN doc SORT doc.created DESC"
    result = system.validate_aql_query(bad_aql)

    print("\nTest 1 - AQL SORT after RETURN:")
    print(f"Query: {bad_aql}")
    print(f"Caught error: {not result['valid']}")
    print(f"Errors: {result['errors']}")

    if not result["valid"]:
        print("✓ SUCCESS: System caught SORT after RETURN error")
    else:
        print("✗ FAILURE: System did not catch the error")

    # Test 2: Tool result with rate limit (I often miss these)
    failed_tool_result = {
        "error": "Rate limit exceeded",
        "status": 429,
        "content": None,
    }
    result = system.validate_tool_result(failed_tool_result)

    print("\nTest 2 - Tool failure detection:")
    print(f"Tool result: {failed_tool_result}")
    print(f"Caught failure: {not result['success']}")
    print(f"Failure type: {result['failure_type']}")

    if not result["success"]:
        print("✓ SUCCESS: System caught tool failure")
    else:
        print("✗ FAILURE: System did not catch tool failure")

    # Test 3: Valid AQL should pass
    good_aql = "FOR doc IN core_memory FILTER doc.foundational == true SORT doc.created DESC RETURN doc"
    result = system.validate_aql_query(good_aql)

    print("\nTest 3 - Valid AQL should pass:")
    print(f"Query: {good_aql}")
    print(f"Valid: {result['valid']}")

    if result["valid"]:
        print("✓ SUCCESS: System correctly validated good AQL")
    else:
        print("✗ FAILURE: System incorrectly flagged good AQL")

    return True


def test_session_continuity_real_application():
    """Test if session continuity actually loads and applies knowledge"""

    print("\n=== TESTING SESSION CONTINUITY REAL APPLICATION ===")

    system = SessionContinuitySystem()

    # Test 1: Get startup checklist
    checklist = system.get_session_startup_checklist()
    print("\nTest 1 - Startup checklist loaded:")
    for item in checklist:
        print(f"  {item}")

    if len(checklist) > 0:
        print("✓ SUCCESS: Session continuity provides startup checklist")
    else:
        print("✗ FAILURE: No startup checklist provided")

    # Test 2: Validate operation before execution
    bad_shell_command = "python scripts/test.py"  # Relative path - should fail
    result = system.validate_before_operation("shell_command", bad_shell_command)

    print("\nTest 2 - Pre-operation validation:")
    print(f"Command: {bad_shell_command}")
    print(f"Should proceed: {result['proceed']}")
    print(f"Errors: {result['errors']}")

    if not result["proceed"]:
        print("✓ SUCCESS: System caught relative path error")
    else:
        print("✗ FAILURE: System did not catch relative path error")

    # Test 3: Context-specific knowledge retrieval
    db_knowledge = system.get_operational_knowledge_for_context("database operations")
    print("\nTest 3 - Context-specific knowledge:")
    print(f"Database knowledge loaded: {len(db_knowledge) > 0}")

    if len(db_knowledge) > 0:
        print("✓ SUCCESS: Context-specific knowledge retrieved")
        for key in db_knowledge.keys():
            print(f"  - {key}")
    else:
        print("✗ FAILURE: No context-specific knowledge retrieved")

    return True


def test_decision_system_real_improvement():
    """Test if decision system actually improves decision quality"""

    print("\n=== TESTING DECISION SYSTEM REAL IMPROVEMENT ===")

    system = AutonomousDecisionSystem()

    # Test 1: Assess a reactive decision (should score low)
    reactive_decision = "Implement user suggestion"
    reactive_rationale = "User recommended this approach so I will implement it"

    result = system.assess_decision_quality(reactive_decision, reactive_rationale)
    print("\nTest 1 - Reactive decision assessment:")
    print(f"Decision: {reactive_decision}")
    print(f"Autonomous score: {result['autonomous_score']}")
    print(f"Concerns: {result['concerns']}")

    if result["autonomous_score"] < 50:
        print("✓ SUCCESS: System correctly identified reactive decision as low quality")
    else:
        print("✗ FAILURE: System did not catch reactive decision pattern")

    # Test 2: Assess an autonomous decision (should score high)
    autonomous_decision = "Focus on mistake prevention over research synthesis"
    autonomous_rationale = "Holistic analysis shows operational problems repeatedly occur despite stored knowledge. Evidence-based assessment indicates mistake prevention builds foundation for compound learning and addresses actual operational needs rather than theoretical improvements."

    result = system.assess_decision_quality(autonomous_decision, autonomous_rationale)
    print("\nTest 2 - Autonomous decision assessment:")
    print(f"Decision: {autonomous_decision}")
    print(f"Autonomous score: {result['autonomous_score']}")
    print(f"Strengths: {result['strengths']}")

    if result["autonomous_score"] >= 75:
        print(
            "✓ SUCCESS: System correctly identified autonomous decision as high quality"
        )
    else:
        print("✗ FAILURE: System did not properly assess autonomous decision")

    # Test 3: Generate framework summary
    summary = system.generate_decision_framework_summary()
    print("\nTest 3 - Framework summary generated:")
    print(f"Summary length: {len(summary)} characters")

    if len(summary) > 100:
        print("✓ SUCCESS: Decision framework summary generated")
    else:
        print("✗ FAILURE: No meaningful framework summary generated")

    return True


def test_real_world_integration():
    """Test if systems actually work together in real scenarios"""

    print("\n=== TESTING REAL-WORLD INTEGRATION ===")

    mistake_system = MistakePreventionSystem()
    continuity_system = SessionContinuitySystem()
    decision_system = AutonomousDecisionSystem()

    # Scenario: I want to run an AQL query
    print("\nScenario: Running AQL query with integrated validation")

    # Step 1: Use mistake prevention to validate query
    query = "FOR doc IN core_memory RETURN doc SORT doc.created DESC"  # Bad query
    validation = mistake_system.validate_aql_query(query)

    print(f"Query validation: {validation}")

    # Step 2: Use session continuity to check operational requirements
    operation_check = continuity_system.validate_before_operation("aql_query", query)
    print(f"Operation check: {operation_check}")

    # Step 3: Use decision system to assess whether to proceed
    if not validation["valid"]:
        decision_context = "aql_query_failed_validation"
        decision_rationale = "Query failed validation due to SORT after RETURN. Should fix syntax based on stored operational knowledge before proceeding."
        decision_assessment = decision_system.assess_decision_quality(
            decision_context, decision_rationale
        )

        print(f"Decision assessment: {decision_assessment}")

        if decision_assessment["autonomous_score"] > 50:
            print(
                "✓ SUCCESS: Integrated system correctly handled failed query validation"
            )
        else:
            print("✗ FAILURE: Decision system did not properly assess fix approach")

    return True


def run_all_reality_checks():
    """Run all reality check tests"""

    print("REALITY CHECK: Testing if systems actually work as intended")
    print("=" * 80)

    try:
        test_mistake_prevention_real_scenarios()
        test_session_continuity_real_application()
        test_decision_system_real_improvement()
        test_real_world_integration()

        print("\n" + "=" * 80)
        print("REALITY CHECK COMPLETE")
        print("Review results above to verify systems work as intended")

    except Exception as e:
        print(f"\nREALITY CHECK FAILED: {e}")
        print("Systems may not be working as intended")
        return False

    return True


if __name__ == "__main__":
    run_all_reality_checks()
