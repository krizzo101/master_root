#!/usr/bin/env python3
"""
Test Suite for Intelligent Model Selection Engine

This module provides comprehensive tests for the model selection engine,
validating decision logic, prompt analysis, and configuration handling.

Author: AI Assistant
Date: 2025-07-30
Version: 1.0.0
"""

import json
import os
import tempfile
import unittest

from .model_selection_engine import (
    ModelDecision,
    ModelSelectionEngine,
    TaskContext,
    create_task_context,
    select_optimal_model,
)


class TestModelSelectionEngine(unittest.TestCase):
    """Test cases for the ModelSelectionEngine class."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = ModelSelectionEngine()

        # Test prompts for different task types
        self.test_prompts = {
            "requirements_gathering": "Create user stories and acceptance criteria for a healthcare appointment booking system",
            "system_architecture": "Design an event-driven microservices architecture for a real-time notification platform",
            "code_implementation": "Design and implement key design patterns for a scalable e-commerce cart system",
            "testing_strategy": "Create a comprehensive testing strategy for a financial transaction processing system",
            "devops_deployment": "Design a complete CI/CD pipeline for a multi-environment SaaS application",
            "database_design": "Design a comprehensive data model for a social media platform with users, posts, comments",
            "security_analysis": "Analyze and design security architecture for a healthcare data management system",
            "performance_optimization": "Create a performance optimization strategy for a high-traffic API gateway",
            "code_review": "Design a comprehensive code quality assessment framework for a team of 20+ developers",
            "technical_documentation": "Create comprehensive API documentation standards and templates for a microservices platform",
        }

    def test_config_loading(self):
        """Test that configuration file loads correctly."""
        self.assertIsNotNone(self.engine.config)
        self.assertIn("version", self.engine.config)
        self.assertIn("decision_matrix", self.engine.config)
        self.assertIn("model_characteristics", self.engine.config)

    def test_valid_models(self):
        """Test that valid models are correctly identified."""
        expected_models = ["gpt-4.1-nano", "gpt-4.1-mini", "gpt-4.1", "o4-mini", "o3"]
        self.assertEqual(set(self.engine.valid_models), set(expected_models))

    def test_prompt_analysis_task_types(self):
        """Test prompt analysis for different task types."""
        for task_type, prompt in self.test_prompts.items():
            with self.subTest(task_type=task_type):
                analysis = self.engine.analyze_prompt(prompt)
                self.assertIn("task_type", analysis)
                self.assertIn("confidence", analysis)
                self.assertIn("keywords_found", analysis)

                # Check that the detected task type matches expected
                if task_type != "general_development":
                    self.assertEqual(analysis["task_type"], task_type)

    def test_prompt_analysis_time_constraints(self):
        """Test prompt analysis for time constraints."""
        # Test urgent
        urgent_prompt = (
            "I need this urgently - create a quick overview of system architecture"
        )
        analysis = self.engine.analyze_prompt(urgent_prompt)
        self.assertEqual(analysis["time_constraint"], "urgent")

        # Test thorough
        thorough_prompt = "Please provide a thorough and comprehensive analysis of the security architecture"
        analysis = self.engine.analyze_prompt(thorough_prompt)
        self.assertEqual(analysis["time_constraint"], "thorough")

        # Test normal (default)
        normal_prompt = "Create a system design for a web application"
        analysis = self.engine.analyze_prompt(normal_prompt)
        self.assertEqual(analysis["time_constraint"], "normal")

    def test_prompt_analysis_quality_requirements(self):
        """Test prompt analysis for quality requirements."""
        # Test overview
        overview_prompt = "Give me a quick overview of the database design"
        analysis = self.engine.analyze_prompt(overview_prompt)
        self.assertEqual(analysis["quality_requirement"], "overview")

        # Test comprehensive
        comprehensive_prompt = (
            "Provide a comprehensive and detailed analysis of the testing strategy"
        )
        analysis = self.engine.analyze_prompt(comprehensive_prompt)
        self.assertEqual(analysis["quality_requirement"], "comprehensive")

        # Test detailed (default)
        detailed_prompt = "Create a system architecture design"
        analysis = self.engine.analyze_prompt(detailed_prompt)
        self.assertEqual(analysis["quality_requirement"], "detailed")

    def test_prompt_analysis_complexity_levels(self):
        """Test prompt analysis for complexity levels."""
        # Test simple
        simple_prompt = "Create a simple and basic user interface design"
        analysis = self.engine.analyze_prompt(simple_prompt)
        self.assertEqual(analysis["complexity_level"], "simple")

        # Test complex
        complex_prompt = (
            "Design a complex and sophisticated distributed system architecture"
        )
        analysis = self.engine.analyze_prompt(complex_prompt)
        self.assertEqual(analysis["complexity_level"], "complex")

        # Test moderate (default)
        moderate_prompt = "Create a standard web application design"
        analysis = self.engine.analyze_prompt(moderate_prompt)
        self.assertEqual(analysis["complexity_level"], "moderate")

    def test_model_selection_requirements_gathering(self):
        """Test model selection for requirements gathering tasks."""
        context = TaskContext(
            task_type="requirements_gathering",
            time_constraint="normal",
            quality_requirement="detailed",
            complexity_level="moderate",
        )

        decision = self.engine.select_model(context)
        self.assertIsInstance(decision, ModelDecision)
        self.assertIn(decision.selected_model, self.engine.valid_models)
        self.assertGreater(decision.confidence_score, 0.0)
        self.assertLessEqual(decision.confidence_score, 1.0)

    def test_model_selection_system_architecture(self):
        """Test model selection for system architecture tasks."""
        context = TaskContext(
            task_type="system_architecture",
            time_constraint="urgent",
            quality_requirement="overview",
            complexity_level="moderate",
        )

        decision = self.engine.select_model(context)
        self.assertEqual(decision.selected_model, "gpt-4.1-nano")

    def test_model_selection_complex_architecture(self):
        """Test model selection for complex architectural tasks."""
        context = TaskContext(
            task_type="system_architecture",
            time_constraint="thorough",
            quality_requirement="comprehensive",
            complexity_level="complex",
        )

        decision = self.engine.select_model(context)
        self.assertEqual(decision.selected_model, "o3")

    def test_user_override(self):
        """Test that user override works correctly."""
        context = TaskContext(
            task_type="requirements_gathering",
            time_constraint="normal",
            quality_requirement="detailed",
            complexity_level="moderate",
            user_override="gpt-4.1-mini",
        )

        decision = self.engine.select_model(context)
        self.assertEqual(decision.selected_model, "gpt-4.1-mini")
        self.assertEqual(decision.confidence_score, 1.0)
        self.assertIn("User override", decision.reasoning)

    def test_invalid_user_override(self):
        """Test handling of invalid user override."""
        context = TaskContext(
            task_type="requirements_gathering",
            time_constraint="normal",
            quality_requirement="detailed",
            complexity_level="moderate",
            user_override="invalid-model",
        )

        # Should not raise exception, should use normal selection
        decision = self.engine.select_model(context)
        self.assertIn(decision.selected_model, self.engine.valid_models)

    def test_alternatives_generation(self):
        """Test that alternatives are generated correctly."""
        context = TaskContext(
            task_type="requirements_gathering",
            time_constraint="normal",
            quality_requirement="detailed",
            complexity_level="moderate",
        )

        decision = self.engine.select_model(context)
        self.assertIsInstance(decision.alternatives, list)
        self.assertLessEqual(len(decision.alternatives), 5)

        # All alternatives should be valid models
        for alt in decision.alternatives:
            self.assertIn(alt, self.engine.valid_models)

    def test_reasoning_generation(self):
        """Test that reasoning is generated correctly."""
        context = TaskContext(
            task_type="system_architecture",
            time_constraint="urgent",
            quality_requirement="overview",
            complexity_level="moderate",
        )

        decision = self.engine.select_model(context)
        self.assertIsInstance(decision.reasoning, str)
        self.assertGreater(len(decision.reasoning), 0)
        self.assertIn("gpt-4.1-nano", decision.reasoning)

    def test_model_info_retrieval(self):
        """Test retrieval of model information."""
        model_info = self.engine.get_model_info("gpt-4.1-nano")
        self.assertIsInstance(model_info, dict)
        self.assertIn("speed", model_info)
        self.assertIn("technical_depth", model_info)
        self.assertIn("structure", model_info)
        self.assertIn("completeness", model_info)

    def test_invalid_model_info_retrieval(self):
        """Test handling of invalid model information requests."""
        with self.assertRaises(ValueError):
            self.engine.get_model_info("invalid-model")

    def test_available_models_listing(self):
        """Test listing of available models."""
        models = self.engine.list_available_models()
        self.assertIsInstance(models, list)
        self.assertEqual(len(models), 5)
        self.assertEqual(set(models), set(self.engine.valid_models))

    def test_task_types_listing(self):
        """Test listing of available task types."""
        task_types = self.engine.get_task_types()
        self.assertIsInstance(task_types, list)
        self.assertGreater(len(task_types), 0)
        self.assertIn("requirements_gathering", task_types)
        self.assertIn("system_architecture", task_types)


class TestTaskContext(unittest.TestCase):
    """Test cases for the TaskContext class."""

    def test_task_context_creation(self):
        """Test TaskContext creation with default values."""
        context = TaskContext()
        self.assertEqual(context.task_type, "general_development")
        self.assertEqual(context.time_constraint, "normal")
        self.assertEqual(context.quality_requirement, "detailed")
        self.assertEqual(context.complexity_level, "moderate")
        self.assertEqual(context.prompt_text, "")
        self.assertIsNone(context.user_override)

    def test_task_context_creation_with_values(self):
        """Test TaskContext creation with specific values."""
        context = TaskContext(
            task_type="system_architecture",
            time_constraint="urgent",
            quality_requirement="overview",
            complexity_level="simple",
            prompt_text="Test prompt",
            user_override="gpt-4.1-nano",
        )

        self.assertEqual(context.task_type, "system_architecture")
        self.assertEqual(context.time_constraint, "urgent")
        self.assertEqual(context.quality_requirement, "overview")
        self.assertEqual(context.complexity_level, "simple")
        self.assertEqual(context.prompt_text, "Test prompt")
        self.assertEqual(context.user_override, "gpt-4.1-nano")


class TestModelDecision(unittest.TestCase):
    """Test cases for the ModelDecision class."""

    def test_model_decision_creation(self):
        """Test ModelDecision creation."""
        decision = ModelDecision(
            selected_model="gpt-4.1-nano",
            confidence_score=0.8,
            reasoning="Test reasoning",
            alternatives=["gpt-4.1-mini", "gpt-4.1"],
            task_analysis={"task_type": "system_architecture"},
        )

        self.assertEqual(decision.selected_model, "gpt-4.1-nano")
        self.assertEqual(decision.confidence_score, 0.8)
        self.assertEqual(decision.reasoning, "Test reasoning")
        self.assertEqual(decision.alternatives, ["gpt-4.1-mini", "gpt-4.1"])
        self.assertEqual(decision.task_analysis["task_type"], "system_architecture")


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions."""

    def test_create_task_context(self):
        """Test create_task_context function."""
        prompt = "Create user stories for a healthcare system"
        context = create_task_context(prompt)

        self.assertIsInstance(context, TaskContext)
        self.assertEqual(context.prompt_text, prompt)
        self.assertEqual(context.task_type, "requirements_gathering")

    def test_create_task_context_with_override(self):
        """Test create_task_context function with user override."""
        prompt = "Create user stories for a healthcare system"
        context = create_task_context(prompt_text=prompt, user_override="gpt-4.1-mini")

        self.assertEqual(context.user_override, "gpt-4.1-mini")

    def test_select_optimal_model(self):
        """Test select_optimal_model function."""
        prompt = "Design a microservices architecture for a notification system"
        decision = select_optimal_model(prompt)

        self.assertIsInstance(decision, ModelDecision)
        self.assertIn(decision.selected_model, ["gpt-4.1-nano", "gpt-4.1", "o3"])

    def test_select_optimal_model_with_override(self):
        """Test select_optimal_model function with user override."""
        prompt = "Design a microservices architecture for a notification system"
        decision = select_optimal_model(
            prompt_text=prompt, user_override="gpt-4.1-mini"
        )

        self.assertEqual(decision.selected_model, "gpt-4.1-mini")


class TestConfigurationHandling(unittest.TestCase):
    """Test cases for configuration handling."""

    def test_missing_config_file(self):
        """Test handling of missing configuration file."""
        with self.assertRaises(FileNotFoundError):
            ModelSelectionEngine("nonexistent_config.json")

    def test_invalid_config_file(self):
        """Test handling of invalid configuration file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"invalid": "json"')
            temp_config = f.name

        try:
            with self.assertRaises(json.JSONDecodeError):
                ModelSelectionEngine(temp_config)
        finally:
            os.unlink(temp_config)


def run_performance_tests():
    """Run performance tests for the model selection engine."""
    print("\n=== Performance Tests ===")

    engine = ModelSelectionEngine()

    # Test prompt analysis performance
    import time

    test_prompts = [
        "Create user stories for a healthcare system",
        "Design a microservices architecture for a notification platform",
        "Implement design patterns for an e-commerce cart system",
        "Create a comprehensive testing strategy for financial transactions",
        "Design a CI/CD pipeline for a SaaS application",
    ]

    start_time = time.time()
    for prompt in test_prompts:
        analysis = engine.analyze_prompt(prompt)
        context = create_task_context(prompt)
        decision = engine.select_model(context)

    end_time = time.time()
    total_time = end_time - start_time
    avg_time = total_time / len(test_prompts)

    print(f"Processed {len(test_prompts)} prompts in {total_time:.3f}s")
    print(f"Average time per prompt: {avg_time:.3f}s")
    print(f"Performance: {len(test_prompts)/total_time:.1f} prompts/second")


if __name__ == "__main__":
    # Run unit tests
    unittest.main(verbosity=2, exit=False)

    # Run performance tests
    run_performance_tests()
