#!/usr/bin/env python3
"""Test script for get_documentation function."""

import asyncio
import os
import sys

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from project_context.tools.analysis import get_documentation


async def test_get_documentation():
    """Test the get_documentation function with various parameters."""

    print("🧪 Testing get_documentation implementation...")

    try:
        # Test 1: Basic call without filters
        print("\n📊 Test 1: Basic documentation coverage analysis")
        result = await get_documentation()

        print(f"✅ Total elements: {result['summary']['total_elements']}")
        print(f"✅ Documented elements: {result['summary']['documented_elements']}")
        print(
            f"✅ Documentation percentage: {result['summary']['documentation_percentage']}%"
        )

        # Test 2: Filter by Python files
        print("\n🐍 Test 2: Python-only documentation analysis")
        python_result = await get_documentation(language="python")

        print(f"✅ Python elements: {python_result['summary']['total_elements']}")
        print(f"✅ Python documented: {python_result['summary']['documented_elements']}")
        print(
            f"✅ Python doc percentage: {python_result['summary']['documentation_percentage']}%"
        )

        # Test 3: Function-specific analysis
        print("\n⚙️ Test 3: Function documentation analysis")
        function_result = await get_documentation(element_type="function")

        print(f"✅ Total functions: {function_result['summary']['total_elements']}")
        print(
            f"✅ Documented functions: {function_result['summary']['documented_elements']}"
        )
        print(
            f"✅ Function doc percentage: {function_result['summary']['documentation_percentage']}%"
        )

        # Test 4: Show undocumented public APIs
        print("\n📝 Test 4: Undocumented public APIs")
        if result["undocumented_public_apis"]:
            print(
                f"✅ Found {len(result['undocumented_public_apis'])} undocumented public APIs"
            )
            for api in result["undocumented_public_apis"][:5]:  # Show first 5
                print(
                    f"   - {api['element_type']} {api['element_name']} in {api['file_path']}"
                )
        else:
            print("✅ No undocumented public APIs found!")

        # Test 5: Show recommendations
        print("\n💡 Test 5: Documentation recommendations")
        if result["recommendations"]:
            print("✅ Recommendations:")
            for rec in result["recommendations"]:
                print(f"   {rec}")
        else:
            print("✅ No specific recommendations")

        # Test 6: Coverage by file
        print("\n📁 Test 6: Coverage by file")
        if result["coverage_by_file"]:
            print("✅ Files with lowest documentation coverage:")
            for file_info in result["coverage_by_file"][:5]:
                print(
                    f"   - {file_info['file_path']}: {file_info['coverage_percentage']}% "
                    f"({file_info['documented_elements']}/{file_info['total_elements']})"
                )

        print("\n🎉 All tests completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Error testing get_documentation: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    success = await test_get_documentation()
    if success:
        print("\n✅ get_documentation implementation working correctly!")
    else:
        print("\n❌ get_documentation implementation has issues")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
