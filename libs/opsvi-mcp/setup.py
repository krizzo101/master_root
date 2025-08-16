"""
Setup script for OPSVI MCP Servers

Install with: pip install -e .
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text()

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip() 
        for line in requirements_file.read_text().splitlines()
        if line.strip() and not line.startswith("#") and not line.startswith("-")
    ]

setup(
    name="opsvi-mcp",
    version="1.0.0",
    author="OPSVI Team",
    description="MCP Server implementations for Claude Code, OpenAI Codex, and Cursor Agent integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/opsvi/opsvi-mcp",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "opsvi_mcp": [
            "servers/*.yaml",
            "servers/**/*.yaml",
            "servers/**/*.md",
        ],
    },
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
        ],
    },
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "opsvi-claude-code=opsvi_mcp.servers.claude_code.__main__:main",
            "opsvi-claude-code-v2=opsvi_mcp.servers.claude_code_v2.__main__:main",
            "opsvi-codex=opsvi_mcp.servers.openai_codex.__main__:main",
            "opsvi-cursor=opsvi_mcp.servers.cursor_agent.__main__:main",
            "opsvi-orchestrator=opsvi_mcp.servers.unified_orchestrator:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Text Processing :: Linguistic",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    keywords="mcp claude openai codex cursor ai development automation",
    project_urls={
        "Bug Reports": "https://github.com/opsvi/opsvi-mcp/issues",
        "Source": "https://github.com/opsvi/opsvi-mcp",
        "Documentation": "https://github.com/opsvi/opsvi-mcp/blob/main/README.md",
    },
)