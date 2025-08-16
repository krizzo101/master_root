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
    description="Generate file maps for better AI agent context",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="DocRuleGen Team",
    author_email="info@example.com",
    url="https://github.com/yourusername/genfilemap",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=requirements,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "genfilemap=genfilemap:main",
        ],
    },
    include_package_data=True,
    package_data={
        "genfilemap": [
            "schema/*.json",
            "templates/*.txt",
        ],
    },
)
