"""
Setup configuration for opsvi-api
"""

from pathlib import Path

from setuptools import find_packages, setup

# Read README if it exists
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    long_description = readme_path.read_text(encoding="utf-8")

setup(
    name="opsvi-api",
    version="0.1.0",
    description="API clients and servers for OpsVi services",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="OpsVi Team",
    author_email="team@opsvi.ai",
    url="https://github.com/opsvi/master_root",
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    install_requires=["fastapi>=0.104.0", "httpx>=0.25.0", "uvicorn>=0.24.0"],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.5.0",
        ],
        "test": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.21.0",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="opsvi api autonomous ai ml",
    project_urls={
        "Bug Reports": "https://github.com/opsvi/master_root/issues",
        "Source": "https://github.com/opsvi/master_root",
    },
)
