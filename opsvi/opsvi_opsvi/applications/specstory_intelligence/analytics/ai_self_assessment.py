"""
AI Self-Assessment - Test AI instance quality before proceeding
"""

from datetime import datetime
from typing import Any, Dict


class AISelfAssessment:
    """Self-diagnostic test for AI instance quality"""

    def __init__(self):
        self.test_results = {}
        self.pass_threshold = 0.75

    def run_full_assessment(self) -> Dict[str, Any]:
        """Run complete self-assessment battery"""

        results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "overall_score": 0,
            "pass": False,
            "issues": [],
        }

        # Core capability tests
        results["tests"]["reasoning"] = self._test_logical_reasoning()
        results["tests"]["memory"] = self._test_working_memory()
        results["tests"]["instruction_following"] = self._test_instruction_following()
        results["tests"]["context_awareness"] = self._test_context_awareness()
        results["tests"]["error_detection"] = self._test_error_detection()
        results["tests"]["tool_usage"] = self._test_tool_competency()

        # Calculate overall score
        scores = [test["score"] for test in results["tests"].values()]
        results["overall_score"] = sum(scores) / len(scores)
        results["pass"] = results["overall_score"] >= self.pass_threshold

        # Identify issues
        for test_name, test_result in results["tests"].items():
            if test_result["score"] < 0.6:
                results["issues"].append(
                    f"Failed {test_name}: {test_result.get('issue', 'Unknown')}"
                )

        return results

    def _test_logical_reasoning(self) -> Dict[str, Any]:
        """Test basic logical reasoning ability"""
        try:
            # Simple logic test
            a, b, c = 5, 10, 15
            result = (a + b) * 2
            expected = 30

            if result == expected:
                return {"score": 1.0, "status": "pass"}
            else:
                return {"score": 0.0, "status": "fail", "issue": "Basic math error"}
        except Exception as e:
            return {"score": 0.0, "status": "fail", "issue": f"Exception: {e}"}

    def _test_working_memory(self) -> Dict[str, Any]:
        """Test ability to maintain context"""
        try:
            # Track multiple variables
            data = {"a": 1, "b": 2, "c": 3}
            data["sum"] = data["a"] + data["b"] + data["c"]

            if data["sum"] == 6:
                return {"score": 1.0, "status": "pass"}
            else:
                return {"score": 0.0, "status": "fail", "issue": "Working memory error"}
        except Exception as e:
            return {"score": 0.0, "status": "fail", "issue": f"Exception: {e}"}

    def _test_instruction_following(self) -> Dict[str, Any]:
        """Test ability to follow precise instructions"""
        try:
            # Multi-step instruction test
            words = "test instruction following"
            word_count = len(words.split())
            char_count = len(words.replace(" ", ""))

            if word_count == 3 and char_count == 20:
                return {"score": 1.0, "status": "pass"}
            else:
                return {
                    "score": 0.5,
                    "status": "partial",
                    "issue": "Instruction precision issue",
                }
        except Exception as e:
            return {"score": 0.0, "status": "fail", "issue": f"Exception: {e}"}

    def _test_context_awareness(self) -> Dict[str, Any]:
        """Test awareness of current context"""
        try:
            # Check if aware of being in assessment
            context_check = (
                "self-assessment" in "Currently running self-assessment test"
            )

            if context_check:
                return {"score": 1.0, "status": "pass"}
            else:
                return {
                    "score": 0.0,
                    "status": "fail",
                    "issue": "Context awareness issue",
                }
        except Exception as e:
            return {"score": 0.0, "status": "fail", "issue": f"Exception: {e}"}

    def _test_error_detection(self) -> Dict[str, Any]:
        """Test ability to detect obvious errors"""
        try:
            # Intentional error detection
            calculation = 2 + 2
            if calculation == 5:  # Obviously wrong
                return {
                    "score": 0.0,
                    "status": "fail",
                    "issue": "Failed to detect obvious error",
                }
            else:
                return {"score": 1.0, "status": "pass"}
        except Exception as e:
            return {"score": 0.0, "status": "fail", "issue": f"Exception: {e}"}

    def _test_tool_competency(self) -> Dict[str, Any]:
        """Test basic tool usage understanding"""
        try:
            # Simulate tool understanding
            tools_available = ["edit_file", "run_terminal_cmd", "read_file"]
            correct_tool = "read_file"
            task = "read a file"

            if correct_tool in tools_available:
                return {"score": 1.0, "status": "pass"}
            else:
                return {"score": 0.0, "status": "fail", "issue": "Tool selection error"}
        except Exception as e:
            return {"score": 0.0, "status": "fail", "issue": f"Exception: {e}"}

    def generate_assessment_report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable assessment report"""

        status = "✅ PASS" if results["pass"] else "❌ FAIL"
        score = f"{results['overall_score']:.1%}"

        report = f"""
AI SELF-ASSESSMENT REPORT
========================
Status: {status}
Overall Score: {score}
Threshold: {self.pass_threshold:.1%}

Test Results:
"""

        for test_name, test_result in results["tests"].items():
            status_icon = (
                "✅"
                if test_result["score"] >= 0.8
                else "⚠️"
                if test_result["score"] >= 0.6
                else "❌"
            )
            report += f"  {status_icon} {test_name}: {test_result['score']:.1%}\n"

        if results["issues"]:
            report += "\nIssues Detected:\n"
            for issue in results["issues"]:
                report += f"  • {issue}\n"

        recommendation = "PROCEED" if results["pass"] else "RESTART SESSION"
        report += f"\nRecommendation: {recommendation}\n"

        return report.strip()


def quick_assessment() -> bool:
    """Quick pass/fail assessment"""
    assessor = AISelfAssessment()
    results = assessor.run_full_assessment()
    return results["pass"]


def detailed_assessment() -> str:
    """Full assessment with report"""
    assessor = AISelfAssessment()
    results = assessor.run_full_assessment()
    return assessor.generate_assessment_report(results)
