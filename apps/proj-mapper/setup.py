"""Setup script for the Project Mapper package."""

import os
from setuptools import setup, find_packages

# Get version
about = {}
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "src", "proj_mapper", "version.py"), "r") as f:
    exec(f.read(), about)

# Read README for long description
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="proj-mapper",
    version=about["__version__"],
    description="A tool for mapping project structures and relationships",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/proj_mapper",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
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
    python_requires=">=3.8",
    install_requires=[
        "pydantic>=1.9.0,<2.0.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "mypy>=0.910",
            "black>=22.1.0",
            "isort>=5.10.1",
            "flake8>=4.0.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "proj-mapper=proj_mapper.cli.main:cli",
        ],
    },
)
