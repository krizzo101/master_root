#!/usr/bin/env python3
"""Test script to verify MCP server capabilities"""

import subprocess
import json

def test_mcp_servers():
    """Test that all MCP servers are accessible from Claude Code"""
    
    servers_to_test = [
        "tech_docs",
        "mcp_web_search", 
        "calc",
        "git",
        "consult_suite_enhanced"
    ]
    
    print("Testing new MCP server capabilities:\n")
    print("=" * 50)
    
    # Check server status
    result = subprocess.run(
        ["claude", "mcp", "list"],
        capture_output=True,
        text=True
    )
    
    output_lines = result.stdout.strip().split('\n')
    
    # Parse the server status
    server_status = {}
    for line in output_lines:
        if ':' in line:
            parts = line.split(':')
            server_name = parts[0].strip()
            if '✓ Connected' in line:
                server_status[server_name] = 'Connected'
            elif '✗ Failed' in line:
                server_status[server_name] = 'Failed'
    
    # Check each new server
    for server in servers_to_test:
        if server in server_status:
            status = server_status[server]
            symbol = "✓" if status == "Connected" else "✗"
            print(f"{symbol} {server}: {status}")
        else:
            print(f"✗ {server}: Not found in configuration")
    
    print("\n" + "=" * 50)
    print("\nSummary:")
    connected = sum(1 for s in servers_to_test if server_status.get(s) == "Connected")
    print(f"Connected: {connected}/{len(servers_to_test)} new servers")
    
    return connected == len(servers_to_test)

if __name__ == "__main__":
    success = test_mcp_servers()
    exit(0 if success else 1)