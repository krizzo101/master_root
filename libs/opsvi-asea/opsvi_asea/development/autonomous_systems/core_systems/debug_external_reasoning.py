#!/usr/bin/env python3
"""
Debug script to identify why external reasoning service initialization fails.
"""

import sys
import asyncio
import json
from pathlib import Path

# Add current directory to path
sys.path.append(".")


async def debug_initialization():
    print("🔍 Debugging External Reasoning Service Initialization")
    print("=" * 60)

    # Step 1: Test configuration loading
    print("\n1. Testing Configuration Loading...")
    try:
        config_path = (
            Path(__file__).parent.parent / "config" / "autonomous_systems_config.json"
        )
        print(f"Config path: {config_path}")
        print(f"Config exists: {config_path.exists()}")

        with open(config_path, "r") as f:
            config = json.load(f)
        print("✅ Configuration loaded successfully")

        # Check required fields
        required_fields = [
            "external_reasoning.openai_api_key",
            "external_reasoning.models.reasoning",
            "database.host",
            "database.database",
            "database.username",
            "database.password",
        ]

        for field in required_fields:
            keys = field.split(".")
            value = config
            try:
                for key in keys:
                    value = value[key]
                print(f"✅ {field}: {'*' * min(len(str(value)), 10)}")
            except KeyError:
                print(f"❌ Missing field: {field}")

    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        import traceback

        traceback.print_exc()
        return

    # Step 2: Test OpenAI client initialization
    print("\n2. Testing OpenAI Client...")
    try:
        from autonomous_openai_client import AutonomousOpenAIClient

        api_key = config["external_reasoning"]["openai_api_key"]
        client = AutonomousOpenAIClient(api_key)
        print("✅ OpenAI client created successfully")

        # Test a simple model call
        print("Testing simple API call...")

        # Use the sync client for testing
        import openai

        sync_client = openai.OpenAI(api_key=api_key)

        response = sync_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5,
        )
        print("✅ OpenAI API call successful")
        print(f"Response: {response.choices[0].message.content}")

    except Exception as e:
        print(f"❌ OpenAI client failed: {e}")
        import traceback

        traceback.print_exc()
        return

    # Step 3: Test database connection
    print("\n3. Testing Database Connection...")
    try:
        from knowledge_context_gatherer import KnowledgeContextGatherer

        db_config = config["database"]
        gatherer = KnowledgeContextGatherer(db_config)

        connection_result = await gatherer.connect()
        print(f"Database connection result: {connection_result}")

        if connection_result:
            print("✅ Database connection successful")
        else:
            print("❌ Database connection failed")

        gatherer.close()

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        import traceback

        traceback.print_exc()
        return

    # Step 4: Test full service initialization
    print("\n4. Testing Full Service Initialization...")
    try:
        from external_reasoning_service import ExternalReasoningService

        service = ExternalReasoningService()

        # Test each step of initialization
        print("Creating OpenAI client...")
        api_key = service.config["external_reasoning"]["openai_api_key"]
        service.openai_client = AutonomousOpenAIClient(api_key)
        print("✅ OpenAI client created")

        print("Creating context gatherer...")
        db_config = service.config["database"]
        service.context_gatherer = KnowledgeContextGatherer(db_config)
        print("✅ Context gatherer created")

        print("Connecting to database...")
        connection_success = await service.context_gatherer.connect()
        print(f"Database connection: {connection_success}")

        if connection_success:
            print("✅ Full service initialization successful!")

            # Test a simple analysis
            print("\n5. Testing Simple Analysis...")
            result = await service.analyze_decision(
                decision="Test decision", rationale="Test rationale for debugging"
            )

            if result["success"]:
                print("✅ External reasoning analysis works!")
                print(
                    f"Analysis method: {result.get('data', {}).get('analysis_method', 'unknown')}"
                )
                print(f"Cost: ${result.get('data', {}).get('analysis_cost', 0.0):.4f}")
            else:
                print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")

        else:
            print("❌ Database connection failed, cannot complete initialization")

        await service.close()

    except Exception as e:
        print(f"❌ Full service initialization failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_initialization())
