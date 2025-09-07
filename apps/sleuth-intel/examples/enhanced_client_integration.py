"""
Enhanced EnformionClient Integration Examples
Demonstrates how to integrate the enhanced client with existing Sleuth Intel architecture
"""

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.providers.enhanced_enformion_client import (
    EnformionAPIError,
    EnformionClient,
    ErrorType,
    MockEnformionClient,
)


class EnhancedSleuthInvestigation:
    """Example integration of Enhanced EnformionClient with Sleuth Intel workflows"""

    def __init__(self, use_mock: bool = True):
        """Initialize with enhanced client"""
        if use_mock:
            self.client = MockEnformionClient(enable_caching=True, enable_metrics=True)
            print("🧪 Using MockEnformionClient for demonstration")
        else:
            self.client = EnformionClient(
                enable_caching=True,
                enable_metrics=True,
                enable_circuit_breaker=True,
                rate_limit_per_minute=50,  # Conservative for production
            )
            print("🔗 Using real EnformionClient")

    def comprehensive_person_investigation(self, phone_number: str) -> Dict[str, Any]:
        """
        Comprehensive investigation starting with phone number
        Demonstrates enhanced features and error handling
        """
        print(f"\n🔍 Starting comprehensive investigation for: {phone_number}")
        investigation_results = {
            "query": {"phone": phone_number},
            "results": {},
            "metadata": {
                "investigation_id": f"inv_{int(time.time())}",
                "start_time": time.time(),
            },
        }

        try:
            # Step 1: Enhanced phone lookup with metadata
            print("  📞 Phase 1: Phone intelligence gathering...")
            phone_data = self.client.reverse_phone_search(
                phone_number=phone_number, include_metadata=True
            )

            investigation_results["results"]["phone_intelligence"] = phone_data
            print(
                f"     ✓ Phone lookup complete - Confidence: {phone_data.get('confidence_score', 'N/A')}"
            )

            # Step 2: Address intelligence if location found
            if "location" in phone_data or "address" in phone_data:
                print("  🏠 Phase 2: Address intelligence gathering...")

                # Extract address information
                address_info = phone_data.get("location", phone_data.get("address", {}))
                if isinstance(address_info, dict):
                    city = address_info.get("city")
                    state = address_info.get("state")
                    address = address_info.get("address", address_info.get("street"))

                    if address or (city and state):
                        address_data = self.client.address_search(
                            street_address=address or f"Unknown St",
                            city=city,
                            state=state,
                            include_residents=True,
                            include_property_details=True,
                            include_demographics=True,
                        )

                        investigation_results["results"][
                            "address_intelligence"
                        ] = address_data
                        residents = address_data.get("residents", [])
                        print(
                            f"     ✓ Address analysis complete - Found {len(residents)} residents"
                        )

            # Step 3: Person search if name identified
            associated_name = phone_data.get("associated_name")
            if associated_name:
                print("  👤 Phase 3: Person intelligence gathering...")

                name_parts = associated_name.split()
                if len(name_parts) >= 2:
                    person_data = self.client.person_search(
                        first_name=name_parts[0],
                        last_name=name_parts[-1],  # Use last part as last name
                        phone=phone_number,
                        include_relatives=True,
                        include_associates=True,
                        confidence_threshold=0.7,
                    )

                    investigation_results["results"][
                        "person_intelligence"
                    ] = person_data
                    results = person_data.get("results", [])
                    print(
                        f"     ✓ Person search complete - Found {len(results)} matches"
                    )

            # Step 4: Email intelligence if email addresses found
            email_addresses = self._extract_emails(investigation_results["results"])
            if email_addresses:
                print("  📧 Phase 4: Email intelligence gathering...")

                email_results = []
                for email in email_addresses[:3]:  # Limit to first 3 emails
                    try:
                        email_data = self.client.email_search(
                            email_address=email,
                            include_validation=True,
                            include_social_profiles=True,
                            include_domain_analysis=True,
                        )
                        email_results.append(email_data)
                        print(
                            f"     ✓ Email analysis: {email} - Deliverable: {email_data.get('is_deliverable', 'Unknown')}"
                        )

                    except EnformionAPIError as e:
                        print(f"     ⚠️ Email lookup failed for {email}: {e}")
                        continue

                investigation_results["results"]["email_intelligence"] = email_results

            # Step 5: Generate investigation summary
            investigation_results["summary"] = self._generate_investigation_summary(
                investigation_results
            )
            investigation_results["metadata"]["end_time"] = time.time()
            investigation_results["metadata"]["duration_seconds"] = (
                investigation_results["metadata"]["end_time"]
                - investigation_results["metadata"]["start_time"]
            )

            print(
                f"\n✅ Investigation complete in {investigation_results['metadata']['duration_seconds']:.2f}s"
            )
            return investigation_results

        except EnformionAPIError as e:
            error_info = {
                "error_type": e.error_type.value,
                "message": str(e),
                "timestamp": time.time(),
            }

            investigation_results["error"] = error_info
            print(f"\n❌ Investigation failed: {e}")

            if e.is_retryable():
                print("   🔄 Error is retryable - consider retry logic")

            return investigation_results

    def bulk_phone_investigation(self, phone_numbers: List[str]) -> Dict[str, Any]:
        """
        Bulk investigation of multiple phone numbers using enhanced bulk operations
        """
        print(f"\n📦 Starting bulk investigation for {len(phone_numbers)} phone numbers")

        # Prepare bulk requests
        bulk_requests = []
        for phone in phone_numbers:
            bulk_requests.append({"phone": phone, "include_metadata": True})

        try:
            # Submit bulk search
            bulk_result = self.client.bulk_search(
                search_requests=bulk_requests,
                search_type="phone",
                batch_size=10,
                concurrent_requests=3,
            )

            job_id = bulk_result.get("job_id")
            print(f"✓ Bulk job submitted: {job_id}")
            print(
                f"  Estimated completion: {bulk_result.get('estimated_completion', 'Unknown')}"
            )

            # In real implementation, you would poll for completion
            # For demo, we'll simulate the results
            simulated_results = []
            for i, phone in enumerate(phone_numbers):
                simulated_results.append(
                    {
                        "phone": phone,
                        "status": "completed",
                        "data": {
                            "phone_number": phone,
                            "line_type": "mobile" if i % 2 == 0 else "landline",
                            "carrier": f"Carrier {i % 3 + 1}",
                            "associated_name": f"Person {i + 1}",
                            "confidence_score": 0.8 + (i % 3) * 0.1,
                        },
                    }
                )

            return {
                "job_id": job_id,
                "status": "completed",
                "total_requests": len(phone_numbers),
                "results": simulated_results,
                "bulk_metadata": bulk_result.get("_sleuth_metadata", {}),
            }

        except EnformionAPIError as e:
            print(f"❌ Bulk investigation failed: {e}")
            return {"error": {"type": e.error_type.value, "message": str(e)}}

    def advanced_business_investigation(
        self, business_name: str, location: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Advanced business investigation with principal analysis
        """
        print(f"\n🏢 Starting business investigation: {business_name}")

        try:
            # Enhanced business search
            business_data = self.client.business_search(
                business_name=business_name,
                city=location.get("city") if location else None,
                state=location.get("state") if location else None,
                include_principals=True,
                include_competitors=True,
                include_financial=True,
            )

            results = {
                "business_intelligence": business_data,
                "principal_investigations": [],
            }

            # Investigate principals if found
            business_results = business_data.get("results", [])
            if business_results:
                business_info = business_results[0]  # Use first result
                principals = business_info.get("principals", [])

                print(f"  👥 Found {len(principals)} principals to investigate")

                for principal in principals[:3]:  # Limit to first 3 principals
                    principal_name = principal.get("name", "")
                    if principal_name:
                        print(f"     Investigating principal: {principal_name}")

                        name_parts = principal_name.split()
                        if len(name_parts) >= 2:
                            try:
                                person_data = self.client.person_search(
                                    first_name=name_parts[0],
                                    last_name=name_parts[-1],
                                    include_associates=True,
                                    confidence_threshold=0.8,
                                )

                                results["principal_investigations"].append(
                                    {
                                        "principal_name": principal_name,
                                        "principal_role": principal.get(
                                            "title", "Unknown"
                                        ),
                                        "investigation_results": person_data,
                                    }
                                )

                            except EnformionAPIError as e:
                                print(f"     ⚠️ Principal investigation failed: {e}")
                                continue

            print("✅ Business investigation complete")
            return results

        except EnformionAPIError as e:
            print(f"❌ Business investigation failed: {e}")
            return {"error": str(e)}

    def monitor_client_performance(self) -> Dict[str, Any]:
        """
        Monitor client performance and health
        """
        print("\n📊 Monitoring client performance...")

        # Health check
        health = self.client.health_check()
        print(f"  System Status: {health['status']}")

        if hasattr(self.client, "get_metrics_summary"):
            # Get performance metrics
            metrics = self.client.get_metrics_summary(period_minutes=60)

            print(f"  Total Requests: {metrics['total_requests']}")
            print(f"  Success Rate: {metrics['success_rate']:.2%}")
            print(f"  Cache Hit Rate: {metrics['cache_hit_rate']:.2%}")
            print(
                f"  Average Response Time: {metrics['average_response_time_ms']:.2f}ms"
            )

            if metrics["total_requests"] > 0:
                print("\n  📈 Performance Analysis:")
                if metrics["cache_hit_rate"] < 0.3:
                    print("    • Consider optimizing cache usage")
                if metrics["success_rate"] < 0.95:
                    print("    • High error rate detected")
                if metrics["average_response_time_ms"] > 1000:
                    print("    • High latency detected")

            return {
                "health": health,
                "metrics": metrics,
                "recommendations": self._generate_performance_recommendations(metrics),
            }
        else:
            return {"health": health}

    def predict_usage_costs(self, planned_usage: Dict[str, int]) -> Dict[str, Any]:
        """
        Predict usage costs based on planned request patterns
        """
        print("\n💰 Predicting usage costs...")

        if hasattr(self.client, "predict_credit_usage"):
            predictions = self.client.predict_credit_usage(planned_usage)

            print("  📊 Usage Predictions:")
            print(f"    Hourly Credits: {predictions['total_credits_per_hour']}")
            print(f"    Daily Credits: {predictions['total_credits_per_day']}")
            print(f"    Monthly Credits: {predictions['total_credits_per_month']}")

            # Cost analysis (assuming $0.10 per credit as example)
            cost_per_credit = 0.10
            monthly_cost = predictions["total_credits_per_month"] * cost_per_credit

            predictions["cost_analysis"] = {
                "cost_per_credit": cost_per_credit,
                "monthly_cost_usd": monthly_cost,
                "annual_cost_usd": monthly_cost * 12,
            }

            print(f"  💵 Estimated Monthly Cost: ${monthly_cost:.2f}")

            return predictions
        else:
            print("  ⚠️ Cost prediction not available with current client")
            return {"error": "Cost prediction not supported"}

    # Helper methods

    def _extract_emails(self, results: Dict) -> List[str]:
        """Extract email addresses from investigation results"""
        emails = []

        # Extract from phone data
        phone_data = results.get("phone_intelligence", {})
        if "email" in phone_data:
            emails.append(phone_data["email"])

        # Extract from person data
        person_data = results.get("person_intelligence", {})
        person_results = person_data.get("results", [])
        for person in person_results:
            person_emails = person.get("emails", [])
            emails.extend(person_emails)

        # Extract from address data
        address_data = results.get("address_intelligence", {})
        residents = address_data.get("residents", [])
        for resident in residents:
            if "email" in resident:
                emails.append(resident["email"])

        # Remove duplicates and return
        return list(set(emails))

    def _generate_investigation_summary(self, investigation: Dict) -> Dict[str, Any]:
        """Generate a summary of investigation findings"""
        results = investigation.get("results", {})

        summary = {"total_data_points": 0, "confidence_scores": [], "key_findings": []}

        # Analyze phone intelligence
        phone_data = results.get("phone_intelligence", {})
        if phone_data:
            summary["total_data_points"] += 1
            if "confidence_score" in phone_data:
                summary["confidence_scores"].append(phone_data["confidence_score"])

            if "associated_name" in phone_data:
                summary["key_findings"].append(
                    f"Phone associated with: {phone_data['associated_name']}"
                )

        # Analyze address intelligence
        address_data = results.get("address_intelligence", {})
        if address_data:
            summary["total_data_points"] += 1
            residents = address_data.get("residents", [])
            if residents:
                summary["key_findings"].append(
                    f"Address has {len(residents)} residents"
                )

        # Analyze person intelligence
        person_data = results.get("person_intelligence", {})
        if person_data:
            person_results = person_data.get("results", [])
            summary["total_data_points"] += len(person_results)
            summary["key_findings"].append(
                f"Found {len(person_results)} person matches"
            )

        # Calculate average confidence
        if summary["confidence_scores"]:
            summary["average_confidence"] = sum(summary["confidence_scores"]) / len(
                summary["confidence_scores"]
            )

        return summary

    def _generate_performance_recommendations(self, metrics: Dict) -> List[str]:
        """Generate performance recommendations based on metrics"""
        recommendations = []

        if metrics.get("cache_hit_rate", 0) < 0.3:
            recommendations.append(
                "Improve cache utilization by reducing duplicate requests"
            )

        if metrics.get("success_rate", 1) < 0.95:
            recommendations.append(
                "Investigate high error rates and implement better error handling"
            )

        if metrics.get("average_response_time_ms", 0) > 1000:
            recommendations.append(
                "High latency detected - consider optimizing requests or using bulk operations"
            )

        if not recommendations:
            recommendations.append(
                "Performance looks good - no immediate optimizations needed"
            )

        return recommendations


def main():
    """Demonstrate enhanced client integration"""
    print("🚀 Enhanced EnformionClient Integration Demo")
    print("=" * 60)

    # Initialize investigation system
    investigator = EnhancedSleuthInvestigation(use_mock=True)

    # Example 1: Comprehensive person investigation
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Comprehensive Person Investigation")
    print("=" * 60)

    investigation_result = investigator.comprehensive_person_investigation("9103925349")

    # Print summary
    if "summary" in investigation_result:
        summary = investigation_result["summary"]
        print(f"\n📋 Investigation Summary:")
        print(f"  • Data Points: {summary.get('total_data_points', 0)}")
        print(f"  • Key Findings: {len(summary.get('key_findings', []))}")
        if "average_confidence" in summary:
            print(f"  • Average Confidence: {summary['average_confidence']:.2f}")

        for finding in summary.get("key_findings", []):
            print(f"    - {finding}")

    # Example 2: Bulk investigation
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Bulk Phone Investigation")
    print("=" * 60)

    phone_list = ["9103925349", "7045551234", "6785559876", "9194567890"]
    bulk_result = investigator.bulk_phone_investigation(phone_list)

    if "results" in bulk_result:
        print(f"\n📦 Bulk Results Summary:")
        print(f"  • Total Processed: {len(bulk_result['results'])}")
        successful = sum(
            1 for r in bulk_result["results"] if r["status"] == "completed"
        )
        print(f"  • Successful: {successful}")
        print(f"  • Success Rate: {successful/len(bulk_result['results']):.2%}")

    # Example 3: Business investigation
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Business Investigation")
    print("=" * 60)

    business_result = investigator.advanced_business_investigation(
        "Example Corporation", {"city": "Charlotte", "state": "NC"}
    )

    if "principal_investigations" in business_result:
        principals = business_result["principal_investigations"]
        print(f"\n🏢 Business Investigation Summary:")
        print(f"  • Principals Investigated: {len(principals)}")

        for principal in principals:
            name = principal.get("principal_name", "Unknown")
            role = principal.get("principal_role", "Unknown")
            print(f"    - {name} ({role})")

    # Example 4: Performance monitoring
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Performance Monitoring")
    print("=" * 60)

    performance_info = investigator.monitor_client_performance()

    if "recommendations" in performance_info:
        recommendations = performance_info["recommendations"]
        print(f"\n📊 Performance Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")

    # Example 5: Usage cost prediction
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Usage Cost Prediction")
    print("=" * 60)

    planned_usage = {
        "phone_search": 500,  # 500 per hour
        "person_search": 200,  # 200 per hour
        "address_search": 100,  # 100 per hour
        "email_search": 50,  # 50 per hour
        "business_search": 25,  # 25 per hour
    }

    cost_prediction = investigator.predict_usage_costs(planned_usage)

    if "cost_analysis" in cost_prediction:
        cost_info = cost_prediction["cost_analysis"]
        print(f"\n💰 Cost Analysis Summary:")
        print(f"  • Monthly Cost: ${cost_info['monthly_cost_usd']:.2f}")
        print(f"  • Annual Cost: ${cost_info['annual_cost_usd']:.2f}")

    print("\n" + "=" * 60)
    print("✅ Integration Demo Complete")
    print("=" * 60)

    # Save example results for reference
    example_results = {
        "investigation": investigation_result,
        "bulk_processing": bulk_result,
        "business_intelligence": business_result,
        "performance_monitoring": performance_info,
        "cost_prediction": cost_prediction,
    }

    # Write to file for inspection
    with open("integration_demo_results.json", "w") as f:
        json.dump(example_results, f, indent=2, default=str)

    print("📄 Detailed results saved to: integration_demo_results.json")


if __name__ == "__main__":
    main()
