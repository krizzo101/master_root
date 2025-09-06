#!/usr/bin/env python3
"""
PhoneSearchAgent Usage Examples
Demonstrates various phone lookup and analysis capabilities
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models.person import PhoneType

from agents.phone_search_agent import PhoneSearchAgent, RiskLevel


class PhoneSearchExamples:
    """Comprehensive examples of PhoneSearchAgent usage"""

    def __init__(self):
        """Initialize agent with production settings"""
        self.agent = PhoneSearchAgent(
            enable_person_enrichment=True,
            fraud_detection_threshold=0.6,
            include_historical_data=True,
        )

    def basic_phone_lookup(self):
        """Example 1: Basic reverse phone lookup"""
        print("=" * 60)
        print("Example 1: Basic Reverse Phone Lookup")
        print("=" * 60)

        phone_number = "5551234567"  # Replace with actual number for testing

        try:
            result = self.agent.reverse_phone_lookup(phone_number)

            print(f"Phone Number: {result.formatted_number}")
            print(f"Carrier: {result.carrier_info.name or 'Unknown'}")
            print(f"Line Type: {result.carrier_info.type or 'Unknown'}")
            print(f"Location: {result.carrier_info.location or 'Unknown'}")
            print(f"Confidence Score: {result.confidence_score:.2f}")

            if result.owner_info:
                print(f"Owner: {result.owner_info.name.display_name}")
                if result.owner_info.addresses:
                    addr = result.owner_info.addresses[0]
                    print(
                        f"Address: {addr.street}, {addr.city}, {addr.state} {addr.zip_code}"
                    )

            if result.fraud_assessment:
                print(f"Risk Level: {result.fraud_assessment.overall_risk}")
                print(f"Spam Score: {result.fraud_assessment.spam_score:.2f}")

        except Exception as e:
            print(f"Error: {e}")

        print()

    def phone_validation_examples(self):
        """Example 2: Phone number validation and formatting"""
        print("=" * 60)
        print("Example 2: Phone Number Validation and Formatting")
        print("=" * 60)

        test_phones = [
            "5551234567",
            "(555) 123-4567",
            "555-123-4567",
            "+1 555 123 4567",
            "15551234567",
            "invalid_phone",
            "123",
            "0551234567",  # Invalid area code
        ]

        for phone in test_phones:
            is_valid, message = self.agent.validate_phone_format(phone)
            print(f"Phone: {phone:15} | Valid: {is_valid:5} | {message}")

            if is_valid:
                try:
                    normalized = self.agent.normalize_phone_number(phone)
                    formatted_national = self.agent._format_phone_number(
                        normalized, "national"
                    )
                    formatted_intl = self.agent._format_phone_number(
                        normalized, "international"
                    )

                    print(f"  Normalized: {normalized}")
                    print(f"  National:   {formatted_national}")
                    print(f"  International: {formatted_intl}")
                except Exception as e:
                    print(f"  Format Error: {e}")

            print()

    def carrier_and_line_type_detection(self):
        """Example 3: Carrier and line type detection"""
        print("=" * 60)
        print("Example 3: Carrier and Line Type Detection")
        print("=" * 60)

        test_numbers = [
            "5551234567",  # Regular mobile
            "8001234567",  # Toll-free
            "2125551234",  # NYC landline
            "7021234567",  # Las Vegas mobile
        ]

        for phone in test_numbers:
            try:
                print(f"Analyzing: {phone}")

                # Get carrier info
                carrier_info = self.agent.get_carrier_info(phone)
                print(f"  Carrier: {carrier_info.name or 'Unknown'}")
                print(f"  Type: {carrier_info.type or 'Unknown'}")
                print(f"  Location: {carrier_info.location or 'Unknown'}")
                print(f"  Ported: {carrier_info.is_ported}")
                print(f"  Confidence: {carrier_info.confidence:.2f}")

                # Get line type
                line_type = self.agent.get_line_type(phone)
                print(f"  Line Type: {line_type}")

            except Exception as e:
                print(f"  Error: {e}")

            print()

    def fraud_risk_assessment(self):
        """Example 4: Spam and fraud risk assessment"""
        print("=" * 60)
        print("Example 4: Spam and Fraud Risk Assessment")
        print("=" * 60)

        # Test various risk levels
        test_cases = [
            ("5551234567", "Normal mobile number"),
            ("8001234567", "Toll-free number"),
            ("9005551234", "Premium rate number"),
            ("1111111111", "Repeated digits"),
            ("2165551234", "High-risk area code"),
        ]

        for phone, description in test_cases:
            try:
                print(f"Testing: {phone} ({description})")

                risk_assessment = self.agent.assess_spam_risk(phone)

                print(f"  Overall Risk: {risk_assessment.overall_risk}")
                print(f"  Spam Score: {risk_assessment.spam_score:.2f}")
                print(f"  Reputation Score: {risk_assessment.reputation_score:.2f}")

                if risk_assessment.fraud_indicators:
                    print("  Fraud Indicators:")
                    for indicator in risk_assessment.fraud_indicators:
                        print(f"    - {indicator}")

                if risk_assessment.suspicious_patterns:
                    print("  Suspicious Patterns:")
                    for pattern in risk_assessment.suspicious_patterns:
                        print(f"    - {pattern}")

            except Exception as e:
                print(f"  Error: {e}")

            print()

    def batch_phone_lookup(self):
        """Example 5: Batch phone lookup processing"""
        print("=" * 60)
        print("Example 5: Batch Phone Lookup")
        print("=" * 60)

        phone_list = [
            "5551234567",
            "5557654321",
            "8001234567",
            "2125551234",
            "7021234567",
        ]

        print(f"Processing {len(phone_list)} phone numbers...")

        try:
            results = self.agent.batch_phone_lookup(
                phone_list,
                max_concurrent=2,  # Limit concurrent requests
                include_owner_details=True,
            )

            print(f"Successfully processed {len(results)} numbers:")
            print()

            for phone, result in results.items():
                print(f"Phone: {result.formatted_number}")
                print(f"  Carrier: {result.carrier_info.name or 'Unknown'}")
                print(
                    f"  Risk: {result.fraud_assessment.overall_risk if result.fraud_assessment else 'Unknown'}"
                )
                print(
                    f"  Owner: {result.owner_info.name.display_name if result.owner_info else 'Unknown'}"
                )
                print(f"  Confidence: {result.confidence_score:.2f}")
                print()

        except Exception as e:
            print(f"Batch lookup error: {e}")

    def owner_identification_example(self):
        """Example 6: Owner identification and related numbers"""
        print("=" * 60)
        print("Example 6: Owner Identification and Related Numbers")
        print("=" * 60)

        phone = "5551234567"

        try:
            # Identify owner
            owner = self.agent.identify_owner(phone)

            if owner:
                print(f"Owner Information:")
                print(f"  Name: {owner.name.display_name}")

                if owner.demographics:
                    print(f"  Age: {owner.demographics.age or 'Unknown'}")
                    print(f"  Gender: {owner.demographics.gender or 'Unknown'}")

                if owner.addresses:
                    print("  Addresses:")
                    for addr in owner.addresses[:3]:  # Show top 3
                        print(
                            f"    {addr.street}, {addr.city}, {addr.state} {addr.zip_code}"
                        )

                if owner.emails:
                    print("  Email Addresses:")
                    for email in owner.emails[:3]:  # Show top 3
                        print(f"    {email.address}")

                # Find related phone numbers
                related_numbers = self.agent.find_related_numbers(phone)
                if related_numbers:
                    print("  Related Phone Numbers:")
                    for related_phone in related_numbers:
                        formatted = self.agent._format_phone_number(related_phone)
                        print(f"    {formatted}")
            else:
                print("No owner information found")

        except Exception as e:
            print(f"Owner identification error: {e}")

        print()

    def phone_metadata_analysis(self):
        """Example 7: Detailed phone metadata analysis"""
        print("=" * 60)
        print("Example 7: Phone Metadata Analysis")
        print("=" * 60)

        phone = "5551234567"

        try:
            result = self.agent.reverse_phone_lookup(phone)
            metadata = result.metadata

            print(f"Phone Metadata for {result.formatted_number}:")
            print(f"  Area Code: {metadata.area_code}")
            print(f"  Exchange: {metadata.exchange}")
            print(f"  Subscriber: {metadata.subscriber}")
            print(f"  Country Code: +{metadata.country_code}")
            print(f"  National Format: {metadata.formatted_national}")
            print(f"  International Format: {metadata.formatted_international}")
            print(f"  Is Valid: {metadata.is_valid}")
            print(f"  Number Type: {metadata.number_type}")
            print(
                f"  Geographic Description: {metadata.geographic_description or 'Unknown'}"
            )

            if result.history:
                print("  Historical Data:")
                for entry in result.history:
                    print(
                        f"    {entry.timestamp}: {entry.status} - {entry.carrier or 'Unknown'}"
                    )

        except Exception as e:
            print(f"Metadata analysis error: {e}")

        print()

    def advanced_search_scenarios(self):
        """Example 8: Advanced search scenarios"""
        print("=" * 60)
        print("Example 8: Advanced Search Scenarios")
        print("=" * 60)

        scenarios = [
            {
                "name": "Suspicious Caller Investigation",
                "phone": "8001234567",
                "description": "Investigating suspicious toll-free caller",
            },
            {
                "name": "Mobile Number Verification",
                "phone": "5551234567",
                "description": "Verifying mobile number for account security",
            },
            {
                "name": "Business Line Analysis",
                "phone": "8005551234",
                "description": "Analyzing business customer service line",
            },
        ]

        for scenario in scenarios:
            print(f"Scenario: {scenario['name']}")
            print(f"Description: {scenario['description']}")
            print(f"Phone: {scenario['phone']}")

            try:
                # Comprehensive lookup with all features
                result = self.agent.reverse_phone_lookup(
                    scenario["phone"],
                    include_owner_details=True,
                    include_fraud_assessment=True,
                )

                # Risk assessment
                if result.fraud_assessment:
                    risk = result.fraud_assessment.overall_risk
                    spam_score = result.fraud_assessment.spam_score

                    print(f"  Risk Assessment: {risk} (Spam Score: {spam_score:.2f})")

                    if risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                        print("  ⚠️  HIGH RISK - Recommend blocking or verification")
                    elif risk == RiskLevel.MEDIUM:
                        print("  ⚡ MEDIUM RISK - Proceed with caution")
                    else:
                        print("  ✅ LOW RISK - Appears legitimate")

                # Carrier analysis
                carrier = result.carrier_info
                print(
                    f"  Carrier: {carrier.name or 'Unknown'} ({carrier.type or 'Unknown'})"
                )

                if carrier.is_ported:
                    print("  📱 Number has been ported")

                # Owner information
                if result.owner_info:
                    owner = result.owner_info
                    print(f"  Registered Owner: {owner.name.display_name}")

                    # Check for business indicators
                    if any(
                        "corp" in addr.street.lower() or "inc" in addr.street.lower()
                        for addr in owner.addresses
                        if addr.street
                    ):
                        print("  🏢 Appears to be business-related")

                print(f"  Overall Confidence: {result.confidence_score:.2f}")

            except Exception as e:
                print(f"  Error analyzing {scenario['phone']}: {e}")

            print("-" * 40)

    def export_results_example(self):
        """Example 9: Export results in different formats"""
        print("=" * 60)
        print("Example 9: Export Results")
        print("=" * 60)

        phone = "5551234567"

        try:
            result = self.agent.reverse_phone_lookup(phone)

            # Export as JSON
            result_dict = {
                "phone_number": result.phone_number,
                "formatted_number": result.formatted_number,
                "carrier": {
                    "name": result.carrier_info.name,
                    "type": result.carrier_info.type,
                    "location": result.carrier_info.location,
                    "is_ported": result.carrier_info.is_ported,
                },
                "fraud_assessment": {
                    "overall_risk": result.fraud_assessment.overall_risk
                    if result.fraud_assessment
                    else None,
                    "spam_score": result.fraud_assessment.spam_score
                    if result.fraud_assessment
                    else 0.0,
                    "fraud_indicators": result.fraud_assessment.fraud_indicators
                    if result.fraud_assessment
                    else [],
                },
                "owner": {
                    "name": result.owner_info.name.display_name
                    if result.owner_info
                    else None,
                    "addresses": [
                        f"{addr.street}, {addr.city}, {addr.state} {addr.zip_code}"
                        for addr in (
                            result.owner_info.addresses if result.owner_info else []
                        )
                    ],
                },
                "confidence_score": result.confidence_score,
                "lookup_timestamp": result.lookup_timestamp.isoformat(),
            }

            print("JSON Export:")
            print(json.dumps(result_dict, indent=2))

            # Export as CSV-like format
            print("\nCSV-like Export:")
            print("Phone,Formatted,Carrier,Type,Location,Risk,Owner,Confidence")
            csv_line = f"{result.phone_number},{result.formatted_number},"
            csv_line += f"{result.carrier_info.name or ''},"
            csv_line += f"{result.carrier_info.type or ''},"
            csv_line += f"{result.carrier_info.location or ''},"
            csv_line += f"{result.fraud_assessment.overall_risk if result.fraud_assessment else ''},"
            csv_line += (
                f"{result.owner_info.name.display_name if result.owner_info else ''},"
            )
            csv_line += f"{result.confidence_score:.2f}"
            print(csv_line)

        except Exception as e:
            print(f"Export error: {e}")

    def run_all_examples(self):
        """Run all examples"""
        print("PhoneSearchAgent Comprehensive Examples")
        print("=" * 60)
        print()

        examples = [
            self.basic_phone_lookup,
            self.phone_validation_examples,
            self.carrier_and_line_type_detection,
            self.fraud_risk_assessment,
            self.batch_phone_lookup,
            self.owner_identification_example,
            self.phone_metadata_analysis,
            self.advanced_search_scenarios,
            self.export_results_example,
        ]

        for i, example in enumerate(examples, 1):
            try:
                example()
                if i < len(examples):
                    input("Press Enter to continue to next example...")
                    print()
            except KeyboardInterrupt:
                print("\nExamples interrupted by user")
                break
            except Exception as e:
                print(f"Error in example {i}: {e}")
                continue


def main():
    """Main function to run examples"""
    examples = PhoneSearchExamples()

    if len(sys.argv) > 1:
        # Run specific example
        example_name = sys.argv[1]
        if hasattr(examples, example_name):
            getattr(examples, example_name)()
        else:
            print(f"Example '{example_name}' not found")
            print("Available examples:")
            methods = [
                method
                for method in dir(examples)
                if not method.startswith("_")
                and callable(getattr(examples, method))
                and method != "run_all_examples"
            ]
            for method in methods:
                print(f"  - {method}")
    else:
        # Run all examples
        examples.run_all_examples()


if __name__ == "__main__":
    main()
