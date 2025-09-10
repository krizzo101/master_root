#!/usr/bin/env python3
"""Fix API key handling in CLI functions"""

import re


def fix_config_creation(content):
    # Pattern to match ClaudeCodeConfig() calls with api_key parameter
    pattern = r"(config = ClaudeCodeConfig\(\s*)(provider=provider,\s*model=model,\s*api_key=api_key,\s*working_directory=[^,\)]+)\s*\)"

    def replace_func(match):
        indent = match.group(1).replace(
            "config = ClaudeCodeConfig(",
            "    # Only pass api_key if explicitly provided, let config load from env otherwise\n    config_kwargs = {",
        )
        params = match.group(2)

        # Split parameters
        params_dict = {}
        for param in params.split(","):
            param = param.strip()
            if "=" in param:
                key, value = param.split("=", 1)
                params_dict[key.strip()] = value.strip()

        # Build new config creation
        result = indent + "\n"
        result += '        "provider": provider,\n'
        result += '        "model": model,\n'

        if "working_directory" in params_dict:
            result += (
                f'        "working_directory": {params_dict["working_directory"]},\n'
            )

        result += "    }\n"
        result += "    if api_key:\n"
        result += '        config_kwargs["api_key"] = api_key\n'
        result += "    \n"
        result += "    config = ClaudeCodeConfig(**config_kwargs)"

        return result

    return re.sub(pattern, replace_func, content, flags=re.MULTILINE | re.DOTALL)


# Read the file
with open("src/claude_code/cli/main.py", "r") as f:
    content = f.read()

print("Original API key issues:")
for i, line in enumerate(content.split("\n"), 1):
    if "api_key=api_key" in line and "ClaudeCodeConfig" in line:
        print(f"Line {i}: {line.strip()}")

# Apply fix manually for each case
lines = content.split("\n")

# Fix each occurrence
for i, line in enumerate(lines):
    if "api_key=api_key" in line and "ClaudeCodeConfig" in line:
        # Find the start of the ClaudeCodeConfig call
        indent = len(line) - len(line.lstrip())
        indent_str = " " * indent

        # Replace this line and potentially the next few
        lines[i] = (
            indent_str
            + "# Only pass api_key if explicitly provided, let config load from env otherwise"
        )

        # Insert the new config creation logic
        config_lines = [
            indent_str + "config_kwargs = {",
            indent_str + '    "provider": provider,',
            indent_str + '    "model": model,',
            indent_str + '    "working_directory": working_directory,',
            indent_str + "}",
            indent_str + "if api_key:",
            indent_str + '    config_kwargs["api_key"] = api_key',
            indent_str + "",
            indent_str + "config = ClaudeCodeConfig(**config_kwargs)",
        ]

        # Find where the ClaudeCodeConfig call ends and replace
        j = i + 1
        while j < len(lines) and not lines[j].strip().endswith(")"):
            j += 1

        # Replace the entire config creation block
        lines[i : j + 1] = config_lines

# Write the fixed content
fixed_content = "\n".join(lines)

with open("src/claude_code/cli/main.py", "w") as f:
    f.write(fixed_content)

print("Fixed all API key configuration issues!")
