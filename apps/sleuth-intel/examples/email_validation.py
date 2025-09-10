#!/usr/bin/env python3
"""
Email Validation Example
========================

This example demonstrates email validation, verification,
and social profile discovery capabilities.

Setup:
------
1. Install sleuth-intel: pip install sleuth-intel
2. Set environment variables:
   - ENFORMION_API_USERNAME
   - ENFORMION_API_PASSWORD

Usage:
------
python email_validation.py
"""

import asyncio
import csv
import json
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from sleuth_intel import SleuthIntel
from sleuth_intel.models import EmailVerificationRequest, PersonSearchRequest


class EmailValidator:
    """Email validation and enrichment handler."""

    def __init__(self):
        self.client = SleuthIntel()
        self.validation_results = []

    async def validate_email(
        self,
        email: str,
        check_deliverability: bool = True,
        find_social_profiles: bool = True,
        find_owner: bool = True,
    ) -> Dict[str, Any]:
        """
        Validate and enrich a single email address.

        Args:
            email: Email address to validate
            check_deliverability: Check if email is deliverable
            find_social_profiles: Search for associated social media
            find_owner: Try to identify the email owner

        Returns:
            Dictionary with validation results
        """
        print(f"✉️ Validating: {email}")

        result = {
            "email": email,
            "timestamp": datetime.now().isoformat(),
            "validation": {},
            "owner": {},
            "social_profiles": {},
            "risk_indicators": [],
        }

        try:
            # Step 1: Basic validation and deliverability check
            request = EmailVerificationRequest(
                email=email,
                check_smtp=check_deliverability,
                check_dns=True,
                check_disposable=True,
                check_free_provider=True,
            )

            response = await self.client.email_verification(request)

            if response.success:
                result["validation"] = {
                    "valid_format": response.is_valid_format,
                    "valid_domain": response.is_valid_domain,
                    "deliverable": response.is_deliverable,
                    "smtp_valid": response.smtp_valid,
                    "disposable": response.is_disposable,
                    "free_provider": response.is_free_provider,
                    "role_based": response.is_role_based,
                    "catch_all": response.is_catch_all,
                    "domain": response.domain,
                    "username": response.username,
                    "suggestion": response.did_you_mean,
                }

                # Risk assessment
                if response.is_disposable:
                    result["risk_indicators"].append("Disposable email")
                if response.is_role_based:
                    result["risk_indicators"].append("Role-based email")
                if not response.is_deliverable:
                    result["risk_indicators"].append("Not deliverable")
                if response.is_catch_all:
                    result["risk_indicators"].append("Catch-all domain")

                print(f"  ✅ Valid: {response.is_valid_format}")
                print(f"  📬 Deliverable: {response.is_deliverable}")
                print(f"  🌐 Domain: {response.domain}")

                # Step 2: Find social profiles
                if find_social_profiles and response.social_profiles:
                    result["social_profiles"] = response.social_profiles
                    print(f"  👥 Social profiles found: {len(response.social_profiles)}")

                # Step 3: Try to identify owner
                if find_owner and response.is_valid_format:
                    owner_info = await self._find_email_owner(email)
                    if owner_info:
                        result["owner"] = owner_info
                        print(f"  👤 Owner: {owner_info.get('name', 'Unknown')}")
            else:
                result["validation"]["error"] = response.error_message
                print(f"  ❌ Validation failed: {response.error_message}")

        except Exception as e:
            result["error"] = str(e)
            print(f"  ❌ Error: {str(e)}")

        return result

    async def _find_email_owner(self, email: str) -> Optional[Dict[str, Any]]:
        """Try to identify the owner of an email address."""
        try:
            # Use email as a search parameter
            request = PersonSearchRequest(
                email=email, include_phones=True, include_addresses=True
            )

            response = await self.client.person_search(request)

            if response.success and response.results:
                # Return the most likely match
                person = response.results[0]
                return {
                    "name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                    "age": person.get("age"),
                    "location": f"{person.get('city', '')}, {person.get('state', '')}".strip(
                        ", "
                    ),
                    "phones": person.get("phones", [])[:3],
                    "confidence": person.get("match_confidence", 0),
                }
        except:
            pass

        return None

    async def bulk_validate(
        self,
        emails: List[str],
        output_format: str = "json",
        rate_limit_delay: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Validate multiple email addresses in bulk.

        Args:
            emails: List of email addresses
            output_format: Output format (json, csv)
            rate_limit_delay: Delay between requests in seconds

        Returns:
            List of validation results
        """
        print(f"\n📧 Bulk Email Validation")
        print(f"Processing {len(emails)} emails...")
        print("=" * 50)

        results = []
        valid_count = 0
        deliverable_count = 0

        for i, email in enumerate(emails, 1):
            print(f"\n[{i}/{len(emails)}] {email}")

            result = await self.validate_email(
                email=email,
                check_deliverability=True,
                find_social_profiles=True,
                find_owner=False,  # Skip owner lookup for bulk validation
            )

            results.append(result)

            if result.get("validation", {}).get("valid_format"):
                valid_count += 1
            if result.get("validation", {}).get("deliverable"):
                deliverable_count += 1

            # Rate limiting
            if i < len(emails):
                await asyncio.sleep(rate_limit_delay)

        # Generate summary
        summary = {
            "total_emails": len(emails),
            "valid_emails": valid_count,
            "deliverable_emails": deliverable_count,
            "invalid_emails": len(emails) - valid_count,
            "validation_rate": (valid_count / len(emails) * 100) if emails else 0,
            "deliverability_rate": (deliverable_count / len(emails) * 100)
            if emails
            else 0,
        }

        print("\n" + "=" * 50)
        print("📊 Validation Summary:")
        print(f"  • Total: {summary['total_emails']}")
        print(
            f"  • Valid: {summary['valid_emails']} ({summary['validation_rate']:.1f}%)"
        )
        print(
            f"  • Deliverable: {summary['deliverable_emails']} ({summary['deliverability_rate']:.1f}%)"
        )

        # Save results
        if output_format == "csv":
            self._save_csv(results, summary)
        else:
            self._save_json(results, summary)

        return results

    def _save_json(self, results: List[Dict], summary: Dict):
        """Save results to JSON file."""
        output_file = f"email_validation_{datetime.now():%Y%m%d_%H%M%S}.json"

        with open(output_file, "w") as f:
            json.dump(
                {
                    "summary": summary,
                    "timestamp": datetime.now().isoformat(),
                    "results": results,
                },
                f,
                indent=2,
            )

        print(f"\n💾 Results saved to: {output_file}")

    def _save_csv(self, results: List[Dict], summary: Dict):
        """Save results to CSV file."""
        output_file = f"email_validation_{datetime.now():%Y%m%d_%H%M%S}.csv"

        with open(output_file, "w", newline="") as f:
            fieldnames = [
                "email",
                "valid_format",
                "deliverable",
                "domain",
                "disposable",
                "free_provider",
                "role_based",
                "owner_name",
                "risk_indicators",
                "social_profiles",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for result in results:
                validation = result.get("validation", {})
                owner = result.get("owner", {})

                row = {
                    "email": result["email"],
                    "valid_format": validation.get("valid_format", False),
                    "deliverable": validation.get("deliverable", False),
                    "domain": validation.get("domain", ""),
                    "disposable": validation.get("disposable", False),
                    "free_provider": validation.get("free_provider", False),
                    "role_based": validation.get("role_based", False),
                    "owner_name": owner.get("name", ""),
                    "risk_indicators": ", ".join(result.get("risk_indicators", [])),
                    "social_profiles": len(result.get("social_profiles", {})),
                }
                writer.writerow(row)

        print(f"\n💾 Results saved to: {output_file}")

    async def domain_analysis(self, domain: str) -> Dict[str, Any]:
        """
        Analyze all email addresses from a specific domain.

        Args:
            domain: Domain to analyze

        Returns:
            Domain analysis results
        """
        print(f"\n🌐 Domain Analysis: {domain}")
        print("=" * 50)

        analysis = {
            "domain": domain,
            "timestamp": datetime.now().isoformat(),
            "mx_records": [],
            "spf_record": None,
            "dmarc_record": None,
            "catch_all": False,
            "disposable": False,
            "free_provider": False,
            "reputation": {},
            "common_patterns": [],
        }

        try:
            # Check domain configuration
            test_email = f"test@{domain}"
            request = EmailVerificationRequest(
                email=test_email, check_dns=True, check_mx=True
            )

            response = await self.client.email_verification(request)

            if response.success:
                analysis["mx_records"] = response.mx_records
                analysis["catch_all"] = response.is_catch_all
                analysis["disposable"] = response.is_disposable
                analysis["free_provider"] = response.is_free_provider

                print(f"  ✅ Domain exists")
                print(f"  📧 MX Records: {len(response.mx_records)}")
                print(f"  🎯 Catch-all: {response.is_catch_all}")
                print(f"  🗑️ Disposable: {response.is_disposable}")

                # Identify common email patterns
                common_patterns = [
                    "info",
                    "contact",
                    "support",
                    "sales",
                    "admin",
                    "hello",
                    "team",
                    "help",
                    "service",
                    "inquiry",
                ]

                print(f"\n  🔍 Checking common email patterns...")
                for pattern in common_patterns:
                    test_email = f"{pattern}@{domain}"
                    req = EmailVerificationRequest(email=test_email, check_smtp=False)
                    resp = await self.client.email_verification(req)

                    if resp.success and resp.is_valid_format:
                        analysis["common_patterns"].append(
                            {"email": test_email, "exists": resp.is_deliverable}
                        )
                        if resp.is_deliverable:
                            print(f"    ✅ {test_email}")

                    await asyncio.sleep(0.2)  # Rate limiting

            else:
                analysis["error"] = response.error_message
                print(f"  ❌ Domain check failed: {response.error_message}")

        except Exception as e:
            analysis["error"] = str(e)
            print(f"  ❌ Error: {str(e)}")

        return analysis

    async def close(self):
        """Clean up resources."""
        await self.client.close()


class EmailCampaignValidator:
    """Validate email lists for marketing campaigns."""

    def __init__(self):
        self.validator = EmailValidator()

    async def validate_campaign_list(
        self,
        email_list: List[str],
        remove_invalid: bool = True,
        remove_risky: bool = True,
        remove_role_based: bool = True,
    ) -> Dict[str, Any]:
        """
        Validate and clean an email list for campaigns.

        Args:
            email_list: List of email addresses
            remove_invalid: Remove invalid emails
            remove_risky: Remove risky emails (disposable, catch-all)
            remove_role_based: Remove role-based emails

        Returns:
            Cleaned list and statistics
        """
        print(f"\n📮 Campaign Email List Validation")
        print(f"Original list size: {len(email_list)} emails")
        print("=" * 50)

        results = await self.validator.bulk_validate(email_list)

        clean_list = []
        removed = defaultdict(list)

        for result in results:
            email = result["email"]
            validation = result.get("validation", {})

            should_remove = False
            removal_reason = None

            # Check removal criteria
            if remove_invalid and not validation.get("valid_format"):
                should_remove = True
                removal_reason = "invalid_format"
            elif remove_invalid and not validation.get("deliverable"):
                should_remove = True
                removal_reason = "undeliverable"
            elif remove_risky and validation.get("disposable"):
                should_remove = True
                removal_reason = "disposable"
            elif remove_risky and validation.get("catch_all"):
                should_remove = True
                removal_reason = "catch_all"
            elif remove_role_based and validation.get("role_based"):
                should_remove = True
                removal_reason = "role_based"

            if should_remove:
                removed[removal_reason].append(email)
            else:
                clean_list.append(email)

        # Generate report
        report = {
            "original_count": len(email_list),
            "clean_count": len(clean_list),
            "removed_count": len(email_list) - len(clean_list),
            "removal_rate": (
                (len(email_list) - len(clean_list)) / len(email_list) * 100
            )
            if email_list
            else 0,
            "removed_breakdown": {
                reason: len(emails) for reason, emails in removed.items()
            },
            "clean_list": clean_list,
            "removed_emails": dict(removed),
        }

        print("\n📊 Validation Results:")
        print(f"  • Original: {report['original_count']}")
        print(f"  • Clean: {report['clean_count']}")
        print(f"  • Removed: {report['removed_count']} ({report['removal_rate']:.1f}%)")
        print("\n  Removal Breakdown:")
        for reason, count in report["removed_breakdown"].items():
            print(f"    • {reason}: {count}")

        # Save clean list
        clean_file = f"clean_email_list_{datetime.now():%Y%m%d_%H%M%S}.txt"
        with open(clean_file, "w") as f:
            for email in clean_list:
                f.write(f"{email}\n")
        print(f"\n💾 Clean list saved to: {clean_file}")

        # Save full report
        report_file = f"campaign_validation_report_{datetime.now():%Y%m%d_%H%M%S}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        print(f"💾 Full report saved to: {report_file}")

        return report

    async def close(self):
        """Clean up resources."""
        await self.validator.close()


async def main():
    """Main function with example usage."""
    print("Sleuth Intel - Email Validation Example")
    print("=" * 60)

    # Example 1: Single email validation
    print("\n📌 Example 1: Single Email Validation")
    print("-" * 40)

    validator = EmailValidator()

    try:
        result = await validator.validate_email(
            email="john.doe@example.com",
            check_deliverability=True,
            find_social_profiles=True,
            find_owner=True,
        )

        print("\n✅ Validation complete!")
        if result.get("risk_indicators"):
            print(f"⚠️ Risk Indicators: {', '.join(result['risk_indicators'])}")

    except Exception as e:
        print(f"❌ Validation failed: {str(e)}")

    # Example 2: Bulk email validation
    print("\n📌 Example 2: Bulk Email Validation")
    print("-" * 40)

    test_emails = [
        "valid@example.com",
        "invalid@fake-domain-xyz.com",
        "disposable@tempmail.com",
        "role@company.com",
        "user@gmail.com",
    ]

    await validator.bulk_validate(test_emails, output_format="json")

    # Example 3: Domain analysis
    print("\n📌 Example 3: Domain Analysis")
    print("-" * 40)

    domain_analysis = await validator.domain_analysis("example.com")

    # Example 4: Campaign list cleaning
    print("\n📌 Example 4: Campaign List Cleaning")
    print("-" * 40)

    campaign_validator = EmailCampaignValidator()

    campaign_list = [
        "customer1@gmail.com",
        "info@company.com",
        "test@tempmail.com",
        "user@example.com",
        "invalid-email",
        "support@business.com",
    ]

    await campaign_validator.validate_campaign_list(
        email_list=campaign_list,
        remove_invalid=True,
        remove_risky=True,
        remove_role_based=True,
    )

    await validator.close()
    await campaign_validator.close()

    print("\n✨ All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
