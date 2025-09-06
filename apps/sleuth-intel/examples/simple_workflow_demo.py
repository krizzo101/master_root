"""
Simple Workflow Template Demonstration

Quick examples showing how to use the workflow templates for basic investigations.
Perfect for getting started with the Sleuth Intel workflow system.
"""

import asyncio
import json
from datetime import datetime

from src.orchestration.sleuth_orchestrator import SleuthIntelOrchestrator
from src.orchestration.workflow_templates import (
    InvestigationDepth,
    WorkflowBudget,
    WorkflowTemplateManager,
    address_analysis_workflow,
    business_due_diligence_workflow,
    person_investigation_workflow,
    phone_investigation_workflow,
)


async def demo_phone_lookup():
    """Simple phone number lookup demonstration"""
    print("📞 Phone Investigation Demo")
    print("=" * 30)

    phone_number = "+1-555-123-4567"
    print(f"Looking up: {phone_number}")

    # Basic lookup
    result = await phone_investigation_workflow(
        phone_number=phone_number, depth=InvestigationDepth.BASIC
    )

    print(f"✓ Investigation completed")
    print(f"  Cost: ${result['metadata']['total_cost']:.2f}")
    print(f"  Time: {result['metadata']['execution_time']:.1f}s")
    print(f"  Success Rate: {result['metadata']['success_rate']:.1%}")

    # Show some results if available
    if result["results"]["detailed_results"]:
        successful_results = [
            r for r in result["results"]["detailed_results"] if r["success"]
        ]
        if successful_results:
            print(f"  Data sources: {len(result['results']['data_sources'])}")
            print(
                f"  Data points found: {result['results']['summary']['unique_data_points']}"
            )

    print()


async def demo_person_search():
    """Simple person search demonstration"""
    print("👤 Person Investigation Demo")
    print("=" * 30)

    print("Searching for: John Smith in Los Angeles, CA")

    result = await person_investigation_workflow(
        first_name="John",
        last_name="Smith",
        city="Los Angeles",
        state="CA",
        depth=InvestigationDepth.BASIC,
    )

    print(f"✓ Investigation completed")
    print(f"  Cost: ${result['metadata']['total_cost']:.2f}")
    print(f"  Success Rate: {result['metadata']['success_rate']:.1%}")
    print(f"  Coverage Score: {result['results']['summary']['coverage_score']:.1%}")
    print()


async def demo_business_lookup():
    """Simple business lookup demonstration"""
    print("🏢 Business Investigation Demo")
    print("=" * 30)

    print("Looking up: Acme Corporation")

    result = await business_due_diligence_workflow(
        company_name="Acme Corporation",
        city="New York",
        state="NY",
        depth=InvestigationDepth.BASIC,
    )

    print(f"✓ Investigation completed")
    print(f"  Cost: ${result['metadata']['total_cost']:.2f}")
    print(f"  Agents Used: {len(result['metadata']['agents_used'])}")
    print()


async def demo_address_lookup():
    """Simple address lookup demonstration"""
    print("🏠 Address Investigation Demo")
    print("=" * 30)

    print("Analyzing: 123 Main Street, Anytown, CA")

    result = await address_analysis_workflow(
        street_address="123 Main Street",
        city="Anytown",
        state="CA",
        depth=InvestigationDepth.BASIC,
    )

    print(f"✓ Investigation completed")
    print(f"  Cost: ${result['metadata']['total_cost']:.2f}")
    print(f"  Time: {result['metadata']['execution_time']:.1f}s")
    print()


async def demo_with_budget():
    """Demonstration with budget constraints"""
    print("💰 Budget-Constrained Investigation Demo")
    print("=" * 40)

    # Set a tight budget
    budget = WorkflowBudget(max_cost_usd=2.00, max_time_minutes=5)

    print(f"Budget: ${budget.max_cost_usd:.2f} max")
    print("Investigating person with budget constraints...")

    orchestrator = SleuthIntelOrchestrator()
    manager = WorkflowTemplateManager(orchestrator)

    result = await manager.execute_workflow(
        template_type="person_investigation",
        depth="comprehensive",  # Request comprehensive but budget will constrain
        query_data={
            "first_name": "Jane",
            "last_name": "Doe",
            "city": "Seattle",
            "state": "WA",
        },
        budget=budget,
    )

    print(f"✓ Budget-constrained investigation completed")
    print(f"  Actual Cost: ${result['metadata']['total_cost']:.2f}")
    print(
        f"  Budget Used: {(result['metadata']['total_cost'] / budget.max_cost_usd) * 100:.1f}%"
    )
    print(f"  Template Used: {result['template']}")
    print()


async def demo_cost_estimation():
    """Demonstrate cost estimation before execution"""
    print("📊 Cost Estimation Demo")
    print("=" * 25)

    orchestrator = SleuthIntelOrchestrator()
    manager = WorkflowTemplateManager(orchestrator)

    # Estimate costs for different scenarios
    scenarios = [
        ("Phone lookup (basic)", "phone_investigation", "basic", 1),
        ("Person search (comprehensive)", "person_investigation", "comprehensive", 1),
        ("Business investigation (deep)", "business_due_diligence", "deep", 1),
        ("Bulk processing (100 records)", "bulk_processing", "basic", 100),
    ]

    print("Cost estimates:")
    for name, template, depth, records in scenarios:
        try:
            estimate = manager.estimate_workflow_cost(template, depth, records)
            print(f"  {name}")
            print(f"    Total: ${estimate['total_estimated_cost']:.2f}")
            if records > 1:
                print(f"    Per record: ${estimate['per_record_cost']:.2f}")
        except Exception as e:
            print(f"  {name}: Error - {e}")

    print()


async def demo_progress_tracking():
    """Demonstrate progress tracking during investigation"""
    print("⏳ Progress Tracking Demo")
    print("=" * 25)

    progress_updates = []

    async def track_progress(update):
        progress_updates.append(update)
        status = update["status"]
        progress = update["progress"] * 100
        print(f"  Progress: {progress:.0f}% - Status: {status}")

        if update["errors"]:
            print(f"  ⚠️  Errors: {len(update['errors'])}")

    print("Starting person investigation with progress tracking...")

    orchestrator = SleuthIntelOrchestrator()
    manager = WorkflowTemplateManager(orchestrator)

    result = await manager.execute_workflow(
        template_type="person_investigation",
        depth="comprehensive",
        query_data={
            "first_name": "Progress",
            "last_name": "Tracker",
            "city": "Demo",
            "state": "TX",
        },
        progress_callback=track_progress,
    )

    print(f"✓ Investigation with tracking completed")
    print(f"  Total progress updates: {len(progress_updates)}")
    print(f"  Final success rate: {result['metadata']['success_rate']:.1%}")
    print()


async def demo_result_formats():
    """Demonstrate different result export formats"""
    print("📄 Result Export Demo")
    print("=" * 20)

    # Run a simple investigation
    result = await phone_investigation_workflow(
        phone_number="+1-555-DEMO-123", depth=InvestigationDepth.BASIC
    )

    print("Exporting results in different formats...")

    # Export to JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # JSON export
    json_file = f"demo_result_{timestamp}.json"
    with open(json_file, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"  ✓ JSON: {json_file}")

    # CSV summary export
    csv_file = f"demo_summary_{timestamp}.csv"
    with open(csv_file, "w") as f:
        f.write("Metric,Value\n")
        f.write(f"Workflow,{result.get('template', 'Unknown')}\n")
        f.write(f"Success Rate,{result['metadata']['success_rate']:.2%}\n")
        f.write(f"Total Cost,${result['metadata']['total_cost']:.2f}\n")
        f.write(f"Execution Time,{result['metadata']['execution_time']:.1f}s\n")
        f.write(f"Data Sources,{len(result['results']['data_sources'])}\n")
    print(f"  ✓ CSV: {csv_file}")

    # Text summary export
    txt_file = f"demo_report_{timestamp}.txt"
    with open(txt_file, "w") as f:
        f.write("SLEUTH INTEL INVESTIGATION REPORT\n")
        f.write("=" * 35 + "\n\n")
        f.write(f"Template: {result.get('template', 'Unknown')}\n")
        f.write(f"Execution Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("SUMMARY:\n")
        f.write(f"- Success Rate: {result['metadata']['success_rate']:.1%}\n")
        f.write(f"- Total Cost: ${result['metadata']['total_cost']:.2f}\n")
        f.write(
            f"- Execution Time: {result['metadata']['execution_time']:.1f} seconds\n"
        )
        f.write(f"- Data Sources: {len(result['results']['data_sources'])}\n")
        f.write(
            f"- Data Points: {result['results']['summary']['unique_data_points']}\n"
        )
    print(f"  ✓ TXT: {txt_file}")

    print()


async def run_simple_demos():
    """Run all simple demonstrations"""
    print("SLEUTH INTEL WORKFLOW TEMPLATES")
    print("Simple Usage Demonstrations")
    print("=" * 50)
    print()

    try:
        await demo_phone_lookup()
        await demo_person_search()
        await demo_business_lookup()
        await demo_address_lookup()
        await demo_with_budget()
        await demo_cost_estimation()
        await demo_progress_tracking()
        await demo_result_formats()

        print("=" * 50)
        print("✅ All demonstrations completed successfully!")
        print("\nNext steps:")
        print(
            "- Try the interactive mode: python workflow_usage_examples.py interactive"
        )
        print("- Explore advanced examples in advanced_workflow_examples.py")
        print("- Check the generated result files for output examples")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("\nThis might occur if:")
        print("- Required services are not running")
        print("- API credentials are not configured")
        print("- Network connectivity issues")


if __name__ == "__main__":
    asyncio.run(run_simple_demos())
