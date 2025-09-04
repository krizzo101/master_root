#!/usr/bin/env python3
"""
Quick Session ID Validation Script
Validates that our deterministic session ID generation matches expectations
"""
import hashlib
import sys

sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator")
sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator/src")

from execution_plan.adapter import ExecutionPlanAdapter
from unified_context_phase2_plan import create_unified_context_phase2_plan


def generate_deterministic_uuid(task_id: str, plan_id: str) -> str:
    """Generate deterministic UUID for comparison"""
    seed_string = f"{plan_id}-{task_id}"
    hash_obj = hashlib.md5(seed_string.encode())
    hex_str = hash_obj.hexdigest()
    # Format as proper UUID
    return f"{hex_str[:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:32]}"


def main():
    print("🧪 SESSION ID VALIDATION")
    print("=" * 40)

    # Test 1: Validate adapter generates correct UUIDs
    print("\n1️⃣  Testing ExecutionPlanAdapter UUID generation...")
    adapter = ExecutionPlanAdapter()

    test_cases = [
        ("test_task_1", "unified_context"),
        ("implement_base_pipeline", "unified_context"),
        ("research_cicd_integration", "unified_context"),
    ]

    for task_id, plan_id in test_cases:
        expected_uuid = generate_deterministic_uuid(task_id, plan_id)
        adapter_uuid = adapter.generate_deterministic_uuid(task_id, plan_id)

        match = expected_uuid == adapter_uuid
        status = "✅" if match else "❌"
        print(f"   {status} {task_id}")
        print(f"      Expected: {expected_uuid}")
        print(f"      Adapter:  {adapter_uuid}")
        if not match:
            return False

    # Test 2: Validate Phase 2 plan session ID mappings
    print("\n2️⃣  Testing Phase 2 plan session IDs...")
    try:
        phase2_plan = create_unified_context_phase2_plan()
        enhanced_tasks = adapter.convert_execution_plan(phase2_plan)

        print(f"   📋 Phase 2 tasks: {len(enhanced_tasks)}")
        print("   🎯 Session ID mappings:")

        for task in enhanced_tasks[:5]:  # Show first 5 tasks
            print(f"      {task.task_id} → {task.agent_uuid}")

        print(f"      ... and {len(enhanced_tasks) - 5} more tasks")

    except Exception as e:
        print(f"   ❌ Error loading Phase 2 plan: {e}")
        return False

    # Test 3: Reproducibility test
    print("\n3️⃣  Testing reproducibility...")

    # Create the same plan twice
    plan1 = create_unified_context_phase2_plan()
    plan2 = create_unified_context_phase2_plan()

    tasks1 = adapter.convert_execution_plan(plan1)
    tasks2 = adapter.convert_execution_plan(plan2)

    reproducible = True
    for t1, t2 in zip(tasks1, tasks2):
        if t1.agent_uuid != t2.agent_uuid:
            print(f"   ❌ Mismatch: {t1.task_id} → {t1.agent_uuid} vs {t2.agent_uuid}")
            reproducible = False

    if reproducible:
        print("   ✅ All session IDs are reproducible")
    else:
        print("   ❌ Session IDs are NOT reproducible!")
        return False

    print("\n🎉 ALL VALIDATIONS PASSED!")
    print("\n📋 READY FOR TESTING:")
    print("   Run: python test_session_ids.py")
    print("   Then: python execute_phase2_optimized.py")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
