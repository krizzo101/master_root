#!/usr/bin/env python3
"""
Test script for Agent Scratchpad Integration

This script demonstrates the agent scratchpad functionality that has been
integrated into the OAMAT-SD system.
"""

import asyncio

from src.applications.oamat_sd.src.sd_logging.log_config import LogConfig
from src.applications.oamat_sd.src.sd_logging.logger_factory import LoggerFactory


async def test_scratchpad_functionality():
    """Test the agent scratchpad functionality"""

    print("🧪 Testing Agent Scratchpad Integration")
    print("=" * 50)

    # Initialize logging system
    log_config = LogConfig(
        console_rich=True,
        console_progress=True,
        truncate_prompts_console=200,
        full_prompts_in_api_log=True,
    )
    logger_factory = LoggerFactory(log_config)

    # Get the scratchpad logger
    scratchpad_logger = logger_factory.get_scratchpad_logger()

    print("✅ Scratchpad logger initialized")

    # Test 1: Add reasoning steps
    print("\n📝 Test 1: Adding reasoning steps")
    scratchpad_logger.add_reasoning_step(
        agent_role="researcher",
        step="Analyzing user request for complexity",
        context={"request_type": "web_application", "estimated_complexity": "medium"},
    )

    scratchpad_logger.add_reasoning_step(
        agent_role="researcher",
        step="Determining required research areas",
        context={"areas": ["React", "Node.js", "database_design"]},
    )

    # Test 2: Add calculations
    print("🧮 Test 2: Adding calculations")
    scratchpad_logger.add_calculation(
        agent_role="researcher",
        calculation="complexity_score = (frontend_complexity + backend_complexity) / 2",
        result=7.5,
        context={"frontend_complexity": 8, "backend_complexity": 7},
    )

    # Test 3: Add decisions
    print("🎯 Test 3: Adding decisions")
    scratchpad_logger.add_decision(
        agent_role="researcher",
        decision="Subdivide into 3 specialized agents",
        rationale="Complexity score 7.5 exceeds threshold of 5.0",
        context={"threshold": 5.0, "subdivision_count": 3},
    )

    # Test 4: Add tool calls
    print("🔧 Test 4: Adding tool calls")
    scratchpad_logger.add_tool_call(
        agent_role="researcher",
        tool_name="web_search",
        input_data={"query": "React best practices 2025"},
        output_data={"results_count": 15, "top_result": "React 18 features"},
    )

    # Test 5: Get scratchpad summary
    print("\n📋 Test 5: Getting scratchpad summary")
    summary = scratchpad_logger.get_scratchpad_summary("researcher")
    print("Scratchpad Summary for 'researcher':")
    print("-" * 40)
    print(summary)

    # Test 6: Get JSON format
    print("\n📊 Test 6: Getting JSON format")
    json_entries = scratchpad_logger.get_scratchpad_json("researcher")
    print(f"Total entries: {len(json_entries)}")
    print(f"Entry types: {[entry['entry_type'] for entry in json_entries]}")

    # Test 7: Test multiple agents
    print("\n👥 Test 7: Testing multiple agents")
    scratchpad_logger.add_reasoning_step(
        agent_role="frontend_developer",
        step="Planning React component structure",
        context={"framework": "React", "components_count": 5},
    )

    scratchpad_logger.add_reasoning_step(
        agent_role="backend_developer",
        step="Designing API endpoints",
        context={"api_type": "REST", "endpoints_count": 8},
    )

    # Test 8: Get all scratchpad entries
    print("\n📋 Test 8: Getting all scratchpad entries")
    all_summary = scratchpad_logger.get_scratchpad_summary()
    print("All Scratchpad Entries:")
    print("-" * 40)
    print(all_summary)

    # Test 9: Clear specific agent scratchpad
    print("\n🧹 Test 9: Clearing specific agent scratchpad")
    scratchpad_logger.clear_scratchpad("researcher")
    remaining_summary = scratchpad_logger.get_scratchpad_summary()
    print("Remaining entries after clearing 'researcher':")
    print("-" * 40)
    print(remaining_summary)

    print("\n✅ All scratchpad tests completed successfully!")
    print("\n🎯 Scratchpad Integration Summary:")
    print("- Built on existing logging infrastructure")
    print("- Tracks reasoning steps, calculations, decisions, and tool calls")
    print("- Provides both human-readable and JSON formats")
    print("- Supports per-agent and global scratchpad management")
    print("- Integrated into execution engine for automatic tracking")


if __name__ == "__main__":
    asyncio.run(test_scratchpad_functionality())
