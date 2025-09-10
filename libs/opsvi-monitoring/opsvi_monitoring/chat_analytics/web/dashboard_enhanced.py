"""
Enhanced Dashboard with Project Intelligence Integration

This module extends the existing dashboard with project intelligence correlations.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, render_template, request

# Add parent paths for imports
sys.path.insert(0, "/home/opsvi/master_root/libs/opsvi-monitoring")
sys.path.insert(0, "/home/opsvi/master_root")

from opsvi_monitoring.chat_analytics.intelligence import (
    AgentAnalyzer,
    ChangeTracker,
    CodeContextExtractor,
    ProjectIntelligenceCorrelator,
    SymbolTracker,
)

# Initialize Flask app
app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

# Initialize intelligence components
correlator = ProjectIntelligenceCorrelator()
code_extractor = CodeContextExtractor()
symbol_tracker = SymbolTracker()
change_tracker = ChangeTracker()
agent_analyzer = AgentAnalyzer()


# ============================================================================
# CODE EVOLUTION ENDPOINTS
# ============================================================================


@app.route("/api/code-evolution/<session_id>")
def api_code_evolution(session_id: str):
    """
    Track how code evolved during a session.

    Returns timeline of file changes with before/after metrics.
    """
    try:
        # Establish baseline
        baseline = change_tracker.establish_baseline(session_id)

        # Get change patterns
        patterns = change_tracker.detect_change_patterns(session_id)

        # Get impact analysis
        impact = change_tracker.calculate_impact_score(session_id)

        # Get file evolution for hot files
        evolution_data = []
        for hot_file in patterns.get("hot_files", [])[:5]:
            file_path = hot_file["file"]
            evolution = change_tracker.get_file_evolution(file_path, session_id)
            evolution_data.append(
                {
                    "file": file_path,
                    "changes": hot_file["changes"],
                    "timeline": evolution,
                }
            )

        return jsonify(
            {
                "session_id": session_id,
                "baseline": {
                    "total_files": baseline["metrics"]["total_files"],
                    "total_functions": baseline["metrics"]["total_functions"],
                    "total_classes": baseline["metrics"]["total_classes"],
                    "total_lines": baseline["metrics"]["total_lines"],
                },
                "patterns": patterns,
                "impact": impact,
                "file_evolution": evolution_data,
                "recommendations": change_tracker._generate_recommendations(
                    {
                        "patterns": patterns,
                        "impact": impact,
                        "hot_files": patterns.get("hot_files", []),
                    }
                ),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/symbol-discussion/<symbol_name>")
def api_symbol_discussion(symbol_name: str):
    """
    Find all chat discussions about a symbol.

    Returns messages mentioning the symbol with context.
    """
    try:
        # Get symbol metadata
        metadata = symbol_tracker.get_symbol_metadata(symbol_name)

        # Get discussion history
        history = symbol_tracker.get_symbol_history(symbol_name, limit=50)

        # Get symbol relationships
        relationships = symbol_tracker.get_symbol_relationships(symbol_name)

        # Get evolution analysis
        evolution = symbol_tracker.analyze_symbol_evolution(symbol_name)

        return jsonify(
            {
                "symbol": symbol_name,
                "metadata": metadata,
                "history": history,
                "relationships": relationships,
                "evolution": evolution,
                "summary": {
                    "total_references": len(history),
                    "sessions": evolution.get("sessions", 0),
                    "files_affected": evolution.get("files_affected", 0),
                    "reference_types": evolution.get("reference_types", {}),
                },
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/agent-utilization")
def api_agent_utilization():
    """
    Analyze which agents are most discussed/modified.

    Correlates agent_architecture with chat activity.
    """
    try:
        session_id = request.args.get("session_id")

        # Get utilization analysis
        utilization = agent_analyzer.analyze_agent_utilization(session_id)

        # Get agent patterns
        patterns = agent_analyzer.detect_agent_patterns(session_id)

        # Get hierarchy
        hierarchy = agent_analyzer.get_agent_hierarchy()

        return jsonify(
            {
                "utilization": utilization,
                "patterns": patterns,
                "hierarchy": hierarchy,
                "summary": {
                    "total_agents": utilization["summary"]["total_agents"],
                    "agents_used": utilization["summary"]["agents_used"],
                    "total_invocations": utilization["summary"]["total_invocations"],
                    "most_used": utilization["most_used"][:5]
                    if utilization["most_used"]
                    else [],
                    "recommendations": patterns.get("recommendations", []),
                },
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/hot-files")
def api_hot_files():
    """
    Identify files with most chat activity.

    Combines file_elements with chat references.
    """
    try:
        days = int(request.args.get("days", 7))
        limit = int(request.args.get("limit", 20))

        # Get hot symbols to find associated files
        hot_symbols = symbol_tracker.get_hot_symbols(days=days)

        # Aggregate by file
        file_activity = {}
        for symbol in hot_symbols:
            metadata = symbol_tracker.get_symbol_metadata(symbol["name"])
            for location in metadata.get("locations", []):
                if isinstance(location, dict):
                    file_path = location.get("file")
                elif isinstance(location, str):
                    file_path = location
                else:
                    continue

                if file_path:
                    if file_path not in file_activity:
                        file_activity[file_path] = {
                            "path": file_path,
                            "symbols": [],
                            "total_references": 0,
                            "complexity_score": 0,
                        }

                    file_activity[file_path]["symbols"].append(symbol["name"])
                    file_activity[file_path]["total_references"] += symbol["references"]
                    file_activity[file_path]["complexity_score"] += symbol.get(
                        "complexity", 0
                    )

        # Sort by activity
        hot_files = sorted(
            file_activity.values(), key=lambda x: x["total_references"], reverse=True
        )[:limit]

        # Add file metrics
        for file_info in hot_files:
            # Get file elements
            file_elements = correlator._get_file_elements(file_info["path"])
            if file_elements:
                file_info["metrics"] = {
                    "functions": file_elements.get("fn_count", 0),
                    "classes": file_elements.get("class_count", 0),
                    "lines": file_elements.get("line_count", 0),
                }

            # Get evolution
            evolution = change_tracker.get_file_evolution(file_info["path"])
            file_info["changes"] = len(evolution)
            file_info["last_modified"] = (
                evolution[-1]["timestamp"] if evolution else None
            )

        return jsonify(
            {
                "hot_files": hot_files,
                "period_days": days,
                "total_files": len(file_activity),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/complexity-impact/<session_id>")
def api_complexity_impact(session_id: str):
    """
    Analyze complexity changes during session.

    Uses QualityQuickCollector data when available.
    """
    try:
        # Get baseline and current complexity
        baseline = change_tracker.establish_baseline(session_id)
        impact = change_tracker.calculate_impact_score(session_id)

        # Get change patterns
        patterns = change_tracker.detect_change_patterns(session_id)

        # Calculate complexity changes
        complexity_changes = {
            "functions": {
                "before": baseline["metrics"]["total_functions"],
                "after": baseline["metrics"]["total_functions"]
                + impact["metrics"]["functions_added"]
                - impact["metrics"]["functions_removed"],
                "delta": impact["metrics"]["functions_added"]
                - impact["metrics"]["functions_removed"],
            },
            "classes": {
                "before": baseline["metrics"]["total_classes"],
                "after": baseline["metrics"]["total_classes"]
                + impact["metrics"]["classes_added"]
                - impact["metrics"]["classes_removed"],
                "delta": impact["metrics"]["classes_added"]
                - impact["metrics"]["classes_removed"],
            },
            "lines": {
                "before": baseline["metrics"]["total_lines"],
                "after": baseline["metrics"]["total_lines"]
                + impact["metrics"]["lines_added"]
                - impact["metrics"]["lines_removed"],
                "delta": impact["metrics"]["lines_added"]
                - impact["metrics"]["lines_removed"],
            },
        }

        # Determine complexity trend
        if (
            complexity_changes["functions"]["delta"] > 10
            or complexity_changes["classes"]["delta"] > 5
        ):
            trend = "increasing"
            trend_severity = "high"
        elif (
            complexity_changes["functions"]["delta"] > 5
            or complexity_changes["classes"]["delta"] > 2
        ):
            trend = "increasing"
            trend_severity = "moderate"
        elif (
            complexity_changes["functions"]["delta"] < -5
            or complexity_changes["classes"]["delta"] < -2
        ):
            trend = "decreasing"
            trend_severity = "positive"
        else:
            trend = "stable"
            trend_severity = "neutral"

        return jsonify(
            {
                "session_id": session_id,
                "complexity_changes": complexity_changes,
                "impact_score": impact["impact_score"],
                "trend": {"direction": trend, "severity": trend_severity},
                "hot_files": patterns.get("hot_files", [])[:5],
                "recommendations": [
                    "Consider breaking down complex functions"
                    if complexity_changes["functions"]["delta"] > 10
                    else None,
                    "Good job reducing complexity" if trend == "decreasing" else None,
                    "Review new classes for proper abstraction"
                    if complexity_changes["classes"]["delta"] > 5
                    else None,
                ],
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# SESSION INTELLIGENCE ENDPOINTS
# ============================================================================


@app.route("/api/session-intelligence/<session_id>")
def api_session_intelligence(session_id: str):
    """
    Get comprehensive intelligence report for a session.

    Combines all intelligence components into a unified report.
    """
    try:
        # Get base intelligence from correlator
        base_report = correlator.get_session_intelligence(session_id)

        # Add symbol analysis
        symbol_report = symbol_tracker.generate_symbol_report(session_id)

        # Add change analysis
        change_report = change_tracker.generate_change_report(session_id)

        # Add agent analysis
        agent_report = agent_analyzer.generate_agent_report(session_id)

        # Combine into comprehensive report
        intelligence_report = {
            "session_id": session_id,
            "overview": {
                "files_affected": len(base_report["files_affected"]),
                "symbols_discussed": len(base_report["symbols_discussed"]),
                "agents_utilized": agent_report["summary"]["agents_used"],
                "total_changes": change_report["summary"]["total_changes"],
                "impact_score": change_report["summary"]["impact_score"],
            },
            "files": base_report["files_affected"][:10],
            "symbols": {
                "top_discussed": base_report["symbols_discussed"][:10],
                "undefined": symbol_report.get("undefined", []),
                "hot_symbols": symbol_report.get("hot_symbols", [])[:5],
            },
            "changes": {
                "patterns": change_report["patterns"],
                "timeline": change_report["timeline"][:20],
                "hot_files": change_report["hot_files"][:5],
                "impact": change_report["impact"],
            },
            "agents": {
                "most_used": agent_report["hot_agents"][:5],
                "patterns": agent_report["patterns"],
                "utilization_rate": (
                    agent_report["summary"]["agents_used"]
                    / agent_report["summary"]["total_agents"]
                    * 100
                )
                if agent_report["summary"]["total_agents"] > 0
                else 0,
            },
            "recommendations": list(
                set(
                    change_report.get("recommendations", [])
                    + agent_report.get("recommendations", [])
                )
            ),
        }

        return jsonify(intelligence_report)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/code-context/extract", methods=["POST"])
def api_extract_code_context():
    """
    Extract code context from a message.

    Analyzes message content for code elements.
    """
    try:
        data = request.get_json()
        message = data.get("message", "")

        # Extract context
        context = code_extractor.extract_context(message)

        # Analyze density
        density = code_extractor.analyze_code_density(message)

        return jsonify({"context": context, "density": density})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pattern-detection")
def api_pattern_detection():
    """
    Detect patterns across all sessions or specific session.

    Identifies refactoring, debugging, feature development patterns.
    """
    try:
        session_id = request.args.get("session_id")
        pattern_type = request.args.get("type", "all")

        patterns = {
            "change_patterns": {},
            "symbol_patterns": {},
            "agent_patterns": {},
            "insights": [],
        }

        # Get change patterns
        if pattern_type in ["all", "changes"]:
            if session_id:
                patterns["change_patterns"] = change_tracker.detect_change_patterns(
                    session_id
                )
            else:
                # Would need to implement cross-session analysis
                patterns["change_patterns"] = {
                    "message": "Session ID required for change patterns"
                }

        # Get symbol patterns
        if pattern_type in ["all", "symbols"]:
            hot_symbols = symbol_tracker.get_hot_symbols(session_id, days=30)
            patterns["symbol_patterns"] = {
                "hot_symbols": hot_symbols[:10],
                "total_unique": len(hot_symbols),
            }

        # Get agent patterns
        if pattern_type in ["all", "agents"]:
            patterns["agent_patterns"] = agent_analyzer.detect_agent_patterns(
                session_id
            )

        # Generate insights
        if patterns["change_patterns"].get("total_changes", 0) > 50:
            patterns["insights"].append(
                "High volume of changes detected - consider smaller, focused sessions"
            )

        if patterns["symbol_patterns"].get("total_unique", 0) > 100:
            patterns["insights"].append(
                "Large number of symbols discussed - complex session detected"
            )

        if patterns["agent_patterns"].get("usage_patterns"):
            patterns["insights"].append(
                "Agent usage patterns detected - review for optimization opportunities"
            )

        return jsonify(patterns)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================


@app.route("/api/analytics/knowledge-gaps")
def api_knowledge_gaps():
    """
    Identify knowledge gaps based on undefined symbols and questions.
    """
    try:
        session_id = request.args.get("session_id")

        # Get undefined symbols
        undefined = []
        if session_id:
            undefined = symbol_tracker.find_undefined_symbols(session_id)

        # Analyze symbol references for patterns
        symbol_report = symbol_tracker.generate_symbol_report(session_id)

        gaps = {
            "undefined_symbols": undefined,
            "low_documentation": [],  # Would need to correlate with doc coverage
            "frequently_questioned": [],  # Would need NLP on chat content
            "recommendations": [],
        }

        # Generate recommendations
        if len(undefined) > 10:
            gaps["recommendations"].append(
                "Many undefined symbols - consider updating project intelligence"
            )

        if len(undefined) > 0:
            gaps["recommendations"].append(
                f"Document these undefined symbols: {', '.join([u['name'] for u in undefined[:5]])}"
            )

        return jsonify(gaps)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analytics/productivity")
def api_productivity_analytics():
    """
    Analyze developer productivity metrics.
    """
    try:
        session_id = request.args.get("session_id")

        if not session_id:
            return jsonify({"error": "session_id required"}), 400

        # Get change velocity
        patterns = change_tracker.detect_change_patterns(session_id)

        # Get session intelligence
        intelligence = correlator.get_session_intelligence(session_id)

        productivity = {
            "files_per_hour": 0,  # Would need timestamp analysis
            "changes_per_file": 0,
            "symbols_per_change": 0,
            "tool_efficiency": {},
            "velocity_trend": patterns.get("change_velocity", []),
        }

        # Calculate metrics
        if patterns["files_changed"] > 0:
            productivity["changes_per_file"] = (
                patterns["total_changes"] / patterns["files_changed"]
            )

        if patterns["total_changes"] > 0:
            productivity["symbols_per_change"] = (
                len(intelligence["symbols_discussed"]) / patterns["total_changes"]
            )

        # Tool efficiency
        for tool, count in patterns.get("tools_used", {}).items():
            productivity["tool_efficiency"][tool] = {
                "usage_count": count,
                "percentage": (count / patterns["total_changes"] * 100)
                if patterns["total_changes"] > 0
                else 0,
            }

        return jsonify(productivity)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# HEALTH CHECK
# ============================================================================


@app.route("/api/intelligence/health")
def api_intelligence_health():
    """Check health of intelligence components."""
    try:
        health = {
            "status": "healthy",
            "components": {
                "correlator": "ok",
                "code_extractor": "ok",
                "symbol_tracker": "ok",
                "change_tracker": "ok",
                "agent_analyzer": "ok",
            },
            "data": {
                "symbols_indexed": len(symbol_tracker.symbol_index),
                "agents_loaded": len(agent_analyzer.agent_cache),
                "has_proj_intel": Path("/home/opsvi/master_root/.proj-intel").exists(),
            },
        }

        return jsonify(health)
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5002)
