#!/usr/bin/env python3
"""
Orchestrator Cognitive Enhancement Test Framework

This creates test prompts and validation criteria for comparing:
1. Fresh agent with ASEA Orchestrator cognitive enhancement
2. Control agent with no cognitive enhancement tools
3. Objective measurement of cognitive enhancement effectiveness
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Any


class OrchestratorCognitiveEnhancementTest:
    """Framework for testing cognitive enhancement via ASEA Orchestrator"""

    def __init__(self):
        self.test_scenarios = self._create_test_scenarios()
        self.validation_criteria = self._define_validation_criteria()
        self.results_dir = "/home/opsvi/asea/development/autonomous_systems/validation_systems/orchestrator_test_results"

    def _create_test_scenarios(self) -> List[Dict[str, Any]]:
        """Create test scenarios that benefit from cognitive enhancement"""

        scenarios = [
            {
                "name": "complex_decision_analysis",
                "description": "Multi-criteria decision with budget constraints",
                "prompt": """
You need to help a startup decide between three AI development approaches:

1. **In-house development**: $50K upfront, 6 months timeline, 70% success probability
2. **Hybrid approach**: $30K upfront, 4 months timeline, 60% success probability  
3. **Full outsourcing**: $80K upfront, 3 months timeline, 85% success probability

Additional constraints:
- Budget limit: $60K total
- Must launch within 5 months
- Success probability must be >65%
- Team has limited AI expertise

Provide a comprehensive analysis with:
- Cost-benefit analysis for each option
- Risk assessment and mitigation strategies
- Final recommendation with detailed rationale
- Implementation timeline with key milestones

Be thorough and systematic in your analysis.
""",
                "cognitive_enhancement_expected": [
                    "Budget analysis using Budget Manager plugin",
                    "Workflow intelligence for decision optimization",
                    "Multi-step reasoning with cost tracking",
                    "Systematic risk analysis",
                    "Evidence-based recommendations",
                ],
            },
            {
                "name": "technical_architecture_design",
                "description": "System architecture with multiple constraints",
                "prompt": """
Design a scalable AI-powered customer service system for an e-commerce platform with:

**Requirements:**
- Handle 10,000+ concurrent users
- Support 5 languages with real-time translation
- Integrate with existing CRM (Salesforce)
- 99.9% uptime requirement
- <200ms response time
- Budget: $200K implementation, $50K/month operational

**Constraints:**
- Must use cloud infrastructure (AWS/Azure/GCP)
- GDPR compliance required
- Integration with legacy systems (REST APIs only)
- Team expertise: Python, Node.js, limited ML experience

Provide:
1. High-level architecture diagram description
2. Technology stack recommendations with rationale
3. Scalability strategy and cost projections
4. Risk analysis and mitigation plans
5. Implementation phases with timelines
6. Operational considerations and monitoring strategy

Be comprehensive and consider all technical and business aspects.
""",
                "cognitive_enhancement_expected": [
                    "Systematic architecture analysis",
                    "Cost modeling and budget tracking",
                    "Multi-phase workflow planning",
                    "Risk assessment with mitigation strategies",
                    "Technology evaluation with trade-offs",
                ],
            },
            {
                "name": "research_synthesis_challenge",
                "description": "Complex research synthesis with multiple sources",
                "prompt": """
Analyze the current state and future trends of AI in healthcare, focusing on:

**Research Areas:**
1. Diagnostic AI (radiology, pathology, clinical decision support)
2. Drug discovery and development acceleration
3. Personalized medicine and treatment optimization
4. Healthcare operations optimization
5. Ethical considerations and regulatory challenges

**Analysis Requirements:**
- Synthesize current capabilities and limitations
- Identify emerging trends and breakthrough technologies
- Assess market opportunities and challenges
- Evaluate regulatory landscape and compliance issues
- Provide strategic recommendations for healthcare organizations

**Deliverables:**
1. Executive summary with key findings
2. Detailed analysis of each research area
3. Trend analysis with timeline predictions
4. Strategic recommendations with implementation priorities
5. Risk assessment and mitigation strategies

Provide a comprehensive, well-structured analysis that demonstrates deep understanding of the domain.
""",
                "cognitive_enhancement_expected": [
                    "Structured research methodology",
                    "Systematic synthesis across domains",
                    "Evidence-based trend analysis",
                    "Strategic thinking with prioritization",
                    "Comprehensive risk assessment",
                ],
            },
        ]

        return scenarios

    def _define_validation_criteria(self) -> Dict[str, Any]:
        """Define objective criteria for measuring cognitive enhancement"""

        return {
            "quantitative_metrics": {
                "response_structure": {
                    "description": "Organization and structure of response",
                    "scoring": {
                        "excellent": "Clear sections, logical flow, comprehensive coverage",
                        "good": "Well organized with minor gaps",
                        "fair": "Basic organization, some structure",
                        "poor": "Disorganized, unclear structure",
                    },
                },
                "depth_of_analysis": {
                    "description": "Thoroughness and depth of analysis",
                    "scoring": {
                        "excellent": "Multi-layered analysis with nuanced understanding",
                        "good": "Good depth with some sophisticated insights",
                        "fair": "Adequate analysis with basic insights",
                        "poor": "Superficial analysis, lacks depth",
                    },
                },
                "evidence_usage": {
                    "description": "Use of evidence and reasoning",
                    "scoring": {
                        "excellent": "Strong evidence-based reasoning throughout",
                        "good": "Good use of evidence with solid reasoning",
                        "fair": "Some evidence, basic reasoning",
                        "poor": "Little evidence, weak reasoning",
                    },
                },
                "practical_applicability": {
                    "description": "Actionability and practical value",
                    "scoring": {
                        "excellent": "Highly actionable with clear implementation steps",
                        "good": "Good practical value with some actionable elements",
                        "fair": "Some practical value, limited actionability",
                        "poor": "Limited practical value, mostly theoretical",
                    },
                },
                "cognitive_sophistication": {
                    "description": "Sophistication of cognitive processing",
                    "scoring": {
                        "excellent": "Multi-perspective analysis, complex reasoning, meta-cognitive awareness",
                        "good": "Good analytical thinking with some complexity",
                        "fair": "Basic analytical thinking",
                        "poor": "Simple, linear thinking",
                    },
                },
            },
            "process_indicators": {
                "systematic_approach": "Evidence of systematic methodology",
                "cost_awareness": "Consideration of budget and resource constraints",
                "risk_assessment": "Identification and analysis of risks",
                "optimization_thinking": "Evidence of optimization and improvement focus",
                "workflow_intelligence": "Evidence of intelligent workflow or process design",
            },
            "cognitive_enhancement_markers": {
                "external_validation": "Use of external tools or validation",
                "compound_analysis": "Multi-stage or compound analytical processes",
                "budget_integration": "Integration of cost/budget considerations",
                "intelligence_amplification": "Evidence of amplified analytical capabilities",
                "meta_reasoning": "Evidence of reasoning about reasoning",
            },
        }

    def generate_test_prompt_for_fresh_agent(self, scenario_name: str) -> str:
        """Generate test prompt for fresh agent with orchestrator access"""

        scenario = next(
            (s for s in self.test_scenarios if s["name"] == scenario_name), None
        )
        if not scenario:
            raise ValueError(f"Scenario '{scenario_name}' not found")

        orchestrator_prompt = f"""
# COGNITIVE ENHANCEMENT TEST

You have access to the ASEA Orchestrator for cognitive enhancement. The orchestrator is located at:
`/home/opsvi/asea/asea_orchestrator/`

## Available Cognitive Enhancement Capabilities:

1. **Budget Manager Plugin** - Cost analysis, budget tracking, resource optimization
2. **Workflow Intelligence Plugin** - Workflow analysis, optimization recommendations
3. **AI Reasoning Plugin** - Advanced reasoning capabilities (requires API key)
4. **Cognitive Enhancement Plugins** - Pre-analysis, critic, reminder systems

## How to Use the Orchestrator:

You can create and execute workflows using the orchestrator. Example:

```python
# Create a workflow for cognitive enhancement
from asea_orchestrator.core import Orchestrator
from asea_orchestrator.workflow import WorkflowManager
from asea_orchestrator.plugins.types import PluginConfig

# Define workflow steps
workflow_definitions = {{
    "cognitive_analysis": {{
        "steps": [
            {{
                "plugin_name": "budget_manager",
                "parameters": {{"operation": "analyze_costs"}},
                "outputs": {{"analysis": "budget_analysis"}}
            }},
            {{
                "plugin_name": "workflow_intelligence", 
                "parameters": {{"operation": "optimize_approach"}},
                "outputs": {{"recommendations": "optimization_suggestions"}}
            }}
        ]
    }}
}}

# Execute workflow
workflow_manager = WorkflowManager(workflow_definitions)
orchestrator = Orchestrator(plugin_dir, workflow_manager)
result = await orchestrator.run_workflow("cognitive_analysis")
```

## Your Task:

{scenario["prompt"]}

## Instructions:

1. **Use the orchestrator** to enhance your cognitive processing for this task
2. **Apply budget analysis** where relevant using the Budget Manager
3. **Use workflow intelligence** to optimize your analytical approach
4. **Demonstrate cognitive enhancement** through systematic, multi-stage analysis
5. **Show your work** - explain how you used the cognitive enhancement tools

Your response should demonstrate enhanced analytical capabilities through the use of the orchestrator's cognitive enhancement infrastructure.

---

**Test Scenario**: {scenario["name"]}
**Expected Enhancements**: {', '.join(scenario["cognitive_enhancement_expected"])}
"""

        return orchestrator_prompt

    def generate_control_prompt(self, scenario_name: str) -> str:
        """Generate control prompt for agent without cognitive enhancement"""

        scenario = next(
            (s for s in self.test_scenarios if s["name"] == scenario_name), None
        )
        if not scenario:
            raise ValueError(f"Scenario '{scenario_name}' not found")

        control_prompt = f"""
# STANDARD ANALYSIS TEST

{scenario["prompt"]}

---

**Test Scenario**: {scenario["name"]} (Control - No Enhancement Tools)

Please provide a comprehensive response using your standard analytical capabilities.
"""

        return control_prompt

    def create_validation_rubric(self) -> str:
        """Create validation rubric for objective assessment"""

        rubric = """
# COGNITIVE ENHANCEMENT VALIDATION RUBRIC

## Scoring Scale: 1-4 (Poor, Fair, Good, Excellent)

### QUANTITATIVE METRICS:

**1. Response Structure (1-4)**
- Organization and logical flow
- Comprehensive coverage of requirements
- Clear section divisions and transitions

**2. Depth of Analysis (1-4)**
- Thoroughness of investigation
- Nuanced understanding demonstrated
- Multi-layered analytical approach

**3. Evidence Usage (1-4)**
- Quality and relevance of evidence
- Strength of reasoning and justification
- Logical connections between points

**4. Practical Applicability (1-4)**
- Actionability of recommendations
- Implementation feasibility
- Clear next steps provided

**5. Cognitive Sophistication (1-4)**
- Complexity of reasoning demonstrated
- Multi-perspective analysis
- Meta-cognitive awareness

### PROCESS INDICATORS (Present/Absent):

- [ ] Systematic methodology evident
- [ ] Cost/budget awareness demonstrated
- [ ] Risk assessment included
- [ ] Optimization thinking shown
- [ ] Workflow intelligence applied

### COGNITIVE ENHANCEMENT MARKERS (Present/Absent):

- [ ] External tool usage evident
- [ ] Multi-stage analytical process
- [ ] Budget integration shown
- [ ] Intelligence amplification demonstrated
- [ ] Meta-reasoning evidence

### OVERALL ASSESSMENT:

**Total Quantitative Score**: ___/20
**Process Indicators**: ___/5
**Enhancement Markers**: ___/5

**Cognitive Enhancement Evidence**: (Describe specific evidence of enhancement)

**Comparison Notes**: (How does this compare to control agent?)

**Validation Conclusion**: (Enhanced/Not Enhanced/Inconclusive)
"""

        return rubric

    def save_test_materials(self):
        """Save all test materials to files"""

        # Create results directory
        os.makedirs(self.results_dir, exist_ok=True)

        # Save test scenarios
        for scenario in self.test_scenarios:
            # Enhanced agent prompt
            enhanced_prompt = self.generate_test_prompt_for_fresh_agent(
                scenario["name"]
            )
            enhanced_file = (
                f"{self.results_dir}/{scenario['name']}_enhanced_agent_prompt.md"
            )
            with open(enhanced_file, "w") as f:
                f.write(enhanced_prompt)

            # Control agent prompt
            control_prompt = self.generate_control_prompt(scenario["name"])
            control_file = (
                f"{self.results_dir}/{scenario['name']}_control_agent_prompt.md"
            )
            with open(control_file, "w") as f:
                f.write(control_prompt)

        # Save validation rubric
        rubric = self.create_validation_rubric()
        rubric_file = f"{self.results_dir}/validation_rubric.md"
        with open(rubric_file, "w") as f:
            f.write(rubric)

        # Save test framework metadata
        metadata = {
            "created": datetime.now().isoformat(),
            "test_scenarios": [s["name"] for s in self.test_scenarios],
            "validation_criteria": self.validation_criteria,
            "instructions": {
                "enhanced_agent": "Use the enhanced agent prompts with fresh agent sessions",
                "control_agent": "Use control prompts with fresh agent in clean environment",
                "validation": "Use validation rubric for objective assessment",
                "comparison": "Compare scores and evidence between enhanced vs control",
            },
        }

        metadata_file = f"{self.results_dir}/test_framework_metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

        return self.results_dir


def main():
    """Generate test framework materials"""

    print("=== ORCHESTRATOR COGNITIVE ENHANCEMENT TEST FRAMEWORK ===")

    test_framework = OrchestratorCognitiveEnhancementTest()
    results_dir = test_framework.save_test_materials()

    print(f"\n✅ Test materials generated in: {results_dir}")
    print("\nGenerated files:")
    print("📝 Enhanced agent prompts (3 scenarios)")
    print("📝 Control agent prompts (3 scenarios)")
    print("📝 Validation rubric")
    print("📝 Test framework metadata")

    print("\n🧪 TESTING INSTRUCTIONS:")
    print(
        "1. Use enhanced agent prompts with fresh agents that have orchestrator access"
    )
    print("2. Use control prompts with fresh agents in clean environments")
    print("3. Apply validation rubric to both responses")
    print("4. Compare scores and evidence objectively")
    print("5. Document results for cognitive enhancement validation")

    print(f"\n📊 TEST SCENARIOS:")
    for scenario in test_framework.test_scenarios:
        print(f"   • {scenario['name']}: {scenario['description']}")

    return results_dir


if __name__ == "__main__":
    main()
