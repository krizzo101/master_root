#!/usr/bin/env python3

import json
import os
import sys

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from smart_decomposition_agent import O3MetaIntelligenceAnalysis


def debug_schema():
    print("Debugging O3MetaIntelligenceAnalysis schema...")

    try:
        schema = O3MetaIntelligenceAnalysis.model_json_schema()
        print("\nGenerated Schema:")
        print(json.dumps(schema, indent=2))

        print(f"\nProperties keys: {list(schema.get('properties', {}).keys())}")
        print(f"Required keys: {schema.get('required', [])}")

        # Check for mismatches
        properties_keys = set(schema.get("properties", {}).keys())
        required_keys = set(schema.get("required", []))

        extra_required = required_keys - properties_keys
        missing_required = properties_keys - required_keys

        if extra_required:
            print(f"\n❌ Extra required keys not in properties: {extra_required}")
        if missing_required:
            print(f"\n⚠️  Properties not marked as required: {missing_required}")

        if not extra_required and not missing_required:
            print("\n✅ Schema looks correct!")

        # Check nested schemas for issues
        print("\n🔍 Checking nested schemas...")
        if "$defs" in schema:
            for def_name, def_schema in schema["$defs"].items():
                if "properties" in def_schema and "required" in def_schema:
                    def_props = set(def_schema["properties"].keys())
                    def_required = set(def_schema["required"])
                    def_extra = def_required - def_props
                    if def_extra:
                        print(f"❌ {def_name} has extra required keys: {def_extra}")
                    else:
                        print(f"✅ {def_name} schema OK")

    except Exception as e:
        print(f"Error generating schema: {e}")
        import traceback

        traceback.print_exc()


def test_openai_validation():
    """Test if OpenAI accepts this schema"""
    try:
        import os

        from openai import OpenAI

        # Try to create a client (won't actually make request)
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required - no fallbacks allowed"
            )
        client = OpenAI(api_key=api_key)

        schema = O3MetaIntelligenceAnalysis.model_json_schema()
        print("\n🧪 Testing OpenAI schema validation...")
        print(f"Schema has {len(schema.get('properties', {}))} properties")
        print(f"Schema has {len(schema.get('required', []))} required fields")

        # Check for common OpenAI issues
        issues = []

        # Check if all required fields exist in properties
        props = set(schema.get("properties", {}).keys())
        required = set(schema.get("required", []))
        extra_required = required - props
        if extra_required:
            issues.append(f"Extra required fields: {extra_required}")

        # Check nested schemas
        for def_name, def_schema in schema.get("$defs", {}).items():
            if "properties" in def_schema and "required" in def_schema:
                def_props = set(def_schema["properties"].keys())
                def_required = set(def_schema["required"])
                def_extra = def_required - def_props
                if def_extra:
                    issues.append(f"{def_name} has extra required: {def_extra}")

        if issues:
            print("❌ Schema validation issues found:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("✅ Schema should be valid for OpenAI")

    except Exception as e:
        print(f"Error testing OpenAI validation: {e}")


if __name__ == "__main__":
    debug_schema()
    test_openai_validation()
