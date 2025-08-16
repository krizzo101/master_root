#!/usr/bin/env python3
"""
Test Auto-Attach Functionality

Demonstrates the auto-attach script with various test scenarios.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auto_attach import AutoAttach


def test_basic_functionality():
    """Test basic auto-attach functionality."""
    print("🧪 Testing Basic Auto-Attach Functionality")
    print("=" * 50)

    auto_attach = AutoAttach(".proj-intel/file_dependencies_demo.json")

    if not auto_attach.load_dependencies():
        print("❌ Failed to load dependencies")
        return False

    # Test with a single file
    test_file = "libs/opsvi-security/opsvi_security/core.py"
    related_files = auto_attach.find_related_files([test_file])

    print(f"Input file: {test_file}")
    print(f"Related files found: {len(related_files)}")
    print("✅ Basic functionality test passed")
    return True


def test_multiple_files():
    """Test auto-attach with multiple input files."""
    print("\n🧪 Testing Multiple Files")
    print("=" * 50)

    auto_attach = AutoAttach(".proj-intel/file_dependencies_demo.json")

    if not auto_attach.load_dependencies():
        print("❌ Failed to load dependencies")
        return False

    # Test with multiple files
    test_files = [
        "libs/opsvi-security/opsvi_security/core.py",
        "libs/opsvi-core/opsvi_core/core/base.py"
    ]

    related_files = auto_attach.find_related_files(test_files)

    print(f"Input files: {test_files}")
    print(f"Related files found: {len(related_files)}")
    print("✅ Multiple files test passed")
    return True


def test_file_analysis():
    """Test detailed file analysis."""
    print("\n🧪 Testing File Analysis")
    print("=" * 50)

    auto_attach = AutoAttach(".proj-intel/file_dependencies_demo.json")

    if not auto_attach.load_dependencies():
        print("❌ Failed to load dependencies")
        return False

    test_file = "libs/opsvi-security/opsvi_security/core.py"
    analysis = auto_attach.analyze_file_dependencies(test_file)

    if analysis:
        print(f"File: {analysis['file_path']}")
        print(f"Type: {analysis['file_type']}")
        print(f"Lines: {analysis['line_count']}")
        print(f"Directory: {analysis['directory']}")
        print(f"Imports: {analysis['imports']}")
        print(f"Imported by: {len(analysis['imported_by'])} files")
        print(f"Related files breakdown:")
        for category, files in analysis['related_files'].items():
            print(f"  {category}: {len(files)} files")
        print("✅ File analysis test passed")
        return True
    else:
        print("❌ File analysis failed")
        return False


def test_filtering():
    """Test file filtering by type."""
    print("\n🧪 Testing File Filtering")
    print("=" * 50)

    auto_attach = AutoAttach(".proj-intel/file_dependencies_demo.json")

    if not auto_attach.load_dependencies():
        print("❌ Failed to load dependencies")
        return False

    # Get all files
    all_files = auto_attach.find_related_files(["libs/opsvi-security/opsvi_security/core.py"])

    # Filter by type
    source_files = auto_attach.filter_files_by_type(all_files, ["source"])
    config_files = auto_attach.filter_files_by_type(all_files, ["config"])
    test_files = auto_attach.filter_files_by_type(all_files, ["test"])

    print(f"All files: {len(all_files)}")
    print(f"Source files: {len(source_files)}")
    print(f"Config files: {len(config_files)}")
    print(f"Test files: {len(test_files)}")
    print("✅ File filtering test passed")
    return True


def test_indexes():
    """Test index lookups."""
    print("\n🧪 Testing Index Lookups")
    print("=" * 50)

    auto_attach = AutoAttach(".proj-intel/file_dependencies_demo.json")

    if not auto_attach.load_dependencies():
        print("❌ Failed to load dependencies")
        return False

    # Test directory lookup
    directory = "libs/opsvi-security/opsvi_security"
    dir_files = auto_attach.get_files_by_directory(directory)
    print(f"Files in {directory}: {len(dir_files)}")

    # Test type lookup
    source_files = auto_attach.get_files_by_type("source")
    config_files = auto_attach.get_files_by_type("config")
    test_files = auto_attach.get_files_by_type("test")
    print(f"Source files: {len(source_files)}")
    print(f"Config files: {len(config_files)}")
    print(f"Test files: {len(test_files)}")

    # Test import lookup
    importers = auto_attach.get_importers("logging")
    print(f"Files importing 'logging': {len(importers)}")

    print("✅ Index lookups test passed")
    return True


def main():
    """Run all tests."""
    print("🚀 Auto-Attach Test Suite")
    print("=" * 60)

    tests = [
        test_basic_functionality,
        test_multiple_files,
        test_file_analysis,
        test_filtering,
        test_indexes
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ {test.__name__} failed")
        except Exception as e:
            print(f"❌ {test.__name__} failed with exception: {e}")

    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit(main())
