#!/usr/bin/env python3
"""
Intelligent Model Selection Demo

This script demonstrates the intelligent model selection system with various
example prompts and scenarios, showing how the system automatically selects
the optimal model based on task characteristics.

Author: AI Assistant
Date: 2025-07-30
Version: 1.0.0
"""

from model_selection_engine import (
    ModelSelectionEngine,
    create_task_context,
    select_optimal_model,
)
import json


def print_separator(title: str):
    """Print a formatted separator with title."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def print_decision(decision, prompt: str):
    """Print a formatted model decision."""
    print(f"\n📝 Prompt: {prompt}")
    print(f"🤖 Selected Model: {decision.selected_model}")
    print(f"🎯 Confidence: {decision.confidence_score:.2f}")
    print(f"💭 Reasoning: {decision.reasoning}")
    print(f"🔄 Alternatives: {', '.join(decision.alternatives[:3])}")
    print(f"📊 Task Analysis: {decision.task_analysis}")


def demo_basic_selection():
    """Demonstrate basic model selection with different task types."""
    print_separator("BASIC MODEL SELECTION DEMO")

    engine = ModelSelectionEngine()

    # Test prompts for different SDLC phases
    test_cases = [
        {
            "title": "Requirements Gathering",
            "prompt": "Create user stories and acceptance criteria for a healthcare appointment booking system",
        },
        {
            "title": "System Architecture",
            "prompt": "Design an event-driven microservices architecture for a real-time notification platform",
        },
        {
            "title": "Code Implementation",
            "prompt": "Design and implement key design patterns for a scalable e-commerce cart system",
        },
        {
            "title": "Testing Strategy",
            "prompt": "Create a comprehensive testing strategy for a financial transaction processing system",
        },
        {
            "title": "DevOps & Deployment",
            "prompt": "Design a complete CI/CD pipeline for a multi-environment SaaS application",
        },
    ]

    for case in test_cases:
        print(f"\n🔍 {case['title']}")
        decision = select_optimal_model(case["prompt"])
        print_decision(decision, case["prompt"])


def demo_time_constraints():
    """Demonstrate model selection based on time constraints."""
    print_separator("TIME CONSTRAINT DEMO")

    base_prompt = "Design a system architecture for a web application"

    # Test different time constraints
    time_variations = [
        {
            "constraint": "Urgent",
            "prompt": f"URGENT: {base_prompt} - I need this immediately!",
        },
        {"constraint": "Normal", "prompt": base_prompt},
        {
            "constraint": "Thorough",
            "prompt": f"Please provide a thorough and comprehensive {base_prompt}",
        },
    ]

    for variation in time_variations:
        print(f"\n⏰ {variation['constraint']} Time Constraint")
        decision = select_optimal_model(variation["prompt"])
        print_decision(decision, variation["prompt"])


def demo_quality_requirements():
    """Demonstrate model selection based on quality requirements."""
    print_separator("QUALITY REQUIREMENT DEMO")

    base_prompt = "Create a database design"

    # Test different quality requirements
    quality_variations = [
        {
            "requirement": "Overview",
            "prompt": f"Give me a quick overview of {base_prompt}",
        },
        {"requirement": "Detailed", "prompt": f"Create a detailed {base_prompt}"},
        {
            "requirement": "Comprehensive",
            "prompt": f"Provide a comprehensive and complete {base_prompt}",
        },
    ]

    for variation in quality_variations:
        print(f"\n📋 {variation['requirement']} Quality Requirement")
        decision = select_optimal_model(variation["prompt"])
        print_decision(decision, variation["prompt"])


def demo_complexity_levels():
    """Demonstrate model selection based on complexity levels."""
    print_separator("COMPLEXITY LEVEL DEMO")

    base_prompt = "Design a system"

    # Test different complexity levels
    complexity_variations = [
        {"complexity": "Simple", "prompt": f"Create a simple and basic {base_prompt}"},
        {"complexity": "Moderate", "prompt": f"Design a standard {base_prompt}"},
        {
            "complexity": "Complex",
            "prompt": f"Design a complex and sophisticated distributed {base_prompt}",
        },
    ]

    for variation in complexity_variations:
        print(f"\n🧩 {variation['complexity']} Complexity")
        decision = select_optimal_model(variation["prompt"])
        print_decision(decision, variation["prompt"])


def demo_user_overrides():
    """Demonstrate user override functionality."""
    print_separator("USER OVERRIDE DEMO")

    prompt = "Create user stories for a healthcare system"

    print(f"\n🔧 Without Override")
    decision = select_optimal_model(prompt)
    print_decision(decision, prompt)

    print(f"\n🔧 With User Override (gpt-4.1-mini)")
    decision = select_optimal_model(prompt, user_override="gpt-4.1-mini")
    print_decision(decision, prompt)

    print(f"\n🔧 With User Override (o3)")
    decision = select_optimal_model(prompt, user_override="o3")
    print_decision(decision, prompt)


def demo_prompt_analysis():
    """Demonstrate prompt analysis capabilities."""
    print_separator("PROMPT ANALYSIS DEMO")

    engine = ModelSelectionEngine()

    complex_prompt = """
    URGENT: Create a comprehensive and detailed security architecture design
    for a complex healthcare data management system that handles PHI.
    This needs to be thorough and complete with advanced threat modeling.
    """

    print(f"📝 Analyzing Prompt: {complex_prompt.strip()}")

    analysis = engine.analyze_prompt(complex_prompt)
    print(f"\n🔍 Analysis Results:")
    print(f"   Task Type: {analysis['task_type']}")
    print(f"   Time Constraint: {analysis['time_constraint']}")
    print(f"   Quality Requirement: {analysis['quality_requirement']}")
    print(f"   Complexity Level: {analysis['complexity_level']}")
    print(f"   Confidence: {analysis['confidence']:.2f}")
    print(f"   Keywords Found: {', '.join(analysis['keywords_found'][:5])}...")

    # Show the resulting model selection
    decision = engine.select_model(create_task_context(complex_prompt))
    print_decision(decision, complex_prompt.strip())


def demo_model_characteristics():
    """Demonstrate model characteristics and information."""
    print_separator("MODEL CHARACTERISTICS DEMO")

    engine = ModelSelectionEngine()

    print("📊 Model Characteristics:")
    for model in engine.list_available_models():
        info = engine.get_model_info(model)
        print(f"\n🤖 {model}:")
        print(f"   Speed: {info['speed']}")
        print(f"   Technical Depth: {info['technical_depth']}")
        print(f"   Structure: {info['structure']}")
        print(f"   Completeness: {info['completeness']}")
        print(f"   Avg Execution Time: {info['avg_execution_time']}")
        print(f"   Avg Word Count: {info['avg_word_count']}")
        print(f"   Best For: {', '.join(info['best_for'][:3])}...")


def demo_decision_matrix():
    """Demonstrate the decision matrix structure."""
    print_separator("DECISION MATRIX DEMO")

    engine = ModelSelectionEngine()

    # Show a sample decision matrix entry
    print("📋 Sample Decision Matrix Entry (System Architecture):")

    matrix = engine.config["decision_matrix"]["system_architecture"]
    print(json.dumps(matrix, indent=2))


def demo_performance_comparison():
    """Demonstrate performance comparison across models."""
    print_separator("PERFORMANCE COMPARISON DEMO")

    engine = ModelSelectionEngine()

    test_prompt = "Design a microservices architecture for a notification system"

    print(f"📝 Test Prompt: {test_prompt}")
    print(f"\n⚡ Performance Comparison:")

    for model in engine.list_available_models():
        info = engine.get_model_info(model)
        print(f"\n🤖 {model}:")
        print(f"   Expected Time: {info['avg_execution_time']}")
        print(f"   Expected Words: {info['avg_word_count']}")
        print(f"   Speed Category: {info['speed']}")

    # Show what the system would select
    decision = select_optimal_model(test_prompt)
    print(f"\n🎯 System Selection: {decision.selected_model}")
    print(f"   Reasoning: {decision.reasoning}")


def main():
    """Run all demonstration scenarios."""
    print("🚀 Intelligent Model Selection System Demo")
    print("Based on comprehensive SDLC testing results")

    try:
        # Run all demos
        demo_basic_selection()
        demo_time_constraints()
        demo_quality_requirements()
        demo_complexity_levels()
        demo_user_overrides()
        demo_prompt_analysis()
        demo_model_characteristics()
        demo_decision_matrix()
        demo_performance_comparison()

        print_separator("DEMO COMPLETE")
        print("✅ All demonstrations completed successfully!")
        print("\n💡 Key Benefits:")
        print("   • Automatic model selection based on task characteristics")
        print("   • Intelligent prompt analysis")
        print("   • User override capability")
        print("   • Performance optimization")
        print("   • Consistent decision making")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
