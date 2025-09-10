#!/usr/bin/env python3
"""
Configuration validation and management for chat monitoring system
"""

import json
import logging
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import jsonschema
import yaml


@dataclass
class ValidationResult:
    """Configuration validation result"""

    valid: bool
    errors: List[str]
    warnings: List[str]
    config: Optional[Dict[str, Any]] = None


class ConfigValidator:
    """Configuration validator and manager"""

    def __init__(self):
        self.schema = self._get_config_schema()
        self.logger = logging.getLogger(__name__)

    def _get_config_schema(self) -> Dict[str, Any]:
        """Get JSON schema for configuration validation"""
        return {
            "type": "object",
            "required": ["service", "watcher", "database", "monitoring"],
            "properties": {
                "service": {
                    "type": "object",
                    "required": ["name", "log_level"],
                    "properties": {
                        "name": {"type": "string", "minLength": 1},
                        "log_level": {"enum": ["DEBUG", "INFO", "WARNING", "ERROR"]},
                        "workers": {"type": "integer", "minimum": 1, "maximum": 16},
                        "max_connections": {"type": "integer", "minimum": 1},
                    },
                },
                "watcher": {
                    "type": "object",
                    "required": ["enabled", "batch_size", "queue_size"],
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "batch_size": {"type": "integer", "minimum": 1, "maximum": 100},
                        "queue_size": {
                            "type": "integer",
                            "minimum": 10,
                            "maximum": 10000,
                        },
                        "max_files_per_minute": {"type": "integer", "minimum": 1},
                        "file_extensions": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "watch_directories": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
                "database": {
                    "type": "object",
                    "required": ["postgres"],
                    "properties": {
                        "postgres": {
                            "type": "object",
                            "required": ["url"],
                            "properties": {
                                "url": {"type": "string", "minLength": 10},
                                "max_connections": {"type": "integer", "minimum": 1},
                                "connection_timeout": {"type": "integer", "minimum": 1},
                            },
                        },
                        "sqlite": {
                            "type": "object",
                            "properties": {"path": {"type": "string", "minLength": 1}},
                        },
                    },
                },
                "monitoring": {
                    "type": "object",
                    "required": ["enabled"],
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "port": {"type": "integer", "minimum": 1024, "maximum": 65535},
                        "health_checks": {
                            "type": "object",
                            "properties": {
                                "enabled": {"type": "boolean"},
                                "interval_seconds": {"type": "integer", "minimum": 10},
                                "timeout_seconds": {"type": "integer", "minimum": 1},
                            },
                        },
                    },
                },
            },
        }

    def load_config(self, config_path: str, env: str = None) -> ValidationResult:
        """Load and validate configuration file"""
        try:
            # Load base configuration
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            # Apply environment overrides
            if env and "environment" in config and env in config["environment"]:
                self._apply_overrides(config, config["environment"][env])
                del config["environment"]  # Remove environment section after applying

            # Substitute environment variables
            config = self._substitute_env_vars(config)

            # Validate against schema
            validation_result = self._validate_schema(config)

            # Additional custom validations
            if validation_result.valid:
                validation_result = self._validate_custom_rules(
                    config, validation_result
                )

            validation_result.config = config
            return validation_result

        except FileNotFoundError:
            return ValidationResult(
                valid=False,
                errors=[f"Configuration file not found: {config_path}"],
                warnings=[],
            )
        except yaml.YAMLError as e:
            return ValidationResult(
                valid=False, errors=[f"YAML parsing error: {e}"], warnings=[]
            )
        except Exception as e:
            return ValidationResult(
                valid=False,
                errors=[f"Unexpected error loading config: {e}"],
                warnings=[],
            )

    def _apply_overrides(self, base_config: Dict, overrides: Dict):
        """Apply environment-specific overrides to base configuration"""
        for key, value in overrides.items():
            if (
                key in base_config
                and isinstance(value, dict)
                and isinstance(base_config[key], dict)
            ):
                self._apply_overrides(base_config[key], value)
            else:
                base_config[key] = value

    def _substitute_env_vars(self, obj: Any) -> Any:
        """Recursively substitute environment variables in configuration"""
        if isinstance(obj, dict):
            return {k: self._substitute_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            env_var = obj[2:-1]
            default = None

            if ":-" in env_var:
                env_var, default = env_var.split(":-", 1)

            return os.getenv(env_var, default)
        else:
            return obj

    def _validate_schema(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate configuration against JSON schema"""
        try:
            jsonschema.validate(config, self.schema)
            return ValidationResult(valid=True, errors=[], warnings=[])
        except jsonschema.ValidationError as e:
            return ValidationResult(
                valid=False,
                errors=[f"Schema validation error: {e.message}"],
                warnings=[],
            )

    def _validate_custom_rules(
        self, config: Dict[str, Any], result: ValidationResult
    ) -> ValidationResult:
        """Apply custom validation rules"""
        errors = result.errors.copy()
        warnings = result.warnings.copy()

        # Check database URL format
        postgres_url = config.get("database", {}).get("postgres", {}).get("url", "")
        if postgres_url and not postgres_url.startswith(
            ("postgresql://", "postgres://")
        ):
            errors.append(
                "PostgreSQL URL must start with 'postgresql://' or 'postgres://'"
            )

        # Check watch directories exist
        watch_dirs = config.get("watcher", {}).get("watch_directories", [])
        for watch_dir in watch_dirs:
            if not os.path.exists(watch_dir):
                warnings.append(f"Watch directory does not exist: {watch_dir}")

        # Check queue size vs batch size ratio
        queue_size = config.get("watcher", {}).get("queue_size", 0)
        batch_size = config.get("watcher", {}).get("batch_size", 0)
        if queue_size > 0 and batch_size > 0:
            if queue_size < batch_size * 10:
                warnings.append(
                    f"Queue size ({queue_size}) should be at least 10x batch size ({batch_size})"
                )

        # Check monitoring port conflicts
        monitoring_port = config.get("monitoring", {}).get("port", 8080)
        if monitoring_port in [3000, 5432, 6379, 9090]:  # Common service ports
            warnings.append(
                f"Monitoring port {monitoring_port} conflicts with common service ports"
            )

        # Check resource thresholds
        health_checks = config.get("monitoring", {}).get("health_checks", {})
        thresholds = health_checks.get("endpoints", [])
        for endpoint in thresholds:
            if endpoint.get("type") == "resources":
                resource_thresholds = endpoint.get("thresholds", {})
                cpu_threshold = resource_thresholds.get("cpu_percent", 0)
                memory_threshold = resource_thresholds.get("memory_percent", 0)

                if cpu_threshold > 95:
                    warnings.append(f"CPU threshold {cpu_threshold}% is very high")
                if memory_threshold > 95:
                    warnings.append(
                        f"Memory threshold {memory_threshold}% is very high"
                    )

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def export_config(self, config: Dict[str, Any], format: str = "yaml") -> str:
        """Export configuration in specified format"""
        if format.lower() == "json":
            return json.dumps(config, indent=2)
        elif format.lower() == "yaml":
            return yaml.dump(config, default_flow_style=False, sort_keys=False)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def generate_sample_config(self) -> str:
        """Generate a sample configuration file"""
        sample_config = {
            "service": {
                "name": "chat-monitoring",
                "log_level": "INFO",
                "workers": 2,
                "max_connections": 50,
            },
            "watcher": {
                "enabled": True,
                "batch_size": 10,
                "queue_size": 1000,
                "file_extensions": [".jsonl"],
                "watch_directories": ["/home/app/.claude/projects"],
            },
            "database": {
                "postgres": {
                    "url": "${POSTGRES_URL}",
                    "max_connections": 10,
                    "connection_timeout": 10,
                }
            },
            "monitoring": {
                "enabled": True,
                "port": 8080,
                "health_checks": {
                    "enabled": True,
                    "interval_seconds": 30,
                    "timeout_seconds": 10,
                },
            },
            "logging": {"level": "INFO", "format": "json"},
        }

        return yaml.dump(sample_config, default_flow_style=False, sort_keys=False)


def main():
    """Main CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Configuration validator and manager")
    parser.add_argument("command", choices=["validate", "generate", "export"])
    parser.add_argument("--config", "-c", help="Configuration file path")
    parser.add_argument(
        "--env", "-e", help="Environment (production, staging, development)"
    )
    parser.add_argument(
        "--format", "-f", choices=["yaml", "json"], default="yaml", help="Output format"
    )
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    validator = ConfigValidator()

    if args.command == "validate":
        if not args.config:
            print("ERROR: --config is required for validate command")
            sys.exit(1)

        result = validator.load_config(args.config, args.env)

        if result.valid:
            print("✅ Configuration is valid")
            if result.warnings:
                print("\n⚠️  Warnings:")
                for warning in result.warnings:
                    print(f"  - {warning}")
            sys.exit(0)
        else:
            print("❌ Configuration is invalid")
            print("\nErrors:")
            for error in result.errors:
                print(f"  - {error}")
            if result.warnings:
                print("\nWarnings:")
                for warning in result.warnings:
                    print(f"  - {warning}")
            sys.exit(1)

    elif args.command == "generate":
        sample_config = validator.generate_sample_config()

        if args.output:
            with open(args.output, "w") as f:
                f.write(sample_config)
            print(f"Sample configuration written to {args.output}")
        else:
            print(sample_config)

    elif args.command == "export":
        if not args.config:
            print("ERROR: --config is required for export command")
            sys.exit(1)

        result = validator.load_config(args.config, args.env)

        if not result.valid:
            print("ERROR: Configuration is invalid, cannot export")
            sys.exit(1)

        exported_config = validator.export_config(result.config, args.format)

        if args.output:
            with open(args.output, "w") as f:
                f.write(exported_config)
            print(f"Configuration exported to {args.output}")
        else:
            print(exported_config)


if __name__ == "__main__":
    main()
