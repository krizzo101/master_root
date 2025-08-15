"""Progress reporting utilities for Project Mapper.

This module provides progress reporting functionality for long-running operations.
"""

import sys
import time
import logging
import os
from enum import Enum
from typing import Optional, Callable, Dict, Any, List, Tuple, Union
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.progress import (
    Progress, 
    BarColumn, 
    TextColumn, 
    TimeElapsedColumn, 
    TimeRemainingColumn,
    SpinnerColumn
)
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log levels for progress reporting."""
    
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LogHandler:
    """Handles logging configuration for the Project Mapper CLI."""
    
    def __init__(self, 
                 console: Optional[Console] = None,
                 verbose: bool = False,
                 debug_mode: bool = False):
        """Initialize the log handler.
        
        Args:
            console: Console to use for output
            verbose: Whether to show verbose output
            debug_mode: Whether to enable debug logging to file
        """
        self.console = console or Console()
        self.verbose = verbose
        self.debug_mode = debug_mode
        
        # Configure logging
        self._configure_logging()
    
    def _configure_logging(self) -> None:
        """Configure logging with Rich handler and optional debug file handler."""
        # Set console level to INFO or WARNING, ensuring debug output never goes to console
        console_level = logging.INFO if self.verbose else logging.WARNING
        
        # Create console handler with rich formatting - debug messages will never go here
        console_handler = RichHandler(
            console=self.console,
            rich_tracebacks=True,
            tracebacks_show_locals=self.verbose,
            omit_repeated_times=True,
            level=console_level  # Never set to DEBUG
        )
        
        # Create handlers list
        handlers = [console_handler]
        
        # Set up debug file handler if debug mode is enabled
        if self.debug_mode:
            # Create log directory if it doesn't exist
            log_dir = Path('./log')
            log_dir.mkdir(exist_ok=True)
            
            # Create file handler for debug logs
            debug_file_handler = logging.FileHandler(
                filename=log_dir / 'debug.log', 
                mode='w',  # Overwrite existing log file
                encoding='utf-8'
            )
            debug_file_handler.setLevel(logging.DEBUG)
            
            # Create detailed formatter for debug logs
            detailed_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            debug_file_handler.setFormatter(detailed_formatter)
            
            # Add file handler to handlers list
            handlers.append(debug_file_handler)
            
            # Log that debug mode is enabled - only to file, not console
            debug_logger = logging.getLogger('proj_mapper')
            debug_logger.setLevel(logging.DEBUG)
            
            # Remove any existing handlers to avoid duplicates
            for handler in debug_logger.handlers[:]:
                debug_logger.removeHandler(handler)
                
            # Add only the file handler
            debug_logger.addHandler(debug_file_handler)
            debug_logger.propagate = False  # Don't propagate to root logger
            debug_logger.debug("Debug mode enabled - detailed logging to ./log/debug.log")
        
        # Configure root logger
        root_logger = logging.getLogger()
        
        # Remove any existing handlers to avoid duplicates
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Set root logger level to DEBUG if debug mode is enabled, to ensure messages are captured
        root_level = logging.DEBUG if self.debug_mode else console_level
        root_logger.setLevel(root_level)
        
        # Add handlers to root logger
        for handler in handlers:
            root_logger.addHandler(handler)

    def set_log_level(self, level: int) -> None:
        """Set the log level.
        
        Args:
            level: Log level to set
        """
        # Set root logger level
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # Update console handler level - never go below INFO for console
        console_level = max(level, logging.INFO) if self.debug_mode else level
        for handler in root_logger.handlers:
            if isinstance(handler, RichHandler):
                handler.setLevel(console_level)
            # File handlers keep their original level
            elif isinstance(handler, logging.FileHandler) and level == logging.DEBUG:
                # Ensure file handlers can receive debug messages when debug is enabled
                handler.setLevel(logging.DEBUG)


class ProgressReporter:
    """Reports progress of long-running operations."""
    
    def __init__(self, 
                 console: Optional[Console] = None,
                 quiet: bool = False,
                 verbose: bool = False,
                 log_dir: str = './log'):
        """Initialize the progress reporter.
        
        Args:
            console: Console to use for output
            quiet: Whether to suppress output
            verbose: Whether to show verbose output
            log_dir: Directory for log files
        """
        self.console = console or Console(file=open(os.devnull, 'w'))  # Suppress rich console output
        self.quiet = quiet
        self.verbose = verbose
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self._progress = None
        self._tasks = {}
        
        # Configure logging
        self._configure_logging()
    
    def _configure_logging(self) -> None:
        """Configure logging with file output."""
        # Create progress log file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        progress_log = self.log_dir / f"progress_{timestamp}.log"
        
        # Create file handler
        file_handler = logging.FileHandler(progress_log, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Get logger
        logger = logging.getLogger('proj_mapper.progress')
        
        # Remove any existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Add file handler
        logger.addHandler(file_handler)
        
        # Set level
        logger.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        
        # If not quiet, add minimal console output
        if not self.quiet:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter('%(message)s')
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        logger.info(f"Progress will be logged to: {progress_log}")
    
    def log(self, 
            message: str, 
            level: Union[LogLevel, int] = LogLevel.INFO) -> None:
        """Log a message.
        
        Args:
            message: Message to log
            level: Log level
        """
        if isinstance(level, LogLevel):
            level = level.value
        
        logger.log(level, message)
        
        # Write to progress file
        if self._progress and not self.quiet:
            self._progress.console.print(message)
    
    def start_progress(self, total: int = 100, description: str = "Processing") -> None:
        """Start a new progress bar.
        
        Args:
            total: Total number of steps
            description: Description of the operation
        """
        if self.quiet:
            return
        
        # Create a new progress bar
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console
        )
        
        # Start the progress display
        self._progress.start()
        
        # Create the main task
        self._main_task_id = self._progress.add_task(description, total=total)
        self._tasks[description] = self._main_task_id
    
    def update_progress(self, 
                       advance: int = 1, 
                       description: Optional[str] = None,
                       task_name: Optional[str] = None) -> None:
        """Update the progress bar.
        
        Args:
            advance: Number of steps to advance
            description: New description for the task
            task_name: Name of the task to update (main task if None)
        """
        if self.quiet or self._progress is None:
            return
        
        task_id = self._tasks.get(task_name, self._main_task_id)
        
        # Update the task
        if description is not None:
            self._progress.update(task_id, description=description, advance=advance)
        else:
            self._progress.update(task_id, advance=advance)
    
    def add_subtask(self, 
                   name: str, 
                   total: int, 
                   description: str) -> None:
        """Add a subtask to the progress bar.
        
        Args:
            name: Unique name for the subtask
            total: Total number of steps for the subtask
            description: Description of the subtask
        """
        if self.quiet or self._progress is None:
            return
        
        task_id = self._progress.add_task(description, total=total)
        self._tasks[name] = task_id
    
    def complete_subtask(self, name: str) -> None:
        """Mark a subtask as complete.
        
        Args:
            name: Name of the subtask
        """
        if self.quiet or self._progress is None:
            return
        
        task_id = self._tasks.get(name)
        if task_id is not None:
            self._progress.update(task_id, completed=True)
    
    def stop_progress(self) -> None:
        """Stop the progress bar."""
        if self.quiet or self._progress is None:
            return
        
        self._progress.stop()
        self._progress = None
        self._tasks = {}
    
    def display_result(self, 
                      title: str, 
                      data: Dict[str, Any],
                      expand: bool = False) -> None:
        """Display a result table.
        
        Args:
            title: Title for the result
            data: Data to display
            expand: Whether to expand nested dictionaries
        """
        if self.quiet:
            return
        
        # Create a table
        table = Table(title=title)
        table.add_column("Key", style="bold cyan")
        table.add_column("Value")
        
        # Add rows
        for key, value in data.items():
            if isinstance(value, dict) and expand:
                # Format nested dictionary
                nested_value = "\n".join(f"{k}: {v}" for k, v in value.items())
                table.add_row(key, nested_value)
            else:
                table.add_row(key, str(value))
        
        # Display the table
        self.console.print(table)
    
    def display_summary(self, 
                       title: str, 
                       items: List[Union[str, Tuple[str, str]]]) -> None:
        """Display a summary panel.
        
        Args:
            title: Title for the summary
            items: Items to display (strings or key-value tuples)
        """
        if self.quiet:
            return
        
        # Format items
        if all(isinstance(item, tuple) for item in items):
            # Key-value pairs
            content = "\n".join([f"[bold]{k}[/bold]: {v}" for k, v in items])
        else:
            # Simple list
            content = "\n".join([f"• {item}" for item in items])
        
        # Create and display panel
        panel = Panel(content, title=title, border_style="blue")
        self.console.print(panel)
    
    def create_spinner(self, 
                      text: str, 
                      callback: Callable[[], Any],
                      finish_text: Optional[str] = None) -> Any:
        """Execute a function with a spinner.
        
        Args:
            text: Text to display with the spinner
            callback: Function to execute
            finish_text: Text to display when done
            
        Returns:
            Result from the callback
        """
        if self.quiet:
            return callback()
        
        with self.console.status(text) as status:
            result = callback()
            if finish_text:
                status.update(finish_text)
        
        return result 