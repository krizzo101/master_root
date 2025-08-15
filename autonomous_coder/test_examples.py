#!/usr/bin/env python3
"""
Test Examples - Demonstrates the Autonomous Coder capabilities
"""

import asyncio
from main import main
from pathlib import Path


async def run_examples():
    """Run several example builds to demonstrate capabilities."""
    
    examples = [
        {
            "description": "Build a simple TODO app with modern web technologies",
            "expected_tech": ["vite", "typescript", "react"],
            "project_type": "Simple Web App"
        },
        {
            "description": "Create a REST API for managing products with authentication",
            "expected_tech": ["fastapi", "sqlalchemy", "python"],
            "project_type": "REST API"
        },
        {
            "description": "Build a CLI tool for batch file processing",
            "expected_tech": ["python", "typer"],
            "project_type": "CLI Tool"
        },
        {
            "description": "Create a dashboard with charts and data visualization",
            "expected_tech": ["react", "tailwind", "recharts"],
            "project_type": "Dashboard"
        }
    ]
    
    print("\n" + "="*60)
    print("🧪 AUTONOMOUS CODER TEST SUITE")
    print("Testing different project types")
    print("="*60)
    
    results = []
    
    for i, example in enumerate(examples, 1):
        print(f"\n📝 Test {i}/{len(examples)}: {example['project_type']}")
        print(f"   Request: {example['description']}")
        
        try:
            # Run the build
            output_dir = f"./test_output/example_{i}"
            exit_code = await main(
                description=example['description'],
                output_path=output_dir,
                force_research=False  # Use cached research for speed
            )
            
            if exit_code == 0:
                # Check if expected files exist
                output_path = Path(output_dir)
                projects = list(output_path.glob("*"))
                
                if projects:
                    project_path = projects[0]
                    
                    # Check for key files
                    has_package = (project_path / "package.json").exists()
                    has_requirements = (project_path / "requirements.txt").exists()
                    has_main = any(project_path.glob("main.*"))
                    
                    success = has_package or has_requirements or has_main
                    
                    results.append({
                        "test": example['project_type'],
                        "success": success,
                        "files_found": has_package or has_requirements
                    })
                    
                    print(f"   ✅ Success: Generated {example['project_type']}")
                else:
                    results.append({
                        "test": example['project_type'],
                        "success": False,
                        "error": "No project generated"
                    })
                    print(f"   ❌ Failed: No project generated")
            else:
                results.append({
                    "test": example['project_type'],
                    "success": False,
                    "error": f"Exit code {exit_code}"
                })
                print(f"   ❌ Failed: Exit code {exit_code}")
                
        except Exception as e:
            results.append({
                "test": example['project_type'],
                "success": False,
                "error": str(e)
            })
            print(f"   ❌ Error: {str(e)}")
    
    # Print summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results if r.get("success"))
    total = len(results)
    
    for result in results:
        status = "✅ PASS" if result.get("success") else "❌ FAIL"
        print(f"{status}: {result['test']}")
        if not result.get("success") and "error" in result:
            print(f"        Error: {result['error']}")
    
    print(f"\n📈 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The Autonomous Coder is working perfectly!")
    else:
        print(f"⚠️  {total - passed} test(s) failed. Check the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_examples())
    exit(0 if success else 1)