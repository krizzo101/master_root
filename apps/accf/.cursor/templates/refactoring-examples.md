<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"Refactoring Examples","description":"This document provides examples of refactoring approaches illustrating before-and-after scenarios for improving code and workflow patterns, focusing on pattern recognition, autonomous triggers, team instructions, verbosity reduction, and optimization targets.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document by identifying its main thematic sections based on the heading hierarchy and content flow. Extract key examples and patterns, especially before-and-after refactoring cases, and highlight important concepts such as silent failure patterns, autonomous triggers, DRY principles, and optimization metrics. Ensure line numbers are accurate and sections do not overlap. Capture code blocks and pattern descriptions as key elements to aid navigation and comprehension.","sections":[{"name":"Introduction and Document Overview","description":"Introduces the document and sets the context for the refactoring examples presented.","line_start":7,"line_end":8},{"name":"Command-Style to Pattern Recognition Refactoring","description":"Demonstrates refactoring from explicit command-style steps to recognizing silent failure patterns with structured implementation steps.","line_start":9,"line_end":13},{"name":"Workflow to Autonomous Triggers Refactoring","description":"Shows how workflows can be refactored into autonomous triggers based on keyword detection and automated process chaining.","line_start":14,"line_end":18},{"name":"Team Instructions to Encyclopedia Patterns Refactoring","description":"Illustrates refactoring team instructions into pattern-based validations such as DRY violation detection and test coverage validation.","line_start":19,"line_end":23},{"name":"Verbose to High-Density Refactoring","description":"Compares a verbose 98-line rule with a concise 4-line high-density implementation focusing on research orchestration and triggers.","line_start":24,"line_end":28},{"name":"Optimization Targets Summary","description":"Summarizes key optimization goals including size reduction, operational content density, autonomous recognition focus, and quality metrics.","line_start":29,"line_end":33}],"key_elements":[{"name":"Silent Failure Pattern Example","description":"Code pattern illustrating silent failure where a query returns empty results despite existing data, used in the Command-Style refactoring.","line":11},{"name":"Research Trigger Autonomous Workflow","description":"Example of an autonomous trigger workflow initiated by keywords to perform web search, scraping, and synthesis.","line":16},{"name":"DRY Violation and Test Coverage Validation Patterns","description":"Patterns for detecting repeated code blocks and functions lacking tests, representing team instruction refactoring.","line":21},{"name":"Verbose vs High-Density Rule Comparison","description":"Contrasts a detailed 98-line rule with a concise 4-line implementation focusing on research orchestration and triggers.","line":26},{"name":"Optimization Metrics Table","description":"Summary of optimization targets including size reduction percentages, content density, focus areas, and quality criteria.","line":30}]}
-->
<!-- FILE_MAP_END -->

# Refactoring Examples

## Command-Style → Pattern Recognition

**Before**: Step 1: Check query results, Step 2: Validate collection, Step 3: Investigate fields...
**After**: **Silent Failure Pattern** | **Signature**: Query succeeds but returns [] when data exists | **Implementation**: Collection validation → field validation → correction

## Workflow → Autonomous Triggers

**Before**: When user requests research: Start with web search, identify URLs, scrape content...
**After**: **Research Trigger**: "research"/"investigate" keywords | **Implementation**: web_search → scraping → tech_docs → synthesis

## Team Instructions → Encyclopedia Patterns

**Before**: Team members should ensure code follows DRY principles. Remember to write tests...
**After**: **DRY Violation Detection**: Repeated code blocks | **Test Coverage Validation**: Functions without tests

## Verbose → High-Density

**Before (98 lines)**: This rule provides comprehensive guidance for autonomous agents when they need to perform complex research operations...
**After (4 lines)**: **Research Orchestration** | **Trigger**: research keywords | **Implementation**: web_search → scraping → synthesis

## Optimization Targets
**Size**: 40-70% reduction | **Density**: >80% operational content | **Focus**: Autonomous recognition
**Quality**: Fast recognition, clear implementation, precise validation
