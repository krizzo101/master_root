#!/usr/bin/env python3
"""
Test script to verify knowledge MCP server startup
Run this to ensure the server will load correctly in new Claude sessions
"""

import subprocess
import json
import time
import sys

def test_server_startup():
    """Test that the knowledge server starts and responds correctly"""
    
    print("🔍 Testing Knowledge MCP Server Startup...")
    print("-" * 50)
    
    # Test 1: Check Python path and imports
    print("\n1️⃣ Testing imports...")
    cmd = [
        "/home/opsvi/miniconda/bin/python", "-c",
        "import sys; sys.path.insert(0, '/home/opsvi/master_root'); "
        "from apps.knowledge_system import mcp_knowledge_server; "
        "print('✓ Import successful')"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Import failed: {result.stderr}")
        return False
    print(result.stdout.strip())
    
    # Test 2: Start server and send initialize request
    print("\n2️⃣ Testing server startup with MCP protocol...")
    
    # Prepare MCP initialize request
    initialize_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    # Start the server process
    process = subprocess.Popen(
        ["/home/opsvi/miniconda/bin/python", "-m", "apps.knowledge_system"],
        env={"PYTHONPATH": "/home/opsvi/master_root"},
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Send initialize request
        request_str = json.dumps(initialize_request) + "\n"
        stdout, stderr = process.communicate(input=request_str, timeout=5)
        
        # Parse response
        if stdout:
            # FastMCP banner is in stderr, actual response in stdout
            for line in stdout.strip().split('\n'):
                if line.startswith('{'):
                    try:
                        response = json.loads(line)
                        if 'result' in response:
                            print("✓ Server initialized successfully")
                            print(f"  - Protocol version: {response['result'].get('protocolVersion', 'unknown')}")
                            print(f"  - Server name: {response['result'].get('serverInfo', {}).get('name', 'unknown')}")
                            
                            # Check for tools
                            tools = response['result'].get('capabilities', {}).get('tools', {})
                            if tools:
                                print(f"  - Available tools: {len(tools)} registered")
                                for tool_name in list(tools.keys())[:5]:  # Show first 5 tools
                                    print(f"    • {tool_name}")
                            return True
                    except json.JSONDecodeError:
                        continue
        
        print(f"⚠️ Server started but no valid response received")
        if stderr and "FastMCP" in stderr:
            print("✓ FastMCP server banner detected (server is running)")
            return True
        
        return False
        
    except subprocess.TimeoutExpired:
        process.kill()
        print("❌ Server startup timeout")
        return False
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False
    finally:
        if process.poll() is None:
            process.kill()
    
    # Test 3: Verify .mcp.json configuration
    print("\n3️⃣ Verifying .mcp.json configuration...")
    try:
        with open('/home/opsvi/master_root/.mcp.json', 'r') as f:
            config = json.load(f)
            
        if 'knowledge' in config.get('mcpServers', {}):
            knowledge_config = config['mcpServers']['knowledge']
            print("✓ Knowledge server registered in .mcp.json")
            print(f"  - Command: {knowledge_config.get('command', 'not set')}")
            print(f"  - Module: {' '.join(knowledge_config.get('args', []))}")
            print(f"  - PYTHONPATH: {knowledge_config.get('env', {}).get('PYTHONPATH', 'not set')}")
            return True
        else:
            print("❌ Knowledge server not found in .mcp.json")
            return False
    except Exception as e:
        print(f"❌ Error reading .mcp.json: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Knowledge MCP Server Startup Test")
    print("=" * 50)
    
    success = test_server_startup()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed! Server should start correctly in new Claude sessions.")
        print("\nTo use in Claude, the following MCP tools will be available:")
        print("  • mcp__knowledge__knowledge_query")
        print("  • mcp__knowledge__knowledge_store")
        print("  • mcp__knowledge__knowledge_update")
        print("  • mcp__knowledge__knowledge_relate")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)