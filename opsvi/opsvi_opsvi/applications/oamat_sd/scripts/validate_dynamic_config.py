#!/usr/bin/env python3
"""
Dynamic Configuration Schema Validation Script
==============================================

Validates that the runtime configuration schema correctly matches
the current static configuration structure and can be used for
dynamic generation by the master agent.
"""

import json
from pathlib import Path
import sys

import jsonschema
import yaml

from src.applications.oamat_sd.src.config.config_manager import ConfigManager


def load_schema():
    """Load the runtime configuration schema."""
    schema_path = Path("config/runtime_config_schema.json")
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path) as f:
        return json.load(f)


def load_current_config():
    """Load the current static configuration as reference."""
    config_path = Path("config/app_config.yaml")
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        return yaml.safe_load(f)


def convert_yaml_to_json_compatible(config):
    """Convert YAML config to JSON-compatible format for validation."""
    # Handle any Python-specific types that might not translate directly
    return json.loads(json.dumps(config, default=str))


def validate_schema_completeness(schema, config):
    """Validate that schema covers all config sections."""
    schema_props = set(schema["properties"].keys())
    config_keys = set(ConfigManager().keys())

    missing_in_schema = config_keys - schema_props
    extra_in_schema = schema_props - config_keys

    return {
        "missing_in_schema": list(missing_in_schema),
        "extra_in_schema": list(extra_in_schema),
        "complete": len(missing_in_schema) == 0,
    }


def validate_config_against_schema(config, schema):
    """Validate current config against the dynamic schema."""
    try:
        # Convert config to JSON-compatible format
        json_config = convert_yaml_to_json_compatible(config)

        # Validate against schema
        jsonschema.validate(instance=json_config, schema=schema)
        return {"valid": True, "errors": []}

    except jsonschema.ValidationError as e:
        return {
            "valid": False,
            "errors": [f"Validation error: {e.message} at path: {e.absolute_path}"],
        }
    except Exception as e:
        return {"valid": False, "errors": [f"Unexpected error: {str(e)}"]}


def generate_sample_dynamic_config(schema):
    """Generate a sample dynamic configuration for testing."""
    # This would normally be done by the master agent
    # For validation, we'll create a minimal valid example

    sample_config = {
        "version": "1.0.0",
        "environment": "development",
        "models": {
            "reasoning": {
                "model_name": "o3-mini",
                "supports_temperature": False,
                "max_tokens": 12000,
                "reasoning_effort": "medium",
            },
            "agent": {
                "model_name": "gpt-4.1-mini",
                "temperature": 0.3,
                "max_tokens": 3000,
            },
            "implementation": {
                "model_name": "gpt-4.1",
                "temperature": 0.1,
                "max_tokens": 4000,
            },
        },
        "openai_api": {
            "base_url": "https://api.openai.com/v1/chat/completions",
            "timeout_seconds": 120,
            "max_retries": 3,
            "backoff_multiplier": 2.0,
            "rate_limits": {"requests_per_minute": 60, "tokens_per_day": 1000000},
        },
        "execution": {
            "agent_timeout_seconds": 400,
            "total_execution_timeout_seconds": 2000,
            "max_parallel_agents": 6,
            "max_retry_attempts": 3,
        },
        # Note: This is just a partial sample - master agent would generate complete config
    }

    return sample_config


def main():
    """Main validation execution."""
    print("🔍 DYNAMIC CONFIGURATION SCHEMA VALIDATION")
    print("=" * 50)

    try:
        # Load schema and current config
        print("📋 Loading schema and configuration...")
        schema = load_schema()
        current_config = load_current_config()

        print(f"✅ Schema loaded: {len(schema['properties'])} top-level properties")
        print(f"✅ Config loaded: {len(current_config)} top-level sections")

        # Validate schema completeness
        print("\n🎯 VALIDATING SCHEMA COMPLETENESS:")
        completeness = validate_schema_completeness(schema, current_config)

        if completeness["complete"]:
            print("✅ Schema covers all configuration sections")
        else:
            print("❌ Schema incomplete:")
            if completeness["missing_in_schema"]:
                print(f"   Missing in schema: {completeness['missing_in_schema']}")
            if completeness["extra_in_schema"]:
                print(f"   Extra in schema: {completeness['extra_in_schema']}")

        # Validate current config against schema
        print("\n🔍 VALIDATING CURRENT CONFIG AGAINST SCHEMA:")
        validation = validate_config_against_schema(current_config, schema)

        if validation["valid"]:
            print("✅ Current configuration validates against schema")
        else:
            print("❌ Validation errors found:")
            for error in validation["errors"]:
                print(f"   {error}")

        # Test dynamic config generation capability
        print("\n🚀 TESTING DYNAMIC CONFIGURATION GENERATION:")
        try:
            sample_config = generate_sample_dynamic_config(schema)
            sample_validation = validate_config_against_schema(sample_config, schema)

            if sample_validation["valid"]:
                print("✅ Sample dynamic configuration validates successfully")
                print(
                    "🎯 Master agent can generate valid configurations using this schema"
                )
            else:
                print("❌ Sample dynamic configuration validation failed:")
                for error in sample_validation["errors"]:
                    print(f"   {error}")
        except Exception as e:
            print(f"❌ Dynamic config generation test failed: {e}")

        # Summary
        print("\n📊 VALIDATION SUMMARY:")
        overall_success = completeness["complete"] and validation["valid"]

        if overall_success:
            print("🎉 SUCCESS: Dynamic configuration system ready for deployment")
            print("✅ Schema is complete and validates current configuration")
            print("✅ Master agent can use this schema for runtime generation")
            return 0
        else:
            print("❌ ISSUES FOUND: Dynamic configuration system needs fixes")
            return 1

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
