"""Debug tracer for relationship detection.

This module provides a debug tracer for the relationship detection process,
helping to identify where errors might be occurring, particularly around 
handling relationship_type values and enum/string conversions.
"""

import logging
import inspect
import functools
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
from enum import Enum

# Create a specialized logger for the debug tracer
logger = logging.getLogger('proj_mapper.debug_tracer')

class RelationshipDebugTracer:
    """Debug tracer for relationship detection process."""
    
    def __init__(self, log_dir: str = './log'):
        """Initialize the debug tracer.
        
        Args:
            log_dir: Directory to write log files to
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Set up file logger
        self._setup_file_logger()
        
        # Track patched functions
        self.patched_functions = {}
        
    def _setup_file_logger(self):
        """Set up file logging for the debug tracer."""
        # Add a file handler to the logger
        file_handler = logging.FileHandler(
            self.log_dir / 'relationship_debug.log',
            mode='w'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Create a formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Add the handler to the logger
        logger.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        
        logger.debug("RelationshipDebugTracer initialized")
        
    def trace_object(self, obj: Any, prefix: str = '') -> None:
        """Trace an object's attributes and values.
        
        Args:
            obj: Object to trace
            prefix: Prefix for log messages
        """
        logger.debug(f"{prefix}Object type: {type(obj)}")
        
        # If the object is None, log and return
        if obj is None:
            logger.debug(f"{prefix}Object is None")
            return
            
        # If the object is a primitive type, log the value
        if isinstance(obj, (str, int, float, bool)):
            logger.debug(f"{prefix}Value: {repr(obj)}")
            return
            
        # If the object is an enum, log the key details
        if isinstance(obj, Enum):
            logger.debug(f"{prefix}Enum type: {type(obj)}")
            logger.debug(f"{prefix}Enum name: {obj.name}")
            logger.debug(f"{prefix}Has .value: {hasattr(obj, 'value')}")
            if hasattr(obj, 'value'):
                logger.debug(f"{prefix}Enum value: {obj.value}")
            return
            
        # For other objects, log their attributes
        try:
            # Log dict representation if available
            if hasattr(obj, '__dict__'):
                for key, value in vars(obj).items():
                    if key.startswith('_'):
                        continue
                    logger.debug(f"{prefix}Attribute {key}: {type(value)} - {repr(value)[:100]}")
            
            # For dictionaries, log key-value pairs
            elif isinstance(obj, dict):
                for key, value in obj.items():
                    logger.debug(f"{prefix}Key {key}: {type(value)} - {repr(value)[:100]}")
                    
            # For lists, log each element
            elif isinstance(obj, (list, tuple)):
                for i, item in enumerate(obj):
                    logger.debug(f"{prefix}Item {i}: {type(item)} - {repr(item)[:100]}")
        except Exception as e:
            logger.error(f"{prefix}Error tracing object: {e}")
            
    def trace_relationship_type_handling(self, obj: Any, attr_name: str) -> None:
        """Trace specific handling of relationship_type attribute.
        
        Args:
            obj: Object containing relationship_type
            attr_name: Name of the attribute (usually 'relationship_type')
        """
        if not hasattr(obj, attr_name):
            logger.debug(f"Object does not have attribute '{attr_name}'")
            return
            
        value = getattr(obj, attr_name)
        logger.debug(f"Object.{attr_name} type: {type(value)}")
        
        # Check for specific conversions/accesses
        if isinstance(value, str):
            logger.debug(f"'{attr_name}' is a string: {value}")
            logger.debug(f"Has .value: {hasattr(value, 'value')}")
            logger.debug(f"Has .name: {hasattr(value, 'name')}")
        elif isinstance(value, Enum):
            logger.debug(f"'{attr_name}' is an enum: {value}")
            logger.debug(f"Enum.name: {value.name}")
            logger.debug(f"Has .value: {hasattr(value, 'value')}")
            if hasattr(value, 'value'):
                logger.debug(f"Enum.value: {value.value}")
                
    def patch_function(self, module: Any, function_name: str) -> None:
        """Patch a function to add debug tracing.
        
        Args:
            module: The module containing the function
            function_name: Name of the function to patch
        """
        original_function = getattr(module, function_name, None)
        if not original_function:
            logger.error(f"Function {function_name} not found in module {module.__name__}")
            return
            
        # Save the original function
        self.patched_functions[(module, function_name)] = original_function
        
        # Create a wrapped function
        @functools.wraps(original_function)
        def wrapped(*args, **kwargs):
            logger.debug(f"Entering {function_name}")
            
            # Log arguments
            arg_names = inspect.getfullargspec(original_function).args
            for i, arg in enumerate(args):
                arg_name = arg_names[i] if i < len(arg_names) else f"arg{i}"
                logger.debug(f"  {arg_name}: {type(arg)}")
                
                # Special tracing for relationship_type
                if arg_name == 'relationship_type':
                    self.trace_relationship_type_handling(arg, '')
                elif hasattr(arg, 'relationship_type'):
                    self.trace_relationship_type_handling(arg, 'relationship_type')
                    
            for name, value in kwargs.items():
                logger.debug(f"  {name}: {type(value)}")
                
                # Special tracing for relationship_type
                if name == 'relationship_type':
                    self.trace_relationship_type_handling(value, '')
                    
            try:
                result = original_function(*args, **kwargs)
                logger.debug(f"Exiting {function_name} successfully")
                return result
            except Exception as e:
                logger.exception(f"Exception in {function_name}: {e}")
                raise
                
        # Replace the original function
        setattr(module, function_name, wrapped)
        logger.debug(f"Patched {module.__name__}.{function_name}")
        
    def unpatch_all(self) -> None:
        """Restore all patched functions to their original state."""
        for (module, function_name), original_function in self.patched_functions.items():
            setattr(module, function_name, original_function)
            logger.debug(f"Unpatched {module.__name__}.{function_name}")
            
        self.patched_functions = {}
        logger.debug("All functions unpatched")
        
def setup_debug_tracing():
    """Set up debug tracing for relationship detection.
    
    This function should be called before running the relationship detection process
    to add detailed logging that can help identify issues.
    """
    tracer = RelationshipDebugTracer()
    
    # Import modules we want to trace
    from proj_mapper.relationship.graph import graph, edge
    from proj_mapper.cli.commands.relationship import discovery
    from proj_mapper.models import relationship
    
    # Patch key functions that work with relationship_type
    tracer.patch_function(edge.Edge, "__str__")
    tracer.patch_function(edge.Edge, "to_relationship")
    tracer.patch_function(graph.RelationshipGraph, "add_edge")
    tracer.patch_function(graph.RelationshipGraph, "serialize")
    tracer.patch_function(discovery, "_build_relationship_graph")
    tracer.patch_function(discovery, "_edge_to_dict")
    tracer.patch_function(discovery, "_node_to_dict")
    
    # Return the tracer so it can be unpatch_all() later if needed
    return tracer 