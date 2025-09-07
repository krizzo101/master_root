"""Setup configuration for Sleuth Intel package."""

import os

from setuptools import find_packages, setup

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


# Read requirements
def read_requirements(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


# Get version from __init__.py
def get_version():
    init_file = os.path.join("src", "__init__.py")
    with open(init_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "0.1.0"


setup(
    name="sleuth-intel",
    version=get_version(),
    author="Sleuth Intel Team",
    author_email="team@sleuth-intel.com",
    description="Advanced intelligence gathering and analysis platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/sleuth-intel",
    project_urls={
        "Bug Tracker": "https://github.com/your-org/sleuth-intel/issues",
        "Documentation": "https://docs.sleuth-intel.com",
        "Source Code": "https://github.com/your-org/sleuth-intel",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=read_requirements("requirements.txt"),
    extras_require={
        "dev": read_requirements("requirements-dev.txt"),
        "test": read_requirements("requirements-test.txt"),
        "prod": read_requirements("requirements-prod.txt"),
    },
    entry_points={
        "console_scripts": [
            "sleuth-intel=src.cli:main",
            "sleuth-server=src.api.app:run_server",
        ],
    },
    include_package_data=True,
    package_data={
        "sleuth_intel": [
            "config/*.yaml",
            "config/*.json",
            "templates/*.html",
            "static/**/*",
        ],
    },
    zip_safe=False,
)
