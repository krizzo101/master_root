#!/usr/bin/env python3
"""
CLI interface for the Project Intelligence Chat Analytics Integration.

Usage:
    python cli.py correlate --session-id <session_id>
    python cli.py symbols --hot --days 7
    python cli.py changes --session-id <session_id>
    python cli.py agents --analyze
    python cli.py report --session-id <session_id> --output report.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from opsvi_monitoring.chat_analytics.intelligence import (
    AgentAnalyzer,
    ChangeTracker,
    CodeContextExtractor,
    ProjectIntelligenceCorrelator,
    SymbolTracker,
)


class IntelligenceCLI:
    """Command-line interface for intelligence analytics."""

    def __init__(self):
        self.correlator = ProjectIntelligenceCorrelator()
        self.symbol_tracker = SymbolTracker()
        self.change_tracker = ChangeTracker()
        self.agent_analyzer = AgentAnalyzer()
        self.code_extractor = CodeContextExtractor()

    def correlate_session(self, session_id: str, verbose: bool = False):
        """Correlate a chat session with project intelligence."""
        print(f"Correlating session: {session_id}")

        # Get session intelligence
        report = self.correlator.get_session_intelligence(session_id)

        if verbose:
            print(json.dumps(report, indent=2))
        else:
            print(f"Files affected: {len(report['files_affected'])}")
            print(f"Symbols discussed: {len(report['symbols_discussed'])}")
            print(f"Modifications: {len(report['modification_timeline'])}")

        return report

    def analyze_symbols(
        self, session_id: str = None, hot: bool = False, days: int = 7, limit: int = 20
    ):
        """Analyze symbol usage and discussions."""
        if hot:
            print(f"Hot symbols (last {days} days):")
            symbols = self.symbol_tracker.get_hot_symbols(session_id, days)[:limit]

            for symbol in symbols:
                print(
                    f"  {symbol['name']}: {symbol['references']} refs, "
                    f"{symbol['sessions']} sessions, complexity: {symbol['complexity']}"
                )
        else:
            report = self.symbol_tracker.generate_symbol_report(session_id)
            print(f"Total symbols: {report['summary']['total_symbols']}")
            print(f"Unique symbols: {report['summary']['unique_symbols']}")
            print(f"Undefined symbols: {report['summary']['undefined_symbols']}")

            if report["undefined"]:
                print("\nUndefined symbols:")
                for undef in report["undefined"][:10]:
                    suggestion = (
                        f" (maybe: {undef['suggestion']})"
                        if undef.get("suggestion")
                        else ""
                    )
                    print(f"  - {undef['name']}{suggestion}")

        return symbols if hot else report

    def analyze_changes(self, session_id: str, show_timeline: bool = False):
        """Analyze code changes in a session."""
        print(f"Analyzing changes for session: {session_id}")

        # Get change report
        report = self.change_tracker.generate_change_report(session_id)

        print(f"Total changes: {report['summary']['total_changes']}")
        print(f"Files affected: {report['summary']['files_affected']}")
        print(f"Impact score: {report['summary']['impact_score']}")

        if report["hot_files"]:
            print("\nHot files:")
            for hot_file in report["hot_files"][:5]:
                print(f"  {hot_file['file']}: {hot_file['changes']} changes")

        if show_timeline:
            print("\nChange timeline:")
            for event in report["timeline"][:20]:
                print(
                    f"  {event['timestamp']}: {event['action']} {event['file']} "
                    f"(using {event['tool']})"
                )

        if report["recommendations"]:
            print("\nRecommendations:")
            for rec in report["recommendations"]:
                print(f"  - {rec}")

        return report

    def analyze_agents(self, session_id: str = None, show_patterns: bool = False):
        """Analyze agent utilization and patterns."""
        print("Analyzing agent utilization...")

        # Get agent report
        report = self.agent_analyzer.generate_agent_report(session_id)

        print(f"Total agents: {report['summary']['total_agents']}")
        print(f"Agents used: {report['summary']['agents_used']}")
        print(f"Total invocations: {report['summary']['total_invocations']}")
        print(f"Average complexity: {report['summary']['average_complexity']:.2f}")

        if report["hot_agents"]:
            print("\nMost used agents:")
            for agent in report["hot_agents"][:5]:
                print(
                    f"  {agent['name']}: {agent['usage_count']} uses, "
                    f"complexity: {agent['complexity']}"
                )

        if show_patterns:
            patterns = report.get("patterns", {})
            if patterns.get("collaboration_patterns"):
                print("\nCollaboration patterns:")
                for collab in patterns["collaboration_patterns"][:5]:
                    print(
                        f"  {collab['agent1']} -> {collab['agent2']}: "
                        f"{collab['frequency']} times"
                    )

        if report["recommendations"]:
            print("\nRecommendations:")
            for rec in report["recommendations"]:
                print(f"  - {rec}")

        return report

    def extract_code_context(self, message: str):
        """Extract code context from a message."""
        context = self.code_extractor.extract_context(message)
        density = self.code_extractor.analyze_code_density(message)

        print("Code Context Extraction:")
        print(f"  Files mentioned: {len(context['files'])}")
        print(f"  Total symbols: {context['metadata']['total_symbols']}")
        print(f"  Code blocks: {len(context['code_blocks'])}")
        print(f"  Errors detected: {len(context['errors'])}")

        print("\nCode Density Analysis:")
        print(f"  Code percentage: {density['code_percentage']}%")
        print(f"  Technical elements: {density['technical_elements']}")
        print(f"  Complexity score: {density['complexity_score']}")

        return context, density

    def generate_full_report(self, session_id: str, output_file: str = None):
        """Generate a comprehensive intelligence report."""
        print(f"Generating full report for session: {session_id}")

        report = {
            "session_id": session_id,
            "correlation": self.correlator.get_session_intelligence(session_id),
            "symbols": self.symbol_tracker.generate_symbol_report(session_id),
            "changes": self.change_tracker.generate_change_report(session_id),
            "agents": self.agent_analyzer.generate_agent_report(session_id),
        }

        # Calculate summary metrics
        report["summary"] = {
            "files_affected": len(report["correlation"]["files_affected"]),
            "symbols_discussed": report["symbols"]["summary"]["unique_symbols"],
            "undefined_symbols": report["symbols"]["summary"]["undefined_symbols"],
            "total_changes": report["changes"]["summary"]["total_changes"],
            "impact_score": report["changes"]["summary"]["impact_score"],
            "agents_used": report["agents"]["summary"]["agents_used"],
            "agent_invocations": report["agents"]["summary"]["total_invocations"],
        }

        # Compile all recommendations
        report["recommendations"] = list(
            set(
                report["changes"].get("recommendations", [])
                + report["agents"].get("recommendations", [])
            )
        )

        if output_file:
            with open(output_file, "w") as f:
                json.dump(report, f, indent=2)
            print(f"Report saved to: {output_file}")
        else:
            print(json.dumps(report["summary"], indent=2))

        return report

    def close(self):
        """Close all connections."""
        self.correlator.close()
        self.symbol_tracker.close()
        self.change_tracker.close()
        self.agent_analyzer.close()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Project Intelligence Chat Analytics CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Correlate command
    correlate_parser = subparsers.add_parser(
        "correlate", help="Correlate chat session with project intelligence"
    )
    correlate_parser.add_argument(
        "--session-id", required=True, help="Session ID to correlate"
    )
    correlate_parser.add_argument(
        "--verbose", action="store_true", help="Show detailed output"
    )

    # Symbols command
    symbols_parser = subparsers.add_parser("symbols", help="Analyze symbol usage")
    symbols_parser.add_argument("--session-id", help="Filter by session ID")
    symbols_parser.add_argument("--hot", action="store_true", help="Show hot symbols")
    symbols_parser.add_argument(
        "--days", type=int, default=7, help="Number of days for hot symbols"
    )
    symbols_parser.add_argument(
        "--limit", type=int, default=20, help="Maximum results to show"
    )

    # Changes command
    changes_parser = subparsers.add_parser("changes", help="Analyze code changes")
    changes_parser.add_argument(
        "--session-id", required=True, help="Session ID to analyze"
    )
    changes_parser.add_argument(
        "--timeline", action="store_true", help="Show change timeline"
    )

    # Agents command
    agents_parser = subparsers.add_parser("agents", help="Analyze agent utilization")
    agents_parser.add_argument("--session-id", help="Filter by session ID")
    agents_parser.add_argument(
        "--patterns", action="store_true", help="Show usage patterns"
    )

    # Extract command
    extract_parser = subparsers.add_parser(
        "extract", help="Extract code context from message"
    )
    extract_parser.add_argument("--message", required=True, help="Message to analyze")

    # Report command
    report_parser = subparsers.add_parser(
        "report", help="Generate comprehensive report"
    )
    report_parser.add_argument(
        "--session-id", required=True, help="Session ID for report"
    )
    report_parser.add_argument("--output", help="Output file path (JSON format)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize CLI
    cli = IntelligenceCLI()

    try:
        if args.command == "correlate":
            cli.correlate_session(args.session_id, args.verbose)

        elif args.command == "symbols":
            cli.analyze_symbols(args.session_id, args.hot, args.days, args.limit)

        elif args.command == "changes":
            cli.analyze_changes(args.session_id, args.timeline)

        elif args.command == "agents":
            cli.analyze_agents(args.session_id, args.patterns)

        elif args.command == "extract":
            cli.extract_code_context(args.message)

        elif args.command == "report":
            cli.generate_full_report(args.session_id, args.output)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        cli.close()


if __name__ == "__main__":
    main()
