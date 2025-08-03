
"""
Setup script for genfilemap package.
"""

import os
from setuptools import setup, find_packages

# Read the content of README.md
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

# Read requirements.txt
with open("requirements.txt", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="genfilemap",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        "genfilemap": [
            "templates/*.json",
            "schemas/*.json",
        ],
    },
    install_requires=[
        "openai>=1.6.0",
        "anthropic>=0.3.0",
        "aiohttp>=3.8.0",
        "pyyaml>=6.0.0",
        "rich>=13.0.0",
        "appdirs>=1.4.4",
    ],
    entry_points={
        "console_scripts": [
            "genfilemap=genfilemap.cli:main",
            "genfilemap-watcher=genfilemap.file_watcher:main",
        ],
    },
    python_requires=">=3.8",
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool for generating file maps and documentation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/genfilemap",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
) 