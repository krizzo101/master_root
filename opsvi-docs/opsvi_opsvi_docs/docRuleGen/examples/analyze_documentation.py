# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Document Analysis API Examples","description":"Example script demonstrating how to use the Document Analysis Workflow API to analyze documentation files, map them to a taxonomy, and generate analysis results.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Import necessary modules and classes for the script.","line_start":9,"line_end":18},{"name":"Function: analyze_with_existing_taxonomy","description":"Analyze documentation using an existing taxonomy file.","line_start":20,"line_end":62},{"name":"Function: analyze_without_taxonomy","description":"Analyze documentation without using a taxonomy file.","line_start":62,"line_end":102},{"name":"Function: analyze_single_document","description":"Analyze a single document.","line_start":102,"line_end":142},{"name":"Main Execution Block","description":"Main block to execute the analysis functions and handle example document creation.","line_start":144,"line_end":176}],"key_elements":[{"name":"analyze_with_existing_taxonomy","description":"Function to analyze documentation using an existing taxonomy file.","line":21},{"name":"analyze_without_taxonomy","description":"Function to analyze documentation without using a taxonomy file.","line":63},{"name":"analyze_single_document","description":"Function to analyze a single document.","line":103},{"name":"DocumentAnalysisWorkflow","description":"Class used to create a workflow for document analysis.","line":18},{"name":"traceback","description":"Module imported for error handling.","line":176}]}
"""
# FILE_MAP_END

#!/usr/bin/env python3

"""
Example script demonstrating how to use the Document Analysis Workflow API.

This script shows how to analyze a directory of documentation files,
map them to a taxonomy, and generate analysis results.
"""

import os
import sys
import json
from pathlib import Path

# Remove the sys.path manipulation and use proper imports
# sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from docRuleGen.rules_engine.workflow import DocumentAnalysisWorkflow


def analyze_with_existing_taxonomy():
    """Analyze documentation using an existing taxonomy file."""
    # Paths to documentation and taxonomy
    doc_dir = "docs/examples"
    taxonomy_file = "docRuleGen/examples/sample_taxonomy.yaml"
    output_dir = "analysis_output"

    print(
        f"Analyzing documentation in '{doc_dir}' using taxonomy from '{taxonomy_file}'..."
    )

    # Create workflow instance
    workflow = DocumentAnalysisWorkflow(
        doc_dir=doc_dir,
        taxonomy_file=taxonomy_file,
        output_dir=output_dir,
        max_workers=4,
        file_extensions=[".md", ".txt", ".yaml", ".yml", ".json"],
    )

    # Run analysis
    results = workflow.run()

    # Print summary
    print("\nAnalysis Summary:")
    print(f"Total documents: {results.get('total_documents', 0)}")
    print(f"Analyzed documents: {results.get('analyzed_documents', 0)}")

    if "documents_by_type" in results:
        print("\nDocument Types:")
        for doc_type, count in results["documents_by_type"].items():
            print(f"  {doc_type}: {count}")

    # Save results to a file
    summary_path = Path(output_dir) / "analysis_summary.json"
    os.makedirs(summary_path.parent, exist_ok=True)

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved analysis summary to {summary_path}")
    print(f"Detailed analysis results are in the '{output_dir}' directory")


def analyze_without_taxonomy():
    """Analyze documentation without using a taxonomy file."""
    # Paths to documentation
    doc_dir = "docs/examples"
    output_dir = "analysis_output_no_taxonomy"

    print(f"Analyzing documentation in '{doc_dir}' without taxonomy...")

    # Create workflow instance
    workflow = DocumentAnalysisWorkflow(
        doc_dir=doc_dir,
        output_dir=output_dir,
        max_workers=4,
        file_extensions=[".md", ".txt"],
    )

    # Run analysis
    results = workflow.run()

    # Print summary
    print("\nAnalysis Summary (No Taxonomy):")
    print(f"Total documents: {results.get('total_documents', 0)}")
    print(f"Analyzed documents: {results.get('analyzed_documents', 0)}")

    if "documents_by_type" in results:
        print("\nDocument Types:")
        for doc_type, count in results["documents_by_type"].items():
            print(f"  {doc_type}: {count}")

    # Save results to a file
    summary_path = Path(output_dir) / "analysis_summary.json"
    os.makedirs(summary_path.parent, exist_ok=True)

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved analysis summary to {summary_path}")
    print(f"Detailed analysis results are in the '{output_dir}' directory")


def analyze_single_document():
    """Analyze a single document."""
    # Path to document
    doc_path = "docs/examples/example_doc.md"
    output_dir = "analysis_output_single"

    print(f"Analyzing single document: '{doc_path}'...")

    # Create workflow instance
    workflow = DocumentAnalysisWorkflow(
        doc_dir=str(Path(doc_path).parent), output_dir=output_dir
    )

    # Analyze single document
    result = workflow.analyze_document(Path(doc_path))

    # Print summary
    print("\nSingle Document Analysis:")
    print(f"Document type: {result.get('document_type', 'unknown')}")
    print(f"Key concepts: {len(result.get('concepts', []))}")

    if "references" in result:
        print("\nCross-References:")
        for ref in result["references"]:
            print(f"  {ref.get('type', 'link')}: {ref.get('target', 'unknown')}")

    # Save result to a file
    output_file = Path(output_dir) / f"{Path(doc_path).stem}_analysis.json"
    os.makedirs(output_file.parent, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"\nSaved document analysis to {output_file}")


if __name__ == "__main__":
    print("Document Analysis API Examples\n")

    # Create example directories if needed
    doc_dirs = [
        "docs/examples",
        "analysis_output",
        "analysis_output_no_taxonomy",
        "analysis_output_single",
    ]
    for doc_dir in doc_dirs:
        os.makedirs(doc_dir, exist_ok=True)

    # Check if example document exists, create if not
    example_doc = "docs/examples/example_doc.md"
    if not os.path.exists(example_doc):
        with open(example_doc, "w", encoding="utf-8") as f:
            f.write("# Example Document\n\n")
            f.write(
                "This is an example document for testing the Document Analysis API.\n\n"
            )
            f.write("## Features\n\n")
            f.write("- Feature 1: Description of feature 1\n")
            f.write("- Feature 2: Description of feature 2\n\n")
            f.write("See also: [Related Document](related_doc.md)\n")

        print(f"Created example document: {example_doc}")

    try:
        # Run examples
        print("\n" + "=" * 60)
        analyze_with_existing_taxonomy()

        print("\n" + "=" * 60)
        analyze_without_taxonomy()

        print("\n" + "=" * 60)
        analyze_single_document()

        print("\n" + "=" * 60)
        print("All examples completed successfully.")
    except Exception as e:
        print(f"Error running examples: {str(e)}")
        import traceback

        traceback.print_exc()
