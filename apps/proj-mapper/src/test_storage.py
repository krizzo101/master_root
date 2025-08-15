"""Test script for storage functionality.

This script tests the storage module after refactoring.
"""

from proj_mapper.output.storage import StorageManager
from proj_mapper.output.config import GeneratorConfig, MapFormatType
from proj_mapper.output.storage.base import MapStorageProvider
from proj_mapper.output.storage.file_storage import LocalFileSystemStorage
from proj_mapper.output.storage.manager import StorageManager as DirectStorageManager

def test_imports():
    """Test that all imports work correctly."""
    # Test importing from base module
    assert StorageManager
    
    # Test importing from specific modules
    assert MapStorageProvider
    assert LocalFileSystemStorage
    assert DirectStorageManager
    
    print("Import tests passed.")

def test_instance_creation():
    """Test creating instances of storage classes."""
    # Test base provider creation
    try:
        provider = LocalFileSystemStorage(base_dir=".maps")
        print("LocalFileSystemStorage instance created successfully.")
    except Exception as e:
        print(f"Error creating LocalFileSystemStorage: {e}")
        return False
    
    # Test storage manager creation
    try:
        manager = StorageManager(storage_provider=provider)
        print("StorageManager instance created successfully.")
    except Exception as e:
        print(f"Error creating StorageManager: {e}")
        return False
    
    # Test direct import
    try:
        direct_manager = DirectStorageManager(storage_provider=provider)
        print("DirectStorageManager instance created successfully.")
    except Exception as e:
        print(f"Error creating DirectStorageManager: {e}")
        return False
    
    print("Instance creation tests passed.")
    return True

def main():
    """Run all tests."""
    print("Testing storage module...")
    test_imports()
    if test_instance_creation():
        print("All tests passed!")
    else:
        print("Tests failed.")

if __name__ == "__main__":
    main() 