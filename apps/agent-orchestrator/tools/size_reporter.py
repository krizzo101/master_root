#!/usr/bin/env python3
"""
Size Reporter - Standalone size analysis and reporting tool for GPT-5 payloads
Provides detailed analysis, visualization, and reporting capabilities.
"""

import argparse
import json
import logging
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from gpt5_payload_generator import (
        GPT5PayloadGenerator,
        PayloadSizeAnalyzer,
        TokenCountAnalyzer,
    )
except ImportError as e:
    print(f"Error importing GPT-5 payload generator: {e}")
    sys.exit(1)


class SizeReportGenerator:
    """Generate comprehensive size analysis reports"""

    def __init__(self):
        self.token_analyzer = TokenCountAnalyzer()
        self.size_analyzer = PayloadSizeAnalyzer()

    def generate_detailed_report(
        self, session_files: List[str], output_format: str = "json"
    ) -> Dict[str, Any]:
        """Generate detailed size analysis report for multiple sessions"""

        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_files": len(session_files),
                "analysis_version": "1.0",
            },
            "file_analyses": [],
            "aggregate_statistics": {},
            "size_distribution": {},
            "recommendations": [],
        }

        # Analyze each file
        total_tokens = 0
        total_cost = 0
        file_sizes = []
        token_counts = []

        for file_path in session_files:
            try:
                file_analysis = self._analyze_single_file(file_path)
                report["file_analyses"].append(file_analysis)

                if "error" not in file_analysis:
                    total_tokens += file_analysis.get("token_count", 0)
                    total_cost += file_analysis.get("estimated_cost", 0)
                    file_sizes.append(file_analysis.get("file_size_mb", 0))
                    token_counts.append(file_analysis.get("token_count", 0))

            except Exception as e:
                logging.error(f"Error analyzing {file_path}: {e}")
                report["file_analyses"].append(
                    {"file_path": file_path, "error": str(e)}
                )

        # Calculate aggregate statistics
        successful_analyses = [f for f in report["file_analyses"] if "error" not in f]
        if successful_analyses:
            report["aggregate_statistics"] = self._calculate_aggregate_stats(
                successful_analyses, total_tokens, total_cost, file_sizes, token_counts
            )

            report["size_distribution"] = self._analyze_size_distribution(token_counts)
            report["recommendations"] = self._generate_global_recommendations(
                successful_analyses
            )

        return report

    def _analyze_single_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a single session file"""
        try:
            # Load file
            with open(file_path, "r", encoding="utf-8") as f:
                if file_path.endswith(".jsonl"):
                    lines = f.readlines()
                    content = {
                        "messages": [json.loads(line) for line in lines if line.strip()]
                    }
                else:
                    content = json.load(f)

            # File metadata
            file_path_obj = Path(file_path)
            file_size_mb = file_path_obj.stat().st_size / (1024 * 1024)

            # Token analysis
            analysis = self.token_analyzer.analyze_content(content)

            # Content structure analysis
            structure_analysis = self._analyze_content_structure(content)

            return {
                "file_path": file_path,
                "file_name": file_path_obj.name,
                "file_size_mb": file_size_mb,
                "token_count": analysis.total_tokens,
                "estimated_cost": analysis.estimated_cost,
                "context_efficiency_score": analysis.context_efficiency_score,
                "recommended_chunks": analysis.recommended_chunks,
                "processing_time_estimate": analysis.processing_time_estimate,
                "structure_analysis": structure_analysis,
                "size_category": self._categorize_file_size(analysis.total_tokens),
                "optimization_potential": self._assess_optimization_potential(
                    analysis, structure_analysis
                ),
            }

        except Exception as e:
            return {"file_path": file_path, "error": str(e)}

    def _analyze_content_structure(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the structure and composition of content"""

        messages = content.get("messages", [])
        tool_calls = content.get("tool_calls", [])
        file_operations = content.get("file_operations", [])

        # Message analysis
        message_types = {"user": 0, "assistant": 0, "system": 0, "tool": 0}
        for msg in messages:
            msg_type = msg.get("role", "unknown")
            if msg_type in message_types:
                message_types[msg_type] += 1

        # Tool usage analysis
        tool_usage = {}
        for tool_call in tool_calls:
            tool_name = tool_call.get("name", "unknown")
            tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1

        # File operation analysis
        file_op_types = {}
        for file_op in file_operations:
            op_type = file_op.get("operation", "unknown")
            file_op_types[op_type] = file_op_types.get(op_type, 0) + 1

        return {
            "message_composition": message_types,
            "total_messages": len(messages),
            "tool_usage_breakdown": tool_usage,
            "total_tool_calls": len(tool_calls),
            "unique_tools_used": len(tool_usage),
            "file_operation_types": file_op_types,
            "total_file_operations": len(file_operations),
            "content_diversity_score": self._calculate_diversity_score(
                message_types, tool_usage, file_op_types
            ),
        }

    def _calculate_diversity_score(
        self, messages: Dict, tools: Dict, file_ops: Dict
    ) -> float:
        """Calculate content diversity score (0-100)"""
        # Count different types of activities
        activity_types = 0

        if sum(messages.values()) > 0:
            activity_types += len([v for v in messages.values() if v > 0])

        if len(tools) > 0:
            activity_types += min(5, len(tools))  # Cap tool diversity contribution

        if len(file_ops) > 0:
            activity_types += min(
                3, len(file_ops)
            )  # Cap file op diversity contribution

        # Normalize to 0-100 scale
        max_possible_score = 15  # 4 message types + 5 tools + 3 file ops
        return min(100.0, (activity_types / max_possible_score) * 100)

    def _categorize_file_size(self, token_count: int) -> str:
        """Categorize file by token count"""
        if token_count < 1000:
            return "Tiny"
        elif token_count < 5000:
            return "Small"
        elif token_count < 25000:
            return "Medium"
        elif token_count < 100000:
            return "Large"
        else:
            return "Extra Large"

    def _assess_optimization_potential(
        self, token_analysis, structure_analysis
    ) -> Dict[str, Any]:
        """Assess potential for optimization"""

        # Factors that indicate high optimization potential
        potential_score = 0
        reasons = []

        # Low context efficiency suggests redundancy
        if token_analysis.context_efficiency_score < 60:
            potential_score += 30
            reasons.append("Low context efficiency detected")

        # High repetition in tool usage
        tool_usage = structure_analysis.get("tool_usage_breakdown", {})
        if tool_usage:
            max_tool_usage = max(tool_usage.values())
            total_tools = sum(tool_usage.values())
            if max_tool_usage > total_tools * 0.5:  # One tool dominates
                potential_score += 20
                reasons.append("Repetitive tool usage patterns")

        # Large token count suggests chunking opportunities
        if token_analysis.total_tokens > 50000:
            potential_score += 25
            reasons.append("Large size suitable for chunking")

        # Low diversity score
        if structure_analysis.get("content_diversity_score", 0) < 40:
            potential_score += 15
            reasons.append("Low content diversity")

        # Many recommended chunks indicate optimization opportunity
        if token_analysis.recommended_chunks > 10:
            potential_score += 10
            reasons.append("High chunk count indicates optimization opportunity")

        potential_level = "Low"
        if potential_score >= 70:
            potential_level = "Very High"
        elif potential_score >= 50:
            potential_level = "High"
        elif potential_score >= 30:
            potential_level = "Medium"

        return {
            "optimization_score": min(100, potential_score),
            "optimization_level": potential_level,
            "optimization_reasons": reasons,
        }

    def _calculate_aggregate_stats(
        self,
        analyses: List[Dict],
        total_tokens: int,
        total_cost: float,
        file_sizes: List[float],
        token_counts: List[int],
    ) -> Dict[str, Any]:
        """Calculate aggregate statistics across all files"""

        if not analyses:
            return {}

        return {
            "total_files": len(analyses),
            "total_tokens": total_tokens,
            "total_estimated_cost": total_cost,
            "average_tokens_per_file": total_tokens / len(analyses),
            "average_file_size_mb": sum(file_sizes) / len(file_sizes),
            "token_statistics": {
                "min": min(token_counts),
                "max": max(token_counts),
                "median": self._calculate_median(token_counts),
                "std_deviation": self._calculate_std_dev(token_counts),
            },
            "size_categories": self._count_size_categories(analyses),
            "optimization_summary": self._summarize_optimization_potential(analyses),
        }

    def _analyze_size_distribution(self, token_counts: List[int]) -> Dict[str, Any]:
        """Analyze the distribution of file sizes"""

        if not token_counts:
            return {}

        # Create histogram bins
        max_tokens = max(token_counts)
        bin_count = min(10, len(token_counts))  # Max 10 bins
        bin_size = max(1000, max_tokens // bin_count)

        bins = {}
        for tokens in token_counts:
            bin_key = (tokens // bin_size) * bin_size
            bins[bin_key] = bins.get(bin_key, 0) + 1

        return {
            "bin_size": bin_size,
            "distribution": bins,
            "percentiles": {
                "25th": self._calculate_percentile(token_counts, 25),
                "50th": self._calculate_percentile(token_counts, 50),
                "75th": self._calculate_percentile(token_counts, 75),
                "90th": self._calculate_percentile(token_counts, 90),
            },
        }

    def _generate_global_recommendations(self, analyses: List[Dict]) -> List[str]:
        """Generate global recommendations based on all analyses"""
        recommendations = []

        # Check for high optimization potential files
        high_opt_files = [
            a
            for a in analyses
            if a.get("optimization_potential", {}).get("optimization_score", 0) > 60
        ]

        if len(high_opt_files) > len(analyses) * 0.3:
            recommendations.append(
                f"High optimization potential detected in {len(high_opt_files)} files - "
                "consider implementing chunking and context compression"
            )

        # Check for cost concerns
        total_cost = sum(a.get("estimated_cost", 0) for a in analyses)
        if total_cost > 10.0:
            recommendations.append(
                f"High total estimated cost (${total_cost:.2f}) - "
                "prioritize optimization for cost reduction"
            )

        # Check for large files
        large_files = [a for a in analyses if a.get("token_count", 0) > 100000]
        if large_files:
            recommendations.append(
                f"{len(large_files)} extra-large files detected - "
                "consider session summarization before GPT-5 submission"
            )

        # Check for low efficiency
        low_eff_files = [
            a for a in analyses if a.get("context_efficiency_score", 100) < 50
        ]
        if len(low_eff_files) > len(analyses) * 0.4:
            recommendations.append(
                "Many files with low context efficiency - "
                "review content for redundancy and repetitive patterns"
            )

        return recommendations

    def _count_size_categories(self, analyses: List[Dict]) -> Dict[str, int]:
        """Count files by size category"""
        categories = {}
        for analysis in analyses:
            category = analysis.get("size_category", "Unknown")
            categories[category] = categories.get(category, 0) + 1
        return categories

    def _summarize_optimization_potential(self, analyses: List[Dict]) -> Dict[str, Any]:
        """Summarize optimization potential across all files"""
        opt_scores = []
        opt_levels = {"Very High": 0, "High": 0, "Medium": 0, "Low": 0}

        for analysis in analyses:
            opt_data = analysis.get("optimization_potential", {})
            opt_scores.append(opt_data.get("optimization_score", 0))
            opt_level = opt_data.get("optimization_level", "Low")
            opt_levels[opt_level] = opt_levels.get(opt_level, 0) + 1

        return {
            "average_optimization_score": sum(opt_scores) / len(opt_scores)
            if opt_scores
            else 0,
            "optimization_level_distribution": opt_levels,
            "high_potential_files": len([s for s in opt_scores if s > 60]),
        }

    def _calculate_median(self, values: List[float]) -> float:
        """Calculate median value"""
        sorted_values = sorted(values)
        n = len(sorted_values)
        if n % 2 == 0:
            return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
        else:
            return sorted_values[n // 2]

    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) <= 1:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)

    def _calculate_percentile(self, values: List[int], percentile: int) -> int:
        """Calculate percentile value"""
        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)

        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            return int(lower + (upper - lower) * (index - int(index)))

    def generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML report from analysis data"""

        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>GPT-5 Payload Size Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .section {{ margin-bottom: 30px; }}
        .metric {{ background: #e9f5ff; padding: 10px; margin: 10px 0; border-radius: 3px; }}
        .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 10px 0; }}
        .success {{ background: #d4edda; border-left: 4px solid #28a745; padding: 10px; margin: 10px 0; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .chart {{ margin: 20px 0; }}
        .recommendations {{ background: #f8f9fa; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>GPT-5 Payload Size Analysis Report</h1>
        <p>Generated: {generated_at}</p>
        <p>Total Files Analyzed: {total_files}</p>
    </div>

    <div class="section">
        <h2>Executive Summary</h2>
        {executive_summary}
    </div>

    <div class="section">
        <h2>Aggregate Statistics</h2>
        {aggregate_stats}
    </div>

    <div class="section">
        <h2>Size Distribution</h2>
        {size_distribution}
    </div>

    <div class="section">
        <h2>Individual File Analysis</h2>
        {file_analysis_table}
    </div>

    <div class="section">
        <h2>Recommendations</h2>
        <div class="recommendations">
            {recommendations}
        </div>
    </div>
</body>
</html>
        """

        # Generate sections
        executive_summary = self._generate_html_executive_summary(report_data)
        aggregate_stats = self._generate_html_aggregate_stats(report_data)
        size_distribution = self._generate_html_size_distribution(report_data)
        file_analysis_table = self._generate_html_file_table(report_data)
        recommendations = self._generate_html_recommendations(report_data)

        return html_template.format(
            generated_at=report_data["report_metadata"]["generated_at"],
            total_files=report_data["report_metadata"]["total_files"],
            executive_summary=executive_summary,
            aggregate_stats=aggregate_stats,
            size_distribution=size_distribution,
            file_analysis_table=file_analysis_table,
            recommendations=recommendations,
        )

    def _generate_html_executive_summary(self, report_data: Dict) -> str:
        """Generate HTML for executive summary"""
        stats = report_data.get("aggregate_statistics", {})

        return f"""
        <div class="metric">
            <strong>Total Token Count:</strong> {stats.get('total_tokens', 0):,}
        </div>
        <div class="metric">
            <strong>Total Estimated Cost:</strong> ${stats.get('total_estimated_cost', 0):.4f}
        </div>
        <div class="metric">
            <strong>Average Tokens per File:</strong> {stats.get('average_tokens_per_file', 0):,.0f}
        </div>
        <div class="metric">
            <strong>Files Requiring Optimization:</strong> {stats.get('optimization_summary', {}).get('high_potential_files', 0)}
        </div>
        """

    def _generate_html_aggregate_stats(self, report_data: Dict) -> str:
        """Generate HTML for aggregate statistics"""
        stats = report_data.get("aggregate_statistics", {})
        token_stats = stats.get("token_statistics", {})

        return f"""
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Minimum Tokens</td><td>{token_stats.get('min', 0):,}</td></tr>
            <tr><td>Maximum Tokens</td><td>{token_stats.get('max', 0):,}</td></tr>
            <tr><td>Median Tokens</td><td>{token_stats.get('median', 0):,}</td></tr>
            <tr><td>Standard Deviation</td><td>{token_stats.get('std_deviation', 0):,.0f}</td></tr>
        </table>
        """

    def _generate_html_size_distribution(self, report_data: Dict) -> str:
        """Generate HTML for size distribution"""
        categories = report_data.get("aggregate_statistics", {}).get(
            "size_categories", {}
        )

        rows = ""
        for category, count in categories.items():
            rows += f"<tr><td>{category}</td><td>{count}</td></tr>"

        return f"""
        <table>
            <tr><th>Size Category</th><th>File Count</th></tr>
            {rows}
        </table>
        """

    def _generate_html_file_table(self, report_data: Dict) -> str:
        """Generate HTML table for individual file analysis"""
        files = report_data.get("file_analyses", [])

        rows = ""
        for file_data in files:
            if "error" not in file_data:
                opt_level = file_data.get("optimization_potential", {}).get(
                    "optimization_level", "Unknown"
                )
                opt_class = (
                    "warning"
                    if opt_level in ["High", "Very High"]
                    else "success"
                    if opt_level == "Low"
                    else ""
                )

                rows += f"""
                <tr class="{opt_class}">
                    <td>{file_data.get('file_name', 'Unknown')}</td>
                    <td>{file_data.get('token_count', 0):,}</td>
                    <td>${file_data.get('estimated_cost', 0):.4f}</td>
                    <td>{file_data.get('size_category', 'Unknown')}</td>
                    <td>{opt_level}</td>
                </tr>
                """

        return f"""
        <table>
            <tr>
                <th>File Name</th>
                <th>Token Count</th>
                <th>Estimated Cost</th>
                <th>Size Category</th>
                <th>Optimization Potential</th>
            </tr>
            {rows}
        </table>
        """

    def _generate_html_recommendations(self, report_data: Dict) -> str:
        """Generate HTML for recommendations"""
        recommendations = report_data.get("recommendations", [])

        if not recommendations:
            return "<p>No specific recommendations at this time.</p>"

        rec_html = "<ul>"
        for rec in recommendations:
            rec_html += f"<li>{rec}</li>"
        rec_html += "</ul>"

        return rec_html


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Size Reporter - Comprehensive size analysis for GPT-5 payloads",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze single file
  python size_reporter.py session.jsonl

  # Analyze directory with JSON output
  python size_reporter.py /path/to/sessions --pattern "*.jsonl" --output report.json

  # Generate HTML report
  python size_reporter.py /path/to/sessions --format html --output report.html

  # Analyze with verbose logging
  python size_reporter.py session.jsonl --verbose
        """,
    )

    parser.add_argument("input", help="Input file or directory path")
    parser.add_argument(
        "--pattern", "-p", help='File pattern for directory analysis (e.g., "*.jsonl")'
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "html"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )

    # Find input files
    input_path = Path(args.input)
    if input_path.is_dir():
        patterns = ["*.jsonl", "*.json"] if not args.pattern else [args.pattern]
        files = []
        for pattern in patterns:
            files.extend(input_path.glob(pattern))
        files = [str(f) for f in sorted(files)]
    else:
        files = [str(input_path)]

    if not files:
        logging.error("No files found matching criteria")
        sys.exit(1)

    logging.info(f"Analyzing {len(files)} files...")

    # Generate report
    reporter = SizeReportGenerator()
    report = reporter.generate_detailed_report(files, args.format)

    # Output report
    if args.format == "html":
        html_content = reporter.generate_html_report(report)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(html_content)
            logging.info(f"HTML report written to: {args.output}")
        else:
            print(html_content)
    else:
        # JSON format
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, default=str)
            logging.info(f"JSON report written to: {args.output}")
        else:
            print(json.dumps(report, indent=2, default=str))

    # Print summary
    stats = report.get("aggregate_statistics", {})
    if stats:
        print(f"\n=== Analysis Complete ===")
        print(f"Files Analyzed: {stats.get('total_files', 0)}")
        print(f"Total Tokens: {stats.get('total_tokens', 0):,}")
        print(f"Total Estimated Cost: ${stats.get('total_estimated_cost', 0):.4f}")
        print(
            f"High Optimization Potential: {stats.get('optimization_summary', {}).get('high_potential_files', 0)} files"
        )


if __name__ == "__main__":
    main()
