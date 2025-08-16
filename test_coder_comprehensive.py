#!/usr/bin/env python3
"""Comprehensive test of CoderAgent to identify any gaps."""

import sys
import os
sys.path.insert(0, '/home/opsvi/master_root/libs/opsvi-agents')

from opsvi_agents.core_agents.coder import CoderAgent, Language

def comprehensive_test():
    """Test all CoderAgent capabilities comprehensively."""
    
    agent = CoderAgent()
    results = {"passed": [], "failed": []}
    
    # Test 1: Generate complex Python class with inheritance
    print("\n=== Test 1: Complex Python Class ===")
    try:
        result = agent.execute({
            "action": "generate",
            "description": "Create a DatabaseManager class that inherits from BaseManager with attributes: connection, pool_size, timeout and methods for CRUD operations",
            "language": "python"
        })
        if "code" in result and "class DatabaseManager" in result["code"]:
            print("✅ Complex class generation")
            results["passed"].append("Complex class generation")
        else:
            print("❌ Complex class generation failed")
            results["failed"].append("Complex class generation")
    except Exception as e:
        print(f"❌ Error: {e}")
        results["failed"].append(f"Complex class generation: {e}")
    
    # Test 2: Generate TypeScript interface and class
    print("\n=== Test 2: TypeScript Code ===")
    try:
        result = agent.execute({
            "action": "generate",
            "description": "Create a TypeScript interface and class for a UserService",
            "language": "typescript"
        })
        if "code" in result and "interface" in result["code"]:
            print("✅ TypeScript generation")
            results["passed"].append("TypeScript generation")
        else:
            print("❌ TypeScript generation incomplete")
            results["failed"].append("TypeScript generation")
    except Exception as e:
        print(f"❌ Error: {e}")
        results["failed"].append(f"TypeScript generation: {e}")
    
    # Test 3: Code refactoring with all goals
    print("\n=== Test 3: Comprehensive Refactoring ===")
    sample_code = """
def process(d):
    r = []
    for i in range(len(d)):
        if d[i] > 0:
            r.append(d[i] * 2)
    x = 0
    for v in r:
        x = x + v
    return x
"""
    try:
        result = agent.execute({
            "action": "refactor",
            "code": sample_code,
            "language": "python",
            "goals": ["readability", "performance", "structure", "maintainability", "testability"]
        })
        if "refactored_code" in result:
            print(f"✅ Refactoring with {len(result.get('changes', []))} changes")
            results["passed"].append("Comprehensive refactoring")
        else:
            print("❌ Refactoring failed")
            results["failed"].append("Comprehensive refactoring")
    except Exception as e:
        print(f"❌ Error: {e}")
        results["failed"].append(f"Comprehensive refactoring: {e}")
    
    # Test 4: Fix code with various errors
    print("\n=== Test 4: Error Fixing ===")
    buggy_code = """
def calculate_average(numbers):
    total = 0
    for i in range(len(numbers))
        total += numbers[i]
    average = total / len(numbers)
    print(f"Average is {average}")
    return averge  # Typo
"""
    try:
        result = agent.execute({
            "action": "fix",
            "code": buggy_code,
            "language": "python",
            "error": "SyntaxError and NameError"
        })
        if "fixed_code" in result:
            print(f"✅ Fixed {len(result.get('fixes_applied', []))} issues")
            results["passed"].append("Error fixing")
        else:
            print("❌ Error fixing failed")
            results["failed"].append("Error fixing")
    except Exception as e:
        print(f"❌ Error: {e}")
        results["failed"].append(f"Error fixing: {e}")
    
    # Test 5: Optimize code for all metrics
    print("\n=== Test 5: Code Optimization ===")
    slow_code = """
def find_duplicates(items):
    duplicates = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i] == items[j] and items[i] not in duplicates:
                duplicates.append(items[i])
    return duplicates
"""
    try:
        result = agent.execute({
            "action": "optimize",
            "code": slow_code,
            "language": "python",
            "metrics": ["speed", "memory", "complexity"],
            "profile": True
        })
        if "optimized_code" in result:
            print(f"✅ Applied {len(result.get('optimizations_applied', []))} optimizations")
            results["passed"].append("Code optimization")
        else:
            print("❌ Optimization failed")
            results["failed"].append("Code optimization")
    except Exception as e:
        print(f"❌ Error: {e}")
        results["failed"].append(f"Code optimization: {e}")
    
    # Test 6: Generate API endpoint
    print("\n=== Test 6: API Generation ===")
    try:
        result = agent.execute({
            "action": "generate",
            "description": "Create a REST API endpoint for user authentication with JWT",
            "language": "python"
        })
        if "code" in result and ("@app" in result["code"] or "FastAPI" in result["code"]):
            print("✅ API endpoint generation")
            results["passed"].append("API generation")
        else:
            print("❌ API generation incomplete")
            results["failed"].append("API generation")
    except Exception as e:
        print(f"❌ Error: {e}")
        results["failed"].append(f"API generation: {e}")
    
    # Test 7: Generate database model
    print("\n=== Test 7: Database Model ===")
    try:
        result = agent.execute({
            "action": "generate",
            "description": "Create a database model for Product with fields: id, name, price, stock, category",
            "language": "python"
        })
        if "code" in result and ("Column" in result["code"] or "class Product" in result["code"]):
            print("✅ Database model generation")
            results["passed"].append("Database model")
        else:
            print("❌ Database model incomplete")
            results["failed"].append("Database model")
    except Exception as e:
        print(f"❌ Error: {e}")
        results["failed"].append(f"Database model: {e}")
    
    # Test 8: Code review
    print("\n=== Test 8: Code Review ===")
    try:
        result = agent.execute({
            "action": "review",
            "code": sample_code,
            "language": "python"
        })
        if "score" in result and "issues" in result:
            print(f"✅ Code review: score={result['score']}, issues={len(result['issues'])}")
            results["passed"].append("Code review")
        else:
            print("❌ Code review incomplete")
            results["failed"].append("Code review")
    except Exception as e:
        print(f"❌ Error: {e}")
        results["failed"].append(f"Code review: {e}")
    
    # Test 9: Code explanation
    print("\n=== Test 9: Code Explanation ===")
    try:
        result = agent.execute({
            "action": "explain",
            "code": "lambda x: x**2 if x > 0 else 0",
            "language": "python"
        })
        if "explanation" in result:
            print("✅ Code explanation")
            results["passed"].append("Code explanation")
        else:
            print("❌ Code explanation failed")
            results["failed"].append("Code explanation")
    except Exception as e:
        print(f"❌ Error: {e}")
        results["failed"].append(f"Code explanation: {e}")
    
    # Test 10: Code conversion
    print("\n=== Test 10: Language Conversion ===")
    py_code = """
def greet(name):
    return f"Hello, {name}!"
"""
    try:
        result = agent.execute({
            "action": "convert",
            "code": py_code,
            "from_language": "python",
            "to_language": "javascript"
        })
        if "converted_code" in result:
            print("✅ Code conversion")
            results["passed"].append("Code conversion")
        else:
            print("❌ Code conversion failed")
            results["failed"].append("Code conversion")
    except Exception as e:
        print(f"❌ Error: {e}")
        results["failed"].append(f"Code conversion: {e}")
    
    # Test 11: Template application
    print("\n=== Test 11: Template Application ===")
    try:
        result = agent.execute({
            "action": "template",
            "template": "singleton",
            "params": {"name": "ConfigManager", "init_body": "self.config = {}"}
        })
        if "code" in result:
            print("✅ Template application")
            results["passed"].append("Template application")
        else:
            print("❌ Template application failed")
            results["failed"].append("Template application")
    except Exception as e:
        print(f"❌ Error: {e}")
        results["failed"].append(f"Template application: {e}")
    
    # Test 12: Generate React component
    print("\n=== Test 12: React Component ===")
    try:
        result = agent.execute({
            "action": "generate",
            "description": "Create a React component for a todo list with add and delete functionality",
            "language": "javascript"
        })
        if "code" in result and ("React" in result["code"] or "useState" in result["code"]):
            print("✅ React component generation")
            results["passed"].append("React component")
        else:
            print("❌ React component incomplete")
            results["failed"].append("React component")
    except Exception as e:
        print(f"❌ Error: {e}")
        results["failed"].append(f"React component: {e}")
    
    # Summary
    print("\n" + "="*50)
    print(f"SUMMARY: {len(results['passed'])} passed, {len(results['failed'])} failed")
    print(f"Success rate: {len(results['passed'])*100/(len(results['passed'])+len(results['failed'])):.1f}%")
    
    if results["failed"]:
        print("\nFailed tests:")
        for fail in results["failed"]:
            print(f"  - {fail}")
    
    # Check available features
    print("\n" + "="*50)
    print("AGENT CAPABILITIES:")
    print(f"- Languages supported: {len(Language.__members__)}")
    print(f"- Templates available: {len(agent.templates)}")
    print(f"- Pattern categories: {len(agent.patterns)}")
    print(f"- Optimization strategies: {len(agent.optimizations)}")
    
    return len(results["failed"]) == 0

if __name__ == "__main__":
    try:
        success = comprehensive_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)