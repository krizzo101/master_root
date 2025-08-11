#!/usr/bin/env python3
"""
SOPHISTICATION VALIDATION SCRIPT

Comprehensive validation system that checks all enforcement mechanisms
and provides detailed compliance reporting for oamat_sd implementation.
"""

from datetime import datetime
import json
from pathlib import Path
import sys
from typing import Any, Dict, List

# Add the enforcement module to path
sys.path.append(str(Path(__file__).parent / "src" / "enforcement"))

try:
    from implementation_guards import (
        ImplementationGuard,
        RuntimeSophisticationMonitor,
        SophisticationViolationError,
        validate_codebase_sophistication,
    )
except ImportError:
    print("WARNING: Implementation guards not found. Creating minimal validation.")

    class ImplementationGuard:
        FORBIDDEN_PATTERNS = {
            "template_based_agents": [
                "create_researcher_agent",
                "create_implementer_agent",
            ],
            "simple_parallel": ["asyncio.gather"],
            "role_assignments": ["role='researcher'", "role='implementer'"],
        }

        REQUIRED_PATTERNS = {
            "o3_generation": [
                "o3_generate_workflow",
                "o3_generate_agent_specification",
            ],
            "send_api": ["Send(", "langgraph.constants.Send"],
            "dynamic_synthesis": ["synthesize_agent_from_specification"],
        }

        def check_forbidden_patterns(self, code: str) -> List[str]:
            violations = []
            for category, patterns in self.FORBIDDEN_PATTERNS.items():
                for pattern in patterns:
                    if pattern in code:
                        violations.append(f"FORBIDDEN {category}: {pattern}")
            return violations

        def check_required_patterns(self, code: str) -> List[str]:
            validations = []
            for category, patterns in self.REQUIRED_PATTERNS.items():
                for pattern in patterns:
                    if pattern in code:
                        validations.append(f"REQUIRED {category}: {pattern}")
            return validations


class SophisticationValidator:
    """Comprehensive sophistication validation system"""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent
        self.src_path = self.project_root / "src"
        self.guard = ImplementationGuard()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "overall_compliance": 0,
            "violations": [],
            "validations": [],
            "checkpoint_status": {},
            "file_analysis": {},
            "recommendations": [],
        }

    def validate_implementation_contract(self) -> Dict[str, Any]:
        """Validate against the implementation contract requirements"""

        contract_path = self.project_root / "IMPLEMENTATION_CONTRACT.md"
        if not contract_path.exists():
            return {"status": "MISSING", "message": "Implementation contract not found"}

        return {"status": "PRESENT", "message": "Implementation contract exists"}

    def validate_specification_lock_in(self) -> Dict[str, Any]:
        """Validate against specification lock-in requirements"""

        spec_path = self.project_root / "SPECIFICATION_LOCK_IN.md"
        if not spec_path.exists():
            return {"status": "MISSING", "message": "Specification lock-in not found"}

        return {"status": "PRESENT", "message": "Specification lock-in exists"}

    def analyze_codebase_patterns(self) -> Dict[str, Any]:
        """Analyze entire codebase for sophistication patterns"""

        if not self.src_path.exists():
            return {"error": "Source directory not found"}

        python_files = list(self.src_path.rglob("*.py"))
        # Exclude enforcement files from pattern detection (they contain pattern definitions)
        python_files = [f for f in python_files if "enforcement" not in str(f)]

        analysis = {
            "files_analyzed": 0,
            "violations_found": [],
            "patterns_validated": [],
            "compliance_by_file": {},
        }

        for file_path in python_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                # Check violations
                violations = self.guard.check_forbidden_patterns(content)
                validations = self.guard.check_required_patterns(content)

                file_compliance = {
                    "violations": violations,
                    "validations": validations,
                    "compliance_score": self._calculate_file_compliance(
                        violations, validations
                    ),
                }

                analysis["files_analyzed"] += 1
                analysis["violations_found"].extend(
                    [f"{file_path}: {v}" for v in violations]
                )
                analysis["patterns_validated"].extend(
                    [f"{file_path}: {v}" for v in validations]
                )
                analysis["compliance_by_file"][str(file_path)] = file_compliance

            except Exception as e:
                analysis["compliance_by_file"][str(file_path)] = {
                    "error": f"Failed to analyze: {str(e)}"
                }

        return analysis

    def validate_checkpoint_25_percent(self) -> Dict[str, Any]:
        """Validate 25% checkpoint: O3 Analysis Engine"""

        main_agent_path = self.src_path.parent / "smart_decomposition_agent.py"
        if not main_agent_path.exists():
            return {"status": "FAIL", "message": "Main agent file not found"}

        with open(main_agent_path) as f:
            content = f.read()

        requirements = [
            ("o3_model_integration", "o3-mini" in content.lower()),
            ("analysis_capability", "analyze" in content.lower()),
            ("no_simple_analysis", "simple_analysis" not in content),
        ]

        status = "PASS" if all(req[1] for req in requirements) else "FAIL"
        details = {req[0]: req[1] for req in requirements}

        return {"status": status, "details": details}

    def validate_checkpoint_50_percent(self) -> Dict[str, Any]:
        """Validate 50% checkpoint: Dynamic Agent Synthesis"""

        agent_factory_path = self.src_path / "agents" / "agent_factory.py"
        if not agent_factory_path.exists():
            return {"status": "FAIL", "message": "Agent factory not found"}

        with open(agent_factory_path) as f:
            content = f.read()

        requirements = [
            ("specification_based", "specification" in content or "spec" in content),
            ("no_researcher_template", "researcher_template" not in content),
            ("no_implementer_template", "implementer_template" not in content),
            ("no_role_based_creation", "role='researcher'" not in content),
        ]

        status = "PASS" if all(req[1] for req in requirements) else "FAIL"
        details = {req[0]: req[1] for req in requirements}

        return {"status": status, "details": details}

    def validate_checkpoint_75_percent(self) -> Dict[str, Any]:
        """Validate 75% checkpoint: Send API Orchestration"""

        python_files = list(self.src_path.rglob("*.py"))

        send_api_found = False
        asyncio_violations = []

        for file_path in python_files:
            with open(file_path) as f:
                content = f.read()

            if "Send(" in content and "langgraph" in content:
                send_api_found = True

            if "asyncio.gather" in content:
                asyncio_violations.append(str(file_path))

        requirements = [
            ("send_api_present", send_api_found),
            ("no_asyncio_gather", len(asyncio_violations) == 0),
        ]

        status = "PASS" if all(req[1] for req in requirements) else "FAIL"
        details = {req[0]: req[1] for req in requirements}
        if asyncio_violations:
            details["asyncio_violations"] = asyncio_violations

        return {"status": status, "details": details}

    def validate_checkpoint_100_percent(self) -> Dict[str, Any]:
        """Validate 100% checkpoint: Full Sophistication"""

        # Run all previous checkpoints
        checkpoint_25 = self.validate_checkpoint_25_percent()
        checkpoint_50 = self.validate_checkpoint_50_percent()
        checkpoint_75 = self.validate_checkpoint_75_percent()

        # Check for runtime adaptation
        python_files = list(self.src_path.rglob("*.py"))
        adaptation_found = False

        for file_path in python_files:
            with open(file_path) as f:
                content = f.read()

            adaptation_patterns = [
                "adapt_workflow",
                "runtime_adaptation",
                "mid_execution",
            ]
            if any(pattern in content for pattern in adaptation_patterns):
                adaptation_found = True
                break

        all_checkpoints_pass = all(
            checkpoint["status"] == "PASS"
            for checkpoint in [checkpoint_25, checkpoint_50, checkpoint_75]
        )

        status = "PASS" if all_checkpoints_pass and adaptation_found else "FAIL"

        return {
            "status": status,
            "checkpoint_25": checkpoint_25,
            "checkpoint_50": checkpoint_50,
            "checkpoint_75": checkpoint_75,
            "runtime_adaptation": adaptation_found,
        }

    def _calculate_file_compliance(
        self, violations: List[str], validations: List[str]
    ) -> float:
        """Calculate compliance score for a file"""
        if not violations and not validations:
            return 0.0  # No patterns detected

        total_patterns = len(violations) + len(validations)
        if total_patterns == 0:
            return 0.0

        return (len(validations) / total_patterns) * 100

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive sophistication compliance report"""

        print("🔍 Running comprehensive sophistication validation...")

        # Contract validation
        self.results["contract_validation"] = self.validate_implementation_contract()

        # Specification validation
        self.results["specification_validation"] = self.validate_specification_lock_in()

        # Codebase analysis
        print("📂 Analyzing codebase patterns...")
        self.results["codebase_analysis"] = self.analyze_codebase_patterns()

        # Checkpoint validations
        print("📊 Validating implementation checkpoints...")
        self.results["checkpoint_status"][
            "25_percent"
        ] = self.validate_checkpoint_25_percent()
        self.results["checkpoint_status"][
            "50_percent"
        ] = self.validate_checkpoint_50_percent()
        self.results["checkpoint_status"][
            "75_percent"
        ] = self.validate_checkpoint_75_percent()
        self.results["checkpoint_status"][
            "100_percent"
        ] = self.validate_checkpoint_100_percent()

        # Calculate overall compliance
        self._calculate_overall_compliance()

        # Generate recommendations
        self._generate_recommendations()

        return self.results

    def _calculate_overall_compliance(self):
        """Calculate overall compliance score"""

        # Checkpoint compliance (40% weight)
        checkpoint_scores = []
        for checkpoint_name, checkpoint_data in self.results[
            "checkpoint_status"
        ].items():
            if checkpoint_data["status"] == "PASS":
                checkpoint_scores.append(100)
            else:
                checkpoint_scores.append(0)

        checkpoint_compliance = (
            sum(checkpoint_scores) / len(checkpoint_scores) if checkpoint_scores else 0
        )

        # Codebase compliance (60% weight)
        codebase_analysis = self.results["codebase_analysis"]
        if "compliance_by_file" in codebase_analysis:
            file_scores = [
                file_data.get("compliance_score", 0)
                for file_data in codebase_analysis["compliance_by_file"].values()
                if isinstance(file_data, dict) and "compliance_score" in file_data
            ]
            codebase_compliance = (
                sum(file_scores) / len(file_scores) if file_scores else 0
            )
        else:
            codebase_compliance = 0

        # Weighted overall compliance
        self.results["overall_compliance"] = (
            checkpoint_compliance * 0.4 + codebase_compliance * 0.6
        )

    def _generate_recommendations(self):
        """Generate recommendations based on analysis"""

        recommendations = []

        # Check contract and specification
        if self.results["contract_validation"]["status"] == "MISSING":
            recommendations.append(
                "❌ CRITICAL: Implementation contract missing - create before proceeding"
            )

        if self.results["specification_validation"]["status"] == "MISSING":
            recommendations.append(
                "❌ CRITICAL: Specification lock-in missing - define requirements"
            )

        # Check checkpoints
        for checkpoint_name, checkpoint_data in self.results[
            "checkpoint_status"
        ].items():
            if checkpoint_data["status"] == "FAIL":
                recommendations.append(
                    f"🔴 CHECKPOINT FAILURE: {checkpoint_name} requirements not met"
                )

        # Check violations
        codebase_analysis = self.results["codebase_analysis"]
        if codebase_analysis.get("violations_found"):
            recommendations.append(
                f"⚠️  {len(codebase_analysis['violations_found'])} sophistication violations detected"
            )

        # Overall compliance recommendations
        compliance = self.results["overall_compliance"]
        if compliance < 50:
            recommendations.append(
                "🚨 CRITICAL: Implementation is not sophisticated - major refactoring required"
            )
        elif compliance < 75:
            recommendations.append(
                "⚠️  WARNING: Implementation needs sophistication improvements"
            )
        elif compliance < 90:
            recommendations.append("📈 GOOD: Minor sophistication improvements needed")
        else:
            recommendations.append(
                "✅ EXCELLENT: Implementation meets sophistication requirements"
            )

        self.results["recommendations"] = recommendations

    def print_report(self):
        """Print formatted validation report"""

        print("\n" + "=" * 80)
        print("🎯 OAMAT_SD SOPHISTICATION VALIDATION REPORT")
        print("=" * 80)

        print(f"\n📊 OVERALL COMPLIANCE: {self.results['overall_compliance']:.1f}%")

        # Print checkpoint status
        print("\n📋 CHECKPOINT STATUS:")
        for checkpoint_name, checkpoint_data in self.results[
            "checkpoint_status"
        ].items():
            status_icon = "✅" if checkpoint_data["status"] == "PASS" else "❌"
            print(f"  {status_icon} {checkpoint_name}: {checkpoint_data['status']}")

        # Print violations summary
        codebase_analysis = self.results["codebase_analysis"]
        violation_count = len(codebase_analysis.get("violations_found", []))
        validation_count = len(codebase_analysis.get("patterns_validated", []))

        print("\n📂 CODEBASE ANALYSIS:")
        print(f"  📁 Files analyzed: {codebase_analysis.get('files_analyzed', 0)}")
        print(f"  ❌ Violations found: {violation_count}")
        print(f"  ✅ Patterns validated: {validation_count}")

        # Print recommendations
        print("\n💡 RECOMMENDATIONS:")
        for recommendation in self.results["recommendations"]:
            print(f"  {recommendation}")

        print("\n" + "=" * 80)


def main():
    """Main validation execution"""

    # Initialize validator
    validator = SophisticationValidator()

    # Generate comprehensive report
    results = validator.generate_comprehensive_report()

    # Print formatted report
    validator.print_report()

    # Save detailed results to file
    results_file = Path("sophistication_validation_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Detailed results saved to: {results_file}")

    # Exit with appropriate code
    overall_compliance = results["overall_compliance"]
    if overall_compliance < 75:
        print(
            f"\n🚨 VALIDATION FAILED: Compliance {overall_compliance:.1f}% < 75% required"
        )
        sys.exit(1)
    else:
        print(
            f"\n✅ VALIDATION PASSED: Compliance {overall_compliance:.1f}% >= 75% required"
        )
        sys.exit(0)


if __name__ == "__main__":
    main()
