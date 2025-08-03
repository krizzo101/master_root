
"""
File Watcher for GenFileMap

This module provides functionality for watching files for changes and automatically
updating file maps as needed, using the watchdog library.
"""

import os
import sys
import time
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import threading

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from genfilemap.core import run_process
from genfilemap.core.file_operations import count_lines
from genfilemap.config import load_config, get_config_value

# Constants
DEFAULT_DEBOUNCE_DELAY = 2.0  # seconds
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

def load_file_config(file_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a configuration dictionary for a specific file.
    
    Args:
        file_path: Path to the file
        config: Base configuration dictionary
        
    Returns:
        Dictionary with file-specific configuration
    """
    return {
        "path": file_path,
        "recursive": False,
        "force": True,  # Always force processing in watcher mode
        "debug": config.get('debug', False),
        "dry_run": False,  # Explicitly set to False to override global config
        "clean": False
    }

def process_file_async(file_path: str, file_config: Dict[str, Any], event_type: Optional[str] = None) -> bool:
    """
    Process a file asynchronously.
    
    Args:
        file_path: Path to the file to process
        file_config: Configuration for file processing
        event_type: Type of event that triggered the processing
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"Running with config: path={file_path}, force={file_config.get('force', True)}, "
              f"dry_run={file_config.get('dry_run', False)}")
        
        # Process the file using the core module
        result = run_process(file_config)
        
        if result:
            print(f"Successfully processed file: {file_path}")
            return True
        else:
            print(f"Failed to process file: {file_path}")
            return False
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

class FileWatcher:
    """Main class for watching files and updating file maps."""
    
    def __init__(self, path: str, recursive: bool = True, debounce_delay: float = DEFAULT_DEBOUNCE_DELAY, 
                 verbose: bool = False, include_extensions: Optional[List[str]] = None, 
                 exclude_extensions: Optional[List[str]] = None, min_line_count: int = 50):
        """
        Initialize the file watcher.
        
        Args:
            path: Path to watch
            recursive: Whether to watch subdirectories
            debounce_delay: Time in seconds to wait before processing changes
            verbose: Whether to enable verbose logging
            include_extensions: List of file extensions to include
            exclude_extensions: List of file extensions to exclude
            min_line_count: Minimum number of lines for a file to be processed (default: 50)
                            This is used because AI tools typically read ~50 lines at a time,
                            so file maps are most useful for longer files that can't be read in one go.
        """
        self.path = os.path.abspath(path)
        self.recursive = recursive
        self.debounce_delay = debounce_delay
        self.include_extensions = include_extensions or []
        self.exclude_extensions = exclude_extensions or []
        self.min_line_count = min_line_count
        
        # Set up logging
        self.verbose = verbose
        self.log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(level=self.log_level, format=LOG_FORMAT)
        self.logger = logging.getLogger('genfilemap.file_watcher')
        
        # Statistics
        self.stats = {
            'processed': 0,
            'skipped': 0,
            'errors': 0
        }
        
        # Load configuration
        self.config = load_config()
        
        # Debounce tracking
        self.pending_events = {}
        self.debounce_timers = {}
        self.lock = threading.Lock()
        
        # Set up the file event handler and observer
        self.event_handler = FileEventHandler(self)
        self.observer = None
        self.running = False
        self.start_time = None
        
        # Print initial configuration
        print(f"\nFile watcher configured with settings:")
        print(f"  - Path: {self.path}")
        print(f"  - Recursive: {self.recursive}")
        print(f"  - Debounce delay: {self.debounce_delay}s")
        print(f"  - Include extensions: {self.include_extensions or 'default set'}")
        print(f"  - Exclude extensions: {self.exclude_extensions}")
        print(f"  - Minimum line count: {self.min_line_count} lines")
    
    def start(self):
        """Start the file watcher."""
        self.running = True
        self.start_time = time.time()
        print(f"Starting file watcher for {self.path} (recursive={self.recursive})")
        
        # Create and start the observer
        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.path, recursive=self.recursive)
        self.observer.start()
        
        print("File watcher started. Press Ctrl+C to stop.")
    
    def stop(self):
        """Stop the file watcher."""
        self.running = False
        print("Stopping file watcher...")
        
        # Stop the observer
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        # Display statistics
        duration = time.time() - self.start_time
        print(f"File watcher stopped after {duration:.2f} seconds")
        print(f"Statistics: Processed: {self.stats['processed']}, Skipped: {self.stats['skipped']}, Errors: {self.stats['errors']}")
    
    def process_file(self, file_path: str, event_type: int = None) -> None:
        """Process a single file asynchronously."""
        file_path = os.path.abspath(file_path)
        
        if not os.path.isfile(file_path):
            print(f"File {file_path} does not exist.")
            self.stats['skipped'] += 1
            return
            
        # Check if we should process this file
        if not self.should_process_file(file_path):
            return
            
        print(f"Processing file: {file_path}")
        
        # Load global config and file-specific config
        # Check if config is already a dict or has to_dict method
        config = self.config.to_dict() if hasattr(self.config, 'to_dict') else self.config
        file_config = load_file_config(file_path, config)
        
        # Debug output of configuration values being used
        print("\nConfiguration details:")
        print(f"  Global config 'dry_run': {config.get('dry_run', False)}")
        print(f"  Global config 'force': {config.get('force', False)}")
        print(f"  Global config 'debug': {config.get('debug', False)}")
        print("\n  File-specific config:")
        for key, value in file_config.items():
            print(f"    - {key}: {value}")
        
        try:
            result = process_file_async(file_path, file_config, event_type)
            if result:
                self.stats['processed'] += 1
            else:
                self.stats['errors'] += 1
        except Exception as e:
            self.logger.error(f"Unexpected error processing file {file_path}: {str(e)}")
            self.stats['errors'] += 1
    
    def should_process_file(self, file_path: str) -> bool:
        """
        Determine if a file should be processed.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file should be processed, False otherwise
        """
        # Skip files that don't exist or aren't readable
        if not os.path.isfile(file_path) or not os.access(file_path, os.R_OK):
            self.logger.debug(f"Skipping non-existent or unreadable file: {file_path}")
            self.stats['skipped'] += 1
            return False
        
        # Skip files with too few lines
        # This matters because the primary purpose of file maps is to help AI agents understand files
        # AI tools typically can read ~50 lines at a time, so files shorter than this don't benefit from maps
        try:
            line_count = count_lines(file_path)
            if line_count < self.min_line_count:
                self.logger.debug(f"Skipping file with fewer than {self.min_line_count} lines: {file_path} ({line_count} lines)")
                self.stats['skipped'] += 1
                return False
        except Exception as e:
            self.logger.warning(f"Error counting lines in file {file_path}: {str(e)}")
            self.stats['errors'] += 1
            return False
        
        # Skip hash files
        if file_path.endswith('.hash'):
            self.logger.debug(f"Skipping hash file: {file_path}")
            self.stats['skipped'] += 1
            return False
        
        # Get file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Check include extensions if specified
        if self.include_extensions:
            if file_ext not in self.include_extensions:
                self.logger.debug(f"Skipping non-included file type: {file_path}")
                self.stats['skipped'] += 1
                return False
        else:
            # Use file processing include from config
            include_extensions = get_config_value(self.config, "file_processing.include_extensions", [])
            if include_extensions and file_ext not in include_extensions:
                self.logger.debug(f"Skipping file type not in config includes: {file_path}")
                self.stats['skipped'] += 1
                return False
        
        # Check exclude extensions
        exclude_extensions = self.exclude_extensions or get_config_value(self.config, "file_processing.exclude_extensions", [])
        if exclude_extensions and file_ext in exclude_extensions:
            self.logger.debug(f"Skipping excluded file type: {file_path}")
            self.stats['skipped'] += 1
            return False
        
        # Skip files in common ignored directories
        ignore_dirs = ['.git', '__pycache__', 'node_modules', 'venv', '.venv', 'dist', 'build']
        if any(f'/{d}/' in file_path or file_path.endswith(f'/{d}') for d in ignore_dirs):
            self.logger.debug(f"Skipping file in ignored directory: {file_path}")
            self.stats['skipped'] += 1
            return False
        
        # Check if the file path contains any patterns from .fileignore
        ignore_file = get_config_value(self.config, "file_processing.ignore_file", ".fileignore")
        ignore_patterns = self._load_ignore_patterns(ignore_file)
        if self._is_ignored(file_path, ignore_patterns):
            self.logger.debug(f"Skipping file matching ignore pattern: {file_path}")
            self.stats['skipped'] += 1
            return False
        
        # All checks passed, this file should be processed
        return True
    
    def _load_ignore_patterns(self, ignore_file: str) -> List[str]:
        """
        Load ignore patterns from a file.
        
        Args:
            ignore_file: Path to the ignore file
            
        Returns:
            List of ignore patterns
        """
        patterns = []
        if os.path.isfile(ignore_file):
            try:
                with open(ignore_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            patterns.append(line)
            except Exception as e:
                self.logger.warning(f"Error reading ignore file {ignore_file}: {str(e)}")
        return patterns
    
    def _is_ignored(self, file_path: str, patterns: List[str]) -> bool:
        """
        Check if a file path matches any ignore patterns.
        
        Args:
            file_path: Path to check
            patterns: List of ignore patterns
            
        Returns:
            True if the file should be ignored, False otherwise
        """
        from fnmatch import fnmatch
        rel_path = os.path.relpath(file_path, self.path)
        
        for pattern in patterns:
            if fnmatch(rel_path, pattern) or fnmatch(os.path.basename(rel_path), pattern):
                return True
        return False
    
    def handle_event(self, event_type: str, file_path: str):
        """
        Handle a file event with debouncing.
        
        Args:
            event_type: Type of event ('created' or 'modified')
            file_path: Path to the file
        """
        with self.lock:
            # Cancel any existing timer for this file
            if file_path in self.debounce_timers:
                self.debounce_timers[file_path].cancel()
            
            # Create a new timer to process this file after the debounce delay
            timer = threading.Timer(
                self.debounce_delay,
                self._process_debounced_event,
                args=[file_path]
            )
            timer.daemon = True
            self.debounce_timers[file_path] = timer
            
            # Store the event type (use the most recent one)
            self.pending_events[file_path] = event_type
            
            # Start the timer
            timer.start()
            self.logger.debug(f"Scheduled {event_type} event for {file_path} with {self.debounce_delay}s delay")
    
    def _process_debounced_event(self, file_path: str):
        """
        Process a debounced file event.
        
        Args:
            file_path: Path to the file
        """
        with self.lock:
            event_type = self.pending_events.pop(file_path, None)
            self.debounce_timers.pop(file_path, None)
        
        if event_type:
            self.logger.debug(f"Processing debounced {event_type} event for {file_path}")
            self.process_file(file_path, event_type)


class FileEventHandler(FileSystemEventHandler):
    """Handler for file system events."""
    
    def __init__(self, watcher: FileWatcher):
        """
        Initialize the file event handler.
        
        Args:
            watcher: The FileWatcher instance
        """
        super().__init__()
        self.watcher = watcher
    
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory:
            self.watcher.logger.debug(f"File created: {event.src_path}")
            self.watcher.handle_event('created', event.src_path)
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            self.watcher.logger.debug(f"File modified: {event.src_path}")
            self.watcher.handle_event('modified', event.src_path)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Watch for file changes and automatically update file maps"
    )
    
    parser.add_argument(
        "path",
        type=str,
        nargs="?",
        default=".",
        help="Path to watch (default: current directory)"
    )
    
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Watch subdirectories recursively"
    )
    
    parser.add_argument(
        "--include",
        type=str,
        help="Comma-separated list of file extensions to include (e.g., '.py,.js,.md')"
    )
    
    parser.add_argument(
        "--exclude",
        type=str,
        help="Comma-separated list of file extensions to exclude (e.g., '.pyc,.tmp')"
    )
    
    parser.add_argument(
        "--debounce",
        type=float,
        default=DEFAULT_DEBOUNCE_DELAY,
        help=f"Debounce delay in seconds (default: {DEFAULT_DEBOUNCE_DELAY})"
    )
    
    parser.add_argument(
        "--min-lines",
        type=int,
        default=50,
        help="Minimum number of lines for a file to be processed (default: 50)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Parse include and exclude extensions if provided
    include_extensions = None
    if args.include:
        include_extensions = args.include.split(',')
    
    exclude_extensions = None
    if args.exclude:
        exclude_extensions = args.exclude.split(',')
    
    # Create and start the watcher
    watcher = FileWatcher(
        path=args.path,
        recursive=args.recursive,
        debounce_delay=args.debounce,
        verbose=args.verbose,
        include_extensions=include_extensions,
        exclude_extensions=exclude_extensions,
        min_line_count=args.min_lines
    )
    
    try:
        watcher.start()
        # Keep the main thread running
        while watcher.running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Stopping file watcher...")
    finally:
        watcher.stop()


if __name__ == "__main__":
    main() 