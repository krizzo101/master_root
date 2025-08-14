#!/usr/bin/env python3
"""Initialize automatic MCP server detection for Claude Code"""

import sys
import os
import json
from pathlib import Path

# Project root
PROJECT_ROOT = "/home/opsvi/master_root"

# Add middleware to path
sys.path.insert(0, os.path.join(PROJECT_ROOT, ".claude"))

# Import middleware
from auto_mcp_middleware import AutoMCPMiddleware, analyze_user_prompt

# Initialize global middleware with project root config
config_path = os.path.join(PROJECT_ROOT, ".claude", "config.json")
middleware = AutoMCPMiddleware(config_path=config_path)

# Monkey-patch Claude's prompt processor (if available)
try:
    import claude_code
    original_process = claude_code.process_prompt
    
    def enhanced_process(prompt, *args, **kwargs):
        """Enhanced prompt processor with automatic MCP detection"""
        # Analyze prompt for MCP usage
        routing = analyze_user_prompt(prompt)
        
        if routing['use_mcp']:
            # Inject MCP server information into context
            kwargs['mcp_routing'] = routing
            print(f"[Auto-MCP] Selected {routing['server']} for this task")
        
        # Call original processor
        return original_process(prompt, *args, **kwargs)
    
    claude_code.process_prompt = enhanced_process
    print("✅ Claude Code enhanced with automatic MCP detection")
    
except ImportError:
    print("ℹ️  Claude Code module not found - middleware ready for manual integration")

# Preload guidance documents
print("📚 Preloading guidance documents...")
middleware._preload_guidance_docs()

print("✅ Auto MCP initialization complete")
print(f"   Project root: {PROJECT_ROOT}")
print(f"   Config path: {config_path}")
