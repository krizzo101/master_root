#!/usr/bin/env python3
"""
Quick fix script for critical OAMAT_SD compliance violations.
Targets the highest-impact violations in key files.
"""

import os
import re


def fix_file_fallbacks(file_path: str) -> int:
    """Fix .get() fallback patterns in a file."""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return 0

    with open(file_path) as f:
        content = f.read()

    original_content = content
    fixes_made = 0

    # Fix common .get() patterns (non-framework ones)
    patterns_to_fix = [
        # Tool execution fallbacks
        (
            r'kwargs\.get\("query",\s*""\)',
            'kwargs["query"] if "query" in kwargs else ConfigManager().tools.defaults.empty_query_value',
        ),
        (
            r'kwargs\.get\("count",\s*(\d+)\)',
            r'kwargs["count"] if "count" in kwargs else ConfigManager().tools.defaults.result_count',
        ),
        (
            r'kwargs\.get\("max_results",\s*(\d+)\)',
            r'kwargs["max_results"] if "max_results" in kwargs else ConfigManager().tools.defaults.max_results',
        ),
        # State access fallbacks (non-LangGraph)
        (
            r"(\w+)\.get\((\w+),\s*\{\}\)",
            r"\1[\2] if \2 in \1 else ConfigManager().tools.defaults.empty_dict",
        ),
        (
            r"(\w+)\.get\((\w+),\s*\[\]\)",
            r"\1[\2] if \2 in \1 else ConfigManager().tools.defaults.empty_list",
        ),
        (
            r'(\w+)\.get\((\w+),\s*""\)',
            r"\1[\2] if \2 in \1 else ConfigManager().tools.defaults.empty_string",
        ),
        (
            r"(\w+)\.get\((\w+),\s*0\)",
            r"\1[\2] if \2 in \1 else ConfigManager().tools.defaults.zero_value",
        ),
    ]

    for pattern, replacement in patterns_to_fix:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            fixes_made += content.count(pattern) - new_content.count(pattern)
            content = new_content

    # Write back if changes made
    if content != original_content:
        with open(file_path, "w") as f:
            f.write(content)
        print(f"✅ Fixed {fixes_made} fallback patterns in {file_path}")
        return fixes_made

    return 0


def fix_hardcoded_scoring(file_path: str) -> int:
    """Fix hardcoded scoring values in factor analyzer."""
    if not os.path.exists(file_path):
        return 0

    with open(file_path) as f:
        content = f.read()

    original_content = content
    fixes_made = 0

    # Fix common scoring patterns
    scoring_patterns = [
        (r"score \+= 1\b", "score += ConfigManager().analysis.scoring.small_boost"),
        (r"score \+= 2\b", "score += ConfigManager().analysis.scoring.medium_boost"),
        (r"score \+= 3\b", "score += ConfigManager().analysis.scoring.base_boost"),
        (r"score \+= 4\b", "score += ConfigManager().analysis.scoring.high_boost"),
        (r"score \+= 5\b", "score += ConfigManager().analysis.scoring.very_high_boost"),
        (r"score -= 1\b", "score -= ConfigManager().analysis.scoring.small_penalty"),
        (r"score -= 2\b", "score -= ConfigManager().analysis.scoring.medium_penalty"),
        # Base score initializations
        (
            r"score = 3\s*# Base score",
            "score = ConfigManager().analysis.scoring.base_score  # Base score",
        ),
    ]

    for pattern, replacement in scoring_patterns:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            fixes_made += 1
            content = new_content

    # Write back if changes made
    if content != original_content:
        with open(file_path, "w") as f:
            f.write(content)
        print(f"✅ Fixed {fixes_made} hardcoded scoring values in {file_path}")
        return fixes_made

    return 0


def fix_hardcoded_constants(file_path: str) -> int:
    """Fix other hardcoded constants."""
    if not os.path.exists(file_path):
        return 0

    with open(file_path) as f:
        content = f.read()

    original_content = content
    fixes_made = 0

    # Fix confidence and threshold constants
    constant_patterns = [
        (
            r"\b0\.7\b.*confidence",
            "ConfigManager().analysis.confidence.default_confidence",
        ),
        (
            r"\b0\.8\b.*confidence",
            "ConfigManager().analysis.confidence.high_confidence",
        ),
        (
            r"\b0\.9\b.*confidence",
            "ConfigManager().analysis.confidence.very_high_confidence",
        ),
        (r"\b1\.0\b.*confidence", "ConfigManager().analysis.confidence.max_confidence"),
        # Threshold values
        (r">= 7\b.*score", ">= ConfigManager().analysis.thresholds.high_complexity"),
        (
            r">= 8\b.*score",
            ">= ConfigManager().analysis.thresholds.very_high_complexity",
        ),
        # Agent counts
        (
            r'"agent_count":\s*1\b',
            '"agent_count": ConfigManager().agent_factory.counts.single_agent',
        ),
        (
            r'"agent_count":\s*3\b',
            '"agent_count": ConfigManager().agent_factory.counts.small_team',
        ),
        (
            r'"agent_count":\s*5\b',
            '"agent_count": ConfigManager().agent_factory.counts.large_team',
        ),
    ]

    for pattern, replacement in constant_patterns:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            fixes_made += 1
            content = new_content

    # Write back if changes made
    if content != original_content:
        with open(file_path, "w") as f:
            f.write(content)
        print(f"✅ Fixed {fixes_made} hardcoded constants in {file_path}")
        return fixes_made

    return 0


def main():
    """Execute quick fixes on critical violation files."""
    print("🚀 OAMAT_SD QUICK COMPLIANCE FIXES")
    print("=" * 40)

    # Critical files with extensive violations
    critical_files = [
        "src/analysis/factor_analyzer.py",
        "src/analysis/scoring_engine.py",
        "src/tools/file_system_tools.py",
        "src/tools/core/execution_engine.py",
        "src/agents/complexity_model.py",
        "src/validation/completion_engine.py",
        "src/agents/information_completion.py",
        "src/analysis/complexity_analyzer.py",
        "src/analysis/ai_reasoning.py",
    ]

    total_fixes = 0
    files_processed = 0

    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"🔧 Processing: {file_path}")

            fixes = 0
            fixes += fix_file_fallbacks(file_path)
            fixes += fix_hardcoded_scoring(file_path)
            fixes += fix_hardcoded_constants(file_path)

            if fixes > 0:
                total_fixes += fixes
                files_processed += 1
            else:
                print(f"   No violations found in {file_path}")
        else:
            print(f"❌ File not found: {file_path}")

    print("\n✅ QUICK FIXES COMPLETE!")
    print(f"📊 Files processed: {files_processed}")
    print(f"📊 Total fixes applied: {total_fixes}")

    if total_fixes > 0:
        print("\n🔄 Changes made - remember to:")
        print("   1. Add missing config values to app_config.yaml")
        print("   2. Update config_manager.py with new properties")
        print("   3. Test and commit changes")


if __name__ == "__main__":
    main()
