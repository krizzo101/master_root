from setuptools import find_packages, setup

setup(
    name="opsvi-interfaces",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "pyyaml>=6.0",
    ],
    python_requires=">=3.8",
)
