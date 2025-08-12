#!/usr/bin/env python3
"""
Autonomous Systems Interface

Clean interface to working autonomous systems tools.
Provides easy access to validated operational tools.
"""
import sys
import os
from typing import Dict, Any

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from core_systems.mistake_prevention_system import MistakePreventionSystem

    MISTAKE_PREVENTION_AVAILABLE = True
except ImportError as e:
    print(f"Failed to import mistake_prevention_system: {e}")
    MISTAKE_PREVENTION_AVAILABLE = False

try:
    from core_systems.session_continuity_system import SessionContinuitySystem

    SESSION_CONTINUITY_AVAILABLE = True
except ImportError as e:
    print(f"Failed to import session_continuity_system: {e}")
    SESSION_CONTINUITY_AVAILABLE = False

try:
    from core_systems.autonomous_decision_system import AutonomousDecisionSystem

    DECISION_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"Failed to import autonomous_decision_system: {e}")
    DECISION_SYSTEM_AVAILABLE = False

try:
    from cognitive_enhancement_orchestrator import (
        enhance_decision_making,
        enhance_analysis,
        validate_cognitive_enhancement,
    )

    COGNITIVE_ENHANCEMENT_AVAILABLE = True
except ImportError:
    COGNITIVE_ENHANCEMENT_AVAILABLE = False

# Import the new low-level tool provider
from core_tool_provider import (
    get_session_continuity_tool,
    get_decision_system_tool,
    get_mistake_prevention_tool,
)


class AutonomousSystemsInterface:
    """
    Clean interface to working autonomous systems

    Provides access to validated tools:
    - Mistake prevention (AQL validation, error prevention)
    - Session continuity (path validation, context management)
    - Decision enhancement (autonomous decision analysis)
    - Cognitive enhancement (orchestrator-based enhancement)
    """

    def __init__(self):
        self.available_systems = self._check_available_systems()
        if self.available_systems["mistake_prevention"]:
            self.mistake_prevention = get_mistake_prevention_tool()
        if self.available_systems["session_continuity"]:
            self.session_continuity = get_session_continuity_tool()
        if self.available_systems["decision_system"]:
            self.decision_system = get_decision_system_tool()

    def _check_available_systems(self) -> Dict[str, bool]:
        """Check which systems are available"""
        return {
            "mistake_prevention": MISTAKE_PREVENTION_AVAILABLE,
            "session_continuity": SESSION_CONTINUITY_AVAILABLE,
            "decision_system": DECISION_SYSTEM_AVAILABLE,
            "cognitive_enhancement": COGNITIVE_ENHANCEMENT_AVAILABLE,
        }

    def get_system_status(self) -> Dict[str, Any]:
        """Get status of all autonomous systems"""
        status = {
            "available_systems": self.available_systems,
            "working_systems": [
                name for name, available in self.available_systems.items() if available
            ],
            "total_available": sum(self.available_systems.values()),
        }

        # Test cognitive enhancement if available
        if self.available_systems["cognitive_enhancement"]:
            try:
                cognitive_status = validate_cognitive_enhancement()
                status["cognitive_enhancement_status"] = cognitive_status["status"]
            except Exception as e:
                status["cognitive_enhancement_error"] = str(e)

        return status

    # Mistake Prevention Interface
    def validate_aql(self, query: str) -> Dict[str, Any]:
        """Validate AQL query syntax"""
        if not self.available_systems["mistake_prevention"]:
            return {
                "available": False,
                "message": "Mistake prevention system not available",
            }

        try:
            return self.mistake_prevention.validate_aql_query(query)
        except Exception as e:
            return {"error": str(e), "available": True}

    def prevent_mistakes(
        self, operation_type: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get mistake prevention guidance"""
        if not self.available_systems["mistake_prevention"]:
            return {
                "available": False,
                "message": "Mistake prevention system not available",
            }

        try:
            return self.mistake_prevention.get_operational_knowledge_summary()
        except Exception as e:
            return {"error": str(e), "available": True}

    # Session Continuity Interface
    def get_session_info(self) -> Dict[str, Any]:
        """Get session context and continuity information"""
        if not self.available_systems["session_continuity"]:
            return {
                "available": False,
                "message": "Session continuity system not available",
            }

        try:
            return self.session_continuity.get_session_startup_checklist()
        except Exception as e:
            return {"error": str(e), "available": True}

    def validate_file_paths(self, paths: list) -> Dict[str, Any]:
        """Validate file paths for session continuity"""
        if not self.available_systems["session_continuity"]:
            return {
                "available": False,
                "message": "Session continuity system not available",
            }

        try:
            return self.session_continuity.validate_before_operation(
                "shell_command", paths[0] if paths else ""
            )
        except Exception as e:
            return {"error": str(e), "available": True}

    # Decision System Interface
    def assess_decision(self, context: str, rationale: str) -> Dict[str, Any]:
        """Assess decision quality"""
        if not self.available_systems["decision_system"]:
            return {"available": False, "message": "Decision system not available"}

        try:
            return self.decision_system.assess_decision_quality(context, rationale)
        except Exception as e:
            return {"error": str(e), "available": True}

    def autonomous_decision(self, decision_context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform autonomous decision analysis"""
        if not self.available_systems["decision_system"]:
            return {"available": False, "message": "Decision system not available"}

        try:
            return self.decision_system.plan_next_autonomous_phase(decision_context)
        except Exception as e:
            return {"error": str(e), "available": True}

    # Cognitive Enhancement Interface
    def enhance_decision_making(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance decision making using orchestrator"""
        if not self.available_systems["cognitive_enhancement"]:
            return {
                "available": False,
                "message": "Cognitive enhancement not available",
            }

        try:
            return enhance_decision_making(context)
        except Exception as e:
            return {"error": str(e), "available": True}

    def enhance_analysis(self, analysis_context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance analysis using orchestrator"""
        if not self.available_systems["cognitive_enhancement"]:
            return {
                "available": False,
                "message": "Cognitive enhancement not available",
            }

        try:
            return enhance_analysis(analysis_context)
        except Exception as e:
            return {"error": str(e), "available": True}

    def validate_cognitive_enhancement(self) -> Dict[str, Any]:
        """Validate cognitive enhancement capabilities"""
        if not self.available_systems["cognitive_enhancement"]:
            return {
                "available": False,
                "message": "Cognitive enhancement not available",
            }

        try:
            return validate_cognitive_enhancement()
        except Exception as e:
            return {"error": str(e), "available": True}


# Global interface instance
autonomous_systems = AutonomousSystemsInterface()
