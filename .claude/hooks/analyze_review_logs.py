#!/usr/bin/env python3
"""
Log analysis utility for answer_review audit trails and performance metrics.
Provides insights into review patterns, performance, and decision history.
"""

import argparse
import json
import pathlib
import statistics
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class ReviewLogAnalyzer:
    """Analyzes review logs for patterns and insights."""
    
    def __init__(self, log_dir: pathlib.Path):
        self.log_dir = log_dir
        self.audit_dir = log_dir / "audit"
        self.metrics_dir = log_dir / "metrics"
        self.operational_dir = log_dir / "operational"
        
    def load_audit_logs(self, days_back: int = 7) -> List[Dict]:
        """Load audit logs from the past N days."""
        logs = []
        cutoff = datetime.now() - timedelta(days=days_back)
        
        if not self.audit_dir.exists():
            return logs
            
        for file in sorted(self.audit_dir.glob("review_audit_*.jsonl")):
            # Parse date from filename
            try:
                file_date_str = file.stem.replace("review_audit_", "")
                file_date = datetime.strptime(file_date_str, "%Y-%m-%d")
                if file_date < cutoff:
                    continue
            except:
                pass
                
            with open(file, "r") as f:
                for line in f:
                    if line.strip():
                        try:
                            logs.append(json.loads(line))
                        except:
                            pass
                            
        return logs
    
    def load_metrics(self, days_back: int = 7) -> List[Dict]:
        """Load performance metrics from the past N days."""
        metrics = []
        cutoff = datetime.now() - timedelta(days=days_back)
        
        if not self.metrics_dir.exists():
            return metrics
            
        for file in sorted(self.metrics_dir.glob("performance_*.jsonl")):
            try:
                file_date_str = file.stem.replace("performance_", "")
                file_date = datetime.strptime(file_date_str, "%Y-%m-%d")
                if file_date < cutoff:
                    continue
            except:
                pass
                
            with open(file, "r") as f:
                for line in f:
                    if line.strip():
                        try:
                            metrics.append(json.loads(line))
                        except:
                            pass
                            
        return metrics
    
    def analyze_review_patterns(self, audit_logs: List[Dict]) -> Dict:
        """Analyze patterns in review decisions."""
        total_reviews = len([l for l in audit_logs if "verdict" in l])
        passed = len([l for l in audit_logs if l.get("verdict", {}).get("passed")])
        failed = total_reviews - passed
        
        # Analyze by model
        model_stats = defaultdict(lambda: {"total": 0, "passed": 0, "failed": 0})
        for log in audit_logs:
            if "model" in log and "verdict" in log:
                model = log["model"]
                model_stats[model]["total"] += 1
                if log["verdict"]["passed"]:
                    model_stats[model]["passed"] += 1
                else:
                    model_stats[model]["failed"] += 1
        
        # Analyze research blocks
        research_blocks = len([l for l in audit_logs if l.get("action") == "research_block"])
        
        # Session analysis
        sessions = defaultdict(list)
        for log in audit_logs:
            if "session_id" in log:
                sessions[log["session_id"]].append(log)
        
        avg_attempts = []
        for session_logs in sessions.values():
            attempts = [l.get("attempt_num", 1) for l in session_logs if "attempt_num" in l]
            if attempts:
                avg_attempts.append(max(attempts))
        
        return {
            "total_reviews": total_reviews,
            "passed": passed,
            "failed": failed,
            "pass_rate": round(passed / total_reviews * 100, 2) if total_reviews else 0,
            "model_stats": dict(model_stats),
            "research_blocks": research_blocks,
            "unique_sessions": len(sessions),
            "avg_attempts_per_session": round(statistics.mean(avg_attempts), 2) if avg_attempts else 0,
            "max_attempts_seen": max(avg_attempts) if avg_attempts else 0
        }
    
    def analyze_performance(self, metrics: List[Dict]) -> Dict:
        """Analyze performance metrics."""
        durations_by_op = defaultdict(list)
        
        for metric in metrics:
            if "duration_ms" in metric and "operation" in metric:
                durations_by_op[metric["operation"]].append(metric["duration_ms"])
        
        perf_stats = {}
        for op, durations in durations_by_op.items():
            if durations:
                perf_stats[op] = {
                    "count": len(durations),
                    "mean_ms": round(statistics.mean(durations), 2),
                    "median_ms": round(statistics.median(durations), 2),
                    "min_ms": round(min(durations), 2),
                    "max_ms": round(max(durations), 2),
                    "p95_ms": round(sorted(durations)[int(len(durations) * 0.95)], 2) if len(durations) > 20 else None
                }
        
        return perf_stats
    
    def analyze_failures(self, audit_logs: List[Dict]) -> Dict:
        """Analyze failure patterns and common guidance."""
        failures = [l for l in audit_logs if l.get("verdict") and not l["verdict"]["passed"]]
        
        if not failures:
            return {"no_failures": True}
        
        # Extract guidance patterns
        guidance_samples = []
        guidance_keywords = Counter()
        
        for failure in failures[:20]:  # Sample first 20
            guidance = failure.get("verdict", {}).get("guidance", "")
            if guidance and guidance != "Review error:":
                guidance_samples.append(guidance[:200])
                # Extract keywords (simple word frequency)
                words = guidance.lower().split()
                for word in words:
                    if len(word) > 4:  # Skip short words
                        guidance_keywords[word] += 1
        
        return {
            "total_failures": len(failures),
            "common_keywords": dict(guidance_keywords.most_common(10)),
            "sample_guidance": guidance_samples[:5]
        }
    
    def generate_report(self, days_back: int = 7) -> str:
        """Generate a comprehensive analysis report."""
        audit_logs = self.load_audit_logs(days_back)
        metrics = self.load_metrics(days_back)
        
        report = []
        report.append(f"=== Answer Review Log Analysis Report ===")
        report.append(f"Period: Last {days_back} days")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")
        
        # Review patterns
        patterns = self.analyze_review_patterns(audit_logs)
        report.append("## Review Statistics")
        report.append(f"- Total reviews: {patterns['total_reviews']}")
        report.append(f"- Passed: {patterns['passed']} ({patterns['pass_rate']}%)")
        report.append(f"- Failed: {patterns['failed']}")
        report.append(f"- Research blocks: {patterns['research_blocks']}")
        report.append(f"- Unique sessions: {patterns['unique_sessions']}")
        report.append(f"- Avg attempts per session: {patterns['avg_attempts_per_session']}")
        report.append(f"- Max attempts seen: {patterns['max_attempts_seen']}")
        report.append("")
        
        # Model performance
        if patterns['model_stats']:
            report.append("## Model Performance")
            for model, stats in patterns['model_stats'].items():
                pass_rate = round(stats['passed'] / stats['total'] * 100, 2) if stats['total'] else 0
                report.append(f"- {model}: {stats['total']} reviews, {pass_rate}% pass rate")
            report.append("")
        
        # Performance metrics
        perf_stats = self.analyze_performance(metrics)
        if perf_stats:
            report.append("## Performance Metrics")
            for op, stats in perf_stats.items():
                report.append(f"\n### {op}")
                report.append(f"  - Count: {stats['count']}")
                report.append(f"  - Mean: {stats['mean_ms']}ms")
                report.append(f"  - Median: {stats['median_ms']}ms")
                report.append(f"  - Range: {stats['min_ms']}ms - {stats['max_ms']}ms")
                if stats.get('p95_ms'):
                    report.append(f"  - P95: {stats['p95_ms']}ms")
            report.append("")
        
        # Failure analysis
        failures = self.analyze_failures(audit_logs)
        if not failures.get("no_failures"):
            report.append("## Failure Analysis")
            report.append(f"- Total failures: {failures['total_failures']}")
            
            if failures.get('common_keywords'):
                report.append("\nCommon guidance keywords:")
                for word, count in list(failures['common_keywords'].items())[:5]:
                    report.append(f"  - {word}: {count} occurrences")
            
            if failures.get('sample_guidance'):
                report.append("\nSample guidance (truncated):")
                for i, guidance in enumerate(failures['sample_guidance'], 1):
                    report.append(f"  {i}. {guidance}...")
        
        return "\n".join(report)


def main():
    """Main CLI interface for log analysis."""
    parser = argparse.ArgumentParser(description="Analyze answer_review logs")
    parser.add_argument(
        "--log-dir",
        type=pathlib.Path,
        default=pathlib.Path(".claude/hooks/logs"),
        help="Path to log directory"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to analyze"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format"
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        help="Output file (default: stdout)"
    )
    
    args = parser.parse_args()
    
    analyzer = ReviewLogAnalyzer(args.log_dir)
    
    if args.format == "text":
        report = analyzer.generate_report(args.days)
        if args.output:
            args.output.write_text(report)
            print(f"Report saved to {args.output}")
        else:
            print(report)
    else:
        # JSON format - raw data
        data = {
            "audit_logs": analyzer.load_audit_logs(args.days),
            "metrics": analyzer.load_metrics(args.days),
            "analysis": {
                "patterns": analyzer.analyze_review_patterns(analyzer.load_audit_logs(args.days)),
                "performance": analyzer.analyze_performance(analyzer.load_metrics(args.days)),
                "failures": analyzer.analyze_failures(analyzer.load_audit_logs(args.days))
            }
        }
        
        output = json.dumps(data, indent=2, default=str)
        if args.output:
            args.output.write_text(output)
            print(f"JSON data saved to {args.output}")
        else:
            print(output)


if __name__ == "__main__":
    main()