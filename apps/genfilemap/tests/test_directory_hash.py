
"""
Tests for directory hashing functionality.

This module contains tests for the directory-level hashing optimization feature,
which allows GenFileMap to only process directories that have changed.
"""

import os
import json
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from genfilemap.core.directory_hash import (
    DirectoryHashInfo,
    compute_file_hash,
    compute_directory_hashes,
    load_hash_cache,
    save_hash_cache,
    find_changed_directories
)
from genfilemap.core.directory_hash_processing import process_files_with_directory_hashing


class TestDirectoryHashing(unittest.TestCase):
    """Test cases for directory hashing functionality."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Create some subdirectories and files
        self.subdirs = [
            os.path.join(self.temp_dir, 'subdir1'),
            os.path.join(self.temp_dir, 'subdir2'),
            os.path.join(self.temp_dir, 'subdir2', 'subsubdir')
        ]
        
        for subdir in self.subdirs:
            os.makedirs(subdir, exist_ok=True)
        
        # Create test files
        self.files = {
            'root_file.txt': os.path.join(self.temp_dir, 'root_file.txt'),
            'subdir1_file.txt': os.path.join(self.temp_dir, 'subdir1', 'subdir1_file.txt'),
            'subdir2_file.txt': os.path.join(self.temp_dir, 'subdir2', 'subdir2_file.txt'),
            'subsubdir_file.txt': os.path.join(self.temp_dir, 'subdir2', 'subsubdir', 'subsubdir_file.txt')
        }
        
        # Create files with content
        for filename, filepath in self.files.items():
            with open(filepath, 'w') as f:
                f.write(f"Content of {filename}\n")
        
        # Create a temporary cache file
        self.cache_file = os.path.join(self.temp_dir, 'hash_cache.json')
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_compute_file_hash(self):
        """Test computing a hash for a single file."""
        # Compute hash for a test file
        file_hash = compute_file_hash(self.files['root_file.txt'])
        
        # Assert the hash is a non-empty string
        self.assertIsNotNone(file_hash)
        self.assertIsInstance(file_hash, str)
        self.assertTrue(len(file_hash) > 0)
        
        # Create a copy of the file with different content
        with open(self.files['root_file.txt'] + '.copy', 'w') as f:
            f.write("Different content\n")
        
        # Compute hash for the copy
        copy_hash = compute_file_hash(self.files['root_file.txt'] + '.copy')
        
        # Assert the hashes are different
        self.assertNotEqual(file_hash, copy_hash)
    
    def test_directory_hash_info(self):
        """Test DirectoryHashInfo class."""
        # Create a hash info object
        hash_info = DirectoryHashInfo(
            path=self.temp_dir,
            local_hash="localhash123",
            recursive_hash="rechash456"
        )
        
        # Test properties
        self.assertEqual(hash_info.path, self.temp_dir)
        self.assertEqual(hash_info.local_hash, "localhash123")
        self.assertEqual(hash_info.recursive_hash, "rechash456")
        self.assertEqual(hash_info.file_hashes, {})
        self.assertEqual(hash_info.subdir_hashes, {})
        
        # Test to_dict method
        hash_dict = hash_info.to_dict()
        self.assertEqual(hash_dict['path'], self.temp_dir)
        self.assertEqual(hash_dict['local_hash'], "localhash123")
        self.assertEqual(hash_dict['recursive_hash'], "rechash456")
        self.assertEqual(hash_dict['file_hashes'], {})
        self.assertEqual(hash_dict['subdir_hashes'], {})
    
    def test_compute_directory_hashes(self):
        """Test computing hashes for a directory."""
        # Compute hashes for the test directory
        hash_info = compute_directory_hashes(self.temp_dir)
        
        # Assert basic properties
        self.assertIsNotNone(hash_info)
        self.assertEqual(hash_info.path, os.path.abspath(self.temp_dir))
        self.assertIsNotNone(hash_info.local_hash)
        self.assertIsNotNone(hash_info.recursive_hash)
        
        # Assert file hashes
        self.assertEqual(len(hash_info.file_hashes), 1)  # root_file.txt
        self.assertIn('root_file.txt', hash_info.file_hashes)
        
        # Assert subdirectory hashes
        self.assertEqual(len(hash_info.subdir_hashes), 2)  # subdir1 and subdir2
        self.assertIn('subdir1', hash_info.subdir_hashes)
        self.assertIn('subdir2', hash_info.subdir_hashes)
        
        # Assert subdir2 has a subdirectory
        subdir2_info = hash_info.subdir_hashes['subdir2']
        self.assertIn('subsubdir', subdir2_info.subdir_hashes)
    
    def test_save_and_load_hash_cache(self):
        """Test saving and loading the hash cache."""
        # Compute hashes for the test directory
        hash_info = compute_directory_hashes(self.temp_dir)
        
        # Create a cache
        cache = {hash_info.path: hash_info}
        
        # Save the cache
        success = save_hash_cache(cache, self.cache_file)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.cache_file))
        
        # Load the cache
        loaded_cache = load_hash_cache(self.cache_file)
        
        # Assert the cache was loaded correctly
        self.assertEqual(len(loaded_cache), 1)
        self.assertIn(hash_info.path, loaded_cache)
        
        # Assert the loaded hash info has the same properties
        loaded_info = loaded_cache[hash_info.path]
        self.assertEqual(loaded_info.path, hash_info.path)
        self.assertEqual(loaded_info.local_hash, hash_info.local_hash)
        self.assertEqual(loaded_info.recursive_hash, hash_info.recursive_hash)
        
        # Assert subdirectories were loaded
        self.assertEqual(len(loaded_info.subdir_hashes), 2)
        self.assertIn('subdir1', loaded_info.subdir_hashes)
        self.assertIn('subdir2', loaded_info.subdir_hashes)
    
    def test_find_changed_directories_no_changes(self):
        """Test finding changed directories when nothing has changed."""
        # Compute hashes for the test directory
        hash_info = compute_directory_hashes(self.temp_dir)
        
        # Create a cache
        cache = {hash_info.path: hash_info}
        
        # Find changed directories
        changed_dirs = find_changed_directories(self.temp_dir, cache)
        
        # Assert no directories have changed
        self.assertEqual(len(changed_dirs), 0)
    
    def test_find_changed_directories_with_changes(self):
        """Test finding changed directories when files have changed."""
        # Compute hashes for the test directory
        hash_info = compute_directory_hashes(self.temp_dir)
        
        # Create a cache
        cache = {hash_info.path: hash_info}
        
        # Modify a file in subdir1
        with open(self.files['subdir1_file.txt'], 'w') as f:
            f.write("Modified content\n")
        
        # Find changed directories
        changed_dirs = find_changed_directories(self.temp_dir, cache)
        
        # Assert only subdir1 has changed
        self.assertEqual(len(changed_dirs), 1)
        self.assertIn(os.path.abspath(self.subdirs[0]), changed_dirs)
    
    def test_find_changed_directories_new_dir(self):
        """Test finding changed directories when a new directory is added."""
        # Compute hashes for the test directory
        hash_info = compute_directory_hashes(self.temp_dir)
        
        # Create a cache
        cache = {hash_info.path: hash_info}
        
        # Create a new directory with a file
        new_dir = os.path.join(self.temp_dir, 'new_dir')
        os.makedirs(new_dir, exist_ok=True)
        with open(os.path.join(new_dir, 'new_file.txt'), 'w') as f:
            f.write("New file content\n")
        
        # Find changed directories
        changed_dirs = find_changed_directories(self.temp_dir, cache)
        
        # Assert the root directory has changed (because it contains the new directory)
        self.assertIn(os.path.abspath(self.temp_dir), changed_dirs)
    
    @patch('genfilemap.core.processing.process_files_async')
    def test_process_files_with_directory_hashing(self, mock_process_files_async):
        """Test processing files with directory hashing."""
        # Mock the process_files_async function to return True
        mock_process_files_async.return_value = True
        
        # Create a configuration
        config = {
            "path": self.temp_dir,
            "file_processing.recursive": True,
            "performance.use_dir_hashing": True,
            "app_dir": self.temp_dir
        }
        
        # Process files with directory hashing
        success = process_files_with_directory_hashing(config)
        
        # Assert processing was successful
        self.assertTrue(success)
        
        # Assert process_files_async was called
        mock_process_files_async.assert_called()
        
        # Assert the cache file was created
        cache_dir = os.path.join(self.temp_dir, "cache")
        self.assertTrue(os.path.exists(cache_dir))
        
        # Modify a file and process again
        with open(self.files['subdir2_file.txt'], 'w') as f:
            f.write("Modified content in subdir2\n")
        
        # Reset the mock
        mock_process_files_async.reset_mock()
        
        # Process files again
        success = process_files_with_directory_hashing(config)
        
        # Assert processing was successful
        self.assertTrue(success)
        
        # Assert process_files_async was called with the correct directory
        for call_args in mock_process_files_async.call_args_list:
            args, kwargs = call_args
            dir_config = args[0]
            # One of the calls should be for subdir2
            if dir_config["path"] == os.path.abspath(self.subdirs[1]):
                break
        else:
            self.fail("process_files_async was not called with subdir2")


if __name__ == '__main__':
    unittest.main() 