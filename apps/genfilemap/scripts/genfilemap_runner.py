
#!/usr/bin/env python3
"""
GenFileMap CLI Runner

This script provides a simple command-line interface for running GenFileMap
operations via subprocess, avoiding any circular import issues.
"""

import sys
import subprocess
import argparse
import os.path
from pathlib import Path


def update_file(file_path, force=False):
    """
    Update the file map for a single file.
    
    Args:
        file_path: Path to the file to update
        force: Whether to force update even if hash matches
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Build the command to run genfilemap directly as installed package
        cmd = [
            "genfilemap",
            "update",
            "--file", file_path
        ]
        
        if force:
            cmd.append("--force")
            
        # Run the command
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ Successfully updated file map for: {file_path}")
            print(result.stdout)
            return True
        else:
            print(f"✗ Error updating file map: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def update_directory(directory_path, recursive=False, force=False):
    """
    Update file maps for all files in a directory.
    
    Args:
        directory_path: Path to the directory
        recursive: Whether to process subdirectories
        force: Whether to force update even if hash matches
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Build the command to run genfilemap directly as installed package
        cmd = [
            "genfilemap",
            "update",
            "--directory", directory_path
        ]
        
        if recursive:
            cmd.append("--recursive")
            
        if force:
            cmd.append("--force")
            
        # Run the command
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ Successfully updated file maps in: {directory_path}")
            print(result.stdout)
            return True
        else:
            print(f"✗ Error updating file maps: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="GenFileMap CLI Runner"
    )
    
    # Command subparsers
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update file maps")
    update_parser.add_argument("--file", help="Path to the file to update")
    update_parser.add_argument("--directory", help="Path to the directory to update")
    update_parser.add_argument("--recursive", "-r", action="store_true", help="Process subdirectories")
    update_parser.add_argument("--force", "-f", action="store_true", help="Force update even if hash matches")
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    if args.command == "update":
        if args.file:
            file_path = os.path.abspath(args.file)
            if not os.path.isfile(file_path):
                print(f"Error: File not found: {file_path}")
                return 1
                
            return 0 if update_file(file_path, args.force) else 1
            
        elif args.directory:
            dir_path = os.path.abspath(args.directory)
            if not os.path.isdir(dir_path):
                print(f"Error: Directory not found: {dir_path}")
                return 1
                
            return 0 if update_directory(dir_path, args.recursive, args.force) else 1
            
        else:
            print("Error: Either --file or --directory must be specified for the update command")
            return 1
    else:
        print("Error: No command specified")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 