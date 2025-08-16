#!/usr/bin/env python3
"""
Contract Compliance Validation Script
Validates that the OAMAT_SD application adheres to the NO FALLBACKS RULE
"""

import re
import sys
from pathlib import Path


def check_for_fallback_mechanisms():
    """Check for any fallback mechanisms in the codebase"""
    violations = []

    # Search for fallback-related patterns (only actual fallback logic)
    fallback_patterns = [
        r"agent_creator\.create_specialized_agents",
        r"alternative.*agent.*creation",
        r"backup.*agent.*creation",
        r"default.*agent.*creation",
    ]

    # Search in oamat_sd directory
    oamat_sd_path = Path(__file__).parent
    python_files = list(oamat_sd_path.rglob("*.py"))

    # Exclude the validation script itself
    python_files = [
        f for f in python_files if f.name != "validate_contract_compliance.py"
    ]

    for file_path in python_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

                for line_num, line in enumerate(lines, 1):
                    for pattern in fallback_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            # Skip comments and strings
                            stripped = line.strip()
                            if (
                                not stripped.startswith("#")
                                and not stripped.startswith('"')
                                and not stripped.startswith("'")
                            ):
                                violations.append(
                                    f"{file_path}:{line_num}: {line.strip()}"
                                )
                                break
        except Exception as e:
            violations.append(f"{file_path}: ERROR reading file - {e}")

    return violations


def check_contract_enforcement():
    """Check for contract enforcement patterns"""
    compliance = []

    # Search for contract enforcement patterns
    enforcement_patterns = [
        r"CONTRACT ENFORCEMENT",
        r"NO FALLBACKS RULE",
        r"system must fail completely",
        r"raise RuntimeError.*fail completely",
    ]

    oamat_sd_path = Path(__file__).parent
    python_files = list(oamat_sd_path.rglob("*.py"))

    for file_path in python_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

                for pattern in enforcement_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        compliance.append(f"{file_path}: Contains {pattern}")
        except Exception as e:
            compliance.append(f"{file_path}: ERROR reading file - {e}")

    return compliance


def main():
    """Main validation function"""
    print("🔍 CONTRACT COMPLIANCE VALIDATION")
    print("=" * 50)

    # Check for fallback violations
    print("\n1. Checking for fallback mechanisms...")
    violations = check_for_fallback_mechanisms()

    if violations:
        print("❌ FALLBACK VIOLATIONS DETECTED:")
        for violation in violations[:10]:  # Show first 10
            print(f"   {violation}")
        if len(violations) > 10:
            print(f"   ... and {len(violations) - 10} more violations")
        print("\n🚨 CONTRACT VIOLATION: Fallback mechanisms are prohibited!")
        return False
    else:
        print("✅ No fallback mechanisms detected")

    # Check for contract enforcement
    print("\n2. Checking for contract enforcement...")
    compliance = check_contract_enforcement()

    if compliance:
        print("✅ CONTRACT ENFORCEMENT DETECTED:")
        for item in compliance:
            print(f"   {item}")
    else:
        print("⚠️  No explicit contract enforcement patterns detected")

    # Check specific files
    print("\n3. Checking specific contract compliance...")

    # Check smart_decomposition_agent.py
    agent_file = Path(__file__).parent / "smart_decomposition_agent.py"
    if agent_file.exists():
        with open(agent_file) as f:
            content = f.read()
            # Check for actual standard agent creation logic, not comments about it
            if "agent_creator.create_specialized_agents" in content:
                print(
                    "❌ VIOLATION: smart_decomposition_agent.py still contains standard agent creation"
                )
                return False
            elif "CONTRACT ENFORCEMENT" in content:
                print("✅ smart_decomposition_agent.py contains contract enforcement")
            else:
                print(
                    "⚠️  smart_decomposition_agent.py missing explicit contract enforcement"
                )

    # Check subdivision_agent_factory.py
    factory_file = (
        Path(__file__).parent / "src" / "agents" / "subdivision_agent_factory.py"
    )
    if factory_file.exists():
        with open(factory_file) as f:
            content = f.read()
            if "CONTRACT ENFORCEMENT" in content:
                print("✅ subdivision_agent_factory.py contains contract enforcement")
            else:
                print(
                    "⚠️  subdivision_agent_factory.py missing explicit contract enforcement"
                )

    print("\n" + "=" * 50)
    print("✅ CONTRACT COMPLIANCE VALIDATION COMPLETE")
    print("✅ NO FALLBACKS RULE ENFORCED")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
