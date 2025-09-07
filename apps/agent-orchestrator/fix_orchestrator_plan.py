#!/usr/bin/env python3

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.unified.enhanced_agent_task import EnhancedAgentTask
from src.unified.unified_orchestrator import create_standard_orchestrator


async def main():
    orchestrator = create_standard_orchestrator(
        output_dir=Path("orchestrator_fixes"), max_parallel=3
    )

    tasks = [
        EnhancedAgentTask(
            task_id="fix_get_metrics",
            task_type="development-specialist",
            prompt="Add missing get_metrics() method to UnifiedOrchestrator class in src/unified/unified_orchestrator.py. Method should return self.metrics.",
        ),
        EnhancedAgentTask(
            task_id="fix_error_handling",
            task_type="development-specialist",
            prompt="Find why agent execution shows empty errors in generic_orchestrator.py. Fix error capture and logging in execute_agent method.",
        ),
        EnhancedAgentTask(
            task_id="validate_task_types",
            task_type="development-specialist",
            prompt="Check which task types are valid in claude. Replace test-remediation-specialist with valid types in validation plan.",
        ),
    ]

    await orchestrator.run(lambda: tasks)


if __name__ == "__main__":
    asyncio.run(main())
