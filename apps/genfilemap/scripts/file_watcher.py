
#!/usr/bin/env python3
"""
Shell File Watcher for GenFileMap

This script watches for file changes and uses shell commands to run the
genfilemap tool directly, completely avoiding any Python import issues.
"""

import os
import sys
import time
import logging
import argparse
import subprocess
import shlex
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Constants
DEFAULT_DEBOUNCE_DELAY = 2.0  # seconds
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

class FileWatcher:
    """Main class for watching files and updating file maps."""
    
    def __init__(self, path, recursive=True, debounce_delay=DEFAULT_DEBOUNCE_DELAY, verbose=False,
                 include_extensions=None, exclude_extensions=None, min_file_size=100):
        """
        Initialize the file watcher.
        
        Args:
            path: Path to watch
            recursive: Whether to watch subdirectories
            debounce_delay: Time in seconds to wait before processing changes
            verbose: Whether to enable verbose logging
            include_extensions: List of file extensions to include
            exclude_extensions: List of file extensions to exclude
            min_file_size: Minimum file size in bytes
        """
        self.path = os.path.abspath(path)
        self.recursive = recursive
        self.debounce_delay = debounce_delay
        self.include_extensions = include_extensions or []
        self.exclude_extensions = exclude_extensions or []
        self.min_file_size = min_file_size
        
        # Set up logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(level=log_level, format=LOG_FORMAT)
        self.logger = logging.getLogger('shell_file_watcher')
        
        # Statistics
        self.stats = {
            'processed': 0,
            'skipped': 0,
            'errors': 0
        }
        
        # Set up the file event handler and observer
        self.event_handler = FileEventHandler(self)
        self.observer = None
        self.running = False
        self.start_time = None
        
        # Print initial configuration
        self.logger.info(f"File watcher configured with settings:")
        self.logger.info(f"  - Path: {self.path}")
        self.logger.info(f"  - Recursive: {self.recursive}")
        self.logger.info(f"  - Debounce delay: {self.debounce_delay}s")
        self.logger.info(f"  - Include extensions: {self.include_extensions or 'default set'}")
        self.logger.info(f"  - Exclude extensions: {self.exclude_extensions}")
        self.logger.info(f"  - Minimum file size: {self.min_file_size} bytes")
    
    def start(self):
        """Start the file watcher."""
        self.running = True
        self.start_time = time.time()
        self.logger.info(f"Starting file watcher for {self.path} (recursive={self.recursive})")
        
        # Create and start the observer
        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.path, recursive=self.recursive)
        self.observer.start()
        
        self.logger.info("File watcher started. Press Ctrl+C to stop.")
        print(f"DECISION: File watcher now monitoring {self.path}" + (" and subdirectories" if self.recursive else ""))
    
    def stop(self):
        """Stop the file watcher."""
        self.running = False
        self.logger.info("Stopping file watcher...")
        print(f"DECISION: Shutting down file watcher")
        
        # Stop the observer
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        # Display statistics
        duration = time.time() - self.start_time
        self.logger.info(f"File watcher stopped after {duration:.2f} seconds")
        self.logger.info(f"Statistics: {self.stats}")
        print(f"DECISION: File watcher statistics - Processed: {self.stats['processed']}, Skipped: {self.stats['skipped']}, Errors: {self.stats['errors']}")
    
    def process_file(self, file_path):
        """
        Process a file to update its file map.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            True if the file was processed successfully, False otherwise
        """
        try:
            print(f"DECISION: Evaluating whether to process file: {file_path}")
            if not self.should_process_file(file_path):
                print(f"DECISION: Skipping file based on filtering criteria: {file_path}")
                return False
                
            self.logger.info(f"Processing file: {file_path}")
            print(f"DECISION: Processing file that passed all filter criteria: {file_path}")
            
            # Instead of just creating a hash file, actually call GenFileMap CLI
            try:
                # Use the GenFileMap CLI to process the file
                cmd = [
                    "genfilemap",
                    file_path  # Positional argument for the path
                    # Removed "-f" force flag to prevent unnecessary regeneration
                ]
                
                self.logger.debug(f"Running command: {' '.join(cmd)}")
                print(f"DECISION: Executing GenFileMap command for file: {file_path}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.logger.info(f"Successfully processed file: {file_path}")
                    self.stats['processed'] += 1
                    print(f"DECISION: Successfully processed file with GenFileMap: {file_path}")
                    return True
                else:
                    # If GenFileMap returns non-zero, it might be filtering out this file
                    # That's fine - it means the file shouldn't be processed
                    self.logger.debug(f"GenFileMap didn't process file: {result.stderr}")
                    self.stats['skipped'] += 1
                    print(f"DECISION: GenFileMap returned non-zero exit code, skipping file: {file_path}")
                    print(f"DECISION: GenFileMap stderr: {result.stderr.strip()}")
                    return False
                    
            except Exception as e:
                self.logger.error(f"Error processing file {file_path}: {str(e)}")
                self.stats['errors'] += 1
                print(f"DECISION: Error executing GenFileMap command: {str(e)}")
                return False
                
        except Exception as e:
            self.logger.error(f"Unexpected error processing file {file_path}: {str(e)}")
            self.stats['errors'] += 1
            print(f"DECISION: Unexpected error during file processing: {str(e)}")
            return False
    
    def should_process_file(self, file_path):
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
            print(f"DECISION: Skipping non-existent or unreadable file: {file_path}")
            return False
        
        # Skip hash files
        if file_path.endswith('.hash'):
            self.logger.debug(f"Skipping hash file: {file_path}")
            self.stats['skipped'] += 1
            print(f"DECISION: Skipping hash file: {file_path}")
            return False
        
        # Skip log files
        if file_path.endswith('.log'):
            self.logger.debug(f"Skipping log file: {file_path}")
            self.stats['skipped'] += 1
            print(f"DECISION: Skipping log file: {file_path}")
            return False
        
        # Get file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        print(f"DECISION: Evaluating file extension: {file_ext}")
        
        # Check include extensions if specified
        if self.include_extensions:
            if file_ext not in self.include_extensions:
                self.logger.debug(f"Skipping non-included file type: {file_path}")
                self.stats['skipped'] += 1
                print(f"DECISION: Skipping non-included file type (not in {self.include_extensions}): {file_path}")
                return False
            else:
                print(f"DECISION: File extension {file_ext} is in include list")
        else:
            # Default supported extensions if none specified
            default_supported_extensions = [
                # Code file types
                '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss', '.less',
                '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.go', '.rs', '.rb', '.php',
                '.swift', '.kt', '.scala', '.sh', '.bash', '.ps1', '.bat', '.cmd',
                # Documentation file types
                '.md', '.rst', '.txt', '.adoc', '.textile'
            ]
            
            if file_ext not in default_supported_extensions:
                self.logger.debug(f"Skipping unsupported file type: {file_path}")
                self.stats['skipped'] += 1
                print(f"DECISION: Skipping unsupported file type: {file_ext}")
                return False
            else:
                print(f"DECISION: File extension {file_ext} is in default supported extensions")
        
        # Check exclude extensions
        if self.exclude_extensions and file_ext in self.exclude_extensions:
            self.logger.debug(f"Skipping excluded file type: {file_path}")
            self.stats['skipped'] += 1
            print(f"DECISION: Skipping file with excluded extension {file_ext}")
            return False
        
        # Skip common binary and temporary files
        skip_extensions = ['.exe', '.dll', '.so', '.pyc', '.pyo', '.o', '.swp', '.tmp']
        if any(file_path.endswith(ext) for ext in skip_extensions):
            self.logger.debug(f"Skipping file with ignored extension: {file_path}")
            self.stats['skipped'] += 1
            print(f"DECISION: Skipping file with ignored binary/temp extension: {file_path}")
            return False
        
        # Skip files in directories that should be ignored
        ignore_dirs = ['.git', '__pycache__', 'node_modules', 'venv', '.venv']
        if any(f'/{d}/' in file_path or file_path.endswith(f'/{d}') for d in ignore_dirs):
            self.logger.debug(f"Skipping file in ignored directory: {file_path}")
            self.stats['skipped'] += 1
            print(f"DECISION: Skipping file in ignored directory: {file_path}")
            return False
        
        # Check minimum file size
        try:
            file_size = os.path.getsize(file_path)
            if file_size < self.min_file_size:
                self.logger.debug(f"Skipping small file: {file_path} ({file_size} bytes)")
                self.stats['skipped'] += 1
                print(f"DECISION: Skipping small file: {file_path} ({file_size} bytes < {self.min_file_size} bytes)")
                return False
            else:
                print(f"DECISION: File size {file_size} bytes meets minimum requirement of {self.min_file_size} bytes")
        except Exception as e:
            self.logger.debug(f"Error checking file size, will try to process anyway: {str(e)}")
            print(f"DECISION: Error checking file size, will try to process anyway: {str(e)}")
            
        print(f"DECISION: File {file_path} passes all filters, will be processed")
        return True


class FileEventHandler(FileSystemEventHandler):
    """Handler for file system events."""
    
    def __init__(self, watcher):
        """
        Initialize the file event handler.
        
        Args:
            watcher: The FileWatcher instance
        """
        self.watcher = watcher
        self.logger = watcher.logger
        self.last_events = {}
        super().__init__()
    
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            print(f"DECISION: Ignoring directory creation event: {event.src_path}")
            return
        
        print(f"DECISION: File creation detected: {event.src_path}")
        self._process_event('created', event.src_path)
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            print(f"DECISION: Ignoring directory modification event: {event.src_path}")
            return
        
        print(f"DECISION: File modification detected: {event.src_path}")
        self._process_event('modified', event.src_path)
    
    def _process_event(self, event_type, file_path):
        """
        Process a file event with debouncing.
        
        Args:
            event_type: Type of event ('created' or 'modified')
            file_path: Path to the file
        """
        # Simple debouncing using timestamps
        current_time = time.time()
        key = (event_type, file_path)
        
        # Check if we've seen this event recently
        if key in self.last_events:
            time_since_last = current_time - self.last_events[key]
            if time_since_last < self.watcher.debounce_delay:
                self.logger.debug(f"Debouncing {event_type} event for {file_path}")
                print(f"DECISION: Debouncing event (time since last: {time_since_last:.2f}s < {self.watcher.debounce_delay}s): {file_path}")
                self.last_events[key] = current_time
                return
            else:
                print(f"DECISION: Event passes debounce (time since last: {time_since_last:.2f}s >= {self.watcher.debounce_delay}s)")
        else:
            print(f"DECISION: First time seeing this event, no debouncing needed")
        
        # Update the last event time
        self.last_events[key] = current_time
        
        # Process the file
        self.logger.info(f"File {event_type}: {file_path}")
        print(f"DECISION: Processing file after {event_type} event: {file_path}")
        self.watcher.process_file(file_path)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Shell-based file watcher for GenFileMap"
    )
    
    parser.add_argument(
        "path", nargs="?", default=".",
        help="Path to watch (default: current directory)"
    )
    
    parser.add_argument(
        "--recursive", "-r", action="store_true",
        help="Watch directories recursively"
    )
    
    parser.add_argument(
        "--debounce", type=float, dest="debounce_delay", default=DEFAULT_DEBOUNCE_DELAY,
        help=f"Debounce delay in seconds (default: {DEFAULT_DEBOUNCE_DELAY})"
    )
    
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--include", "-i", type=str, 
        help="Comma-separated list of file extensions to include (e.g., '.py,.js,.md')"
    )
    
    parser.add_argument(
        "--exclude", "-e", type=str,
        help="Comma-separated list of file extensions to exclude"
    )
    
    parser.add_argument(
        "--min-size", type=int, default=100,
        help="Minimum file size in bytes (default: 100)"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    print(f"DECISION: Starting file watcher with arguments: {args}")
    
    # Create and start the file watcher
    watcher = FileWatcher(
        args.path,
        recursive=args.recursive,
        debounce_delay=args.debounce_delay,
        verbose=args.verbose,
        include_extensions=args.include.split(',') if args.include else None,
        exclude_extensions=args.exclude.split(',') if args.exclude else None,
        min_file_size=args.min_size
    )
    
    try:
        # Start the watcher
        watcher.start()
        
        print(f"DECISION: Entering main loop to watch for file changes")
        # Keep the main thread running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        print(f"DECISION: User keyboard interrupt detected, shutting down")
    finally:
        # Clean up
        watcher.stop()
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 