#!/usr/bin/env python3
"""
Chat Analytics CLI

Commands:
    ingest    - Ingest chat logs from JSONL files
    analyze   - Run analysis on chat data
    dashboard - Start web dashboard
    summary   - Generate AI summaries for sessions
"""

import argparse
import sys
from pathlib import Path


def ingest_command(args):
    """Run chat log ingestion"""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from opsvi_monitoring.chat_analytics.ingestion.sqlite_ingester import (
        main as ingest_main,
    )

    return ingest_main()


def analyze_command(args):
    """Run response time analysis"""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from opsvi_monitoring.chat_analytics.analysis.response_analyzer import (
        ResponseTimeAnalyzer,
        format_duration,
    )

    analyzer = ResponseTimeAnalyzer()

    print("\n=== RESPONSE TIME ANALYSIS ===")
    metrics = analyzer.get_response_times()
    print(f"Average response time: {format_duration(metrics['average'])}")
    print(f"Median response time: {format_duration(metrics['median'])}")
    print(f"Shortest: {format_duration(metrics['shortest']['time'])}")
    print(f"Longest: {format_duration(metrics['longest']['time'])}")
    print(f"Total prompts analyzed: {metrics['total_prompts']}")

    print("\n=== ACTIVITY ANALYSIS ===")
    activity = analyzer.get_activity_summary()
    for session_id, stats in list(activity.items())[:5]:
        print(f"\nSession {session_id[:8]}...")
        print(
            f"  Active: {format_duration(stats['active_time_seconds'])} ({stats['active_percentage']:.1f}%)"
        )
        print(
            f"  Dead: {format_duration(stats['dead_time_seconds'])} ({stats['dead_percentage']:.1f}%)"
        )

    analyzer.close()
    return 0


def dashboard_command(args):
    """Start web dashboard"""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from opsvi_monitoring.chat_analytics.web.dashboard import app

    print(f"Starting Chat Analytics Dashboard on http://{args.host}:{args.port}")
    print("Press CTRL+C to stop")

    app.run(host=args.host, port=args.port, debug=args.debug)
    return 0


def summary_command(args):
    """Generate AI summaries"""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from opsvi_monitoring.chat_analytics.analysis.session_analyzer import (
        main as summary_main,
    )

    return summary_main()


def main():
    parser = argparse.ArgumentParser(
        description="OPSVI Chat Analytics CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest chat logs")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Run analysis")

    # Dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Start web dashboard")
    dashboard_parser.add_argument(
        "--port", type=int, default=5001, help="Port (default: 5001)"
    )
    dashboard_parser.add_argument(
        "--host", default="0.0.0.0", help="Host (default: 0.0.0.0)"
    )
    dashboard_parser.add_argument("--debug", action="store_true", help="Debug mode")

    # Summary command
    summary_parser = subparsers.add_parser("summary", help="Generate AI summaries")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "ingest": ingest_command,
        "analyze": analyze_command,
        "dashboard": dashboard_command,
        "summary": summary_command,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
