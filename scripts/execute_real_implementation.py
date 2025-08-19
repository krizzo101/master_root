#!/usr/bin/env python3
"""
Execute REAL TODO implementations - no simulations, actual code changes
"""

import sys
sys.path.insert(0, '/home/opsvi/master_root/libs')
sys.path.insert(0, '/home/opsvi/master_root/libs/opsvi-meta')

import asyncio
import json
from pathlib import Path
from datetime import datetime

from opsvi_meta.todo_discovery import TodoDiscoveryEngine
from opsvi_meta.real_implementation_pipeline import RealImplementationPipeline


async def main():
    """Execute real implementations"""
    
    print("="*70)
    print("REAL TODO IMPLEMENTATION - NO SIMULATIONS")
    print("="*70)
    
    # Discover TODOs
    print("\n🔍 Discovering TODOs...")
    discovery = TodoDiscoveryEngine()
    todos = discovery.discover_todos()
    
    print(f"Found {len(todos)} TODOs total")
    
    # Filter for simple/medium complexity to start
    simple_todos = [t for t in todos if t.estimated_complexity in ["simple", "medium"]]
    print(f"Found {len(simple_todos)} simple/medium complexity TODOs")
    
    # Get high priority ones
    high_priority = sorted(
        [t for t in simple_todos if t.priority >= 4],
        key=lambda x: -x.priority
    )[:3]  # Start with just 3 for safety
    
    if not high_priority:
        print("No high priority TODOs found")
        return 1
    
    print(f"\n📋 Will implement {len(high_priority)} high-priority TODOs:")
    for i, todo in enumerate(high_priority, 1):
        print(f"\n{i}. File: {Path(todo.file_path).name}")
        print(f"   Line {todo.line_number}: {todo.content[:60]}...")
        print(f"   Category: {todo.category}, Priority: {todo.priority}")
    
    # Confirm before proceeding
    print("\n" + "="*70)
    print("⚠️  WARNING: This will ACTUALLY modify files!")
    print("Backups will be created for each modified file.")
    print("="*70)
    
    response = input("\nProceed with REAL implementation? (type 'yes' to confirm): ")
    if response.lower() != 'yes':
        print("Cancelled")
        return 0
    
    # Create pipeline
    print("\n🚀 Starting REAL implementation pipeline...")
    pipeline = RealImplementationPipeline()
    
    # Process TODOs one by one
    for i, todo in enumerate(high_priority, 1):
        print(f"\n{'='*70}")
        print(f"Processing TODO {i}/{len(high_priority)}")
        print(f"File: {todo.file_path}")
        print(f"TODO: {todo.content}")
        print("="*70)
        
        result = await pipeline.implement_todo_for_real(todo)
        
        print(f"\n📊 Result: {result.status.upper()}")
        if result.files_modified:
            print(f"   Files modified: {', '.join(result.files_modified)}")
            print(f"   Lines changed: {result.lines_changed}")
        if result.tests_created:
            print(f"   Tests created: {', '.join(result.tests_created)}")
            print(f"   Tests passed: {'✅ Yes' if result.test_passed else '❌ No'}")
        if result.error_message:
            print(f"   Error: {result.error_message}")
        print(f"   Duration: {result.duration_seconds:.2f} seconds")
        
        # Validate the implementation
        if result.status in ["success", "partial"]:
            is_valid = pipeline.validate_implementation(result)
            print(f"   Validation: {'✅ Passed' if is_valid else '❌ Failed'}")
    
    # Generate final report
    print("\n" + "="*70)
    print("FINAL REPORT")
    print("="*70)
    
    report = pipeline.generate_report()
    
    print(f"\nTotal attempted: {report['summary']['total_attempted']}")
    print(f"Successful: {report['summary']['successful']} ({report['summary']['success_rate']:.1f}%)")
    print(f"Partial: {report['summary']['partial']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"\nFiles modified: {report['summary']['files_modified']}")
    print(f"Tests created: {report['summary']['tests_created']}")
    print(f"Lines changed: {report['summary']['lines_changed']}")
    print(f"Total duration: {report['summary']['total_duration']:.2f} seconds")
    
    # Save report
    report_dir = Path("/home/opsvi/master_root/.meta-system/real_reports")
    report_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = report_dir / f"real_implementation_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Full report saved to: {report_file}")
    
    # Show git status to confirm changes
    print("\n🔍 Git status (showing actual changes):")
    import subprocess
    result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True)
    print(result.stdout)
    
    return 0 if report['summary']['successful'] > 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)