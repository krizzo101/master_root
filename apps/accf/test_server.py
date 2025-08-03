"""
Simple test script to run the server and test endpoints.
"""

import asyncio
import uvicorn
from accf_agents.api.app import app


def main():
    """Run the server for testing."""
    print("Starting ACCF Research Agent API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info", reload=False)


if __name__ == "__main__":
    main()
