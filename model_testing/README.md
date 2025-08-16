# Model Testing Framework

This directory contains comprehensive testing frameworks for evaluating and comparing AI model performance, with a focus on GPT-5 vs GPT-4.1 series comparisons.

## Overview

The testing framework implements industry-standard evaluation methodologies based on:
- **simple-evals**: Zero-shot, chain-of-thought evaluation patterns
- **human-eval**: Functional correctness testing for code generation
- **structured-outputs**: Schema-driven validation
- **gpt-5-coding-examples**: Real-world application generation

## Framework Features

### 🧠 **GPT-5 Reasoning Effort Testing**
- **Low/Medium/High Reasoning Levels**: Comprehensive evaluation of how reasoning effort affects performance
- **Coding-Focused Evaluation**: Specialized tests for programming tasks
- **Performance Analysis**: Quality vs. execution time trade-offs
- **Efficiency Scoring**: Quality per unit time metrics

### 📊 **Test Categories**

#### **Code Generation**
- Python function implementation
- React component development
- API design and documentation

#### **Coding Reasoning**
- **Debugging Complex Code**: Stack overflow, race conditions, memory leaks
- **Code Complexity Analysis**: Big O notation, performance bottlenecks
- **Design Pattern Recognition**: Observer, Strategy patterns

#### **Algorithm Design**
- **Dynamic Programming**: Longest palindromic subsequence, TSP
- **Graph Algorithms**: Strongly connected components, MST
- **Optimization Problems**: Genetic algorithms, simulated annealing

#### **Code Optimization**
- **Performance Optimization**: Algorithm improvement, database queries
- **Memory Optimization**: Streaming, memory pooling, garbage collection
- **Concurrent Optimization**: Threading, lock-free data structures

#### **General Reasoning**
- Mathematical reasoning
- Logical reasoning
- Scientific reasoning

#### **Creative Tasks**
- Application generation
- Content creation
- Design systems

#### **Structured Output**
- Data extraction
- Code analysis
- API documentation

#### **Agentic Tasks**
- Multi-step planning
- Tool calling

#### **Long Context**
- Information retrieval from large documents

#### **Factuality**
- Fact checking
- Accuracy verification

## File Structure

```
model_testing/
├── README.md                                    # This file
├── gpt5_vs_gpt41_comprehensive_test_framework.py  # Main testing framework
└── results/                                     # Generated test results (auto-created)
    ├── comprehensive_gpt5_vs_gpt41_results.json
    ├── comprehensive_gpt5_vs_gpt41_report.md
    └── comprehensive_gpt5_vs_gpt41_executive_summary.md
```

## Usage

### Running the Framework

```bash
# Navigate to the model testing directory
cd model_testing/

# Run the comprehensive testing framework
python gpt5_vs_gpt41_comprehensive_test_framework.py
```

### Configuration

The framework supports testing different model pairs:

```python
MODEL_PAIRS = [
    ("gpt-4.1-nano", "gpt-5-nano"),
    ("gpt-4.1-mini", "gpt-5-mini"),
    ("gpt-4.1", "gpt-5")
]
```

### Reasoning Effort Levels

For GPT-5 testing, the framework supports three reasoning effort levels:

- **Low**: 1 iteration, 120s timeout, low verbosity, no critic
- **Medium**: 2 iterations, 180s timeout, medium verbosity, critic enabled
- **High**: 3 iterations, 300s timeout, high verbosity, critic enabled

## Output Files

The framework generates three types of output files:

### 1. **comprehensive_gpt5_vs_gpt41_results.json**
Detailed JSON results containing:
- Raw test metrics for each model pair
- Category-specific performance data
- Reasoning effort analysis
- Comparison statistics

### 2. **comprehensive_gpt5_vs_gpt41_report.md**
Comprehensive markdown report including:
- Executive summary
- GPT-5 reasoning effort analysis
- Category performance breakdown
- Detailed test results
- Key insights and recommendations

### 3. **comprehensive_gpt5_vs_gpt41_executive_summary.md**
High-level executive summary with:
- Key findings
- GPT-5 reasoning effort insights
- Category insights
- Actionable recommendations

## Evaluation Metrics

The framework evaluates models across multiple dimensions:

- **Functional Correctness**: Code execution accuracy
- **Code Quality**: Comments, type hints, error handling, documentation
- **Reasoning Quality**: Step-by-step analysis, logical structure
- **Creativity Score**: Originality and innovation
- **Structure Quality**: Organization and formatting
- **Completeness**: Task completion level
- **Accuracy**: Correctness for reasoning tasks
- **Error Rate**: Failure rate (lower is better)
- **Execution Time**: Performance measurement
- **Efficiency Score**: Quality per unit time

## Key Insights

The framework provides automated analysis of:

- **Performance Trade-offs**: Quality vs. execution time
- **Reasoning Effort Optimization**: Optimal effort level recommendations
- **Model Comparison**: GPT-5 vs GPT-4.1 performance differences
- **Category Strengths**: Which tasks each model excels at
- **Efficiency Analysis**: Cost-benefit analysis of different configurations

## Recommendations

Based on testing results, the framework provides:

- **Upgrade Recommendations**: Whether to upgrade to GPT-5 series
- **Reasoning Effort Guidance**: When to use low/medium/high reasoning
- **Use Case Optimization**: Best practices for different task types
- **Performance Monitoring**: Guidelines for production validation

## Dependencies

The framework requires:
- Python 3.8+
- `asyncio` for asynchronous execution
- `statistics` for statistical analysis
- `numpy` for numerical operations
- Access to GPT-4.1 and GPT-5 APIs via consult agent tools

## Contributing

To add new test categories or evaluation metrics:

1. Add new test category to `TestCategory` enum
2. Create test datasets in `TEST_DATASETS`
3. Add optimized prompts for both GPT-4.1 and GPT-5
4. Implement evaluation metrics in `_calculate_metrics`
5. Update report generation methods

## License

This testing framework is part of the project's evaluation toolkit and follows the project's licensing terms.
