#!/usr/bin/env python3
"""
Development Process Orchestrator (DPO) Setup Script

This script installs the DPO system and its dependencies.
"""

from pathlib import Path

from setuptools import find_packages, setup

# Read the README file
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    long_description = readme_path.read_text()

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = requirements_path.read_text().strip().split("\n")

setup(
    name="dpo-system",
    version="1.0.0",
    author="Master Root AI Development Team",
    author_email="dev@masterroot.ai",
    description="Development Process Orchestrator - Intelligent development workflow automation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/masterroot/dpo",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.2.0",
        ],
        "monitoring": [
            "prometheus-client>=0.16.0",
            "opentelemetry-api>=1.17.0",
            "opentelemetry-sdk>=1.17.0",
            "opentelemetry-instrumentation>=0.38b0",
        ],
    },
    entry_points={
        "console_scripts": [
            "dpo=dpo.cli:main",
            "dpo-server=dpo.server:main",
            "dpo-dashboard=dpo.dashboard:main",
        ],
    },
    include_package_data=True,
    package_data={
        "dpo": [
            "templates/*.json",
            "config/*.json",
            "config/*.yaml",
            "static/*",
        ],
    },
    zip_safe=False,
)
