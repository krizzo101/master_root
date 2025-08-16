#!/usr/bin/env python3
"""
Infrastructure Change Validator
Systematic validation for infrastructure changes

This system prevents mistakes like forgetting to update database references
or project rules when making infrastructure changes.
"""

from datetime import datetime
from typing import Dict, List, Any


class InfrastructureChangeValidator:
    """Systematic infrastructure change validation"""

    def __init__(self):
        self.validation_steps = {
            "pre_change_assessment": "Assess impact before making changes",
            "change_execution": "Execute change with validation checkpoints",
            "database_update_check": "Check and update database references",
            "rules_update_check": "Check and update project rules",
            "system_message_check": "Check if system message needs updating",
            "integration_validation": "Validate integration points still work",
            "documentation": "Document change and validation results",
        }

        self.common_change_types = {
            "tool_location_change": {
                "description": "Moving operational tools to new location",
                "impact_areas": [
                    "database_references",
                    "project_rules",
                    "system_message",
                    "integration_points",
                ],
                "validation_queries": [
                    "FOR doc IN core_memory FILTER CONTAINS(doc.content, 'old_path') RETURN doc",
                    "Search .cursor/rules/ for outdated references",
                ],
            },
            "capability_development": {
                "description": "Developing new autonomous capabilities",
                "impact_areas": [
                    "database_documentation",
                    "project_rules",
                    "integration_points",
                ],
                "validation_queries": [
                    "Update rules with usage instructions",
                    "Document capability in core_memory",
                ],
            },
            "system_architecture_change": {
                "description": "Changes to system architecture or organization",
                "impact_areas": [
                    "database_schema",
                    "project_rules",
                    "system_message",
                    "all_integrations",
                ],
                "validation_queries": ["Comprehensive impact assessment required"],
            },
        }

    def validate_infrastructure_change(
        self, change_description: str, change_type: str = "general"
    ) -> Dict[str, Any]:
        """Validate infrastructure change systematically"""

        validation_result = {
            "change_description": change_description,
            "change_type": change_type,
            "validation_timestamp": datetime.now().isoformat(),
            "validation_steps_completed": [],
            "impact_assessment": {},
            "required_updates": [],
            "validation_checklist": [],
            "validation_success": False,
        }

        try:
            # Step 1: Pre-change assessment
            impact_assessment = self._assess_change_impact(
                change_description, change_type
            )
            validation_result["impact_assessment"] = impact_assessment
            validation_result["validation_steps_completed"].append(
                "pre_change_assessment"
            )

            # Step 2: Generate required updates list
            required_updates = self._generate_required_updates(impact_assessment)
            validation_result["required_updates"] = required_updates

            # Step 3: Generate validation checklist
            validation_checklist = self._generate_validation_checklist(
                change_type, required_updates
            )
            validation_result["validation_checklist"] = validation_checklist

            # Step 4: Validation guidance
            validation_guidance = self._generate_validation_guidance(change_type)
            validation_result["validation_guidance"] = validation_guidance

            validation_result["validation_success"] = True

        except Exception as e:
            validation_result["validation_error"] = str(e)
            validation_result["validation_success"] = False

        return validation_result

    def _assess_change_impact(
        self, change_description: str, change_type: str
    ) -> Dict[str, Any]:
        """Assess impact of proposed change"""

        impact_assessment = {
            "change_scope": self._determine_change_scope(change_description),
            "affected_systems": self._identify_affected_systems(
                change_description, change_type
            ),
            "risk_level": self._assess_risk_level(change_description, change_type),
            "complexity": self._assess_complexity(change_description),
        }

        return impact_assessment

    def _generate_required_updates(
        self, impact_assessment: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate list of required updates based on impact assessment"""

        required_updates = []

        affected_systems = impact_assessment.get("affected_systems", [])

        if "database_references" in affected_systems:
            required_updates.append(
                {
                    "update_type": "database_references",
                    "description": "Update database references to new paths/locations",
                    "validation_method": "AQL query to find and update references",
                    "priority": "high",
                }
            )

        if "project_rules" in affected_systems:
            required_updates.append(
                {
                    "update_type": "project_rules",
                    "description": "Update project rules with new paths/instructions",
                    "validation_method": "Search and update .cursor/rules/ files",
                    "priority": "high",
                }
            )

        if "system_message" in affected_systems:
            required_updates.append(
                {
                    "update_type": "system_message",
                    "description": "Update system message with new information",
                    "validation_method": "Review and update system message content",
                    "priority": "medium",
                }
            )

        if "integration_points" in affected_systems:
            required_updates.append(
                {
                    "update_type": "integration_points",
                    "description": "Validate and update integration points",
                    "validation_method": "Test integration functionality",
                    "priority": "high",
                }
            )

        return required_updates

    def _generate_validation_checklist(
        self, change_type: str, required_updates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate systematic validation checklist"""

        checklist = []

        # Pre-change validation
        checklist.append(
            {
                "step": "pre_change_validation",
                "description": "Use autonomous decision system to assess change impact",
                "command": "python3 autonomous_decision_system.py assess 'infrastructure_change' 'change_description'",
                "required": True,
            }
        )

        # Change execution with validation
        checklist.append(
            {
                "step": "change_execution",
                "description": "Execute change with systematic validation",
                "command": "Document each step of the change process",
                "required": True,
            }
        )

        # Post-change validation for each required update
        for update in required_updates:
            checklist.append(
                {
                    "step": f"validate_{update['update_type']}",
                    "description": f"Validate {update['description']}",
                    "command": update["validation_method"],
                    "required": update["priority"] == "high",
                }
            )

        # Final validation
        checklist.append(
            {
                "step": "final_validation",
                "description": "Validate all systems work correctly after change",
                "command": "Test critical functionality end-to-end",
                "required": True,
            }
        )

        return checklist

    def _generate_validation_guidance(self, change_type: str) -> Dict[str, Any]:
        """Generate specific validation guidance for change type"""

        if change_type in self.common_change_types:
            change_info = self.common_change_types[change_type]
            return {
                "change_type": change_type,
                "description": change_info["description"],
                "impact_areas": change_info["impact_areas"],
                "validation_queries": change_info["validation_queries"],
                "specific_guidance": f"This is a {change_type} - pay special attention to {', '.join(change_info['impact_areas'])}",
            }
        else:
            return {
                "change_type": "general",
                "description": "General infrastructure change",
                "impact_areas": [
                    "database_references",
                    "project_rules",
                    "integration_points",
                ],
                "validation_queries": ["Check all references to changed components"],
                "specific_guidance": "Perform comprehensive impact assessment for this general change",
            }

    def _determine_change_scope(self, change_description: str) -> str:
        """Determine scope of change"""
        if (
            "tool" in change_description.lower()
            or "system" in change_description.lower()
        ):
            return "system_level"
        elif "capability" in change_description.lower():
            return "capability_level"
        elif "rule" in change_description.lower():
            return "rule_level"
        else:
            return "general"

    def _identify_affected_systems(
        self, change_description: str, change_type: str
    ) -> List[str]:
        """Identify systems affected by change"""
        affected_systems = []

        if (
            "move" in change_description.lower()
            or "location" in change_description.lower()
        ):
            affected_systems.extend(
                ["database_references", "project_rules", "system_message"]
            )

        if (
            "tool" in change_description.lower()
            or "system" in change_description.lower()
        ):
            affected_systems.extend(["integration_points", "operational_protocols"])

        if "capability" in change_description.lower():
            affected_systems.extend(["database_documentation", "project_rules"])

        return list(set(affected_systems))  # Remove duplicates

    def _assess_risk_level(self, change_description: str, change_type: str) -> str:
        """Assess risk level of change"""
        risk_indicators = ["core", "critical", "fundamental", "system", "all"]

        if any(
            indicator in change_description.lower() for indicator in risk_indicators
        ):
            return "high"
        elif (
            "tool" in change_description.lower()
            or "capability" in change_description.lower()
        ):
            return "medium"
        else:
            return "low"

    def _assess_complexity(self, change_description: str) -> str:
        """Assess complexity of change"""
        complexity_indicators = ["multiple", "system", "architecture", "comprehensive"]

        if any(
            indicator in change_description.lower()
            for indicator in complexity_indicators
        ):
            return "high"
        elif (
            "move" in change_description.lower()
            or "update" in change_description.lower()
        ):
            return "medium"
        else:
            return "low"

    def generate_validation_report(self, validation_result: Dict[str, Any]) -> str:
        """Generate validation report"""

        report = f"""
=== INFRASTRUCTURE CHANGE VALIDATION REPORT ===
Change: {validation_result['change_description']}
Type: {validation_result['change_type']}
Timestamp: {validation_result['validation_timestamp']}
Validation Success: {'✓' if validation_result['validation_success'] else '✗'}

=== IMPACT ASSESSMENT ===
Scope: {validation_result['impact_assessment'].get('change_scope', 'unknown')}
Risk Level: {validation_result['impact_assessment'].get('risk_level', 'unknown')}
Complexity: {validation_result['impact_assessment'].get('complexity', 'unknown')}
Affected Systems: {', '.join(validation_result['impact_assessment'].get('affected_systems', []))}

=== REQUIRED UPDATES ===
"""

        for update in validation_result.get("required_updates", []):
            report += f"- {update['update_type']}: {update['description']} (Priority: {update['priority']})\n"

        report += "\n=== VALIDATION CHECKLIST ===\n"
        for step in validation_result.get("validation_checklist", []):
            required_marker = "REQUIRED" if step["required"] else "OPTIONAL"
            report += f"[{required_marker}] {step['description']}\n"
            report += f"  Command: {step['command']}\n\n"

        return report


def main():
    """Test infrastructure change validator"""

    print("=== TESTING INFRASTRUCTURE CHANGE VALIDATOR ===")

    validator = InfrastructureChangeValidator()

    # Test with the actual change that caused the issue
    test_change = "Move autonomous operational tools from /development/temp/ to /development/autonomous_systems/"

    validation_result = validator.validate_infrastructure_change(
        test_change, "tool_location_change"
    )

    report = validator.generate_validation_report(validation_result)
    print(report)

    return validation_result


if __name__ == "__main__":
    main()
