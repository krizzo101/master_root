"""
Setup script for ACCF Research Agent package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh if line.strip() and not line.startswith("#")
    ]

setup(
    name="accf-agents",
    version="0.5.0",
    author="ACCF Team",
    author_email="team@accf.org",
    description="Production-ready research agent system with Neo4j GraphRAG integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/accf/research-agent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=6.2.1",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.7.0",
            "mutmut>=3.3.1",
            "safety>=3.6.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "accf-agent=accf_agents.cli:main",
        ],
    },
)
