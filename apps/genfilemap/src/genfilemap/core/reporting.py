
"""
Reporting functionality for GenFileMap.

This module handles report generation and statistics tracking.
"""

import json
from typing import Dict, Any
import os

from genfilemap.logging_utils import info

# Global report data
report_data = {
    "processed_files": 0,
    "updated_files": 0,
    "skipped_files": 0,
    "errors": 0,
    "api_calls": 0,
    "api_tokens_used": 0,
    "duration": 0,
    "validation_results": [],  # List of validation results for each file
    "detailed_logs": []
}

def initialize_report() -> Dict[str, Any]:
    """
    Initialize a new report data structure.
    
    Returns:
        A dictionary with report fields initialized to zero
    """
    return {
        "processed_files": 0,
        "updated_files": 0,
        "skipped_files": 0,
        "errors": 0,
        "api_calls": 0,
        "api_tokens_used": 0,
        "duration": 0,
        "validation_results": [],  # List of validation results for each file
        "detailed_logs": []
    }

def generate_report(report_path: str, report_data: Dict[str, Any]) -> None:
    """
    Generate a JSON report of the file map operations.
    
    Args:
        report_path: Path to write the report
        report_data: The report data dictionary
    """
    # Ensure report path is in map_reports directory if not specified with a directory
    if not os.path.dirname(report_path):
        # Create map_reports directory if it doesn't exist
        os.makedirs("map_reports", exist_ok=True)
        report_path = os.path.join("map_reports", report_path)
    else:
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    # Create the report object
    report = {
        "summary": {
            "processed_files": report_data["processed_files"],
            "updated_files": report_data["updated_files"],
            "skipped_files": report_data["skipped_files"],
            "errors": report_data["errors"],
            "api_calls": report_data["api_calls"],
            "api_tokens_used": report_data.get("api_tokens_used", 0),
            "duration_seconds": report_data["duration"],
            "validation_summary": {
                "total_validated": len(report_data["validation_results"]),
                "valid_files": sum(1 for r in report_data["validation_results"] if r["is_valid"]),
                "files_with_issues": sum(1 for r in report_data["validation_results"] if not r["is_valid"])
            }
        },
        "validation_results": report_data["validation_results"],
        "details": report_data["detailed_logs"]
    }
    
    # Write the report
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    info(f"Report generated at {report_path}")
    
    # Print summary to console
    info("\nSummary:")
    info(f"  Files processed: {report_data['processed_files']}")
    info(f"  Files updated: {report_data['updated_files']}")
    info(f"  Files skipped: {report_data['skipped_files']}")
    info(f"  Errors: {report_data['errors']}")
    info(f"  API calls: {report_data['api_calls']}")
    info(f"  Duration: {report_data['duration']:.2f} seconds")
    
    # Print validation summary if validation was used
    if report_data["validation_results"]:
        info("\nValidation Summary:")
        info(f"  Files validated: {len(report_data['validation_results'])}")
        info(f"  Valid files: {sum(1 for r in report_data['validation_results'] if r['is_valid'])}")
        info(f"  Files with issues: {sum(1 for r in report_data['validation_results'] if not r['is_valid'])}")
        
        # Print details of files with issues
        files_with_issues = [r for r in report_data["validation_results"] if not r["is_valid"]]
        if files_with_issues:
            info("\nFiles with validation issues:")
            for result in files_with_issues:
                info(f"  {result['file']}:")
                for issue in result["issues"]:
                    info(f"    - {issue['type']}: {issue['description']} (Severity: {issue['severity']})") 