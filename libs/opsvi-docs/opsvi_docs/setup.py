"""
Setup script for docRuleGen project.
"""

from setuptools import setup, find_packages

setup(
    name="docRuleGen",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "openai",
        "jsonschema",
        # Add other dependencies here
    ],
    extras_require={
        "genfilemap": ["utils-genfilemap"],  # Optional dependency on genFileMap
    },
    entry_points={
        "console_scripts": [
            "docrulegen=docRuleGen.docRuleGen:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="Tools for document rule generation and management",
    keywords="documentation, rules, AI",
    package_data={
        "docRuleGen": ["templates/*.json", "*.template"],
    },
    python_requires=">=3.7",
)
