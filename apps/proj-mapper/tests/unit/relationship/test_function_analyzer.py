"""Unit tests for function call analysis."""

import pytest
from proj_mapper.relationship.function_analyzer import FunctionCallAnalyzer

def test_simple_function_call():
    """Test detection of simple function calls."""
    code = """
def caller():
    result = callee()
    return result
"""
    analyzer = FunctionCallAnalyzer(code)
    calls = analyzer.analyze()
    
    assert len(calls) == 1
    assert calls[0].caller_id == "caller"
    assert calls[0].callee_name == "callee"
    assert calls[0].confidence == 1.0
    assert not calls[0].is_method_call

def test_method_call():
    """Test detection of method calls."""
    code = """
class MyClass:
    def caller(self):
        self.callee()
        
    def callee(self):
        pass
"""
    analyzer = FunctionCallAnalyzer(code)
    calls = analyzer.analyze()
    
    assert len(calls) == 1
    assert calls[0].caller_id == "caller"
    assert calls[0].callee_name == "callee"
    assert calls[0].confidence == 1.0
    assert calls[0].is_method_call
    assert calls[0].qualifier == "self"

def test_chained_method_call():
    """Test detection of chained method calls."""
    code = """
def process_data():
    data.clean().transform().save()
"""
    analyzer = FunctionCallAnalyzer(code)
    calls = analyzer.analyze()
    
    assert len(calls) == 3
    methods = [call.callee_name for call in calls]
    assert "clean" in methods
    assert "transform" in methods
    assert "save" in methods
    assert all(call.is_method_call for call in calls)
    assert any(call.qualifier == "data.clean.transform" for call in calls)

def test_import_tracking():
    """Test tracking of imports."""
    code = """
from math import sqrt
import os.path as path
from typing import List, Optional

def compute():
    x = sqrt(4)
    p = path.join('a', 'b')
"""
    analyzer = FunctionCallAnalyzer(code)
    calls = analyzer.analyze()
    
    assert len(calls) == 2
    sqrt_call = next(call for call in calls if call.callee_name == "sqrt")
    join_call = next(call for call in calls if call.callee_name == "join")
    
    assert sqrt_call.confidence == 1.0
    assert join_call.qualifier == "path"

def test_class_method():
    """Test detection of class method calls."""
    code = """
class DataProcessor:
    @classmethod
    def from_file(cls, filename):
        return cls()
        
    def process(self):
        result = self.from_file('data.txt')
        return result
"""
    analyzer = FunctionCallAnalyzer(code)
    calls = analyzer.analyze()
    
    assert len(calls) == 1
    assert calls[0].callee_name == "from_file"
    assert calls[0].is_method_call
    assert calls[0].qualifier == "self"

def test_nested_calls():
    """Test detection of nested function calls."""
    code = """
def outer():
    def inner():
        print('hello')
    
    inner()
    return True
"""
    analyzer = FunctionCallAnalyzer(code)
    calls = analyzer.analyze()
    
    assert len(calls) == 2  # inner() and print()
    assert any(call.callee_name == "inner" for call in calls)
    assert any(call.callee_name == "print" for call in calls)

def test_error_handling():
    """Test handling of invalid code."""
    code = """
def broken_function()
    invalid syntax here
"""
    analyzer = FunctionCallAnalyzer(code)
    calls = analyzer.analyze()
    
    assert len(calls) == 0  # Should handle error gracefully

def test_context_capture():
    """Test capturing of call context."""
    code = """
def process_data():
    # Prepare data
    data = load_data()
    # Transform data
    result = transform(data)
    # Done
"""
    analyzer = FunctionCallAnalyzer(code)
    calls = analyzer.analyze()
    
    assert len(calls) == 2
    for call in calls:
        assert call.context_before.strip()
        assert call.context_after.strip()
        assert call.line_number > 0 