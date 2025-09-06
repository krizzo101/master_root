#!/usr/bin/env python3
"""
Setup script for Enhanced Chat Monitor package.
"""

from pathlib import Path

from setuptools import find_packages, setup

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="enhanced-chat-monitor",
    version="1.0.0",
    description="Agent Collaboration Observatory for Claude Code agent swarms",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Claude Code Enhanced Monitor",
    author_email="noreply@anthropic.com",
    url="https://github.com/anthropics/claude-code",
    # Package configuration
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    # Entry point for command-line usage
    entry_points={
        "console_scripts": [
            "chat-monitor=monitor:cli_main",
        ],
    },
    # Dependencies
    install_requires=[
        # No external dependencies - uses only Python standard library
    ],
    # Optional dependencies
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=21.0",
            "flake8>=3.8",
        ],
    },
    # Package metadata
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Tools",
        "Topic :: System :: Monitoring",
        "Topic :: Communications",
    ],
    # Package data
    include_package_data=True,
    zip_safe=False,
    # Keywords for PyPI
    keywords="monitoring, agents, collaboration, claude-code, observability",
)
