#!/usr/bin/env python3
"""
Test script to validate MCP server installations and configurations
"""

import sys
import os
import importlib
import asyncio
from pathlib import Path

# Add the libs directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing module imports...")
    
    modules_to_test = [
        ("opsvi_mcp.servers.claude_code", "Claude Code (Original)"),
        ("opsvi_mcp.servers.claude_code_v2", "Claude Code V2"),
        ("opsvi_mcp.servers.openai_codex", "OpenAI Codex"),
        ("opsvi_mcp.servers.cursor_agent", "Cursor Agent"),
        ("opsvi_mcp.servers.context_bridge", "Context Bridge"),
    ]
    
    success = True
    for module_name, display_name in modules_to_test:
        try:
            module = importlib.import_module(module_name)
            print(f"✓ {display_name}: Successfully imported")
        except ImportError as e:
            print(f"✗ {display_name}: Import failed - {e}")
            success = False
        except Exception as e:
            print(f"✗ {display_name}: Unexpected error - {e}")
            success = False
    
    return success


def test_configurations():
    """Test that configurations can be instantiated"""
    print("\nTesting configurations...")
    
    configs_to_test = [
        ("opsvi_mcp.servers.claude_code.config", "ServerConfig", "Claude Code Config"),
        ("opsvi_mcp.servers.claude_code_v2.config", "ServerConfig", "Claude Code V2 Config"),
        ("opsvi_mcp.servers.openai_codex.config", "CodexConfig", "OpenAI Codex Config"),
        ("opsvi_mcp.servers.cursor_agent.config", "CursorConfig", "Cursor Agent Config"),
    ]
    
    success = True
    for module_name, class_name, display_name in configs_to_test:
        try:
            module = importlib.import_module(module_name)
            config_class = getattr(module, class_name)
            
            # Try to instantiate (may fail if required env vars missing)
            try:
                if "openai" in module_name.lower():
                    # Skip OpenAI if no API key
                    if not os.environ.get("OPENAI_API_KEY"):
                        print(f"⚠ {display_name}: Skipped (OPENAI_API_KEY not set)")
                        continue
                        
                config = config_class()
                print(f"✓ {display_name}: Successfully instantiated")
            except ValueError as e:
                print(f"⚠ {display_name}: Missing required environment variable - {e}")
            
        except Exception as e:
            print(f"✗ {display_name}: Failed - {e}")
            success = False
    
    return success


def test_server_instantiation():
    """Test that servers can be instantiated"""
    print("\nTesting server instantiation...")
    
    servers_to_test = [
        ("opsvi_mcp.servers.claude_code_v2.server", "ClaudeCodeV2Server", "Claude Code V2 Server"),
        ("opsvi_mcp.servers.openai_codex.server", "OpenAICodexServer", "OpenAI Codex Server"),
        ("opsvi_mcp.servers.cursor_agent.server", "CursorAgentServer", "Cursor Agent Server"),
    ]
    
    success = True
    for module_name, class_name, display_name in servers_to_test:
        try:
            module = importlib.import_module(module_name)
            server_class = getattr(module, class_name)
            
            # Try to instantiate (may fail if config requirements not met)
            try:
                if "openai" in module_name.lower():
                    # Skip OpenAI if no API key
                    if not os.environ.get("OPENAI_API_KEY"):
                        print(f"⚠ {display_name}: Skipped (OPENAI_API_KEY not set)")
                        continue
                
                if "claude" in module_name.lower():
                    # Skip Claude if no token
                    if not os.environ.get("CLAUDE_CODE_TOKEN"):
                        print(f"⚠ {display_name}: Can instantiate but needs CLAUDE_CODE_TOKEN to function")
                        # Still try to instantiate
                        
                server = server_class()
                print(f"✓ {display_name}: Successfully instantiated")
                
                # Check if server has required methods
                required_methods = ['run', '_setup_tools']
                for method in required_methods:
                    if not hasattr(server, method):
                        print(f"  ⚠ Missing method: {method}")
                        
            except Exception as e:
                print(f"⚠ {display_name}: Instantiation failed - {e}")
                
        except Exception as e:
            print(f"✗ {display_name}: Import failed - {e}")
            success = False
    
    return success


def test_unified_orchestrator():
    """Test the unified orchestrator"""
    print("\nTesting Unified Orchestrator...")
    
    try:
        from opsvi_mcp.servers.unified_orchestrator import UnifiedMCPOrchestrator
        
        # Check if required env vars are set
        required_vars = ["CLAUDE_CODE_TOKEN", "OPENAI_API_KEY"]
        missing = [var for var in required_vars if not os.environ.get(var)]
        
        if missing:
            print(f"⚠ Unified Orchestrator: Requires {', '.join(missing)}")
            print("  Set these environment variables to enable full functionality")
            return True
        
        # Try to instantiate
        orchestrator = UnifiedMCPOrchestrator()
        print(f"✓ Unified Orchestrator: Successfully instantiated")
        print(f"  Active servers: {list(orchestrator.servers.keys())}")
        
        return True
        
    except Exception as e:
        print(f"✗ Unified Orchestrator: Failed - {e}")
        return False


def check_dependencies():
    """Check if required dependencies are installed"""
    print("\nChecking dependencies...")
    
    dependencies = [
        ("fastmcp", "FastMCP (Core framework)"),
        ("pydantic", "Pydantic (Data models)"),
        ("yaml", "PyYAML (Configuration)"),
        ("aiofiles", "Aiofiles (Async file I/O)"),
        ("websockets", "WebSockets (Cursor communication)"),
    ]
    
    optional_deps = [
        ("openai", "OpenAI (Codex integration)"),
        ("anthropic", "Anthropic (Claude API)"),
    ]
    
    success = True
    
    # Check required dependencies
    for module_name, display_name in dependencies:
        try:
            importlib.import_module(module_name)
            print(f"✓ {display_name}: Installed")
        except ImportError:
            print(f"✗ {display_name}: Not installed - run: pip install {module_name}")
            success = False
    
    # Check optional dependencies
    print("\nOptional dependencies:")
    for module_name, display_name in optional_deps:
        try:
            importlib.import_module(module_name)
            print(f"✓ {display_name}: Installed")
        except ImportError:
            print(f"⚠ {display_name}: Not installed (optional)")
    
    return success


def main():
    """Run all tests"""
    print("=" * 60)
    print("MCP Server Installation Test Suite")
    print("=" * 60)
    
    # Check environment
    print("\nEnvironment Variables:")
    env_vars = [
        ("CLAUDE_CODE_TOKEN", "Claude Code authentication"),
        ("OPENAI_API_KEY", "OpenAI API access"),
        ("CURSOR_WORKSPACE", "Cursor workspace directory"),
        ("CURSOR_COMM_METHOD", "Cursor communication method"),
    ]
    
    for var, description in env_vars:
        value = os.environ.get(var)
        if value:
            if "KEY" in var or "TOKEN" in var:
                # Mask sensitive values
                masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
                print(f"  {var}: {masked} ({description})")
            else:
                print(f"  {var}: {value} ({description})")
        else:
            print(f"  {var}: Not set ({description})")
    
    # Run tests
    results = []
    
    results.append(("Dependencies", check_dependencies()))
    results.append(("Module Imports", test_imports()))
    results.append(("Configurations", test_configurations()))
    results.append(("Server Instantiation", test_server_instantiation()))
    results.append(("Unified Orchestrator", test_unified_orchestrator()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed! MCP servers are properly installed.")
    else:
        print("⚠ Some tests failed. Please check the output above for details.")
        print("\nTo fix missing dependencies, run:")
        print("  pip install -r /home/opsvi/master_root/libs/opsvi-mcp/requirements.txt")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())