"""
Quick Model Test for o3_agent Tool

Simple script to test the o3_agent tool with different models.
"""

import asyncio
import json
from datetime import datetime

# Simple test prompt
TEST_PROMPT = """
Design a simple REST API for a todo list application. Include:
1. API endpoints for CRUD operations
2. Basic data model
3. Error handling
4. Simple authentication
"""

APPROVED_MODELS = ["o4-mini", "o3", "gpt-4.1-mini", "gpt-4.1", "gpt-4.1-nano"]


async def test_single_model(model: str):
    """Test a single model with the o3_agent tool."""
    print(f"\n{'='*50}")
    print(f"Testing: {model}")
    print(f"{'='*50}")

    try:
        # Import the MCP tool
        from mcp_agent_server import ConsultAgentTool

        # Create tool instance
        tool = ConsultAgentTool()

        # Call the tool
        result = await tool.execute(
            {
                "prompt": TEST_PROMPT,
                "model": model,
                "iterate": 1,
                "critic_enabled": False,
                "artifact_type": "code",
            }
        )

        # Extract text from TextContent objects
        response_text = ""
        if result and len(result) > 0:
            response_text = result[0].text

        print(f"✅ Success!")
        print(f"Response length: {len(response_text)} characters")
        print(f"Response preview: {response_text[:200]}...")

        return {
            "model": model,
            "success": True,
            "response": response_text,
            "response_length": len(response_text),
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        return {"model": model, "success": False, "error": str(e)}


async def main():
    """Main function to test all models."""
    print("🚀 Quick Model Test")
    print(f"Testing models: {', '.join(APPROVED_MODELS)}")
    print(f"Test prompt: {TEST_PROMPT[:100]}...")

    results = {}

    for model in APPROVED_MODELS:
        result = await test_single_model(model)
        results[model] = result
        await asyncio.sleep(1)  # Brief pause

    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")

    successful_models = []
    for model, result in results.items():
        if result["success"]:
            successful_models.append(model)
            print(f"✅ {model}: {result['response_length']} characters")
        else:
            print(f"❌ {model}: {result['error']}")

    print(f"\nSuccessful: {len(successful_models)}/{len(APPROVED_MODELS)}")

    # Save results
    with open("quick_test_results.json", "w") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "test_prompt": TEST_PROMPT,
                "results": results,
            },
            f,
            indent=2,
        )

    print(f"\n💾 Results saved to: quick_test_results.json")


if __name__ == "__main__":
    asyncio.run(main())
