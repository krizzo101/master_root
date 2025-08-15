#!/usr/bin/env python3
"""
Recursive Chain Demonstration
Shows a 3-level recursive chain where each level:
1. Uses a different MCP tool
2. Spawns the next level
3. Tracks depth
"""

import json
import time
import subprocess
from datetime import datetime

def level1_execution():
    """Level 1: Main orchestrator"""
    print("=== LEVEL 1 EXECUTION ===")
    print(f"Depth: 1")
    print(f"Start time: {datetime.now().isoformat()}")
    
    # Level 1 uses time MCP tool (simulated)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"MCP Time Tool Result: {current_time}")
    
    # Spawn Level 2
    print("\nSpawning Level 2...")
    level2_result = level2_execution(parent_time=current_time, depth=2)
    
    print("\n=== LEVEL 1 COMPLETE ===")
    print(f"Level 2 returned: {level2_result}")
    
    return {
        "level": 1,
        "time": current_time,
        "child_result": level2_result
    }

def level2_execution(parent_time, depth):
    """Level 2: Middle tier"""
    print(f"\n  === LEVEL 2 EXECUTION ===")
    print(f"  Depth: {depth}")
    print(f"  Parent started at: {parent_time}")
    
    # Level 2 uses firecrawl MCP tool (simulated)
    firecrawl_result = {
        "url": "https://example.com",
        "title": "Example Domain",
        "scraped_at": datetime.now().isoformat()
    }
    print(f"  MCP Firecrawl Result: {json.dumps(firecrawl_result, indent=2)}")
    
    # Spawn Level 3
    print("\n  Spawning Level 3...")
    level3_result = level3_execution(parent_time=datetime.now().isoformat(), depth=3)
    
    print(f"\n  === LEVEL 2 COMPLETE ===")
    
    return {
        "level": 2,
        "firecrawl_data": firecrawl_result,
        "child_result": level3_result
    }

def level3_execution(parent_time, depth):
    """Level 3: Leaf node - performs calculation"""
    print(f"\n    === LEVEL 3 EXECUTION ===")
    print(f"    Depth: {depth}")
    print(f"    Parent started at: {parent_time}")
    
    # Level 3 performs calculation
    calculation = (10 * 5) + (8 - 3)
    print(f"    Calculation: (10 * 5) + (8 - 3) = {calculation}")
    
    # Level 3 uses relative time MCP tool (simulated)
    from datetime import datetime, timedelta
    base_time = datetime.strptime("2025-08-12 20:00:00", "%Y-%m-%d %H:%M:%S")
    current = datetime.now()
    time_diff = current - base_time
    
    relative_time = {
        "base": "2025-08-12 20:00:00",
        "current": current.strftime("%Y-%m-%d %H:%M:%S"),
        "difference_seconds": int(time_diff.total_seconds()),
        "human_readable": f"{int(time_diff.total_seconds() / 60)} minutes ago"
    }
    print(f"    MCP Relative Time Result: {json.dumps(relative_time, indent=2)}")
    
    print(f"\n    === LEVEL 3 COMPLETE ===")
    
    return {
        "level": 3,
        "calculation_result": calculation,
        "relative_time": relative_time,
        "depth": depth
    }

def main():
    """Main entry point"""
    print("Starting Recursive Chain Demonstration")
    print("=" * 50)
    
    # Start the recursive chain
    result = level1_execution()
    
    print("\n" + "=" * 50)
    print("FINAL RECURSIVE CHAIN RESULT:")
    print(json.dumps(result, indent=2))
    
    # Show depth tracking summary
    print("\n" + "=" * 50)
    print("DEPTH TRACKING SUMMARY:")
    print(f"Level 1: Depth 1 - Used Time MCP Tool")
    print(f"Level 2: Depth 2 - Used Firecrawl MCP Tool")
    print(f"Level 3: Depth 3 - Used Relative Time MCP Tool")
    print(f"Maximum recursion depth reached: 3")

if __name__ == "__main__":
    main()