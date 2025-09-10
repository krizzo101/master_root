#!/usr/bin/env python3
"""
Claude Chat Import Setup Validator

Validates that all components are properly configured and ready for
the Claude chat log import process.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import yaml


def check_file_exists(file_path: str, description: str) -> bool:
    """Check if a file exists and report status."""
    path = Path(file_path)
    if path.exists():
        size = path.stat().st_size
        print(f"✅ {description}: {file_path} ({size:,} bytes)")
        return True
    else:
        print(f"❌ {description}: {file_path} (NOT FOUND)")
        return False


def check_directory_exists(dir_path: str, description: str) -> bool:
    """Check if a directory exists and report status."""
    path = Path(dir_path)
    if path.exists() and path.is_dir():
        file_count = len(list(path.glob("**/*.jsonl")))
        print(f"✅ {description}: {dir_path} ({file_count} JSONL files)")
        return True
    else:
        print(f"❌ {description}: {dir_path} (NOT FOUND)")
        return False


def validate_config_file(config_path: str) -> bool:
    """Validate the configuration file."""
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        # Check required sections
        required_sections = [
            "adapter_config",
            "source_config",
            "import_phases",
            "processing",
        ]
        missing_sections = [
            section for section in required_sections if section not in config
        ]

        if missing_sections:
            print(f"❌ Config validation failed: Missing sections: {missing_sections}")
            return False

        print(f"✅ Configuration file valid: {config_path}")

        # Print key settings
        print(f"   • Adapter ID: {config['adapter_config']['adapter_id']}")
        print(f"   • Batch size: {config['adapter_config']['batch_size']}")
        print(f"   • Workers: {config['adapter_config']['max_concurrent_workers']}")
        print(f"   • Embeddings: {config['adapter_config']['generate_embeddings']}")
        print(
            f"   • Relationships: {config['adapter_config']['extract_relationships']}"
        )

        return True

    except Exception as e:
        print(f"❌ Config validation failed: {str(e)}")
        return False


def check_sample_jsonl_file() -> bool:
    """Check if we can parse a sample JSONL file."""
    try:
        projects_dir = Path("/home/opsvi/.claude/projects")
        jsonl_files = list(projects_dir.glob("**/*.jsonl"))

        if not jsonl_files:
            print("❌ No JSONL files found to sample")
            return False

        # Test parsing first file
        sample_file = jsonl_files[0]
        messages_parsed = 0

        with open(sample_file, "r") as f:
            for line_num, line in enumerate(f, 1):
                if line_num > 5:  # Just test first 5 lines
                    break

                line = line.strip()
                if not line:
                    continue

                try:
                    message = json.loads(line)

                    # Check for expected fields
                    if "sessionId" in message and "timestamp" in message:
                        messages_parsed += 1

                except json.JSONDecodeError:
                    print(f"❌ JSON parsing failed on line {line_num} of {sample_file}")
                    return False

        print(
            f"✅ Sample JSONL parsing successful: {sample_file.name} ({messages_parsed} messages)"
        )
        return True

    except Exception as e:
        print(f"❌ JSONL sampling failed: {str(e)}")
        return False


def check_database_connection() -> bool:
    """Check database connectivity."""
    try:
        import psycopg2

        conn = psycopg2.connect(
            "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context"
        )
        conn.close()

        print("✅ Database connection successful")
        return True

    except ImportError:
        print("❌ psycopg2 not available - install with: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False


def check_python_dependencies() -> bool:
    """Check required Python packages."""
    required_packages = [
        ("yaml", "PyYAML"),
        ("psycopg2", "psycopg2-binary"),
        ("numpy", "numpy"),
        ("sentence_transformers", "sentence-transformers"),
    ]

    missing_packages = []

    for module_name, package_name in required_packages:
        try:
            __import__(module_name)
            print(f"✅ {package_name} available")
        except ImportError:
            print(f"❌ {package_name} not available")
            missing_packages.append(package_name)

    if missing_packages:
        print(f"\n📦 Install missing packages with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False

    return True


def main():
    """Main validation function."""
    print("🔍 Claude Chat Import Setup Validation")
    print("=" * 50)

    checks = []

    # File existence checks
    print("\n📁 File System Checks:")
    checks.append(
        check_file_exists("config/claude_chat_import_config.yaml", "Configuration file")
    )
    checks.append(check_file_exists("execute_claude_chat_import.py", "Import script"))
    checks.append(check_file_exists("start_claude_chat_import.sh", "Starter script"))
    checks.append(
        check_file_exists(
            "src/project_context/ingestion/adapters/chat_adapter.py", "Chat adapter"
        )
    )

    # Directory checks
    print("\n📂 Directory Checks:")
    checks.append(
        check_directory_exists(
            "/home/opsvi/.claude/projects", "Claude projects directory"
        )
    )
    checks.append(
        check_directory_exists("src/project_context", "Project context source")
    )

    # Configuration validation
    print("\n⚙️  Configuration Validation:")
    checks.append(validate_config_file("config/claude_chat_import_config.yaml"))

    # Data validation
    print("\n📊 Data Validation:")
    checks.append(check_sample_jsonl_file())

    # Dependency checks
    print("\n🐍 Python Dependencies:")
    checks.append(check_python_dependencies())

    # Database check
    print("\n🗄️  Database Connectivity:")
    checks.append(check_database_connection())

    # Summary
    print("\n" + "=" * 50)
    print("📋 VALIDATION SUMMARY")
    print("=" * 50)

    passed_checks = sum(checks)
    total_checks = len(checks)

    if passed_checks == total_checks:
        print(f"🎉 All {total_checks} checks passed!")
        print("\n✨ Your system is ready for Claude chat import!")
        print("\n🚀 Next steps:")
        print(
            "   1. Make the starter script executable: chmod +x start_claude_chat_import.sh"
        )
        print("   2. Run the import: ./start_claude_chat_import.sh")
        print("   3. Monitor progress in the generated log files")

        return True
    else:
        failed_checks = total_checks - passed_checks
        print(f"❌ {failed_checks}/{total_checks} checks failed")
        print("\n🔧 Please fix the issues above before running the import.")

        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
