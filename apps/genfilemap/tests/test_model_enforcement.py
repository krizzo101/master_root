
#!/usr/bin/env python3
"""
Test script to verify that only gpt-4.1-mini is allowed.
This script attempts to use a different model but should be forced to use gpt-4.1-mini.
"""

import asyncio
import os
import sys
from genfilemap.api import create_api_client
from genfilemap.utils import get_api_key
from genfilemap.config import load_config

async def test_model_enforcement():
    """Test that only gpt-4.1-mini is allowed"""
    # Load configuration
    config = load_config()

    # Get API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        return False

    # Create API client
    client = create_api_client("openai", api_key)

    # Try to use a different model
    test_model = "gpt-3.5-turbo"
    print(f"Attempting to use model: {test_model}")

    try:
        # Simple completion request
        result = await client.generate_completion(
            system_message="You are a helpful assistant.",
            user_message="Say hello world.",
            model=test_model,
            max_tokens=100
        )

        print("\nResponse received:")
        print(result)
        print("\nCheck the warnings above to see if the model was enforced to gpt-4.1-mini")
        return True
    except Exception as e:
        print(f"Error during API call: {str(e)}")
        return False

async def main():
    """Main entry point"""
    success = await test_model_enforcement()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())