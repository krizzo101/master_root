"""Debug tracing utilities for Project Mapper.

This module provides utilities for tracing and debugging issues with the Project Mapper.
It configures logging to route all debug output to a file while keeping the console clean.
"""

import sys
import os
import logging
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Callable

# Original excepthook
original_excepthook = sys.excepthook

class DebugTracer:
    """Manages debug tracing and enhanced exception handling."""
    
    def __init__(self, log_dir: str = './log', log_file: Optional[str] = None):
        """Initialize the debug tracer.
        
        Args:
            log_dir: Directory to store log files
            log_file: Log file name (default: debug_{timestamp}.log)
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Generate log file name if not provided
        if log_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = f"debug_{timestamp}.log"
        
        self.log_file = self.log_dir / log_file
        self.setup_logging()
        
        # Dictionary to store function hooks
        self.function_hooks: Dict[str, Callable] = {}
        
        # Logger for this class
        self.logger = logging.getLogger('proj_mapper.debug_tracer')
        self.logger.debug(f"Debug tracer initialized. Logging to {self.log_file}")
    
    def setup_logging(self):
        """Set up logging configuration to route debug output to file."""
        # Create root logger
        root_logger = logging.getLogger()
        
        # Remove any existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Set root level to DEBUG to capture everything
        root_logger.setLevel(logging.DEBUG)
        
        # Create file handler for debug logs
        file_handler = logging.FileHandler(
            filename=self.log_file, 
            mode='w',  # Overwrite existing file
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Create detailed formatter for debug logs
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(detailed_formatter)
        
        # Add handler to root logger
        root_logger.addHandler(file_handler)
        
        # Create a console handler with restricted level (INFO or higher)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Create simplified formatter for console
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # Add handler to root logger
        root_logger.addHandler(console_handler)
        
        return root_logger
    
    def enable_enhanced_exceptions(self):
        """Enable enhanced exception handling."""
        sys.excepthook = self._enhanced_excepthook
        return self
    
    def _enhanced_excepthook(self, exc_type, exc_value, exc_traceback):
        """Enhanced exception hook with more detailed logging."""
        # Format the exception and traceback
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        
        # Log the exception
        self.logger.error("Exception caught by enhanced excepthook:")
        for line in tb_lines:
            self.logger.error(line.rstrip())
        
        # Enhanced debug for particular error types
        if exc_type is AttributeError and "'str' object has no attribute" in str(exc_value):
            self.logger.error(f"DETECTED STRING ATTRIBUTE ERROR: {exc_value}")
            
            # Extract frames from the traceback
            frames = traceback.extract_tb(exc_traceback)
            if frames:
                last_frame = frames[-1]
                filename, lineno, funcname, line = last_frame
                self.logger.error(f"Error occurred in {filename} at line {lineno} in function {funcname}")
                if line:
                    self.logger.error(f"Code: {line}")
                    
                # Try to get variable values
                frame_obj = None
                for frame, _ in traceback.walk_tb(exc_traceback):
                    if frame.f_code.co_filename == filename and frame.f_lineno == lineno:
                        frame_obj = frame
                        break
                        
                if frame_obj:
                    self.logger.error("Local variables in the frame:")
                    for var_name, var_value in frame_obj.f_locals.items():
                        self.logger.error(f"  {var_name} = {repr(var_value)}")
                        
                        # Inspect relationship_type more closely
                        if "relationship_type" in var_name.lower() or "node_type" in var_name.lower():
                            self.logger.error(f"  -> Type: {type(var_value)}")
                            self.logger.error(f"  -> Dir: {dir(var_value)}")
                            if hasattr(var_value, "__dict__"):
                                self.logger.error(f"  -> Dict: {var_value.__dict__}")
        
        # Call the original excepthook
        original_excepthook(exc_type, exc_value, exc_traceback)
    
    def patch_function(self, module_name: str, function_name: str, wrapper: Callable):
        """Patch a function with a custom wrapper.
        
        Args:
            module_name: Name of the module containing the function
            function_name: Name of the function to patch
            wrapper: Wrapper function that takes (original_func, *args, **kwargs)
            
        Returns:
            True if patch was successful, False otherwise
        """
        try:
            import importlib
            module = importlib.import_module(module_name)
            original_func = getattr(module, function_name)
            
            # Create and apply the patch
            def patched_func(*args, **kwargs):
                return wrapper(original_func, *args, **kwargs)
            
            patched_func.__name__ = original_func.__name__
            patched_func.__doc__ = original_func.__doc__
            
            # Store the patch
            self.function_hooks[(module_name, function_name)] = (original_func, patched_func)
            
            # Apply the patch
            setattr(module, function_name, patched_func)
            self.logger.debug(f"Patched {module_name}.{function_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to patch {module_name}.{function_name}: {e}")
            self.logger.debug("Traceback:", exc_info=True)
            return False
    
    def restore_all_patches(self):
        """Restore all patched functions."""
        for (module_name, function_name), (original_func, _) in self.function_hooks.items():
            try:
                import importlib
                module = importlib.import_module(module_name)
                setattr(module, function_name, original_func)
                self.logger.debug(f"Restored {module_name}.{function_name}")
            except Exception as e:
                self.logger.error(f"Failed to restore {module_name}.{function_name}: {e}")
                self.logger.debug("Traceback:", exc_info=True)
        
        # Clear the function hooks
        self.function_hooks.clear()


def install_enum_patches(tracer: DebugTracer) -> bool:
    """Install patches to fix enum handling in relationship detection.
    
    Args:
        tracer: DebugTracer instance
        
    Returns:
        True if patches were successful, False otherwise
    """
    try:
        # Patch RelationshipType to handle .value correctly
        from proj_mapper.models.relationship import RelationshipType
        
        def enum_wrapper(original_getattribute, self, name):
            if name == 'value':
                # Log access to .value
                tracer.logger.debug(f"Enum.value accessed for {self}")
                
                # Get the caller information
                stack = traceback.extract_stack()
                if len(stack) > 1:
                    caller = stack[-2]
                    tracer.logger.debug(f"Called from {caller.filename}:{caller.lineno}")
                
                # Return the name instead of value for auto() enums
                return self.name
            return original_getattribute(self, name)
        
        # Patch the __getattribute__ method
        RelationshipType.__getattribute__ = lambda self, name: enum_wrapper(
            object.__getattribute__, self, name
        )
        
        tracer.logger.debug("Patched RelationshipType.__getattribute__")
        
        # Patch Edge.to_relationship to handle None values
        def patch_to_relationship(original_func, edge):
            try:
                return original_func(edge)
            except Exception as e:
                tracer.logger.error(f"Error in Edge.to_relationship: {e}")
                tracer.logger.debug(f"Edge: {edge}")
                tracer.logger.debug(f"Source: {edge.source}, Target: {edge.target}")
                tracer.logger.debug(f"Source data: {edge.source.data}")
                tracer.logger.debug(f"Target data: {edge.target.data}")
                
                # Create the relationship with safe values
                from proj_mapper.models.relationship import Relationship
                return Relationship(
                    source_id=edge.source.id,
                    source_type="unknown" if edge.source.data is None else edge.source.data.__class__.__name__,
                    target_id=edge.target.id,
                    target_type="unknown" if edge.target.data is None else edge.target.data.__class__.__name__,
                    relationship_type=edge.relationship_type,
                    confidence=edge.confidence,
                    metadata=edge.metadata,
                )
        
        tracer.patch_function("proj_mapper.relationship.graph.edge", "Edge.to_relationship", patch_to_relationship)
        
        # Add more patches as needed
        return True
    except Exception as e:
        tracer.logger.error(f"Failed to install enum patches: {e}")
        tracer.logger.debug("Traceback:", exc_info=True)
        return False


def initialize_debug_tracing():
    """Initialize debug tracing with all necessary patches.
    
    Returns:
        DebugTracer instance
    """
    tracer = DebugTracer()
    tracer.enable_enhanced_exceptions()
    install_enum_patches(tracer)
    
    # Log environment info
    tracer.logger.debug(f"Python version: {sys.version}")
    tracer.logger.debug(f"Platform: {sys.platform}")
    tracer.logger.debug(f"Current directory: {os.getcwd()}")
    
    # Return the tracer for further use
    return tracer 